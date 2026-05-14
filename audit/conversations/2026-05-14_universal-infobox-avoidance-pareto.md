<!-- man_hours: 0.6 -->
# Universal Infobox And Avoidance Pareto

**Date:** 2026-05-14
**Session ID:** 1b151b74-03a6-476f-b887-0e3acb40fa90

## Objective
Implement the approved plan for universal criterion info popovers, avoidance diagnostics, RI-04 exclusion cleanup, and supporting audit/test coverage without editing the canonical plan file.

## Key Decisions
- RI-04 remains an avoidance/ranking criterion through A12; the `E_RI04` hard-exclusion condition and code-catalogue entry were removed.
- Criterion preview payloads now expose EPRI weight, IAEA/EPRI basis, fail-condition descriptors, and pass marks for all criteria and all fail/flag codes, including non-user-editable rules.
- Added a separate Avoidance Diagnostics results tool mirroring hard-fail diagnostics for caution verdicts.
- Documented the failure-root-cause finding: most suspicious NH-03/NH-04/NH-07/RI-04 hard failures came from safety-floor synthesis rather than direct E-code triggers.

## Files Changed
- `audit/post_processing/failure_diagnostics_20260514/REPORT.md` — diagnostic report for NH-02, NH-03, NH-04, NH-07, EP-01, and RI-04 failure mechanisms.
- `src/atoms_vs_ashes/criterion_spec/preview.py` — added descriptor, pass mark, EPRI weight, source-basis, and notes metadata to preview objects.
- `src/atoms_vs_ashes/gui/_criterion_info.py` — new shared renderer for universal criterion "?" infoboxes.
- `src/atoms_vs_ashes/gui/_criterion_preview_lookup.py` — cached result-side preview lookup for drawers.
- `src/atoms_vs_ashes/gui/_threshold_editor_widgets.py` — added criterion info popovers to threshold editor cards.
- `src/atoms_vs_ashes/gui/_results_render_drawer.py` — added criterion info popovers to failed/avoidance result cards.
- `src/atoms_vs_ashes/gui/_results_data_avoidance_diag.py` — new DB loader for avoidance diagnostic data.
- `src/atoms_vs_ashes/gui/_results_render_avoidance_diag.py` — new Avoidance Diagnostics tab renderer.
- `src/atoms_vs_ashes/gui/_results_page_main.py` — wired the new results-page tool.
- `config/scoring_rubrics/ri_radiological.yaml` and `config/scoring_specs/ri_radiological.yaml` — removed only `E_RI04`, kept `A12`, updated RI-04 notes, and cleaned duplicate YAML keys in the rubric mirror.
- `src/atoms_vs_ashes/scoring/_codes.py` — removed live `E_RI04` catalogue entry.
- `tests/criterion_spec/test_preview_descriptor.py`, `tests/gui/test_results_avoidance_diag.py`, `tests/scoring/test_ri04_no_exclusion.py` — added focused coverage.
- `architecture/plans/universal-infobox-avoidance-pareto-ri-04-fix.md` and `audit/plans/universal-infobox-avoidance-pareto-ri-04-fix.md` — mirrored completed plan with execution notes.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` — updated effort metadata for new/touched files.

## Outcome
Completed — all plan to-dos were implemented. Focused regression tests passed (`34 passed`), lints passed, and touched Python/Markdown files remain under repository line limits.
