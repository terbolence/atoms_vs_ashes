# Implementation Tiers & Phases

Priority ordering and phased implementation plan. Migrated from former §4 + Phase tables of the monolithic data source access plan.

---

## 1. Priority ranking methodology

Sources are ordered by **implementation priority**, determined by how much progress each enables toward correctly describing the siting criteria:

- **Criterion class:** Exclusionary (E-rule: fail = site eliminated) > Avoidance (A-rule: strong screening penalty) > Rank-only (scoring)
- **Category weight:** NH 25% > RI 15% = NS-infra 15% = NS-socio 15% > EP 10% = HI 10% > NS-site 10%
- **Sub-criteria breadth:** sources serving more sub-criteria rank higher
- **ROI:** lower effort for high impact ranks higher
- **Dependencies:** foundational layers before derivatives
- **Coverage:** global (all 23 countries) preferred over partial

**Legend — Criterion Class column:**

- **E** = Exclusionary (Screen (Excl.)) — a fail eliminates the site
- **E/S** = Exclusionary/Suitability (Screen + Rank) — can exclude AND rank
- **A/S** = Avoidance/Suitability (Screen + Rank) — strong avoidance screening + ranking
- **S+R** = Screen + Rank (non-safety screening + ranking)
- **R** = Rank only (Suitability)
- **D** = Derived (depends on upstream connectors)

---

## 2. Tier A — Critical Path: Exclusionary & Primary Avoidance (Priorities 0–14)

These sources directly enable binary pass/fail or strong avoidance decisions. Without them, no site can be confidently screened.

**Ordering rationale (2026-04-13):** Reordered by LLM weakness — criteria where the LLM had the highest inconclusive/deferred rates and lowest confidence are prioritised first, as API data will have the greatest impact there.

