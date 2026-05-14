<!-- man_hours: 0.6 -->
# Results Controls Audit Fix

**Date:** 2026-05-14
**Session ID:** 1b151b74-03a6-476f-b887-0e3acb40fa90

## Objective

Audit the Results-page controls (with focus on Failure Diagnostics and Avoidance Diagnostics) for misleading labels, partial wiring, and inconsistent naming, then implement a fix that makes each control's behavior match what its label promises.

## Key Decisions

- Keep all Results-page controls (Run pool / Run / Show older runs / Country focus / Tool radio / Include eliminated / Bands / Bundle section), and keep all five diagnostics controls — but fix or rewire them rather than removing any.
- Make `Top criteria` consistently filter the Pareto, gap distribution, unlock/de-flag curve, and near-miss table.
- Drop the silent widening of the near-threshold filter to 25% — `Only <= X%` and the near-miss review queue now use the exact configured `near_miss_gap_pct`.
- Relabel `Max gap shown (%)` to `Max gap in distribution (%)` and add help text saying it only affects the gap distribution.
- Standardise the unlock/de-flag radio under a single `Recovery metric` label across both tabs (format labels remain tab-specific: `Full site unlocks` / `Criterion failures resolved` for Failure Diagnostics, `Sites de-flagged` / `Criterion flags resolved` for Avoidance Diagnostics).
- Extract the small pure dataframe helpers into a shared `_results_render_diag_filters.py` module so both tabs use the same filter math and so the renderer files stay under the 300-line limit.

## Files Changed

- `src/atoms_vs_ashes/gui/_results_render_diag_filters.py` — new shared helper module providing `pareto_df`, `gap_df`, `unlock_df`, `near_miss_rows`, `near_miss_df`, and `unlock_steps`.
- `src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py` — Pareto, gap distribution, near-miss table, and controls now consume the shared helpers; `Top criteria` filters the Pareto, near-only uses exact threshold, recovery-metric label and help text added.
- `src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py` — same control behavior fixes as the failure tab; `Relaxation metric` renamed to `Recovery metric`.
- `tests/gui/test_results_exclusion_diag.py` — added focused helper tests for top-N Pareto, max-gap, exact near-miss, recovery-metric selection.
- `tests/gui/test_results_avoidance_diag.py` — mirror tests for the avoidance helper paths.
- `architecture/plans/results-controls-audit-fix.md` and `audit/plans/results-controls-audit-fix.md` — plan mirrors, marked `Status: Completed`.
- `audit/man_hours_registry.yml` — updated entries for the modified files and added entries for the new shared helper and exclusion test file.

## Outcome

Completed — automated verification: `pytest tests/gui/test_results_exclusion_diag.py tests/gui/test_results_avoidance_diag.py` 20 passed; `pytest tests/criterion_spec/test_preview_descriptor.py tests/scoring/test_ri04_no_exclusion.py` 8 passed (related-work guard); ReadLints clean on all touched files. Manual Streamlit GUI walkthrough of the diagnostics controls is still owed to the user before considering the visual verification step closed.
