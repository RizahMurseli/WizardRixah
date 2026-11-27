# Sa larg arrin në Kosovë — me makinë / në këmbë

Webmap në stilin e Chronotrains që animon sa larg arrin nga çdo pikë e Kosovës
**me makinë** (0–3 orë) ose **në këmbë** (0–12 orë), me të dhëna OpenStreetMap.

## Publikimi në Netlify
1. Netlify → **Add new site → Import an existing project → GitHub** → zgjidh `WizardRixah`.
2. Zgjidh degën (p.sh. `main` ose `ccr-1b0e3e25-gl14yy`). Cilësimet merren nga `netlify.toml`
   (base `kosova-izokrone`, komanda `bash netlify-build.sh`, publish `dist`).
3. **Deploy**. Ndërtimi shkarkon OSM për Kosovën nga Geofabrik, ndërton rrjetet rrugore dhe publikon faqen.
   Për të dhëna të reja: *Deploys → Trigger deploy*.

## Skedarët
- `app.html` – faqja (Leaflet + canvas; Dijkstra në shfletues).
- `process.py` – OSM `.pbf` → `data/car.bin.gz`, `data/walk.bin.gz`, `data/places.json`.
- `build_app.py` – fut kufirin (`border.json`, nga `komunat.geojson`) dhe krijon `dist/index.html`.
- `netlify-build.sh` – i gjithë ndërtimi.

Shpejtësitë: sipas klasës së rrugës ose `maxspeed` (makinë, me rrugë njëdrejtimëshe), 5 km/h (në këmbë); pa trafik.
