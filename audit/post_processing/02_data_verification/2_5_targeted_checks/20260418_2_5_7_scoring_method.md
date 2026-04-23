<!-- man_hours: 1.5 -->

---
step: "13_data_post_processing §2.5.7"
title: "Targeted check — Scoring method review"
date: 2026-04-18
inputs:
  - requirements/06_scoring_matrix.md
  - requirements/05_siting_criteria.md (+ 05_1 through 05_5)
  - report/methodology/methodology.md
  - audit/post_processing/01_requirements_coverage/20260418_gaps.md
  - audit/post_processing/02_data_verification/20260418_data_inventory.md
reference_standards:
  - IAEA SSG-35 (Site Survey and Site Selection for Nuclear Installations, 2015)
  - IAEA SSR-1 / NS-R-3 Rev.1 (Site Evaluation for Nuclear Installations, 2016)
  - IAEA SSG-9 Rev.1 (Seismic Hazards in Site Evaluation, 2022)
  - EPRI Report 3002023910 (Advanced Nuclear Technology Siting Guide, 2022)
---

# §2.5.7 — Scoring method review

## 1. Objective

Assess whether `requirements/06_scoring_matrix.md` is detailed enough to support the Phase 3 ranking of ~363 candidate sites. Specifically:

1. Catalogue the 6 criteria with existing quantitative scoring bands and assess their completeness against IAEA/EPRI expectations.
2. For the 40 criteria without bands, prioritise by Phase (Screen > Rank) and data availability.
3. Propose sub-weights within each of the 7 category allocations (currently undefined per §8.2).
4. Identify additional sensitivity-analysis parameters and improvements needed before §4 (scoring) can run.

---

## 2. Existing scoring bands — completeness audit

### 2.1 Criteria with defined bands (6 of 46)

| # | Criterion | Band subject | Bands defined | Thresholds sound? | Data source aligned? | IAEA/EPRI alignment | Issues |
|---|-----------|-------------|:---:|:---:|:---:|---|---|
| 1 | NH-01 | PGA at 475-yr return period | 5 bands | **Yes** | **Yes** (EFEHR) | SSG-9 consistent; 0.30 g upper threshold aligns with SMR design envelope margins | None — well-constructed |
| 2 | NH-10 | Max wind speed / gust | 5 bands | **Yes** | **Yes** (NOAA NCEI; ERA5 correctly excluded) | EN 1991-1-4 wind class referenced; EPRI Siting Guide §4.3 compatible | Methodology §2.5 warning about ERA5 is clear; no action needed |
| 3 | NH-11 (drought) | SPI-12 minimum | 5 bands | **Yes** | **Yes** (ERA5 monthly tp → SPI-12) | McKee et al. (1993) methodology correct | Consider coupling with NS-01 seasonal sub-score (same SPI-12 data) to avoid double-counting |
| 4 | NH-11 (snow) | Snow months per year | 5 bands | **Yes** | **Yes** (ERA5 monthly sf) | Adequate for structural/accessibility screening | Band width (2 months per band) is appropriate for European range |
| 5 | NH-12 (max temp) | Max recorded air temperature | 5 bands | **Yes** | **Yes** (NOAA NCEI) | Cooling-system design thresholds reasonable | Band 5 threshold (< 33 °C) may be too generous — most Central European sites will score 4 or 5, reducing discrimination |
| 6 | NH-12 (min temp) | Min recorded air temperature | 5 bands | **Yes** | **Yes** (NOAA NCEI) | Cold-design implications well-mapped | Good range for the study area |
| 7 | RI-01 | Atmospheric dispersion (3 sub-scores: wind rose, stability, mixing height) | 3 × 5 bands | **Yes** | **Yes** (ERA5 u10/v10/blh) | NS-G-3.2 §4.3 consistent; provisional equal sub-weighting (33/33/33) stated | Equal sub-weighting should be reviewed — wind rose favorability arguably more safety-relevant than mixing height |
| 8 | NS-01 (seasonal) | SPI-12 drought sub-score for cooling | 5 bands | **Yes** | **Yes** (ERA5) | Only the seasonal-variation sub-criterion; full NS-01 bands (source type, volume, stress) still missing | Explicitly flagged as partial in the matrix |

**Summary:** 6 criteria (counting NH-11 and NH-12 sub-bands together, plus RI-01 composite and NS-01 partial) have well-constructed bands. All thresholds are technically defensible. The data sources are correctly assigned (ERA5 for climatology, NOAA NCEI for extremes — matching the methodology §2.5 classification).

### 2.2 Issues with existing bands

| Issue | Criterion | Severity | Recommendation |
|-------|-----------|----------|----------------|
| **NH-11 / NS-01 SPI-12 overlap**: both use identical SPI-12 data with nearly identical bands — risk of double-counting drought in composite score | NH-11 + NS-01 | Medium | Define which criterion "owns" the drought signal. Recommendation: NH-11 captures the meteorological drought hazard; NS-01 should use the SPI-12 only as a sub-score within a broader cooling-water assessment (source type + flow + stress + seasonal). The final NS-01 composite weight should be adjusted so total drought influence ≤ combined weight of NH-11 + NS-01 drought sub-score. |
| **NH-12 max-temp band 5 too generous**: < 33 °C gives score 5, but most Central/Eastern European sites have historical maxima of 35–40 °C, meaning nearly all sites score 3–4 with minimal discrimination | NH-12 | Low | Acceptable for screening. For final ranking, consider narrowing band 5 to < 30 °C or adding half-score resolution. Not blocking for §4. |
| **RI-01 equal sub-weighting**: wind rose direction (dose pathway to population) is arguably more safety-consequential than mean mixing height | RI-01 | Low | Propose revised sub-weights: wind rose 40%, stability fraction 35%, mixing height 25%. Not blocking; current equal weights are stated as provisional. |

