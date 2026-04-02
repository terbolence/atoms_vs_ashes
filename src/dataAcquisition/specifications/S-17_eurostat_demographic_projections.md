# S-17: Eurostat Demographic Projections / National Statistical Offices — Integration Specification

**Source ID:** S-17
**Phase:** 2 — Core Ranking
**Estimated effort:** 16 h
**Criteria served:** RI-05 (settlement hierarchy confirmation — Priority 2), RI-06 (projected density, urban expansion, future receptor growth — Priority 1), NS-09 (socioeconomic impact — Priority 1), NS-10 (workforce, retraining — Priority 1), NS-12 (public opinion proxy — Priority 1)
**Connector slug:** `eurostat_projections`

---

## 1. Source Profile

| Field | Value |
|-------|-------|
| Name | Eurostat EUROPOP2023 Population Projections + Eurostat Regional Statistics + National Statistical Office supplements |
| Provider | European Commission — Eurostat (Statistical Office of the European Union); national statistical offices for non-EU countries |
| URLs | Eurostat data browser: `https://ec.europa.eu/eurostat/databrowser/`; Statistics API (JSON-stat): `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/`; SDMX 2.1 API: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/`; EUROPOP2023 metadata: `https://ec.europa.eu/eurostat/cache/metadata/en/proj_23n_esms.htm`; Population projections portal: `https://ec.europa.eu/eurostat/web/population-demography/population-projections` |
| Protocol | REST API (JSON-stat 2.0 via Statistics API; SDMX/JSON via SDMX 2.1 API); bulk CSV download |
| Auth | **None required for Eurostat.** National statistical office portals may require registration for some countries. |
| Formats | JSON-stat 2.0 (Statistics API primary), SDMX-JSON (SDMX API), CSV (bulk download), TSV (legacy) |
| Spatial coverage | **EUROPOP2023 national projections:** 30 countries (27 EU + IS, NO, CH). Covers 12 of 23 in-scope countries (PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT). **EUROPOP2019 regional projections:** NUTS3-level for EU-27 + EFTA, 1,169 regions (proj_19rp3). **Eurostat candidate-country data:** TR, RS, ME, MK, AL have partial demographic statistics via `cand_` dataset variants. **No Eurostat coverage:** BA, XK, MD, UA, BY, AM. |
| Temporal coverage | EUROPOP2023 projections: 2022–2100 (base year 2022, published March 2024). EUROPOP2019 regional projections: 2019–2100. Eurostat demographic statistics: annual, most series 2000–2023. |
| Update cadence | EUROPOP projections: every 4–5 years (2014, 2019, 2023). Regional projections lag national by ~1–2 years. Demographic statistics: annual updates (Q1 for prior year). |
| License | Eurostat copyright: free for all uses with attribution. Reuse policy: Commission Decision 2011/833/EU. Attribution: "Source: Eurostat, EUROPOP2023" |
| IAEA references | SSG-35 §A.39 (population distribution around the site — projected over facility lifetime); SSR-1 §6 (site and design interface — population considerations); SSG-35 §4.9 (non-safety criteria — socioeconomic considerations) |

---

## 2. Extraction Strategy

### 2.1 Pathway comparison

| Pathway | Classification | Viability | Notes |
|---------|---------------|-----------|-------|
| **Eurostat Statistics API — EUROPOP2023 national projections (proj_23np)** | **Preferred** | High | National-level population projections by age and sex, 2022–2100, for 12 in-scope EU countries. One API call per dataset per country set. Provides 60-year population growth trajectory (matching SMR design life). Small JSON responses (~50 KB per query). |
| **Eurostat Statistics API — EUROPOP2023 demographic indicators (proj_23ndbi)** | **Preferred (complementary)** | High | Demographic balances: births, deaths, net migration, old-age dependency ratio, median age. National level. Provides the structural demographic context: is the region growing, stable, or declining? |
| **Eurostat Statistics API — EUROPOP2019 regional projections (proj_19rp3)** | **Preferred (complementary)** | High | NUTS3-level population projections from the 2019 round. EUROPOP2023 regional projections may not yet be published; EUROPOP2019 regional data remains the most recent regional projection available. Provides sub-national spatial differentiation. |
| **Eurostat Statistics API — Regional demographic statistics** | **Preferred (complementary)** | High | Current population, age structure, and demographic change by NUTS3 region (`DEMO_R_PJANGRP3`, `DEMO_R_GIND3`). Already partially covered by S-16; this connector retrieves the projection-relevant subset (age structure, dependency ratio, growth rate). |
| **Eurostat Statistics API — Regional economic/labour statistics** | **Preferred (complementary)** | High | NUTS2/NUTS3-level datasets for GDP (`NAMA_10R_3GDP`), employment by sector (`LFST_R_LFE2EN2N`), educational attainment (`EDAT_LFSE_04`), housing stock. Required for NS-09, NS-10. |
| **Eurostat bulk download facility** | **Fallback** | Medium | Full TSV/CSV files for any Eurostat dataset at `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/`. Useful for large extractions but less convenient than JSON-stat for targeted queries. |
| **National statistical offices (non-EU countries)** | **Supplementary** | Low–Medium | TR (TurkStat), RS (SORS), ME (MONSTAT), MK (SSO), AL (INSTAT), BA (BHAS), XK (KAS), MD (NBS), UA (SSSU), BY (Belstat), AM (ArmStat). Each has different API/download formats. Implemented as static JSON lookup tables with manually curated projections rather than automated API connectors, given the heterogeneity. |
| **UN World Population Prospects (WPP)** | **Fallback** | Medium | UN DESA WPP 2024 provides national-level projections for all 23 in-scope countries. Coarser than Eurostat but universally available. Useful as fallback for non-Eurostat countries. Available via API at `https://population.un.org/dataportal/api/`. |
| **Manual NSO data compilation** | **Rejected (for automation)** | Low | Many NSOs publish projections only as PDF reports or static Excel files. Not programmable. Manually compiled data should be stored as curated JSON reference files under `sources/nso_projections/`. |

### 2.2 Preferred extraction design

**Fact:** The connector requires five complementary data products from Eurostat, plus supplementary national-level data for non-EU countries:

1. **EUROPOP2023 national projections (proj_23np)** — Population projections by single-year age group and sex for 2022–2100. Provides the core 60-year population trajectory for each in-scope EU country. Answers: "What will the national population be in 2050/2080 under baseline assumptions?"

2. **EUROPOP2023 demographic indicators (proj_23ndbi)** — Projected old-age dependency ratio, median age, total fertility rate, life expectancy, net migration rate. Answers: "Is the population ageing, growing, or declining? What is the migration pressure?"

3. **EUROPOP2019 regional projections (proj_19rp3)** — NUTS3-level projected population for 2019–2060. Answers: "Which sub-national regions around each site are growing or declining?" This provides site-level spatial differentiation within countries.

4. **Eurostat regional demographic statistics** — Current population structure by age (`DEMO_R_PJANGRP3`), crude demographic growth rate (`DEMO_R_GIND3`). Provides the current baseline for trend extrapolation in regions where projections are unavailable.

5. **Eurostat regional socioeconomic statistics** — GDP per capita (`NAMA_10R_3POPGDP`), employment by economic sector (`LFST_R_LFE2EN2N`), educational attainment (`EDAT_LFSE_04`), housing permits/stock. Provides the socioeconomic context for NS-09 and NS-10.

6. **National statistical office supplements** — For non-EU countries, curated JSON files with national population projections from TurkStat, UN WPP, or individual NSO publications. Stored under `sources/nso_projections/{country_code}.json`.

**Requirement:** The connector must:
1. Query EUROPOP2023 national projections for all in-scope EU countries
2. Query EUROPOP2019 regional projections for NUTS3 regions containing or near in-scope sites
3. Query current demographic and socioeconomic statistics for relevant NUTS2/NUTS3 regions
4. Load curated NSO projection data for non-EU countries from local JSON files
5. For each site, compute projected population density, growth trajectory, workforce indicators, and socioeconomic metrics
6. Fall back to UN WPP national projections when Eurostat coverage is unavailable

**Inference:** Population projections are fundamentally a national/regional attribute, not a point attribute. The connector maps each site to its NUTS3 region (using the NUTS3 lookup already implemented in S-16) and retrieves the regional projection. Where only national projections exist, the national trajectory is applied with a regional scaling factor derived from the current NUTS3/national population ratio.

### 2.3 Eurostat Statistics API query patterns

#### EUROPOP2023 national population projections (proj_23np)

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/proj_23np
  ?format=JSON
  &lang=en
  &projection=BSL          # baseline scenario
  &sex=T                   # total (both sexes)
  &age=TOTAL               # all ages
  &geo=RO&geo=BG&geo=PL... # in-scope EU countries
  &time=2030&time=2040&time=2050&time=2060&time=2070&time=2080
```

Returns JSON-stat 2.0 document with projected total population per country per projection year.

**Fact:** EUROPOP2023 projection variants:

| Code | Variant | Relevance |
|------|---------|-----------|
| BSL | Baseline | **Primary** — central scenario |
| LMIG | Lower migration | Sensitivity test — fewer immigrants |
| HMIG | Higher migration | Sensitivity test — more immigrants |
| LFRT | Lower fertility | Sensitivity test — fewer births |
| LMRT | Lower mortality | Sensitivity test — longer life expectancy |
| NMIG | No migration | Sensitivity test — zero net migration |

**Requirement:** Query BSL (baseline) as primary. Optionally query LMIG and HMIG as sensitivity bounds for the projection uncertainty band.

#### EUROPOP2023 demographic indicators (proj_23ndbi)

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/proj_23ndbi
  ?format=JSON
  &lang=en
  &projection=BSL
  &indic_de=MEDAGEPOP       # median age
  &geo=RO&geo=BG...
  &time=2030&time=2050&time=2080
```

**Fact:** Key demographic indicators available in `proj_23ndbi`:

| Code | Indicator | Relevance |
|------|-----------|-----------|
| MEDAGEPOP | Median age of population | Workforce ageing indicator (NS-10) |
| OLDDEP | Old-age dependency ratio (65+/15–64) | Dependency burden; workforce pressure (NS-10) |
| CNMIGRATRT | Crude net migration rate | Migration pressure affecting growth (RI-06) |
| NATGROWRT | Natural population growth rate | Organic growth/decline (RI-06) |
| GROWRT | Total population growth rate | Composite growth rate (RI-06) |
| GBIRTHRT | Gross birth rate | Demographic vitality |
| GDEATHRT | Gross death rate | Mortality trend |

#### EUROPOP2019 regional projections (proj_19rp3)

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/proj_19rp3
  ?format=JSON
  &lang=en
  &projection=BSL
  &sex=T
  &age=TOTAL
  &geo=RO411&geo=RO414...   # NUTS3 codes for regions containing sites
  &time=2030&time=2040&time=2050
