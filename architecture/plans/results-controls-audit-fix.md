<!-- man_hours: 2.0 -->
---
name: results-controls-audit-fix
status: Completed
overview: Audit and fix Results-page controls whose labels are misleading or whose values are only partially wired, with emphasis on Failure Diagnostics and Avoidance Diagnostics. The plan keeps useful controls, removes or clarifies weak controls, and adds focused tests for the corrected filtering behavior.
todos:
  - id: audit-results-controls
    content: Audit Results-page controls and confirm keep/remove/fix decisions against actual code paths.
    status: completed
  - id: fix-failure-diagnostics-controls
    content: Update Failure Diagnostics so Top criteria filters Pareto too, near-only uses near_miss_gap_pct exactly, labels/help text are accurate, and recovery metric naming is consistent.
    status: completed
  - id: fix-avoidance-diagnostics-controls
    content: Apply the same control behavior and naming fixes to Avoidance Diagnostics.
    status: completed
  - id: add-control-helper-tests
    content: Add focused tests for top-N, near-only threshold, max-gap filtering, and recovery metric dataframe output in exclusion and avoidance diagnostics tests.
    status: completed
  - id: verify-results-controls
    content: Run focused tests, lints, and perform manual GUI verification checklist for both diagnostics tabs and Results tool/country controls.
    status: completed
isProject: false
---

# Results Controls Audit Fix

## Status: Completed (2026-05-14)

## Current Findings

- `[src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py](src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py)` and `[src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py](src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py)` both have the same control-shape issue: the controls are visually placed above all diagnostic outputs, but several only affect some outputs.
- `Top criteria` currently affects `_gap_df(...)` and `_unlock_df(...)`, but `_render_pareto(...)` ignores it and always renders every Pareto row.
- `Only <= X%` labels itself with `near_miss_gap_pct`, but `_gap_df(...)` hardcodes `25.0`; `_render_near_miss_table(...)` also uses `max(near_miss_gap_pct, 25.0)`, so a UI value of 15% can still show up to 25%.
- `Max gap shown (%)` only affects the gap distribution. That can be valid, but the label should be made explicit so it does not imply Pareto/unlock filtering.
- `Show site points` only affects the boxplot overlay. That is useful, but should keep help text explaining it only overlays the gap chart.
- `Unlock metric` in Failure Diagnostics and `Relaxation metric` in Avoidance Diagnostics control the same conceptual chart choice. Naming should be consistent.
- `[src/atoms_vs_ashes/gui/_results_page_main.py](src/atoms_vs_ashes/gui/_results_page_main.py)` tool radio is wired correctly. `[src/atoms_vs_ashes/gui/_results_run_picker.py](src/atoms_vs_ashes/gui/_results_run_picker.py)`, `[src/atoms_vs_ashes/gui/_results_country_focus.py](src/atoms_vs_ashes/gui/_results_country_focus.py)`, `[src/atoms_vs_ashes/gui/_results_render_stability.py](src/atoms_vs_ashes/gui/_results_render_stability.py)`, and `[src/atoms_vs_ashes/gui/_results_render_sens.py](src/atoms_vs_ashes/gui/_results_render_sens.py)` have direct control effects and are not removal candidates in this pass.

## Control Matrix

- `Run pool` / `Run` / `Show older runs` in `[src/atoms_vs_ashes/gui/_results_run_picker.py](src/atoms_vs_ashes/gui/_results_run_picker.py)`:
  - Decision: keep. They select the run universe and row cap; labels match behavior.
- `Country focus` in `[src/atoms_vs_ashes/gui/_results_country_focus.py](src/atoms_vs_ashes/gui/_results_country_focus.py)`:
  - Decision: keep. It is passed to Coverage/Sites/Diagnostics/Stability/Sensitivity paths.
- `Tool` radio in `[src/atoms_vs_ashes/gui/_results_page_main.py](src/atoms_vs_ashes/gui/_results_page_main.py)`:
  - Decision: keep. It switches active Results tool.
- `Include eliminated sites` in `[src/atoms_vs_ashes/gui/_results_country_focus.py](src/atoms_vs_ashes/gui/_results_country_focus.py)`:
  - Decision: keep. It only appears in Sites and directly filters Sites.
- `Top criteria` in diagnostics renderers:
  - Decision: keep, but make it filter the Pareto chart/table, gap distribution, and unlock/de-flag curve consistently.
- `Max gap shown (%)` in diagnostics renderers:
  - Decision: keep, but relabel to `Max gap shown in distribution (%)` or add matching help text; do not apply it to Pareto.
- `Only <= X%` in diagnostics renderers:
  - Decision: keep, but wire it to the actual `near_miss_gap_pct` everywhere and remove the hardcoded 25% fallback.
- `Show site points` in diagnostics renderers:
  - Decision: keep, with consistent help text saying it overlays points only on the gap distribution.
- `Unlock metric` / `Relaxation metric`:
  - Decision: keep, but rename consistently to `Recovery metric` in both tabs. Failure format labels: `Full site unlocks`, `Criterion failures resolved`. Avoidance format labels: `Sites de-flagged`, `Criterion flags resolved`.
