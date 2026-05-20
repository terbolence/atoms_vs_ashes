<!-- man_hours: 0.5 -->
# V1.2 Build Deliverables Follow-Up

**Date:** 2026-05-20
**Session ID:** 5d2f12c3-776e-4f0c-99aa-81b6b6de79b7

## Objective

Update the stakeholder work-audit synthesis and results-table deliverable to explain why the requested list of CEE coal and thermal sites with power-export and surface-area indicators required a programmatic screening workflow.

## Key Decisions

- The results table now includes legacy installed capacity as a power-export proxy and screened site area as a surface-area indicator.
- Both generated Markdown deliverables explain that these indicators are useful only after exclusionary screening, avoidance checks, national scoring, sensitivity testing and map review.
- The prose states the limits of both indicators: legacy capacity does not confirm SMR export rights, and screened site area does not prove ownership, contiguous developable land, permitting status or final layout suitability.
- No online search, download or external API call was made.

## Files Changed

- `scripts/results_table_model.py` - added the shared results-table row model and column definitions.
- `scripts/results_table_data.py` - added power-export proxy, site surface area and process-explanation text to the generated results table.
- `scripts/build_work_audit_synthesis.py` - added the stakeholder-request and programmatic-workflow explanation to the generated synthesis.
- `tests/scripts/test_v1_2_build_deliverables.py` - extended scope tests for the new results-table columns.
- `audit/man_hours_registry.yml` - updated effort estimates for the new and edited files.
- `audit/man_hours_summary.md` - regenerated the project scale report.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.md` - regenerated source Markdown.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.csv` - regenerated source CSV with new columns.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.docx` - regenerated DOCX.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.md` - regenerated source Markdown.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.docx` - regenerated DOCX.

## Outcome

Completed - the deliverables now explain why a reliable stakeholder list required repeatable, programmatic processing, and the results table includes power-export and surface-area indicators.