---

## 3. Missing scoring bands — prioritised inventory (40 criteria)

### 3.1 Priority classification logic

| Priority | Rule | Count |
|----------|------|------:|
| **P1 — Critical** | Exclusionary or Avoidance criterion with API data available; scoring must be quantitative for traceability | 9 |
| **P2 — High** | Ranking criterion with API data ≥ 70% fill; quantitative bands will meaningfully improve discrimination | 11 |
| **P3 — Medium** | Ranking criterion with API data 20–69% or partial proxy; bands useful but LLM fallback acceptable | 10 |
| **P4 — Low** | Ranking criterion with API data < 20% or LLM-only; categorical/qualitative scoring adequate at Stage 1–2 | 10 |

### 3.2 Full prioritised list

#### P1 — Critical (define before §4)

| # | Criterion | Phase | Data source | Fill % | Proposed band basis | IAEA/EPRI requirement |
|---|-----------|-------|-------------|-------:|---------------------|----------------------|
| 1 | **RI-04** Pop. density | Screen+Rank | GHSL (100 m) | 100% | Pop density per km² at 5/16/25/80 km radii | SSG-35 §A.39 — population density zones are a primary siting discriminant |
| 2 | **NS-05** Land availability | Screen+Rank | CORINE/WC/OSM | 73.7% | Buildable area in hectares | EPRI — ≥ 14 ha nuclear island threshold |
| 3 | **EP-01** Emergency plan feasibility | Screen+Rank | GHSL + DRV-02 composite | 85.8% | Composite score (0–100) | SSG-35 §4.6 — emergency planning feasibility is a primary screen |
| 4 | **EP-02** Evacuation routes | Rank | OSM road density | 100% (suspect) | Road density km/km² | SSG-35 §4.6(a)–(b) |
| 5 | **NS-02** Grid connection | Screen+Rank | ENTSO-E (fixed) + OSM + plant capacity fallback | 82.7% | Distance to substation/HV line in km + voltage class + export capacity | EPRI — grid connection is a primary infrastructure screen |
| 6 | **NS-01** Cooling water (full) | Screen+Rank | HydroRIVERS + GloFAS + WRI | 87.5% | Source type + flow rate + distance + water stress | SSG-35 §4.9 — cooling water availability; currently only SPI-12 sub-score defined |
| 7 | **NS-08** Ecological sensitivity | Screen+Rank | Natura 2000 + WDPA | 73.7% | Distance to nearest protected area in km | SSG-35 Table II-1 No. 10 |
| 8 | **NS-03** Transport access | Screen+Rank | OSM | 73.5% | Distance to highway / rail / waterway in km | EPRI — transport access is a logistics screen |
| 9 | **HI-01** Aircraft crash | Screen+Rank | OurAirports | 100% | Distance to nearest airport in km + airport class | SSG-35 Table II-1 Nos. 2–5 |

#### P2 — High (define before or during §4)

| # | Criterion | Phase | Data source | Fill % | Proposed band basis |
|---|-----------|-------|-------------|-------:|---------------------|
| 1 | **RI-05** Pop. centres distance | Rank | Eurostat GISCO / GeoNames | 100% | Distance to nearest city > 50k in km |
| 2 | **RI-06** Pop. projections | Rank | Eurostat Projections | 100% | Growth rate (%/yr) over plant lifetime |
| 3 | **NH-02** Surface rupture | Screen (Excl.) | EFSM20 / EGDI | 52.5% | Distance to nearest capable fault in km (pass/fail at 8 km; residual ranking beyond) |
| 4 | **NH-03** Liquefaction | Screen+Rank | Zhu + EGDI | 65.5% | Susceptibility class (very low → very high) |
| 5 | **NH-04** Slope stability | Screen+Rank | CopDEM (fixed) | 80.0% | Mean slope angle in degrees (buffer-max issue resolved) |
| 6 | **NH-05** Subsidence / karst | Screen+Rank | WOKAM + EGDI + OneGeology | 84.6% | Karst severity class + mining void presence |
| 7 | **NH-09** River flooding | Screen+Rank | EU Flood + GFMS + EMS | 60.7% | Flood zone class + return-period depth |
| 8 | **NH-08** Coastal flooding | Screen+Rank | EU Flood + GFMS + EMS | 40.1% | Distance to coast + storm surge class + flood zone |
| 9 | **HI-02** Industrial explosions | Screen+Rank | EEA / Seveso | 56.5% | Distance to nearest SEVESO/IED facility in km |
| 10 | **HI-03** Toxic / gas releases | Screen+Rank | EEA / Seveso | 74.3% | Distance to nearest toxic source in km |
| 11 | **HI-06** Military installations | Screen+Rank | OSM (FIX-04) | 86.6% | Distance to nearest military area in km |

#### P3 — Medium (define during §4 or use LLM fallback)