- `Bands` in `[src/atoms_vs_ashes/gui/_results_render_stability.py](src/atoms_vs_ashes/gui/_results_render_stability.py)`:
  - Decision: keep. It filters the stability ledger directly.
- `Bundle section` in `[src/atoms_vs_ashes/gui/_results_render_sens.py](src/atoms_vs_ashes/gui/_results_render_sens.py)`:
  - Decision: keep. It switches the sensitivity metrics panel.

## Implementation Steps

1. Add small pure filter helpers to both diagnostics renderers, or one shared helper if it does not push files over 300 lines:
   - `pareto_df(diag, top_n)` returns only the top-N rows.
   - `gap_df(diag, top_n, max_gap, near_only, near_miss_gap_pct)` uses `near_miss_gap_pct`, not `25.0`.
   - `near_miss_rows(diag, near_miss_gap_pct)` uses the exact threshold and does not silently widen to 25%.
2. Update Failure Diagnostics in `[src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py](src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py)`:
   - Pass `top_n` into `_render_pareto(...)`.
   - Pass `near_miss_gap_pct` into `_render_gap_distribution(...)` and `_gap_df(...)`.
   - Rename or clarify `Max gap shown (%)`.
   - Rename `Unlock metric` to `Recovery metric`.
3. Update Avoidance Diagnostics in `[src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py](src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py)` with the same behavior and naming.
4. Add tests:
   - In `[tests/gui/test_results_exclusion_diag.py](tests/gui/test_results_exclusion_diag.py)`, cover top-N Pareto filtering, exact near-miss threshold filtering, max-gap filtering, and metric selection dataframe output.
   - In `[tests/gui/test_results_avoidance_diag.py](tests/gui/test_results_avoidance_diag.py)`, mirror equivalent tests for avoidance.
   - If Streamlit render functions remain hard to test, expose only pure helper functions under underscored names and test those.
5. Run verification:
   - `pytest tests/gui/test_results_exclusion_diag.py tests/gui/test_results_avoidance_diag.py -q`
   - `pytest tests/criterion_spec/test_preview_descriptor.py tests/scoring/test_ri04_no_exclusion.py -q` as a quick guard for the recently touched related work.
   - `ReadLints` on the edited diagnostics files.
6. Manual GUI verification after implementation:
   - Failure Diagnostics: changing `Top criteria`, `Only <= X%`, `Max gap shown`, `Show site points`, and `Recovery metric` visibly changes the intended chart/table.
   - Avoidance Diagnostics: same checks.
   - Country focus changes both diagnostics counts/charts.
   - Results tool selector still switches tabs correctly.

## Expected Result

The Results controls will be either clearly useful and functional or removed/clarified. Most importantly, the diagnostics controls will stop implying global effects they do not have, and the near-threshold filter will use the exact configured threshold.

## Execution Notes (2026-05-14)

- Extracted the small pure dataframe helpers (`pareto_df`, `gap_df`, `unlock_df`, `near_miss_rows`, `near_miss_df`, `unlock_steps`) into a new shared module `src/atoms_vs_ashes/gui/_results_render_diag_filters.py` so both diagnostics tabs use identical filter semantics and to keep both renderer files under the 300-line limit.
- Failure Diagnostics (`_results_render_exclusion_diag.py`):
  - `_render_pareto(diag, top_n)` now slices the Pareto dataframe to `top_n`.
  - `_render_gap_distribution(...)` accepts and forwards `near_miss_gap_pct` to `gap_df(...)`, removing the hardcoded `25.0` near-only fallback.
  - `_render_near_miss_table(...)` uses `near_miss_gap_pct` exactly (no `max(..., 25.0)` widening).
  - Relabeled `Max gap shown (%)` to `Max gap in distribution (%)` and added explicit scope help text.
  - Renamed `Unlock metric` to `Recovery metric` and added help text. Tightened `Show site points` and `Top criteria` help text.
- Avoidance Diagnostics (`_results_render_avoidance_diag.py`): identical fixes; `Relaxation metric` renamed to `Recovery metric`; format labels remain `Sites de-flagged` / `Criterion flags resolved`.
- Added focused tests in both `tests/gui/test_results_exclusion_diag.py` and `tests/gui/test_results_avoidance_diag.py` covering top-N Pareto truncation, exact near-miss threshold, max-gap capping, and recovery-metric column selection (`pareto_df`, `gap_df`, `unlock_df`, `near_miss_df`, `near_miss_rows`).
- Verification:
  - `pytest tests/gui/test_results_exclusion_diag.py tests/gui/test_results_avoidance_diag.py -q` → 20 passed.
  - `pytest tests/criterion_spec/test_preview_descriptor.py tests/scoring/test_ri04_no_exclusion.py -q` → 8 passed (related-work guard).
  - `ReadLints` on all touched files → clean.
- Manual GUI verification still owed to the user (Streamlit pure-helper tests cover the filter math; the GUI smoke check should confirm that each control visibly mutates only the documented charts).
