# City Isochrones vs GHSL

Interactive map comparing free-flow driving isochrones (30 / 60 / 90 min) from a city's centre with the
[Global Human Settlement Layer](https://human-settlement.emergency.copernicus.eu/) city definitions:

- **Urban Centre** (GHS-UCDB R2024A): the dense built-up core
- **Functional Urban Area** (GHS-FUA R2019A): the core plus its commuting zone

For each isochrone the page reports its area, the intersection-over-union (IoU) with each GHSL boundary,
the share of the GHSL area covered, and the share of the isochrone outside it. The hypothesis to test:
*is a ~1 hour isochrone a good approximation of a city?*

## Using it

1. Open the page (GitHub Pages link) or run it locally (below).
2. Paste your own **HERE API key** in the sidebar. It is stored only in your browser.
3. Search for any of the 11,422 GHSL urban centres. Click the map to move the origin.

### Getting a free HERE API key

1. Create an account at [platform.here.com](https://platform.here.com).
2. Go to **Access Manager → Apps → Register new app**.
3. Open the app → **Credentials** → **API Keys** → **Create API key**, and copy it.

The free plan includes Isoline Routing. Results are cached in your browser, so revisiting a city uses no quota.

## Running locally

```
python3 -m http.server 8000     # then open http://localhost:8000
```

On macOS you can double-click `start.command`. Optionally put your key in `config.js`
(see `config.example.js`); that file is git-ignored.

## Data and method

- Isochrones: HERE Isoline Routing API v8, `transportMode=car`, `departureTime=any` (no traffic),
  origin = GHSL urban-centre centroid.
- GHSL boundaries simplified at 100 m. Each 2024 urban centre is linked to the FUA containing its
  centroid (9,347 of 11,422 have one). Rebuild with `scripts/prepare_ghsl.py` after downloading the
  GHSL archives into `data/raw/`.
- Areas and overlaps computed geodesically with Turf.js.

Inspired by [mansueto-institute/urban-isolines](https://github.com/mansueto-institute/urban-isolines).
GHSL data © European Union, JRC. Map data © OpenStreetMap contributors.
