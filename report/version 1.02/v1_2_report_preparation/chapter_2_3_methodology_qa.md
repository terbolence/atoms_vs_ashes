<!-- man_hours: 1.2 -->
# Chapter 2 and 3 Methodology QA Note

## Scope

This note records the internal review basis for the version 1.2 Chapter 2 and Chapter 3 methodology rewrite. It is not reader-facing report prose.

## Evidence Used

| Evidence source | Use in rewrite |
| --- | --- |
| `/Users/terbolence/.cursor/plans/v1.2_full_report_writing_plan_5c7dbbf9.plan.md` | Section acceptance criteria, frozen runs, national sensitivity control and Step 6 scope. |
| `report/version 1.02/output/report/writing plan/writingDecisions.md` | Publication controls, Stage 1-2 boundary, NuScale VOYGR-6-only framing and national sensitivity language. |
| `report/version 1.02/output/report/writing plan/v1_2_iteration_controls.md` | Clean-output checks, evidence-source confidentiality and required final checks. |
| `report/version 1.02/output/report/writing plan/writingStyle.md` | WEO-style prose, positive direct phrasing and em-dash ban. |
| `report/version 1.02/methodology/exclusionary_floors.md` | Chapter 2 exclusionary-floor table and Stage 1 screening description. |
| `report/version 1.02/methodology/ssr1_traceability.md` | Chapter 3 IAEA safety-family framing. |
| `report/version 1.02/methodology/sensitivity_analysis.md` and `experts/scoring/national_sensitivity_report_author.md` | National sensitivity framing for Chapter 3.8. |
| `config/scoring_rubrics/*.yaml` | Criterion list, phase treatment and displayed baseline weights in Chapter 3 tables. |
| Local read-only scoring query against `score-2ffc8a70` | Published 16-country roster counts used in Chapter 2.2 and 2.5. |

## Section Review

| Section | Status | Review note |
| --- | --- | --- |
| 2.1 | Complete | Stage 1 is framed as survey and screening, distinct from Stage 2 ranking and Stage 3 characterization. |
| 2.2 | Complete | Published roster excludes Belarus and uses the frozen 16-country, 352-site count with country table. |
| 2.3 | Complete | Evidence sources are described qualitatively; upstream source names, connector names and model-process language were removed. |
| 2.4 | Complete | Screening logic and exclusionary floors are summarized from the generated floor artefact. |
| 2.5 | Complete | Candidate counts are anchored to the local frozen scoring query: 289 exclusionary-pass candidates, 28 clear of avoidance flags and 261 retained with avoidance flags. |
| 2.6 | Complete | Candidate descriptions separate facts, interpretation and data caveats. |
| 2.7 | Complete | Limitations keep Stage 1 at survey resolution and route unresolved issues to Stage 3. |
| 3.1 | Complete | Stage 2 is framed as comparative site selection and prioritisation only. |
| 3.2 | Complete | Family framework explains decision role without treating safety as a tradeable preference. |
| 3.3 | Complete | Safety-related criteria table shows baseline weights and gate/ranking treatment. |
| 3.4 | Complete | HI-01 and HI-06 reviewer-sensitive distinctions are reflected in public-facing language. |
| 3.5 | Complete | RI and EP criteria are framed as comparative indicators; EP-01 hard-floor role remains visible. |
| 3.6 | Complete | NS-05 distinguishes canonical site footprint from wider favourable-area context. |
| 3.7 | Complete | Dual gate logic is explicit before weighted composite ranking. |
| 3.8 | Complete | National sensitivity is the controlling frame; 50,000 iterations and seed 42 are stated without internal run IDs. |
| 3.9 | Drafted, unchecked | The rationale is coherent, but the named preferred-site table depends on Chapter 4 and Chapter 5 profile completion. Leave ToC unchecked until those surfaces agree. |
| 3.10 | Complete | Outputs and limitations preserve Stage 1-2 scope and reserve licensing suitability for Stage 3 and the national regulatory process. |

## Clean-Output Review

- Reader-facing Chapter 2 and Chapter 3 files were searched for unresolved placeholders, internal run IDs, upstream source names, model/process language, repository paths and em-dash characters.
- Chapter 2.3 uses qualitative evidence-source language only.
- Chapter 3.8 uses national sensitivity only for country and site selection language.
- Remaining cross-report dependency: Chapter 3.9 should receive a named preferred-site table only after Chapter 4 results and Chapter 5 selected-site profiles are aligned.
