#!/usr/bin/env bash
# Netlify build: download OSM for Kosovo, build road graphs, write the site to dist/
set -euo pipefail
PBF="${PBF:-/tmp/kosovo.osm.pbf}"
python3 -m pip install -q osmium shapely numpy
if [ ! -s "$PBF" ]; then
  curl -fsSL --retry 4 -o "$PBF" https://download.geofabrik.de/europe/kosovo-latest.osm.pbf
fi
rm -rf dist && mkdir -p dist/data
python3 process.py "$PBF" border.json dist/data
echo "{\"osm_date\":\"$(date -u +%F)\"}" > dist/data/meta.json
python3 build_app.py dist/index.html
ls -la dist dist/data
