<!-- man_hours: 0.6 -->
# NS-02 A13 Grid Option A

**Date:** 2026-05-16
**Session ID:** Cursor subagent session (not available)

## Objective
Implement the user-approved Option A decision for exactly one avoidance criterion: NS-02 A13 grid connection.

## Key Decisions
- Option A was implemented as the threshold-consistency fix: the A13 predicate stays `grid_export_capacity_mw < 462`, and the capacity-margin score 5-6 band now begins at `grid_export_capacity_mw >= 462.0`.
- The default capacity ladder was mirrored into both the scoring spec and legacy rubric path so compiled and direct rubric loading agree for NS-02.
- NULL policy and legacy `BF-01` alias handling were left unchanged because they were outside the approved Option A scope.

## Files Changed
- `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` — aligned `capacity_margin` recipe bands to the A13 pivot.
- `config/scoring_specs/ns_non_safety.yaml` — added NS-02 Option A notes and default capacity bands.
- `config/scoring_rubrics/ns_non_safety.yaml` — mirrored NS-02 Option A notes and default capacity bands for legacy loading.
- `tests/criterion_spec/test_band_recipes.py` — updated the capacity recipe golden check.
- `tests/scoring/test_threshold_band_runtime.py` — added/updated NS-02 runtime boundary checks.
- `criteria/avoidance/NS-02_A13_grid_connection.md` — converted the decision note to implemented final state.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — updated project effort metadata.

## Outcome
Completed — focused NS-02 validation passed. A broader compiler parity run still reports unrelated `NH-08`/`NH-10` drift already present in the working tree and not part of this NS-02 implementation.
