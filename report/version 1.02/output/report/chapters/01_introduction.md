# 1. Introduction

## 1.1 Purpose of the Report

This report supports government decision-makers in deciding which coal and other thermal power plant sites in Central, Eastern and Southern Europe merit further assessment for small modular reactor (SMR) deployment, using NuScale VOYGR-6 as the reference deployment envelope. It converts a broad regional site universe into a traceable shortlist of sites that may justify progression toward detailed site characterization under the staged siting logic described in IAEA SSG-35 [1], [6].

The report is a Stage 1 and Stage 2 decision-support document. It does not ask whether a site can be licensed, financed, procured, or built. It asks a narrower and more immediate question: among the candidate population available to this study, which sites appear sufficiently suitable and robust to justify further investigation?

The study combines regional site survey, structured screening, comparative evaluation, scoring, sensitivity analysis, and country-level interpretation. It uses a merged database built from deterministic data sources and curated LLM-assisted enrichment, then applies project scoring rules and generated audit artefacts to rank and explain site suitability [6]. The VOYGR-6 reference-case convention does not imply vendor selection, procurement intent, or host-country licensing acceptance.

## 1.2 Scope and Boundaries: IAEA Stages 1 and 2 Only

The IAEA siting process moves from regional survey to preferred-site selection, then to progressively more detailed characterization, pre-operational confirmation, and operational monitoring [1]. This report covers only the first two stages. Its purpose is to support a decision to progress selected sites toward Stage 3 characterization; it does not claim to complete Stage 3 or any later licensing-quality investigation.

| Stage | Name                  | Purpose in this report                                                                                           |
| ----- | --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1     | Site Survey           | Regional analysis, identification of potential sites, and screening to candidate sites.                          |
| 2     | Site Selection        | Evaluation, comparison, and ranking of candidate sites to identify preferred sites or shortlists.                |
| 3     | Site Characterization | Out of scope. Requires confirmatory site investigations, detailed characterization, and design-basis parameters. |
| 4     | Pre-operational       | Out of scope. Concerns confirmatory measurements and monitoring before operation.                                |
| 5     | Operational           | Out of scope. Concerns long-term monitoring and periodic safety review.                                          |

The project also follows the three-step procedural logic documented for SSG-35 §3.3: regional analysis identifies potential sites, screening narrows that population to candidate sites, and evaluation, comparison and ranking identify preferred sites [1], [6]. In this report, those steps are grouped under Stage 1 Site Survey and Stage 2 Site Selection. The internal mapping between this procedural logic and the project workflow is maintained in `report/requirements/04_siting_methodology.md` [6].

The data are suitable for Stage 1 and Stage 2 decision support. They support exclusion, comparison, ranking, and sensitivity-aware prioritisation. They do not establish design-basis ground motion, design-basis flood levels, licensing-quality geotechnical parameters, emergency plan approval, or final environmental acceptability under SSR-1 expectations for detailed site evaluation [2]. Where the analysis recommends a site for progression, that recommendation means support for a decision to progress toward Stage 3 characterization, not approval for construction.

## 1.3 Coal-to-Nuclear Transition Context

Coal-to-nuclear transition is relevant because coal and thermal power plant sites often concentrate assets that are difficult to recreate on greenfield land: industrial zoning, grid interconnections, cooling-water arrangements or permits, transport access, operating workforces, and communities already linked to power generation. These assets do not make a site suitable for nuclear deployment on their own. They explain why former or operating thermal sites are a rational starting point for a Stage 1 and Stage 2 screening study.

The U.S. Department of Energy frames coal-to-nuclear transition as a way to preserve and renew energy-community economic activity while replacing retiring coal generation with reliable, clean electricity [4]. DOE/INL analysis also identifies potential reuse value in existing transmission, cooling, roads, rail, land, and workforce relationships, while noting that each site still requires detailed technical, environmental, regulatory, and community review [4], [5].

For governments, the DOE guide highlights four practical questions that are directly relevant to this study [4]:

1. How much power should the new nuclear plant provide?
2. Should the replacement nuclear plant be built on the original coal site or nearby?
3. What existing coal plant infrastructure can be reused?
4. Can the project manage any gap between coal retirement and nuclear operation?

This report addresses those questions at screening resolution. It does not determine the commercial model, final vendor selection, financing structure, construction sequence, or local acceptance pathway. It identifies where existing coal-related assets and nuclear siting constraints appear to align well enough to support a decision to progress toward Stage 3 characterization.

## 1.4 Regulatory and Methodological Framework: IAEA, EPRI, and Project Alignment

