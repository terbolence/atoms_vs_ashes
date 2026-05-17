# 2. Stage 1: Site Survey

This chapter explains how the study moves from the initial site universe to candidate sites suitable for Stage 2 comparison. It should stay at screening resolution and should not duplicate detailed criteria tables from methodology artefacts.

## 2.1 Objectives of the Site Survey Stage

The objective of Stage 1 is to move from a broad regional inventory of coal and thermal power plant sites to a defined candidate population for Stage 2 comparison. In IAEA SSG-35 terms, this is the site survey stage: regional analysis, identification of potential sites, and screening to candidate sites [1]. It is not the point at which site suitability is confirmed.

For this report, Stage 1 has three practical outputs. First, it defines the study region and the types of sites that are eligible for consideration. Second, it creates a georeferenced site universe with enough plant, location, ownership, grid, cooling, environmental, and hazard context to support structured screening [6]. Third, it records the main data limitations so that Stage 2 rankings are interpreted as screening evidence, not as design-basis conclusions.

The Stage 1 process therefore serves a control function. It prevents the later scoring and sensitivity analysis from comparing sites that are poorly identified, outside the intended geography, or unsupported by the minimum evidence needed for a defensible screening study. It also separates data-readiness issues from genuine siting concerns, which is essential for deciding whether a weak result reflects a poor site, a missing dataset, or a question that must be deferred to Stage 3 characterization.

## 2.2 Study Region and Initial Site Universe

The study region covers Central, Eastern and Southern Europe as defined for the project scope. The in-scope country set is Austria, Bosnia and Herzegovina, Bulgaria, Belarus, Czechia, Croatia, Hungary, Latvia, Moldova, Montenegro, North Macedonia, Poland, Romania, Serbia, Slovakia, Turkey, and Ukraine [7]. Other countries are outside the report boundary and are not included in the regional ranking.

The initial site universe contains 363 georeferenced sites [7]. It is built primarily from coal and lignite power plant records, supplemented where the project scope identifies other thermal or industrial power plant sites that may be relevant to coal-to-nuclear or thermal-site reuse [6]. At this stage, inclusion in the universe means only that a site is relevant enough to enter screening. It does not mean the site is viable, preferred, available, or acceptable for nuclear deployment.

| Scope element        | Treatment in Stage 1                                                                                              | Reporting implication                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Geography            | Seventeen-country study area in Central, Eastern and Southern Europe.                                             | Rankings and country profiles do not claim completeness outside this region.           |
| Site type            | Coal, lignite, and relevant thermal power plant sites, plus project-designated additional sites where applicable. | The study starts from reuse potential, not from a blank-map greenfield search.         |
| Site geometry        | One representative site coordinate is used for screening measurements.                                            | Distances and buffers are screening proxies; Stage 3 must use actual site layouts [7]. |
| Reference technology | NuScale VOYGR-6 is used as the single reference deployment envelope.                                              | Results compare sites against one consistent SMR case, not across vendor alternatives. |

## 2.3 Data Acquisition and Evidence Base

Stage 1 uses a layered evidence base. Plant identity and operating context come from structured power plant inventories and national or regional energy sources. Spatial and environmental evidence comes from open geospatial datasets, satellite products, hazard catalogues, infrastructure datasets, and national or European registers where available [8]. Curated LLM-assisted enrichment is used only for targeted gaps where deterministic sources do not provide the required field [7].

The source hierarchy is deliberately conservative. Authoritative structured data and first-party datasets take priority where they exist. Proxy datasets, volunteered geographic information, and lower-resolution spatial products are used when they are adequate for screening but not for licensing-grade conclusions. LLM-assisted evidence is treated as a curated supplement rather than an authoritative source.

| Evidence family                           | Typical sources                                                                         | Stage 1 role                                                                      | Main limitation                                                                    |
| ----------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Plant inventory and status                | Global Energy Monitor, Beyond Fossil Fuels, JRC, national energy sources.               | Identify sites, coordinates, fuel type, status, capacity, and retirement context. | Source reconciliation is required where names, status, or coordinates differ.      |
| Natural hazard evidence                   | Geological, seismic, flood, meteorological, volcanic, terrain, and land-cover datasets. | Establish whether major safety-related concerns require screening attention.      | Desk-scale sources do not replace site-specific hazard characterization.           |
| Human-induced and infrastructure evidence | Industrial registers, transport networks, grid data, OpenStreetMap, national sources.   | Identify external hazards and practical implementation constraints.               | Public sources may understate classified, local, or operator-specific constraints. |
| Population, land use, and environment     | Population grids, protected-area datasets, land-cover products, national registers.     | Support emergency-planning, radiological-impact, and environmental screening.     | Resolution and legal status vary across countries and source families.             |
| Curated enrichment and assumptions        | Reviewed web/legal/policy evidence, assumption register, quality flags.                 | Fill targeted gaps and record uncertainty for later interpretation.               | Requires human review before being used for strong country or site claims.         |

Every evidence item is interpreted through provenance and quality controls. The database quality vocabulary distinguishes high, medium, low, insufficient, and not-applicable evidence [7]. These flags are not cosmetic: they shape how confidently a criterion can be used, whether a site should be treated as data-limited, and what should be checked during Stage 3 characterization.

## 2.4 Initial Eligibility Checks and Screening Logic

Initial eligibility checks determine whether a site can be evaluated consistently before it enters the Stage 2 scoring workflow. These checks are deliberately basic. They confirm that the site is inside the study region, has a usable coordinate, belongs to the intended coal, lignite or thermal-site universe, and has enough minimum evidence to support screening.