```

Returns NUTS3-level projected population. Provides spatial differentiation: a site in a declining rural NUTS3 region within a growing country gets a different projection than a site in a growing urban region.

**Inference:** EUROPOP2019 regional projections extend to 2060 (shorter horizon than EUROPOP2023 national projections which go to 2100). For the 60-year SMR design life, NUTS3 projections provide coverage to ~2060; beyond that, the connector extrapolates using the national growth rate trajectory from EUROPOP2023.

#### Regional demographic and socioeconomic statistics

```
# Population by age group and NUTS3
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/DEMO_R_PJANGRP3
  ?format=JSON&lang=en&sex=T&age=Y15-64&age=Y_GE65&age=TOTAL
  &geo=RO411&geo=RO414...&time=2023

# GDP per capita by NUTS3
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/NAMA_10R_3POPGDP
  ?format=JSON&lang=en&unit=EUR_HAB
  &geo=RO411&geo=RO414...&time=2022

# Employment by sector NUTS2
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/LFST_R_LFE2EN2N
  ?format=JSON&lang=en&sex=T&age=Y15-64
  &nace_r2=TOTAL&nace_r2=B-E&nace_r2=F&nace_r2=D
  &geo=RO41&geo=RO42...&time=2023

# Educational attainment NUTS2
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/EDAT_LFSE_04
  ?format=JSON&lang=en&sex=T&age=Y25-64
  &isced11=ED5-8              # tertiary education
  &geo=RO41&geo=RO42...&time=2023
```

### 2.4 NSO supplement data format

For non-EU countries, curated JSON files follow a standardised schema:

```json
{
  "country_code": "UA",
  "country_name": "Ukraine",
  "source": "State Statistics Service of Ukraine (SSSU) + UN WPP 2024",
  "source_url": "https://ukrstat.gov.ua/",
  "retrieved_date": "2026-03-15",
  "projection_variant": "medium",
  "base_year": 2023,
  "projections": {
    "2030": {"population": 36500000, "growth_rate": -0.008},
    "2040": {"population": 33200000, "growth_rate": -0.009},
    "2050": {"population": 30100000, "growth_rate": -0.010},
    "2060": {"population": 27500000, "growth_rate": -0.009},
    "2080": {"population": 23800000, "growth_rate": -0.007}
  },
  "median_age_2050": 48.2,
  "old_age_dependency_2050": 0.42,
  "quality_note": "Based on UN WPP 2024 medium variant; war displacement effects create high uncertainty"
}
```

**Requirement:** NSO supplement files are manually curated and stored under `sources/nso_projections/`. The connector loads them at startup and uses them as fallback for countries without Eurostat coverage. The project should include template JSON files for all 11 non-EU in-scope countries.

---

## 3. Criterion Mapping

| Criterion | Sub-criterion | Support level | Derived variable | Evidence grade | Source query | Notes |
|-----------|--------------|---------------|-----------------|---------------|-------------|-------|
| **RI-05** | Settlement hierarchy | Indirect (confirmatory) | `projected_urban_growth_rate`, `urban_expansion_pressure_index` | Ranking | proj_19rp3 + DEMO_R_GIND3 | **Inference:** S-17 is Priority 2 for RI-05 (S-16 is Priority 1). S-17 supplements S-16's static settlement hierarchy with projected growth: a "periurban" zone today may be "suburban" in 30 years if growth is strong. The connector computes an urban expansion pressure index from the regional growth rate differential (urban NUTS3 vs rural NUTS3 within the same country). |
| **RI-06** | Projected density | Direct (primary) | `projected_pop_2050`, `projected_pop_2080`, `pop_change_pct_2050`, `pop_change_pct_2080`, `projected_density_2050_persons_km2` | Screening + Ranking | proj_23np + proj_19rp3 | **Fact:** S-17 is the Priority 1 source for RI-06 projected density. EUROPOP2023 provides national population trajectories; EUROPOP2019 provides NUTS3 spatial disaggregation. The connector computes projected population density within EPZ radii by applying the regional growth factor to S-16's baseline population density. |
| **RI-06** | Urban expansion | Direct (primary) | `urban_expansion_pressure`, `growth_classification` | Ranking | proj_19rp3 + DEMO_R_GIND3 | **Inference:** Urban expansion is inferred from differential growth rates: NUTS3 regions with growth rates exceeding the national average indicate expansion pressure. The connector classifies each site's region as "rapid_growth" / "moderate_growth" / "stable" / "moderate_decline" / "rapid_decline". |
| **RI-06** | Future receptor growth | Direct (primary) | `population_trajectory_60yr`, `receptor_growth_factor`, `projection_uncertainty_band` | Ranking | proj_23np (BSL + LMIG + HMIG) | **Fact:** The 60-year receptor growth factor is the ratio of projected population to current population over the SMR design life (2026–2086). Querying multiple projection variants (baseline, lower migration, higher migration) provides an uncertainty band. |
| **NS-09** | Employment | Direct (primary) | `employment_total`, `employment_industry_pct`, `employment_construction_pct`, `employment_energy_pct`, `unemployment_rate` | Ranking | LFST_R_LFE2EN2N + LFST_R_LFU3RT | **Fact:** S-17 is Priority 1 for NS-09 employment. NUTS2-level employment data by sector indicates the regional labour market structure. Regions with high industrial/energy employment have proven capacity to support large construction/operation projects. |
| **NS-09** | Tax revenue | Indirect (proxy) | `gdp_per_capita_eur`, `gdp_growth_5yr_pct`, `fiscal_capacity_index` | Ranking | NAMA_10R_3POPGDP + NAMA_10R_3GDP | **Inference:** Regional GDP per capita and growth trend serve as proxies for fiscal capacity. A nuclear project generates substantial tax revenue; regions with lower GDP per capita may benefit more (higher relative impact), while regions with higher GDP indicate stronger institutional capacity. |
| **NS-09** | Community benefit | Indirect (proxy) | `deprivation_index`, `gdp_gap_to_national_avg` | Ranking | NAMA_10R_3POPGDP + DEMO_R_GIND3 | **Inference:** Community benefit potential is approximated by the gap between regional and national GDP per capita. Regions below the national average have higher potential benefit from nuclear investment. |
| **NS-10** | Existing workforce | Direct (primary) | `working_age_pop`, `employment_rate`, `industrial_employment_pct`, `energy_sector_employment`, `tertiary_education_pct` | Ranking | DEMO_R_PJANGRP3 + LFST_R_LFE2EN2N + EDAT_LFSE_04 | **Fact:** S-17 is Priority 1 for NS-10 workforce. Working-age population (15–64) from NUTS3 demographics, employment rate and sectoral structure from NUTS2, and educational attainment from NUTS2. |
| **NS-10** | Retraining potential | Direct (primary) | `coal_energy_employment`, `retraining_pool_index`, `projected_workforce_2050` | Ranking | LFST_R_LFE2EN2N (NACE B-E, D) + proj_19rp3 (Y15-64) | **Inference:** Retraining potential is highest in regions with existing energy/mining/heavy-industry workforce that may be displaced by coal phase-out. The connector cross-references with I-4 GEM Coal Plant Tracker to identify regions with coal-to-nuclear transition potential. Employment in NACE sector D (electricity/gas) and B-E (industry) indicates retrainable workforce. |
| **NS-12** | Public opinion proxy | Indirect (weak proxy) | `nuclear_policy_stance`, `energy_sector_dependence`, `education_level` | Ranking (weak) | LFST_R_LFE2EN2N (D sector) + EDAT_LFSE_04 + curated policy JSON | **Inference:** S-17 does not directly measure public opinion. Proxies include: energy sector employment share (higher → more familiarity with energy infrastructure), educational attainment (correlated with nuanced views), and curated country-level nuclear policy stance data. This is a weak proxy; NS-12 primarily depends on N-21 national regulatory/policy research (Phase 4). |

### Screening thresholds (from methodology)

| Decision | Criterion | Condition | Action |
|----------|-----------|-----------|--------|
| — | RI-06 | All sub-criteria are ranking-only | No exclusionary screening from this source |
| — | NS-09, NS-10, NS-12 | All sub-criteria are ranking-only | No exclusionary screening from this source |
| — | RI-05 | S-17 provides confirmatory data only; S-16 handles the screening-relevant data | No exclusionary screening from this source |

**Fact:** None of the criteria served by S-17 have exclusionary (E-rule) or avoidance (A-rule) thresholds. All outputs feed the scoring module for site ranking.

**Requirement:** The connector persists projection and socioeconomic metrics. The scoring module consumes the persisted values to rank sites. The connector does NOT produce `ScreeningResult` rows.

---

## 4. Regional Applicability

### 4.1 Coverage assessment

| Country group | Countries | EUROPOP2023 national | EUROPOP2019 regional (NUTS3) | Eurostat demographics | Eurostat socioeconomic | NSO supplement | Notes |
|---------------|-----------|---------------------|-----------------------------|-----------------------|------------------------|----------------|-------|
| EU member states | PL, CZ, SK, HU, AT, SI, HR, RO, BG, EE, LV, LT | **Full** | **Full** | **Full** | **Full** | Not needed | Complete Eurostat coverage for all datasets. 12 countries with authoritative projections. |
| EU candidate / accession | TR, RS, ME, MK, AL | **None** (not in EUROPOP) | **None** | **Partial** (`cand_` datasets) | **Partial** | **Required** | Turkey and Western Balkans candidates have some NUTS-equivalent regions and limited Eurostat statistics. Population projections must come from national statistical offices or UN WPP. |
| Eastern Europe non-EU | UA, MD, BY | **None** | **None** | **None** | **None** | **Required** | No Eurostat coverage. National statistical offices have varying data quality. UN WPP 2024 provides universal national-level fallback. |
| Armenia | AM | **None** | **None** | **None** | **None** | **Required** | ArmStat publishes national projections. UN WPP provides fallback. |
| Bosnia and Herzegovina | BA | **None** | **None** | **None** | **None** | **Required** | BHAS (Agency for Statistics) has limited projection capacity. UN WPP is the primary source. |
| Kosovo | XK | **None** | **None** | **None** | **None** | **Required** | KAS (Kosovo Agency of Statistics) has limited data. UN WPP provides fallback. |

**Fact:** Of the 23 in-scope countries, 12 have full EUROPOP2023+2019 coverage (the EU members). 5 candidate countries have partial Eurostat statistics but no projections. 6 countries have no Eurostat coverage at all.

**Requirement:** The connector must:
1. Provide full EUROPOP-based population projections for EU-12 countries
2. Provide partial projections for candidate-5 (TR, RS, ME, MK, AL) using available Eurostat statistics + NSO supplement + UN WPP fallback
3. For non-covered countries (BA, XK, MD, UA, BY, AM), use curated NSO supplement files with UN WPP fallback
4. Write `DataQualityFlag` with appropriate level: `high` for EU-12, `medium` for candidate-5, `low` for NSO-supplement countries, `insufficient` if no projection data is available

### 4.2 Non-EU country supplement sources

| Country | NSO | Projection availability | Fallback |
|---------|-----|------------------------|----------|
| TR | TurkStat (TURKSTAT) | National projections published; regional projections available for 81 provinces | UN WPP 2024 |
| RS | SORS (Statistical Office) | National projections available; partial regional data | UN WPP 2024 |
| ME | MONSTAT | Limited; census-based estimates only | UN WPP 2024 |
| MK | SSO (State Statistical Office) | National projections available | UN WPP 2024 |
| AL | INSTAT | National projections available | UN WPP 2024 |
| BA | BHAS | Very limited; post-2013 census estimates | UN WPP 2024 |
| XK | KAS | Limited; recent census (2011) basis | UN WPP 2024 |
| MD | NBS (National Bureau of Statistics) | National projections available; high uncertainty due to emigration | UN WPP 2024 |
| UA | SSSU (State Statistics Service) | National projections available; high uncertainty due to conflict displacement | UN WPP 2024 |
| BY | Belstat | National projections published | UN WPP 2024 |
| AM | ArmStat | National projections available | UN WPP 2024 |

**Requirement:** Include pre-curated JSON supplement files for all 11 non-EU countries. Use UN WPP 2024 medium variant as the baseline. Where NSO data is more recent or detailed, layer it on top.

---

## 5. Integration Design

### 5.1 Component architecture

```
EurostatProjectionsConnector
│
│  ── Data retrieval (API queries + local files, cached) ──────────
├── __init__(settings)                # config from connectors.eurostat_projections
├── health_check()                    # GET small query to Statistics API → verify connectivity
├── _query_statistics_api(dataset, params) → dict
│     # httpx GET to Statistics API
│     # parse JSON-stat 2.0 → dict
│     # handle rate limiting (courtesy 0.5s delay), retry on 5xx
│
│  ── EUROPOP projection queries ──────────────────────────────────
├── fetch_national_projections(country_codes, years, variant)
│     # dataset=proj_23np, projection=BSL
│     # returns dict[country_code → NationalProjection]
├── fetch_national_indicators(country_codes, years, indicators)
│     # dataset=proj_23ndbi
│     # returns dict[country_code → DemographicIndicators]
├── fetch_regional_projections(nuts3_codes, years)
│     # dataset=proj_19rp3, projection=BSL
│     # returns dict[nuts3_code → RegionalProjection]
│
│  ── Current statistics queries ──────────────────────────────────
├── fetch_regional_demographics(nuts3_codes, year)
│     # DEMO_R_PJANGRP3 + DEMO_R_GIND3
│     # returns dict[nuts3_code → RegionalDemographics]
├── fetch_regional_economics(nuts2_codes, year)
│     # NAMA_10R_3POPGDP + LFST_R_LFE2EN2N + EDAT_LFSE_04
│     # returns dict[nuts2_code → RegionalEconomics]
│
│  ── NSO supplement loader ───────────────────────────────────────
├── load_nso_supplements()
│     # read sources/nso_projections/*.json
│     # returns dict[country_code → NsoProjection]
│
│  ── Single-site API (core) ──────────────────────────────────────
├── fetch(lat, lon, **params) → EurostatProjectionsResult
│     # 1. identify NUTS3 region (via S-16 shared NUTS3 index)
│     # 2. look up national + regional projections
│     # 3. compute growth trajectory
│     # 4. look up socioeconomic metrics
│     # 5. assemble result
│
│  ── Batch API (operates on DB sites) ────────────────────────────
├── enrich_site(site_id, session, run_id)
├── enrich_batch(session, run_id, site_ids=None, country_codes=None)
├── enrich_all(session, run_id)
│
│  ── Pure computation (no I/O, fully testable) ───────────────────
├── _compute_growth_trajectory(national, regional, base_pop)
│     # national trajectory + regional scaling → projected pop per decade
├── _compute_receptor_growth_factor(current_pop, projected_pop_2080)
│     # ratio over 60-year design life
├── _compute_projection_uncertainty(bsl, lmig, hmig)
│     # uncertainty band from multiple projection variants
├── _compute_urban_expansion_pressure(regional_growth, national_growth)
│     # differential growth rate → expansion index
├── _classify_growth(growth_rate) → str
│     # "rapid_growth" | "moderate_growth" | "stable" | "moderate_decline" | "rapid_decline"
├── _compute_workforce_indicators(demographics, economics, education)
│     # working-age pop, industrial/energy employment, education level
├── _compute_socioeconomic_impact(economics, national_avg)
│     # GDP gap, deprivation index, fiscal capacity
├── _compute_retraining_potential(economics, coal_employment)
│     # cross-reference with coal sector data
├── _identify_nuts_region(lat, lon) → (nuts3_code, nuts2_code) | None
│     # delegate to shared NUTS3 index from S-16
├── _validate_result(result) → EurostatProjectionsResult
│
│  ── JSON-stat parsing (pure, fully testable) ────────────────────
├── _parse_jsonstat_projection(json_data) → dict[str, dict[str, float]]
│     # geo → {year → population}
├── _parse_jsonstat_indicators(json_data) → dict[str, dict[str, float]]
│     # geo → {indicator → value}
├── _parse_jsonstat_demographics(json_data) → dict[str, RegionalDemographics]
├── _parse_jsonstat_economics(json_data) → dict[str, RegionalEconomics]
│
├── close()
├── __enter__ / __exit__
```

### 5.2 Data flow — data ingestion (run once per batch, cached)

```
ingest_projections(session, run_id, reference_year=2023)
  │
  ├─ Check cache: projection data within cache_ttl_days?
  │    → if yes: load from cache → return
  │
  ├─ EU-12 in-scope countries:
  │    │
  │    ├─ fetch_national_projections(EU_12, years=[2030,2040,2050,2060,2070,2080], "BSL")
  │    │    → proj_23np baseline
  │    ├─ fetch_national_projections(EU_12, years=[2050,2080], "LMIG")
  │    │    → lower migration sensitivity
  │    ├─ fetch_national_projections(EU_12, years=[2050,2080], "HMIG")
  │    │    → higher migration sensitivity
  │    ├─ fetch_national_indicators(EU_12, years=[2030,2050,2080], indicators=ALL)
  │    │    → proj_23ndbi demographic indicators
  │    │
  │    ├─ Identify NUTS3 regions containing in-scope sites (from DB)
  │    ├─ fetch_regional_projections(nuts3_codes, years=[2030,2040,2050])
  │    │    → proj_19rp3 regional projections
  │    │
  │    ├─ Identify NUTS2 parent regions for NUTS3 codes
  │    ├─ fetch_regional_demographics(nuts3_codes, reference_year)
  │    │    → DEMO_R_PJANGRP3, DEMO_R_GIND3
  │    ├─ fetch_regional_economics(nuts2_codes, reference_year)
  │    │    → NAMA_10R_3POPGDP, LFST_R_LFE2EN2N, EDAT_LFSE_04
  │    │
  │    └─ On error per query: log, mark dataset unavailable, continue
  │
  ├─ Candidate countries (TR, RS, ME, MK, AL):
  │    ├─ Attempt fetch_regional_demographics (partial coverage)
  │    ├─ Attempt fetch_regional_economics (partial coverage)
  │    └─ Load NSO supplement for projection data
  │
  ├─ Non-EU countries (BA, XK, MD, UA, BY, AM):
  │    └─ load_nso_supplements()
  │
  ├─ Cache all retrieved data locally as JSON
  ├─ Persist DataSource provenance records
  │
  └─ Return IngestionResult
       → n_countries_with_projections, n_regions_with_data, n_nso_supplements_loaded
