<!-- man_hours: 1.0 -->
# Report Format Writing Controls

**Date:** 2026-05-18
**Session ID:** current Cursor session

## Objective

Mandate the new report-writing and formatting rules across the version 1.2 writing controls, the active full-report writing plan, and the DOCX export pipeline. Regenerate the requested sample exports so the user can inspect formatting.

## Key Decisions

- `report_format.json` remains the sole authoritative layout spec; `reference.docx` is generated from it and refreshed when the JSON hash changes.
- Reader-facing report text bans the Unicode em dash character U+2014, drafting notes, working references, repository paths, internal process language, and internal data-source names.
- Reader-facing citations use Harvard style and exclude the GEM database.
- Country and Chapter 4 results tables must use national sensitivity analysis, ranking order, scores, score bands, failed criteria, avoidance criteria, and measured threshold evidence where available.
- Tables require black borders on every cell side. The title page must include visible first-page content and the lower-left `Prepared for:` / `Contributors:` rubric.
- Belarus is excluded from the published analysis unless the user restores it.

## Files Changed

- `report/version 1.02/output/report/writing plan/report_format.json` - added publication rules, title-page rubric, and all-side table borders.
- `report/version 1.02/output/report/writing plan/writingStyle.md` - added direct-prose, no U+2014, Harvard citation, and no-internal-reference rules.
- `report/version 1.02/output/report/writing plan/writingDecisions.md` - added national sensitivity, country-ledger, source-confidentiality, map, citation, Chapter 1, Chapter 4, and conclusion rules.
- `report/version 1.02/output/report/writing plan/v1_2_iteration_controls.md` - added blocking publication gates and final checks.
- `report/version 1.02/output/report/writing plan/prompts/specialists/writing_quality_auditor.md` - aligned the reviewer checklist with the new rules.
- `/Users/terbolence/.cursor/plans/v1.2_full_report_writing_plan_5c7dbbf9.plan.md` - adapted the active plan to the new publication rules.
- `architecture/plans/v1-2-full-report-writing-plan.md` and `audit/plans/v1-2-full-report-writing-plan.md` - mirrored the updated plan.
- `scripts/report_format_config.py`, `scripts/make_reference_docx.py`, `scripts/build_report.py`, `scripts/export_markdown_docx.py`, and `scripts/report_docx_postprocess.py` - enforced generated reference templates and DOCX formatting.
- `tests/test_report_format_config.py` - added regression coverage for format settings, template rebuilds, and U+2014 absence in controls.
- `audit/feature_completion_matrices/2026-05-18_report_format_writing_controls.md` - recorded the user-visible export path.
- `pyproject.toml`, `.gitignore`, `audit/man_hours_registry.yml`, and `audit/man_hours_summary.md` - updated dependency, generated-template, and audit metadata.

## Outcome

Completed - the writing controls and active plan now mandate the requested rules. The three requested DOCX exports were regenerated in `report/version 1.02/output/report/build/format_samples/`, tests passed, and sample verification confirmed justified body text, bottom-centre page numbers, the first-page rubric, and all-side table borders.
