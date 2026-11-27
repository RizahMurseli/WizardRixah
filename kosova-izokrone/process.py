"""Build a compact routable road graph for Kosovo from an OSM PBF.

Usage: process.py <kosovo.osm.pbf> <border.json> <outdir>
Output: <outdir>/car.bin.gz, <outdir>/walk.bin.gz, <outdir>/places.json
Binary layout (little-endian):
  header: magic 'KXG2', nNodes u32, nEdges u32, nPts u32
  nodes: lon i32[n], lat i32[n]          (1e-5 deg)
  edges: u u32[m], v u32[m], len f32[m] (meters), spd u8[m] (car: km/h, walk: km/h*10),
         cls u8[m], dir u8[m] (0 both, 1 forward only, 2 backward only), pad to 4,
         ptStart u32[m+1]
  pts: lon i32[p], lat i32[p]            (intermediate geometry, simplified)
"""
import sys, math, gzip, json, struct
import numpy as np
import osmium
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

import os
SRC = sys.argv[1]
OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
BORDER = json.load(open(sys.argv[2]))
kos = prep(Polygon(BORDER[0]).buffer(0.01))

# class index, default car speed (km/h)
CLASSES = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
           'residential', 'living_street', 'service', 'track', 'path', 'footway', 'steps',
           'pedestrian', 'cycleway', 'bridleway', 'road']
LINK = {'motorway_link': 'motorway', 'trunk_link': 'trunk', 'primary_link': 'primary',
        'secondary_link': 'secondary', 'tertiary_link': 'tertiary'}
CAR_SPEED = {'motorway': 110, 'trunk': 85, 'primary': 65, 'secondary': 55, 'tertiary': 45,
             'unclassified': 35, 'residential': 25, 'living_street': 10, 'service': 15,
             'track': 15, 'road': 25}
LINK_SPEED = {'motorway': 50, 'trunk': 45, 'primary': 40, 'secondary': 35, 'tertiary': 30}
NO = {'no', 'private'}


def parse_speed(s):
    if not s:
        return None
    s = s.strip().lower()
    try:
        if s.endswith('mph'):
            return float(s[:-3]) * 1.609
        return float(s.split()[0])
    except ValueError:
        return None


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways = []      # (refs, lons, lats, car, walk, cls)
        self.places = []

    def node(self, n):
        p = n.tags.get('place')
        if p in ('city', 'town', 'village') and 'name' in n.tags:
            if not kos.contains(Point(n.location.lon, n.location.lat)):
                return
            pop = n.tags.get('population', '')
            try:
                pop = int(pop.replace('.', '').replace(',', '').split()[0])
            except Exception:
                pop = 0
            self.places.append({'n': n.tags.get('name:sq') or n.tags['name'], 'p': p,
                                'lon': round(n.location.lon, 5), 'lat': round(n.location.lat, 5),
                                'pop': pop})

    def way(self, w):
        t = w.tags
        hw = t.get('highway')
        if not hw:
            return
        is_link = hw in LINK
        base = LINK.get(hw, hw)
        if base not in CLASSES or t.get('area') == 'yes':
            return
        if t.get('access') in NO and not t.get('foot') and not t.get('motor_vehicle'):
            return
        # car
        car = 0
        if base in CAR_SPEED and t.get('motor_vehicle') not in NO and t.get('motorcar') not in NO \
                and t.get('access') not in NO:
            if base == 'track' and t.get('tracktype') not in ('grade1', 'grade2'):
                car = 0
            else:
                d = LINK_SPEED[base] if is_link else CAR_SPEED[base]
                ms = parse_speed(t.get('maxspeed'))
                if ms and not is_link:
                    d = min(d * 1.25, ms * 0.9)  # traffic / junction realism
                car = max(5, min(130, int(round(d))))
        # walk
        walk = 0
        if base not in ('motorway', 'trunk') or t.get('foot') in ('yes', 'designated'):
            if t.get('foot') not in NO and t.get('motorroad') != 'yes':
                walk = 30 if base == 'steps' else 50
                if base in ('path', 'track', 'bridleway'):
                    walk = 45
        if not car and not walk:
            return
        ow = t.get('oneway')
        d = 0
        if ow in ('yes', '1', 'true'):
            d = 1
        elif ow in ('-1', 'reverse'):
            d = 2
        elif ow != 'no' and (t.get('junction') == 'roundabout' or base == 'motorway'):
            d = 1
        refs, lons, lats = [], [], []
        for nd in w.nodes:
            if not nd.location.valid():
                continue
            refs.append(nd.ref)
            lons.append(nd.location.lon)
            lats.append(nd.location.lat)
        if len(refs) < 2:
            return
        self.ways.append((refs, lons, lats, car, walk, CLASSES.index(base), d))


h = H()
h.apply_file(SRC, locations=True)
print('ways', len(h.ways), 'places', len(h.places), file=sys.stderr)

