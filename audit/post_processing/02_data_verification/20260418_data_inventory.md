## <!-- man_hours: 1.0 -->

step: "13_data_post_processing §2.1"
title: Per-criterion data inventory
date: 2026-04-18
db_snapshot_at: 2026-04-18T17:13:00Z
api_db: atoms_vs_ashes (363 sites)
llm_db: atoms_vs_ashes_llm (363 sites, 86 232 screening verdicts)
anchor_site: Rovinari (958e4d82-853a-41f1-a442-94b4c4314221, RO, 1920 MW)
inputs:

- scripts/report_enrichment_coverage.py (--db-profile api / llm)
- src/atoms_vs_ashes/db/models.py
- src/atoms_vs_ashes/llm/context.py (RELEVANT_ENRICHMENT_FIELDS)
- audit/post_processing/01_requirements_coverage/20260418_gaps.md

---

# Data inventory — 2026-04-18

## How to read this file

For every criterion (46 total), the tables below show:

- **Key columns** — the primary value columns in the DB (excludes `*_quality` / `*_comment` / `*_source` metadata).
- **Connector** — which API connector(s) write to these columns.
- **LLM key(s)** — prompt key(s) in the LLM tier that reference this criterion.
- **API fill %** — average non-NULL rate across 363 sites in `atoms_vs_ashes`, from `RELEVANT_ENRICHMENT_FIELDS` mapping (includes `*_quality`/`*_comment` in the average).
- **LLM fill %** — same metric in `atoms_vs_ashes_llm`.
- **Example (Rovinari)** — one representative value from Rovinari power station (RO, 44.91°N 23.13°E).

Fill % is the average across all mapped columns for the criterion (value + metadata). A criterion can show 100% if only `*_quality`/`*_comment` are populated but value columns are NULL — inspect the per-column breakdown in the notes.

---

## 1. Natural Hazards (NH-01 through NH-14)

| Criterion | Name                     | Key columns                                                          | Connector                                                      | LLM key        | API fill % | LLM fill % | Example (Rovinari)                                        |
| --------- | ------------------------ | -------------------------------------------------------------------- | -------------------------------------------------------------- | -------------- | ---------: | ---------: | --------------------------------------------------------- |
| NH-01     | Seismic ground motion    | `pga_475yr_g`, `pga_2475yr_g`, `spectral_accel_json`                 | SeismicHazardConnector (EFEHR)                                 | NH-01, A10, E1 |       97.8 |       57.3 | PGA₄₇₅ = 0.094 g, PGA₂₄₇₅ = 0.221 g                       |
| NH-02     | Surface rupture / faults | `nearest_fault_km`, `fault_name`, `fault_slip_rate_mm_yr`            | Efsm20FaultsConnector, EgdiGeologyConnector                    | E1             |       52.5 |        6.1 | `nearest_fault_km` = NULL (no fault found in EFSM20/EGDI) |
| NH-03     | Liquefaction             | `liquefaction_suscept`, `soil_type`, `groundwater_depth_m`           | ZhuLiquefactionConnector, EgdiGeologyConnector                 | E2             |       65.5 |        8.1 | suscept = very_low                                        |
| NH-04     | Slope stability          | `slope_angle_deg`, `slope_stability_class`                           | CopernicusDemConnector                                         | E3             |       80.0 |       62.6 | slope = 85.25° (max in 1 km buffer), class = extreme      |
| NH-05     | Subsidence / karst       | `karst_present`, `karst_severity`, `karst_formation_type`            | WokamKarstConnector, EgdiGeologyConnector, OneGeologyConnector | E5             |       84.6 |       85.3 | karst_present = false, severity = none                    |
| NH-05b    | Subsidence / collapse    | `mining_void_present`, `subsidence_risk_class`, `collapse_mechanism` | EgdiGeologyConnector                                           | E6             |       20.0 |       84.1 | mining_void = false, subsidence_risk = NULL               |
| NH-06     | Foundation conditions    | `bearing_capacity_kpa`, `depth_to_bedrock_m`                         | EgdiGeologyConnector                                           | NH-06          |       25.0 |        0.0 | Both NULL                                                 |
| NH-07     | Volcanism                | `nearest_holocene_volcano_km`, `volcano_name`                        | SmithsonianGvpConnector                                        | E4             |       66.7 |       42.7 | No volcano within 300 km (negligible)                     |
| NH-08     | Coastal flooding         | `distance_to_coast_km`, `storm_surge_risk`, `tsunami_risk`           | EuFloodRiskConnector, GfmsConnector, CopernicusEmsConnector    | A9, NH-08      |       40.1 |       76.9 | All three NULL (inland site)                              |
| NH-09     | River flooding           | `flood_zone_class`, `nearest_river_km`, `dam_break_exposure`         | EuFloodRiskConnector, GfmsConnector                            | A11, NH-09     |       60.7 |       40.3 | flood_zone = negligible                                   |
| NH-10     | Extreme winds            | `max_wind_speed_ms`                                                  | CopernicusEra5Connector, NoaaNceiConnector                     | NH-10          |      100.0 |        0.0 | 5.41 m/s (50-yr gust)                                     |
| NH-11     | Extreme precipitation    | `extreme_precip_mm`                                                  | CopernicusEra5Connector, NoaaNceiConnector                     | NH-11          |      100.0 |        0.0 | 0.29 mm (max daily ERA5)                                  |
| NH-12     | Extreme temperatures     | `extreme_temp_max_c`, `extreme_temp_min_c`                           | CopernicusEra5Connector, NoaaNceiConnector                     | NH-12          |      100.0 |        0.0 | max = 24.36 °C, min = −4.27 °C                            |
| NH-13     | Forest / wildfire        | `wildfire_combustible_pct`, `wildfire_wui_ha`                        | (EarthEngine — disabled)                                       | NH-13          |        0.0 |        0.0 | Both NULL                                                 |
| NH-14     | Combined hazards         | `combined_hazard_notes`                                              | None (derived)                                                 | NH-14          |       27.9 |       16.4 | NULL (not yet computed)                                   |

