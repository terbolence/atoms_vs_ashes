<!-- man_hours: 1.8 -->
# Version 1.2 Output Separation Manifest

## Purpose

This manifest separates the version 1.2 report outputs into the published copy and the internal audit copy. The published copy is the client-facing report surface. The internal audit copy preserves exact regeneration evidence, run identifiers, local paths, working notes, and process traceability.

## Published Copy

| Output class | Files | Publication treatment |
| --- | --- | --- |
| Main report chapters | `report/version 1.02/output/report/chapters/00_acronyms.md` through `08_references.md` | Included in the assembled report after local links, HTML comments, and internal identifiers are stripped by the build pipeline. |
| Chapter 5 country profiles | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/{AT,BA,BG,CZ,HR,HU,LV,MD,ME,MK,PL,RO,RS,SK,TR,UA}_country_prototype.md` | Included in alphabetical order. Belarus remains excluded from the published country profile sequence. |
| Chapter 5 selected-site profiles | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/sites/*.md` for the published country roster | Included by country order. Site profiles remain Stage 1-2 screening outputs and do not state licensing suitability. |
| Recommendation and failure sections | `recommended_top5_sites.md`; `consolidated_failure_section.md` | Included after country and site profiles. |
| Annexes | `report/version 1.02/output/report/annexes/annex_a_*.md` through `annex_f_*.md` | Included after Chapter 8. Annex F uses publication-safe artefact descriptions; exact paths and commands remain in the audit copy. |
| Static figures | PNG figures under `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/` | Published where referenced by the report source and available on disk. |
| Final assembled report | `report/version 1.02/output/report/build/atoms_vs_ashes_report.docx` | Client-facing export produced by the local report build pipeline. |

## Internal Audit Copy

| Output class | Files | Audit treatment |
| --- | --- | --- |
| Working controls and plans | `report/version 1.02/output/report/writing plan/`; `/Users/terbolence/.cursor/plans/v1.2_full_report_writing_plan_5c7dbbf9.plan.md` | Retained for process traceability and not included in the published report body. |
| Preparation and closure records | `report/version 1.02/v1_2_report_preparation/*.md` | Retained as the decision log for freeze gates, closure tracking, inherited-file audit, and output separation. |
| Audit logs and matrices | `audit/conversations/*.md`; `audit/feature_completion_matrices/*.md`; `audit/man_hours_registry.yml`; `audit/man_hours_summary.md` | Retained for QA and man-hours traceability. |
| Regeneration inputs | Country bundles, site bundles, CSV ledgers, and methodology artefacts | Retained for reproducibility and review. They are data evidence, not report prose. |
| Interactive map HTML | `report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures/*_site_status_map.html` | Audit-only. The published copy uses static PNG maps or omits unresolved image references. |
| Excluded or non-published country material | Belarus country profile and non-roster caveat plans | Audit-only unless the user explicitly restores them to the published roster. |
| Build intermediates | Merged markdown and reference templates under the build folder | Audit and production-control artefacts. The client-facing deliverable is the final assembled report. |

## Publication Rules Applied

The published copy must not contain internal run identifiers, local repository paths, command names, drafting notes, specialist placeholders, model-process language, unresolved TODO markers, or interactive map attribution. The build pipeline strips local markdown links and HTML comments from assembled manuscript text while keeping external public citations in the reference list.

## Open Control

Before client release, regenerate or rebuild the final DOCX after any text edit. The final exported file should be treated as publication-current only after the clean-output, numeric, and style checks pass on the rebuilt manuscript.
