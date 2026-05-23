<!-- man_hours: 6.0 -->
## 8. Scoring Matrix Design

### 8.1 Scoring Methodology

Each ranking criterion shall be assessed using a five-level scoring scale:

| Score | Descriptor | Definition                                                          |
| ----- | ---------- | ------------------------------------------------------------------- |
| 5     | Excellent  | Significantly exceeds requirements; minimal or no mitigation needed |
| 4     | Good       | Meets requirements with minor favourable conditions                 |
| 3     | Acceptable | Meets minimum requirements; standard mitigation may be needed       |
| 2     | Marginal   | Approaches minimum requirements; significant mitigation required    |
| 1     | Poor       | Does not meet requirements without major engineering intervention   |

Binary exclusionary criteria (Section 7, Phase = "Screen (Excl.)") are scored Pass/Fail. A Fail on any exclusionary criterion eliminates the site regardless of other scores.

### 8.2 Weighting Framework

Criterion weights shall reflect the relative importance of each criterion category, informed by IAEA principles (safety primacy) and the project's coal-to-nuclear conversion objectives.

| Category                                         | Weight Allocation | Rationale                                              |
| ------------------------------------------------ | ----------------- | ------------------------------------------------------ |
| Safety-Related: Natural Hazards (NH)             | 25%               | Primary safety concern per SF-1 Principle 8            |
| Safety-Related: Human Induced Hazards (HI)       | 10%               | Defence-in-depth from external threats                 |
| Safety-Related: Radiological Impact (RI)         | 15%               | Population protection per NS-R-3 §2.27                 |
| Safety-Related: Emergency Planning (EP)          | 10%               | Emergency response feasibility per NS-R-3 §2.29        |
| Non-Safety: Infrastructure & Grid (NS-01–03)     | 15%               | Critical for coal-to-nuclear economic viability        |
| Non-Safety: Site Characteristics (NS-04–08)      | 10%               | Physical and environmental suitability                 |
| Non-Safety: Socioeconomic & Synergies (NS-09–13) | 15%               | Coal-to-nuclear business case and workforce transition |

**Total: 100%**

Within each category, individual criteria shall be assigned sub-weights summing to the category allocation. The detailed sub-weight table shall be developed during project execution and documented in the report Annex A.

### 8.3 Composite Score Calculation

For each candidate site _s_, the composite score _S(s)_ is calculated as:

\[
S(s) = \sum\_{i=1}^{n} w_i \cdot c_i(s)
\]

Where:

- \( w_i \) = normalised weight for criterion _i_ (sum of all weights = 1.0)
- \( c_i(s) \) = score (1–5) for site _s_ on criterion _i_
- \( n \) = total number of ranking criteria

### 8.4 Sensitivity Analysis

To ensure ranking robustness:

1. **Weight perturbation:** Each category weight shall be varied ±20% (with complementary adjustment of other weights to maintain sum = 100%). Rankings shall be re-computed for each perturbation.
2. **Score uncertainty:** Where data quality is low, criterion scores shall be assigned as ranges (e.g., 2–4). Monte Carlo simulation (1,000 iterations) using uniform distributions within score ranges shall produce a ranking stability index.
3. **Threshold sensitivity:** Discretionary screening thresholds (Section 6.3.2) shall be varied ±25% to assess the impact on the candidate site pool.

Results shall be reported as a ranking stability table showing whether each site's position in the top-15 is robust or sensitive to assumption changes.

---

### 8.5 Per-Criterion Scoring Bands (Annex A — in development)

This section documents the quantitative bands that map raw data values to the 1–5 score scale. It is populated as connectors are implemented and validated. Sub-weights within each category are developed in parallel and will be compiled into the full Annex A table before final report assembly.

**Column conventions:**

| Column | Meaning |
|--------|---------|
| Score | 1–5 per §8.1 |
| Condition | Numeric threshold or categorical rule applied to the named field(s) |
| Primary data source | Connector and DB field that supplies the input value |
| Data quality floor | Minimum `*_quality` grade required to trust the score |

Scores assigned from `quality = low` data must be presented as **ranges** (e.g., 2–4) in the final report and propagated as score uncertainty in the Monte Carlo sensitivity analysis (§8.4).

---

#### NH-01 — Seismic Ground Motion (PGA at 475-year return period)

*Source: EFEHR / SHARE connector (S-01). DB field: `nh01_pga_475yr_g` in `site_natural_hazards`.*  
*Note: PGA values triggering potential exclusion (E1 basis) are reviewed separately by a qualified seismic engineer; scoring bands below apply only to the Phase 3 ranking.*

| Score | Condition | Descriptor |
|-------|-----------|-----------|
| 5 | PGA < 0.05 g | Very low seismicity (shield / stable craton) |
| 4 | 0.05 – 0.10 g | Low seismicity (standard structural design) |
| 3 | 0.10 – 0.20 g | Moderate seismicity (enhanced design provisions) |
| 2 | 0.20 – 0.30 g | High seismicity (significant structural cost impact) |
| 1 | > 0.30 g | Very high seismicity (SMR design envelope margin likely exceeded; expert review required) |