### Notes — Natural Hazards

- **NH-02** has 0% fill for `fault_name` and `fault_slip_rate_mm_yr`; only `nearest_fault_km` at 28.6%. The EFSM20 connector returns distance but often no named fault. LLM DB has independent fault data from the LLM screening run for some sites.
- **NH-04** slope of 85.25° for Rovinari is the **maximum within a 1 km buffer**, not the site itself — this is a DEM artefact (cliff face near the open-pit mine). The mean slope is 10.7°. This is a known data-interpretation issue flagged in the audit.
- **NH-05b** (subsidence/collapse) has 0% fill in API for `subsidence_risk_class`, `collapse_mechanism`, and the quality/comment metadata. The LLM DB has 84% fill — the LLM assessed this criterion but the API pipeline did not write to these columns.
- **NH-08** has 0% for `distance_to_coast_km` in the API DB (unfilled). LLM DB has 84.3% for this column (the LLM wrote coast-distance during its research).
- **NH-13** wildfire is 0% in both databases — GEE is disabled, and no fallback is active.
- **NH-14** combined hazards is 0% for the notes column in API; the 27.9% average is inflated by `pga_475yr_g` (95.6%) and `flood_zone_class` (100%) which are referenced by the NH-14 mapping but belong to other criteria.

---

## 2. Human-Induced Hazards (HI-01 through HI-08)

