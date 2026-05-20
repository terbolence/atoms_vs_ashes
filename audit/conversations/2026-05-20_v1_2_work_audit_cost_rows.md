<!-- man_hours: 0.3 -->
# V1.2 Work Audit Cost Rows

**Date:** 2026-05-20
**Session ID:** 5d2f12c3-776e-4f0c-99aa-81b6b6de79b7

## Objective

Add three stakeholder-requested rows to the work-audit synthesis effort table: actual man-days, supplementary days and cash spent.

## Key Decisions

- Added the rows through `scripts/build_work_audit_synthesis.py` so the values persist across future rebuilds.
- Used client-facing spelling and formatting: `Actual man-days`, `Supplementary days`, and `Cash spent`.
- No online search, download or external API call was made.

## Files Changed

- `scripts/build_work_audit_synthesis.py` - added three effort/cost rows to the generated table.
- `audit/man_hours_registry.yml` - updated the cumulative effort estimate for the generator.
- `audit/man_hours_summary.md` - regenerated the project scale report.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.md` - regenerated source Markdown.
- `report/version 1.02/output/report/build/atoms_vs_ashes_work_audit_synthesis.docx` - regenerated DOCX.

## Outcome

Completed - validation confirmed the new rows are present in Markdown and DOCX and that table layout and clean-output checks still pass.