```

### 5.3 Data flow — single site

```
fetch(lat, lon) → EurostatProjectionsResult
  │
  ├─ Ensure data loaded (ingest_projections if not cached)
  │
  ├─ _identify_nuts_region(lat, lon)
  │    → (nuts3_code, nuts2_code) or None
  │
  ├─ Determine country_code from coordinates
  │
  ├─ IF EU-12 country:
  │    ├─ Look up national projection → growth trajectory
  │    ├─ Look up NUTS3 regional projection → regional scaling
  │    ├─ _compute_growth_trajectory(national, regional, base_pop)
  │    ├─ _compute_receptor_growth_factor(current, projected_2080)
  │    ├─ _compute_projection_uncertainty(bsl, lmig, hmig)
  │    ├─ _compute_urban_expansion_pressure(regional, national)
  │    ├─ Look up NUTS3 demographics → working age, dependency
  │    ├─ Look up NUTS2 economics → GDP, employment, education
  │    ├─ _compute_workforce_indicators(demographics, economics, education)
  │    ├─ _compute_socioeconomic_impact(economics, national_avg)
  │    ├─ quality = "high"
  │    └─ Assemble result
  │
  ├─ IF candidate country (TR, RS, ME, MK, AL):
  │    ├─ Look up NSO supplement for national projection
  │    ├─ Attempt NUTS-equivalent regional demographics if available
  │    ├─ Use available Eurostat statistics (partial)
  │    ├─ quality = "medium"
  │    └─ Assemble result with available data, null for missing
  │
  ├─ IF non-covered country (BA, XK, MD, UA, BY, AM):
  │    ├─ Look up NSO supplement for national projection
  │    ├─ No regional disaggregation available
  │    ├─ No Eurostat statistics available
  │    ├─ quality = "low"
  │    └─ Assemble result with national projection only
  │
  └─ _validate_result(result)
       → range checks, completeness verification
```

### 5.3b Data flow — batch enrichment

```
enrich_batch(session, run_id, site_ids=None, country_codes=None) → BatchResult
  │
  ├─ Ensure data loaded (ingest_projections if not cached)
  ├─ Ensure DataSource provenance records
  │    → "eurostat_europop2023"
  │    → "eurostat_europop2019_regional"
  │    → "eurostat_regional_statistics"
  │    → "nso_supplements"
  │
  ├─ Load sites from DB
  │
  ├─ FOR each site in sites:
  │    │
  │    ├─ Cache check: SiteAttribute for (site_id, "RI-06", run_id)?
  │    │    → if exists → skip (all criteria written together)
  │    │
  │    ├─ fetch(site.latitude, site.longitude) → EurostatProjectionsResult
  │    │    → on failure: log, write DataQualityFlag, continue
  │    │
  │    ├─ persist_result(session, site.site_id, result, run_id)
  │    │    → session.merge() × 4 SiteAttribute rows
  │    │      (RI-06, NS-09, NS-10, NS-12)
  │    │    → session.add() DataQualityFlag if needed
  │    │    → session.commit()  ← per site
  │    │
  │    └─ Log "projections_site_complete"
  │
  └─ Return BatchResult
