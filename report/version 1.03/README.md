# Version 1.03 — Report Workspace

Working tree for the 1.03 report iteration. Folder layout mirrors **version 1.02** (which in turn evolved from 1.01). Version 1.03 is a surgical revision of the accepted version 1.02 report in response to the next round of Ovidiu Coman feedback; the v1.02 tree retains the full closure history of the prior round.

## Top level

| Path | Purpose |
| --- | --- |
| `methodology/` | Methodology memos, failure analysis, assumption register, sensitivity analysis, sites evaluation. |
| `requirements/` | Client requirements pack and coverage reports. |
| `sites_evaluation/` | Scoring process and criteria reference for report narrative and engine alignment. |
| `output/` | Generated and client-facing artefacts. |

## Output layout

| Path | Purpose |
| --- | --- |
| `output/report/` | Main report manuscript, annexes, build exports, writing controls, sensitivity packs, feedback. |
| `output/report/chapters/` | Numbered chapter files; Chapter 5 uses `05_country_and_site_profiles/` with `data/`, `figures/`, `sites/`. |
| `output/report/build/` | Pandoc merge, reference DOCX, side deliverables, format samples (regenerated for v1.03). |
| `output/report/writing plan/` | `report_format.json`, ToC, style/decision controls, prompts. |
| `output/report/feedback/` | Reviewer DOCX, extracted comments, synthesised triage. The current round's DOCX lives at `output/report/feedback/atoms_vs_ashes_report_feedback.docx`. |
| `output/sensitivity/` | National sensitivity export pack inherited from the v1.2 frozen analysis. |
| `output/sitesList/` | Sites-list deliverable workspace. |
| `output/workReport/` | Work-report deliverable workspace. |

## Baseline

The accepted version 1.02 report is the analytical baseline. Sections, country/site profiles, tables, charts, and annexes carry forward unchanged unless the new feedback round requires a surgical edit. Per-comment routing and the v1.03 closure register are managed through `output/report/feedback/synthesised_comments/` once the extractor has produced its pack. Shared repo assets (`report/regulations/`, `report/technology evaluation/`) stay at `report/` root unless a version-specific fork is required.

## Build configuration note

The build helper `scripts/report_format_config.py` still defaults to the v1.02 `report_format.json`. Until that default is parameterised, v1.03 builds must pass `--format "report/version 1.03/output/report/writing plan/report_format.json"` explicitly. This is logged in the v1.03 setup audit entry.
