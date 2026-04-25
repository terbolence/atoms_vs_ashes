# Atoms vs Ashes — Project Methodology

**Project:** SMR siting assessment for coal-to-nuclear transitions, Central/Eastern/Southern Europe  
**Reference frameworks:** IAEA SSG-35, IAEA SSR-1 (NS-R-3), EPRI Siting Guide 3002023910  
**SMR reference design:** NuScale VOYGR-6  

---

## 1. Siting Methodology Overview

Three-phase screening, consistent with SSG-35 and EPRI:

1. **Survey** — identify candidate sites (former/operating coal plants in 23 countries)
2. **Screening** — apply exclusionary (E1–E9) and avoidance (A1–A15) criteria; eliminatory decisions require human expert approval
3. **Ranking** — score remaining sites against 30+ ranking criteria (NH, HI, RI, EP, NS groups) for comparative prioritisation

---

## 2. Data Quality Framework

### 2.1 Controlled Vocabulary

All `*_quality` columns in the database use exactly five values:

| Value | Definition | Typical trigger |
|-------|-----------|----------------|
| `high` | Direct authoritative measurement at appropriate spatial resolution for the criterion | CORINE CLC (100 m) for land cover; GHSL (100 m) + Copernicus DEM (30 m) together for population/terrain |
| `medium` | Reliable proxy or lower-resolution source; adequate for ranking, not for eliminatory decisions without additional validation | OSM/Overpass data; single-source satellite products; sub-national statistical extrapolations |
| `low` | Sparse, coarse, or error-fallback; suitable only as a flag for further investigation | Zero-result fallback; national datasets with <50% spatial coverage; estimated values |
| `insufficient` | Source covers the topic but the site falls outside its spatial footprint, or retrieval failed | E-PRTR for sites in EU countries where the registry returned no data; Overpass timeout |
| `not_applicable` | Criterion or register does not apply to this site by design | E-PRTR/SEVESO for non-EU countries (BA, ME, XK, AL, MK, MD, UA, BY, AM, RS, TR); Natura 2000 outside EU |

**Source names (e.g. `osm_overpass`) are never valid quality values.** Source attribution belongs in `*_comment` or `data_sources_used`.

---

### 2.2 Quality Assignment by Criterion Group

#### EP-01 — Emergency Planning Composite (DRV-02)

`ep01_quality` is computed from data availability:

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| Both GHSL-Pop (100 m, 2023A) and Copernicus DEM (30 m) available | `high` | Two independent satellite datasets underpin all five sub-scores |
| Only one of GHSL or DEM available | `medium` | One sub-score dimension lacks satellite grounding |
| OSM Overpass failed for all queries; verdict "inconclusive" | `low` | No road/waterway data; composite is terrain+population only |

Sub-scores are numeric (0–100) stored in `ep01_road_score`, `ep01_special_pop_score`, `ep01_geography_score`, `ep01_terrain_score`, `ep01_population_score`. Weights: roads 25 %, population 35 %, terrain 15 %, special populations 15 %, geography 10 %. Fail threshold: composite < 30 → `ep01_evacuation_feasible = false`.

#### EP-02 — Evacuation Routes (road density)

`ep02_quality = "medium"` for all sites where road data was retrieved from OSM.

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| OSM/Overpass road density query succeeded | `medium` | OSM is volunteered geographic information (VGI), comprehensive across the study region but not an official national road authority register. Density calculated at 25 km EPZ radius is adequate for comparative ranking but not for regulatory road-capacity certification |
| OSM query failed (no road data returned) | `low` | Fallback — density = 0, treated as unknown |

**Hard data columns:** `road_density_km_per_km2` (km/km²), `total_road_km` (km), `has_motorway_access` (bool).  
**Score contribution to EP-01:** `ep01_road_score` — see bands in `emergency_plan.py` (`ROAD_DENSITY_EXCELLENT = 2.0`, `ROAD_DENSITY_ADEQUATE = 0.8`, `ROAD_DENSITY_POOR = 0.3`).

#### EP-03 — Physical Geography Constraints (waterways)