```

**Inference:** Like S-13 (ENTSO-E), the data is country/region-level, so per-site computation is a lookup after the ingestion phase. Sites in the same NUTS3 region share identical regional projections; site differentiation comes from the shared projection data and from cross-referencing with S-16 baseline population density.

### 5.4 CRS handling

**Fact:** Eurostat projection data is non-geographic (tabular, indexed by NUTS code or country code). The connector maps sites to NUTS regions via the shared NUTS3 spatial index (already implemented in S-16). No CRS transformation is needed within this connector.

**Requirement:** The `_identify_nuts_region` function delegates to the S-16 `EurostatGiscoConnector`'s NUTS3 lookup (point-in-polygon with Shapely). If S-16 has not been loaded, the connector loads NUTS3 boundaries independently.

### 5.5 Caching strategy

| Cache target | TTL | Size estimate | Rationale |
|-------------|-----|---------------|-----------|
| National projections (proj_23np, all variants) | 365 days | ~100 KB total | EUROPOP2023 published March 2024; next round ~2027–2028. |
| Demographic indicators (proj_23ndbi) | 365 days | ~50 KB total | Same publication cycle as projections. |
| Regional projections (proj_19rp3) | 365 days | ~500 KB | EUROPOP2019; will be superseded when 2023 regional projections are published. |
| Regional demographics (DEMO_R_PJANGRP3 etc.) | 90 days | ~200 KB per dataset | Updated annually. |
| Regional economics (NAMA_10R_3POPGDP etc.) | 90 days | ~200 KB per dataset | Updated annually. |
| NSO supplement files | Manual update | ~5 KB per country | Curated; updated when new NSO publications are identified. |

**Requirement:** Cache directory: `sources/eurostat_projections/`. Subdirectories: `national/`, `regional/`, `statistics/`, `nso/`. Cache key per dataset: `projections:{dataset_code}:{variant}:{year}`.

### 5.6 Error handling specifics

| Scenario | Handling |
|----------|----------|
| Eurostat API returns HTTP 416 (no data for this combination) | Valid — some NUTS3 regions or countries may not have data for the requested combination. Set value to `null`. Quality flag `low`. |
| Eurostat API returns HTTP 500 (server error) | Retry 3× with exponential backoff. If persistent, use stale cache. Log `projections_api_error`. |
| Eurostat API returns partial data (some NUTS3 codes missing from response) | Parse available data. Mark missing NUTS3 regions with quality flag `insufficient`. |
| proj_19rp3 dataset unavailable or deprecated | Fall back to applying national growth rate uniformly. Quality flag `medium`. Log `projections_regional_unavailable`. |
| EUROPOP2023 replaced by future round (e.g., EUROPOP2028) | Dataset code is configurable in YAML. Update config when new round is published. Old cached data remains valid until new data is loaded. |
| NSO supplement file missing for a country | Log `projections_nso_missing`. Set all projection fields to `null`. Quality flag `insufficient`. Note that N-21 (Phase 4) national research is required. |
| NSO supplement file has invalid JSON | Log `projections_nso_parse_error`. Skip this country's supplement. Quality flag `insufficient`. |
| NUTS3 code format changed in NUTS 2024 vs 2021 | The connector uses NUTS 2024 boundaries (from S-16). proj_19rp3 uses NUTS 2021 codes. Implement a NUTS code translation table for affected regions (typically only a few reclassifications per country). |
| Site outside all NUTS3 polygons (non-EU country) | Expected for non-EU countries. Use country-level projection from NSO supplement. No NUTS-specific data. |
| Network timeout | Retry 3× with exponential backoff (2s, 4s, 8s). Use stale cache if available. |

---

## 6. Result Dataclasses

### 6.1 EurostatProjectionsResult (top-level)

```
EurostatProjectionsResult
├── lat: float
├── lon: float
├── country_code: str                           # ISO 3166-1 alpha-2
├── nuts3_code: str | None                      # NUTS3 region (if available)
├── nuts2_code: str | None                      # NUTS2 region (if available)
├── population_projection: PopulationProjectionResult | None
├── socioeconomic: SocioeconomicResult | None
├── workforce: WorkforceResult | None
├── policy_proxy: PolicyProxyResult | None
├── source: str                                 # "eurostat_europop2023" | "nso_supplement" | "un_wpp_2024"
├── reference_year: int                         # base year (e.g., 2022 for EUROPOP2023)
├── quality: str                                # "high" | "medium" | "low" | "insufficient"
├── error: str | None
├── to_dict() → dict
```

### 6.2 PopulationProjectionResult

```
PopulationProjectionResult
├── base_population: int                        # current population (national or NUTS3)
├── base_year: int
├── projected_pop_2030: int | None
├── projected_pop_2040: int | None
├── projected_pop_2050: int | None
├── projected_pop_2060: int | None
├── projected_pop_2080: int | None
├── pop_change_pct_2050: float | None           # % change base_year → 2050
├── pop_change_pct_2080: float | None           # % change base_year → 2080
├── receptor_growth_factor_60yr: float | None   # ratio: pop(base+60) / pop(base)
├── projection_lo_2050: int | None              # lower bound (LMIG variant)
├── projection_hi_2050: int | None              # upper bound (HMIG variant)
├── projection_lo_2080: int | None
├── projection_hi_2080: int | None
├── growth_classification: str                  # "rapid_growth" | "moderate_growth" | "stable" | "moderate_decline" | "rapid_decline"
├── urban_expansion_pressure: float | None      # regional growth rate minus national average
├── median_age_2050: float | None
├── old_age_dependency_2050: float | None       # 65+ / 15–64
├── net_migration_rate_projected: float | None  # per 1000 inhabitants
├── projection_source: str                      # "europop2023" | "europop2019_regional" | "nso" | "un_wpp"
├── projection_variant: str                     # "baseline" | "medium"
├── spatial_level: str                          # "nuts3" | "national" | "subnational_nso"
├── to_dict() → dict
```

### 6.3 SocioeconomicResult

```
SocioeconomicResult
├── nuts3_gdp_million_eur: float | None
├── nuts3_gdp_per_capita_eur: float | None
├── national_gdp_per_capita_eur: float | None
├── gdp_gap_to_national_pct: float | None       # (regional - national) / national × 100
├── gdp_growth_5yr_pct: float | None            # 5-year GDP growth trend
├── fiscal_capacity_index: float | None         # normalised 0–1 relative to EU-27 median
├── deprivation_index: float | None             # composite: GDP gap + unemployment + education gap
├── to_dict() → dict
```

### 6.4 WorkforceResult

```
WorkforceResult
├── working_age_pop: int | None                 # 15–64 (NUTS3)
├── working_age_pct: float | None               # 15–64 / total (NUTS3)
├── projected_working_age_2050: int | None      # projected 15–64
├── employment_rate_pct: float | None           # NUTS2
├── unemployment_rate_pct: float | None         # NUTS2
├── employment_industry_pct: float | None       # NACE B-E as % of total (NUTS2)
├── employment_construction_pct: float | None   # NACE F as % of total (NUTS2)
├── employment_energy_pct: float | None         # NACE D as % of total (NUTS2)
├── tertiary_education_pct: float | None        # ISCED 5-8 as % of 25–64 (NUTS2)
├── retraining_pool_index: float | None         # normalised 0–1; higher = more retrainable workforce
├── coal_energy_employment: int | None          # cross-reference with I-4 GEM (if available)
├── to_dict() → dict
```

### 6.5 PolicyProxyResult

```
PolicyProxyResult
├── nuclear_policy_stance: str | None           # "favourable" | "neutral" | "unfavourable" | "moratorium" | "phaseout" | "unknown"
├── energy_sector_dependence: float | None      # NACE D employment / total employment
├── education_index: float | None               # tertiary % normalised
├── policy_source: str | None                   # "curated_2026" | "nso_supplement"
├── to_dict() → dict
```

### 6.6 NsoProjection (internal)

```
NsoProjection
├── country_code: str
├── country_name: str
├── source: str
├── source_url: str
├── retrieved_date: str
├── projection_variant: str
├── base_year: int
├── projections: dict[str, dict[str, float]]    # year → {population, growth_rate}
├── median_age_2050: float | None
├── old_age_dependency_2050: float | None
├── quality_note: str | None
```

### 6.7 BatchResult / SiteEnrichmentSummary

Reuse shared `BatchResult` and `SiteEnrichmentSummary` dataclasses from the shared `connectors.common` module.

---

## 7. Data Contracts

### 7.1 Persistence mapping

| Project field | Target table | Column | Source |
|---------------|-------------|--------|--------|
| Population projection + trajectory | `site_attributes` | `value_numeric` = `receptor_growth_factor_60yr`, `value_text` = `growth_classification`, `value_json` = full PopulationProjectionResult | `PopulationProjectionResult.to_dict()` |
| Criterion ID (projections) | `site_attributes` | `criterion_id` | `"RI-06"` |
| Socioeconomic metrics | `site_attributes` | `value_numeric` = `gdp_per_capita_eur`, `value_text` = null, `value_json` = full SocioeconomicResult | `SocioeconomicResult.to_dict()` |
| Criterion ID (socioeconomic) | `site_attributes` | `criterion_id` | `"NS-09"` |
| Workforce indicators | `site_attributes` | `value_numeric` = `working_age_pop`, `value_text` = null, `value_json` = full WorkforceResult | `WorkforceResult.to_dict()` |
| Criterion ID (workforce) | `site_attributes` | `criterion_id` | `"NS-10"` |
| Policy proxy | `site_attributes` | `value_numeric` = null, `value_text` = `nuclear_policy_stance`, `value_json` = full PolicyProxyResult | `PolicyProxyResult.to_dict()` |
| Criterion ID (policy) | `site_attributes` | `criterion_id` | `"NS-12"` |
| Source provenance | `data_sources` | `name` | `"eurostat_europop2023"`, `"eurostat_europop2019_regional"`, `"eurostat_regional_statistics"`, `"nso_supplements"` |
| Quality flag | `data_quality_flags` | `level`, `detail` | Per site/criterion |

**Requirement:** Persist **four** `SiteAttribute` rows per site from this connector:

1. `criterion_id="RI-06"`, `value_numeric=receptor_growth_factor_60yr`, `value_text=growth_classification`, `value_json={projected populations at decade intervals, uncertainty band, demographic indicators, urban expansion pressure, projection source/variant/spatial level}`
2. `criterion_id="NS-09"`, `value_numeric=gdp_per_capita_eur`, `value_json={GDP, GDP gap, GDP growth, fiscal capacity, deprivation index}`
3. `criterion_id="NS-10"`, `value_numeric=working_age_pop`, `value_json={employment rates, sectoral breakdown, education, retraining index, projected workforce}`
4. `criterion_id="NS-12"`, `value_text=nuclear_policy_stance`, `value_json={policy stance, energy dependence, education index, source}`

### 7.2 Screening result mapping

The connector does NOT produce `ScreeningResult` rows directly. All criteria served by S-17 are ranking-only. The scoring module reads the persisted `SiteAttribute` values.

### 7.3 Database migration and FK requirements

#### CRITERION_IDS constant

**Requirement:** The connector's `models.py` must declare:

```python
CRITERION_IDS = ("RI-06", "NS-09", "NS-10", "NS-12")
```

**Fact:** This constant is consumed by `test_connector_db_compatibility.py::TestCriteriaSeedCompleteness`.

#### Alembic migration

**Fact:** Alembic migration `005_seed_all_siting_criteria.py` already seeds all four criteria:
- `RI-06`: "Population Projections" — category: radiological_impact, phase: ranking, description: "Projected density over 60-year design life. Ranking only."
- `NS-09`: "Socioeconomic Impact" — category: non_safety, phase: ranking, description: "Employment, tax revenue, community benefit, public acceptance. Ranking only."
- `NS-10`: "Workforce Availability" — category: non_safety, phase: ranking, description: "Existing skilled workforce, retraining potential, housing. Ranking only."
- `NS-12`: "Regulatory/Political Environment" — category: non_safety, phase: ranking, description: "National nuclear policy, public opinion, licensing pathway. Ranking only."

**Requirement:** No new Alembic migration is needed. Verify with:

```bash
pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v
```

### 7.4 Relationship with S-16 (Eurostat GISCO)

**Fact:** S-16 and S-17 share several data domains but serve different criteria with different temporal perspectives:

| Domain | S-16 provides | S-17 provides | Coordination |
|--------|--------------|--------------|--------------|
| Population density | Current (Census 2021 via GEOSTAT 1km grid) → RI-04 | Projected (EUROPOP 2023/2019) → RI-06 | S-17 uses S-16 baseline density as anchor |
| City proximity | Current distances + settlement hierarchy → RI-05 | Projected urban growth rate → RI-05 (confirmatory) | S-17 supplements S-16 with growth trend |
| GDP/employment | Current NUTS3 GDP, NUTS2 employment → NS-09 (partial) | Historical trend + structural detail → NS-09 (primary) | S-17 adds sectoral detail and time trends not in S-16 |
| Workforce | Current working-age population → NS-10 (partial) | Projected workforce + education + retraining → NS-10 (primary) | S-17 adds forward-looking workforce indicators |

**Requirement:** The connector must:
1. Share the NUTS3 spatial index with S-16 (avoid re-downloading NUTS3 boundaries)
2. Not duplicate S-16 data — if S-16 has already persisted RI-04 and basic NS-09 data, S-17 writes separate rows for RI-06, NS-09, NS-10, NS-12 with complementary (not overlapping) `criterion_id` values
3. For NS-09, S-17 writes its own `SiteAttribute` row with the projection/trend-enriched socioeconomic data. The scoring module merges S-16 and S-17 NS-09 contributions during ranking.

**Open Issue:** S-16 writes an NS-09 row with current GDP/employment. S-17 also targets NS-09 with trend-enriched data. Two options: (a) S-17 writes a separate NS-09 row with a distinct `source_id`, allowing the scoring module to choose or merge; (b) S-17 enriches the same NS-09 row. Option (a) is preferred for provenance clarity but may conflict with the `uq_site_criterion_run` unique constraint. Resolution: S-17 uses `session.merge()` to upsert — if S-16 has already written NS-09, S-17 **replaces** it with the richer dataset (since S-17 is Priority 1 for NS-09). This is acceptable because S-17 includes all S-16 NS-09 fields plus additional trend data.

---

## 8. Validation and QA

| Check | Type | Rule | Failure action |
|-------|------|------|---------------|
| Population non-negative | Semantic | All projected populations ≥ 0 | Flag `insufficient` |
| Growth factor plausibility | Semantic | `0.3 ≤ receptor_growth_factor_60yr ≤ 3.0` (population cannot halve or triple in 60 years for any European country) | Flag `low` if outside |
| Population change monotonic with time distance | Logic | For declining populations: pop_2030 ≥ pop_2050 ≥ pop_2080. For growing: pop_2030 ≤ pop_2050 ≤ pop_2080 | Flag `low` if violated (may indicate variant mixing) |
| Projection uncertainty band | Logic | `projection_lo ≤ baseline ≤ projection_hi` for each year | Flag `low` if violated |
| GDP per capita plausibility | Semantic | `1,000 ≤ GDP/capita ≤ 200,000` EUR | Flag `low` if outside |
| Employment rate range | Semantic | `20 ≤ employment_rate ≤ 90` % | Flag `low` if outside |
| Unemployment rate range | Semantic | `0 ≤ unemployment_rate ≤ 50` % | Flag `low` if outside |
| Education rate range | Semantic | `5 ≤ tertiary_education_pct ≤ 80` % | Flag `low` if outside |
| NUTS code format | Schema | 5-character code matching country prefix for NUTS3; 4-character for NUTS2 | Reject invalid codes |
| Country-to-projection mapping | Schema | Each in-scope country has either Eurostat projection or NSO supplement | Quality `insufficient` if neither |
| JSON-stat response structure | Schema | Response contains expected `class: "dataset"` and `value` array | Log `projections_parse_error`, retry |
| Projection base year | Temporal | EUROPOP2023 base year is 2022; warn if data appears to use different base | Log warning |
| NSO supplement freshness | Temporal | `retrieved_date` within 2 years of current date | Flag `medium` if older |
| Old-age dependency ratio | Semantic | `0.1 ≤ old_age_dependency ≤ 1.0` | Flag `low` if outside |
| Median age plausibility | Semantic | `25 ≤ median_age ≤ 65` | Flag `low` if outside |
| Nuclear policy stance valid | Schema | Must be one of: "favourable", "neutral", "unfavourable", "moratorium", "phaseout", "unknown" | Default to "unknown" |

---

## 9. Operational Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeout per HTTP request | 30 s | Configurable via `connectors.eurostat_projections.timeout_s`. |
| Retry policy | 3 attempts, exponential backoff (2s base, 60s max, jitter) | Consistent with project defaults. |
| Rate limiting | **None required.** Eurostat Statistics API has no formal rate limit. | Client-side courtesy delay: 0.5s between requests (configurable). |
| Concurrency | Single-threaded sequential | Courtesy to Eurostat servers. |
| API calls per ingestion | ~15–25 (6 national projection queries + 5–10 regional queries + 5–8 statistics queries) | Small, well-defined queries. |
| Total data download per ingestion | ~2–5 MB | All JSON-stat responses are small. |
| Per-site computation | ~0.1 ms | NUTS lookup + growth trajectory calculation. |
| Execution modes | 1. **Data ingestion**: `ingest_projections(session, run_id, year)` — fetch all projection + statistics data | Must run before site enrichment |
| | 2. **Single site**: `fetch(lat, lon)` → `EurostatProjectionsResult` (no DB) | |
| | 3. **Single site + persist**: `enrich_site(site_id, session, run_id)` | |
| | 4. **Batch**: `enrich_batch(session, run_id, ...)` / `enrich_all(session, run_id)` | |
| Batch commit strategy | Per-site commit | Each site committed independently. |
| Batch resumability | Cache check on `(site_id, "RI-06", run_id)` | Re-run same `run_id` → skips already-enriched sites. |
| Idempotency | Guaranteed via `uq_site_criterion_run` unique constraint + `session.merge()` | |
| Observability | Log events: `projections_national_query_ok`, `projections_regional_query_ok`, `projections_statistics_query_ok`, `projections_nso_loaded`, `projections_api_error`, `projections_parse_error`, `projections_nso_missing`, `projections_site_complete`, `projections_batch_progress`, `projections_batch_done` | Include `country_code`, `nuts3_code`, `dataset_code`, `site_id`, `elapsed_ms`, `index`, `total` |

### Two-phase execution

**Phase A — Data ingestion (API queries, run infrequently):**
- ~15–25 Eurostat API calls with 0.5s courtesy delay = ~10–15 seconds
- Parse JSON-stat responses
- Load NSO supplement files
- Total first-run: ~20–30 seconds
- Subsequent runs (cached): < 1 second

**Phase B — Site enrichment (lookup, instant):**
- Per-site: ~0.1 ms (NUTS lookup + growth trajectory computation)
- 500 sites: < 1 second
- No network calls during enrichment

### Timing estimate

| Sites | Data ingestion (first run) | Per-site compute | Estimated wall time |
|-------|---------------------------|-----------------|-------------------|
| 1 | ~20–30 s (API queries) | ~0.1 ms | ~30 s (ingestion-dominated) |
| 10 | Cached | ~1 ms | < 1 s |
| 100 | Cached | ~10 ms | < 1 s |
| 500 | Cached | ~50 ms | < 1 s |

---

## 10. Testing Strategy

### 10.1 Unit tests (no network)

| Test class | What it tests | Fixture data |
|-----------|--------------|-------------|
| `TestParseJsonstatProjection` | `_parse_jsonstat_projection(json)` → dict[country → {year → pop}] | Sample JSON-stat with RO, BG for 2030, 2050, 2080 |
| `TestParseJsonstatIndicators` | `_parse_jsonstat_indicators(json)` → dict[country → {indicator → value}] | Sample JSON-stat with median age, old-age dependency for RO |
| `TestParseJsonstatDemographics` | `_parse_jsonstat_demographics(json)` → dict[nuts3 → RegionalDemographics] | Sample JSON-stat for DEMO_R_PJANGRP3 with 3 NUTS3 regions |
| `TestParseJsonstatEconomics` | `_parse_jsonstat_economics(json)` → dict[nuts2 → RegionalEconomics] | Sample JSON-stat for NAMA_10R_3POPGDP, LFST_R_LFE2EN2N |
| `TestComputeGrowthTrajectory` | National + regional scaling → correct projected populations | Known national + regional projections for Romania |
| `TestComputeReceptorGrowthFactor` | pop(2080) / pop(2022) → correct ratio | Growing (PL), declining (BG), stable (AT) |
| `TestComputeProjectionUncertainty` | BSL, LMIG, HMIG → correct bounds | Sample projection variants |
| `TestComputeUrbanExpansionPressure` | Regional vs national growth rate → correct index | Growing urban region, declining rural region |
| `TestClassifyGrowth` | Growth rate → correct classification at boundaries | Edge cases: -0.5%, 0.0%, +0.5%, +1.5% per decade |
| `TestComputeWorkforceIndicators` | Demographics + economics + education → correct composite | Synthetic NUTS data |
| `TestComputeSocioeconomicImpact` | GDP gap, fiscal capacity, deprivation index | Regions above and below national average |
| `TestComputeRetrainingPotential` | Industrial/energy employment → retraining index | Coal-heavy region vs service-economy region |
| `TestLoadNsoSupplement` | Parse curated JSON → NsoProjection | Sample UA supplement file |
| `TestNsoSupplementValidation` | Invalid/missing fields → appropriate error handling | Malformed JSON, missing required fields |
| `TestNutsCodeTranslation` | NUTS 2021 → 2024 code mapping for changed regions | Known reclassified NUTS3 codes |
| `TestResultStructure` | `EurostatProjectionsResult.to_dict()` shape and types | Constructed result |
| `TestValidation` | Range checks (growth factor 0.3–3.0, GDP plausibility, employment range) | Edge-case values |

### 10.2 Integration tests (mocked HTTP)

| Test | What it tests |
|------|--------------|
| `test_fetch_national_projections_eu12` | Mock API → correct national projections for 12 EU countries |
| `test_fetch_national_indicators` | Mock API → correct demographic indicators for Romania |
| `test_fetch_regional_projections_nuts3` | Mock API → correct NUTS3 projections for 3 Romanian regions |
| `test_fetch_regional_demographics` | Mock API → correct DEMO_R_PJANGRP3 for test NUTS3 regions |
| `test_fetch_regional_economics` | Mock API → correct GDP, employment, education for test NUTS2 |
| `test_ingest_projections_full_flow` | Mock all queries → all EU-12 projections + statistics loaded |
| `test_nso_supplement_loading` | Mock files → 11 NSO supplements loaded |
| `test_fetch_site_romania_eu` | Mock all data → fetch(44.15, 23.12) → complete result with high quality |
| `test_fetch_site_turkey_candidate` | Mock data → fetch for TR site → partial data, quality "medium" |
| `test_fetch_site_ukraine_nso` | Mock NSO file → fetch for UA site → national projection only, quality "low" |
| `test_fetch_site_belarus_minimal` | Mock data → fetch for BY site → NSO supplement, quality "low" |
| `test_health_check` | Mock successful small query → health_check returns True |
| `test_api_error_retry` | Mock HTTP 500 → connector retries and succeeds on 3rd attempt |
| `test_cache_reuse` | Second ingest call uses cached data |
| `test_partial_eurostat_coverage` | Mock partial NUTS3 data → available regions populated, missing regions flagged |

### 10.3 Batch tests (mocked HTTP + test DB)

| Test | What it tests |
|------|--------------|
| `test_enrich_site_persists_four_attributes` | `enrich_site()` → 4 `SiteAttribute` rows (RI-06, NS-09, NS-10, NS-12) + `DataSource` rows |
| `test_enrich_batch_by_ids` | `enrich_batch(site_ids=[...])` → enriches exactly those sites |
| `test_enrich_batch_by_country` | `enrich_batch(country_codes=["RO"])` → enriches all Romanian sites |
| `test_sites_same_nuts3_share_projection` | 5 Romanian sites in same NUTS3 → all get identical regional projection |
| `test_batch_per_site_commit` | Failure on site 2 does not lose site 1 data |
| `test_batch_resumability` | Re-run same `run_id` → skips already-enriched sites |
| `test_batch_progress_logging` | 30 sites → `projections_batch_progress` emitted at site 25 |
| `test_batch_empty_site_list` | `enrich_batch(site_ids=[])` → returns immediately with `total_sites=0` |
| `test_non_eu_site_uses_nso_supplement` | Armenian site → uses NSO supplement, quality "low" |
| `test_ns09_upsert_over_s16` | If S-16 has already written NS-09, S-17 upserts with richer data |

### 10.4 DB compatibility tests

| Test | What it tests | Layer |
|------|--------------|-------|
| `TestCriteriaSeedCompleteness::test_all_criterion_ids_are_seeded` | `CRITERION_IDS = ("RI-06", "NS-09", "NS-10", "NS-12")` all in Alembic seed | Static (no DB) |
| `TestConnectorPersistLiveDB::test_eurostat_projections_persist_succeeds` | Persist mock result → 4 SiteAttribute rows, no FK violation | Live DB |

### 10.5 Sample fixture data

```python
SAMPLE_NATIONAL_PROJECTION_JSONSTAT = {
    "version": "2.0",
    "class": "dataset",
    "label": "Population on 1st January by age, sex and type of projection",
    "id": ["projection", "freq", "sex", "age", "geo", "time"],
    "size": [1, 1, 1, 1, 2, 3],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "sex": {"category": {"index": {"T": 0}}},
        "age": {"category": {"index": {"TOTAL": 0}}},
        "geo": {"category": {"index": {"RO": 0, "BG": 1}}},
        "time": {"category": {"index": {"2030": 0, "2050": 1, "2080": 2}}},
    },
    "value": [
        18800000, 17200000, 14100000,  # RO: 2030, 2050, 2080
        6200000, 5400000, 4100000,     # BG: 2030, 2050, 2080
    ],
}

