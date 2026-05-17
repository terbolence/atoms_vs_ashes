<!-- man_hours: 0.8 -->
# S-38 Natural Earth Coast Distance

**Date:** 2026-05-17
**Plan:** `/Users/terbolence/.cursor/plans/natural-earth-coast-distance_8c1d28b8.plan.md`
**Scoring run:** `20260517T104618_459ae424`

## Objective

Implement S-38 Natural Earth as an offline coastline-distance source for
NH-08 so inland river sites such as Braila are distinguished from true
sea-coastal sites.

## Key Decisions

- User gave explicit consent for the one-time Natural Earth coastline download.
- The vendored source is Natural Earth 1:50m physical coastline, public domain,
  stored as `data/cartography/ne_50m_coastline.geojson`.
- `site_natural_hazards.distance_to_coast_km` remains the canonical persisted
  metric, with the existing scoring alias `coast_distance_km`.
- Missing coast distance no longer triggers A9 by itself; A9 now requires
  measured `<10 km` low-elevation exposure or positive storm-surge / tsunami
  proxy evidence.
- The existing merged DB was at Alembic `047`; migration `048` was applied so
  the scorer could load the current ORM model and refresh GUI-visible results.

## Validation

- S-38 dry-run coverage: 361/361 sites.
- Distance buckets: `<2`=49, `2-5`=27, `5-10`=6, `10-50`=36, `>50`=243.
- Anchor distances:
  - Braila power station: 81.043 km.
  - Porto Romano Power Station: 1.836 km.
  - Varna power station: 13.288 km.
- Targeted tests: `42 passed`.
- Refreshed merged scoring run: 361 sites, 8 SMRs, 138624 ranking rows, 63544
  verdict rows, 2888 composite rows.
- Braila latest NH-08 result: score `9.5`, A9 verdict `pass`, measured
  `{"coast_distance_km": 81.04, "elevation_m": 13.51}`.

## Files Changed

- `data/cartography/ne_50m_coastline.geojson` and `data/cartography/README.md`.
- `src/atoms_vs_ashes/connectors/natural_earth/`.
- `src/scripts/backfill_s38_coast_distance.py`.
- `config/scoring_specs/nh_natural_hazards.yaml`.
- `config/scoring_rubrics/nh_natural_hazards.yaml`.
- `criteria/avoidance/NH-08_A9_coastal_flooding.md`.
- `criteria/ranking/NH-08 — Coastal flooding storm surge and tsunami.md`.
- `tests/connectors/test_natural_earth_coastline.py`.
- `tests/scripts/test_backfill_s38_coast_distance.py`.
- `tests/scoring/test_threshold_band_runtime.py`.
- `tests/scoring/test_search_sentinel_bands.py`.
- `audit/feature_completion_matrices/2026-05-17_s38_natural_earth_coast_distance.md`.

## Outcome

Completed. NH-08 now consumes measured S-38 coast distance, the merged DB has
all 361 site distances populated, and the refreshed scoring run shows Braila
as a favourable inland NH-08 case with no A9 coastal flooding caution.