| Rank   | Source                             | Spec?   | Effort | Primary Criteria Served                                                                                      | Class   | LLM Weakness | Sub-crit | Cumul. h | Justification                                                                                                                                                                                                    |
| ------ | ---------------------------------- | ------- | ------ | ------------------------------------------------------------------------------------------------------------ | ------- | ------------ | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0** 🔴 | **FIX-03** OSM Site Area Enrichment | 📋 done | 6 h   | BF-02 (land area adequacy), A15 (site area), NS-05a (contiguous land)                                        | **E-eq** | **A15: 85% inconcl** — LLM cannot assess area | 3       | 6        | **Exclusionary-equivalent** per project decision 2026-04-13. 0% fill rate. Highest ROI: OSM connector exists, only needs new query + area computation.        |
| **1**  | **S-01** + **S-18** GEM/SHARE + EFSM20 Faults | ✅ done | 28 h | NH-01 (PGA, SA), NH-02 (fault distance, slip rate)                                                           | **E**   | **E1: 92% deferred** — zero enrichment data | 6        | 34       | E1 (capable faults + seismic) is the worst-performing exclusionary criterion. 92% of sites deferred due to missing data. Faults at 2% fill, PGA at 29%. Combined implementation unlocks full E1 assessment.     |
| **2**  | **S-22** + **S-02** (batch) Zhu Liquefaction + EGDI | ✅ done | 4 h | NH-03 (liquefaction susceptibility)                                                                          | **E/S** | **E2: 92% deferred** — zero soil/liquefaction data | 1  | 38       | E2 (liquefaction) is equally deferred as E1. Zhu raster is 4 h, purpose-built for screening. EGDI already implemented provides soil context. Combined with S-01 PGA enables full liquefaction exclusion.         |
| **3**  | **S-14** + **S-15** Natura 2000 + WDPA | 📋 done | 16 h | NS-08 (Natura 2000 + global protected areas)                                                                 | **E**   | **E7: 92% deferred** — zero protected area data | 2  | 54       | E7 (protected areas) is 92% deferred. No enrichment data exists. EU-mandatory environmental constraint (Natura 2000) plus global coverage (WDPA/RAMSAR/UNESCO).                                                  |
| **4**  | **S-20** GHSL GHS-POP              | ✅ done | 16 h   | RI-04a–d (pop density 5/16/25/80 km), RI-05a, RI-06a, EP-01a, HI-03b, NS-07c, NS-09c, NS-10c                 | **E/A** | **E8: 92% deferred** — zero population data | 10       | 70       | E8 (emergency planning zones) is 92% deferred. Population density is both exclusionary (E8) and primary avoidance (A12: 26% inconcl). Serves the most sub-criteria (~10) of any single source.                   |
| **5**  | **S-08** + **S-10** EU Flood Risk + Copernicus EMS | ✅ done | 24 h | NH-08 (storm surge, flood), NH-09 (river flooding)                                                        | **A/S** | **E6: 25% inconcl, 27% low conf; E9: 10% inconcl** | 3+ | 94       | E6 (subsidence/flooding) has the worst non-deferred performance: 25% inconclusive. E9 (cooling water flooding) at 10%. Flood data fills both gaps plus A11 (17% inconcl). **IMPLEMENTED 2026-04-13.**             |
| **6**  | **S-25** WOKAM Karst               | ✅ done | 4 h    | NH-05a (karst occurrence), RI-03c (karst vulnerability)                                                      | **E/S** | **E5: 11% inconcl, 12% low conf** — LLM 88% fill but needs validation | 2 | 98 | E5 (karst) has 11% inconclusive. LLM achieved 88% fill but from general knowledge — WOKAM provides authoritative validation. 4 h, excellent ROI. **IMPLEMENTED 2026-04-13.**                                    |
| **7**  | **S-19** Copernicus DEM (GLO-30)   | ✅      | 12 h   | NH-04a (slope), NH-08d (tsunami proxy), RI-01d (terrain channeling), EP-03a (topographic barriers), NS-04a/b | **E/S** | **E3: 8% inconcl, 9% low conf** — slope data 2% fill | 6 | 110      | E3 (slope stability) has 8% inconclusive. LLM performed reasonably but slope data is only 2% fill. DEM is a foundational layer for terrain, drainage, tsunami proxy.                                             |
| **8**  | **S-07** Smithsonian GVP           | ✅ done | 8 h    | NH-07 (volcano proximity, volcanic hazard)                                                                   | **E**   | **E4: 0% inconcl, 81% high conf** — LLM strong but API confirms | 2 | 118 | E4 (volcanism) — LLM performed best here (81% high confidence). API provides authoritative confirmation. Low regional relevance (only TR/AM) but must be checked for all sites.                                  |
| **9**  | **I-2** (batch) + **S-12** + **S-37** OSM Military/SEVESO/Industrial | 📋/⏳ | 34 h | HI-02–HI-04 (industrial), A5–A8 (military/SEVESO/toxic) | **A/S** | **A5: 63% inconcl; A8: 50%; A7: 49%; A6: 38%** | 9 | 152 | A5–A8 are the worst-performing avoidance criteria. Military/industrial data is nearly absent from LLM knowledge. Three sources combined unlock 9 sub-criteria.                                                    |
| **10** | **S-39** + **I-2** (batch) OurAirports + OSM airports | ✅ done | 4 h | HI-01a (airport distance), A1–A4 (flight paths)                                                             | **A/S** | **A1: 45% inconcl; A3: 15%** — airport data absent | 4 | 156 | A1 (airport flight paths) is 45% inconclusive. Public domain airport database, 4 h — trivial implementation for a high-impact avoidance criterion.                                                               |
| **11** | **I-2** (batch) OSM Transport      | 📋 done | 8 h    | A14 (transport access), NS-03 (heavy haul, rail, waterway)                                                   | **A/S** | **A14: 27% inconcl, 28% low conf** | 4 | 164 | A14 (transport access) has 27% inconclusive. OSM already implemented — needs batch query enhancement for highway/rail/port proximity.                                                                             |
| **12** | **I-1** (batch) CORINE Land Cover  | 📋 done | 4 h   | A15 supplement (buildable area classification), NS-05 (land cover)                                           | **A/S** | **A15: 85% inconcl** — supplements FIX-03 with land class | 2 | 168 | Supplements FIX-03 site area with land cover classification to determine buildable vs. constrained area. CORINE connector already exists.                                                                         |
| **13** | **I-2** (batch) + **S-13** OSM Grid + ENTSO-E | 📋 done | 16 h | A13 (grid connection), NS-02 (grid capacity)                                                                | **A/S** | **A13: 13% inconcl** — grid data partially available | 3 | 184 | A13 (grid connection) has 13% inconclusive. OSM provides substation proximity; ENTSO-E adds capacity data.                                                                                                        |

