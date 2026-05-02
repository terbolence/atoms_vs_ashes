# 1. Introduction

## 1.1 Purpose of the Report

This report presents a screening-grade assessment of coal and other thermal power plant sites that could merit further consideration for small modular reactor (SMR) deployment. Its purpose is to support a decision-maker in moving from a broad regional site universe to a defensible shortlist of sites that may justify more detailed site evaluation.

The report is written as a Stage 1 and Stage 2 siting document in the sense used by IAEA SSG-35, _Site Survey and Site Selection for Nuclear Installations_. It is not a site licence application, a site characterization report, or a substitute for detailed investigations required for a construction or operating authorization. The analysis is intended to answer a narrower question: which sites, among the available candidate population, appear most suitable for progression toward detailed characterization?

The study combines regional site survey, structured screening, comparative evaluation, scoring, sensitivity analysis, and country-level interpretation. It uses a merged database built from deterministic data sources and curated LLM-assisted enrichment, then applies project scoring rules and generated audit artefacts to rank and explain site suitability.

## 1.2 Scope and Boundaries: IAEA Stages 1 and 2 Only

The IAEA siting process can be expressed as a staged progression from early survey to operational monitoring. This report covers only the first two stages.

| Stage | Name | Purpose in this report |
| --- | --- | --- |
| 1 | Site Survey | Regional analysis, identification of potential sites, and screening to candidate sites. |
| 2 | Site Selection | Evaluation, comparison, and ranking of candidate sites to identify preferred sites or shortlists. |
| 3 | Site Characterization | Out of scope. Requires confirmatory site investigations, detailed characterization, and design-basis parameters. |
| 4 | Pre-operational | Out of scope. Concerns confirmatory measurements and monitoring before operation. |
| 5 | Operational | Out of scope. Concerns long-term monitoring and periodic safety review. |

The project also follows the three-step procedural logic documented for SSG-35: regional analysis identifies potential sites, screening narrows that population to candidate sites, and evaluation/comparison/ranking identifies preferred sites. In this report, those procedural steps are grouped under Stage 1 Site Survey and Stage 2 Site Selection. The internal mapping between this procedural logic and the project workflow is maintained in `report/requirements/04_siting_methodology.md`.

The data are suitable for Stage 1 and Stage 2 decision support. They support exclusion, comparison, ranking, and sensitivity-aware prioritisation. They do not establish design-basis ground motion, design-basis flood, licensing-quality geotechnical parameters, emergency plan approval, or final environmental acceptability. Where the analysis recommends a site for progression, that recommendation means progression toward Stage 3 characterization, not approval for construction.

## 1.3 Coal-to-Nuclear Transition Context

Coal-to-nuclear transition is relevant because coal power plant communities often already contain several assets that matter for advanced nuclear deployment: industrial land, grid interconnections, cooling-water arrangements or permits, transport access, skilled operating and maintenance workforces, and local economic dependence on power generation.

The U.S. Department of Energy frames coal-to-nuclear transition as a way to preserve and renew energy-community economic activity while replacing retiring coal generation with reliable, clean electricity. DOE's _Coal-to-Nuclear Transitions: An Information Guide_ notes that coal plant retirement can create job, tax-revenue, and economic uncertainty, and that nuclear replacement can support additional long-term jobs, increased local income, increased revenue, and environmental improvement. It also emphasizes that advanced reactors and SMRs may be well suited to coal-plant replacement because they are available in varied sizes, have smaller physical footprints than traditional large reactors, can be more flexible, and may reuse elements of legacy infrastructure.

For utilities and governments, the DOE guide highlights four practical questions that are directly relevant to this study:

1. How much power should the new nuclear plant provide?
2. Should the replacement nuclear plant be built on the original coal site or nearby?
3. What existing coal plant infrastructure can be reused?
4. Can the project manage any gap between coal retirement and nuclear operation?

This report addresses these questions at screening resolution. It does not determine the commercial model, final vendor selection, financing structure, or construction sequence. It identifies where existing coal-related assets and nuclear siting constraints appear to align well enough to justify deeper investigation.

## 1.4 Regulatory and Methodological Framework: IAEA, EPRI, and Project Alignment

The report uses IAEA safety standards as the primary nuclear siting framework and EPRI guidance as a practical advanced-nuclear siting complement. The internal regulatory framework identifies SSG-35 as the primary procedural guide for site survey and site selection, SSR-1 as the overarching site-evaluation requirements framework, and supporting IAEA guides for seismic, meteorological, hydrological, volcanic, geotechnical, human-induced, radiological, and emergency-planning considerations.