The first screening layer is not a final judgment on nuclear suitability. It is a quality-control step that protects the later comparison from obvious identity errors, missing geography, duplicated records, or sites that are outside the project scope. Where evidence is incomplete but the site remains relevant, the site is retained with data-quality flags rather than silently removed.

| Check | Purpose | Stage 1 treatment |
| --- | --- | --- |
| Site identity | Confirm plant name, country, site type, and representative coordinate. | Resolve duplicates or naming conflicts before comparison. |
| Geographic scope | Confirm the site falls within the 17-country study area. | Exclude sites outside the regional boundary from the report ranking. |
| Technology envelope | Confirm the site can be assessed against the NuScale VOYGR-6 reference case. | Use one reference deployment envelope for consistency. |
| Data availability | Confirm that minimum location, plant, hazard, infrastructure, and population evidence can be assembled. | Flag weak fields; do not treat missing data as favourable evidence. |
| Screening constraints | Identify obvious hard constraints or safety-floor concerns. | Defer detailed reasoning to Stage 2 and the exclusionary-floor artefacts. |

This logic keeps Stage 1 focused on readiness for comparison. It does not convert screening flags into construction decisions, and it does not remove the need for expert review where exclusion would have material consequences.

## 2.5 Candidate Site Identification

Candidate site identification is the point at which a potential site becomes suitable for Stage 2 evaluation. A site moves forward when it is within scope, can be represented spatially, has sufficient evidence for the main screening families, and does not fail the basic eligibility logic described above. This produces a candidate population that can be compared using the common scoring framework.

The candidate step applies the IAEA and EPRI logic of progressive refinement. Regional analysis produces a broad potential-site universe; screening removes or flags sites that cannot be compared responsibly; Stage 2 then evaluates, ranks, and tests the robustness of the remaining candidates [1], [2]. The report keeps this distinction explicit so that a "candidate" is understood as a site ready for structured comparison, not a site that has been found suitable for construction.

Exclusionary logic is handled through two connected gates: hard exclusionary conditions and safety floors. Hard conditions capture cases where a measured or classified feature is incompatible with the screening rule. Safety floors prevent a site with a material weakness on a critical axis from being rescued by unrelated strengths elsewhere in the scoring system [2]. Sites that fail these gates can still be described in the report, but they do not become preferred candidates for Stage 3 progression.

## 2.6 Description of Candidate Sites

Candidate sites should be described in a consistent pattern so that country and site profiles can be read comparatively. The description should start with plant identity, country, location, technology or fuel history, status, and the reason the site is relevant to coal-to-nuclear or thermal-site reuse. It should then summarise the screening-relevant context: grid connection, cooling-water context, transport access, land and infrastructure reuse, surrounding population, external hazards, and known environmental or emergency-planning constraints.

The description should separate facts from interpretation. A plant's former coal role, grid proximity, industrial land, or cooling-water access may explain why it is worth screening, but those features do not by themselves establish nuclear suitability. Similarly, ownership, site control, policy support, and local acceptance should be described only to the extent supported by evidence.

Each candidate description should also carry its data caveats. Low-quality, insufficient, not-applicable, or LLM-assisted fields should be stated plainly when they affect interpretation. This avoids giving the appearance of precision where the study has only screening-grade evidence.

## 2.7 Stage 1 Outputs and Limitations

Stage 1 produces a defined site universe, a screened candidate population, and a documented evidence base for Stage 2 comparison. It also records where the evidence is strong, where it is only a proxy, and where data gaps require caution. These outputs allow the report to proceed from inventory building to transparent evaluation without presenting early screening as a final siting conclusion.

The main limitation is resolution. Stage 1 uses representative coordinates, open datasets, structured inventories, screening proxies, and curated enrichment. It does not confirm land rights, final site boundaries, design-basis hazards, engineered mitigation, emergency-plan approval, grid connection agreements, water permits, environmental acceptability, or community consent. Those questions belong to later stages and require field, engineering, regulatory, and stakeholder work.

The practical result is a defensible handoff to Stage 2. Sites that pass Stage 1 are ready for comparative scoring, ranking, and sensitivity analysis. Sites that do not pass, or that remain data-limited, are still useful to the report because their failure modes and evidence gaps explain why they should not be prioritised without further work.

## Drafting Notes

- Primary links: `report/requirements/04_siting_methodology.md`, `report/methodology/assumption_register.md`, and `report/methodology/ssr1_traceability.md`.
- Use sensitivity outputs only for Stage 2 and results references; Stage 1 should focus on site universe and evidence readiness.
- Follow the analytical anchor and output rules in [`../writing plan/writingDecisions.md`](../writing%20plan/writingDecisions.md).
- Human review should check country naming, plant status, and any coal-retirement claims against source data.

## Working References for Chapter 2

1. IAEA, _Site Survey and Site Selection for Nuclear Installations_, Safety Standards Series No. SSG-35, Vienna (2015).
2. Project methodology artefacts: `report/requirements/04_siting_methodology.md`, `report/methodology/ssr1_traceability.md`, `report/methodology/exclusionary_floors.md`, `report/methodology/sensitivity_analysis.md`, `report/methodology/swing_weight_audit.md`, and `report/methodology/assumption_register.md`.
3. Project assumption register: `report/methodology/assumption_register.md`.
4. Project data requirements: `report/requirements/07_data_requirements.md`.
