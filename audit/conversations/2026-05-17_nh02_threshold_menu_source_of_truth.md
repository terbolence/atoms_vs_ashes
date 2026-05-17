<!-- man_hours: 0.6 -->
# NH-02 Threshold Menu Source Of Truth

**Date:** 2026-05-17
**Session ID:** Cursor chat

## Objective

Make the Site Selection Criteria `NH-02 / E1` threshold input the source of truth for compiled scoring behavior: if the menu says 8 km, the engine uses 8 km; if it says 5 km, the engine uses 5 km.

## Key Decisions

- Recipe-linked user-editable thresholds now resolve saved overrides first, then threshold metadata defaults, then static `band_recipe.score5_pivot` only as a fallback.
- `NH-02` spec defaults were aligned to the user-visible 8 km threshold so the stored template, GUI preview, generated bands, and hard E1 expression no longer disagree.
- The existing `score run --profile` path remains the runner contract; no new CLI flag or DB schema was required.

## Files Changed

- `config/scoring_specs/nh_natural_hazards.yaml` — aligned `NH-02` E1 default bands, hard expression, and fallback pivot to 8 km.
- `src/atoms_vs_ashes/criterion_spec/compiler.py` — made user-editable threshold metadata defaults drive recipe pivots before static fallbacks.
- `src/atoms_vs_ashes/criterion_spec/preview.py` — made preview `value` reflect the threshold default used by the compiler.
- `src/atoms_vs_ashes/criterion_spec/_excl_from_pivot.py` — updated documentation to describe the resolved user-visible pivot.
- `src/atoms_vs_ashes/gui/_threshold_editor_widgets.py` — made the differences table compare against the displayed preview value.
- `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` — updated default/override expectations for NH-02.
- `tests/criterion_spec/test_preview.py` — added preview coverage proving NH-02 menu value matches compiled bands and E1 expression.
- `tests/scoring/test_threshold_propagation.py` — updated propagation test to assert the visible default is 8 and an override can move it to 5.
- `tests/scoring/test_threshold_band_runtime.py` — added default-runtime coverage and updated override coverage for 5 km.
- `tests/scoring/test_compiler_parity.py` — updated NH-02 override coverage.
- `audit/feature_completion_matrices/2026-05-17_nh02_threshold_menu_source_of_truth.md` — recorded end-to-end surface trace and completion evidence.
- `architecture/plans/nh02_threshold_menu_source_of_truth.md` and `audit/plans/nh02_threshold_menu_source_of_truth.md` — mirrored the implementation plan and completion notes.
- `audit/man_hours_registry.yml` — updated cumulative effort estimates.

## Outcome

Completed — `NH-02 / E1` now compiles from the Site Selection Criteria threshold value. Focused NH-02 tests passed. A wider pre-existing focused-suite run still shows unrelated `NH-09` and broad spec/rubric parity failures.