The report uses IAEA safety standards as the primary nuclear siting framework and EPRI guidance as the practical bridge to advanced-nuclear screening and ranking. SSG-35 defines the site survey and site selection process used in this report, while SSR-1 provides the overarching site-evaluation requirements against which the project criteria are traced [1], [2], [6]. Supporting IAEA guides inform the treatment of seismic, meteorological, hydrological, volcanic, geotechnical, human-induced, radiological, and emergency-planning considerations [6].

EPRI's advanced nuclear siting guide is used where the IAEA framework needs practical translation into screening actions for advanced reactors. It distinguishes exclusionary screening, avoidance screening, suitability evaluation, and alternative-site ranking [3]. That sequence is consistent with the project workflow: regional analysis, screening of unsuitable sites, comparative evaluation, ranking, and sensitivity testing of candidate sites [6].

| Theme                 | IAEA framing                                                                                 | EPRI / industry framing                                                                                                                     | Project stance                                                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Process stage         | Site survey and site selection under SSG-35; progressive refinement toward characterization. | Pre-screening, exclusionary screening, avoidance screening, suitability evaluation, and ranking.                                            | Treat this report as Stage 1 and Stage 2 only; support a decision to progress shortlisted sites toward Stage 3 characterization.     |
| Criteria families     | Safety-related, nuclear security, and non-safety-related criteria.                           | Practical siting categories for advanced nuclear deployment, including footprint, cooling, grid, transport, and implementation constraints. | Organise evaluation around IAEA safety families, then add project viability criteria where they affect coal-to-nuclear practicality. |
| Exclusion and ranking | Exclusionary, discretionary, and ranking criteria.                                           | Exclusionary screening, avoidance screening, suitability evaluation, and alternative-site ranking.                                          | Use hard exclusionary logic and safety floors before ranking; then apply weighted scoring only to surviving site/SMR pairs.          |
| Level of evidence     | Increasing detail from survey to characterization.                                           | Screening and ranking are decision support before detailed engineering.                                                                     | Use API-primary and curated LLM-supported evidence for screening; defer field confirmation and design-basis values to Stage 3.       |
| Robustness            | Good siting practice requires awareness of uncertainty and assumptions.                      | Ranking should be tested for sensitivity to weights and assumptions.                                                                        | Use sensitivity profiles, swing weights, Monte Carlo score-band sampling, and threshold perturbations to test stability.             |

The SSR-1 traceability matrix maps project criteria to IAEA site-evaluation requirements and labels the coverage as full, partial, screening-only, or out of scope [6]. This prevents the screening study from overstating regulatory completeness. Some requirements are covered at screening resolution, some require detailed siting to close, and operational or programme-level obligations remain outside this report. Project-only criteria, such as grid connection, heavy-haul transport, workforce, regulatory environment, infrastructure reuse, and coal-to-nuclear synergy, are retained for ranking because they affect implementation feasibility, not because they replace SSR-1 safety requirements [6].

## 1.5 Data, Scoring, and Sensitivity Overview

The report relies on a merged evidence base that combines plant inventory data, spatial enrichment, hazard indicators, infrastructure indicators, country-level context, scoring outputs, and documented assumptions. The data architecture follows an API-primary and structured-data-first hierarchy: where authoritative datasets or first-party sources provide a value, those values take precedence; curated LLM-assisted enrichment is used only for targeted gaps and remains subject to provenance and quality controls [6].

At report scale, the methodology has four layers:

1. Candidate inventory: georeferenced coal and thermal power plant sites, with ownership, operational, grid, capacity, and country attributes where available.
2. Evidence enrichment: spatial, hazard, infrastructure, population, environmental, and socioeconomic fields from deterministic datasets and curated enrichment.
3. Merge and provenance: a single scoring dataset with source hierarchy, quality flags, and assumption tracking.
4. Evaluation: exclusionary checks, safety floors, ranking scores, composite ranking, and sensitivity analysis [6].

The scoring methodology translates heterogeneous evidence into screening outcomes. Sites or site/SMR pairs that trigger exclusionary conditions or safety-floor failures are excluded from composite ranking, while their raw evidence remains visible in the audit trail [6]. Surviving pairs retain a transparent 0-10 scoring trail and are compared using weighted scoring. This dual gate prevents a site with a material safety concern from being rescued by favourable non-safety attributes [6].

Sensitivity analysis tests whether ranking conclusions remain robust under reasonable changes in weights, score uncertainty, and thresholds. The suite includes one-at-a-time importance testing, category weight perturbations, swing-weight recalibration, Monte Carlo score-band sampling, threshold perturbation, country-balance diagnostics, and site stability banding [6]. These tests provide the uncertainty frame used throughout the results, country profiles, recommendations, and annexes.