SAMPLE_INDICATORS_JSONSTAT = {
    "version": "2.0",
    "class": "dataset",
    "label": "Demographic balances and indicators by type of projection",
    "id": ["projection", "freq", "indic_de", "geo", "time"],
    "size": [1, 1, 3, 1, 2],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "indic_de": {"category": {"index": {"MEDAGEPOP": 0, "OLDDEP": 1, "GROWRT": 2}}},
        "geo": {"category": {"index": {"RO": 0}}},
        "time": {"category": {"index": {"2050": 0, "2080": 1}}},
    },
    "value": [
        49.8, 53.2,   # MEDAGEPOP: 2050, 2080
        0.48, 0.56,   # OLDDEP: 2050, 2080
        -0.45, -0.38, # GROWRT: 2050, 2080 (% per year)
    ],
}

SAMPLE_REGIONAL_PROJECTION_JSONSTAT = {
    "version": "2.0",
    "class": "dataset",
    "label": "Population on 1 January by age, sex, type of projection and NUTS 3 region",
    "id": ["projection", "freq", "sex", "age", "geo", "time"],
    "size": [1, 1, 1, 1, 2, 2],
    "dimension": {
        "projection": {"category": {"index": {"BSL": 0}}},
        "freq": {"category": {"index": {"A": 0}}},
        "sex": {"category": {"index": {"T": 0}}},
        "age": {"category": {"index": {"TOTAL": 0}}},
        "geo": {"category": {"index": {"RO411": 0, "RO414": 1}}},
        "time": {"category": {"index": {"2030": 0, "2050": 1}}},
    },
    "value": [
        620000, 540000,   # RO411 (Dolj): 2030, 2050
        380000, 310000,   # RO414 (Olt): 2030, 2050
    ],
}