Data quality floor: `medium`. Sites with `quality = low` carry a score range of ±1 band.

---

#### NH-10 — Extreme Winds (straight wind / maximum recorded gust)

*Source: NOAA NCEI connector (S-11). DB field: `max_wind_speed_ms` or `extreme_wind_ms` in `site_natural_hazards`.*  
*⚠ ERA5 monthly means (S-04) are NOT used for this criterion — monthly mean gusts severely underestimate true extremes. See methodology §2.5.*

| Score | Condition (10-min mean or gust at site) | Descriptor |
|-------|-----------------------------------------|-----------|
| 5 | Max recorded < 25 m/s | Low wind region; standard EN 1991-1-4 wind class |
| 4 | 25 – 30 m/s | Moderate (Central/Eastern Europe typical) |
| 3 | 30 – 36 m/s | Elevated (coastal, elevated terrain, or storm-track exposure) |
| 2 | 36 – 42 m/s | High (enhanced structural wind-load design required) |
| 1 | > 42 m/s | Extreme (cyclone-class design loads; significant structural cost premium) |

Data quality floor: `medium`. If only annual mean wind speed is available (no storm record), score as range.

---

#### NH-11 — Extreme Precipitation: Drought (SPI-12)

*Source: ERA5 connector (S-04). DB field: `spi12_min` in `site_natural_hazards`.*  
*ERA5 monthly precipitation (tp) → SPI-12 using McKee et al. (1993). Reliable at quality = medium.*

SPI-12 interpretation reference: 0 to −1 = normal; −1 to −1.5 = moderate drought; −1.5 to −2 = severe; < −2 = extreme.

| Score | Condition (minimum SPI-12 over 1991–2020 record) | Cooling-water implication |
|-------|--------------------------------------------------|--------------------------|
| 5 | SPI-12 min > −1.0 | No meaningful drought in 30-year record; cooling supply reliable |
| 4 | −1.5 to −1.0 | Occasional moderate drought; low seasonal cooling-water stress |
| 3 | −2.0 to −1.5 | Periodic severe drought episodes; cooling contingency plans needed |
| 2 | −2.5 to −2.0 | Extreme drought on record; dry-year cooling vulnerability is real |
| 1 | < −2.5 | Exceptional drought; cooling-water reliability seriously threatened in severe dry years |

Data quality floor: `medium` (ERA5 monthly means are the standard SPI-12 input; acceptable).

---

#### NH-11 — Extreme Precipitation: Snow burden

*Source: ERA5 connector (S-04). DB field: `snow_months_per_year` in `site_natural_hazards`.*  
*ERA5 monthly snowfall (sf, mm water equivalent) → months exceeding 1 mm w.e. threshold. Reliable at quality = medium.*

| Score | Condition (mean snow months/year) | Structural / accessibility implication |
|-------|------------------------------------|----------------------------------------|
| 5 | 0 – 1 month | Negligible winter design load; site accessible year-round |
| 4 | 2 – 3 months | Low snow burden (mild winter zone) |
| 3 | 4 – 5 months | Moderate (most of continental Central/Eastern Europe) |
| 2 | 6 – 7 months | Significant winter operations constraint; enhanced design needed |
| 1 | ≥ 8 months | Severe winter zone; arctic-grade access and snow-load design required |

---

#### NH-12 — Extreme Temperatures: Air temperature maxima

*Source: NOAA NCEI connector (S-11). DB field: `extreme_temp_max_c` in `site_natural_hazards`.*  
*⚠ ERA5 monthly t2m means (S-04) are NOT used for this criterion — monthly means underestimate true records by 3–8 °C. See methodology §2.5.*

| Score | Condition (maximum recorded air temperature) | Cooling-system implication |
|-------|-----------------------------------------------|---------------------------|
| 5 | < 33 °C | Temperate; cooling efficiency rarely constrained |
| 4 | 33 – 36 °C | Moderate summer extreme; standard design margin adequate |
| 3 | 36 – 39 °C | Significant heat stress; thermal discharge compliance may be periodically challenging |
| 2 | 39 – 42 °C | Severe; dry/hybrid cooling backup considered prudent |
| 1 | > 42 °C | Extreme; cooling system design significantly constrained by ambient temperature |

#### NH-12 — Extreme Temperatures: Air temperature minima

*Source: NOAA NCEI connector (S-11). DB field: `extreme_temp_min_c` in `site_natural_hazards`.*

| Score | Condition (minimum recorded air temperature) | Cold-design implication |
|-------|-----------------------------------------------|------------------------|
| 5 | > −15 °C | Mild winter extreme; no special cold-weather design |
| 4 | −15 to −20 °C | Moderate cold; standard winter provisions |
| 3 | −20 to −25 °C | Significant cold; winterisation measures needed |
| 2 | −25 to −30 °C | Harsh continental winter; pipe freeze and HVAC design cost premium |
| 1 | < −30 °C | Extreme cold; arctic-grade design required |

Data quality floor for NH-12 temperature: `medium` (NOAA NCEI station records). If no station within 50 km, score must be presented as a range.

---

