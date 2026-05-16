<!-- man_hours: 0.6 -->
# HI-01 Aircraft ABC Implementation

**Date:** 2026-05-16
**Session ID:** unavailable

## Objective
Implement the user-approved A+B+C decisions for exactly one avoidance criterion: `HI-01_A1-A4_aircraft_crash_hazard.md`.

## Key Decisions
- Implemented Option A by adding a completed-search NULL pass condition to A3 while preserving inconclusive behavior for missing HI-06 evidence.
- Implemented Option B by deriving class-specific large/medium/light airport distances in the scoring context without a DB migration.
- Implemented Option C by aligning A1/A4 avoidance hits with the HI-01 penalty bands so they no longer match the favourable small/GA/heliport band.

## Files Changed
- `config/scoring_specs/hi_human_induced.yaml` — updated HI-01 data anchors, bands, and A1-A4 fail conditions.
- `config/scoring_rubrics/hi_human_induced.yaml` — mirrored the HI-01 runtime rubric changes.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` — derived HI-01 class-specific airport distances from existing fields and connector comments.
- `tests/scoring/test_context_derivations.py` — added class-distance derivation regression tests.
- `tests/scoring/test_search_sentinel_bands.py` — added HI-01 A+B+C band and fail-condition regression tests.
- `criteria/avoidance/HI-01_A1-A4_aircraft_crash_hazard.md` — moved the audit note to final current state.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — updated effort metadata.

## Outcome
Completed — focused HI-01 unit tests passed and HI-01 spec/rubric parity was verified. Full compiler parity still reports unrelated pre-existing NH-08/NH-10 issues.