EPRI's advanced nuclear siting framework is used as a practical bridge between IAEA terminology and the project scoring workflow. It distinguishes exclusionary screening, avoidance screening, suitability evaluation, and alternative-site ranking. This is consistent with the project's own workflow: broad regional analysis, screening of unsuitable sites, comparative evaluation, and ranking/sensitivity analysis of candidate sites.

| Theme | IAEA framing | EPRI / industry framing | Project stance |
| --- | --- | --- | --- |
| Process stage | Site survey and site selection under SSG-35; progressive refinement toward characterization. | Pre-screening, exclusionary screening, avoidance screening, suitability evaluation, and ranking. | Treat this report as Stage 1 and Stage 2 only; recommend Stage 3 work for shortlisted sites. |
| Criteria families | Safety-related, nuclear security, and non-safety-related criteria. | Practical siting categories for advanced nuclear deployment, including footprint, cooling, grid, transport, and implementation constraints. | Organise evaluation around IAEA safety families, then add project viability criteria where they affect coal-to-nuclear practicality. |
| Exclusion and ranking | Exclusionary, discretionary, and ranking criteria. | Exclusionary screening, avoidance screening, suitability evaluation, and alternative-site ranking. | Use hard exclusionary logic and safety floors before ranking; then apply weighted scoring only to surviving site/SMR pairs. |
| Level of evidence | Increasing detail from survey to characterization. | Screening and ranking are decision support before detailed engineering. | Use API-primary and curated LLM-supported evidence for screening; defer field confirmation and design-basis values to Stage 3. |
| Robustness | Good siting practice requires awareness of uncertainty and assumptions. | Ranking should be tested for sensitivity to weights and assumptions. | Use sensitivity profiles, swing weights, Monte Carlo score-band sampling, and threshold perturbations to test stability. |

The SSR-1 traceability matrix maps project criteria to IAEA site-evaluation requirements and labels the coverage as full, partial, screening-only, or out of scope. This matrix is important because it prevents the screening study from overstating its regulatory completeness. For example, some requirements are covered at screening resolution, some require detailed siting to close, and operational or programme-level obligations remain outside this report.

## 1.5 Data, Scoring, and Sensitivity Overview

The report relies on the latest merged database used by the scoring and sensitivity pipeline. The data architecture follows an API-primary / LLM-fallback hierarchy: where first-party APIs or structured open datasets provide a value, that value is authoritative; curated LLM-enriched values are used only where deterministic sources do not provide the required field. The scoring engine reads from the merged database, not directly from API-only or LLM-only source tables.

At report scale, the data methodology can be described in four layers:

1. Candidate inventory: georeferenced coal and thermal power plant sites, with ownership, operational, grid, capacity, and country attributes where available.
2. Evidence enrichment: spatial, hazard, infrastructure, population, environmental, and socioeconomic fields from deterministic datasets and curated enrichment.
3. Merge and provenance: a single merged scoring dataset with source hierarchy and run identifiers.
4. Evaluation: exclusionary checks, ranking scores, composite ranking, and sensitivity analysis.

The scoring methodology translates heterogeneous evidence into screening outcomes. Sites or site/SMR pairs that trigger exclusionary conditions or safety-floor failures are excluded from composite ranking. Surviving pairs retain a transparent 0-10 evidence trail and are then compared using weighted scoring. The exclusionary floors documentation explains the dual gate: hard E-codes and safety floors both prevent weak candidates from being rescued by unrelated favourable criteria.

Sensitivity analysis is used to test whether ranking conclusions are robust to reasonable changes in weights, score uncertainty, and thresholds. The sensitivity suite includes one-at-a-time importance, category weight perturbations, swing-weight recalibration, Monte Carlo score-band sampling, threshold perturbation, country-balance diagnostics, and site stability banding.

For the current analytical anchor, the report uses the latest 10,000-iteration Monte Carlo sensitivity audit: `audit/post_processing/06_scoring/20260502_sensitivity_mc_10000.md`, run ID `sens-7b609bd0`. The report is framed around NuScale VOYGR-6 as the only reference deployment envelope. The existing report-output sensitivity pack under `report/output/sensitivity/20260425b/` remains useful as a temporary drafting reference, but Chapter 4, Chapter 5, and this Introduction should not be finalised until the regional and national report-output packs are regenerated or aligned to the `20260502` run.