**Tier A subtotal: ~184 h — enables all exclusionary checks and primary avoidance screening, ordered by LLM weakness.**

---

## 3. Tier B — High Value: Core Ranking & Secondary Avoidance (Priorities 15–30)

These sources populate the highest-weight ranking criteria and complete secondary avoidance assessments.

| Rank   | Source                                   | Spec?   | Effort | Primary Criteria Served                                                                         | Class   | Sub-crit | Cumul. h | Justification                                                                                                                                                                                               |
| ------ | ---------------------------------------- | ------- | ------ | ----------------------------------------------------------------------------------------------- | ------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **15** | **S-04** Copernicus CDS / ERA5           | ✅ done | 32 h   | NH-10 (wind), NH-11 (precip), NH-12 (temp), RI-01 (atmospheric dispersion)                      | **R**   | ~15      | 182      | Most sub-criteria of any ranking connector (~15). NH has 25% weight, RI has 15%. ERA5 provides consistent meteorological fields across all 23 countries.                                                    |
| **16** | **S-29** EU-Hydro + HydroSHEDS           | ✅ done | 10 h   | RI-02a (river ID), NS-01a (water source type), EP-03b (river crossings), NS-06d                 | **S+R** | 4        | 192      | Foundation for all water-related criteria. NS-01 (cooling water) is Screen + Rank with 15% NS-infra weight. River identification is a dependency for S-30 GloFAS.                                           |
| **17** | **S-30** GloFAS v4                       | ✅ done | 12 h   | RI-02b (discharge), NS-01b (water availability), NS-07a (thermal sensitivity), NS-13b           | **S+R** | 4        | 204      | Cooling water adequacy assessment — NS-01 is Screen + Rank. Quasi-global discharge reanalysis enables dilution capacity and water availability screening. Depends on S-29 for river routing.                |
| **18** | **S-28** Copernicus Marine + Storm Surge | ⏳      | 16 h   | NH-08a/b/c (coastal hazards), NH-12b (SST)                                                      | **A/S** | 4        | 220      | Storm surge and extreme waves are avoidance/suitability. Essential for 8+ coastal in-scope countries. Completes coastal NH-08 assessment started by S-08.                                                   |
| **19** | **S-16** Eurostat GISCO                  | ✅ done | 16 h   | RI-04 (EU census grids), RI-05 (city distance), RI-06 (projections)                             | **A/S** | 3        | 236      | EU census grids with demographic breakdowns. Supplements S-20 GHSL with age-structure and sub-national detail for EU countries. **RI-05 IMPLEMENTED 2026-04-13.** Urban Audit cities + urb_cpop1 populations. |
| **20** | **S-23** ELSUS + NASA Landslides         | ⏳      | 8 h    | NH-04b (landslide susceptibility)                                                               | **E/S** | 1        | 244      | Landslide susceptibility is part of slope stability (exclusionary/suitability). Harmonised European product + global fallback.                                                                              |
| **21** | **S-31** GRanD Dams                      | ⏳      | 4 h    | NH-09c (dam-break exposure proxy)                                                               | **A/S** | 1        | 248      | Dam-break is avoidance/suitability. 4 h effort, combined with S-29 HydroSHEDS for upstream exposure routing.                                                                                                |
| **22** | **S-03** OneGeology                      | ✅ done | 8 h    | NH-02 (fault supplement), NH-05 (karst supplement), NH-06 (lithology)                           | **E/S** | 3        | 256      | Non-EU geology coverage supplement. Extends EGDI (S-02) and EFSM20 (S-18) to non-European in-scope countries.                                                                                               |
| **23** | **S-21** SoilGrids                       | ⏳      | 10 h   | NH-03b (soil texture), NH-06b (bearing capacity), NH-06c (bedrock depth), RI-03a (aquifer type) | **E/S** | 4        | 266      | Global 250 m soil properties. NH-03 is exclusionary/suitability; NH-06 is ranking. Quantitative soil data that geology maps lack.                                                                           |
| **24** | **S-33** WRI Aqueduct 4.0                | ✅ done | 6 h    | NH-11e (drought proxy), NS-01b/c (water stress/competing demand)                                | **S+R** | 3        | 272      | Water stress assessment for cooling water (NS-01 is Screen + Rank). Also feeds drought ranking and future climate water risk. 6 h, excellent ROI.                                                           |
| **25** | **S-38** Natural Earth                   | ⏳      | 2 h    | NH-08d (coastline for tsunami), EP-03c (island/peninsula)                                       | **A/S** | 2        | 274      | 2 h — trivial implementation. Provides coastline vectors needed for tsunami proxy (avoidance) and EP island constraint. Public domain.                                                                      |
| **26** | **S-32** JRC Global Surface Water        | ⏳      | 6 h    | NH-08e (seiche proxy), NS-01a (water source support), NS-04b (drainage), EP-03c                 | **A/S** | 4        | 280      | Surface water occurrence layer. 38-year global record of permanent/seasonal water. Complements river networks (S-29) with lake/reservoir dynamics.                                                          |
| **27** | **S-43** IAEA CNPP/PRIS                  | ⏳      | 10 h   | HI-08a (nuclear reactor distance), NS-12a/b/c (nuclear policy/licensing)                        | **R**   | 4        | 290      | Authoritative nuclear facility locations (PRIS) and national nuclear programme status (CNPP). HI-08 is rank-only but IAEA data is irreplaceable. NS-12 (policy) is important for country-level feasibility. |
| **28** | **S-11** NOAA NCEI                       | ✅ done | 16 h   | NH-10 (tornadoes), NH-11 (hail, rainfall), NH-12 (temp fallback)                                | **R**   | ~6       | 306      | CDS fallback and complement. Station-based observations to validate ERA5 reanalysis. Particularly useful for tornadoes and severe weather events.                                                           |
| **29** | **S-17** Eurostat Projections / NSOs     | ✅ done | 16 h   | RI-06 (projected density), NS-09 (socioeconomic), NS-10 (workforce), NS-12 (policy proxy)       | **R**   | 5+       | 322      | Demographic projections and socioeconomic indicators. RI-06 + NS-09 + NS-10 span 15% RI + 15% NS-socio weight.                                                                                              |
| **30** | **S-26** Copernicus EGMS                 | ⏳      | 10 h   | NH-05c (ground motion / subsidence via InSAR)                                                   | **E/S** | 1        | 332      | Subsidence is exclusionary/suitability (E-rule E6). mm-precision InSAR ground motion across Europe. Annual updates.                                                                                         |