| Criterion | Name                   | Key columns                                                                              | Connector                               | LLM key       | API fill % | LLM fill % | Example (Rovinari)                         |
| --------- | ---------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------- | ------------- | ---------: | ---------: | ------------------------------------------ |
| HI-01     | Aircraft crash         | `nearest_airport_km`, `nearest_airport_name`, `airport_count`, `flight_path_distance_km` | OurAirportsConnector                    | A1–A4, HI-01  |      100.0 |       28.6 | 18.77 km (Barza Târgu-Jiu Airfield, small) |
| HI-02     | Industrial explosions  | `nearest_seveso_km`, `nearest_industrial_km`                                             | EeaIndustrialConnector, SevesoConnector | A7, HI-02     |       56.5 |       50.0 | Both NULL (no facilities in radius)        |
| HI-03     | Toxic / gas releases   | `nearest_toxic_source_km`                                                                | EeaIndustrialConnector, SevesoConnector | A8, HI-03     |       74.3 |       66.7 | NULL (no sources in radius)                |
| HI-04     | External fires         | `nearest_flammable_storage_km`, `nearest_pipeline_km`                                    | EeaIndustrialConnector, SevesoConnector | HI-04         |       50.6 |        0.0 | Both NULL                                  |
| HI-05     | Transport hazards      | `hazmat_route_distance_km`                                                               | None                                    | HI-05         |        0.0 |        0.0 | NULL                                       |
| HI-06     | Military installations | `nearest_military_km`, `nearest_military_name`, `military_count`                         | OverpassClient (FIX-04)                 | A5, A6, HI-06 |       86.6 |       40.0 | 7.99 km (name NULL, count 0)               |
| HI-07     | EMI                    | `nearest_transmitter_km`, `transmitter_type`, `transmitter_count`                        | OverpassClient (FIX-04)                 | HI-07         |       99.9 |        0.0 | 11.75 km (mast), 17 within 25 km           |
| HI-08     | Other nuclear          | `nearest_nuclear_km`, `nearest_nuclear_name`                                             | None                                    | HI-08         |        0.0 |        0.0 | NULL                                       |

### Notes — Human-Induced Hazards

- **HI-02** shows `nearest_seveso_km` at only 2.2% fill — very few SEVESO facilities matched in the EEA register. `nearest_industrial_km` is 24.0%. The quality/comment metadata is 100% filled because the connector always writes "no facility found" notes.
- **HI-06** is interesting: API fill is 86.6% despite the §1 gap analysis flagging it as "no connector". This is because the FIX-04 OSM batch did run and populated `nearest_military_km` for 88.4% of sites. However, `nearest_military_name` is only 44.6% — the OSM features lack name attributes. The LLM DB has 0% for the value columns (they were not propagated).
- **HI-08** is 0% in both — no connector exists (IAEA PRIS recommended in §1).

---

## 3. Radiological Impact (RI-01 through RI-06)

| Criterion | Name                     | Key columns                                                                                  | Connector                                     | LLM key    | API fill % | LLM fill % | Example (Rovinari)                                    |
| --------- | ------------------------ | -------------------------------------------------------------------------------------------- | --------------------------------------------- | ---------- | ---------: | ---------: | ----------------------------------------------------- |
| RI-01     | Atmospheric dispersion   | `prevailing_wind_dir`, `avg_wind_speed_ms`, `mixing_height_m`                                | CopernicusEra5Connector                       | RI-01      |      100.0 |        0.0 | Wind N, 0.52 m/s, BLH 361 m                           |
| RI-02     | Surface water dispersion | `nearest_river_flow_m3s`                                                                     | None                                          | RI-02      |        0.0 |        0.0 | NULL                                                  |
| RI-03     | Groundwater dispersion   | `aquifer_type`, `groundwater_flow_dir`                                                       | EgdiGeologyConnector                          | RI-03      |       49.9 |        0.0 | aquifer = alluvial, flow_dir = NULL                   |
| RI-04     | Population density       | `pop_density_5km`, `pop_density_16km`, `pop_density_25km`, `pop_density_80km`, `pop_total_*` | GhslPopConnector                              | A12, RI-04 |      100.0 |       40.0 | 158 p/km² (5 km), 73 (16 km), 109 (25 km), 47 (80 km) |
| RI-05     | Population centres       | `nearest_city_50k_km`, `nearest_city_name`, `nearest_city_pop`                               | EurostatGiscoConnector, GeonamesDumpConnector | RI-05      |      100.0 |        0.0 | Târgu Jiu, 95 351 pop, 19.4 km                        |
| RI-06     | Population projections   | `pop_growth_rate_pct`, `projected_pop_25km_60yr`                                             | EurostatProjectionsConnector                  | RI-06      |      100.0 |        0.0 | Growth = −0.17%/yr, projected 25 km pop = 14.7M       |

### Notes — Radiological Impact