| Criterion family | Screening role | Main limitation at this stage | Treatment in this report |
| --- | --- | --- | --- |
| Natural hazards | Identify seismic, geotechnical, hydrological, meteorological, volcanic, and combined-hazard concerns. | Desk-scale datasets do not replace site-specific hazard characterization. | Use for screening and ranking; recommend Stage 3 confirmation for shortlisted sites. |
| Human-induced and nuclear-security-related hazards | Screen external hazards from aircraft, transport, industry, military, and related sources. | Public datasets may not capture all local hazardous activities or classified information. | Treat as screening evidence; require local authority and operator confirmation later. |
| Radiological impact and emergency planning | Assess dispersion proxies, population characteristics, evacuation feasibility, and special populations. | Does not constitute a licensing emergency plan or dose assessment. | Use as comparative evidence; defer formal emergency planning to later stages. |
| Non-safety and implementation criteria | Capture grid, cooling, transport, land, ownership, infrastructure reuse, environmental sensitivity, workforce, and coal-to-nuclear synergy. | Several criteria are project viability factors rather than direct SSR-1 safety requirements. | Use for ranking and policy interpretation; disclose which criteria are project-only. |
| Data provenance and assumptions | Explain source hierarchy, quality flags, and assumptions. | LLM-enriched and low-quality fields may have higher uncertainty. | Apply provenance controls, assumption register, and sensitivity testing. |

## 1.6 Structure of the Report

The report is organised to follow the IAEA Stage 1 and Stage 2 logic. Chapter 2 presents Stage 1 Site Survey: the study region, initial site universe, evidence base, eligibility checks, candidate identification, and Stage 1 limitations. Chapter 3 presents Stage 2 Site Selection: the evaluation framework, criterion families, scoring, sensitivity, and shortlist rationale for the NuScale VOYGR-6 reference case.

Chapter 4 summarises regional and cross-country findings, including the main drivers of suitability, exclusion, and uncertainty. Chapter 5 provides alphabetically ordered country profiles for countries with at least one viable NuScale VOYGR-6 candidate, plus a consolidated treatment of failed countries or sites with reasons and measurable distance-to-threshold where available. Each country first lists relevant sites briefly, then identifies the user-selected sites that receive detailed analysis. Chapter 6 recommends detailed Stage 3 investigations and identifies field-confirmation needs, regulatory follow-up, stakeholder follow-up, and prioritised next steps. Chapters 7 and 8 provide final remarks and references.

The annexes and methodology artefacts contain the reproducible technical backbone: SSR-1 traceability, exclusionary floors, scoring and sensitivity methods, failure-mode analysis, swing-weight audit, criterion-correlation diagnostics, the assumption register, and the generated regional and national sensitivity reports.

A separate executive technical brief should describe how the assessment system was created, including the broad process overview, API discovery and limitations, data acquisition and merge approach, data gaps, certainty by method, direct spend, actual human hours, equivalent human hours, token usage, database size, and further-development opportunities. That brief should be read as a governance and audit summary rather than as a replacement for the client-facing technical chapters.

## Working References for the Introduction

1. IAEA, _Site Survey and Site Selection for Nuclear Installations_, Safety Standards Series No. SSG-35, Vienna (2015).
2. IAEA, _Site Evaluation for Nuclear Installations_, Safety Standards Series No. SSR-1 (Rev. 1), Vienna (2019).
3. EPRI, _Advanced Nuclear Technology: Site Selection and Evaluation Criteria for New Nuclear Energy Generation Facilities (Siting Guide) - 2022 Revision_, Report No. 3002023910, Palo Alto (2022).
4. DOE, _Coal-to-Nuclear Transitions: An Information Guide_, U.S. Department of Energy (2024). Local source: `sources/regulations/dos/Coal-to-Nuclear Transitions An Information Guide.pdf`.
5. DOE/INL, _Investigating Benefits and Challenges of Converting Retiring Coal Plants into Nuclear Plants_, INL/RPT-22-67964, Idaho Falls (2022).
6. Project methodology artefacts: `report/requirements/04_siting_methodology.md`, `report/methodology/ssr1_traceability.md`, `report/methodology/exclusionary_floors.md`, `report/methodology/sensitivity_analysis.md`, `report/methodology/swing_weight_audit.md`, and `report/methodology/assumption_register.md`.