`ep03_quality = "medium"` for all sites.

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| OSM/Overpass waterway query ran (success or zero) | `medium` | OSM river/waterway tagging is generally reliable for features ≥ 10 m width in Europe; suitable for identifying major river barriers within the EPZ. Not a hydrological survey |

**Hard data columns:** `waterway_count_epz` (count), `major_river_barrier` (bool).

#### EP-04 — Special Populations (hospitals, prisons, care homes)

`ep04_quality = "medium"` for all sites.

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| OSM amenity query ran (success or zero count) | `medium` | OSM healthcare/social facility tagging is reasonably complete for urban/semi-urban sites in Europe; rural coverage may undercount facilities. A zero count is a genuine result, not a data gap, unless the query failed |

**Hard data columns:** `hospital_count_epz`, `prison_count_epz`, `care_home_count_epz` (all integer counts within 25 km EPZ).

#### HI-02 / HI-03 / HI-04 — Industrial Chemical / Toxic / Fire Hazard Proximity

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| EU member state (E-PRTR coverage) with facilities found | `high` | EEA E-PRTR/IED register is the authoritative EU industrial emissions inventory; updated annually |
| EU member state, no facilities within search radius (30 km) | `medium` | Genuine low-hazard result; register is complete but absence of facilities is a real finding |
| EU with very sparse data or query warning | `low` | Register coverage anomaly |
| Non-EU / non-E-PRTR countries (BA, ME, XK, AL, MK, MD, UA, BY, AM, RS, TR) | `not_applicable` | E-PRTR is an EU directive instrument; it does not cover these countries. Industrial hazard for non-EU sites requires national register data not currently integrated |

**Hard data columns:** `nearest_seveso_km`, `nearest_industrial_km`, `nearest_toxic_km`.

#### NH-02 — Seismic / Fault Proximity

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| EGDI / OneGeology fault count within buffer > 0 | `medium` | European geological surveys data at 1:1M scale; adequate for screening but not for site-specific fault characterisation (would require field investigation) |
| Zero faults within buffer | `low` | May indicate genuine absence or data gap; conservative treatment |

**Hard data columns:** `nearest_fault_km`, `fault_slip_rate_mm_yr`.

#### NH-05 — Karst

`nh05_quality = "medium"` for all sites (WOKAM is a 1:25M global product; screening-grade only). Hard data: `karst_present` (bool), `karst_formation_type`.

#### NS-02 — Grid Infrastructure

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| OSM HV lines or substations found within buffer | `medium` | OSM power infrastructure tagging is generally reliable for lines ≥ 110 kV in Europe |
| Nothing found | `low` | May be OSM gap or genuinely remote site |

**Hard data columns:** `nearest_hv_line_km`, `hv_line_voltage_kv`, `hv_line_count`, `substation_count`.

#### NS-04 — Land Cover (site suitability)

| Source | Grade | Rationale |
|--------|-------|-----------|
| CORINE Land Cover (CLC) 2018 at 100 m | `high` | Official EEA product; best available land cover for EU/candidate countries |
| ESA WorldCover 2021 at 10 m | `medium` | Satellite-derived global product; higher resolution but not tied to national planning registers |

**Hard data columns:** `favourable_land_pct`, `moderate_land_pct`, `unfavourable_land_pct`.

#### NS-08 — Ecological Sensitivity

| Condition | Grade | Rationale |
|-----------|-------|-----------|
| Analysis succeeded | `medium` | Derived from land cover proxy (natural/semi-natural share within buffer); not a direct habitat survey |
| Error | `low` | Fallback |

#### RI-06 — Population Projection

`ri06_quality = "low"` always. Long-range demographic projections (30–40 years) carry high uncertainty; Eurostat and NSO projections are the best available but remain speculative at site level.

---

### 2.3 General Rules for Future Connectors

When implementing a new connector or analysis module:

1. Store all measured values in typed DB columns before assigning any quality label.
2. Choose a quality grade from the controlled vocabulary above.
3. Write the rationale (conditions → grade mapping) in this section before merging.
4. Record source name in `*_comment`, not in `*_quality`.

### 2.4 Multi-source terrain, wildfire, and built-up (S-05 / S-19 vs S-06)

