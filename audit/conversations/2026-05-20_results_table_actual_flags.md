<!-- man_hours: 0.5 -->
# Results Table Actual Flags

**Date:** 2026-05-20
**Session ID:** 5d2f12c3-776e-4f0c-99aa-81b6b6de79b7

## Objective

Update the generated results-table deliverable so the avoidance / failure note column reports actual criterion flag codes instead of generic flag-exists wording.

## Key Decisions

- Extract avoidance and exclusionary flag codes from each site bundle's `screening.verdicts` where available.
- Use the failure-outcomes CSV as a fallback for hard-fail rows without a site bundle, including the Romania full-ledger hard-fail row.
- Preserve full-pass rows as `No avoidance or exclusionary flag recorded.`
- No online search, download or external API call was made.

## Files Changed

- `scripts/results_table_flags.py` - added bundle and failure-outcome flag extraction helpers.
- `scripts/results_table_data.py` - wired actual flag notes into generated table rows.
- `tests/scripts/test_v1_2_build_deliverables.py` - added assertions for actual avoidance and exclusionary flag codes.
- `audit/man_hours_registry.yml` - updated cumulative estimates for touched files.
- `audit/man_hours_summary.md` - regenerated the project scale report.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.md` - regenerated with actual flag codes.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.csv` - regenerated with actual flag codes.
- `report/version 1.02/output/report/build/atoms_vs_ashes_results_table.docx` - regenerated with actual flag codes.

## Outcome

Completed - validation confirmed actual criterion flags in Markdown, CSV and DOCX, including `Avoidance flags: NS-02` and `Exclusionary flags: EP-01, NH-05`.