| # | Criterion | Phase | Data source | Fill % | Proposed band basis |
|---|-----------|-------|-------------|-------:|---------------------|
| 1 | **NH-07** Volcanism | Screen (Excl.) | Smithsonian GVP | 66.7% | Distance to nearest Holocene volcano in km (pass/fail binary; ranking nice-to-have) |
| 2 | **HI-04** External fires | Screen+Rank | EEA / Seveso | 50.6% | Distance to nearest flammable storage / pipeline in km |
| 3 | **NH-06** Foundation | Rank | EGDI | 25.0% | Depth to bedrock in m |
| 4 | **NS-04** Site topography | Rank | CopDEM / CORINE / WorldCover | 100% | Favourable land % within site buffer |
| 5 | **EP-03** Physical geography | Rank | OSM waterways | 100% | Major river barrier (bool) + waterway count in EPZ |
| 6 | **EP-04** Special populations | Rank | GHSL + OSM | 31.7% | Count of hospitals + prisons + care homes within EPZ |
| 7 | **RI-02** Surface water dispersion | Rank | None (cross-link NS-01) | 0% | River flow m³/s at nearest reach |
| 8 | **RI-03** Groundwater dispersion | Rank | EGDI | 49.9% | Aquifer type (categorical) |
| 9 | **NH-13** Wildfire | Rank | CORINE proxy (GEE disabled) | 0% | Combustible vegetation % in buffer |
| 10 | **NH-14** Combined hazards | Rank | Derived | 0% | Multi-hazard index (post-computation) |

#### P4 — Low (LLM-derived scores acceptable; define in Annex A if time permits)

| # | Criterion | Phase | Data source | Fill % | Proposed approach |
|---|-----------|-------|-------------|-------:|-------------------|
| 1 | **HI-05** Transport hazards | Rank | None | 0% | LLM tier-3 score (1–5) with "qualitative" flag |
| 2 | **HI-07** EMI | Rank | OSM (FIX-04) | 99.9% | Distance-based band possible but low discriminatory value |
| 3 | **HI-08** Other nuclear installations | Rank | None (PRIS TBD) | 0% | LLM tier-3 score; quantitative after R-06 |
| 4 | **EP-05** Concurrent hazard | Rank | Derived | 0% | Composite after R-03 |
| 5 | **NS-06** Existing infrastructure | Rank | GEE disabled | 0% | LLM tier-3 score |
| 6 | **NS-07** Env. impact (non-rad) | Rank | None | 0% | LLM tier-3 score (no API source) |
| 7 | **NS-09** Socioeconomic impact | Rank | Eurostat partial | 44.6% | Categorical (LLM + Eurostat metadata) |
| 8 | **NS-10** Workforce availability | Rank | Eurostat partial | 44.6% | Categorical (LLM + Eurostat metadata) |
| 9 | **NS-11** C2N synergies | Rank | None (DRV-03 TBD) | 0% | Categorical pending derived field |
| 10 | **NS-12** Regulatory / political | Rank | Eurostat partial | 100% (qualitative) | Country-level categorical; LLM primary |
| 11 | **NS-13** Construction logistics | Rank | None | 0% | LLM tier-3 score |

---

## 4. Proposed scoring bands for P1 criteria

These 9 criteria must have quantitative bands before §4 can execute. Proposals below follow the same format as the existing bands in `06_scoring_matrix.md §8.5`.

### 4.1 RI-04 — Population Density

*Source: GhslPopConnector. DB fields: `pop_density_5km`, `pop_density_16km`, `pop_density_25km`, `pop_density_80km`.*

The RI-04 score is the **minimum** of four sub-scores (one per radius). The controlling sub-score is typically the innermost populated ring.

**Sub-score: 5 km EPZ population density**

| Score | Condition (persons/km²) | Implication |
|-------|------------------------|-------------|
| 5 | < 25 | Very sparsely populated; minimal dose receptor concern |
| 4 | 25 – 100 | Low density; standard EPZ planning adequate |
| 3 | 100 – 250 | Moderate density; enhanced sheltering/evacuation measures |
| 2 | 250 – 500 | High density; significant emergency planning burden |
| 1 | > 500 | Very high density; SMR siting strongly constrained |

**Sub-score: 16 km protective action zone**

| Score | Condition (persons/km²) | Implication |
|-------|------------------------|-------------|
| 5 | < 50 | Very low |
| 4 | 50 – 150 | Low |
| 3 | 150 – 300 | Moderate |
| 2 | 300 – 600 | High |
| 1 | > 600 | Very high |

**Sub-score: 25 km and 80 km radius** — same thresholds as 16 km zone (25 km) and halved thresholds for 80 km (representing the long-range ingestion pathway zone per SSG-35 §A.39). The composite RI-04 score = min(sub-scores at each radius).

Data quality floor: `medium` (GHSL 100 m).

### 4.2 NS-05 — Land Availability

*Source: CorineConnector, WorldCoverConnector, OSM. DB fields: `buildable_area_ha`, `largest_contiguous_ha`.*

| Score | Condition | Implication |
|-------|-----------|-------------|
| 5 | Buildable area ≥ 50 ha AND largest contiguous ≥ 25 ha | Ample space for nuclear island + support facilities |
| 4 | Buildable ≥ 25 ha AND contiguous ≥ 14 ha | Adequate; standard NuScale VOYGR-6 footprint achievable |
| 3 | Buildable ≥ 14 ha AND contiguous ≥ 10 ha | Tight fit; layout constrained but feasible |
| 2 | Buildable ≥ 8 ha OR contiguous ≥ 5 ha | Marginal; requires creative layout or phased development |
| 1 | Buildable < 8 ha AND contiguous < 5 ha | Insufficient for SMR nuclear island without significant land acquisition |

Data quality floor: `medium`. The 14 ha threshold aligns with EPRI A15 (minimum contiguous industrial land for nuclear island).

