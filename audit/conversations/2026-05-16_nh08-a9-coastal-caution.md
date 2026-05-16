<!-- man_hours: 0.8 -->
# NH-08 A9 Coastal Caution

**Date:** 2026-05-16
**Session ID:** unavailable

## Objective

Implement the user decision for exactly one criterion: NH-08 / A9 coastal
flooding should be caution-oriented and report-facing rather than producing a
misleading pass/fail read when coast-distance evidence is missing.

## Key Decisions

- A9 remains an avoidance penalty whose triggered runtime verdict is
  `caution`, not a hard exclusion.
- Low-elevation, non-landlocked sites with missing `coast_distance_km` now
  trigger the A9 caution so missing coastal evidence is not treated as a
  clear screening pass.
- NH-08 uses explicit bands so high elevation and landlocked-country safe
  branches are preserved in compiled scoring instead of being shadowed by a
  distance-only recipe.
- A9 was removed from the single-metric threshold metadata surface until a
  compound coastal-flood threshold editor exists.

## Files Changed

- `config/scoring_specs/nh_natural_hazards.yaml` - implemented explicit NH-08
  bands and A9 missing-distance caution expression.
- `config/scoring_rubrics/nh_natural_hazards.yaml` - mirrored the NH-08
  caution policy in the legacy rubric.
- `config/scoring_specs/threshold_metadata.yaml` - removed the misleading
  single-distance A9 threshold control.
- `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md`
  - added report-writing instruction to surface unresolved NH-08 coastal
  limitations.
- `criteria/avoidance/NH-08_A9_coastal_flooding.md` - replaced the
  pre-decision analysis with final policy and report-description contract.
- `tests/scoring/test_threshold_band_runtime.py` - added focused NH-08
  regression coverage.

## Outcome

Completed - focused tests confirmed the compiled A9 expression, low-elevation
missing-distance caution behavior, and high-elevation / landlocked favourable
branches. Remaining risk is data-side: persisted `distance_to_coast_km` still
needs enrichment before NH-08 can make site-specific coastal-flood conclusions.