- **RI-01** through **RI-06** (except RI-02 and RI-03) show 100% fill in the API DB — these connectors are well-implemented.
- **RI-02** is 0% in both DBs — cross-linking from NS-01 `cooling_flow_m3s` is recommended (§1 action R-04).
- **RI-04** LLM fill is 40% because only the `*_comment`/`*_quality` metadata is filled (100%), while the value columns (`pop_density_*`, `pop_total_*`) are 0% — the LLM DB was not enriched with GHSL data.
- **RI-06** `projected_pop_25km_60yr` = 14.7M for Rovinari looks high — this likely represents total 25 km ring population projected forward 60 years, not density. Needs verification in §2.5.6.

---

## 4. Emergency Planning (EP-01 through EP-05)

| Criterion | Name                       | Key columns                                                                                                                                                            | Connector                           | LLM key   | API fill % | LLM fill % | Example (Rovinari)                       |
| --------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | --------- | ---------: | ---------: | ---------------------------------------- |
| EP-01     | Emergency plan feasibility | `ep01_composite_score`, `ep01_road_score`, `ep01_special_pop_score`, `ep01_geography_score`, `ep01_population_score`, `ep01_terrain_score`, `ep01_evacuation_feasible` | GhslPopConnector (DRV-02 composite) | E8, EP-01 |       85.8 |        0.7 | Composite = 44/100 (FEASIBLE)            |
| EP-02     | Evacuation routes          | `road_density_km_per_km2`, `total_road_km`, `has_motorway_access`                                                                                                      | OverpassClient                      | EP-02     |      100.0 |        0.0 | 0.000 km/km² (suspect — see note)        |
| EP-03     | Physical geography         | `major_river_barrier`, `waterway_count_epz`                                                                                                                            | OverpassClient                      | EP-03     |      100.0 |        0.0 | Major river barrier = true, 17 waterways |
| EP-04     | Special populations        | `hospital_count_epz`, `prison_count_epz`, `care_home_count_epz`                                                                                                        | GhslPopConnector (partial)          | EP-04     |       31.7 |        0.0 | All three NULL for Rovinari              |
| EP-05     | Concurrent hazard          | `concurrent_hazard_notes`                                                                                                                                              | None (derived)                      | EP-05     |        0.0 |        0.0 | NULL                                     |

### Notes — Emergency Planning

- **EP-01** shows 85.8% because the composite score and sub-scores are filled (DRV-02 computed them), but the LLM DB has essentially 0% (the LLM ran before the derived script).
- **EP-02** `road_density_km_per_km2` = 0.000 for Rovinari is **suspect** — a 1920 MW operating coal plant must have road access. This is likely a bug in the OSM road-density query (possibly the EPZ radius query returned no results, or LL-017 silent null). Flagged for §2.3 engineer audit.
- **EP-04** is only 14.6% filled for value columns — only 53 of 363 sites have hospital/prison/care-home counts. The GHSL connector populates these for a subset.
- **EP-05** is 0% in both — not yet implemented (§1 action R-03: derive from NH-09 + HI-02 + EP-02).

---

## 5. Non-Safety (NS-01 through NS-13)