### 4.3 EP-01 — Emergency Plan Feasibility

*Source: DRV-02 composite (GHSL + OSM + CopDEM). DB field: `ep01_composite_score` (0–100).*

| Score | Condition (composite score) | Implication |
|-------|----------------------------|-------------|
| 5 | ≥ 75 | Highly feasible: low population, good road network, favourable terrain |
| 4 | 60 – 74 | Feasible with standard provisions |
| 3 | 45 – 59 | Feasible but with identified challenges (one sub-score weak) |
| 2 | 30 – 44 | Marginal; significant emergency planning investment required |
| 1 | < 30 | Infeasible or nearly so; `ep01_evacuation_feasible = false` |

Data quality floor: `medium`. Score 1 triggers exclusion review per methodology §2 (EP-01 supports E8).

### 4.4 EP-02 — Evacuation Routes

*Source: OverpassClient (OSM road density). DB fields: `road_density_km_per_km2`, `has_motorway_access`.*

| Score | Condition (road density km/km² within 25 km EPZ) | Implication |
|-------|--------------------------------------------------|-------------|
| 5 | ≥ 2.0 AND motorway access = true | Excellent road network; rapid evacuation capacity |
| 4 | 1.0 – 2.0 OR (≥ 0.8 AND motorway) | Good access; adequate capacity |
| 3 | 0.5 – 1.0 | Moderate; seasonal or capacity constraints possible |
| 2 | 0.3 – 0.5 | Limited; significant route planning needed |
| 1 | < 0.3 | Poor road access; evacuation severely constrained |

Data quality floor: `medium` (OSM). **Warning:** 85% of sites currently show road density = 0.0 (C-1 critical finding from §2.3). EP-02 bands cannot be applied until the Overpass re-run (LL-017 fix) is complete. Sites with 0.0 density should be scored as range (1–3) until re-queried.

### 4.5 NS-02 — Grid Connection

*Source: EntsoEConnector + OverpassClient. DB fields: `nearest_substation_km`, `nearest_hv_line_km`, `hv_line_voltage_kv`.*

The NS-02 score is the **minimum** of a distance sub-score and a voltage sub-score. The ENTSO-E zone-level NTC bug (F-01) has been fixed; where ENTSO-E data is unavailable, the plant's installed capacity is used as fallback.

**Sub-score A: Distance to nearest HV line or substation**

| Score | Condition (km) | Implication |
|-------|---------------|-------------|
| 5 | < 1 | On-site or adjacent; minimal interconnection cost |
| 4 | 1 – 5 | Short new line; standard connection |
| 3 | 5 – 15 | Moderate new-build transmission; feasible |
| 2 | 15 – 30 | Long new line; significant cost and permitting |
| 1 | > 30 | Remote from grid; major infrastructure investment |

**Sub-score B: Voltage class**

| Score | Condition (kV) | Implication |
|-------|---------------|-------------|
| 5 | ≥ 400 | EHV system; ample export capacity |
| 4 | 220 – 399 | HV system; adequate for 462 MWe |
| 3 | 110 – 219 | Intermediate; may require transformer/upgrade |
| 2 | 33 – 109 | Distribution-level; significant upgrade needed |
| 1 | < 33 or unknown | Inadequate without new transmission build |

Composite NS-02 = min(A, B). Data quality floor: `medium` (OSM power infrastructure).

### 4.6 NS-01 — Cooling Water Availability (full composite)

*Extends the existing SPI-12 seasonal sub-score with three additional sub-scores.*

**Sub-score A: Source type**

| Score | Condition | Implication |
|-------|-----------|-------------|
| 5 | Large river (Strahler ≥ 5) or sea / large lake | Abundant cooling; standard once-through or hybrid feasible |
| 4 | Medium river (Strahler 4) or medium lake/reservoir | Adequate; minor seasonal limitations |
| 3 | Small river (Strahler 3) or canal | Limited; cooling tower required year-round |
| 2 | Very small stream (Strahler 1–2) or groundwater only | Marginal; dry/hybrid cooling likely required |
| 1 | No identified water source within 10 km | Dry cooling mandatory; significant cost premium |

**Sub-score B: Distance to cooling source**

| Score | Condition (km) | Implication |
|-------|---------------|-------------|
| 5 | < 0.5 | Adjacent; minimal intake infrastructure |
| 4 | 0.5 – 2.0 | Short pipeline; standard |
| 3 | 2.0 – 5.0 | Moderate distance; feasible but adds cost |
| 2 | 5.0 – 10.0 | Long pipeline; significant civil works |
| 1 | > 10.0 | Remote; cooling supply is a major design constraint |

**Sub-score C: Water stress (WRI Aqueduct)**

| Score | Condition (WRI baseline water stress score) | Implication |
|-------|---------------------------------------------|-------------|
| 5 | < 1.0 (Low) | Minimal competing demand |
| 4 | 1.0 – 2.0 (Low–Medium) | Manageable competition |
| 3 | 2.0 – 3.0 (Medium–High) | Significant competing uses; allocation review needed |
| 2 | 3.0 – 4.0 (High) | Severe competition; regulatory risk for abstraction permits |
| 1 | ≥ 4.0 (Extremely High) | Critical stress; cooling water security at risk |

**Sub-score D: Seasonal drought (SPI-12)** — as already defined in `06_scoring_matrix.md`.

Composite NS-01 = weighted average: Source type 35%, Distance 20%, Water stress 25%, Seasonal drought 20%. Round to nearest integer.