# keep ways that touch Kosovo (bbox pre-check then polygon)
ways = []
for w in h.ways:
    mid = len(w[0]) // 2
    if kos.contains(Point(w[1][0], w[2][0])) or kos.contains(Point(w[1][-1], w[2][-1])) or \
            kos.contains(Point(w[1][mid], w[2][mid])):
        ways.append(w)
print('ways in kosovo', len(ways), file=sys.stderr)

use = {}
for refs, *_ in ways:
    for i, r in enumerate(refs):
        use[r] = use.get(r, 0) + (2 if i in (0, len(refs) - 1) else 1)

node_id = {}
node_lon, node_lat = [], []


def nid(ref, lon, lat):
    i = node_id.get(ref)
    if i is None:
        i = len(node_lon)
        node_id[ref] = i
        node_lon.append(lon)
        node_lat.append(lat)
    return i


R = 6371008.8


def hav(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def dp_simplify(xs, ys, tol):
    """Douglas-Peucker on local metric coords; returns kept indices."""
    n = len(xs)
    if n <= 2:
        return list(range(n))
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay, bx, by = xs[a], ys[a], xs[b], ys[b]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = xs[i] - ax, ys[i] - ay
            if L == 0:
                d = px * px + py * py
            else:
                t = max(0, min(1, (px * dx + py * dy) / L))
                ex, ey = px - t * dx, py - t * dy
                d = ex * ex + ey * ey
            if d > best:
                best, bi = d, i
        if best > tol * tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [i for i in range(n) if keep[i]]


KX = math.cos(math.radians(42.6)) * 111320
KY = 110540
E_u, E_v, E_len, E_car, E_walk, E_cls, E_dir, E_ps = [], [], [], [], [], [], [], [0]
P_lon, P_lat = [], []
for refs, lons, lats, car, walk, cls, dr in ways:
    start = 0
    for i in range(1, len(refs)):
        if i == len(refs) - 1 or use[refs[i]] >= 2:
            seg = range(start, i + 1)
            length = sum(hav(lons[k], lats[k], lons[k + 1], lats[k + 1]) for k in range(start, i))
            if length > 0.5:
                u = nid(refs[start], lons[start], lats[start])
                v = nid(refs[i], lons[i], lats[i])
                xs = [lons[k] * KX for k in seg]
                ys = [lats[k] * KY for k in seg]
                kept = dp_simplify(xs, ys, 8.0)
                for k in kept[1:-1]:
                    P_lon.append(lons[start + k])
                    P_lat.append(lats[start + k])
                E_u.append(u); E_v.append(v); E_len.append(length)
                E_car.append(car); E_walk.append(walk); E_cls.append(cls); E_dir.append(dr)
                E_ps.append(len(P_lon))
            start = i

n, m, p = len(node_lon), len(E_u), len(P_lon)
print('nodes', n, 'edges', m, 'pts', p, file=sys.stderr)


def q(a):
    return np.round(np.asarray(a, dtype=np.float64) * 1e5).astype('<i4').tobytes()


def write_mode(name, spd_list, keep_dir):
    sel = [e for e in range(m) if spd_list[e]]
    remap = {}
    lon, lat = [], []
    def r(i):
        j = remap.get(i)
        if j is None:
            j = remap[i] = len(lon)
            lon.append(node_lon[i]); lat.append(node_lat[i])
        return j
    U, V, LEN, SPD, CLS, DIR, PS, PLON, PLAT = [], [], [], [], [], [], [0], [], []
    for e in sel:
        U.append(r(E_u[e])); V.append(r(E_v[e])); LEN.append(E_len[e]); SPD.append(spd_list[e])
        CLS.append(E_cls[e]); DIR.append(E_dir[e] if keep_dir else 0)
        PLON += P_lon[E_ps[e]:E_ps[e + 1]]; PLAT += P_lat[E_ps[e]:E_ps[e + 1]]
        PS.append(len(PLON))
    n2, m2, p2 = len(lon), len(U), len(PLON)
    buf = b'KXG2' + struct.pack('<III', n2, m2, p2)
    buf += q(lon) + q(lat)
    buf += np.array(U, '<u4').tobytes() + np.array(V, '<u4').tobytes() + np.array(LEN, '<f4').tobytes()
    buf += np.array(SPD, 'u1').tobytes() + np.array(CLS, 'u1').tobytes() + np.array(DIR, 'u1').tobytes()
    buf += b'\0' * ((-len(buf)) % 4)
    buf += np.array(PS, '<u4').tobytes() + q(PLON) + q(PLAT)
    gz = gzip.compress(buf, 9, mtime=0)
    open(os.path.join(OUT, name + '.bin.gz'), 'wb').write(gz)
    print(name, 'nodes', n2, 'edges', m2, 'pts', p2, 'gz', len(gz), file=sys.stderr)


write_mode('car', E_car, True)
write_mode('walk', E_walk, False)

pl = sorted(h.places, key=lambda x: ({'city': 0, 'town': 1, 'village': 2}[x['p']], -x['pop'], x['n']))
json.dump(pl, open(os.path.join(OUT, 'places.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