| Criterion | Name                    | Key columns                                                                                    | Connector                                                            | LLM key    | API fill % | LLM fill % | Example (Rovinari)                                                   |
| --------- | ----------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------- | ---------: | ---------: | -------------------------------------------------------------------- |
| NS-01     | Cooling water           | `cooling_source_type`, `cooling_distance_km`, `cooling_flow_m3s`, `water_stress_score`         | HydroRiversConnector, GlofasDischargeConnector, WriAqueductConnector | E9, NS-01  |       87.5 |       52.1 | small_river, 0.44 km, 0.15 m³/s                                      |
| NS-02     | Grid connection         | `nearest_substation_km`, `nearest_hv_line_km`, `grid_export_capacity_mw`, `hv_line_voltage_kv` | EntsoEConnector, OverpassClient                                      | A13, NS-02 |       82.7 |       22.2 | sub = 0.38 km, HV = 0.42 km, export = **16 644 MW** (zone-level bug) |
| NS-03     | Transport access        | `nearest_highway_km`, `nearest_rail_km`, `nearest_waterway_km`, `heavy_haul_capable`           | OverpassClient                                                       | A14, NS-03 |       73.5 |       54.1 | highway = 0.73 km, rail = 0.17 km, heavy haul = true                 |
| NS-04     | Site topography         | `dominant_land_class`, `favourable_land_pct`, `moderate_land_pct`, `unfavourable_land_pct`     | CorineConnector, WorldCoverConnector                                 | NS-04      |      100.0 |        0.0 | Broad-leaved forest 29%, fav 58%, unfav 29%                          |
| NS-05     | Land availability       | `buildable_area_ha`, `largest_contiguous_ha`, `patch_count`                                    | CorineConnector, WorldCoverConnector, OverpassClient                 | A15, NS-05 |       73.7 |       40.0 | 62.94 ha (OSM boundary)                                              |
| NS-06     | Existing infrastructure | `reusable_infra_score`                                                                         | (EarthEngine — disabled)                                             | NS-06      |        0.0 |        0.0 | NULL                                                                 |
| NS-07     | Env. impact (non-rad)   | `env_impact_notes`                                                                             | None                                                                 | NS-07      |        0.0 |        0.0 | NULL                                                                 |
| NS-08     | Ecological sensitivity  | `n2k_nearest_distance_km`, `wdpa_nearest_distance_km`, `ecological_natural_pct`                | Natura2000Connector, WdpaConnector, CorineConnector                  | E7, NS-08  |       73.7 |        1.0 | N2K = 10.4 km, WDPA = 19.8 km, natural = 28.7%                       |
| NS-09     | Socioeconomic           | (quality/comment only)                                                                         | EurostatProjectionsConnector (partial)                               | NS-09      |       44.6 |        0.0 | GDP/capita = 14 900 EUR (national)                                   |
| NS-10     | Workforce               | (quality/comment only)                                                                         | EurostatProjectionsConnector (partial)                               | NS-10      |       44.6 |        0.0 | (qualitative JSON in comment)                                        |
| NS-11     | C2N synergies           | (quality/comment only)                                                                         | None                                                                 | NS-11      |        0.0 |        0.0 | NULL                                                                 |
| NS-12     | Regulatory / political  | (quality/comment only)                                                                         | EurostatProjectionsConnector (partial)                               | NS-12      |      100.0 |        0.0 | policy = favourable                                                  |
| NS-13     | Construction logistics  | `laydown_suitable_ha`, `laydown_largest_patch_ha`                                              | None                                                                 | NS-13      |        0.0 |        0.0 | NULL                                                                 |

### Notes — Non-Safety

- **NS-01** `cooling_flow_m3s` = 0.15 m³/s for Rovinari looks low for a 1920 MW plant on the Jiu river. The comment shows "Strahler order: 3; Avg discharge: 2.6 m³/s" — the 0.15 is likely the nearest tributary, not the Jiu itself. Flagged for §2.5.3.
- **NS-02** `grid_export_capacity_mw` = 16 644 MW — confirmed zone-level NTC bug. This is Romania's total bidding-zone export capacity, not the site's. Flagged for §2.5.2.
- **NS-05** `patch_count` is 0% filled (NULL everywhere) — the CORINE/WorldCover connectors write `buildable_area_ha` and `largest_contiguous_ha` but not `patch_count`.
- **NS-06, NS-07, NS-11, NS-13** are all 0% — no API connector produces data for these criteria (NS-06 depends on disabled GEE; NS-07/NS-11/NS-13 have no connector per §1).
- **NS-09/NS-10** show 44.6% because only 162 of 363 sites are in EU/Eurostat-covered countries. The Eurostat projections connector writes qualitative JSON to the `*_comment` field.

---

## 6. Summary statistics

### Coverage by API fill bucket