Data quality floor: `medium` for API-populated fields; `low` if only SPI-12 available (ERA5 proxy).

### 4.7 NS-08 — Ecological Sensitivity

*Source: Natura2000Connector, WdpaConnector. DB fields: `n2k_nearest_distance_km`, `wdpa_nearest_distance_km`, `ecological_natural_pct`.*

| Score | Condition | Implication |
|-------|-----------|-------------|
| 5 | Nearest protected area > 25 km AND natural land < 15% of buffer | No ecological conflict; industrial/agricultural landscape |
| 4 | Nearest protected area 10–25 km OR natural land 15–30% | Low conflict; standard EIA adequate |
| 3 | Nearest protected area 5–10 km OR natural land 30–50% | Moderate sensitivity; enhanced EIA and habitat assessment |
| 2 | Nearest protected area 2–5 km OR natural land 50–70% | High sensitivity; ecological mitigation required |
| 1 | Nearest protected area < 2 km OR natural land > 70% | Very high sensitivity; siting strongly constrained |

Data quality floor: `medium` for EU (Natura 2000 authoritative), `low` for non-EU (WDPA only).

### 4.8 NS-03 — Transport Access

*Source: OverpassClient (OSM). DB fields: `nearest_highway_km`, `nearest_rail_km`, `nearest_waterway_km`, `heavy_haul_capable`.*

NS-03 composite = weighted average of 3 sub-scores: Road 40%, Rail 35%, Waterway 25%.

**Sub-score A: Road access (highway distance)**

| Score | Condition (km to motorway/trunk road) | Implication |
|-------|---------------------------------------|-------------|
| 5 | < 2 | Direct motorway/trunk access; heavy-haul capable |
| 4 | 2 – 10 | Short connection via local roads |
| 3 | 10 – 25 | Moderate; requires route planning for heavy loads |
| 2 | 25 – 50 | Distant; significant upgrade or temporary roads needed |
| 1 | > 50 | Very remote; major logistics constraint |

**Sub-score B: Rail access**

| Score | Condition (km to nearest rail line) | Implication |
|-------|-------------------------------------|-------------|
| 5 | < 1 (on-site siding) | Rail access existing; ideal for module delivery |
| 4 | 1 – 5 | Short spur feasible |
| 3 | 5 – 15 | Moderate; new spur needed |
| 2 | 15 – 30 | Distant; road transport only likely |
| 1 | > 30 | No viable rail access |

**Sub-score C: Waterway access (navigable)**

| Score | Condition (km to navigable waterway / port) | Implication |
|-------|---------------------------------------------|-------------|
| 5 | < 2 (Danube / Black Sea port accessible) | Barge delivery of heavy modules feasible |
| 4 | 2 – 10 | Short overland from port/river landing |
| 3 | 10 – 30 | Moderate distance; road transport for large components |
| 2 | 30 – 75 | Distant from navigable water |
| 1 | > 75 or no navigable waterway | Fully road/rail dependent |

Data quality floor: `medium` (OSM).

### 4.9 HI-01 — Aircraft Crash

*Source: OurAirportsConnector. DB fields: `nearest_airport_km`, `nearest_airport_name`, `airport_count`.*

| Score | Condition | Implication |
|-------|-----------|-------------|
| 5 | No airport within 30 km OR only small/private airstrips | Negligible aircraft crash risk |
| 4 | Nearest airport 16–30 km (medium) OR small airport 8–16 km | Low risk; standard aircraft crash analysis adequate |
| 3 | Nearest medium/large airport 8–16 km OR ≥ 3 small airports within 30 km | Moderate; PHA required per NS-G-3.1 |
| 2 | Large airport 5–8 km OR military airfield within 16 km | Elevated risk; detailed flight path analysis required |
| 1 | Any airport < 5 km OR major international airport < 16 km | High risk; SSG-35 Table II-1 triggers avoidance |

Data quality floor: `medium` (OurAirports public dataset).

---

## 5. Proposed scoring bands for P2 criteria

These 11 criteria should have bands defined before or during §4. Brief proposals:

| Criterion | Proposed band variable | Score 5 (best) | Score 3 (mid) | Score 1 (worst) |
|-----------|----------------------|----------------|---------------|-----------------|
| **RI-05** | Distance to city > 50k (km) | > 50 km | 20–30 km | < 10 km |
| **RI-06** | Pop growth rate (%/yr) | < −0.5% (declining) | −0.1% to +0.3% | > +1.0% (rapid growth) |
| **NH-02** | Distance to capable fault (km) | > 50 km | 15–25 km | < 10 km (residual after 8 km exclusion) |
| **NH-03** | Liquefaction susceptibility class | Very low / None | Moderate | Very high |
| **NH-04** | Mean site slope (°) | < 3° | 8–15° | > 25° |
| **NH-05** | Karst + mining severity | No karst, no mining | Minor karst OR inactive mining | Active karst + active/recent mining |
| **NH-09** | Flood zone class | Outside 500-yr zone | 100–500 yr zone | Within 10-yr zone |
| **NH-08** | Coast distance + surge class | > 50 km inland | 5–20 km, low surge | < 2 km, high surge/tsunami |
| **HI-02** | Dist. to nearest SEVESO (km) | > 20 km | 5–10 km | < 2 km |
| **HI-03** | Dist. to nearest toxic source (km) | > 15 km | 5–10 km | < 2 km |
| **HI-06** | Dist. to nearest military (km) | > 30 km | 10–20 km | < 5 km |

