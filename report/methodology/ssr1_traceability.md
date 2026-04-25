# SSR-1 ↔ project-criterion traceability matrix

- Stamp: `20260425`
- Reference: IAEA SSR-1 (2019) — Site Evaluation for Nuclear Installations
- Source map: `config/ssr1_clause_map.yaml`
- Source CSV: `audit/post_processing/06_scoring/20260425_ssr1_traceability.csv`

## How to read this matrix

Each Requirement of IAEA SSR-1 (2019) is mapped to one or more
Atoms-vs-Ashes scoring criteria. ``coverage`` indicates how much
of the Requirement is satisfied at screening resolution:

- **full** — the criterion(s) cover the substantive Requirement
  obligations at pre-screening resolution.
- **partial** — the screening proxies a portion of the
  Requirement; detailed siting is needed to close it out.
- **screening_only** — the basic-filter family captures the
  upstream eligibility gate, not the Requirement itself.
- **out_of_scope** — the Requirement is operational, programmatic
  or QA-related and not addressed by a scoring criterion.

## SSR-1 Requirements

| SSR-1 Req. | Title | Coverage | Mapped criteria | Notes |
| --- | --- | --- | --- | --- |
| SSR-1/Req-1 | Responsibilities in site evaluation | `out_of_scope` | — | Programmatic obligation on operator/regulator. Atoms-vs-Ashes is a pre-screening study; responsibilities are addressed in the operational stage. |
| SSR-1/Req-2 | Process of site evaluation | `screening_only` | BF-01 (Grid export / connection adequacy), BF-02 (Land / nuclear-island footprint) | The basic-filter family captures the upstream eligibility gates (grid adequacy and minimum land footprint) before hazard assessment proper begins. |
| SSR-1/Req-3 | Considerations for site evaluation (information quality) | `out_of_scope` | — | Information-quality considerations are handled by the data provenance layer (API-primary / LLM-fallback) and the assumption register, not by an individual scoring criterion. |
| SSR-1/Req-4 | Earthquakes (vibratory ground motion) | `full` | NH-01 (Seismic ground motion (PGA)), NH-03 (Geotechnical - settlement and liquefaction), NH-06 (Foundation conditions (bearing, bedrock, groundwater)) | PGA, liquefaction/settlement and bedrock/foundation conditions together cover the substantive Req-4 obligations at screening resolution. |
| SSR-1/Req-5 | Surface faulting (capable faults) | `full` | NH-02 (Seismic surface rupture (capable faults)) |  |
| SSR-1/Req-6 | Meteorological hazards (extreme winds, temperatures, precipitation) | `full` | NH-10 (Extreme winds), NH-11 (Extreme precipitation (rain, snow, drought)), NH-12 (Extreme temperatures) |  |
| SSR-1/Req-7 | Flooding (river, coastal, surge, tsunami) | `full` | NH-08 (Coastal flooding (storm surge, tsunami)), NH-09 (River flooding) |  |
| SSR-1/Req-8 | Geotechnical hazards (slope stability, subsidence, karst) | `full` | NH-04 (Geotechnical - slope stability), NH-05 (Subsidence / karst / mining / oil & gas), NH-06 (Foundation conditions (bearing, bedrock, groundwater)) |  |
| SSR-1/Req-9 | Volcanism | `full` | NH-07 (Volcanism) |  |
| SSR-1/Req-10 | Other natural events (wildfire, biological hazards) | `partial` | NH-13 (Forest / wildfire) | Wildfire is covered; biological hazards (e.g. fouling organisms in cooling-water intakes) are deferred to detailed siting because no pan-regional dataset supports a screening rubric. |
| SSR-1/Req-11 | External events caused by human activities | `full` | HI-01 (Aircraft crash hazard), HI-02 (Industrial explosions (Seveso / IED)), HI-03 (Toxic / gas releases), HI-04 (External fires), HI-05 (Transport hazards (hazmat road / rail / pipe)), HI-06 (Military installations), HI-07 (Electromagnetic interference), HI-08 (Other nuclear installations) | Aircraft crash, industrial explosions, toxic releases, external fires, transport hazmat corridors, military installations, EMI and other nuclear installations. |
| SSR-1/Req-12 | Population characteristics (current and projected) | `full` | RI-04 (Population density (EPZ rings)), RI-05 (Distance to large population centres (>50 k)), RI-06 (Population projections (60-yr design life)) |  |
| SSR-1/Req-13 | Emergency planning zones (EPZ feasibility) | `full` | EP-01 (Emergency-plan feasibility (composite)), EP-02 (Evacuation routes (road network)), EP-03 (Physical-geography constraints), EP-04 (Special populations (hospitals, prisons, care homes)), EP-05 (Concurrent-hazard impact on EP) |  |
| SSR-1/Req-14 | Atmospheric dispersion characteristics | `full` | RI-01 (Atmospheric dispersion (wind, stability, BLH)) |  |
| SSR-1/Req-15 | Surface- and groundwater dispersion characteristics | `full` | RI-02 (Surface water dispersion), RI-03 (Groundwater dispersion) |  |
| SSR-1/Req-16 | Radioactive material accumulation in water bodies | `partial` | RI-02 (Surface water dispersion), RI-03 (Groundwater dispersion) | Screening proxy via dispersion characteristics; long-term accumulation modelling is part of detailed siting. |
| SSR-1/Req-17 | Combinations of hazards | `full` | NH-14 (Combined hazards) |  |
| SSR-1/Req-18 | Site protection against external hazards | `partial` | NS-04 (Site topography / grading) | Topography / grading provides screening of natural protection potential; engineered protection is a design-stage concern. |
| SSR-1/Req-19 | Monitoring of site-related parameters | `out_of_scope` | — | Operational obligation; not a screening criterion. |
| SSR-1/Req-20 | Quality assurance for site evaluation | `out_of_scope` | — | Programmatic; addressed by the assumption register and API/LLM provenance layer rather than a scoring criterion. |

## Project-only criteria (not mapped to SSR-1)

These viability axes (cost, transport, regulatory environment, …)
are scored for ranking purposes but sit outside the SSR-1 safety
remit. Listed here for completeness so reviewers see the full
rubric.

| Criterion | Rationale |
| --- | --- |
| NS-01 — Cooling water / ultimate heat sink | Captured under SSR-1 Req-15 indirectly, but treated as a non-safety viability axis here. |
| NS-02 — Grid connection (detailed) | Project-economic; outside SSR-1 scope. |
| NS-03 — Transport access (heavy haul) | Constructability; outside SSR-1 scope. |
| NS-05 — Land availability / ownership / zoning | Project-legal; outside SSR-1 scope. |
| NS-06 — Existing infrastructure reuse | Project-economic; outside SSR-1 scope. |
| NS-07 — Environmental impact (non-radiological) | Covered by EIA legislation, not SSR-1. |
| NS-08 — Ecological sensitivity (Natura 2000 / WDPA) | Covered by EIA legislation, not SSR-1. |
| NS-09 — Socioeconomic impact | Project-acceptability; outside SSR-1 scope. |
| NS-10 — Workforce availability | Project-economic; outside SSR-1 scope. |
| NS-11 — Coal-to-nuclear synergies | Project-strategy; outside SSR-1 scope. |
| NS-12 — Regulatory / political environment | Project-political; outside SSR-1 scope. |
| NS-13 — Construction logistics | Project-economic; outside SSR-1 scope. |

_All rubric criteria are accounted for (no orphans)._