#### RI-01 — Atmospheric Dispersion

*Source: ERA5 connector (S-04). ERA5 monthly u10, v10, BLH → wind rose, Pasquill-Gifford class distribution, mean mixing height.*  
*Quality = medium. Suitable for comparative ranking (Phase 3); not for regulatory dispersion licensing.*

RI-01 is a composite of three sub-scores. In the absence of finalized Annex A sub-weights, provisional equal weighting applies (33% / 33% / 33%). The combined RI-01 score = weighted average of the three sub-scores below, rounded to nearest integer.

**Sub-score A: Wind rose favorability**  
*DB field: `wind_rose_json` → compute angular difference between `prevailing_direction_deg` and bearing to nearest city > 50,000 people (from RI-05 `nearest_city_bearing_deg`).*

| Sub-score | Condition (angle between prevailing wind and bearing-to-nearest-city) | Dispersion implication |
|-----------|------------------------------------------------------------------------|----------------------|
| 5 | ≥ 135° offset (wind blows away or perpendicular-plus) | Highly favourable; releases carried away from population |
| 4 | 90° – 135° | Mostly favourable (crosswind to away) |
| 3 | 45° – 90° | Mixed; occasional transport toward population |
| 2 | 22° – 45° | Predominantly toward population |
| 1 | < 22° offset | Prevailing wind directly toward nearest city; worst-case dose pathway |

**Sub-score B: Stable atmosphere fraction (Pasquill-Gifford F+E class)**  
*DB field: `pg_class_f_fraction` + `pg_class_e_fraction` in `site_radiological`.*

| Sub-score | Condition (% of hours in F or E stability class) | Dispersion implication |
|-----------|--------------------------------------------------|----------------------|
| 5 | < 10 % | Highly dispersive; excellent mixing year-round |
| 4 | 10 – 20 % | Good dispersion; infrequent stable episodes |
| 3 | 20 – 30 % | Typical European lowland; moderate stable fraction |
| 2 | 30 – 40 % | Valley or coastal inversion-prone site |
| 1 | > 40 % | Strongly stable; high dose-rate concern during stable episodes |

**Sub-score C: Mean annual mixing height**  
*DB field: `mean_mixing_height_m` in `site_radiological`.*

| Sub-score | Condition (mean boundary layer height, annual mean) | Dispersion implication |
|-----------|------------------------------------------------------|----------------------|
| 5 | > 800 m | Excellent vertical mixing; dilution very effective |
| 4 | 600 – 800 m | Good mixing |
| 3 | 400 – 600 m | Adequate mixing (most lowland European sites) |
| 2 | 200 – 400 m | Shallow boundary layer; reduced dilution capacity |
| 1 | < 200 m | Very poor mixing; significant concern for radiological dose accumulation |

---

#### NS-01 — Cooling Water Availability: Seasonal drought stress (ERA5 contribution)

*NS-01 primary scoring (source type, volume, competing demands) relies on national hydrological data — not yet fully integrated. ERA5 (S-04) contributes to the seasonal variation sub-criterion only.*  
*DB field: `spi12_min` (same as NH-11 drought). A drought index score below 3 on NH-11 should trigger a `low` confidence flag on NS-01 seasonal reliability.*

| Sub-score | Condition | Cooling implication |
|-----------|-----------|-------------------|
| 5 | SPI-12 min > −1.0 | No meaningful drought stress; cooling-water availability reliable year-round |
| 4 | −1.5 to −1.0 | Occasional seasonal stress; manageable with modest reservoir sizing |
| 3 | −2.0 to −1.5 | Periodic drought stress; storage or alternative intake needed for dry years |
| 2 | −2.5 to −2.0 | Significant drought risk; dry-year cooling reliability is a genuine design constraint |
| 1 | < −2.5 | Severe drought risk; cooling-water security requires major engineering solution |

*Note: This sub-score contributes to NS-01 only when national hydrological flow data is absent. Once national data is integrated, the seasonal variation score should be recalculated using station-observed flow records.*

---

### 8.6 Annex A Development Plan

The full sub-weight table (individual criterion weights within each category, summing to the category allocation) and the remaining per-criterion scoring bands are deferred to **Annex A of the final report**. Development priority:

| Priority | Criteria group | Blocker |
|----------|---------------|---------|
| 1 (now) | NH-01, NH-10, NH-11, NH-12, RI-01 | Connector data available; bands defined above |
| 2 | RI-04, RI-05, EP-01 | Data available (population, road density connectors implemented) |
| 3 | NH-09, NH-08, NS-02, NS-03 | Flood connector and OSM infrastructure connectors implemented; thresholds TBD |
| 4 | NS-09–NS-13 (socioeconomic) | Requires qualitative expert judgement; categorical scoring rules |
| 5 | NH-03, NH-04, NH-06, RI-02, RI-03 | National geotechnical and hydrogeological data needed |

Cross-reference: `report/methodology/methodology.md §2.5` for ERA5 data reliability classification. `requirements/05_1_siting_criteria_natural_hazards.md` and `05_5_siting_criteria_non_safety.md` for criterion definitions.