Detailed 5-band tables for these should be developed in Annex A. The above thresholds are initial proposals based on SSG-35 Table I-1/II-1 distance guidance and EPRI siting practice.

---

## 6. Sub-weight proposals

### 6.1 Current state

`06_scoring_matrix.md §8.2` defines 7 category-level weights summing to 100%, but states: *"Within each category, individual criteria shall be assigned sub-weights summing to the category allocation. The detailed sub-weight table shall be developed during project execution."*

No sub-weights have been defined yet.

### 6.2 Proposed sub-weights

Sub-weights below reflect: (a) IAEA safety primacy (SF-1 Principle 8), (b) criterion Phase (Screen+Rank weighted higher than Rank-only), (c) data availability (criteria with reliable API data weighted higher than LLM-only), and (d) discriminatory power (criteria where values vary significantly across sites weighted higher).

#### Category 1: Natural Hazards (NH) — 25% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| NH-01 | Seismic ground motion | Screen+Rank | 5.0% | Primary seismic safety criterion; excellent data |
| NH-02 | Surface rupture | Screen (Excl.) | 1.5% | Exclusionary (pass/fail); residual ranking value low |
| NH-03 | Liquefaction | Screen+Rank | 2.5% | Safety-critical geotechnical; moderate data |
| NH-04 | Slope stability | Screen+Rank | 2.0% | Foundation safety; data needs fix (mean vs max) |
| NH-05 | Subsidence / karst | Screen+Rank | 2.0% | Foundation integrity; sparse but important |
| NH-06 | Foundation conditions | Rank | 1.0% | Ranking supplement to NH-03/04/05 |
| NH-07 | Volcanism | Screen (Excl.) | 0.5% | Exclusionary only; no European sites near volcanoes are likely candidates |
| NH-08 | Coastal flooding | Screen+Rank | 2.0% | Relevant for coastal/riverine sites |
| NH-09 | River flooding | Screen+Rank | 3.0% | Broadly relevant across study area |
| NH-10 | Extreme winds | Rank | 1.5% | Structural design driver; good data |
| NH-11 | Extreme precipitation | Rank | 1.5% | Climate resilience; good data |
| NH-12 | Extreme temperatures | Rank | 1.5% | Cooling efficiency driver; good data |
| NH-13 | Wildfire | Rank | 0.5% | Low relevance for CEE coal sites; data sparse |
| NH-14 | Combined hazards | Rank | 0.5% | Derived; value depends on upstream quality |
| | | **Subtotal** | **25.0%** | |

#### Category 2: Human-Induced Hazards (HI) — 10% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| HI-01 | Aircraft crash | Screen+Rank | 2.5% | Well-defined IAEA/EPRI threshold; good data |
| HI-02 | Industrial explosions | Screen+Rank | 2.0% | SEVESO proximity; good EU data |
| HI-03 | Toxic / gas releases | Screen+Rank | 1.5% | Related to HI-02; slightly lower standalone weight |
| HI-04 | External fires | Screen+Rank | 1.0% | Pipeline/storage proximity |
| HI-05 | Transport hazards | Rank | 0.5% | Low data availability; LLM only |
| HI-06 | Military installations | Screen+Rank | 1.5% | Avoidance criterion; data partially available |
| HI-07 | EMI | Rank | 0.5% | Rarely discriminatory |
| HI-08 | Other nuclear | Rank | 0.5% | Rare; few sites affected |
| | | **Subtotal** | **10.0%** | |

#### Category 3: Radiological Impact (RI) — 15% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| RI-01 | Atmospheric dispersion | Rank | 3.0% | Primary dose pathway; good ERA5 data |
| RI-02 | Surface water dispersion | Rank | 1.5% | Secondary pathway; data pending cross-link |
| RI-03 | Groundwater dispersion | Rank | 1.5% | Tertiary pathway; sparse data |
| RI-04 | Population density | Screen+Rank | 5.0% | Primary radiological impact metric; excellent data |
| RI-05 | Population centres | Rank | 2.0% | Supporting population metric |
| RI-06 | Population projections | Rank | 2.0% | 60-year design life consideration |
| | | **Subtotal** | **15.0%** | |

#### Category 4: Emergency Planning (EP) — 10% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| EP-01 | Emergency plan feasibility | Screen+Rank | 4.0% | Composite; directly supports exclusion logic |
| EP-02 | Evacuation routes | Rank | 2.5% | Road network; data needs re-query |
| EP-03 | Physical geography | Rank | 1.5% | Terrain/barrier constraints |
| EP-04 | Special populations | Rank | 1.0% | Hospitals/prisons; sparse data |
| EP-05 | Concurrent hazard | Rank | 1.0% | Derived; pending implementation |
| | | **Subtotal** | **10.0%** | |

#### Category 5: Infrastructure & Grid (NS-01 to NS-03) — 15% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| NS-01 | Cooling water | Screen+Rank | 6.0% | Primary infrastructure criterion; multi-sub-score |
| NS-02 | Grid connection | Screen+Rank | 5.0% | Critical for economic viability; ENTSO-E fixed, plant capacity fallback in place |
| NS-03 | Transport access | Screen+Rank | 4.0% | Heavy-haul logistics; good data |
| | | **Subtotal** | **15.0%** | |

#### Category 6: Site Characteristics (NS-04 to NS-08) — 10% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| NS-04 | Site topography | Rank | 1.5% | Terrain suitability; good data |
| NS-05 | Land availability | Screen+Rank | 3.5% | 14 ha threshold; good data |
| NS-06 | Existing infrastructure | Rank | 1.0% | Reuse potential; GEE disabled |
| NS-07 | Env. impact (non-rad) | Screen+Rank | 1.5% | Qualitative; LLM only |
| NS-08 | Ecological sensitivity | Screen+Rank | 2.5% | Protected area proximity; good EU data |
| | | **Subtotal** | **10.0%** | |

