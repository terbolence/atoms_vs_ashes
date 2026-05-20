<!-- man_hours: 1.8 -->
# Expert Prompt Inventory for Version 1.2 Report Writing

## Purpose

This note records how the `experts/` library is used in the version 1.2 report-writing campaign. It supports the controlling plan's requirement to make use of the expert library without forcing connector or live-API prompts into reader-facing drafting tasks where they do not apply.

## Applicable Report Roles

| Expert prompt | Use in the version 1.2 report campaign | Report surface |
| --- | --- | --- |
| `experts/report/stage_methodology_author.md` | Primary methodology author for Stage 1 and Stage 2 narrative. | Chapters 2 and 3; methodology annex links. |
| `experts/report/introduction_author.md` | Introduction author after results, country profiles, and recommendations are stable. | Chapter 1. |
| `experts/report/site_describer.md` | Secondary site-narrative reviewer where a bundle-rendered profile needs prose polish. | Chapter 5 selected site profiles. |
| `experts/scoring/national_sensitivity_report_author.md` | National rank, Monte Carlo bracket, shortlist robustness, and stability interpretation. | Chapters 3, 4, 5; Annex C. |
| `experts/scoring/suitable_sites_scoring_audit.md` | Checks whether suitability and survivor claims follow from the scoring evidence. | Chapter 4, Chapter 5, Ovidiu closure review. |
| `experts/scoring/scoring_criterion_review.md` | Criterion-sensitive review when a report claim depends on recently changed or reviewer-sensitive logic. | HI-01, HI-06, NH-11, EP-01, RI-04, RI-05, NS-02, NS-05 surfaces. |
| `experts/scoring/criterion_matrix_author.md` | Criterion-level explanation and traceability matrix support. | Annex A, Annex B, criterion-weight surfaces. |
| `experts/quality/siting_expert.md` | Domain review of evidence quality, siting interpretation, and Stage 1-2 scope discipline. | Whole-report review, Chapter 5 batch review. |
| `experts/quality/auditor.md` | Final conformance, traceability, feature-surface, and audit review. | Step 8 review sequence and final self-audit. |
| `experts/quality/lessons_learned.md` | Lessons check before final QA so known defects are not reintroduced. | Whole-report review and QA notes. |
| `experts/quality/data_science_siting_curator.md` | Data-quality review where a numeric claim depends on measured-field distributions or proxy evidence. | Chapters 3, 4, 5; Annex E. |
| `experts/assessment/database_fusion.md` | Database-fusion review when a claim depends on merged evidence from several domain tables. | Country/site profiles and Chapter 4 evidence notes. |

## Report-Specific Prompt Roles Outside `experts/`

| Prompt | Use in the version 1.2 report campaign | Report surface |
| --- | --- | --- |
| `report/version 1.02/output/report/writing plan/prompts/country_profile_author.md` | Primary country-profile scaffold author from country bundles. | Chapter 5 country profiles. |
| `report/version 1.02/output/report/writing plan/prompts/site_profile_author.md` | Primary selected-site profile scaffold author from site bundles. | Chapter 5 selected site profiles. |
| `report/version 1.02/output/report/writing plan/prompts/specialists/siting_expert.md` | Consolidated specialist fill voice for country executive, family interpretation, residual risk, and stability placeholders. | Chapter 5 specialist blocks. |
| `report/version 1.02/output/report/writing plan/prompts/specialists/writing_quality_auditor.md` | Binding publication-readiness review prompt. | Whole-report review after drafting and specialist fill. |

## Conditional or Non-Applicable Expert Roles

| Expert prompt | Current status | Reason |
| --- | --- | --- |
| `experts/connectors/api_enrichment_operations.md` | Not applicable in current tranche. | No enrichment or live API operation is being run. Any future use requires explicit consent for the service, call scope, and data exposure. |
| `experts/connectors/data_sources_integrations.md` | Conditional. | Use only if a report gap becomes a source-integration design task, not for prose drafting. |
| `experts/connectors/database_audit.md` | Conditional. | Use only if report claims require a database integrity audit beyond existing generated artefacts. |
| `experts/connectors/site_area_web_search.md` | Not applicable without consent. | Web search and external data retrieval are prohibited without explicit user consent. |
| `experts/connectors/software_architect.md` | Conditional. | Use for pipeline or renderer architecture changes, not for current markdown gate artefacts. |
| `experts/connectors/senior_software_engineer.md` | Conditional. | Use if the campaign requires code changes to renderers, exporters, or lints. |

## Chapter and Gate Assignment

| Campaign unit | Required expert prompts |
| --- | --- |
| Pre-flight and freeze gate | `experts/quality/auditor.md`; `experts/quality/lessons_learned.md`; `experts/scoring/national_sensitivity_report_author.md`. |
| Ovidiu closure register | `experts/quality/auditor.md`; `experts/scoring/suitable_sites_scoring_audit.md`; `experts/scoring/scoring_criterion_review.md`; `experts/quality/siting_expert.md`. |
| Chapter 4 | `experts/report/stage_methodology_author.md`; `experts/scoring/national_sensitivity_report_author.md`; `experts/scoring/suitable_sites_scoring_audit.md`. |
| Chapters 2 and 3 | `experts/report/stage_methodology_author.md`; `experts/scoring/criterion_matrix_author.md`; `experts/scoring/scoring_criterion_review.md` for sensitive criteria. |
| Chapter 5 | Country and site author prompts under `writing plan/prompts/`; `experts/report/site_describer.md`; consolidated and family/criterion specialist prompts; `experts/quality/siting_expert.md`. |
| Chapter 6 | Selected-site residual risks plus `experts/quality/siting_expert.md` and `experts/quality/auditor.md`; no dedicated `experts/report_recommendations_author.md` file exists in this repository snapshot. |
| Chapter 1 | `experts/report/introduction_author.md` after results and recommendations are stable. |
| Chapter 7 | `experts/quality/siting_expert.md` and `experts/quality/auditor.md`; no new facts. |
| Chapter 8 | Harvard reference compilation governed by writing controls and writing-quality auditor. |
| Annexes A-F | `experts/scoring/criterion_matrix_author.md`; `experts/scoring/national_sensitivity_report_author.md`; `experts/scoring/suitable_sites_scoring_audit.md`; `experts/quality/data_science_siting_curator.md` where data limitations are discussed. |

## Working Notes

- The expert inventory contains 18 Markdown prompts. Report drafting primarily uses report, scoring, quality, and assessment prompts.
- Connector prompts are not ignored; they are explicitly parked until the task becomes connector design, database audit, renderer code, or consented enrichment.
- No external web, live API, or paid model calls are authorised by this note.