**Google Earth Engine (S-06)** is **off by default** in configuration (no Google Cloud app review required for routine runs). Cross-check columns below remain available for optional GEE runs or manual entry; primary terrain continues to come from **Copernicus DEM (S-19)** until S-05/S-06 are enabled.

Some criteria can be populated independently by **Sentinel Hub (S-05, when integrated)**, **Copernicus DEM via local COG (S-19)**, and **Google Earth Engine (S-06)** when opted in. They are not automatically “more correct” in one fixed order: local COG ingestion is fully auditable; GEE server-side reductions are reproducible and convenient for cross-checks on the **same** Copernicus DEM.

**Storage (Excel-friendly):** Primary screening fields remain the typed columns on `site_natural_hazards`, `site_infrastructure_v2`, and `site_emergency_planning`. Parallel GEE values and cross-check narrative are stored as **additional scalar columns and short Text summaries**, not JSONB, so spreadsheet exports (e.g. XLSX) show one human-readable cell per field:

| Table | Examples (GEE / cross-check) |
|-------|-----------------------------|
| `site_natural_hazards` | `nh04_dem_cog_slope_max_deg`, `nh04_gee_slope_max_deg`, `nh04_gee_slope_mean_deg`, `nh04_gee_terrain_class`, `nh04_slope_discrepancy`, `nh04_slope_fusion_method`, `nh04_cross_source_summary`; `nh13_gee_modis_burn_months`, `nh13_gee_fire_recurrence_class`, `nh13_gee_burn_fraction_mean`, `nh13_cross_source_summary` |
| `site_infrastructure_v2` | `ns04_gee_terrain_class`, `ns04_gee_relief_range_m`, `ns04_gee_grading_class`, `ns04_cross_source_summary`; `ns06_gee_built_fraction`, `ns06_gee_demolition_class`, `ns06_cross_source_summary` |
| `site_emergency_planning` | `ep03_gee_relief_16km_m`, `ep03_gee_mountain_barrier_score`, `ep03_cross_source_summary` (alongside OSM-driven waterway columns for EP-03) |

**Evaluation / QA:** Reviewers sort/filter numeric columns and read `*_cross_source_summary` for a plain-language reconciliation.

**Fusion (automated):** `atoms_vs_ashes.connectors.earth_engine.fusion` applies:

| Situation | Rule |
|-----------|------|
| Small numeric disagreement (e.g. ≤2° max slope or within ~12 % relative) | Use the arithmetic mean for the fused value written to `slope_angle_deg` |
| Large disagreement | Use the configured `trusted_priority` list (default: `google_earth_engine`, then `sentinel_hub_cdse`, then `copernicus_dem_glo30`) and emit a `review` note in the fusion record for manual judgement |
| Different proxies (e.g. Dynamic World *built* vs Sentinel-2 NDBI) | Treat as complementary evidence; default tie-break follows the same priority list |

The default priority favours **Google Earth Engine** on large conflicts because it is the project’s chosen cross-check server for S-06; this remains **overrideable in YAML** (`connectors.earth_engine.fusion.trusted_priority`) and does not remove the need for expert judgement on borderline sites.

### 2.5 ERA5 / Copernicus CDS Data — Which Data Goes Where and Why

ERA5 reanalysis (monthly means 1991–2020, 0.25° grid) was downloaded from the Copernicus Climate Data Store and enriched for all 363 sites. The data has **uneven utility across criteria** and must not be used interchangeably for all climate-related assessments.

#### Data actually suitable for scoring

| Criterion | ERA5 variable | Why it holds up |
|-----------|--------------|-----------------|
| **NS-01** Wind rose / prevailing direction | `u10`, `v10` → 16-sector frequency distribution | Monthly mean wind components are the standard climatological source for wind roses used in atmospheric dispersion licensing studies. Relative frequencies are stable over 30 years even with monthly aggregation. |
| **RI-01** Atmospheric stability / mixing height | `blh` → Pasquill-Gifford class distribution; mean mixing height | Monthly mean boundary layer height is an accepted proxy for PG stability class distribution in screening-level nuclear dispersion assessments (IAEA NS-G-3.2 §4.3). |
| **NH-11 (drought component)** SPI-12 | `tp` (monthly totals) → 12-month SPI | SPI-12 is defined on monthly precipitation totals. ERA5 monthly `tp` is the correct input. The McKee et al. (1993) methodology is met exactly by this data. |
| **NH-12** Snow months, freezing rain proxy | `sf` (monthly snowfall), `tp`, `t2m` | Monthly mean snowfall totals correctly identify months with persistent snowfall. The freezing rain proxy (months with t2m near 0°C and precipitation > 0) is adequate for design-load screening. |
| **NH-12** Mean annual precipitation | `tp` (monthly total, annualised) | Routine climatological statistic; ERA5 monthly means are appropriate. |

