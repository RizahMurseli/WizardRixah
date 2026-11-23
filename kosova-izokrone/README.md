# Sa larg arrin në Kosovë — me makinë / në këmbë

Webmap (funksionon edhe si app në telefon) në stilin e Chronotrains: animon sa larg arrin nga çdo pikë e Kosovës
**me makinë** (0–3 orë) ose **në këmbë** (0–6 orë).

- Të dhënat rrugore merren **live nga OpenStreetMap** (Overpass API) në shfletues dhe ruhen në pajisje (IndexedDB, 30 ditë).
- Rrjeti rrugor ndërtohet dhe kohët llogariten (Dijkstra) në shfletues; makina respekton rrugët njëdrejtimëshe.
- Shpejtësitë: sipas klasës së rrugës ose `maxspeed` (makinë), 5 km/h (në këmbë), pa trafik.

Faqja e gatshme: `../kosova-izokrone.html` (një skedar i vetëm).

## Ndërtimi
`app.html` është burimi; `build_app.py` fut kufirin e Kosovës (`border.json`, nga `komunat.geojson`) dhe krijon `../kosova-izokrone.html`:
```bash
pip install shapely
python kosova-izokrone/build_app.py
```
