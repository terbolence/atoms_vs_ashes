# man_hours: 0.5
# HI-06 Military Proximity — OSM Connector Sample Report

**Connector slug:** `osm` (`fetch_military_areas`) + `analysis/military_proximity.py`
**Run date:** 2026-05-09 (SP-F classifier landed; live re-run pending Sec.C consent)
**Criteria served:** HI-06 (Military installation proximity)
**Scope:** 363 sites across 23 in-scope countries
**Sources:** [OpenStreetMap Overpass API](https://overpass-api.de/api/interpreter) `military=*`, `landuse=military`, `aeroway=aerodrome` (when co-tagged military)

---

## Methodology

1. `OverpassClient.fetch_military_areas(lat, lon, radius_km=25)` issues a single Overpass QL query that pulls every node, way, and relation with `military=*` or `landuse=military` within 25 km of the site, returning their tags and centroid coordinates.
2. `analysis/military_proximity.py::classify_military_element` maps each element's tags onto the canonical 4-class HI-06 taxonomy:
   - `airfield` — `military=airfield`, or `aeroway=aerodrome|airfield` co-tagged with military land use
   - `depot` — `military` ∈ {`naval_base`, `ammunition`, `bunker`, `depot`, `danger_area`, `nuclear_explosion_site`}
   - `training_area` — `military` ∈ {`range`, `training_area`, `trench`}
   - `other` — `military` ∈ {`checkpoint`, `barracks`, `base`, `office`, `obstacle_course`}, or bare `landuse=military`
3. `assess_military_proximity` walks every classified element, computes haversine distance to the site, picks the nearest as `nearest_*` and the nearest member of `HIGH_CONSEQUENCE_CLASSES = {airfield, depot}` as `nearest_high_consequence_*`. The two distances diverge when a small `barracks` or `checkpoint` is closer than the actual blast / aviation hazard envelope — the high-consequence metric is what feeds A5/A6 thresholding.
4. `assess_and_persist` writes both metrics into `site_human_hazards` via `hasattr` guards: `nearest_military_class`, `nearest_high_consequence_military_km`, `nearest_high_consequence_military_class` (Alembic `042` adds the columns; legacy DBs without the migration silently skip the new fields).

**Fair-use:** Overpass tile server has hard rate limits (HTTP 429, 504). The `OverpassClient` honours `inter_request_delay_s` from `config/default.yml` and retries with exponential backoff + slot polling per LL-017 / LL-018.

---

## Metric Legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| nearest_military_km | km | Distance to closest military element of any class within 25 km | No military feature within 25 km |
| nearest_military_name | text | OSM `name` (or `operator`) of the nearest element | nearest_military_km is null OR element has no name tag (often the case for `landuse=military` polygons) |
| **nearest_military_class** (SP-F) | text | One of `airfield` / `depot` / `training_area` / `other` from `classify_military_element` | nearest_military_km is null |
| **nearest_high_consequence_military_km** (SP-F) | km | Distance to closest `airfield` or `depot` element within 25 km | No airfield / depot within 25 km |
| **nearest_high_consequence_military_class** (SP-F) | text | `airfield` or `depot` | nearest_high_consequence_military_km is null |
| military_count | int | Count of military elements (any class) within 25 km | Always populated; 0 = none |
| hi06_quality | text | `medium` when ≥ 1 element within radius, `low` when 0 (OSM under-coverage suspected) | — |

## SP-F Status (2026-05-09)

- 4-class taxonomy + high-consequence split landed in `analysis/military_proximity.py`.
- DB persistence via `hasattr` in `assess_and_persist` (no breakage if Alembic `042` not yet applied).
- `--requery-nulls` already wired in `scripts/run_fix04_osm_avoidance_batch.py::_needs_requery_military` (existing infrastructure; no further code change needed).
- Legacy `run_fix04_osm_avoidance_batch.py::_parse_military` still uses the older A5/A6 binary classification with raw SQL UPSERT; the modern `military_proximity.assess_and_persist` path is the canonical one for any new HI-06 enrichment runs and should be preferred for the SP-F re-enrichment batch.
- **Pending:** Overpass batch run under `prompts/runAPIs.md` Sec.C (~363 calls, ~12-20 min at 1 s inter-request, free academic tier, may hit 429 on dense regions).
