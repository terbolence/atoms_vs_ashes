# Annex A: IAEA and EPRI Traceability

**What this annex adds.** Annex A carries the per-requirement SSR-1 coverage matrix that the main report summarises but does not reproduce. Chapter 1 §1.4 and Chapter 3 §3.3 explain how IAEA and EPRI frameworks are used in this study; they do not list individual Requirements. Annex A does.

## Reading the matrix

Each Requirement of IAEA SSR-1 (2019) is mapped to one or more project scoring criteria. The coverage column uses four values:

- **full** — the criterion or criteria cover the substantive Requirement obligations at screening resolution.
- **partial** — screening proxies a portion of the Requirement; detailed siting is needed to close it out.
- **screening_only** — the basic-filter family captures the upstream eligibility gate, not the Requirement itself.
- **out_of_scope** — the Requirement is operational, programmatic, or quality-assurance-related and is not addressed by a scoring criterion. These are handled in the Stage 3 and operational phases.

The Stage 3 action column states the investigation that would carry the Requirement beyond screening. Project-only criteria (see the second table) are scored for ranking but sit outside the SSR-1 safety remit; they are listed here for completeness so that reviewers see the full rubric.

## SSR-1 Requirement × project criterion coverage

| SSR-1 Req. | Title | Coverage | Mapped project criteria | Stage 3 action |
| --- | --- | --- | --- | --- |
| Req-1 | Responsibilities in site evaluation | out_of_scope | — | Defined during licensing programme setup; addressed in operational governance. |
| Req-2 | Process of site evaluation | screening_only | BF-01 (grid export), BF-02 (nuclear-island footprint) | Full SSR-1 process applies once Stage 3 begins. |
| Req-3 | Considerations for site evaluation (information quality) | out_of_scope | — | Managed through the project data-provenance layer and the assumption register. |
| Req-4 | Earthquakes (vibratory ground motion) | full | NH-01, NH-03, NH-06 | Site-specific PSHA, dynamic soil properties, foundation characterisation. |
| Req-5 | Surface faulting (capable faults) | full | NH-02 | Capable-fault ground-truth survey within the screening radius. |
| Req-6 | Meteorological hazards (winds, temperatures, precipitation) | full | NH-10, NH-11, NH-12 | On-site meteorological tower and national-station climatology. |
| Req-7 | Flooding (river, coastal, surge, tsunami) | full | NH-08, NH-09 | Design-basis flood analysis with combined-event treatment. |
| Req-8 | Geotechnical hazards (slope, subsidence, karst) | full | NH-04, NH-05, NH-06 | Boreholes, laboratory testing, slope-stability and karst investigation. |
| Req-9 | Volcanism | full | NH-07 | Probabilistic volcanic hazard assessment where the screening return-period regime indicates it. |
| Req-10 | Other natural events (wildfire, biological) | partial | NH-13 | Biological hazards to cooling-water intakes require a dedicated Stage 3 study. |
| Req-11 | External events caused by human activities | full | HI-01, HI-02, HI-03, HI-04, HI-05, HI-06, HI-07, HI-08 | National industrial-register survey, aviation study, defence-ministry engagement. |
| Req-12 | Population characteristics (current and projected) | full | RI-04, RI-05, RI-06 | Census and municipal-planning-based projection; site-specific population mapping. |
| Req-13 | Emergency planning zones (EPZ feasibility) | full | EP-01, EP-02, EP-03, EP-04, EP-05 | Evacuation time estimate, concept of operations, civil-protection coordination. |
| Req-14 | Atmospheric dispersion characteristics | full | RI-01 | Site-specific dispersion model calibrated against on-site meteorology. |
| Req-15 | Surface- and groundwater dispersion characteristics | full | RI-02, RI-03 | Aquifer conceptual model, river-segment dilution measurement, receptor analysis. |
| Req-16 | Radioactive material accumulation in water bodies | partial | RI-02, RI-03 | Long-term accumulation modelling deferred to detailed siting. |
| Req-17 | Combinations of hazards | full | NH-14 | Combined-hazard screening with plausible concurrent events. |
| Req-18 | Site protection against external hazards | partial | NS-04 | Engineered protection is a design-stage item; topography is only a screening proxy. |
| Req-19 | Monitoring of site-related parameters | out_of_scope | — | Operational obligation; set out in the pre-operational programme. |
| Req-20 | Quality assurance for site evaluation | out_of_scope | — | Managed through the project assumption register and provenance layer. |

## Project-only criteria (not mapped to SSR-1)

The criteria below are ranking axes for implementation and coal-to-nuclear practicality. They are not SSR-1 safety requirements and are excluded from the coverage matrix above.

| Criterion | Rationale for inclusion in project ranking |
| --- | --- |
| NS-01 — Cooling water / ultimate heat sink | Viability axis; related to SSR-1 Req-15 indirectly but treated as non-safety here. |
| NS-02 — Grid connection (detailed) | Project-economic axis; outside SSR-1 scope. |
| NS-03 — Transport access (heavy haul) | Constructability axis; outside SSR-1 scope. |
| NS-05 — Land availability, ownership, zoning | Project-legal axis; outside SSR-1 scope. |
| NS-06 — Existing infrastructure reuse | Project-economic axis; outside SSR-1 scope. |
| NS-07 — Environmental impact (non-radiological) | Covered by EIA legislation, not SSR-1. |
| NS-08 — Ecological sensitivity (Natura 2000, WDPA) | Covered by EIA legislation, not SSR-1. |
| NS-09 — Socioeconomic impact | Project-acceptability axis; outside SSR-1 scope. |
| NS-10 — Workforce availability | Project-economic axis; outside SSR-1 scope. |
| NS-11 — Coal-to-nuclear synergies | Project-strategy axis; outside SSR-1 scope. |
| NS-12 — Regulatory and political environment | Project-political axis; outside SSR-1 scope. |
| NS-13 — Construction logistics | Project-economic axis; outside SSR-1 scope. |

All rubric criteria are accounted for (no orphans).

## EPRI alignment

The EPRI Advanced Nuclear Siting Guide distinguishes four screening actions: exclusionary screening, avoidance screening, suitability evaluation, and alternative-site ranking. The project workflow uses this sequence directly. Exclusionary screening in the project is the hard-exclusion gate; avoidance screening is the avoidance-flag treatment; suitability evaluation is the composite ranking after both gates; alternative-site ranking is the Monte Carlo sensitivity analysis described in Annex C. The EPRI criterion families (footprint, cooling, grid, transport, implementation) map into the project NS family and the BF basic filters. No EPRI concept is left unmapped in the project rubric.

## Primary sources for this annex

- `report/methodology/ssr1_traceability.md` — the authoritative source for the matrix above.
- `report/requirements/03_regulatory_framework.md`.
- `report/requirements/04_siting_methodology.md`.
- External standards [1], [2], [8] in Chapter 8.
