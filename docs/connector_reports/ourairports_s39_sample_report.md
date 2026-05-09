# man_hours: 0.6
# HI-01 Aviation Proximity — OurAirports Connector Sample Report

**Connector slug:** `ourairports`
**Run date:** 2026-05-09 (SP-F scaffold landed; live re-run pending Sec.C consent)
**Criteria served:** HI-01 (Aviation A1-A4 avoidance + ranking)
**Scope:** 363 sites across 23 in-scope countries (+ border buffer)
**Sources:** [OurAirports](https://ourairports.com/data/) public-domain CSV dumps (`airports.csv`, `runways.csv`)

---

## Methodology

The connector is a download-based, in-memory spatial-index proximity service:

1. `airports.csv` (~10 MB) and `runways.csv` (~3 MB) are downloaded to `sources/ourairports/` on first run, then cached for `cache_ttl_days` (default 30).
2. `parse_airports_csv` filters the global airport set down to the 23 in-scope countries plus a 10-country border buffer (`ALL_RELEVANT_COUNTRIES`), drops `closed` / `balloonport` types and rows outside the project bounding box, and tags each surviving record with the IAEA NS-G-3.1 avoidance tier (A1-A4) via `AIRPORT_TYPE_TIER`.
3. `parse_runways_csv` joins runway records by `airport_ident`, selecting the **longest hard-surface** (asphalt / concrete / bitumen / paved / tarmac) runway per airport; falls back to the longest runway of any surface when no hard-surface runway exists. Length is normalised to metres (`length_m` if present, else `length_ft × 0.3048`).
4. `build_airport_index` constructs a Shapely `STRtree` of airport points; per-site queries use a deg-margin bounding box for candidate filter, then haversine distance for exact metres.
5. `compute_proximity_result` returns `AirportProximityResult` with the nearest airport (any class), per-tier nearest distances (large / medium / small), nearest flight-path proxy (heliport direct distance OR 0.5 × airport distance), avoidance violations against `AVOIDANCE_THRESHOLDS_KM`, and the new SP-F fields: `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`.

**Fair-use:** OurAirports CSVs are public-domain; no API key, no rate limit per their terms. Downloads are one-shot per cache TTL.

---

## Metric Legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| nearest_airport_km | km | Haversine to closest airport of any in-scope type within 100 km | No airport within 100 km |
| nearest_airport_name | text | Name of the nearest airport | nearest_airport_km is null |
| nearest_airport_type | text | Raw OurAirports type (e.g. `large_airport`, `heliport`) | nearest_airport_km is null |
| **nearest_airport_class** (SP-F) | text | Same as type for now; reserved for future taxonomy collapse (e.g. `large` / `medium` / `small` / `heliport`) | nearest_airport_km is null |
| **nearest_airport_runway_length_m** (SP-F) | m | Longest hard-surface runway at the nearest airport, from `runways.csv` | runways.csv missing OR airport has no runway entry OR no positive-length record |
| **nearest_airport_scheduled_service** (SP-F) | bool | True when nearest airport has `scheduled_service == "yes"` in airports.csv | nearest_airport_km is null |
| nearest_large_airport_km | km | Distance to nearest `large_airport` (A4 avoidance tier) | No large airport in radius |
| nearest_type2_airport_km | km | Distance to nearest `medium_airport` (A2 tier) | No medium airport in radius |
| nearest_small_airport_km | km | Distance to nearest `small_airport` / `seaplane_base` (A3 tier) | No small airport in radius |
| nearest_flight_path_km | km | min(nearest_heliport_km, 0.5 × nearest_airport_km) — flight-path corridor proxy | No airport / heliport in radius |
| airport_count | int | Count of airports within 30 km | Always populated; 0 means none |
| avoidance_violations | list[str] | A1-A4 codes violated against `AVOIDANCE_THRESHOLDS_KM` | Empty list when no violation |

## Quality Grade Legend

| Grade | Meaning |
|-------|---------|
| high (default) | At least one airport within the 100 km search radius |
| low | No airports within 100 km — flagged as data gap (unusual for in-scope geographies) |

## SP-F Status (2026-05-09)

- Parser + dataclass + DB-persist code landed (`hasattr` guards in `_persist_result` allow Alembic migration `042_hi01_hi06_classification_columns` to be applied at any time without code changes).
- Schema columns added in [`042_hi01_hi06_classification_columns`](../../src/alembic/versions/042_hi01_hi06_classification_columns.py): `nearest_airport_class`, `nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`.
- `--requery-nulls` flag now available on `scripts/run_p10_ourairports_batch.py` for HI-01 selective re-fetch.
- **Pending:** live download of `airports.csv` + `runways.csv` followed by H7 staged batch (smoke 3 → batch 20 → country → full 363) under `prompts/runAPIs.md` Sec.C card.
