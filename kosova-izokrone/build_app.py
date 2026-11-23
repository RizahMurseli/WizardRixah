"""Inject the Kosovo border into app.html -> ../kosova-izokrone.html"""
import json, os
from shapely.geometry import Polygon
here = os.path.dirname(os.path.abspath(__file__))
border = json.load(open(os.path.join(here, 'border.json')))
q = Polygon(border[0]).buffer(0.01).simplify(0.01)
qpoly = [[round(x, 3), round(y, 3)] for x, y in q.exterior.coords]
html = open(os.path.join(here, 'app.html'), encoding='utf-8').read()
html = html.replace('__BORDER__', json.dumps(border, separators=(',', ':')))
html = html.replace('__QPOLY__', json.dumps(qpoly, separators=(',', ':')))
open(os.path.join(here, '..', 'kosova-izokrone.html'), 'w', encoding='utf-8').write(html)