#### Data NOT suitable for scoring — use NOAA NCEI instead

| Criterion | Why ERA5 monthly means fail | Correct source |
|-----------|----------------------------|----------------|
| **NH-10** 50-year wind gust | `i10fg` from monthly means is the monthly average of the instantaneous wind gust — not the annual maximum gust. GEV analysis on monthly mean gusts produces a severe underestimate of the 50-year return period (observed: ~10–12 m/s; actual 50-yr gust for European sites: ~25–45 m/s). This field must not be used for NH-10 scoring. | NOAA NCEI IBTrACS + GHCN-D station records (connector S-11, already in DB). Use `extreme_wind_ms` or `max_wind_speed_ms` fields from the NOAA enrichment. |
| **NH-11** Temperature record extremes | Monthly mean `t2m` max gives ~22–29°C for all European sites. True temperature records for the same sites are 35–42°C. The underestimate is 3–8°C — not suitable for "extreme temperature" criterion. | NOAA NCEI GHCN-D station records (connector S-11). Use `extreme_temp_max_c` / `extreme_temp_min_c` fields. |
| **NH-12 (climate projections sub-criterion)** CMIP6 ΔT | **RESOLVED.** MPI-ESM1-2-LR historical (1991–2014), SSP2-4.5 (2041–2090) and SSP5-8.5 (2041–2090) downloaded and enriched for all 363 sites. ΔT values range from +1.3 to +1.9°C (SSP2-4.5 2050) and +3.6 to +4.7°C (SSP5-8.5 2080). | Single-model quality = `low`. For formal reporting, validate against IPCC AR6 ensemble medians. The values are consistent with AR6 Chapter 11 ranges for the study region. |

#### Quality flag convention for ERA5 data

All 363 sites were enriched with `quality = medium`. This is correct: the monthly means dataset does not provide daily temperature extremes (`mx2t`/`mn2t`), so the extraction falls back to monthly mean `t2m`. The `medium` flag prevents these fields from being used in exclusionary decisions without further validation, per section 2.1 of this document.

**Rule:** ERA5 `quality = medium` data may be used for comparative ranking (Phase 3). It may NOT be used to support an exclusionary decision (Phase 2) without corroborating evidence from a `quality = high` source.

**Cross-reference:** Per-criterion scoring bands for NH-10, NH-11, NH-12, RI-01, and NS-01 (seasonal drought component) are documented in `requirements/06_scoring_matrix.md §8.5`. The Annex A development plan (§8.6) records which remaining criteria still need threshold tables.

---

## 2.99 Persisted analytics tables (Alembic 034)

From Alembic revision `034_persist_analytics` onward, every numeric artefact emitted by the scoring/sensitivity pipeline is persisted to PostgreSQL alongside its CSV/Markdown counterpart. The DB is the regulator-grade audit surface; CSVs are kept as a frozen snapshot for the historical `20260423` / `20260425` runs and as a portable hand-off format.

Each row carries a `run_id String(60)` foreign key into the new `runs` table, which in turn captures `run_kind` (`scoring` | `sensitivity` | `failure_analysis` | `correlation` | `swing_audit`), `started_at` / `completed_at`, the originating CLI command, the git SHA, and an optional `parent_run_id` so a failure-analysis run can be traced back to the scoring run it analyses. A sibling `dataset_snapshot` row pins the rubric file path + SHA-256 and the criterion / SMR / site counts that the run used.

