<!-- man_hours: 0.9 -->
# V1.2 Build Deliverables

**Date:** 2026-05-20
**Session ID:** 5d2f12c3-776e-4f0c-99aa-81b6b6de79b7

## Objective

Implement the V1.2 Build Deliverables Plan without editing the plan file itself. Add the two missing side deliverables: an A4 landscape results-table DOCX and a concise stakeholder work-audit synthesis DOCX, with expert prompts, build wiring, validation, and audit closure.

## Key Decisions

- The results table is generated from the v1.2 country ledgers with country scope enforced in code: 16 published countries plus AL/SI/XK as no-pass portfolios; Belarus remains excluded from the published deliverable.
- Romania is handled as a coded full-ledger exception, producing all 23 Romanian rows instead of a top-five extract.
- Country status maps are copied into build-folder assets and embedded where available; AL/SI/XK are listed without maps because no country map exists for those no-pass sections.
- The stakeholder synthesis is built from local sources only: man-hours summary, current country ledgers, executive-brief boundary language, and the three new expert viewpoint prompts. No online search, download, or external API call was made.
- `scripts/build_report.py --side-deliverables-only` now generates only the two side deliverables; normal report builds can also generate them unless `--skip-side-deliverables` is used.

## Files Changed

- `audit/feature_completion_matrices/2026-05-20_v1_2_build_deliverables.md` - opened and closed the supplemental Feature Completion Matrix with validation trace.
- `experts/report/stakeholder_nuclear_engineering_expert.md` - added nuclear engineering stakeholder prompt.
- `experts/report/stakeholder_energy_transition_expert.md` - added energy-transition and net-zero stakeholder prompt.
- `experts/report/stakeholder_management_consultant.md` - added management-consultant stakeholder prompt.
- `scripts/build_report.py` - added side-deliverables CLI wiring and split section discovery into a helper.
- `scripts/report_section_discovery.py` - moved report section discovery out of the main build script.
- `scripts/report_side_deliverables.py` - added the shared dispatcher for the two side deliverables.
- `scripts/build_results_table_deliverable.py` - added the results-table DOCX builder and A4 landscape post-processing.
- `scripts/results_table_data.py` - added results-table country scope, ledger selection, map copying, Markdown rendering, and CSV trace output.
- `scripts/build_work_audit_synthesis.py` - added stakeholder synthesis Markdown and DOCX generator.
- `tests/scripts/test_v1_2_build_deliverables.py` - added entry-point and scope tests for side deliverables.
- `audit/man_hours_registry.yml` - updated cumulative estimates for new and edited files.
- `audit/man_hours_summary.md` - regenerated the project scale report after registry update.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.md` - generated supporting Markdown.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.csv` - generated supporting CSV trace.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.docx` - generated A4 landscape results table.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.md` - generated supporting Markdown.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.docx` - generated stakeholder work-audit synthesis.

## Validation

- `python -m py_compile scripts/build_report.py scripts/report_section_discovery.py scripts/report_side_deliverables.py scripts/build_results_table_deliverable.py scripts/results_table_data.py scripts/build_work_audit_synthesis.py tests/scripts/test_v1_2_build_deliverables.py`
- `python -m pytest tests/scripts/test_v1_2_build_deliverables.py tests/test_report_format_config.py` - 7 passed.
- `python scripts/build_report.py --side-deliverables-only` - wrote both side deliverable DOCX files.
- Custom CSV/XML clean-output validation passed: 16 published countries, 80 selected rows, 23 Romania rows, AL/SI/XK listed, 16 maps copied, results DOCX landscape orientation present, table autofit and black borders present, and no internal paths, run IDs, stale sensitivity wording, placeholders, or em dash in generated Markdown.

## Outcome

Completed - all plan to-dos were implemented and validated. The final Feature Completion Matrix trace is:

```text
CLI: scripts/build_report.py --side-deliverables-only
  -> scripts/report_side_deliverables.py
  -> scripts/build_results_table_deliverable.py + scripts/results_table_data.py + scripts/build_work_audit_synthesis.py
  -> country/site ledgers + figures/*_site_status_map.png + audit/man_hours_summary.md + experts/report/stakeholder_*.md
  -> report/version 1.02/output/report/build/atoms_vs_ashes_results_table.docx + atoms_vs_ashes_work_audit_synthesis.docx
Validation: py_compile, pytest focused suite, side-deliverables build, CSV/XML/clean-output checks passed on 2026-05-20
```