#### Category 7: Socioeconomic & Synergies (NS-09 to NS-13) — 15% total

| Criterion | Name | Phase | Proposed sub-weight | Rationale |
|-----------|------|-------|--------------------:|-----------|
| NS-09 | Socioeconomic impact | Rank | 3.0% | Just-transition relevance; Eurostat partial |
| NS-10 | Workforce availability | Rank | 2.5% | Coal-workforce retraining; Eurostat partial |
| NS-11 | C2N synergies | Rank | 4.5% | Core project differentiator; pending DRV-03 |
| NS-12 | Regulatory / political | Rank | 3.0% | Country-level enabling framework |
| NS-13 | Construction logistics | Rank | 2.0% | Laydown / material supply |
| | | **Subtotal** | **15.0%** | |

### 6.3 Sub-weight sensitivity considerations

Per `06_scoring_matrix.md §8.4`, each category weight must be varied ±20% for sensitivity analysis. The sub-weights proposed above should also be subject to perturbation, specifically:

- **RI-04 (5.0%)** is the single highest sub-weight; verify that ranking is not dominated by population density alone by testing RI-04 at 3.0% and 7.0%.
- **NS-01 (6.0%)** is the highest infrastructure sub-weight; test at 4.0% and 8.0%.
- **NS-11 (4.5%)** is speculative (no data yet); test ranking with NS-11 at 0% (dropped) vs 6.0% (full weight).

---

## 7. IAEA SSG-35 / EPRI alignment assessment

### 7.1 SSG-35 alignment

| SSG-35 requirement | Status in `06_scoring_matrix.md` | Gap? |
|-------------------|--------------------------------|------|
| §4.3 — All relevant natural external events shall be considered | 14 NH criteria defined; NH-13 (wildfire) and NH-14 (combined) have no data | Minor gap — NH-13/14 are ranking-only and have LLM fallback |
| §4.4 — Human-induced external events | 8 HI criteria defined; HI-05/07/08 rank-only with limited data | Minor gap — LLM fallback acceptable at Stage 1–2 |
| §4.5 — Dispersion | RI-01 bands defined (3 sub-scores); RI-02/03 have no bands | **Gap** — RI-02/03 should have at least categorical bands. Cross-link (R-04) will partially address RI-02 |
| §4.6 — Emergency planning | EP-01 composite exists; EP-02/03/04/05 lack bands | **Gap** — EP-02 bands proposed above; EP-03/04/05 can use categorical scoring |
| §4.9 — Cooling water and environmental impact | NS-01 partially banded; NS-07 has no API source | **Gap** — NS-01 full composite proposed above; NS-07 is qualitative by nature |
| §A.39 — Population density zones | RI-04 has 100% data but no scoring bands yet | **Critical gap** — bands proposed above |
| Table I-1 — Natural hazard siting factors | All 14 NH factors mapped to criteria | Aligned |
| Table II-1 — Human-induced hazard siting factors | All 8 HI factors mapped; military (HI-06) data incomplete | Minor gap |
| Annex III — Multi-attribute scoring example | §8.3 composite formula matches SSG-35 Annex III MAUT approach | Aligned |

### 7.2 EPRI 3002023910 alignment

| EPRI requirement | Status | Gap? |
|-----------------|--------|------|
| Exclusionary / Avoidance / Suitability three-tier classification | Mapped to Screen(Excl.) / Screen+Rank / Rank | Aligned |
| Site-technology matching (SMR design envelope) | NH-01 PGA bands reference SMR design envelope | Aligned |
| §4.3 — Meteorological hazards | NH-10/11/12 bands defined | Aligned |
| §4.7 — Grid and cooling infrastructure | NS-01/02 partially banded; NS-01 full bands proposed | Gap being closed |
| §6 — Sensitivity and uncertainty analysis | §8.4 defines weight perturbation (±20%), Monte Carlo (1000 iterations), threshold sensitivity (±25%) | Aligned |
| EPRI "suitability" criteria scoring | 5-point scale (1–5) matches EPRI practice | Aligned |

### 7.3 Gaps requiring attention

| # | Gap | Severity | Action required |
|---|-----|----------|----------------|
| G-1 | **40 of 46 criteria lack quantitative bands** — scoring cannot proceed with reproducible results | **Blocking** | Define at least P1 (9 criteria) bands before §4; P2 during §4; P3–P4 use LLM fallback |
| G-2 | **Sub-weights undefined** — composite score cannot be calculated | **Blocking** | Adopt proposed sub-weights (§6.2 above) or user-revised values before §4 |
| G-3 | **LLM fallback policy not formalised** — §4 must know what to do when API data is absent | **High** | Define: for P4 criteria, use LLM tier-3 score (1–5) directly, flagged as "qualitative / LLM-derived" in the report |
| G-4 | **Score uncertainty propagation for low-quality data** — §8.5 mentions ranges but no formal mapping | **Medium** | Rule: `quality = low` → score ±1 band range; `quality = insufficient` → exclude from composite (use LLM if available, otherwise omit with penalty) |
| G-5 | **NH-11 / NS-01 SPI-12 double-counting** risk | **Medium** | Resolve ownership as proposed in §2.2 |
| G-6 | **RI-01 sub-weight equal split is provisional** | **Low** | Finalise 40/35/25 or equal; document rationale |
| ~~G-7~~ | ~~NS-02 ENTSO-E zone-level NTC bug~~ | ~~Resolved~~ | **FIXED** — connector corrected; plant installed capacity fallback added |
| ~~G-8~~ | ~~NH-04 buffer-max slope interpretation~~ | ~~Resolved~~ | **FIXED** — mean slope now stored correctly |
| G-9 | **EP-02 road density = 0.0 for 85% of sites** (LL-017 silent nulls) | **High** | Overpass re-run with LL-017/018 fixes required before EP-02 scores are reliable |
| G-10 | **EP-04 special populations fill = 31.7%** (missing GHSL tiles + Overpass gaps) | **Medium** | Download remaining GHSL tiles + re-query OSM amenities with LL-017/018 |