SAMPLE_NSO_SUPPLEMENT = {
    "country_code": "UA",
    "country_name": "Ukraine",
    "source": "UN World Population Prospects 2024 (medium variant)",
    "source_url": "https://population.un.org/wpp/",
    "retrieved_date": "2026-03-15",
    "projection_variant": "medium",
    "base_year": 2023,
    "projections": {
        "2030": {"population": 36500000, "growth_rate": -0.008},
        "2040": {"population": 33200000, "growth_rate": -0.009},
        "2050": {"population": 30100000, "growth_rate": -0.010},
        "2060": {"population": 27500000, "growth_rate": -0.009},
        "2080": {"population": 23800000, "growth_rate": -0.007},
    },
    "median_age_2050": 48.2,
    "old_age_dependency_2050": 0.42,
    "quality_note": "Based on UN WPP 2024 medium variant; conflict displacement "
                    "effects create high uncertainty in short-term projections",
}

SAMPLE_ZONE_ASSESSMENT = {
    "country_code": "RO",
    "nuts3_code": "RO411",
    "nuts2_code": "RO41",
    "population_projection": {
        "base_population": 660000,
        "base_year": 2022,
        "projected_pop_2030": 620000,
        "projected_pop_2050": 540000,
        "projected_pop_2080": 420000,
        "pop_change_pct_2050": -18.2,
        "pop_change_pct_2080": -36.4,
        "receptor_growth_factor_60yr": 0.636,
        "projection_lo_2050": 510000,
        "projection_hi_2050": 570000,
        "growth_classification": "moderate_decline",
        "urban_expansion_pressure": -0.15,
        "median_age_2050": 49.8,
        "old_age_dependency_2050": 0.48,
        "projection_source": "europop2019_regional",
        "projection_variant": "baseline",
        "spatial_level": "nuts3",
    },
    "socioeconomic": {
        "nuts3_gdp_million_eur": 5200.0,
        "nuts3_gdp_per_capita_eur": 7800.0,
        "national_gdp_per_capita_eur": 14900.0,
        "gdp_gap_to_national_pct": -47.7,
        "gdp_growth_5yr_pct": 22.0,
        "fiscal_capacity_index": 0.32,
        "deprivation_index": 0.68,
    },
    "workforce": {
        "working_age_pop": 410000,
        "working_age_pct": 62.1,
        "projected_working_age_2050": 310000,
        "employment_rate_pct": 62.0,
        "unemployment_rate_pct": 6.5,
        "employment_industry_pct": 28.0,
        "employment_construction_pct": 7.5,
        "employment_energy_pct": 4.2,
        "tertiary_education_pct": 18.5,
        "retraining_pool_index": 0.55,
        "coal_energy_employment": 3200,
    },
    "policy_proxy": {
        "nuclear_policy_stance": "favourable",
        "energy_sector_dependence": 0.042,
        "education_index": 0.37,
    },
    "quality": "high",
}
```

---

## 11. Configuration

### 11.1 Addition to `config/default.yml`

```yaml
connectors:
  eurostat_projections:
    statistics_api_url: "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
    timeout_s: 30
    inter_request_delay_s: 0.5           # courtesy delay between API calls
    cache_dir: "sources/eurostat_projections"
    projection_cache_ttl_days: 365       # EUROPOP published every ~4 years
    statistics_cache_ttl_days: 90        # annual updates
    nso_supplement_dir: "sources/nso_projections"

    # EUROPOP2023 national projection settings
    national_projection_dataset: "proj_23np"
    national_indicators_dataset: "proj_23ndbi"
    projection_variant_primary: "BSL"    # baseline
    projection_variant_lo: "LMIG"        # lower migration (lower bound)
    projection_variant_hi: "HMIG"        # higher migration (upper bound)
    projection_years:
      - 2030
      - 2040
      - 2050
      - 2060
      - 2070
      - 2080

    # EUROPOP2019 regional projection settings
    regional_projection_dataset: "proj_19rp3"
    regional_projection_years:
      - 2030
      - 2040
      - 2050

    # Current statistics datasets
    datasets:
      demographics_age: "DEMO_R_PJANGRP3"
      demographics_growth: "DEMO_R_GIND3"
      gdp: "NAMA_10R_3GDP"
      gdp_per_capita: "NAMA_10R_3POPGDP"
      employment: "LFST_R_LFE2EN2N"
      unemployment: "LFST_R_LFU3RT"
      education: "EDAT_LFSE_04"
    statistics_reference_year: 2023

    # Demographic indicators to query from proj_23ndbi
    indicators:
      - "MEDAGEPOP"      # median age
      - "OLDDEP"         # old-age dependency ratio
      - "CNMIGRATRT"     # crude net migration rate
      - "NATGROWRT"      # natural growth rate
      - "GROWRT"          # total growth rate

    # Growth classification thresholds (annual % change per decade)
    growth_thresholds:
      rapid_growth_min_pct: 5.0          # > 5% per decade
      moderate_growth_min_pct: 1.0       # 1–5% per decade
      stable_band_pct: 1.0              # -1% to +1% per decade
      moderate_decline_max_pct: -1.0     # -5% to -1% per decade
      # below -5% per decade → "rapid_decline"

    # Nuclear policy stance (curated, country-level)
    nuclear_policy:
      PL: "favourable"         # building first NPP (Westinghouse AP1000)
      CZ: "favourable"         # Dukovany expansion, Temelín
      SK: "favourable"         # Mochovce 3-4 completed, Bohunice replacement planned
      HU: "favourable"         # Paks II under construction
      AT: "unfavourable"       # constitutional ban since 1978
      SI: "neutral"            # Krško operating; new unit under study
      HR: "neutral"            # co-owner of Krško; no new-build policy
      BA: "unknown"            # no nuclear policy framework
      RS: "neutral"            # no operational nuclear; exploring SMR
      ME: "unknown"            # no nuclear policy framework
      XK: "unknown"            # no nuclear policy framework
      AL: "unknown"            # no nuclear policy framework
      MK: "unknown"            # no nuclear policy framework
      RO: "favourable"         # Cernavodă 3-4, SMR programme (NuScale)
      BG: "favourable"         # Kozloduy new unit planned, Belene revival
      MD: "unknown"            # no nuclear policy framework
      UA: "favourable"         # 15 operating reactors; new build planned
      BY: "favourable"         # Ostrovets NPP (2 units VVER-1200)
      EE: "neutral"            # exploring SMR; KAPP project
      LV: "neutral"            # no specific nuclear policy
      LT: "neutral"            # Ignalina closed; Visaginas NPP cancelled; exploring SMR
      AM: "favourable"         # Metsamor operating; replacement reactor planned
      TR: "favourable"         # Akkuyu under construction; 2 more NPPs planned
