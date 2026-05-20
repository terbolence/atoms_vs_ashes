<!-- man_hours: 1.0 -->
# v1.2 Chapter 4 Results Draft

**Date:** 2026-05-18
**Session ID:** v1.2 Chapter 4 parallel worker

## Objective
Rewrite Chapter 4 Results and Findings only for the version 1.2 full report, using frozen local report outputs and national sensitivity evidence while avoiding edits to Chapters 1-3, Chapter 5 profiles, Chapter 6, Chapter 7, and Chapter 8.

## Key Decisions
- Chapter 4 was rewritten from current local Chapter 5 country ledgers and consolidated failure-section evidence rather than preserving inherited v1.01/v1.02 regional-top-20 prose.
- During validation, sibling report work refreshed several country ledgers; Chapter 4 was updated again to the current on-disk counts before closeout.
- National sensitivity was used as the controlling frame; regional sensitivity and internal run identifiers were kept out of reader-facing Chapter 4 prose.
- Romania count reconciliation was handled explicitly: 23 country records, 22 scored records, three full-pass sites, 19 avoidance-flagged sites, and one hard fail.
- Missing evidence and hard-failed rows are described as limitations, hard failures, or `unscored / no measured basis`, never as invented low scores.

## Files Changed
- `report/version 1.02/output/report/chapters/04_results_and_findings.md` - rewritten Chapter 4 sections 4.1-4.6 with current counts, national sensitivity bands, candidate tables, driver tables, uncertainty treatment, and Stage 3 characterisation sequencing.
- `report/version 1.02/output/report/writing plan/tableOfContents.md` - marked Chapter 4 and subsections 4.1-4.6 complete.
- `/Users/terbolence/.cursor/plans/v1.2_full_report_writing_plan_5c7dbbf9.plan.md` - marked the Chapter 4 results task completed and added a progress note.
- `audit/feature_completion_matrices/2026-05-18_v1_2_report_writing.md` - updated the surface matrix and consumption check for the Chapter 4 report output.
- `audit/man_hours_registry.yml` - updated cumulative effort entries for the touched report, ToC, matrix, and audit log files.
- `audit/man_hours_summary.md` - regenerated from the man-hours registry.

## Outcome
Completed - Chapter 4 Results and Findings is drafted and locally scanned. The remaining blockers are whole-report review gates, final citation/reference integration, and cross-chapter numeric/publication lints that run after more chapters are assembled.