**Tier B subtotal: ~150 h (cumulative ~334 h) — enables credible multi-criteria ranking across all criterion families.**

> **Note:** Some sources previously in Tier B (S-14/S-15, S-12/S-37, S-39, S-13, CORINE batch) have been promoted to Tier A based on LLM weakness analysis. Cumulative hours in Tier B/C/D tables reflect original estimates and may need recalculation as Tier A absorbed additional items.

---

## 4. Tier C — Ranking Completeness (Priorities 31–41)

| Rank   | Source                          | Spec?   | Effort | Primary Criteria Served                                                                         | Class     | Sub-crit | Cumul. h | Justification                                                                                                                                                                      |
| ------ | ------------------------------- | ------- | ------ | ----------------------------------------------------------------------------------------------- | --------- | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **31** | **S-35** EFFIS + FIRMS Fire     | ⏳      | 10 h   | NH-13a (wildfire / burned area history)                                                         | **R**     | 1        | 342      | Dedicated fire products — EFFIS Europe + FIRMS global active fires. More authoritative than satellite imagery analysis (S-05/S-06).                                                |
| **32** | **S-36** ESA WorldCover         | ✅      | 8 h    | NS-04c (land cover), NS-05 (buildable), NS-08d (fragmentation), NS-13c (laydown)                | **R**     | 4        | 350      | **IMPLEMENTED 2026-04-13.** 30 tiles (2.23 GB), ESA→CORINE crosswalk, 201 non-EU sites enriched (4.2s). 43+7+1 tests.                                                             |
| **33** | **S-24** USGS VS30              | ⏳      | 4 h    | NH-04c (seismic slope amplification proxy)                                                      | **E/S**   | 1        | 354      | Global VS30 for site response classification. Combined with S-01 PGA for amplification proxy. 4 h, good ROI.                                                                       |
| **34** | **S-27** GEM Fossil Trackers    | ⏳      | 8 h    | NH-05d (oil/gas prox), HI-04a (pipeline prox), HI-04b (LNG prox)                                | **A/S**   | 3        | 362      | Fossil fuel infrastructure database. HI-04 is avoidance/suitability. Supplements I-4 GEM Coal Tracker with broader energy infrastructure.                                          |
| **35** | **S-13** ENTSO-E                | ✅ done | 16 h   | NS-02b (grid capacity proxy), NS-02c (congestion proxy)                                         | **S+R**   | 2        | 378      | Grid connection has 15% NS-infra weight and Screen + Rank classification. ENTSO-E provides system-level electricity data for EU/ENTSO-E members.                                   |
| **35b** | **S-45** PyPSA-Eur Grid Topology | ⏳     | 8 h    | NS-02a (site-level grid export capacity via thermal line rating)                                 | **S+R**   | 1        | 386      | Topological network model with thermal ratings (MVA). Site-level resolution that ENTSO-E zonal data cannot provide. Static download from Zenodo; 8 h effort. |
| **35c** | **FIX-02** NS-02 Grid Pipeline  | 📋 done | 30 h   | NS-02 (all sub-fields: GEM fallback + ENTSO-E + OSM fixes + PyPSA-Eur)                          | **S+R**   | 4        | 416      | Orchestration spec tying S-13, S-45, I-2 OSM fixes, and I-4 GEM fallback into a complete NS-02 pipeline. |
| **36** | **S-42** World Bank WDI         | ⏳      | 8 h    | NS-09a/b (employment/GDP — non-EU), NS-10a/b (workforce/education — non-EU), NS-13a (logistics) | **R**     | 5        | 424      | Country-level socioeconomic indicators for non-EU countries.                                                                                                                       |
| **37** | **S-05** Sentinel Hub           | 📋 done | 24 h   | NH-04 (slope supp.), NH-05 (settlement InSAR supp.), NS-04, NS-06, NS-07                        | **R**     | 5+       | 410      | Versatile satellite imagery connector. Largely supplementary now that dedicated products handle core needs.                                                                        |
| **38** | **S-09** GFMS                   | ✅ done | 8 h    | NH-08/09 (flood fallback)                                                                       | **A/S**   | 2        | 418      | Global flood monitoring fallback for non-EU countries.                                                                                                                              |
| **39** | **S-06** Google Earth Engine    | ✅ done | 24 h   | NH-13 (fire history supp.), NS-04 (terrain supp.), NS-06 (demolition)                           | **R**     | 3+       | 442      | Powerful cloud-compute platform. Largely supplementary now that dedicated connectors handle specific products.                                                                     |
| **40** | **EXT-01** OSM Enhanced Queries | ⏳      | 40 h   | EP-01/02/04 (evacuation), HI-05/06/07 (transport/military hazards), NS-03/05/06, RI-02d         | **A/S+R** | 12+      | 482      | Major enhancement serving ~12 sub-criteria across EP, HI, and NS.                                                                                                                  |
| **41** | **S-34** ESWD Severe Weather    | ⏳      | 6 h    | NH-10b (tornado events), NH-11d (hail events)                                                   | **R**     | 2        | 488      | European severe weather event database. Access may require institutional license.                                                                                                  |