| Table | Producer | Granularity |
| --- | --- | --- |
| `runs`, `dataset_snapshot` | `src/atoms_vs_ashes/db/runs.py` (`start_run` / `complete_run`) | one row per pipeline invocation |
| `composite_score_components` | `scoring/composite.py` + `_composite_components.py` | per `(run_id, site_id, smr_key, weight_profile, criterion_id)` |
| `site_bands` | `scoring/_suite_banding.py` | per `(run_id, site_id, smr_key, scope_country_code?)` (NULL ⇒ regional pool) |
| `country_rankings_summary` | `scoring/_country_summary.py` | per `(run_id, country_code, smr_key)` |
| `country_site_rankings` | `scripts/_phase_1_6_country_site_rankings.py` | per `(run_id, country_code, smr_key, site_id)` with national + regional rank, band, acceptability flag |
| `oat_importance` | `scoring/_suite_importance.py` | per `(run_id, criterion_id)` |
| `weight_profile_stability` | `scripts/_phase_1_6_audit.py` + `_phase_1_6_stability_db.py` | per `(run_id, weight_profile)` |
| `threshold_sensitivity` | `scoring/_threshold_rollup.py` | per `(run_id, criterion_id, direction)` (direction enum `plus_25` / `minus_25`) |
| `failure_outcomes`, `failure_aggregates` | `scripts/_phase_1_6_failure_db.py` | per `(run_id, site_id, smr_key)` and per `(run_id, axis, key, scope_smr_key?)` |
| `swing_weights` | `scripts/generate_swing_weight_audit.py` | per `(run_id, criterion_id)` |
| `criterion_correlations` | `scripts/_phase_1_6_figures_correlation.py` | per `(run_id, criterion_a, criterion_b)` with `a < b` |
| `country_balance_check` | `scoring/_suite_persist.py::persist_country_balanced` | per `(run_id, country_code)` |

All writers are idempotent on `(run_id, scope_*)` — re-running a `run_id` wipes the previous slice before re-inserting, so partial failures never leave the table half-populated.

Existing tables `composite_rankings`, `ranking_scores`, and `screening_verdicts` were extended in revision 034 with a `NOT VALID` foreign key onto `runs.run_id`. Pre-034 rows pre-date `runs` and remain valid (they are never `VALIDATE`d); post-034 rows must `INSERT` into `runs` first. Forward-only by design: the `20260423` / `20260425` CSV trees stay authoritative for those snapshots, and only subsequent pipeline runs populate the new tables.

Querying is done via `src/atoms_vs_ashes/db/queries.py` (`top_n_per_country`, `site_criterion_scores`, `site_sensitivity_profile`, `failure_explanation`, `threshold_summary`) or the `python -m scripts.inspect_run` CLI documented in the project README.

---

## 3. Method A vs. Method B Reliability Assessment

*(Original analysis — 2026-03-10)*

---