NuScale VOYGR-6 remains the single reference deployment envelope for the main report. The scoring and sensitivity analysis are treated as the report's analytical basis for ranking, explaining uncertainty, and identifying which sites may support a decision to progress toward Stage 3 characterization.

| Criterion family                                   | Screening role                                                                                                                              | Main limitation at this stage                                                                | Treatment in this report                                                              |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Natural hazards                                    | Identify seismic, geotechnical, hydrological, meteorological, volcanic, and combined-hazard concerns.                                       | Desk-scale datasets do not replace site-specific hazard characterization.                    | Use for screening and ranking; recommend Stage 3 confirmation for shortlisted sites.  |
| Human-induced and nuclear-security-related hazards | Screen external hazards from aircraft, transport, industry, military, and related sources.                                                  | Public datasets may not capture all local hazardous activities or classified information.    | Treat as screening evidence; require local authority and operator confirmation later. |
| Radiological impact and emergency planning         | Assess dispersion proxies, population characteristics, evacuation feasibility, and special populations.                                     | Does not constitute a licensing emergency plan or dose assessment.                           | Use as comparative evidence; defer formal emergency planning to later stages.         |
| Non-safety and implementation criteria             | Capture grid, cooling, transport, land, ownership, infrastructure reuse, environmental sensitivity, workforce, and coal-to-nuclear synergy. | Several criteria are project viability factors rather than direct SSR-1 safety requirements. | Use for ranking and policy interpretation; disclose which criteria are project-only.  |
| Data provenance and assumptions                    | Explain source hierarchy, quality flags, and assumptions.                                                                                   | LLM-enriched and low-quality fields may have higher uncertainty.                             | Apply provenance controls, assumption register, and sensitivity testing.              |

## 1.6 Structure of the Report

The report is organised around the IAEA Stage 1 and Stage 2 logic. Chapter 2 presents the Stage 1 Site Survey: the study region, initial site universe, evidence base, eligibility checks, candidate identification, and Stage 1 limitations. Chapter 3 presents Stage 2 Site Selection: the evaluation framework, criterion families, scoring, sensitivity analysis, and shortlist rationale for the NuScale VOYGR-6 reference case.

Chapter 4 summarises regional and cross-country findings, including the main drivers of suitability, exclusion, and uncertainty. Chapter 5 provides alphabetically ordered country profiles for countries with at least one viable NuScale VOYGR-6 candidate, plus a consolidated treatment of failed countries or sites with reasons and measurable distance-to-threshold where available. Each country first lists relevant sites, then identifies the user-selected sites that receive detailed analysis. Chapter 6 sets out the investigations and confirmations needed to support a decision to progress toward Stage 3 characterization. Chapters 7 and 8 provide final remarks and references.

The annexes and methodology artefacts provide the technical backbone: SSR-1 traceability, exclusionary floors, scoring and sensitivity methods, failure-mode analysis, swing-weight audit, criterion-correlation diagnostics, the assumption register, and supporting regional and national sensitivity outputs.

A separate executive technical brief describes how the assessment system was created, including the broad process overview, API discovery and limitations, data acquisition and merge approach, data gaps, certainty by method, direct spend, actual human hours, equivalent human hours, token usage, database size, and further-development opportunities. That brief is a governance and audit summary, not a substitute for the client-facing technical chapters.

## Working References for the Introduction

1. IAEA, _Site Survey and Site Selection for Nuclear Installations_, Safety Standards Series No. SSG-35, Vienna (2015).
2. IAEA, _Site Evaluation for Nuclear Installations_, Safety Standards Series No. SSR-1 (Rev. 1), Vienna (2019).
3. EPRI, _Advanced Nuclear Technology: Site Selection and Evaluation Criteria for New Nuclear Energy Generation Facilities (Siting Guide) - 2022 Revision_, Report No. 3002023910, Palo Alto (2022).
4. DOE, _Coal-to-Nuclear Transitions: An Information Guide_, U.S. Department of Energy (2024). Local source: `sources/regulations/dos/Coal-to-Nuclear Transitions An Information Guide.pdf`.
5. DOE/INL, _Investigating Benefits and Challenges of Converting Retiring Coal Plants into Nuclear Plants_, INL/RPT-22-67964, Idaho Falls (2022).
6. Project methodology artefacts: `report/requirements/04_siting_methodology.md`, `report/methodology/ssr1_traceability.md`, `report/methodology/exclusionary_floors.md`, `report/methodology/sensitivity_analysis.md`, `report/methodology/swing_weight_audit.md`, and `report/methodology/assumption_register.md`.