**Tier C subtotal: 156 h (cumulative 488 h) — achieves near-complete ranking capability.**

---

## 5. Tier D — Supplementary & Derived Layers (Priorities 42–48)

| Rank   | Source                                       | Spec? | Effort | Primary Criteria Served                                            | Class | Sub-crit | Cumul. h | Justification                                                                                                                                           |
| ------ | -------------------------------------------- | ----- | ------ | ------------------------------------------------------------------ | ----- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **42** | **S-40** OpenSky Network                     | ⏳    | 8 h    | HI-01b/c (air traffic density, flight corridor)                    | **R** | 2        | 496      | Research/non-commercial use restriction requires licensing review.                                                                                      |
| **43** | **S-41** ERA RINF Railway                    | ⏳    | 6 h    | HI-05b (rail hazmat), NS-03b (rail access)                         | **R** | 2        | 502      | EU-only railway register.                                                                                                                               |
| **44** | **S-44** Eurobarometer                       | ⏳    | 4 h    | NS-09d (public acceptance proxy)                                   | **R** | 1        | 506      | Single sub-criterion. EU-only.                                                                                                                          |
| **45** | **EXT-02** GEM Enhanced Synergy              | ⏳    | 8 h    | NS-06a/c/d (infrastructure reuse), NS-11a/b (synergies)            | **R** | 5        | 514      | Coal-to-nuclear synergy assessment refinement.                                                                                                          |
| **46** | **DRV-01** NaTech Composite                  | ⏳    | 12 h   | NH-14a/b (earthquake + flood × industrial NaTech)                  | **D** | 2        | 526      | Derived layer. Depends on S-01 + S-37 + S-08/S-10.                                                                                                     |
| **47** | **DRV-02** EP Composite Scoring              | ⏳    | 16 h   | EP-01a (composite EPZ feasibility), EP-05a (infra hazard exposure) | **D** | 2        | 542      | Derived layer. Depends on EXT-01 + S-20 + S-19 + S-29.                                                                                                |
| **48** | **DRV-03** Coal-to-Nuclear Synergy Composite | ⏳    | 8 h    | NS-11a/b (infrastructure/grid reuse benefit)                       | **D** | 2        | 550      | Derived layer. Depends on I-4 + I-2 + S-13 + S-29.                                                                                                     |