---

## 8. Sensitivity analysis parameters (§8.4 review)

The existing sensitivity framework in §8.4 is well-structured. Additional parameters to consider:

| Parameter | Current | Recommendation |
|-----------|---------|---------------|
| **Weight perturbation range** | ±20% per category | Adequate for 7 categories; extend to per-criterion sub-weights for top-5 most influential criteria |
| **Monte Carlo iterations** | 1,000 | Adequate for ranking stability; increase to 10,000 if computational budget allows |
| **Score uncertainty source** | "low quality → ranges" | Formalise: `quality = low` → uniform distribution over ±1 band; `quality = medium` → fixed score; `quality = high` → fixed score |
| **Threshold sensitivity** | ±25% on discretionary thresholds | Add ±1 band test: what happens if every site's score on a given criterion moves ±1? |
| **LLM vs API divergence test** | Not defined | Add: for criteria with both API and LLM scores, compute ranking with API-only, LLM-only, and fused scores; compare top-20 stability |
| **Country balance test** | Not defined | Add: verify top-20 is not artefactually dominated by countries with better data coverage (per S-8 from §8 suggestions) |

---

## 9. Minimum viable scoring configuration for §4

To unblock §4 (scoring), the following must be in place:

| # | Item | Status | Action |
|---|------|--------|--------|
| 1 | **P1 scoring bands** (9 criteria) | Proposed in §4 above | Review and adopt; write to `06_scoring_matrix.md §8.5` |
| 2 | **Sub-weight table** (46 criteria) | Proposed in §6.2 above | Review and adopt; write to `06_scoring_matrix.md §8.2` |
| 3 | **LLM fallback policy** | Not yet formalised | Adopt rule: P4 criteria → LLM 1–5 score, flagged "qualitative" |
| 4 | **Score uncertainty policy** | Partially defined (§8.5 last paragraph) | Adopt: `low` → ±1 band range; `insufficient` → exclude criterion from composite |
| 5 | **EP-02 data fix** | Blocked on LL-017 Overpass re-run | Score as range (1–3) until re-queried; do not use 0.0 values |
| 6 | ~~**NS-02 data fix** (F-01)~~ | **FIXED** — ENTSO-E connector corrected; plant installed capacity used as fallback where ENTSO-E unavailable | No further action |
| 7 | ~~**NH-04 interpretation**~~ | **FIXED** — mean slope now stored correctly | No further action |
| 8 | **EP-04 data fix** | Low fill (31.7%); GHSL tiles + Overpass amenity gaps | Score as range (1–3) for sites without data; document as "data incomplete" |

**Remaining blockers:** Items 1–4 require adoption decisions. Items 5 and 8 (EP-02 road density and EP-04 special populations) are the only data-quality issues still outstanding — both require Overpass re-runs with LL-017/018 fixes. With items 1–4 adopted and items 5/8 handled via documented workarounds, §4.1 (score 1 site) can proceed.

---

## 10. Recommendations summary

| # | Recommendation | Priority | Owner |
|---|---------------|----------|-------|
| R-1 | Adopt the 9 P1 scoring bands proposed in §4 (or revise thresholds) and write them into `06_scoring_matrix.md §8.5` | **Blocking** | User approval required |
| R-2 | Adopt the sub-weight table (§6.2) and write it into `06_scoring_matrix.md §8.2` | **Blocking** | User approval required |
| R-3 | Formalise the LLM fallback policy as an addendum to §8.5 | **High** | Can be drafted by agent |
| R-4 | Formalise the score-uncertainty policy (quality grade → score range rule) | **High** | Can be drafted by agent |
| R-5 | Develop P2 scoring bands (11 criteria) during §4 iterations | **Medium** | Progressive |
| R-6 | Resolve NH-11 / NS-01 SPI-12 overlap | **Medium** | Design decision |
| R-7 | Finalise RI-01 sub-weights (40/35/25 proposed vs current equal) | **Low** | Design decision |
| R-8 | Add country-balance and LLM-vs-API sensitivity tests to §8.4 | **Medium** | Before §4.4 (full scoring) |

---

## 11. Definition of done

§2.5.7 is complete when:

- [x] All 6 existing scoring bands reviewed and issues documented
- [x] All 40 missing bands classified by priority (P1–P4)
- [x] P1 bands (9 criteria) proposed with thresholds
- [x] P2 bands (11 criteria) outlined with indicative thresholds
- [x] Sub-weights proposed for all 46 criteria across 7 categories
- [x] IAEA SSG-35 and EPRI 3002023910 alignment assessed
- [x] Sensitivity analysis parameters reviewed
- [x] Minimum viable scoring configuration defined
- [x] Recommendations with priority and ownership documented
