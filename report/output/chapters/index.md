# Report Chapters Index

This folder is the working terrain for the final report body. It mirrors the canonical ToC in [`../writing plan/tableOfContents.md`](../writing%20plan/tableOfContents.md), follows the drafting rules in [`../writing plan/writingDecisions.md`](../writing%20plan/writingDecisions.md), and is exempt from markdown line-count limits under the project rule for `report/output/**`.

## Chapter Files

| Chapter | File | Drafting status |
| --- | --- | --- |
| Acronyms and Abbreviations | [`00_acronyms.md`](00_acronyms.md) | Stub |
| 1. Introduction | [`01_introduction.md`](01_introduction.md) | Pointer to working draft; revise after results and country/site selections freeze |
| 2. Stage 1: Site Survey | [`02_stage_1_site_survey.md`](02_stage_1_site_survey.md) | Terrain stub |
| 3. Stage 2: Site Selection | [`03_stage_2_site_selection.md`](03_stage_2_site_selection.md) | Terrain stub |
| 4. Results and Findings | [`04_results_and_findings.md`](04_results_and_findings.md) | Terrain stub |
| 5. Country and Site Profiles | [`05_country_and_site_profiles.md`](05_country_and_site_profiles.md) | Terrain stub |
| 6. Recommendations for Detailed Site Evaluation | [`06_recommendations_for_detailed_site_evaluation.md`](06_recommendations_for_detailed_site_evaluation.md) | Terrain stub |
| 7. Final Remarks | [`07_final_remarks.md`](07_final_remarks.md) | Terrain stub |
| 8. References | [`08_references.md`](08_references.md) | Terrain stub |

## Supporting Outputs

- Annex terrain: [`../annexes/index.md`](../annexes/index.md)
- Executive technical brief: [`../executive_technical_brief.md`](../executive_technical_brief.md)
- Writing decisions: [`../writing plan/writingDecisions.md`](../writing%20plan/writingDecisions.md)
- Latest analytical anchor: `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md` / run ID `sens-7b609bd0`
- Existing report-output sensitivity pack pending alignment: [`../sensitivity/20260425b/00_regional_summary.md`](../sensitivity/20260425b/00_regional_summary.md)

## Drafting Rule

Use these files for section-by-section AI drafting with human review. Do not treat screening outputs as licensing conclusions; keep Stage 3 characterization, field confirmation, and regulator-facing approval outside the claim boundary.

## Splitting Rule

Keep a chapter as a single numbered markdown file while that remains easy to edit. If a chapter needs subchapter-level composition, replace the single chapter file with a same-numbered folder containing `00_index.md` and numbered subsection files, then update this index and the canonical ToC links.

Recommended first candidate for splitting: Chapter 5, using `05_country_and_site_profiles/00_index.md`, country files under `countries/`, and selected site profiles under `sites/`.