**Tier D subtotal: 62 h (cumulative 550 h) — completes all programmable sources.**

---

## 6. Milestone summary

| Milestone                           | After Rank | Cumul. Hours | What You Can Do                                                                                                                          |
| ----------------------------------- | ---------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Site area + worst exclusionary**  | 4          | 70 h         | Site area (A15), E1 (faults/seismic), E2 (liquefaction), E7 (protected areas), E8 (population) — the 5 criteria where LLM was 92% deferred. |
| **All exclusionary screening**      | 8          | 118 h        | All E-rule checks (E1–E9) operational including flood, karst, slope, volcanism. Can definitively eliminate sites on hard criteria.       |
| **Primary avoidance complete**      | 13         | 184 h        | All A-rule checks (A1–A15) operational — military, airports, transport, grid, industrial. Ordered by LLM weakness for maximum impact.    |
| **Core ranking operational**        | ~22        | ~280 h       | Meteorology, hydrology, coastal hazards, geology, and demographics populated. Meaningful multi-criteria site ranking possible.           |
| **Ranking near-complete**           | ~30        | ~360 h       | EGMS subsidence, IAEA nuclear data, socioeconomic indicators, fire history added. All criterion families have at least partial coverage. |
| **Full programmable coverage**      | ~48        | ~580 h       | All programmable sources implemented. Only national (N-01 to N-21) and overhead remain (~218 h).                                         |

---

## 7. Phase task lists

### Phase 1: Exclusionary & Avoidance Screening Sources (~184 h)

**Goal:** Enable all Exclude/Fail decisions (E1–E9) and primary avoidance checks (A1–A15 thresholds).

Authoritative status (criterion × source × done/not done) is in [`exclusionary_data_sources_access_plan.md`](exclusionary_data_sources_access_plan.md) (E1–E9) and [`avoidance_data_sources_access_plan.md`](avoidance_data_sources_access_plan.md) (A1–A15). The priority queue is in [`priority_work_queue.md`](priority_work_queue.md). The ~184 h cumulative is the sum of Tier A rows.

### Phase 2: Core Ranking Connectors (~250 h)

**Goal:** Populate scoring variables for meteorology, climate, terrain, demographics, hydrology, grid, and socioeconomic proxies.