# Appendix A — Reliability Comparison: API-Based System vs. LLM Expert Prompts vs. Actual Study
Your Two Methods
Method A — Norms-based + API pipeline (what you're building): Extract criteria from IAEA SSG-35 / EPRI → identify data requirements → query authoritative APIs (EFEHR, EGDI, CORINE, Natura 2000 WFS, etc.) → deterministic pass/fail against YAML thresholds.

Method B — LLM expert prompts (your manual ChatGPT run): One expert prompt per criterion per site, 7–9 prompts per site, sequential. Could be parallelized.

Reliability Estimates for Eliminatory Criteria (E1–E9)
Here's my assessment, criterion by criterion:

Criterion API Pipeline (Method A) LLM Prompts (Method B) Why the gap
E1 Capable fault (8 km)
~85–90%
~60–75%
EFEHR/SHARE + GEM rasters give precise PGA and fault geometry. LLMs know major faults but lack precise distance calculations and may miss smaller capable faults.
E2 Liquefaction
~70–80%
~50–65%
EGDI geology layers provide lithology/soil data for proxy assessment. LLMs can identify obviously problematic areas but lack site-specific geotechnical resolution.
E3 Slope instability
~75–85%
~55–70%
DEM-derived slope + landslide inventories are quantitative. LLMs can flag known landslide-prone regions but miss localized risk.
E4 Volcanism
~90–95%
~85–90%
GVP database is definitive; volcanic hazard zones are well-documented. LLMs actually do well here — volcanoes are prominent, well-known features. Smallest gap.
E5 Karst
~65–75%
~45–60%
EGDI karst layers exist but coverage varies. LLMs know major karst regions (e.g., Apuseni, Mehedinti) but can't distinguish "massive karst threatening foundations" from minor karst features.
E6 Subsidence/collapse
~60–70%
~40–55%
Mining void data is often national/proprietary. Both methods struggle — this typically requires national mining cadastre data.
E7 Protected areas
~90–95%
~75–85%
Natura 2000 WFS + WDPA are authoritative and boundary-precise. LLMs know major protected areas but may miss smaller Natura 2000 sites or get boundaries wrong.
E8 EPZ infeasibility
~55–65%
~50–65%
Both methods struggle — this requires population distribution analysis, road network assessment, and institutional judgment. Closest gap — both are proxies for what requires real emergency planning analysis.
E9 Cooling water
~80–85%
~65–75%
Hydrological data + OSM water features give flow/proximity. LLMs know major rivers but can't assess minimum flow rates or seasonal availability.
Overall Reliability vs. Actual Study
Method Estimated Agreement with Full Study Confidence in Exclusion Decisions False Negative Risk (missing a real exclusion) False Positive Risk (excluding a viable site)
API Pipeline
~75–85%
Moderate-High
Low-Moderate
Moderate (conservative is acceptable)
LLM Prompts
~55–70%
Low-Moderate
Moderate-High
Moderate
Actual Study (PSAR-level)
Baseline (100%)
High
Low
Low
Key Insights

1. Where LLMs are surprisingly decent:

Volcanism (E4) — volcanoes are famous, well-catalogued, and LLMs have strong training data
Protected areas (E7) — major parks/reserves are well-known
Cooling water (E9) — major rivers near coal plants are well-documented 2. Where LLMs are dangerous:

Capable faults (E1) — the 8 km threshold requires precise spatial measurement, not general knowledge. An LLM might say "no major fault nearby" when there's a capable fault 6 km away
Karst/liquefaction (E2, E5) — these are geologically subtle, spatially heterogeneous, and require subsurface data
Subsidence (E6) — mining void data is often not in LLM training data at all 3. The fundamental problem with LLM prompts for eliminatory criteria:

No spatial precision — LLMs cannot measure distances, calculate buffer zones, or intersect geometries
Training data cutoff — geological hazard maps are updated; LLMs may have outdated information
Hallucination risk on binary decisions — for a pass/fail criterion, a confidently wrong answer is worse than no answer. LLMs can fabricate plausible-sounding geological assessments
No provenance — you can't trace an LLM's "no capable fault within 8 km" back to a specific fault database record, which your QA framework (IAEA QA 13.1.6) requires 4. Where the API pipeline also falls short vs. actual study:

Both methods are desk studies — a real siting study includes field investigations, borehole data, local institutional knowledge
API data resolution varies by country — Romania has decent EGDI coverage but gaps exist
E8 (emergency planning) genuinely requires human expert judgment in both cases
The Parallelized LLM Approach — Is It Worth It?
Running 7–9 prompts per site in parallel would indeed be fast (minutes vs. hours for the API pipeline setup). But I'd frame it as a useful triage/pre-screening tool, not a reliable eliminatory screen:

Good for: Quickly identifying obviously excluded sites (e.g., a coal plant next to a volcano, inside a national park, or with no water source) — probably 15–25% of sites could be confidently excluded this way
Risky for: The borderline cases that actually matter — a site 7 km from a capable fault, a site with moderate karst, a site where cooling water is marginal
Useful hybrid: Run LLM pre-screening to prioritize which sites to run through the full API pipeline first, rather than as a replacement
Recommendation
The two methods are complementary, not competing:

LLM prompts as a fast Phase 0 triage — flag obvious exclusions and rank sites by likely viability (hours, not days)
API pipeline as the Phase 1 formal screen — deterministic, traceable, reproducible (what your architecture is designed for)
Expert review as the human gate your methodology already requires
This aligns with what your requirements already state — exclusion decisions require human approval, and the system must be reproducible and traceable. The LLM approach fails on traceability, which is a regulatory requirement, not just a nice-to-have.