```

### 11.2 CLI invocation examples

```bash
# Phase A: Ingest all projection + statistics data
python -m atoms_vs_ashes ingest eurostat-projections --year 2023

# Phase B: Enrich single site by ID
python -m atoms_vs_ashes enrich eurostat-projections --site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6

# All sites in Romania and Bulgaria
python -m atoms_vs_ashes enrich eurostat-projections --country RO --country BG

# All sites in the database
python -m atoms_vs_ashes enrich eurostat-projections --all

# Combined: ingest + enrich all
python -m atoms_vs_ashes enrich eurostat-projections --all --ingest

# Resume a previously interrupted batch
python -m atoms_vs_ashes enrich eurostat-projections --all --run-id prev-run-2026-04-01

# Dry run (validate connectivity, query one country, don't persist)
python -m atoms_vs_ashes enrich eurostat-projections --dry-run
```

### 11.3 Programmatic invocation

```python
from atoms_vs_ashes.connectors.eurostat_projections import EurostatProjectionsConnector
from atoms_vs_ashes.db import session_scope
from atoms_vs_ashes.config import get_settings

settings = get_settings()

with EurostatProjectionsConnector(settings) as connector:
    # Phase A: Ingest all projections + statistics
    with session_scope() as session:
        ingestion = connector.ingest_projections(
            session, run_id="run-001", reference_year=2023
        )
        print(f"Loaded projections for {ingestion.n_countries_with_projections} countries, "
              f"{ingestion.n_regions_with_data} NUTS3 regions")

    # Single site — raw result, no DB
    result = connector.fetch(lat=44.15, lon=23.12)
    print(result.population_projection.growth_classification)     # "moderate_decline"
    print(result.population_projection.receptor_growth_factor_60yr)  # 0.636
    print(result.population_projection.projected_pop_2050)        # 540000
    print(result.socioeconomic.gdp_per_capita_eur)                # 7800.0
    print(result.socioeconomic.deprivation_index)                 # 0.68
    print(result.workforce.employment_energy_pct)                  # 4.2
    print(result.workforce.retraining_pool_index)                  # 0.55
    print(result.policy_proxy.nuclear_policy_stance)               # "favourable"

    # Site in Ukraine (NSO supplement)
    result = connector.fetch(lat=50.45, lon=30.52)
    print(result.quality)                                          # "low"
    print(result.population_projection.projection_source)          # "un_wpp"
    print(result.population_projection.projected_pop_2050)         # 30100000

    # Site in Austria (unfavourable policy)
    result = connector.fetch(lat=48.20, lon=16.37)
    print(result.policy_proxy.nuclear_policy_stance)               # "unfavourable"

    # Batch — all Romanian sites
    with session_scope() as session:
        batch = connector.enrich_batch(
            session, run_id="run-001", country_codes=["RO"]
        )
        print(batch.summary_line())  # "85 sites: 85 ok, 0 failed, 0 cached (0.2 s)"
```

---

## 12. Risks and Limitations

| Risk | Severity | Mitigation |
|------|----------|------------|
| EUROPOP2023 regional projections (proj_23rp3) may not yet be published | **Medium** | Use EUROPOP2019 regional projections (proj_19rp3) as fallback. The 2019 regional projections extend to 2060 and are still the most recent available at NUTS3 level. When EUROPOP2023 regional data is published, update the config `regional_projection_dataset` to the new code. |
| Non-EU countries (11 of 23 in-scope) have no Eurostat projections | **High** | Use curated NSO supplement files backed by UN WPP 2024 medium variant. This provides national-level projections only — no regional disaggregation. Quality flag `low`. The scoring module should weight projection data lower for these countries. |
| NUTS code reclassification between NUTS 2021 (used by proj_19rp3) and NUTS 2024 (used by S-16) | **Medium** | Implement a static NUTS code translation table for affected regions. Most reclassifications are minor boundary adjustments; a few involve code renaming. The connector logs warnings when translation is needed. |
| Population projections are inherently uncertain, especially post-2050 | **Medium** | Provide projection uncertainty band (LMIG–HMIG variants). Document that the receptor_growth_factor is a modelled estimate, not an observation. The scoring module should treat projections beyond 2060 with diminishing confidence. |
| Nuclear policy stance is a manually curated field — may become outdated | **Low** | Nuclear policy data is stored in YAML config and curated JSON files, both easily updatable. Include a `last_updated` field. Flag `medium` quality if policy data is > 2 years old. |
| S-17 and S-16 both write NS-09 SiteAttribute rows | **Medium** | S-17 upserts over S-16's NS-09 row (S-17 is Priority 1 for NS-09 and includes all S-16 fields plus trend data). This is by design. Document the upsert behaviour. If both connectors run in the same batch, order matters: run S-16 first, then S-17. |
| Eurostat Statistics API response format (JSON-stat 2.0) is complex | **Low** | JSON-stat uses a cube model with indexed dimensions. Implement a reusable parser tested against known sample responses. The format is stable and well-documented. |
| EUROPOP projections may be replaced by EUROPOP2028 during project lifetime | **Low** | All dataset codes are configurable in YAML. When a new round is published, update config and re-ingest. Cached data from the old round remains valid until replaced. |
| Socioeconomic data has 1–2 year publication lag | **Low** | GDP and employment data for year N is typically available by Q3 of year N+2. A 2023 reference year queried in 2026 will have complete data. Use `statistics_reference_year` config to target the latest available. |
| Public opinion proxy (NS-12) is weak — limited to structural indicators | **Low** | Acknowledged in the criterion mapping. NS-12 primarily depends on N-21 national regulatory/policy research (Phase 4). S-17 provides structural proxies only. Write quality flag `low` for NS-12 from this source. |

---

## 13. Open Issues

| # | Issue | Blocking? | Resolution path |
|---|-------|-----------|----------------|
| 1 | EUROPOP2023 regional projections (proj_23rp3) publication status | No | Monitor Eurostat's population projections portal for regional release. Expected ~2025–2026. Use EUROPOP2019 regional data until then. Make dataset code configurable. |
| 2 | NUTS code translation 2021 → 2024 for affected regions | No | Build a static lookup during implementation. Reference the Eurostat NUTS correspondence tables at `https://ec.europa.eu/eurostat/web/nuts/correspondence-tables`. Affected regions are typically < 5% of total. |
| 3 | NSO supplement curation for 11 non-EU countries | No (blocking for non-EU site quality) | Create template JSON files during implementation. Populate with UN WPP 2024 data. Layer NSO-specific data as it becomes available. Document the curation process in a README under `sources/nso_projections/`. |
| 4 | S-16 / S-17 NS-09 upsert ordering | No | Document that the pipeline should run S-16 before S-17. S-17 upserts with richer data. If S-16 is not run, S-17 still produces a complete NS-09 row (it queries the same GDP/employment datasets plus trend data). |
| 5 | Shared NUTS3 spatial index with S-16 | No | Implement as a shared module (e.g., `connectors/_nuts_index.py`) that both S-16 and S-17 import. Load NUTS3 boundaries once and share the index. Alternatively, S-17 can call `EurostatGiscoConnector._nuts3_lookup` directly if S-16 is instantiated. |
| 6 | UN WPP API availability and format | No | UN WPP 2024 API at `https://population.un.org/dataportal/api/` provides JSON responses. Alternatively, pre-download WPP CSV data and store locally. For this connector, pre-curated JSON files are preferred over live API queries to the UN, to reduce external dependencies. |
| 7 | Country-specific NSO projection quality varies widely | No | Add a `confidence` field to NSO supplement files: "high" (official projection), "medium" (UN WPP), "low" (extrapolated/estimated). Map to DataQualityFlag accordingly. |

---

## 14. Dependencies

### 14.1 New Python dependencies

| Package | Purpose | Already in project? |
|---------|---------|-------------------|
| `httpx` | HTTP client for Eurostat Statistics API | Already in project (core dependency) |
| `shapely` | Point-in-polygon for NUTS3 lookup (shared with S-16) | Already in project (`geo.py` uses shapely) |
| `pyproj` | CRS transformation (shared with S-16, if needed for NUTS lookup) | Already in project (`geo.py` uses pyproj) |

**Fact:** No new Python dependencies are required. All dependencies are already in the project. The connector uses `httpx` for API queries, `shapely` for NUTS lookup (shared with S-16), and standard library `json` for JSON-stat parsing.

### 14.2 Source dependencies

| Dependency | Status |
|-----------|--------|
| Eurostat Statistics API | Available, no registration |
| EUROPOP2023 national projections (proj_23np) | Published March 2024, available |
| EUROPOP2019 regional projections (proj_19rp3) | Published, available |
| UN WPP 2024 | Published July 2024, available via API and download |
| NSO supplement files | Must be curated during implementation |