| #   | Task                             | Source | Status                     | Criteria Unlocked                                   | Hours    |
| --- | -------------------------------- | ------ | -------------------------- | --------------------------------------------------- | -------- |
| 1   | Meteorology connector (CDS/ERA5) | S-04   | ✅ implemented (`connectors/copernicus_era5`) | NH-10/11/12, RI-01 (wind/stability/mixing)          | 32       |
| 2   | NOAA NCEI fallback               | S-11   | ✅ implemented (`connectors/noaa_ncei`) | NH-10 (tornadoes), NH-11 (rainfall), NH-12 (temp)   | 16       |
| 3   | Sentinel Hub terrain/imagery     | S-05   | 📋 spec done, ⏳ implement | NH-04 (slope supplement), NH-05 (settlement), NS-06 | 24       |
| 4   | Google Earth Engine              | S-06   | ⏸️ code present, **disabled** (no Google app review) — use COG/Sentinel path | NH-13 / NS-04 supplements when re-enabled | 24       |
| 5   | ENTSO-E grid connector           | S-13   | ✅ implemented (2026-04-13) | NS-02 (grid capacity/congestion)                    | 16       |
| 6   | Eurostat projections / NSOs      | S-17   | ✅ implemented (`connectors/eurostat_projections`) | RI-06, NS-09, NS-10, NS-12                          | 16       |
| 7   | GFMS flood enrichment            | S-09   | ✅ implemented (`connectors/gfms`) | NH-08/09 (flash flood, dam break fallback)          | 8        |
| 8   | SoilGrids                        | S-21   | ⏳ spec + implement        | NH-03b (soil texture), NH-06b/c (bearing/bedrock)   | 10       |
| 9   | ELSUS v2 + NASA Landslides       | S-23   | ⏳ spec + implement        | NH-04b (landslide susceptibility)                   | 8        |
| 10  | USGS VS30                        | S-24   | ⏳ spec + implement        | NH-04c (seismic amplification proxy)                | 4        |
| 11  | Copernicus EGMS                  | S-26   | ⏳ spec + implement        | NH-05c (ground motion InSAR)                        | 10       |
| 12  | GEM Fossil Trackers              | S-27   | ⏳ spec + implement        | NH-05d (oil/gas prox), HI-04a/b (pipeline/LNG)      | 8        |
| 13  | Copernicus Marine + Storm Surge  | S-28   | ⏳ spec + implement        | NH-08a/b/c (coastal hazards), NH-12b (SST)          | 16       |
| 14  | EU-Hydro + HydroSHEDS            | S-29   | ✅ implemented (`connectors/hydrorivers`) | RI-02a (river ID), NS-01a (water source), EP-03b    | 10       |
| 15  | GloFAS v4                        | S-30   | ✅ implemented (`connectors/glofas_discharge`) | RI-02b (discharge), NS-01b (water avail), NS-07a    | 12       |
| 16  | GRanD Dams                       | S-31   | ⏳ spec + implement        | NH-09c (dam-break exposure)                         | 4        |
| 17  | JRC Global Surface Water         | S-32   | ⏳ spec + implement        | NH-08e (seiche), NS-01a (support), NS-04b           | 6        |
| 18  | WRI Aqueduct 4.0                 | S-33   | ✅ implemented (`connectors/wri_aqueduct`) | NH-11e (drought), NS-01b/c (water stress)           | 6        |
| 19  | EFFIS + FIRMS Fire               | S-35   | ⏳ spec + implement        | NH-13a (fire history/burned area)                   | 10       |
| 20  | ESA WorldCover                   | S-36   | ✅ implemented (2026-04-13) | NS-04c (land cover), NS-05 (buildable), NS-08d      | 8        |
| 21  | Natural Earth                    | S-38   | ⏳ spec + implement        | NH-08d (coast), EP-03c (island/peninsula)           | 2        |
| 22  | OurAirports                      | S-39   | ✅ implemented              | HI-01a (airport distance), A1–A4                    | 4        |
| 23  | IAEA CNPP/PRIS                   | S-43   | ⏳ spec + implement        | HI-08a (nuclear dist), NS-12a/b/c (policy)          | 10       |
| 24  | World Bank WDI                   | S-42   | ⏳ spec + implement        | NS-09a/b, NS-10a/b, NS-13a (non-EU fallback)        | 8        |
|     | **Phase 2 Total**                |        |                            |                                                     | **~250** |

### Phase 3: Infrastructure, Logistics, EP & Derived Layers (~140 h)

**Goal:** Complete infrastructure, transport, EP, coal-to-nuclear synergy scoring, NaTech composites, and remaining supplementary connectors.

