<!-- man_hours: 0.7 -->
# NH-09 River Flooding Decision

**Date:** 2026-05-16
**Session ID:** unavailable

## Objective

Make and implement the best available-data decision for NH-09 / A11 river flooding using the local criterion documentation, scoring specs, source behavior, tests, and the report siting-expert prompt. Do not make live API or network calls and do not touch unrelated criteria.

## Key Decisions

- Use `flood_zone_class_500yr`, derived from local `flood_zone_class`, as the active Stage 1-2 NH-09 ranking evidence.
- Remove the NH-09 `band_recipe` so compiled runtime scoring uses the class-based bands already present in the spec/rubric.
- Remove NH-09/A11 from single-metric threshold metadata because `river_distance_km < X` cannot preserve the fixed `30.5 m` freeboard clause.
- Keep A11 as a static avoidance caution until `elevation_above_design_flood_m` is measured or derived.

## Files Changed

- `config/scoring_specs/nh_natural_hazards.yaml` - made NH-09 class-based bands authoritative and documented the static A11 rationale.
- `config/scoring_specs/threshold_metadata.yaml` - removed the NH-09/A11 single-metric threshold control.
- `tests/scoring/test_threshold_band_runtime.py` - added focused NH-09 runtime tests and removed NH-09 from recipe-pivot override expectations.
- `criteria/avoidance/NH-09_A11_river_flooding.md` - converted the pending sweep note into the final decision record.
- `criteria/ranking/NH-09 — River flooding.md` - aligned the ranking criterion note with the final NH-09 behavior.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` - updated required effort accounting.

## Outcome

Completed - NH-09 now uses the best local Stage 1-2 flood-zone evidence for ranking, while freeboard remains a Stage 3 hydrology follow-up and A11 remains a static compound caution.