### 14.3 Internal dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| S-16 EurostatGiscoConnector — NUTS3 spatial index | Specified (not yet implemented) | S-17 reuses the NUTS3 lookup. If S-16 is implemented first, share the index. If not, S-17 independently downloads NUTS3 boundaries. |
| S-16 EurostatGiscoConnector — NS-09 baseline | Specified (not yet implemented) | S-17 upserts over S-16's NS-09 row. S-17 functions independently if S-16 is not available. |
| I-4 GEM Coal Plant Tracker — coal employment | Implemented | S-17 cross-references coal plant data for retraining potential (NS-10). Read from `sites` table coal plant attributes. Optional — if not available, set `coal_energy_employment = null`. |

### 14.4 Downstream dependencies

| Consumer | Uses |
|----------|------|
| Scoring module (RI-06 ranking) | `receptor_growth_factor_60yr`, `growth_classification`, `projected_pop_2050`, `projection_uncertainty` from `SiteAttribute` where `criterion_id="RI-06"` |
| Scoring module (NS-09 ranking) | `gdp_per_capita_eur`, `deprivation_index`, `fiscal_capacity_index` from `SiteAttribute` where `criterion_id="NS-09"` |
| Scoring module (NS-10 ranking) | `working_age_pop`, `employment_energy_pct`, `retraining_pool_index`, `tertiary_education_pct` from `SiteAttribute` where `criterion_id="NS-10"` |
| Scoring module (NS-12 ranking) | `nuclear_policy_stance` from `SiteAttribute` where `criterion_id="NS-12"` |
| S-16 Eurostat GISCO | S-16 provides the current population baseline that S-17 projects forward. S-17's projected density is computed by applying growth factors to S-16's GEOSTAT-derived current density. |

---

## 15. Acceptance Criteria

### 15.1 Data ingestion

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 1 | Connector queries EUROPOP2023 national projections for 12 EU countries → correct population values at 2030, 2050, 2080 | Unit test with sample JSON-stat |
| 2 | Connector queries EUROPOP2023 demographic indicators → correct median age, old-age dependency | Unit test with sample JSON-stat |
| 3 | Connector queries EUROPOP2019 regional projections for test NUTS3 regions → correct values | Unit test |
| 4 | Connector queries multiple projection variants (BSL, LMIG, HMIG) → correct uncertainty band | Unit test |
| 5 | Connector loads 11 NSO supplement files for non-EU countries | Integration test with mock files |
| 6 | Ingestion handles Eurostat API errors gracefully (retry, stale cache) | Integration test with mock failures |
| 7 | Missing NSO supplement file → quality "insufficient" for that country | Integration test |

### 15.2 Single-site

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 8 | Growth trajectory computed correctly: national + regional scaling → correct decade-by-decade projections | Unit test with known projections |
| 9 | Receptor growth factor: pop(2082) / pop(2022) = correct ratio for Romania | Unit test |
| 10 | Growth classification correct at threshold boundaries | Unit test |
| 11 | Urban expansion pressure correct for growing urban vs declining rural region | Unit test |
| 12 | Workforce indicators assembled correctly from demographics + economics + education | Unit test |
| 13 | Socioeconomic impact: GDP gap, fiscal capacity, deprivation index | Unit test |
| 14 | Retraining potential index computed correctly for coal-heavy region | Unit test |
| 15 | Nuclear policy stance retrieved correctly from config for all 23 countries | Unit test |
| 16 | EU site → quality "high"; candidate site → "medium"; non-EU site → "low" | Unit test |
| 17 | `EurostatProjectionsResult.to_dict()` contains all required fields | Unit test |
| 18 | Connector works with `settings=None` (uses defaults) | Unit test |
| 19 | All unit tests pass without network access | `pytest` run |

### 15.3 Batch operations

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 20 | `enrich_site()` persists 4 `SiteAttribute` rows (RI-06, NS-09, NS-10, NS-12) + `DataSource` rows | DB integration test |
| 21 | Sites in same NUTS3 region receive identical regional projection | DB integration test |
| 22 | `enrich_batch(site_ids=[...])` enriches exactly the requested sites | DB integration test |
| 23 | `enrich_batch(country_codes=["RO"])` enriches all Romanian sites | DB integration test |
| 24 | Per-site commit isolation: failure on site N does not rollback sites 1..N-1 | DB integration test |
| 25 | Batch is resumable: re-running same `run_id` skips already-enriched sites | DB integration test |
| 26 | `BatchResult` contains correct totals | Unit + integration test |
| 27 | Progress logging emits `projections_batch_progress` every 25 sites | Log-capture integration test |
| 28 | CLI `--site-id`, `--country`, `--all`, `--run-id`, `--dry-run`, `--ingest` flags work correctly | CLI integration test |

### 15.4 Database migration and compatibility

| # | Criterion | Verification method |
|---|-----------|-------------------|
| 29 | `models.py` declares `CRITERION_IDS = ("RI-06", "NS-09", "NS-10", "NS-12")` | Code inspection + static import test |
| 30 | All criterion IDs exist in Alembic seed migration 005 | `pytest tests/test_connector_db_compatibility.py::TestCriteriaSeedCompleteness -v` |
| 31 | `models.py` is importable without DB or HTTP dependencies (pure dataclasses) | Static test |
| 32 | `_persist_result` writes 4 `SiteAttribute` rows without FK violation | Live-DB test |
| 33 | `_ensure_data_source` creates/merges DataSource records | Live-DB test |
| 34 | `SiteAttribute` rows use `session.merge()` for idempotency | DB test (run persist twice, verify no duplicates) |
| 35 | NS-09 upsert over S-16 data works correctly (S-17 data replaces S-16 data) | DB test |

---

## 16. Growth Classification and Derived Metric Logic

### 16.1 Growth trajectory computation

```
compute_growth_trajectory(
    national_projection: dict[str, int],     # {year → population}
    regional_projection: dict[str, int] | None,
    base_pop_national: int,
    base_pop_regional: int | None,
) → dict[str, int]:

  IF regional_projection is not None:
      # Use regional projections directly where available
      trajectory = regional_projection.copy()
      # For years beyond regional projection range, extrapolate using national growth rate
      FOR year in national_projection.keys():
          IF year not in trajectory:
              last_regional_year = max(trajectory.keys())
              last_regional_pop = trajectory[last_regional_year]
              national_growth_factor = national_projection[year] / national_projection[last_regional_year]
              trajectory[year] = round(last_regional_pop * national_growth_factor)
      RETURN trajectory

  ELSE:
      # No regional projection — apply national growth rate to regional base
      # Scaling factor: regional_share = base_pop_regional / base_pop_national
      # This assumes the region maintains its proportional share of national population
      IF base_pop_regional is not None:
          regional_share = base_pop_regional / base_pop_national
      ELSE:
          regional_share = 1.0  # national-level only
      trajectory = {}
      FOR year, national_pop in national_projection.items():
          trajectory[year] = round(national_pop * regional_share)
      RETURN trajectory
```

### 16.2 Growth classification

```
classify_growth(pop_change_pct_per_decade: float) → str:

  IF pop_change_pct_per_decade > rapid_growth_min_pct (5.0):
      RETURN "rapid_growth"
  IF pop_change_pct_per_decade > moderate_growth_min_pct (1.0):
      RETURN "moderate_growth"
  IF pop_change_pct_per_decade > -stable_band_pct (-1.0):
      RETURN "stable"
  IF pop_change_pct_per_decade > moderate_decline_max_pct - 4.0 (-5.0):
      RETURN "moderate_decline"
  RETURN "rapid_decline"
```

**Fact:** Growth rate is computed as `(pop_2050 - pop_base) / pop_base × 100 / n_decades`. For EUROPOP2023 base year 2022 → 2050 projection, n_decades ≈ 2.8.

### 16.3 Receptor growth factor

```
receptor_growth_factor_60yr(base_pop: int, projected_pop_60yr: int) → float:
  IF base_pop <= 0:
      RETURN 1.0  # default: no change
  RETURN projected_pop_60yr / base_pop
```

**Fact:** For the NuScale VOYGR-6 with a 60-year design life, the receptor growth factor computes the ratio of projected population at end-of-life to current population. A factor < 1.0 indicates population decline (favourable for siting); > 1.0 indicates growth (unfavourable). This is used by the scoring module to weight the RI-06 criterion.

### 16.4 Urban expansion pressure

```
urban_expansion_pressure(
    regional_growth_rate: float,    # per decade %
    national_growth_rate: float,    # per decade %
) → float:
  RETURN regional_growth_rate - national_growth_rate
```

Positive values indicate the region is growing faster than the national average (urban expansion pressure). Negative values indicate relative decline.

### 16.5 Retraining pool index

```
retraining_pool_index(
    employment_industry_pct: float,
    employment_energy_pct: float,
    employment_construction_pct: float,
    unemployment_rate_pct: float,
) → float:
  # Higher index = more retrainable workforce available
  # Components:
  #   - Industrial employment: skilled workers in manufacturing/mining
  #   - Energy employment: directly relevant to nuclear
  #   - Construction: relevant to NPP construction phase
  #   - Unemployment: available labour pool

  industry_score = min(employment_industry_pct / 30.0, 1.0)      # normalise to EU average ~22%
  energy_score = min(employment_energy_pct / 5.0, 1.0)           # normalise to high-energy regions
  construction_score = min(employment_construction_pct / 10.0, 1.0)
  unemployment_score = min(unemployment_rate_pct / 15.0, 1.0)    # available pool

  RETURN 0.35 * industry_score + 0.30 * energy_score + 0.20 * construction_score + 0.15 * unemployment_score
```

### 16.6 Deprivation index

```
deprivation_index(
    gdp_gap_to_national_pct: float,     # negative = below average
    unemployment_rate_pct: float,
    tertiary_education_pct: float,
) → float:
  # Higher index = more deprived (higher community benefit potential)
  gdp_component = max(0, min(1, -gdp_gap_to_national_pct / 60.0))    # -60% gap → 1.0
  unemployment_component = min(unemployment_rate_pct / 20.0, 1.0)      # 20% unemployment → 1.0
  education_gap = max(0, min(1, (35.0 - tertiary_education_pct) / 25.0))  # EU avg ~35%; lower → more deprived

  RETURN 0.40 * gdp_component + 0.35 * unemployment_component + 0.25 * education_gap
```

### 16.7 Quality determination

| Condition | Quality level |
|-----------|--------------|
| EU member state: EUROPOP2023 national + EUROPOP2019 regional + full statistics | `high` |
| EU member state: EUROPOP2023 national + statistics (no regional projection) | `medium` |
| Candidate country: NSO supplement + partial Eurostat statistics | `medium` |
| Non-EU country: NSO supplement available (UN WPP) | `low` |
| Non-EU country: no NSO supplement | `insufficient` |
| Cached data used (stale cache) | `medium` (if was `high`); unchanged otherwise |
| NS-12 policy proxy (always weak) | `low` |