| Bucket                | Criteria                                                                                                | Count |
| --------------------- | ------------------------------------------------------------------------------------------------------- | ----: |
| **Full (≥90%)**       | NH-01, NH-10, NH-11, NH-12, HI-01, HI-07, RI-01, RI-04, RI-05, RI-06, EP-01, EP-02, EP-03, NS-04, NS-12 |    15 |
| **Good (70–89%)**     | NH-04, NH-05, HI-06, NS-01, NS-02, NS-03, NS-05, NS-08                                                  |     8 |
| **Moderate (50–69%)** | NH-02, NH-03, NH-07, NH-09, HI-02, HI-03, HI-04                                                         |     7 |
| **Sparse (20–49%)**   | NH-05b, NH-06, NH-08, NH-14, EP-04, RI-03, NS-09, NS-10                                                 |     8 |
| **Empty (0–19%)**     | NH-13, HI-05, HI-08, RI-02, EP-05, NS-06, NS-07, NS-11, NS-13                                           |     9 |

**Totals:** 15 full + 8 good + 7 moderate + 8 sparse + 9 empty = **46 criteria**

### API vs LLM fill comparison

| Metric                     | API DB |          LLM DB |
| -------------------------- | -----: | --------------: |
| Total sites                |    363 |             363 |
| Screening verdicts         | 14 544 |          86 232 |
| Mean fill % (all criteria) |   ~62% |            ~22% |
| Criteria with ≥90% fill    |     15 | 2 (E5, E6 only) |
| Criteria at 0% fill        |      9 |              25 |

**Key observation:** The LLM DB has far fewer populated **value** columns than the API DB, because the LLM pipeline was run before most API connectors enriched the data. LLM-side fill is high only for criteria where the LLM itself wrote structured data (e.g. E5 karst 85.3%, E6 subsidence 84.1%) or metadata columns (`*_comment`, `*_quality`). However, the LLM DB has **86 232 screening verdicts** (vs 14 544 in API) — the LLM's assessment output lives primarily in the `screening_verdicts` table, not in the domain columns.

---

## 7. Critical gaps and next steps

### Data issues flagged for follow-up

| #   | Issue                                                                  | Criterion | Severity   | Follow-up step        |
| --- | ---------------------------------------------------------------------- | --------- | ---------- | --------------------- |
| 1   | `grid_export_capacity_mw` = zone-level NTC, not site-level             | NS-02     | **High**   | §2.5.2                |
| 2   | `road_density_km_per_km2` = 0.000 for Rovinari (suspect false zero)    | EP-02     | **High**   | §2.3 (LL-017 check)   |
| 3   | `cooling_flow_m3s` = 0.15 m³/s seems low for Jiu river site            | NS-01     | **Medium** | §2.5.3                |
| 4   | `slope_angle_deg` = 85.25° is max in buffer, not representative        | NH-04     | **Medium** | §2.3 (interpretation) |
| 5   | `nearest_fault_km` = NULL for 71.4% of sites (EFSM20 limited coverage) | NH-02     | **Medium** | §2.3                  |
| 6   | `projected_pop_25km_60yr` = 14.7M looks implausibly high               | RI-06     | **Medium** | §2.5.6                |
| 7   | `patch_count` = 0% everywhere                                          | NS-05     | Low        | Connector bug         |
| 8   | NH-13 wildfire 0% in both DBs (GEE disabled)                           | NH-13     | Low        | §1 action D-03        |
| 9   | EP-04 only 14.6% (hospitals/prisons/care homes)                        | EP-04     | Low        | §1 action D-06        |

### Criteria requiring derived-field computation (from §1)

| Action | Criterion                      | Status                                    |
| ------ | ------------------------------ | ----------------------------------------- |
| R-01   | EP-01 composite score          | **Already computed** (DRV-02; 85.8% fill) |
| R-02   | NH-14 combined hazards         | Not started (0%)                          |
| R-03   | EP-05 concurrent hazard        | Not started (0%)                          |
| R-04   | RI-02 surface water cross-link | Not started (0%)                          |
| R-05   | NS-11 C2N synergies            | Not started (0%)                          |

### Connector gaps (from §1) — confirmed by inventory

| Action | Criterion                 | Status                                                       |
| ------ | ------------------------- | ------------------------------------------------------------ |
| R-06   | HI-08 IAEA PRIS           | Not started (0%)                                             |
| F-01   | NS-02 ENTSO-E fix         | Confirmed: 16 644 MW zone-level value                        |
| F-02   | HI-06 military re-attempt | Partially done: 88.4% have distance, but 44.6% missing names |
