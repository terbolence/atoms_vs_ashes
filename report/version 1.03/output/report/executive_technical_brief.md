<!-- man_hours: 2.4 -->

# Executive Technical Brief

**Purpose.** This standalone brief explains how the Atoms vs Ashes assessment system was built, what it produced, and how executives should interpret the outputs. It is a governance and audit summary for programme owners. It does not replace the client-facing technical report.

**Analytical basis.** The brief is aligned with the report basis: NuScale VOYGR-6 as the single reference deployment envelope, a 352-record published site universe across 16 country profiles, and the project's 50,000-iteration national Monte Carlo sensitivity analysis for site-stability interpretation.

## 1. Objective and Scope of the Automated Assessment System

The system moves from a broad coal and thermal plant inventory to a transparent, sensitivity-aware set of national candidate sites for detailed Stage 3 characterisation consideration. It combines site identification, structured public-evidence collection, scoring, exclusionary screening, national sensitivity analysis, report generation, and human review.

The scope is deliberately bounded. The system supports IAEA SSG-35 Stage 1 and Stage 2 decisions: site survey, screening, comparison, ranking, and selection for detailed follow-up. It does not produce a licence application, design-basis site characterisation, vendor selection, investment decision, construction approval, or public-acceptance finding.

## 2. Process Used

The assessment workflow has seven steps:

1. Candidate site inventory for coal, lignite, gas, oil, and other thermal power plant locations.
2. Structured public-evidence collection for hazards, population, emergency planning, infrastructure, grid, cooling, land, environmental, ownership, and country context.
3. Reconciled evidence preparation with provenance, quality labels, assumptions, and explicit data-gap treatment.
4. Exclusionary screening and safety-floor checks for the NuScale VOYGR-6 reference case.
5. Weighted composite scoring for sites that remain eligible after the gates.
6. National sensitivity analysis to test rank stability within each country.
7. Country profiles, selected-site profiles, annexes, and final review passes to convert the scoring evidence into a decision-ready report.

The most important design choice is the separation between evidence and interpretation. Missing or low-quality evidence remains visible as a limitation or Stage 3 question. It is not converted into a hidden low score, and it is not treated as favourable by default.

## 3. Public-Evidence Collection and API Lessons

Structured public APIs, downloadable data products, national records, and geospatial evidence were preferred where they could support repeatable screening. They offered the strongest audit trail when responses carried stable identifiers, timestamps, source metadata, and clear null semantics.

The practical lesson is that API availability is uneven. Some services are highly structured but geographically incomplete; some provide excellent coverage for EU member states and weaker coverage outside the EU; others are useful for discovery but too coarse for a direct screening score. The system therefore treats API evidence as screening-grade unless the source, resolution, and quality flag justify a stronger interpretation.

Where structured evidence was unavailable, curated public-evidence collection filled targeted gaps. Those fields remain lower-confidence until confirmed through national-source review, owner/operator evidence, field measurement, or regulator engagement. This is appropriate for Stage 1 and Stage 2, but it must not be confused with Stage 3 evidence.

## 4. QA, Versioning, and Report Control

The report uses one analytical basis across the main chapters, Chapter 5 profiles, and annexes. The reader-facing report states the sensitivity basis as the project's 50,000-iteration national Monte Carlo sensitivity analysis and does not expose internal run identifiers. The internal audit copy preserves the exact artefact trail for reproducibility.

Quality control is organised around four checks. First, exclusionary gates and safety floors prevent unsuitable sites from entering composite ranking. Second, evidence-quality labels and assumption IDs preserve uncertainty. Third, national sensitivity analysis checks whether rankings are robust inside each country. Fourth, the writing and publication gates remove internal process language, stale sensitivity framing, and unsupported Stage 3 claims before assembly.

## 5. Operational Metrics

| Metric                                       |              Current value | Interpretation                                                                                                                                         |
| -------------------------------------------- | -------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Published country profiles                   |                         16 | Austria through Ukraine, alphabetical by ISO 3166-1 alpha-2 code.                                                                                      |
| Published site records in country ledgers    |                        352 | Main report site universe used in Chapters 2 and 4.                                                                                                    |
| Scored / ranked records                      |                        302 | Records with composite scores and national sensitivity bands in the published country ledgers (full-pass plus avoidance-flag entries).                 |
| Full-pass records                            |                         33 | Sites clearing both exclusionary and avoidance screens in the published country ledgers.                                                               |
| Avoidance-flag records                       |                        269 | Exclusionary-pass sites requiring issue-specific unlock work.                                                                                          |
| Hard-fail records in Chapter 4 evidence base |                         50 | Sites removed at the exclusionary screen across the 16 published country ledgers (consolidated no-pass countries are tracked separately in Chapter 5). |
| Sensitivity basis                            | 50,000 national iterations | National rank stability, not regional rank, controls country and site sequencing.                                                                      |
| Reference deployment envelope                |                    462 MWe | NuScale VOYGR-6 only.                                                                                                                                  |
| Tracked professional effort                  |         2,301 person-hours | Registry estimate for the full tracked project archive, not a timesheet.                                                                               |
| Written documentation                        |              153,348 lines | Equivalent to about 3,408 dense pages in the current tracked archive.                                                                                  |
| Python software                              |              185,040 lines | Screening, connectors, scoring, GUI, report generation, and supporting scripts.                                                                        |

Direct spend, hosted-model token usage, and external compute costs are not finalised in the tracked project artefacts available to this brief. They should be added from billing records before the brief is used for commercial or procurement reporting.

## 6. Certainty and Data Gaps

High-certainty fields are structured measurements or public institutional records with clear provenance and stable quality flags. Medium-certainty fields are screening proxies that support comparison but still need national or field confirmation. Lower-certainty fields are unavailable, unscored, low-quality, or dependent on public-evidence collection that requires human review.

The report handles uncertainty by carrying evidence coverage, score bands, national stability bands, residual-risk registers, and Stage 3 follow-up actions. This preserves confidence in the results because the report does not over-claim. It identifies which sites justify the next round of work and which questions that work must answer.

## 7. Further Development

The assessment framework can expand beyond coal and thermal plants to other large industrial sites with grid, water, transport, land, workforce, or redevelopment value. The same gates should apply: clear site universe, evidence hierarchy, exclusionary screening, weighted comparison, national sensitivity, residual-risk interpretation, and Stage 3 confirmation.

The highest-value next improvements are stronger national-source confirmation, richer ownership and land-control evidence, automated consistency checks for country-profile counts, and publication-grade figure governance. These improvements would increase confidence without changing the report's Stage 1 and Stage 2 claim boundary.