| #   | Task                                                                | Source                          | Status              | Criteria Unlocked                                                          | Hours    |
| --- | ------------------------------------------------------------------- | ------------------------------- | ------------------- | -------------------------------------------------------------------------- | -------- |
| 1   | OSM enhanced transport/evacuation (EXT-01)                          | I-2 OSM (enhanced)              | ⏳ spec + implement | NS-03, EP-01/02, EP-04, HI-05a/b, HI-06a, HI-07a, RI-02d, NS-05a, NS-06a/c | 40       |
| 2   | Coal-to-nuclear synergy extension (EXT-02)                          | I-4 GEM (enhanced)              | ⏳ spec + implement | NS-06a/c/d, NS-11a/b                                                       | 8        |
| 3   | NaTech Combined Hazard Index (DRV-01)                               | Internal derived                | ⏳ spec + implement | NH-14a/b (earthquake/flood + industrial NaTech)                            | 12       |
| 4   | EP Composite Scoring (DRV-02)                                       | Internal derived                | ⏳ spec + implement | EP-01a (composite feasibility), EP-05a (infra hazard)                      | 16       |
| 5   | Coal-to-Nuclear Synergy Composite (DRV-03)                          | Internal derived                | ⏳ spec + implement | NS-11a/b (infrastructure/grid reuse benefit)                               | 8        |
| 6   | ESWD Severe Weather                                                 | S-34                            | ⏳ spec + implement | NH-10b (tornado), NH-11d (hail)                                            | 6        |
| 7   | OpenSky Network                                                     | S-40                            | ⏳ spec + implement | HI-01b/c (air traffic/corridor proxy)                                      | 8        |
| 8   | ERA RINF Railway                                                    | S-41                            | ⏳ spec + implement | HI-05b (rail hazmat), NS-03b (rail access)                                 | 6        |
| 9   | Eurobarometer                                                       | S-44                            | ⏳ spec + implement | NS-09d (public acceptance proxy)                                           | 4        |
| 10  | Remaining EP/NS sub-criteria (water quality, noise/visual, laydown) | Multiple (S-37, S-20, I-1, I-2) | ⏳ implement        | NS-07b/c/d, NS-13c                                                         | 16       |
| 11  | Integration testing & cross-connector validation                    | All above                       | ⏳                  | Data quality audits, provenance checks                                     | 16       |
|     | **Phase 3 Total**                                                   |                                 |                     |                                                                            | **~140** |

### Phase 4: National & Manual Data (~160 h)

**Goal:** Fill country-specific gaps, manual regulatory data, and weaker open-data fields.

| #   | Task                                      | Source               | Status | Criteria Unlocked                                            | Hours    |
| --- | ----------------------------------------- | -------------------- | ------ | ------------------------------------------------------------ | -------- |
| 1   | National geological survey integration    | N-01 (23 countries)  | ⏳     | NH-02, NH-05, NH-06 (country detail)                         | 40       |
| 2   | National hydrogeological surveys          | N-02 (12+ countries) | ⏳     | NH-03 (groundwater), RI-03 (aquifer detail)                  | 16       |
| 3   | National hydrological services            | N-03 (15+ countries) | ⏳     | NH-09 (dam break detail), NH-12 (water temp), NS-01 (volume) | 24       |
| 4   | National meteorological services          | N-04 (10+ countries) | ⏳     | NH-10/11/12 (where CDS insufficient)                         | 16       |
| 5   | National aviation / military data         | N-07 + N-08          | ⏳     | HI-01 (flight paths), HI-06 (military detail), HI-06b (UXO)  | 24       |
| 6   | National pipeline / energy infrastructure | N-09                 | ⏳     | HI-04 (pipeline), HI-05c (pipeline hazmat)                   | 8        |
| 7   | National cadastre / zoning                | N-16 + N-19          | ⏳     | NS-05b/c (land ownership, zoning)                            | 8        |
| 8   | National communications regulators        | N-17                 | ⏳     | HI-07 (EMI transmitter detail)                               | 4        |
| 9   | National biodiversity datasets            | N-18                 | ⏳     | NS-08 (IBA, protected species)                               | 8        |
| 10  | National health / social care registers   | N-20                 | ⏳     | EP-04 (hospitals, prisons, care facilities)                  | 4        |
| 11  | Country regulatory/policy research        | N-21 (23 countries)  | ⏳     | NS-12 (policy, opinion, licensing)                           | 16       |
|     | **Phase 4 Total**                         |                      |        |                                                              | **~168** |
