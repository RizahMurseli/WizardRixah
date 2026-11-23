# Sa larg arrin në Kosovë — me makinë / në këmbë

Animacion i izokroneve (si Chronotrains) për Kosovën, me të dhëna OpenStreetMap.

## Ndërtimi
```bash
pip install osmium shapely numpy
curl -o kosovo.osm.pbf https://download.geofabrik.de/europe/kosovo-latest.osm.pbf
cd kosova-izokrone
python process.py ../kosovo.osm.pbf border.json   # -> graph.bin.gz, places.json
python build.py 2026-11-23                          # -> ../kosova-izokrone.html
```
`border.json` është kufiri i Kosovës, nxjerrë nga `komunat.geojson` (Atlasi-urban-v26.zip).
