<!-- man_hours: 1.2 -->
# Criteria DB fields and site samples (2026-05-17)

Read-only audit for implementing **scoring logic from existing DB data**
(no new connectors in this pass).

- **Rubric contract:** `config/scoring_rubrics/*.yaml` → `db_fields.api` anchors (`table.column`).
- **Physical DB:** column may differ (e.g. rubric `nh01_pga_475yr_g` → DB `pga_475yr_g`);
  `merge_resolver.resolve_scalar` and `column_aliases` apply at score time.
- **Cohort coverage:** share of `sites` rows with a non-NULL value on any mapped physical column.

## Readiness legend

| Tag | Meaning |
| --- | --- |
| `ready_all_api` | Every API anchor ≥80% populated — bands should fire if expressions match. |
| `partial_logic_possible` | Some anchors ≥80%, others missing — add derivations or band recipes using populated fields. |
| `sparse` | Limited API signal — logic possible but fragile. |
| `llm_only` | No API anchors in rubric — tier from LLM text only. |
| `no_api_data` | Anchors listed but 0% populated — needs connector (out of scope here). |

## Criteria → DB fields

| Criterion | Phases | Primary metric | Readiness | API anchor (`table.column`) | Physical column(s) | Fill % | LLM field |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| BF-01 | basic_filter | `—` | ready_all_api | `site_infrastructure_v2.nearest_substation_km` | `nearest_substation_km` | 100 | `bf01_grid_text` |
|  |  |  |  | `site_infrastructure_v2.hv_line_voltage_kv` | `hv_line_voltage_kv` | 95 |  |
|  |  |  |  | `site_infrastructure_v2.grid_export_capacity_mw` | `grid_export_capacity_mw` | 100 |  |
| BF-02 | basic_filter, ranking | `—` | partial_logic_possible | `site_infrastructure_v2.favourable_area_ha` | `favourable_area_ha` | 100 | `bf02_land_text` |
|  |  |  |  | `site_infrastructure_v2.buildable_area_ha` | `buildable_area_ha` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.largest_contiguous_ha` | `largest_contiguous_ha` | 98 |  |
|  |  |  |  | `sites.site_area_ha` | `site_area_ha` | 71 |  |
| EP-01 | exclusionary, ranking | `ep01_composite_score` | ready_all_api | `site_emergency.ep01_composite_score` | `ep01_composite_score` | 100 | `ep01_feasibility_text` |
| EP-02 | ranking | `road_density_km_per_km2` | ready_all_api | `site_emergency.road_density_km_per_km2` | `road_density_km_per_km2` | 100 | `ep02_routes_text` |
|  |  |  |  | `site_emergency.has_motorway_access` | `has_motorway_access` | 100 |  |
| EP-03 | ranking | `relief_m_per_10km` | partial_logic_possible | `site_emergency.major_river_barrier` | `major_river_barrier` | 100 | `ep03_geography_text` |
|  |  |  |  | `site_emergency.waterway_count_epz` | `waterway_count_epz` | 100 |  |
|  |  |  |  | `site_emergency.relief_m_per_10km` | `*relief_m_per_10km (not in schema)` | 0 |  |
| EP-04 | ranking | `special_pop_count` | ready_all_api | `site_emergency.hospital_count_epz` | `hospital_count_epz` | 100 | `ep04_special_pop_text` |
|  |  |  |  | `site_emergency.prison_count_epz` | `prison_count_epz` | 100 |  |
|  |  |  |  | `site_emergency.care_home_count_epz` | `care_home_count_epz` | 100 |  |
| EP-05 | ranking | `ep05_concurrent_index` | no_api_data | `site_emergency.ep05_concurrent_index` | `*ep05_concurrent_index (not in schema)` | 0 | `ep05_concurrent_text` |
| HI-01 | avoidance, ranking | `composite` | partial_logic_possible | `site_human_induced.nearest_airport_km` | `nearest_airport_km` | 100 | `hi01_aircraft_text` |
|  |  |  |  | `site_human_induced.nearest_airport_type` | `nearest_airport_type` | 100 |  |
|  |  |  |  | `site_human_induced.nearest_airport_class` | `nearest_airport_class` | 100 |  |
|  |  |  |  | `site_human_induced.nearest_military_airfield_km` | `*nearest_military_airfield_km (not in schema)` | 0 |  |
|  |  |  |  | `site_human_induced.nearest_military_class` | `nearest_military_class` | 90 |  |
|  |  |  |  | `site_human_induced.nearest_military_km` | `nearest_military_km` | 90 |  |
|  |  |  |  | `site_human_induced.nearest_high_consequence_military_class` | `nearest_high_consequence_military_class` | 60 |  |
|  |  |  |  | `site_human_induced.nearest_high_consequence_military_km` | `nearest_high_consequence_military_km` | 60 |  |
|  |  |  |  | `site_human_induced.hi06_quality` | `hi06_quality` | 100 |  |
|  |  |  |  | `site_human_induced.flight_path_distance_km` | `flight_path_distance_km` | 100 |  |
|  |  |  |  | `site_human_induced.hi01_comment` | `hi01_comment` | 100 |  |
| HI-02 | avoidance, ranking | `nearest_seveso_km` | partial_logic_possible | `site_human_induced.nearest_seveso_km` | `nearest_seveso_km` | 4 | `hi02_explosions_text` |
|  |  |  |  | `site_human_induced.nearest_ied_km` | `*nearest_ied_km (not in schema)` | 0 |  |
|  |  |  |  | `site_human_induced.hi02_quality` | `hi02_quality` | 100 |  |
| HI-03 | avoidance, ranking | `nearest_toxic_source_km` | sparse | `site_human_induced.nearest_toxic_source_km` | `nearest_toxic_source_km` | 25 | `hi03_toxic_text` |
|  |  |  |  | `site_human_induced.toxic_source_type` | `*toxic_source_type (not in schema)` | 0 |  |
| HI-04 | avoidance, ranking | `nearest_flammable_storage_km` | partial_logic_possible | `site_human_induced.nearest_flammable_storage_km` | `nearest_flammable_storage_km` | 4 | `hi04_external_fires_text` |
|  |  |  |  | `site_human_induced.nearest_pipeline_km` | `nearest_pipeline_km` | 0 |  |
|  |  |  |  | `site_human_induced.hi04_quality` | `hi04_quality` | 100 |  |
| HI-05 | ranking | `nearest_hazmat_corridor_km` | no_api_data | `site_human_induced.nearest_hazmat_corridor_km` | `hazmat_route_distance_km` | 0 | `hi05_transport_text` |
|  |  |  |  | `site_human_induced.hi05_quality` | `hi05_quality` | 0 |  |
| HI-06 | avoidance, ranking | `nearest_military_km` | partial_logic_possible | `site_human_induced.nearest_military_km` | `nearest_military_km` | 90 | `hi06_military_text` |
|  |  |  |  | `site_human_induced.nearest_military_class` | `nearest_military_class` | 90 |  |
|  |  |  |  | `site_human_induced.nearest_high_consequence_military_km` | `nearest_high_consequence_military_km` | 60 |  |
|  |  |  |  | `site_human_induced.nearest_high_consequence_military_class` | `nearest_high_consequence_military_class` | 60 |  |
|  |  |  |  | `site_human_induced.military_type` | `*military_type (not in schema)` | 0 |  |
| HI-07 | ranking | `transmitter_count_10km` | ready_all_api | `site_human_induced.transmitter_count_10km` | `transmitter_count` | 100 | `hi07_emi_text` |
| HI-08 | ranking | `nearest_nuclear_km` | no_api_data | `site_human_induced.nearest_nuclear_km` | `nearest_nuclear_km` | 0 | `hi08_other_nuclear_text` |
|  |  |  |  | `site_human_induced.hi08_quality` | `hi08_quality` | 0 |  |
| NH-01 | ranking, avoidance | `pga_2475yr_g` | partial_logic_possible | `site_natural_hazards.nh01_pga_475yr_g` | `pga_475yr_g` | 100 | `nh01_seismic_text` |
|  |  |  |  | `site_natural_hazards.nh01_pga_2475yr_g` | `pga_2475yr_g` | 96 |  |
|  |  |  |  | `site_natural_hazards.vs30_ms` | `*vs30_ms (not in schema)` | 0 |  |
| NH-02 | exclusionary, ranking | `nearest_fault_km` | ready_all_api | `site_natural_hazards.nearest_fault_km` | `nearest_fault_km` | 100 | `nh02_fault_text` |
|  |  |  |  | `site_natural_hazards.fault_name` | `fault_name` | 100 |  |
|  |  |  |  | `site_natural_hazards.fault_slip_rate_mm_yr` | `fault_slip_rate_mm_yr` | 100 |  |
| NH-03 | exclusionary, ranking | `liquefaction_suscept` | partial_logic_possible | `site_natural_hazards.liquefaction_suscept` | `liquefaction_suscept` | 98 | `nh03_liquefaction_text` |
|  |  |  |  | `site_natural_hazards.nh03_quality` | `nh03_quality` | 100 |  |
|  |  |  |  | `site_natural_hazards.nh03_source` | `nh03_source` | 100 |  |
|  |  |  |  | `site_natural_hazards.bearing_capacity_kpa` | `bearing_capacity_kpa` | 85 |  |
|  |  |  |  | `site_natural_hazards.groundwater_depth_m` | `groundwater_depth_m` | 0 |  |
|  |  |  |  | `site_natural_hazards.pga_475yr_g` | `pga_475yr_g` | 100 |  |
|  |  |  |  | `site_natural_hazards.depth_to_bedrock_m` | `depth_to_bedrock_m` | 99 |  |
| NH-04 | exclusionary, ranking | `slope_angle_deg` | ready_all_api | `site_natural_hazards.slope_angle_deg` | `slope_angle_deg` | 98 | `nh04_slope_text` |
|  |  |  |  | `site_natural_hazards.slope_stability_class` | `slope_stability_class` | 98 |  |
|  |  |  |  | `site_natural_hazards.nh04_dem_cog_slope_max_deg` | `nh04_dem_cog_slope_max_deg` | 98 |  |
| NH-05 | ranking | `mining_void_distance_km` | partial_logic_possible | `site_natural_hazards.karst_present` | `karst_present` | 100 | `nh05_subsidence_text` |
|  |  |  |  | `site_natural_hazards.karst_severity` | `karst_severity` | 100 |  |
|  |  |  |  | `site_natural_hazards.karst_formation_type` | `karst_formation_type` | 23 |  |
|  |  |  |  | `site_natural_hazards.mining_void_present` | `mining_void_present` | 100 |  |
|  |  |  |  | `site_natural_hazards.mining_void_distance_km` | `mining_void_distance_km` | 28 |  |
|  |  |  |  | `site_natural_hazards.subsidence_risk_class` | `subsidence_risk_class` | 0 |  |
| NH-06 | ranking | `bearing_capacity_kpa` | partial_logic_possible | `site_natural_hazards.bearing_capacity_kpa` | `bearing_capacity_kpa` | 85 | `nh06_foundation_text` |
|  |  |  |  | `site_natural_hazards.depth_to_bedrock_m` | `depth_to_bedrock_m` | 99 |  |
|  |  |  |  | `site_natural_hazards.groundwater_depth_m` | `groundwater_depth_m` | 0 |  |
| NH-07 | exclusionary, ranking | `nearest_volcano_km` | partial_logic_possible | `site_natural_hazards.nearest_volcano_km` | `nearest_holocene_volcano_km` | 34 | `nh07_volcanism_text` |
|  |  |  |  | `site_natural_hazards.volcano_name` | `volcano_name` | 34 |  |
|  |  |  |  | `site_natural_hazards.nh07_hazard_class` | `nh07_hazard_class` | 100 |  |
| NH-08 | avoidance, ranking | `coast_distance_km` | partial_logic_possible | `site_natural_hazards.coast_distance_km` | `distance_to_coast_km` | 100 | `nh08_coastal_text` |
|  |  |  |  | `site_natural_hazards.storm_surge_class` | `storm_surge_risk` | 1 |  |
|  |  |  |  | `site_natural_hazards.tsunami_zone_flag` | `tsunami_risk` | 0 |  |
|  |  |  |  | `sites.elevation_m` | `elevation_m` | 100 |  |
| NH-09 | avoidance, ranking | `river_distance_km` | partial_logic_possible | `site_natural_hazards.river_distance_km` | `nearest_river_km` | 4 | `nh09_river_flood_text` |
|  |  |  |  | `site_natural_hazards.elevation_above_design_flood_m` | `*elevation_above_design_flood_m (not in schema)` | 0 |  |
|  |  |  |  | `site_natural_hazards.flood_zone_class_500yr` | `flood_zone_class` | 100 |  |
| NH-10 | ranking | `max_wind_speed_ms` | ready_all_api | `site_natural_hazards.max_wind_speed_ms` | `max_wind_speed_ms` | 100 | `nh10_winds_text` |
| NH-11 | ranking | `—` | partial_logic_possible | `site_natural_hazards.spi12_min` | `*spi12_min (not in schema)` | 0 | `nh11_precip_text` |
|  |  |  |  | `site_natural_hazards.snow_months_per_year` | `*snow_months_per_year (not in schema)` | 0 |  |
|  |  |  |  | `site_natural_hazards.mean_annual_precip_mm` | `mean_annual_precip_mm` | 100 |  |
|  |  |  |  | `site_natural_hazards.extreme_precip_mm` | `extreme_precip_mm` | 100 |  |
|  |  |  |  | `site_natural_hazards.freezing_days_per_year` | `*freezing_days_per_year (not in schema)` | 0 |  |
| NH-12 | ranking | `—` | ready_all_api | `site_natural_hazards.extreme_temp_max_c` | `extreme_temp_max_c` | 100 | `nh12_temperature_text` |
|  |  |  |  | `site_natural_hazards.extreme_temp_min_c` | `extreme_temp_min_c` | 100 |  |
| NH-13 | ranking | `combustible_veg_pct` | no_api_data | `site_natural_hazards.combustible_veg_pct` | `*combustible_veg_pct (not in schema)` | 0 | `nh13_wildfire_text` |
| NH-14 | ranking | `nh_min_resolved_score` | no_api_data | `site_natural_hazards.nh14_combined_index` | `*nh14_combined_index (not in schema)` | 0 | `nh14_combined_text` |
| NS-01 | avoidance, ranking | `—` | ready_all_api | `site_infrastructure_v2.cooling_source_type` | `cooling_source_type` | 100 | `ns01_cooling_text` |
|  |  |  |  | `site_infrastructure_v2.cooling_source_name` | `cooling_source_name` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.cooling_source_hyriv_id` | `cooling_source_hyriv_id` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.cooling_distance_km` | `cooling_distance_km` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.cooling_flow_m3s` | `cooling_flow_m3s` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.water_stress_score` | `water_stress_score` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.water_stress_label` | `water_stress_label` | 100 |  |
| NS-02 | avoidance, ranking | `—` | ready_all_api | `site_infrastructure_v2.nearest_substation_km` | `nearest_substation_km` | 100 | `ns02_grid_text` |
|  |  |  |  | `site_infrastructure_v2.nearest_hv_line_km` | `nearest_hv_line_km` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.hv_line_voltage_kv` | `hv_line_voltage_kv` | 95 |  |
|  |  |  |  | `site_infrastructure_v2.grid_export_capacity_mw` | `grid_export_capacity_mw` | 100 |  |
| NS-03 | avoidance, ranking | `—` | sparse | `site_infrastructure_v2.nearest_highway_km` | `nearest_highway_km` | 70 | `ns03_transport_text` |
|  |  |  |  | `site_infrastructure_v2.nearest_rail_km` | `nearest_rail_km` | 53 |  |
|  |  |  |  | `site_infrastructure_v2.nearest_waterway_km` | `nearest_waterway_km` | 17 |  |
|  |  |  |  | `site_infrastructure_v2.heavy_haul_capable` | `heavy_haul_capable` | 75 |  |
| NS-04 | ranking | `favourable_land_pct` | ready_all_api | `site_infrastructure_v2.favourable_land_pct` | `favourable_land_pct` | 100 | `ns04_topography_text` |
|  |  |  |  | `site_infrastructure_v2.favourable_area_ha` | `favourable_area_ha` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.favourable_area_method` | `favourable_area_method` | 100 |  |
| NS-05 | avoidance, ranking | `composite` | ready_all_api | `site_infrastructure_v2.buildable_area_ha` | `buildable_area_ha` | 100 | `ns05_land_text` |
|  |  |  |  | `site_infrastructure_v2.largest_contiguous_ha` | `largest_contiguous_ha` | 98 |  |
|  |  |  |  | `site_infrastructure_v2.patch_count` | `patch_count` | 98 |  |
| NS-06 | ranking | `reuse_tier` | llm_only | — | — | — | `ns06_reuse_text` |
| NS-07 | avoidance, ranking | `env_impact_tier` | no_api_data | `site_infrastructure_v2.env_impact_tier` | `env_impact_tier` | 0 | `ns07_env_impact_text` |
| NS-08 | exclusionary, ranking | `n2k_nearest_distance_km` | partial_logic_possible | `site_infrastructure_v2.n2k_nearest_distance_km` | `n2k_nearest_distance_km` | 44 | `ns08_ecology_text` |
|  |  |  |  | `site_infrastructure_v2.wdpa_nearest_distance_km` | `wdpa_nearest_distance_km` | 68 |  |
|  |  |  |  | `site_infrastructure_v2.ecological_natural_pct` | `ecological_natural_pct` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.n2k_overlap` | `n2k_overlap` | 44 |  |
|  |  |  |  | `site_infrastructure_v2.wdpa_overlap` | `wdpa_overlap` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.n2k_sensitivity_class` | `n2k_sensitivity_class` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.wdpa_sensitivity_class` | `wdpa_sensitivity_class` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.n2k_result_json` | `n2k_result_json` | 100 |  |
|  |  |  |  | `site_infrastructure_v2.wdpa_result_json` | `wdpa_result_json` | 100 |  |
| NS-09 | ranking | `socio_tier` | no_api_data | `site_socioeconomic.unemployment_pct` | `*unemployment_pct (not in schema)` | 0 | `ns09_socioeconomic_text` |
|  |  |  |  | `site_socioeconomic.gdp_per_capita_eur` | `*gdp_per_capita_eur (not in schema)` | 0 |  |
| NS-10 | ranking | `workforce_tier` | llm_only | — | — | — | `ns10_workforce_text` |
| NS-11 | ranking | `ns11_synergy_index` | no_api_data | `site_infrastructure_v2.ns11_synergy_index` | `*ns11_synergy_index (not in schema)` | 0 | `ns11_synergy_text` |
| NS-12 | ranking | `policy_tier` | llm_only | — | — | — | `ns12_policy_text` |
| NS-13 | ranking | `logistics_tier` | llm_only | — | — | — | `ns13_construction_text` |
| RI-01 | ranking | `—` | no_api_data | `site_radiological.wind_rose_json` | `*wind_rose_json (not in schema)` | 0 | `ri01_dispersion_text` |
|  |  |  |  | `site_radiological.pg_class_f_fraction` | `*pg_class_f_fraction (not in schema)` | 0 |  |
|  |  |  |  | `site_radiological.pg_class_e_fraction` | `*pg_class_e_fraction (not in schema)` | 0 |  |
|  |  |  |  | `site_radiological.mean_mixing_height_m` | `*mean_mixing_height_m (not in schema)` | 0 |  |
| RI-02 | ranking | `cooling_flow_m3s` | ready_all_api | `site_infrastructure_v2.cooling_flow_m3s` | `cooling_flow_m3s` | 100 | `ri02_surface_water_text` |
| RI-03 | ranking | `groundwater_vulnerability_class` | partial_logic_possible | `site_radiological.aquifer_type` | `aquifer_type` | 99 | `ri03_groundwater_text` |
|  |  |  |  | `site_radiological.groundwater_vulnerability_class` | `*groundwater_vulnerability_class (not in schema)` | 0 |  |
| RI-04 | ranking | `—` | ready_all_api | `site_radiological.pop_density_5km` | `pop_density_5km` | 100 | `ri04_population_text` |
|  |  |  |  | `site_radiological.pop_density_16km` | `pop_density_16km` | 100 |  |
|  |  |  |  | `site_radiological.pop_density_25km` | `pop_density_25km` | 100 |  |
|  |  |  |  | `site_radiological.pop_density_80km` | `pop_density_80km` | 100 |  |
| RI-05 | avoidance, ranking | `ri05_distance_margin_pct` | sparse | `site_radiological.nearest_city_50k_km` | `nearest_city_50k_km` | 45 | `ri05_population_centres_text` |
|  |  |  |  | `site_radiological.nearest_city_pop` | `nearest_city_pop` | 45 |  |
| RI-06 | ranking | `pop_growth_rate_pct` | ready_all_api | `site_radiological.pop_growth_rate_pct` | `pop_growth_rate_pct` | 100 | `ri06_pop_projections_text` |
|  |  |  |  | `site_radiological.projected_pop_25km_60yr` | `projected_pop_25km_60yr` | 100 |  |

## Priority subset (logic without new connectors)

Criteria tagged `ready_all_api` or `partial_logic_possible`.

| Criterion | Readiness | Gaps (anchors under 80% fill) |
| --- | --- | --- |
| BF-01 | ready_all_api | — |
| BF-02 | partial_logic_possible | `sites.site_area_ha` 71% |
| EP-01 | ready_all_api | — |
| EP-02 | ready_all_api | — |
| EP-03 | partial_logic_possible | `site_emergency.relief_m_per_10km` 0% |
| EP-04 | ready_all_api | — |
| HI-01 | partial_logic_possible | `site_human_induced.nearest_military_airfield_km` 0%; `site_human_induced.nearest_high_consequence_military_class` 60%; `site_human_induced.nearest_high_consequence_military_km` 60% |
| HI-02 | partial_logic_possible | `site_human_induced.nearest_seveso_km` 4%; `site_human_induced.nearest_ied_km` 0% |
| HI-04 | partial_logic_possible | `site_human_induced.nearest_flammable_storage_km` 4%; `site_human_induced.nearest_pipeline_km` 0% |
| HI-06 | partial_logic_possible | `site_human_induced.nearest_high_consequence_military_km` 60%; `site_human_induced.nearest_high_consequence_military_class` 60%; `site_human_induced.military_type` 0% |
| HI-07 | ready_all_api | — |
| NH-01 | partial_logic_possible | `site_natural_hazards.vs30_ms` 0% |
| NH-02 | ready_all_api | — |
| NH-03 | partial_logic_possible | `site_natural_hazards.groundwater_depth_m` 0% |
| NH-04 | ready_all_api | — |
| NH-05 | partial_logic_possible | `site_natural_hazards.karst_formation_type` 23%; `site_natural_hazards.mining_void_distance_km` 28%; `site_natural_hazards.subsidence_risk_class` 0% |
| NH-06 | partial_logic_possible | `site_natural_hazards.groundwater_depth_m` 0% |
| NH-07 | partial_logic_possible | `site_natural_hazards.nearest_volcano_km` 34%; `site_natural_hazards.volcano_name` 34% |
| NH-08 | partial_logic_possible | `site_natural_hazards.storm_surge_class` 1%; `site_natural_hazards.tsunami_zone_flag` 0% |
| NH-09 | partial_logic_possible | `site_natural_hazards.river_distance_km` 4%; `site_natural_hazards.elevation_above_design_flood_m` 0% |
| NH-10 | ready_all_api | — |
| NH-11 | partial_logic_possible | `site_natural_hazards.spi12_min` 0%; `site_natural_hazards.snow_months_per_year` 0%; `site_natural_hazards.freezing_days_per_year` 0% |
| NH-12 | ready_all_api | — |
| NS-01 | ready_all_api | — |
| NS-02 | ready_all_api | — |
| NS-04 | ready_all_api | — |
| NS-05 | ready_all_api | — |
| NS-08 | partial_logic_possible | `site_infrastructure_v2.n2k_nearest_distance_km` 44%; `site_infrastructure_v2.wdpa_nearest_distance_km` 68%; `site_infrastructure_v2.n2k_overlap` 44% |
| RI-02 | ready_all_api | — |
| RI-03 | partial_logic_possible | `site_radiological.groundwater_vulnerability_class` 0% |
| RI-04 | ready_all_api | — |
| RI-06 | ready_all_api | — |

## Ten example sites (resolved scoring context)

Values below are what `build_context_for_site` exposes (includes aliases and
derivations). `NULL` means the band evaluator sees missing data for that key.

### Suceava power station (RO, retired)

`site_id`: `693d9b73-f9fc-4502-9b94-be020c5d21fb`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.28` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `100.00` | 100 |
| BF-02 | `favourable_area_ha` | `247.28` | 100 |
|  | `buildable_area_ha` | `75.56` | 100 |
|  | `largest_contiguous_ha` | `75.56` | 98 |
|  | `site_area_ha` | `75.56` | 71 |
| EP-01 | `ep01_composite_score` | `44.3` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.542` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `21` | 100 |
|  | `prison_count_epz` | `0` | 100 |
|  | `care_home_count_epz` | `2` | 100 |
| HI-01 | `nearest_airport_km` | `4.62` | 100 |
|  | `nearest_airport_type` | `heliport` | 100 |
|  | `nearest_airport_class` | `heliport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `0.15` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `0.15` | 60 |
|  | `hi06_quality` | `high` | 100 |
|  | `flight_path_distance_km` | `2.88` | 100 |
|  | `hi01_comment` | `Nearest: Suceava "St. John the New" Emergency Hospital Heliport (heliport) at 4.6 km; Nearest lar...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `0.15` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `0.15` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `29` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.16478` | 100 |
|  | `nh01_pga_2475yr_g` | `0.29054` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `very_low` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `87.30` | 85 |
|  | `pga_475yr_g` | `0.16478` | 100 |
|  | `depth_to_bedrock_m` | `27.73` | 99 |
| NH-04 | `slope_angle_deg` | `5.54` | 98 |
|  | `slope_stability_class` | `moderate` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `85.88` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `87.30` | 85 |
|  | `depth_to_bedrock_m` | `27.73` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `332.96` | 100 |
|  | `elevation_m` | `277.91` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `7.83` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `23.66` | 100 |
|  | `extreme_precip_mm` | `0.28` | 100 |
| NH-12 | `extreme_temp_max_c` | `23.73` | 100 |
|  | `extreme_temp_min_c` | `-9.07` | 100 |
| NS-01 | `cooling_source_type` | `river` | 100 |
|  | `cooling_source_name` | `Suceava` | 100 |
|  | `cooling_source_hyriv_id` | `20437434` | 100 |
|  | `cooling_distance_km` | `0.44` | 100 |
|  | `cooling_flow_m3s` | `23.88` | 100 |
|  | `water_stress_score` | `0.180` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.28` | 100 |
|  | `nearest_hv_line_km` | `0.85` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `100.00` | 100 |
| NS-04 | `favourable_land_pct` | `87.50` | 100 |
|  | `favourable_area_ha` | `247.28` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `75.56` | 100 |
|  | `largest_contiguous_ha` | `75.56` | 98 |
|  | `patch_count` | `13` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `0.190` | 44 |
|  | `wdpa_nearest_distance_km` | `8.808` | 68 |
|  | `ecological_natural_pct` | `8.10` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `high` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 47.651873, 'lon': 26.298268, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'RO', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 1253.825650559147, 'overlap': False, 'sitecode': 'ROSCI0380', 'sitename': 'Râul Suceava Liteni', 'sitetype': 'B', 'distance_km': 0.19, 'direction_deg': 132.8, 'conservation_score': None}, {'area_ha': 395.78114094573095, 'overlap': False, 'sitecode': 'ROSCI0371', 'sitename': 'Cumpărătura', 'sitetype': 'B', 'distance_km': 6.392, 'direction_deg': 183.1, 'conservation_score': None}, {'area_ha': 57.586124541396465, 'overlap': False, 'sitecode': 'ROSAC0082', 'sitename': 'Fânețele seculare Ponoare', 'sitetype': 'B', 'distance_km': 8.624, 'direction_deg': 199.4, 'conservation_score': 0.0}, {'area_ha': 8771.562323433536, 'overlap': False, 'sitecode': 'ROSCI0075', 'sitename': 'Pădurea Pătrăuți', 'sitetype': 'B', 'distance_km': 8.849, 'direction_deg': 334.0, 'conservation_score': 0.0}, {'area_ha': 9.403086316812976, 'overlap': False, 'sitecode': 'ROSAC0081', 'sitename': 'Fânețele seculare Frumoasa', 'sitetype': 'B', 'distance_km': 9.441, 'direction_deg': 231.2, 'conservation_score': 0.0}, {'area_ha': 586.6256298898763, 'overlap': False, 'sitecode': 'ROSAC0391', 'sitename': 'Siretul Mijlociu - Bucecea', 'sitetype': 'B', 'distance_km': 11.431, 'direction_deg': 39.8, 'conservation_score': 0.0}, {'area_ha': 876.7241034919177, 'overlap': False, 'sitecode': 'ROSCI0310', 'sitename': 'Lacurile Fălticeni', 'sitetype': 'B', 'distance_km': 12.083, 'direction_deg': 187.8, 'conservation_score': None}, {'area_ha': 787.4415688438909, 'overlap': False, 'sitecode': 'ROSPA0064', 'sitename': 'Lacurile Fălticeni', 'sitetype': 'A', 'distance_km': 12.083, 'direction_deg': 187.6, 'conservation_score': None}, {'area_ha': 2106.207076636514, 'overlap': False, 'sitecode': 'ROSPA0110', 'sitename': 'Acumulările Rogojești - Bucecea', 'sitetype': 'A', 'distance_km': 14.916, 'direction_deg': 354.1, 'conservation_score': None}, {'area_ha': 25356.1308085348, 'overlap': False, 'sitecode': 'ROSPA0116', 'sitename': 'Dorohoi - Șaua Bucecei', 'sitetype': 'A', 'distance_km': 18.308, 'direction_deg': 74.3, 'conservation_score': None}, {'area_ha': 25060.9667798546, 'overlap': False, 'sitecode': 'ROSCI0076', 'sitename': 'Dealul Mare - Hârlău', 'sitetype': 'B', 'distance_km': 19.688, 'direction_deg': 114.2, 'conservation_score': 0.0}, {'area_ha': 320.39472890000053, 'overlap': False, 'sitecode': 'ROSCI0184', 'sitename': 'Pădurea Zamostea - Lunca', 'sitetype': 'B', 'distance_km': 22.458, 'direction_deg': 351.8, 'conservation_score': 0.0}, {'area_ha': 5330.169519859273, 'overlap': False, 'sitecode': 'ROSAC0365', 'sitename': 'Râul Moldova între Păltinoasa și Ruși', 'sitetype': 'B', 'distance_km': 24.113, 'direction_deg': 195.1, 'conservation_score': 0.0}, {'area_ha': 1099.1232134367863, 'overlap': False, 'sitecode': 'ROSCI0379', 'sitename': 'Râul Suceava', 'sitetype': 'B', 'distance_km': 27.173, 'direction_deg': 308.2, 'conservation_score': 0.0}, {'area_ha': 144.63362066965587, 'overlap': False, 'sitecode': 'ROSCI0392', 'sitename': 'Slatina', 'sitetype': 'B', 'distance_km': 29.126, 'direction_deg': 226.2, 'conservation_score': None}, {'area_ha': 2235.6192654947235, 'overlap': False, 'sitecode': 'ROSPA0156', 'sitename': 'Iazul Mare - Stăuceni - Drăcșani', 'sitetype': 'A', 'distance_km': 29.302, 'direction_deg': 78.2, 'conservation_score': None}], 'n2k_sac_count': 12, 'n2k_spa_count': 4, 'reference_date': '1726012800000', 'sensitivity_class': 'high', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 1253.825650559147, 'n2k_nearest_sitecode': 'ROSCI0380', 'n2k_nearest_sitename': 'Râul Suceava Liteni', 'n2k_nearest_sitetype': 'B', 'n2k_sites_within_5km': 1, 'n2k_area_fraction_5km': 0.0532, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 9, 'n2k_sites_within_25km': 13, 'n2k_area_fraction_16km': 0.082, 'n2k_area_fraction_25km': 0.1113, 'n2k_nearest_distance_km': 0.19, 'n2k_max_conservation_score': 0.0, 'n2k_total_protected_area_ha': 74392.19}` | 100 |
|  | `wdpa_result_json` | `{'lat': 47.651873, 'lon': 26.298268, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'RO', 'country_iso3': 'ROU', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 24.11808014, 'overlap': False, 'site_id': 9368, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.808, 'name_english': 'Fânațele seculare Ponoare', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 9.40308952, 'overlap': False, 'site_id': 183774, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.441, 'name_english': 'Fânațele seculare Frumoasa', 'iucn_category': 'III', 'designation_name': 'Natural monument', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 40.15319061, 'overlap': False, 'site_id': 183791, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 12.845, 'name_english': 'Pădurea Crujana', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 5.150939940000001, 'overlap': False, 'site_id': 183866, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.303, 'name_english': 'Bucecea - Bălțile Siretului', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 135.73306274, 'overlap': False, 'site_id': 183804, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.952, 'name_english': 'Făgetul Dragomirna', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 125.08738708, 'overlap': False, 'site_id': 183797, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.13, 'name_english': 'Pădurea Zamostea - Luncă', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Fânațele seculare Ponoare', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 24.11808014, 'wdpa_nearest_site_id': 9368, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 0, 'wdpa_area_fraction_5km': 0.0, 'wdpa_iucn_ii_iii_count': 1, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 5, 'wdpa_sites_within_25km': 6, 'wdpa_area_fraction_16km': 0.0023, 'wdpa_area_fraction_25km': 0.0014, 'wdpa_iucn_iv_v_vi_count': 1, 'wdpa_nearest_designation': 'Nature reserve', 'wdpa_nearest_distance_km': 8.808, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'IV', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'III', 'wdpa_total_protected_area_ha': 339.65, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `23.88` | 100 |
| RI-03 | `aquifer_type` | `low permeability` | 99 |
| RI-04 | `pop_density_5km` | `1228.98` | 100 |
|  | `pop_density_16km` | `222.23` | 100 |
|  | `pop_density_25km` | `150.43` | 100 |
|  | `pop_density_80km` | `93.10` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.185` | 100 |
|  | `projected_pop_25km_60yr` | `227967` | 100 |

### Mintia-Deva power station (RO, retired)

`site_id`: `52a7babe-313f-493b-86b9-bd0c4aece4c3`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.60` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `1285.00` | 100 |
| BF-02 | `favourable_area_ha` | `131.99` | 100 |
|  | `buildable_area_ha` | `0.01` | 100 |
|  | `largest_contiguous_ha` | `0.01` | 98 |
|  | `site_area_ha` | `0.01` | 71 |
| EP-01 | `ep01_composite_score` | `70.3` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.472` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `27` | 100 |
|  | `prison_count_epz` | `0` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `12.36` | 100 |
|  | `nearest_airport_type` | `small_airport` | 100 |
|  | `nearest_airport_class` | `small_airport` | 100 |
|  | `nearest_military_class` | `other` | 90 |
|  | `nearest_military_km` | `3.61` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `7.17` | 60 |
|  | `hi06_quality` | `high` | 100 |
|  | `flight_path_distance_km` | `6.18` | 100 |
|  | `hi01_comment` | `Nearest: Săulești Airfield (small_airport) at 12.4 km; Nearest large: 98.6 km; Nearest medium: 70...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `3.61` | 90 |
|  | `nearest_military_class` | `other` | 90 |
|  | `nearest_high_consequence_military_km` | `7.17` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `34` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.04778` | 100 |
|  | `nh01_pga_2475yr_g` | `0.10621` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `moderate` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `83.30` | 85 |
|  | `pga_475yr_g` | `0.04778` | 100 |
|  | `depth_to_bedrock_m` | `17.62` | 99 |
| NH-04 | `slope_angle_deg` | `11.55` | 98 |
|  | `slope_stability_class` | `steep` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `86.35` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `True` | 100 |
|  | `mining_void_distance_km` | `4.927` | 28 |
| NH-06 | `bearing_capacity_kpa` | `83.30` | 85 |
|  | `depth_to_bedrock_m` | `17.62` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `487.32` | 100 |
|  | `elevation_m` | `191.41` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `6.11` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `24.55` | 100 |
|  | `extreme_precip_mm` | `0.18` | 100 |
| NH-12 | `extreme_temp_max_c` | `24.07` | 100 |
|  | `extreme_temp_min_c` | `-4.72` | 100 |
| NS-01 | `cooling_source_type` | `major_river` | 100 |
|  | `cooling_source_name` | `Râul Mureș` | 100 |
|  | `cooling_source_hyriv_id` | `20482550` | 100 |
|  | `cooling_distance_km` | `0.71` | 100 |
|  | `cooling_flow_m3s` | `171.09` | 100 |
|  | `water_stress_score` | `0.071` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.60` | 100 |
|  | `nearest_hv_line_km` | `0.28` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `1285.00` | 100 |
| NS-04 | `favourable_land_pct` | `55.60` | 100 |
|  | `favourable_area_ha` | `131.99` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `0.01` | 100 |
|  | `largest_contiguous_ha` | `0.01` | 98 |
|  | `patch_count` | `9` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `1.399` | 44 |
|  | `wdpa_nearest_distance_km` | `4.170` | 68 |
|  | `ecological_natural_pct` | `39.50` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `moderate` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 45.912791, 'lon': 22.826129, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'RO', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 1855.784490498543, 'overlap': False, 'sitecode': 'ROSCI0373', 'sitename': 'Râul Mureș între Brănișca și Ilia', 'sitetype': 'B', 'distance_km': 1.399, 'direction_deg': 299.1, 'conservation_score': None}, {'area_ha': 113.29411648032122, 'overlap': False, 'sitecode': 'ROSCI0054', 'sitename': 'Dealul Cetății Deva', 'sitetype': 'B', 'distance_km': 4.17, 'direction_deg': 121.4, 'conservation_score': 0.0}, {'area_ha': 98.2397028553499, 'overlap': False, 'sitecode': 'ROSCI0136', 'sitename': 'Pădurea Bejan', 'sitetype': 'B', 'distance_km': 7.563, 'direction_deg': 144.4, 'conservation_score': 0.0}, {'area_ha': 26678.982323875312, 'overlap': False, 'sitecode': 'ROSPA0132', 'sitename': 'Munții Metaliferi', 'sitetype': 'A', 'distance_km': 10.282, 'direction_deg': 43.2, 'conservation_score': None}, {'area_ha': 250.5808213951798, 'overlap': False, 'sitecode': 'ROSCI0110', 'sitename': 'Măgurile Băiței', 'sitetype': 'B', 'distance_km': 11.962, 'direction_deg': 16.6, 'conservation_score': 0.0}, {'area_ha': 34201.39181557665, 'overlap': False, 'sitecode': 'ROSAC0064', 'sitename': 'Defileul Mureșului', 'sitetype': 'B', 'distance_km': 13.553, 'direction_deg': 286.2, 'conservation_score': 0.0}, {'area_ha': 8372.001779262904, 'overlap': False, 'sitecode': 'ROSPA0139', 'sitename': 'Piemontul Munților Metaliferi - Vințu', 'sitetype': 'A', 'distance_km': 14.663, 'direction_deg': 83.8, 'conservation_score': None}, {'area_ha': 14318.259323758812, 'overlap': False, 'sitecode': 'ROSCI0325', 'sitename': 'Munții Metaliferi', 'sitetype': 'B', 'distance_km': 21.628, 'direction_deg': 320.2, 'conservation_score': 0.0}, {'area_ha': 18.5747842818906, 'overlap': False, 'sitecode': 'ROSCI0254', 'sitename': 'Tufurile calcaroase din Valea Bobâlna', 'sitetype': 'B', 'distance_km': 22.06, 'direction_deg': 92.7, 'conservation_score': 0.0}, {'area_ha': 7064.14362561068, 'overlap': False, 'sitecode': 'ROSAC0250', 'sitename': 'Ținutul Pădurenilor', 'sitetype': 'B', 'distance_km': 23.339, 'direction_deg': 228.3, 'conservation_score': 0.0}, {'area_ha': 736.0443753649065, 'overlap': False, 'sitecode': 'ROSCI0029', 'sitename': 'Cheile Glodului, Cibului și Măzii', 'sitetype': 'B', 'distance_km': 25.104, 'direction_deg': 61.8, 'conservation_score': 0.0}, {'area_ha': 35974.39902128188, 'overlap': False, 'sitecode': 'ROSCI0355', 'sitename': 'Podișul Lipovei - Poiana Ruscă', 'sitetype': 'B', 'distance_km': 25.576, 'direction_deg': 253.9, 'conservation_score': None}], 'n2k_sac_count': 10, 'n2k_spa_count': 2, 'reference_date': '1726012800000', 'sensitivity_class': 'moderate', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 1855.784490498543, 'n2k_nearest_sitecode': 'ROSCI0373', 'n2k_nearest_sitename': 'Râul Mureș între Brănișca și Ilia', 'n2k_nearest_sitetype': 'B', 'n2k_sites_within_5km': 2, 'n2k_area_fraction_5km': 0.1416, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 7, 'n2k_sites_within_25km': 10, 'n2k_area_fraction_16km': 0.0687, 'n2k_area_fraction_25km': 0.1256, 'n2k_nearest_distance_km': 1.399, 'n2k_max_conservation_score': 0.0, 'n2k_total_protected_area_ha': 129681.7}` | 100 |
|  | `wdpa_result_json` | `{'lat': 45.912791, 'lon': 22.826129, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'RO', 'country_iso3': 'ROU', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 82.65933989999999, 'overlap': False, 'site_id': 183982, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 4.17, 'name_english': 'Dealul Colț și Dealul Zănoaga', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 30.63478088, 'overlap': False, 'site_id': 11777, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 5.626, 'name_english': 'Dealul Cetății Deva', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 98.23970032, 'overlap': False, 'site_id': 11762, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.563, 'name_english': 'Pădurea Bejan', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.67426002, 'overlap': False, 'site_id': 183523, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.781, 'name_english': 'Boholt', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 250.58082581000002, 'overlap': False, 'site_id': 183505, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 11.962, 'name_english': 'Calcarele din Dealul Măgura', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 70.73947144, 'overlap': False, 'site_id': 183553, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 15.057, 'name_english': 'Arboretumul Simeria', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 46.491439820000004, 'overlap': False, 'site_id': 183503, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 17.474, 'name_english': 'Măgura Uroiului', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 57.74108887, 'overlap': False, 'site_id': 183472, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.957, 'name_english': 'Măgurile Săcărâmbului', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 67.81108093, 'overlap': False, 'site_id': 183530, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.62, 'name_english': 'Pădurea Chizid', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 40.18719101, 'overlap': False, 'site_id': 183522, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.02, 'name_english': 'Calcarele de la Boiul de Sus', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 18.57477951, 'overlap': False, 'site_id': 183511, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.06, 'name_english': 'Tufurile calcaroase din Valea Bobâlna', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 67.57208252, 'overlap': False, 'site_id': 183502, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.738, 'name_english': 'Calcarele de la Godinești', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 499.69607543999996, 'overlap': False, 'site_id': 183497, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.767, 'name_english': 'Codrii seculari de pe valea Dobrișoarei și Prisloapei', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 69.14456177, 'overlap': False, 'site_id': 183524, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.998, 'name_english': 'Apele mezotermale de la Geoagiu-Băi', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Dealul Colț și Dealul Zănoaga', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 82.65933989999999, 'wdpa_nearest_site_id': 183982, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 1, 'wdpa_area_fraction_5km': 0.0099, 'wdpa_iucn_ii_iii_count': 0, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 6, 'wdpa_sites_within_25km': 14, 'wdpa_area_fraction_16km': 0.0064, 'wdpa_area_fraction_25km': 0.0044, 'wdpa_iucn_iv_v_vi_count': 4, 'wdpa_nearest_designation': 'Not Assigned', 'wdpa_nearest_distance_km': 4.17, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'Not Assigned', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'IV', 'wdpa_total_protected_area_ha': 1400.75, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `171.09` | 100 |
| RI-03 | `aquifer_type` | `hard rocks` | 99 |
| RI-04 | `pop_density_5km` | `52.65` | 100 |
|  | `pop_density_16km` | `104.82` | 100 |
|  | `pop_density_25km` | `87.09` | 100 |
|  | `pop_density_80km` | `42.13` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.915` | 100 |
|  | `projected_pop_25km_60yr` | `131979` | 100 |

### Paroseni power station (RO, operating)

`site_id`: `9825e28e-fd6e-460d-9caf-0342563f9060`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.23` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `90.00` | 100 |
| BF-02 | `favourable_area_ha` | `87.56` | 100 |
|  | `buildable_area_ha` | `82.67` | 100 |
|  | `largest_contiguous_ha` | `82.67` | 98 |
|  | `site_area_ha` | `82.67` | 71 |
| EP-01 | `ep01_composite_score` | `44.2` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.190` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `True` | 100 |
|  | `waterway_count_epz` | `63` | 100 |
| EP-04 | `hospital_count_epz` | `15` | 100 |
|  | `prison_count_epz` | `0` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `40.67` | 100 |
|  | `nearest_airport_type` | `small_airport` | 100 |
|  | `nearest_airport_class` | `small_airport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `2.68` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `2.68` | 60 |
|  | `hi06_quality` | `high` | 100 |
|  | `flight_path_distance_km` | `20.33` | 100 |
|  | `hi01_comment` | `Nearest: Barza Târgu-Jiu Airfield (small_airport) at 40.7 km; Nearest large: 79.4 km; Nearest med...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `medium` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `medium` | 100 |
| HI-06 | `nearest_military_km` | `2.68` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `2.68` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `11` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.09991` | 100 |
|  | `nh01_pga_2475yr_g` | `0.24289` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `very_low` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `79.30` | 85 |
|  | `pga_475yr_g` | `0.09991` | 100 |
|  | `depth_to_bedrock_m` | `23.05` | 99 |
| NH-04 | `slope_angle_deg` | `12.90` | 98 |
|  | `slope_stability_class` | `steep` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `88.31` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `79.30` | 85 |
|  | `depth_to_bedrock_m` | `23.05` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `441.97` | 100 |
|  | `elevation_m` | `619.98` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `6.93` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `32.15` | 100 |
|  | `extreme_precip_mm` | `0.26` | 100 |
| NH-12 | `extreme_temp_max_c` | `21.15` | 100 |
|  | `extreme_temp_min_c` | `-7.05` | 100 |
| NS-01 | `cooling_source_type` | `small_river` | 100 |
|  | `cooling_source_name` | `Jiul de Vest` | 100 |
|  | `cooling_source_hyriv_id` | `20493847` | 100 |
|  | `cooling_distance_km` | `10.29` | 100 |
|  | `cooling_flow_m3s` | `0.54` | 100 |
|  | `water_stress_score` | `0.250` | 100 |
|  | `water_stress_label` | `Low-Medium` | 100 |
| NS-02 | `nearest_substation_km` | `0.23` | 100 |
|  | `nearest_hv_line_km` | `0.32` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `90.00` | 100 |
| NS-04 | `favourable_land_pct` | `28.50` | 100 |
|  | `favourable_area_ha` | `87.56` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `82.67` | 100 |
|  | `largest_contiguous_ha` | `82.67` | 98 |
|  | `patch_count` | `7` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `6.470` | 44 |
|  | `wdpa_nearest_distance_km` | `6.531` | 68 |
|  | `ecological_natural_pct` | `7.60` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `low` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 45.366101, 'lon': 23.261351, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'RO', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 86989.60649507323, 'overlap': False, 'sitecode': 'ROSAC0129', 'sitename': 'Nordul Gorjului de Vest', 'sitetype': 'B', 'distance_km': 6.47, 'direction_deg': 217.9, 'conservation_score': 0.36}, {'area_ha': 24981.787017063118, 'overlap': False, 'sitecode': 'ROSCI0236', 'sitename': 'Strei - Hațeg', 'sitetype': 'B', 'distance_km': 6.531, 'direction_deg': 303.9, 'conservation_score': 0.0}, {'area_ha': 10929.478321736737, 'overlap': False, 'sitecode': 'ROSCI0063', 'sitename': 'Defileul Jiului', 'sitetype': 'B', 'distance_km': 7.135, 'direction_deg': 139.5, 'conservation_score': 0.18181818181818182}, {'area_ha': 39864.75012228587, 'overlap': False, 'sitecode': 'ROSCI0087', 'sitename': 'Grădiștea Muncelului - Cioclovina', 'sitetype': 'B', 'distance_km': 8.457, 'direction_deg': 355.4, 'conservation_score': 0.15789473684210525}, {'area_ha': 38115.952905984406, 'overlap': False, 'sitecode': 'ROSPA0045', 'sitename': 'Grădiștea Muncelului - Ciclovina', 'sitetype': 'A', 'distance_km': 8.457, 'direction_deg': 354.4, 'conservation_score': None}, {'area_ha': 30298.658254978192, 'overlap': False, 'sitecode': 'ROSAC0188', 'sitename': 'Parâng', 'sitetype': 'B', 'distance_km': 10.913, 'direction_deg': 92.8, 'conservation_score': 0.05}, {'area_ha': 49214.407066964966, 'overlap': False, 'sitecode': 'ROSAC0128', 'sitename': 'Nordul Gorjului de Est', 'sitetype': 'B', 'distance_km': 15.958, 'direction_deg': 114.2, 'conservation_score': 0.38461538461538464}, {'area_ha': 43531.55853816967, 'overlap': False, 'sitecode': 'ROSCI0217', 'sitename': 'Retezat', 'sitetype': 'B', 'distance_km': 19.36, 'direction_deg': 263.8, 'conservation_score': 0.37037037037037035}, {'area_ha': 38319.01021809843, 'overlap': False, 'sitecode': 'ROSPA0084', 'sitename': 'Munții Retezat', 'sitetype': 'A', 'distance_km': 19.36, 'direction_deg': 265.0, 'conservation_score': None}, {'area_ha': 137306.2037974761, 'overlap': False, 'sitecode': 'ROSAC0085', 'sitename': 'Frumoasa', 'sitetype': 'B', 'distance_km': 25.789, 'direction_deg': 61.2, 'conservation_score': 0.09090909090909091}, {'area_ha': 130938.81558204207, 'overlap': False, 'sitecode': 'ROSPA0043', 'sitename': 'Frumoasa', 'sitetype': 'A', 'distance_km': 28.172, 'direction_deg': 61.8, 'conservation_score': None}], 'n2k_sac_count': 8, 'n2k_spa_count': 3, 'reference_date': '1726012800000', 'sensitivity_class': 'low', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 86989.60649507323, 'n2k_nearest_sitecode': 'ROSAC0129', 'n2k_nearest_sitename': 'Nordul Gorjului de Vest', 'n2k_nearest_sitetype': 'B', 'n2k_sites_within_5km': 0, 'n2k_area_fraction_5km': 0.0, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 7, 'n2k_sites_within_25km': 9, 'n2k_area_fraction_16km': 0.4546, 'n2k_area_fraction_25km': 0.572, 'n2k_nearest_distance_km': 6.47, 'n2k_max_conservation_score': 0.3846, 'n2k_total_protected_area_ha': 630490.23}` | 100 |
|  | `wdpa_result_json` | `{'lat': 45.366101, 'lon': 23.261351, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'RO', 'country_iso3': 'ROU', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 100062.6875, 'overlap': False, 'site_id': 196477, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.531, 'name_english': 'Geoparcul Dinozaurilor Țara Hațegului', 'iucn_category': 'V', 'designation_name': 'Natural park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 10978.8203125, 'overlap': False, 'site_id': 337831, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.135, 'name_english': 'Parcul Național Defileul Jiului', 'iucn_category': 'II', 'designation_name': 'National park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 38115.953125, 'overlap': False, 'site_id': 11181, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.457, 'name_english': 'Parcul Natural Grădiștea Muncelului - Cioclovina', 'iucn_category': 'V', 'designation_name': 'Natural park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 25.00226974, 'overlap': False, 'site_id': 183499, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 10.121, 'name_english': 'Dealul și Peștera Bolii', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 252.14840698, 'overlap': False, 'site_id': 183500, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 10.548, 'name_english': 'Cheile Crivadiei', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 2.8491098900000003, 'overlap': False, 'site_id': 183588, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 13.959, 'name_english': 'Sfinxul Lainicilor', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 577.99951172, 'overlap': False, 'site_id': 183558, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.872, 'name_english': 'Peștera Tecuri', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 38.843521120000005, 'overlap': False, 'site_id': 183525, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 15.482, 'name_english': 'Cheile Tăii', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.54360998, 'overlap': False, 'site_id': 183611, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 15.794, 'name_english': 'Stâncile Rafailă', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 379.64828491, 'overlap': False, 'site_id': 183504, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 16.391, 'name_english': 'Cheile Jiețului', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3799.07250977, 'overlap': False, 'site_id': 183554, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 16.783, 'name_english': 'Peștera Șura Mare', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 4.0604200399999995, 'overlap': False, 'site_id': 183592, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 17.153, 'name_english': 'Piatra Crinului', 'iucn_category': 'III', 'designation_name': 'Natural monument', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 38319.01171875, 'overlap': False, 'site_id': 861, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.36, 'name_english': 'Parcul Național Retezat', 'iucn_category': 'II', 'designation_name': 'National park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 8.34181976, 'overlap': False, 'site_id': 14577, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.752, 'name_english': 'Locul fosilifer Ohaba - Ponor', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.24795008, 'overlap': False, 'site_id': 183981, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.73, 'name_english': 'Fânațele Pui', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 2.7853600999999997, 'overlap': False, 'site_id': 183609, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.982, 'name_english': 'Dealul Gornăcelu', 'iucn_category': 'III', 'designation_name': 'Natural monument', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1571.0053710900002, 'overlap': False, 'site_id': 183987, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.283, 'name_english': 'Complexul carstic Ponorici - Cioclovina', 'iucn_category': 'Not Assigned', 'designation_name': 'Not Assigned', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 39.813301089999996, 'overlap': False, 'site_id': 349843, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.54, 'name_english': 'Cheile și Peștera Pătrunsa', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 630.37890625, 'overlap': False, 'site_id': 184121, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.675, 'name_english': 'Cheile Sohodolului', 'iucn_category': 'IV', 'designation_name': 'Nature reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Geoparcul Dinozaurilor Țara Hațegului', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 100062.6875, 'wdpa_nearest_site_id': 196477, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 0, 'wdpa_area_fraction_5km': 0.0, 'wdpa_iucn_ii_iii_count': 4, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 9, 'wdpa_sites_within_25km': 19, 'wdpa_area_fraction_16km': 0.2732, 'wdpa_area_fraction_25km': 0.3023, 'wdpa_iucn_iv_v_vi_count': 5, 'wdpa_nearest_designation': 'Natural park', 'wdpa_nearest_distance_km': 6.531, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'V', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'II', 'wdpa_total_protected_area_ha': 194812.21, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `0.54` | 100 |
| RI-03 | `aquifer_type` | `sedimentary sands` | 99 |
| RI-04 | `pop_density_5km` | `433.37` | 100 |
|  | `pop_density_16km` | `137.81` | 100 |
|  | `pop_density_25km` | `65.48` | 100 |
|  | `pop_density_80km` | `46.90` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.304` | 100 |
|  | `projected_pop_25km_60yr` | `99231` | 100 |

### Timelkam power station (AT, retired)

`site_id`: `2dcd2c6d-f375-4408-9492-7910662fac03`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.19` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `400.00` | 100 |
| BF-02 | `favourable_area_ha` | `150.39` | 100 |
|  | `buildable_area_ha` | `30.65` | 100 |
|  | `largest_contiguous_ha` | `30.65` | 98 |
|  | `site_area_ha` | `30.65` | 71 |
| EP-01 | `ep01_composite_score` | `60.9` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.760` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `True` | 100 |
|  | `waterway_count_epz` | `163` | 100 |
| EP-04 | `hospital_count_epz` | `13` | 100 |
|  | `prison_count_epz` | `1` | 100 |
|  | `care_home_count_epz` | `9` | 100 |
| HI-01 | `nearest_airport_km` | `21.75` | 100 |
|  | `nearest_airport_type` | `small_airport` | 100 |
|  | `nearest_airport_class` | `small_airport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `5.90` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `5.90` | 60 |
|  | `hi06_quality` | `medium` | 100 |
|  | `flight_path_distance_km` | `10.87` | 100 |
|  | `hi01_comment` | `Nearest: Gmunden-Laakirchen Airfield (small_airport) at 21.7 km; Nearest large: 50.0 km; Within 3...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `medium` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `medium` | 100 |
| HI-06 | `nearest_military_km` | `5.90` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `5.90` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `225` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.03604` | 100 |
|  | `nh01_pga_2475yr_g` | `0.06970` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `very_low` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `73.30` | 85 |
|  | `pga_475yr_g` | `0.03604` | 100 |
|  | `depth_to_bedrock_m` | `22.89` | 99 |
| NH-04 | `slope_angle_deg` | `10.21` | 98 |
|  | `slope_stability_class` | `steep` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `87.59` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `73.30` | 85 |
|  | `depth_to_bedrock_m` | `22.89` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `249.17` | 100 |
|  | `elevation_m` | `452.04` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `10.05` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `44.73` | 100 |
|  | `extreme_precip_mm` | `0.35` | 100 |
| NH-12 | `extreme_temp_max_c` | `21.35` | 100 |
|  | `extreme_temp_min_c` | `-4.92` | 100 |
| NS-01 | `cooling_source_type` | `small_river` | 100 |
|  | `cooling_source_name` | `Vöckla` | 100 |
|  | `cooling_source_hyriv_id` | `20425630` | 100 |
|  | `cooling_distance_km` | `0.11` | 100 |
|  | `cooling_flow_m3s` | `6.45` | 100 |
|  | `water_stress_score` | `0.028` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.19` | 100 |
|  | `nearest_hv_line_km` | `1.82` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `400.00` | 100 |
| NS-04 | `favourable_land_pct` | `57.60` | 100 |
|  | `favourable_area_ha` | `150.39` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `30.65` | 100 |
|  | `largest_contiguous_ha` | `30.65` | 98 |
|  | `patch_count` | `18` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `6.837` | 44 |
|  | `wdpa_nearest_distance_km` | `4.288` | 68 |
|  | `ecological_natural_pct` | `27.30` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `low` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 48.0122, 'lon': 13.5895, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'AT', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 6134.348919338343, 'overlap': False, 'sitecode': 'AT3117000', 'sitename': 'Mond- und Attersee', 'sitetype': 'B', 'distance_km': 6.837, 'direction_deg': 199.9, 'conservation_score': 0.5}, {'area_ha': 11.810469596297176, 'overlap': False, 'sitecode': 'AT3140000', 'sitename': 'Gerlhamer Moor', 'sitetype': 'B', 'distance_km': 6.898, 'direction_deg': 198.8, 'conservation_score': 0.0}, {'area_ha': 1263.4018096104298, 'overlap': False, 'sitecode': 'AT3123000', 'sitename': 'Wiesengebiete und Seen im Alpenvorland', 'sitetype': 'B', 'distance_km': 9.699, 'direction_deg': 275.0, 'conservation_score': 0.5333333333333333}, {'area_ha': 15.621867551505625, 'overlap': False, 'sitecode': 'AT3106000', 'sitename': 'Reinthaller Moos', 'sitetype': 'B', 'distance_km': 11.553, 'direction_deg': 204.6, 'conservation_score': 0.25}, {'area_ha': 2309.6443475115975, 'overlap': False, 'sitecode': 'AT3113000', 'sitename': 'Untere Traun', 'sitetype': 'A', 'distance_km': 15.014, 'direction_deg': 74.4, 'conservation_score': None}, {'area_ha': 1247.86468236038, 'overlap': False, 'sitecode': 'AT3139000', 'sitename': 'Unteres Traun- und Almtal', 'sitetype': 'B', 'distance_km': 15.037, 'direction_deg': 76.0, 'conservation_score': 0.3684210526315789}, {'area_ha': 4.155815360679214, 'overlap': False, 'sitecode': 'AT3142000', 'sitename': 'Egelsee und Egelseemoor', 'sitetype': 'B', 'distance_km': 20.782, 'direction_deg': 197.6, 'conservation_score': 1.0}, {'area_ha': 31.69196894101341, 'overlap': False, 'sitecode': 'AT3141000', 'sitename': 'Mooswiesen am Irrsee', 'sitetype': 'B', 'distance_km': 22.834, 'direction_deg': 242.4, 'conservation_score': 0.125}, {'area_ha': 728.113543756933, 'overlap': False, 'sitecode': 'AT3138000', 'sitename': 'Schluchtwälder der Steyr- und Ennstaler Voralpen', 'sitetype': 'B', 'distance_km': 23.901, 'direction_deg': 112.2, 'conservation_score': 0.0625}, {'area_ha': 4.291089044019106, 'overlap': False, 'sitecode': 'AT3135000', 'sitename': 'Quellflur bei Grueb', 'sitetype': 'B', 'distance_km': 26.297, 'direction_deg': 235.1, 'conservation_score': 0.0}], 'n2k_sac_count': 9, 'n2k_spa_count': 1, 'reference_date': '1733961600000', 'sensitivity_class': 'low', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 6134.348919338343, 'n2k_nearest_sitecode': 'AT3117000', 'n2k_nearest_sitename': 'Mond- und Attersee', 'n2k_nearest_sitetype': 'B', 'n2k_sites_within_5km': 0, 'n2k_area_fraction_5km': 0.0, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 6, 'n2k_sites_within_25km': 9, 'n2k_area_fraction_16km': 0.033, 'n2k_area_fraction_25km': 0.0299, 'n2k_nearest_distance_km': 6.837, 'n2k_max_conservation_score': 1.0, 'n2k_total_protected_area_ha': 11750.94}` | 100 |
|  | `wdpa_result_json` | `{'lat': 48.0122, 'lon': 13.5895, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'AT', 'country_iso3': 'AUT', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 3.35592008, 'overlap': False, 'site_id': 387336, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 4.288, 'name_english': 'Weyr-Welsern', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 2.10290003, 'overlap': False, 'site_id': 102731, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.007, 'name_english': 'Fasanenau', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 4.97529984, 'overlap': False, 'site_id': 102730, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.13, 'name_english': 'Schalchhamer Auwald', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 11.80333996, 'overlap': False, 'site_id': 103490, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.898, 'name_english': 'Gerlhamer Moor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 7677.453125, 'overlap': False, 'site_id': 555559233, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.183, 'name_english': 'Naturpark Attersee-Traunsee', 'iucn_category': 'V', 'designation_name': 'Nature Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 11.0, 'overlap': False, 'site_id': 555632986, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.341, 'name_english': 'Puchheimer Au', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.03618002, 'overlap': False, 'site_id': 387327, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 11.388, 'name_english': 'Grünberg in der Gemeinde Frankenburg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 10.52742004, 'overlap': False, 'site_id': 103491, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 11.528, 'name_english': 'Kreuzbauernmoor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 15.612250329999998, 'overlap': False, 'site_id': 103496, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 11.554, 'name_english': 'Reinthallermoos', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 4.14330006, 'overlap': False, 'site_id': 555513756, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 11.965, 'name_english': 'Hobelsberg-Riesn', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 2.3268699600000002, 'overlap': False, 'site_id': 103485, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 13.027, 'name_english': 'Aufhamer Uferwald', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 9684.0, 'overlap': False, 'site_id': 555737578, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.453, 'name_english': 'Naturpark Bauernland - Irrsee Mondsee Attersee', 'iucn_category': 'V', 'designation_name': 'Nature Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.46566999, 'overlap': False, 'site_id': 103461, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.456, 'name_english': 'Orter Bucht', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.79999995, 'overlap': False, 'site_id': 555737583, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.506, 'name_english': 'Nadasdy-Klause', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 5.1029501, 'overlap': False, 'site_id': 387355, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.864, 'name_english': 'Krottensee', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 8.50391006, 'overlap': False, 'site_id': 103463, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.944, 'name_english': 'Taferlklaussee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 10.14299965, 'overlap': False, 'site_id': 555513764, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.778, 'name_english': 'Hollereck', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.38917994, 'overlap': False, 'site_id': 103450, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.381, 'name_english': 'Gmöser Moor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 12.544980050000001, 'overlap': False, 'site_id': 103465, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.541, 'name_english': 'Hinterer Langbathsee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 34.588661189999996, 'overlap': False, 'site_id': 103464, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.551, 'name_english': 'Vorderer Langbathsee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.2852399300000004, 'overlap': False, 'site_id': 103489, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.783, 'name_english': 'Egelsee und Egelseemoor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.1145800399999999, 'overlap': False, 'site_id': 387342, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.633, 'name_english': 'Haslauer-Moos', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 15.931030269999999, 'overlap': False, 'site_id': 19051, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.865, 'name_english': 'Neydhartinger Moor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.15642001, 'overlap': False, 'site_id': 387322, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.909, 'name_english': 'Pfarrerhölzl', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.19001997, 'overlap': False, 'site_id': 169288, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.26, 'name_english': 'Goldberg-Feuchtbiotop', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 791.97546387, 'overlap': False, 'site_id': 555513740, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.279, 'name_english': 'Traunstein', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 17.775230410000002, 'overlap': False, 'site_id': 103497, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.489, 'name_english': 'Wildmoos', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 53.297279360000005, 'overlap': False, 'site_id': 387337, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.748, 'name_english': 'Irrsee-Moore', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 348.5413208, 'overlap': False, 'site_id': 103498, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.873, 'name_english': 'Zellersee (Irrsee)', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 4.78271008, 'overlap': False, 'site_id': 103486, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.454, 'name_english': 'Edelkastanienwald', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.45863998, 'overlap': False, 'site_id': 169116, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.827, 'name_english': 'Spießmoja (Spießmoller)', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 5623.97460938, 'overlap': False, 'site_id': 31406, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.325, 'name_english': 'Schafberg-Salzkammergutseen', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 25.89205933, 'overlap': False, 'site_id': 103456, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.342, 'name_english': 'Laudachsee und die Laudachmoore', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 100.85221863, 'overlap': False, 'site_id': 332706, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.612, 'name_english': 'Almauen', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Weyr-Welsern', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 3.35592008, 'wdpa_nearest_site_id': 387336, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 1, 'wdpa_area_fraction_5km': 0.0004, 'wdpa_iucn_ii_iii_count': 0, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 11, 'wdpa_sites_within_25km': 34, 'wdpa_area_fraction_16km': 0.0547, 'wdpa_area_fraction_25km': 0.0792, 'wdpa_iucn_iv_v_vi_count': 34, 'wdpa_nearest_designation': 'Landscape Protection Area', 'wdpa_nearest_distance_km': 4.288, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'V', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'IV', 'wdpa_total_protected_area_ha': 24498.1, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `6.45` | 100 |
| RI-03 | `aquifer_type` | `alluvial` | 99 |
| RI-04 | `pop_density_5km` | `246.45` | 100 |
|  | `pop_density_16km` | `149.38` | 100 |
|  | `pop_density_25km` | `125.68` | 100 |
|  | `pop_density_80km` | `127.71` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.174` | 100 |
|  | `projected_pop_25km_60yr` | `257843` | 100 |

### Braila power station (RO, retired)

`site_id`: `29836b52-a882-4921-95a7-6417e636d9a2`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.23` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `850.00` | 100 |
| BF-02 | `favourable_area_ha` | `179.76` | 100 |
|  | `buildable_area_ha` | `41.78` | 100 |
|  | `largest_contiguous_ha` | `41.78` | 98 |
|  | `site_area_ha` | `41.78` | 71 |
| EP-01 | `ep01_composite_score` | `65.3` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.294` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `21` | 100 |
|  | `prison_count_epz` | `1` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `22.17` | 100 |
|  | `nearest_airport_type` | `small_airport` | 100 |
|  | `nearest_airport_class` | `small_airport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `8.86` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `8.86` | 60 |
|  | `hi06_quality` | `medium` | 100 |
|  | `flight_path_distance_km` | `11.09` | 100 |
|  | `hi01_comment` | `Nearest: Aerial Club Vădeni (small_airport) at 22.2 km; Nearest large: 99.8 km; Nearest medium: 6...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `8.86` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `8.86` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `78` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.21219` | 100 |
|  | `nh01_pga_2475yr_g` | `0.36913` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `high` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `85.30` | 85 |
|  | `pga_475yr_g` | `0.21219` | 100 |
|  | `depth_to_bedrock_m` | `35.42` | 99 |
| NH-04 | `slope_angle_deg` | `1.56` | 98 |
|  | `slope_stability_class` | `flat` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `27.09` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `85.30` | 85 |
|  | `depth_to_bedrock_m` | `35.42` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `81.04` | 100 |
|  | `elevation_m` | `13.51` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `7.71` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `17.42` | 100 |
|  | `extreme_precip_mm` | `0.19` | 100 |
| NH-12 | `extreme_temp_max_c` | `27.68` | 100 |
|  | `extreme_temp_min_c` | `-5.80` | 100 |
| NS-01 | `cooling_source_type` | `major_river` | 100 |
|  | `cooling_source_name` | `Danube` | 100 |
|  | `cooling_source_hyriv_id` | `20500399` | 100 |
|  | `cooling_distance_km` | `1.65` | 100 |
|  | `cooling_flow_m3s` | `6237.30` | 100 |
|  | `water_stress_score` | `0.013` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.23` | 100 |
|  | `nearest_hv_line_km` | `2.53` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `850.00` | 100 |
| NS-04 | `favourable_land_pct` | `69.80` | 100 |
|  | `favourable_area_ha` | `179.76` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `41.78` | 100 |
|  | `largest_contiguous_ha` | `41.78` | 98 |
|  | `patch_count` | `6` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `1.166` | 44 |
|  | `wdpa_nearest_distance_km` | `1.275` | 68 |
|  | `ecological_natural_pct` | `21.60` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `moderate` | 100 |
|  | `wdpa_sensitivity_class` | `moderate` | 100 |
|  | `n2k_result_json` | `{'lat': 45.165033, 'lon': 27.923383, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'RO', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 25794.102833207842, 'overlap': False, 'sitecode': 'ROSPA0005', 'sitename': 'Balta Mică a Brăilei', 'sitetype': 'A', 'distance_km': 1.166, 'direction_deg': 184.3, 'conservation_score': None}, {'area_ha': 20659.15075630127, 'overlap': False, 'sitecode': 'ROSCI0006', 'sitename': 'Balta Mică a Brăilei', 'sitetype': 'B', 'distance_km': 1.275, 'direction_deg': 183.1, 'conservation_score': 0.0}, {'area_ha': 329.287136555521, 'overlap': False, 'sitecode': 'ROSCI0307', 'sitename': 'Lacul Sărat - Brăila', 'sitetype': 'B', 'distance_km': 3.693, 'direction_deg': 318.2, 'conservation_score': 0.0}, {'area_ha': 19004.136466759686, 'overlap': False, 'sitecode': 'ROSPA0040', 'sitename': 'Dunărea Veche - Brațul Măcin', 'sitetype': 'A', 'distance_km': 13.051, 'direction_deg': 151.4, 'conservation_score': None}, {'area_ha': 10429.31730253928, 'overlap': False, 'sitecode': 'ROSCI0012', 'sitename': 'Brațul Măcin', 'sitetype': 'B', 'distance_km': 13.051, 'direction_deg': 142.7, 'conservation_score': 0.125}, {'area_ha': 3234.159923821997, 'overlap': False, 'sitecode': 'ROSCI0305', 'sitename': 'Ianca - Plopu - Sărat - Comăneasca', 'sitetype': 'B', 'distance_km': 15.212, 'direction_deg': 280.1, 'conservation_score': 0.0}, {'area_ha': 2033.3419493879273, 'overlap': False, 'sitecode': 'ROSPA0048', 'sitename': 'Ianca - Plopu - Sărat', 'sitetype': 'A', 'distance_km': 18.324, 'direction_deg': 275.0, 'conservation_score': None}, {'area_ha': 67279.34586816204, 'overlap': False, 'sitecode': 'ROSPA0073', 'sitename': 'Măcin - Niculițel', 'sitetype': 'A', 'distance_km': 18.357, 'direction_deg': 88.0, 'conservation_score': None}, {'area_ha': 16919.460486195338, 'overlap': False, 'sitecode': 'ROSCI0123', 'sitename': 'Munții Măcinului', 'sitetype': 'B', 'distance_km': 20.823, 'direction_deg': 91.8, 'conservation_score': 0.2}, {'area_ha': 84825.30864687337, 'overlap': False, 'sitecode': 'ROSCI0201', 'sitename': 'Podișul Nord Dobrogean', 'sitetype': 'B', 'distance_km': 24.891, 'direction_deg': 118.2, 'conservation_score': 0.1111111111111111}, {'area_ha': 57875.82187531306, 'overlap': False, 'sitecode': 'ROSPA0091', 'sitename': 'Pădurea Babadag', 'sitetype': 'A', 'distance_km': 24.891, 'direction_deg': 122.4, 'conservation_score': None}, {'area_ha': 507824.6267183378, 'overlap': False, 'sitecode': 'ROSPA0031', 'sitename': 'Delta Dunării și Complexul Razim - Sinoie', 'sitetype': 'A', 'distance_km': 28.155, 'direction_deg': 98.1, 'conservation_score': None}, {'area_ha': 18125.124795956723, 'overlap': False, 'sitecode': 'ROSCI0259', 'sitename': 'Valea Călmățuiului', 'sitetype': 'B', 'distance_km': 32.393, 'direction_deg': 250.3, 'conservation_score': 0.5}, {'area_ha': 20861.251310914624, 'overlap': False, 'sitecode': 'ROSPA0145', 'sitename': 'Valea Călmățuiului', 'sitetype': 'A', 'distance_km': 32.393, 'direction_deg': 249.4, 'conservation_score': None}], 'n2k_sac_count': 7, 'n2k_spa_count': 7, 'reference_date': '1726012800000', 'sensitivity_class': 'moderate', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 25794.102833207842, 'n2k_nearest_sitecode': 'ROSPA0005', 'n2k_nearest_sitename': 'Balta Mică a Brăilei', 'n2k_nearest_sitetype': 'A', 'n2k_sites_within_5km': 3, 'n2k_area_fraction_5km': 0.3127, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 6, 'n2k_sites_within_25km': 11, 'n2k_area_fraction_16km': 0.1037, 'n2k_area_fraction_25km': 0.1514, 'n2k_nearest_distance_km': 1.166, 'n2k_max_conservation_score': 0.5, 'n2k_total_protected_area_ha': 855194.44}` | 100 |
|  | `wdpa_result_json` | `{'lat': 45.165033, 'lon': 27.923383, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'RO', 'country_iso3': 'ROU', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 20659.150390630002, 'overlap': False, 'site_id': 63626, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 1.275, 'name_english': 'Parcul Natural Balta Mică a Brăilei', 'iucn_category': 'V', 'designation_name': 'Natural park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 11242.31445313, 'overlap': False, 'site_id': 184172, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.203, 'name_english': 'Parcul Național Munții Macinului', 'iucn_category': 'II', 'designation_name': 'National park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'moderate', 'wdpa_nearest_name': 'Parcul Natural Balta Mică a Brăilei', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 20659.150390630002, 'wdpa_nearest_site_id': 63626, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 1, 'wdpa_area_fraction_5km': 0.2611, 'wdpa_iucn_ii_iii_count': 1, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 1, 'wdpa_sites_within_25km': 2, 'wdpa_area_fraction_16km': 0.0699, 'wdpa_area_fraction_25km': 0.0473, 'wdpa_iucn_iv_v_vi_count': 1, 'wdpa_nearest_designation': 'Natural park', 'wdpa_nearest_distance_km': 1.275, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'V', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'II', 'wdpa_total_protected_area_ha': 31901.46, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `6237.30` | 100 |
| RI-03 | `aquifer_type` | `inland water` | 99 |
| RI-04 | `pop_density_5km` | `118.36` | 100 |
|  | `pop_density_16km` | `237.74` | 100 |
|  | `pop_density_25km` | `120.95` | 100 |
|  | `pop_density_80km` | `67.83` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.233` | 100 |
|  | `projected_pop_25km_60yr` | `183292` | 100 |

### Riedersbach power station (AT, retired)

`site_id`: `660d9d71-6733-4294-951b-1c58614d58cf`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.23` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `220.00` | 100 |
| BF-02 | `favourable_area_ha` | `90.15` | 100 |
|  | `buildable_area_ha` | `12.76` | 100 |
|  | `largest_contiguous_ha` | `12.76` | 98 |
|  | `site_area_ha` | `12.76` | 71 |
| EP-01 | `ep01_composite_score` | `55.6` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.740` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `17` | 100 |
|  | `prison_count_epz` | `3` | 100 |
|  | `care_home_count_epz` | `2` | 100 |
| HI-01 | `nearest_airport_km` | `15.06` | 100 |
|  | `nearest_airport_type` | `heliport` | 100 |
|  | `nearest_airport_class` | `heliport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `19.00` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `19.00` | 60 |
|  | `hi06_quality` | `medium` | 100 |
|  | `flight_path_distance_km` | `12.51` | 100 |
|  | `hi01_comment` | `Nearest: Altötting-Burghausen District Hospital Burghausen Heliport (heliport) at 15.1 km; Neares...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `19.00` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `19.00` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `166` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.03439` | 100 |
|  | `nh01_pga_2475yr_g` | `0.06739` | 96 |
| NH-02 | `nearest_fault_km` | `31.20` | 100 |
|  | `fault_name` | `ATCF007` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.707` | 100 |
| NH-03 | `liquefaction_suscept` | `high` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `80.70` | 85 |
|  | `pga_475yr_g` | `0.03439` | 100 |
|  | `depth_to_bedrock_m` | `20.51` | 99 |
| NH-04 | `slope_angle_deg` | `11.16` | 98 |
|  | `slope_stability_class` | `steep` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `87.27` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `80.70` | 85 |
|  | `depth_to_bedrock_m` | `20.51` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `252.80` | 100 |
|  | `elevation_m` | `403.59` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `8.74` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `44.24` | 100 |
|  | `extreme_precip_mm` | `0.34` | 100 |
| NH-12 | `extreme_temp_max_c` | `21.78` | 100 |
|  | `extreme_temp_min_c` | `-5.04` | 100 |
| NS-01 | `cooling_source_type` | `major_river` | 100 |
|  | `cooling_source_name` | `Redlbach` | 100 |
|  | `cooling_source_hyriv_id` | `20425304` | 100 |
|  | `cooling_distance_km` | `0.58` | 100 |
|  | `cooling_flow_m3s` | `156.18` | 100 |
|  | `water_stress_score` | `0.038` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.23` | 100 |
|  | `nearest_hv_line_km` | `6.11` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `220.00` | 100 |
| NS-04 | `favourable_land_pct` | `50.50` | 100 |
|  | `favourable_area_ha` | `90.15` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `12.76` | 100 |
|  | `largest_contiguous_ha` | `12.76` | 98 |
|  | `patch_count` | `17` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `0.293` | 44 |
|  | `wdpa_nearest_distance_km` | `2.973` | 68 |
|  | `ecological_natural_pct` | `31.10` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `high` | 100 |
|  | `wdpa_sensitivity_class` | `moderate` | 100 |
|  | `n2k_result_json` | `{'lat': 48.031769, 'lon': 12.843122, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'AT', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 336.99214330150664, 'overlap': False, 'sitecode': 'AT3118000', 'sitename': 'Salzachauen', 'sitetype': 'B', 'distance_km': 0.293, 'direction_deg': 189.0, 'conservation_score': 0.0}, {'area_ha': 4838.861123244342, 'overlap': False, 'sitecode': 'DE7744471', 'sitename': 'Salzach und Inn', 'sitetype': 'A', 'distance_km': 0.763, 'direction_deg': 37.4, 'conservation_score': None}, {'area_ha': 5833.858101918441, 'overlap': False, 'sitecode': 'DE7744371', 'sitename': 'Salzach und Unterer Inn', 'sitetype': 'B', 'distance_km': 0.766, 'direction_deg': 41.2, 'conservation_score': 0.0}, {'area_ha': 625.0951971645544, 'overlap': False, 'sitecode': 'AT3110000', 'sitename': 'Ettenau', 'sitetype': 'C', 'distance_km': 2.973, 'direction_deg': 319.5, 'conservation_score': 0.0}, {'area_ha': 740.4465440910658, 'overlap': False, 'sitecode': 'AT3223000', 'sitename': 'Salzachauen, Salzburg', 'sitetype': 'B', 'distance_km': 4.112, 'direction_deg': 146.8, 'conservation_score': 0.0}, {'area_ha': 1119.9623738998255, 'overlap': False, 'sitecode': 'AT3209022', 'sitename': 'Salzachauen, Salzburg', 'sitetype': 'A', 'distance_km': 4.112, 'direction_deg': 147.2, 'conservation_score': None}, {'area_ha': 1263.4018096104298, 'overlap': False, 'sitecode': 'AT3123000', 'sitename': 'Wiesengebiete und Seen im Alpenvorland', 'sitetype': 'B', 'distance_km': 4.44, 'direction_deg': 85.6, 'conservation_score': 0.5333333333333333}, {'area_ha': 0.06551646877340911, 'overlap': False, 'sitecode': 'AT3233000', 'sitename': 'Pfarrkirche St. Georgen bei Salzburg', 'sitetype': 'B', 'distance_km': 4.966, 'direction_deg': 146.9, 'conservation_score': None}, {'area_ha': 57.75385521298596, 'overlap': False, 'sitecode': 'AT3228000', 'sitename': 'Bürmooser Moor', 'sitetype': 'C', 'distance_km': 6.476, 'direction_deg': 121.3, 'conservation_score': 0.0}, {'area_ha': 140.56190276409473, 'overlap': False, 'sitecode': 'AT3225000', 'sitename': 'Weidmoos', 'sitetype': 'A', 'distance_km': 6.692, 'direction_deg': 91.9, 'conservation_score': None}, {'area_ha': 153.51006932552707, 'overlap': False, 'sitecode': 'AT3102000', 'sitename': 'Frankinger Moos', 'sitetype': 'A', 'distance_km': 7.013, 'direction_deg': 69.9, 'conservation_score': None}, {'area_ha': 151.91405917458675, 'overlap': False, 'sitecode': 'AT3103000', 'sitename': 'Pfeiferanger', 'sitetype': 'A', 'distance_km': 8.578, 'direction_deg': 73.0, 'conservation_score': None}, {'area_ha': 0.06996680506574318, 'overlap': False, 'sitecode': 'DE7841371', 'sitename': 'Wochenstuben der Wimperfledermaus im Chiemgau', 'sitetype': 'B', 'distance_km': 8.772, 'direction_deg': 257.7, 'conservation_score': None}, {'area_ha': 183.3985414811886, 'overlap': False, 'sitecode': 'DE8143371', 'sitename': 'Uferbereiche des Waginger Sees, Götzinger Achen und untere Sur', 'sitetype': 'B', 'distance_km': 9.125, 'direction_deg': 176.8, 'conservation_score': 0.0}, {'area_ha': 2.73432328149425, 'overlap': False, 'sitecode': 'DE7942301', 'sitename': 'Heigermoos', 'sitetype': 'B', 'distance_km': 12.159, 'direction_deg': 274.1, 'conservation_score': 0.0}, {'area_ha': 1288.8138964873433, 'overlap': False, 'sitecode': 'DE8142371', 'sitename': 'Moore im Salzach-Hügelland', 'sitetype': 'B', 'distance_km': 12.793, 'direction_deg': 195.5, 'conservation_score': 0.18181818181818182}, {'area_ha': 4.871910689393742, 'overlap': False, 'sitecode': 'AT3152000', 'sitename': 'Kalktuffquelle Wanghausen', 'sitetype': 'B', 'distance_km': 12.955, 'direction_deg': 346.8, 'conservation_score': 0.5}, {'area_ha': 284.0780212892683, 'overlap': False, 'sitecode': 'DE8043371', 'sitename': 'Haarmoos', 'sitetype': 'C', 'distance_km': 13.26, 'direction_deg': 164.7, 'conservation_score': 0.0}, {'area_ha': 111.88755861380382, 'overlap': False, 'sitecode': 'DE7842371', 'sitename': 'Kammmolch-Habitate in den Landkreisen Mühldorf und Altötting', 'sitetype': 'B', 'distance_km': 14.067, 'direction_deg': 314.5, 'conservation_score': 0.0}, {'area_ha': 106.60416705089844, 'overlap': False, 'sitecode': 'AT3202006', 'sitename': 'Oichtenriede', 'sitetype': 'A', 'distance_km': 14.531, 'direction_deg': 94.9, 'conservation_score': None}, {'area_ha': 0.06999555602284557, 'overlap': False, 'sitecode': 'DE7839371', 'sitename': 'Mausohrkolonien im Unterbayerischen Hügelland', 'sitetype': 'B', 'distance_km': 18.649, 'direction_deg': 310.4, 'conservation_score': None}, {'area_ha': 1571.370189861091, 'overlap': False, 'sitecode': 'DE7742371', 'sitename': 'Inn und Untere Alz', 'sitetype': 'B', 'distance_km': 18.675, 'direction_deg': 349.3, 'conservation_score': 0.13333333333333333}, {'area_ha': 46.313319657247774, 'overlap': False, 'sitecode': 'AT3247000', 'sitename': 'Fraham-Aag-Zellhof', 'sitetype': 'B', 'distance_km': 18.746, 'direction_deg': 108.0, 'conservation_score': None}, {'area_ha': 877.7257897305134, 'overlap': False, 'sitecode': 'DE8142372', 'sitename': 'Oberes Surtal und Urstromtal Höglwörth', 'sitetype': 'B', 'distance_km': 19.502, 'direction_deg': 201.8, 'conservation_score': 0.09090909090909091}, {'area_ha': 103.57322533145145, 'overlap': False, 'sitecode': 'DE8041371', 'sitename': 'Standortübungsplatz Traunstein', 'sitetype': 'B', 'distance_km': 20.127, 'direction_deg': 227.0, 'conservation_score': 0.0}, {'area_ha': 0.01000160996439476, 'overlap': False, 'sitecode': 'DE8041301', 'sitename': 'Winterquartier der Mopsfledermaus in Burg Stein', 'sitetype': 'B', 'distance_km': 22.615, 'direction_deg': 257.6, 'conservation_score': None}, {'area_ha': 3.652502325317655, 'overlap': False, 'sitecode': 'AT3229000', 'sitename': 'Nordmoor am Mattsee', 'sitetype': 'B', 'distance_km': 23.168, 'direction_deg': 100.6, 'conservation_score': 0.0}, {'area_ha': 443.2067361200004, 'overlap': False, 'sitecode': 'DE8041302', 'sitename': 'Alz vom Chiemsee bis Altenmarkt', 'sitetype': 'B', 'distance_km': 23.459, 'direction_deg': 253.6, 'conservation_score': 0.0}, {'area_ha': 10376.07557147313, 'overlap': False, 'sitecode': 'DE8140471', 'sitename': 'Chiemseegebiet mit Alz', 'sitetype': 'A', 'distance_km': 23.459, 'direction_deg': 239.4, 'conservation_score': None}, {'area_ha': 123.41348582375349, 'overlap': False, 'sitecode': 'DE7741371', 'sitename': 'Grünbach und Bucher Moor', 'sitetype': 'B', 'distance_km': 24.721, 'direction_deg': 310.7, 'conservation_score': 0.0}, {'area_ha': 147.33288320168182, 'overlap': False, 'sitecode': 'DE7743301', 'sitename': 'Innleite von Buch bis Simbach', 'sitetype': 'B', 'distance_km': 25.506, 'direction_deg': 18.9, 'conservation_score': 0.0}, {'area_ha': 298.45989185659084, 'overlap': False, 'sitecode': 'AT3201014', 'sitename': 'Wallersee-Wengermoor', 'sitetype': 'C', 'distance_km': 26.65, 'direction_deg': 114.5, 'conservation_score': 0.5714285714285714}, {'area_ha': 8141.130572933495, 'overlap': False, 'sitecode': 'DE8140372', 'sitename': 'Chiemsee', 'sitetype': 'B', 'distance_km': 27.931, 'direction_deg': 240.0, 'conservation_score': 0.15384615384615385}, {'area_ha': 49.87894985685351, 'overlap': False, 'sitecode': 'DE8141301', 'sitename': "Hangquellmoor 'Ewige Sau'", 'sitetype': 'B', 'distance_km': 28.064, 'direction_deg': 229.3, 'conservation_score': 0.0}, {'area_ha': 3571.3732032038165, 'overlap': False, 'sitecode': 'DE8140371', 'sitename': 'Moore südlich des Chiemsees', 'sitetype': 'B', 'distance_km': 29.797, 'direction_deg': 228.7, 'conservation_score': 0.5294117647058824}, {'area_ha': 2720.0698950062215, 'overlap': False, 'sitecode': 'DE8141471', 'sitename': 'Moore südlich  des Chiemsees', 'sitetype': 'A', 'distance_km': 31.612, 'direction_deg': 228.2, 'conservation_score': None}, {'area_ha': 3521.720694663969, 'overlap': False, 'sitecode': 'DE7939301', 'sitename': 'Innauen und Leitenwälder', 'sitetype': 'B', 'distance_km': 32.174, 'direction_deg': 277.1, 'conservation_score': 0.07692307692307693}], 'n2k_sac_count': 29, 'n2k_spa_count': 12, 'reference_date': '1733961600000', 'sensitivity_class': 'high', 'n2k_combined_count': 4, 'n2k_nearest_area_ha': 336.99214330150664, 'n2k_nearest_sitecode': 'AT3118000', 'n2k_nearest_sitename': 'Salzachauen', 'n2k_nearest_sitetype': 'B', 'n2k_sites_within_5km': 8, 'n2k_area_fraction_5km': 0.1448, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 20, 'n2k_sites_within_25km': 30, 'n2k_area_fraction_16km': 0.0644, 'n2k_area_fraction_25km': 0.0528, 'n2k_nearest_distance_km': 0.293, 'n2k_max_conservation_score': 0.5714, 'n2k_total_protected_area_ha': 49240.26}` | 100 |
|  | `wdpa_result_json` | `{'lat': 48.031769, 'lon': 12.843122, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'AT', 'country_iso3': 'AUT', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 538.68591309, 'overlap': False, 'site_id': 387350, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 2.973, 'name_english': 'Ettenau', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 19.79244041, 'overlap': False, 'site_id': 103439, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 3.383, 'name_english': 'Höllerersee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 86.11083984, 'overlap': False, 'site_id': 555545116, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 3.434, 'name_english': 'Ettenau II', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 167.04377747, 'overlap': False, 'site_id': 102703, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 4.111, 'name_english': 'Irlacher Au', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 11.90999985, 'overlap': False, 'site_id': 103440, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 4.879, 'name_english': 'Teile des Hehermooses und der Holzöstersee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.60651004, 'overlap': False, 'site_id': 169340, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.378, 'name_english': 'Lilienwiese in St.Georgen', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 57.71977997, 'overlap': False, 'site_id': 555545123, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.476, 'name_english': 'Bürmooser Moor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 140.48077393, 'overlap': False, 'site_id': 387363, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.691, 'name_english': 'Weidmoos', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 35.32093048, 'overlap': False, 'site_id': 169153, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.02, 'name_english': 'Frankinger Moos', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 65.91716766, 'overlap': False, 'site_id': 103441, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.578, 'name_english': 'Seeleithensee und angrenzende Streuwiesen', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 85.92391205, 'overlap': False, 'site_id': 103444, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.702, 'name_english': 'Pfeiferanger', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 23.7005291, 'overlap': False, 'site_id': 103438, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.792, 'name_english': 'Heratingersee in Eggelsberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.0052899999999999996, 'overlap': False, 'site_id': 169526, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.148, 'name_english': 'Linde am Bahnhof Lamprechtshausen', 'iucn_category': 'III', 'designation_name': 'Protected Natural Objects of local importance', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.30156004, 'overlap': False, 'site_id': 169397, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.222, 'name_english': 'Orchideen-Streuwiese Knotzing/Lamprechtshausen', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.5078200099999999, 'overlap': False, 'site_id': 103443, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.62, 'name_english': 'Jackenmoos auf dem Mühlberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.14171999999999998, 'overlap': False, 'site_id': 169470, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 12.981, 'name_english': 'Tümpel bei Lindach', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.011519999999999999, 'overlap': False, 'site_id': 555640725, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.357, 'name_english': 'Eiche auf GP 2371/1, Nußdorf', 'iucn_category': 'III', 'designation_name': 'Protected Natural Objects of local importance', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 103.70305634000002, 'overlap': False, 'site_id': 103427, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.605, 'name_english': 'Oichten-Riede', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1.0618, 'overlap': False, 'site_id': 169502, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 16.282, 'name_english': 'Weitwörther Allee', 'iucn_category': 'III', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1473.3515625, 'overlap': False, 'site_id': 32548, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 17.965, 'name_english': 'Trumer Seen', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.15136001, 'overlap': False, 'site_id': 169262, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.401, 'name_english': 'Feuchtbiotop Unseld in Seeham', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 410.36584473, 'overlap': False, 'site_id': 5447, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 18.425, 'name_english': 'Trumerseen', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 869.9999999999999, 'overlap': False, 'site_id': 67804, 'is_ramsar': True, 'is_emerald': False, 'distance_km': 18.732, 'name_english': 'Stauseen am Unteren Inn', 'iucn_category': 'Not Reported', 'designation_name': 'Wetland of International Importance (Ramsar Site)', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'International'}, {'area_ha': 20.7616291, 'overlap': False, 'site_id': 387332, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.232, 'name_english': 'Nordmoor am Grabensee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 985.97717285, 'overlap': False, 'site_id': 103445, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.362, 'name_english': 'Unterer Inn', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.19287992, 'overlap': False, 'site_id': 169477, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.658, 'name_english': 'Tümpel in Pernerstätt', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 50.390060420000005, 'overlap': False, 'site_id': 5452, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.851, 'name_english': 'Obertrumer See', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 34.042339319999996, 'overlap': False, 'site_id': 555513750, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.245, 'name_english': 'Naturpark Buchberg', 'iucn_category': 'IV', 'designation_name': 'Nature Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 34.042339319999996, 'overlap': False, 'site_id': 555545118, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.245, 'name_english': 'Buchberg', 'iucn_category': 'V', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 5.78961992, 'overlap': False, 'site_id': 555513745, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.746, 'name_english': 'Imsee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 102.2318573, 'overlap': False, 'site_id': 5448, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.976, 'name_english': 'Egelseen', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 115.33779906999999, 'overlap': False, 'site_id': 102701, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.199, 'name_english': 'Lugingersee', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 17.19142914, 'overlap': False, 'site_id': 37113, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.814, 'name_english': 'Ursprunger Moor', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 0.05069, 'overlap': False, 'site_id': 169472, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.863, 'name_english': 'Tümpel bei Wendling', 'iucn_category': 'IV', 'designation_name': 'Protected Landscape Section', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 184.2830658, 'overlap': False, 'site_id': 102695, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.161, 'name_english': 'Salzachsee-Saalachspitz', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3.6503400800000003, 'overlap': False, 'site_id': 555545122, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.168, 'name_english': 'Nordmoor am Mattsee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 6.33176994, 'overlap': False, 'site_id': 555513776, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.207, 'name_english': 'Nordmoor am Mattsee', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 15.0, 'overlap': False, 'site_id': 555632985, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.245, 'name_english': 'Teile der Innauen bei Braunau', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 6.0, 'overlap': False, 'site_id': 555632984, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.946, 'name_english': 'Ascherweiher und seine Umgebung', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 146.10108948, 'overlap': False, 'site_id': 102702, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.953, 'name_english': 'Siezenheimer-Au', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'moderate', 'wdpa_nearest_name': 'Ettenau', 'wdpa_ramsar_count': 1, 'wdpa_nearest_area_ha': 538.68591309, 'wdpa_nearest_site_id': 387350, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 5, 'wdpa_area_fraction_5km': 0.0198, 'wdpa_iucn_ii_iii_count': 3, 'wdpa_ramsar_nearest_km': 18.732, 'wdpa_sites_within_16km': 18, 'wdpa_sites_within_25km': 40, 'wdpa_area_fraction_16km': 0.0167, 'wdpa_area_fraction_25km': 0.0202, 'wdpa_iucn_iv_v_vi_count': 36, 'wdpa_nearest_designation': 'Nature Reserve', 'wdpa_nearest_distance_km': 2.973, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'IV', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'III', 'wdpa_total_protected_area_ha': 5826.19, 'wdpa_international_designation_count': 1}` | 100 |
| RI-02 | `cooling_flow_m3s` | `156.18` | 100 |
| RI-03 | `aquifer_type` | `low permeability` | 99 |
| RI-04 | `pop_density_5km` | `145.57` | 100 |
|  | `pop_density_16km` | `110.82` | 100 |
|  | `pop_density_25km` | `153.35` | 100 |
|  | `pop_density_80km` | `134.57` | 100 |
| RI-06 | `pop_growth_rate_pct` | `0.054` | 100 |
|  | `projected_pop_25km_60yr` | `314610` | 100 |

### Kozienice power station (PL, operating)

`site_id`: `4411a22e-4e8a-4715-b000-1aae34494b68`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.04` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `5772.00` | 100 |
| BF-02 | `favourable_area_ha` | `15.45` | 100 |
|  | `buildable_area_ha` | `20.61` | 100 |
|  | `largest_contiguous_ha` | `187.47` | 98 |
|  | `site_area_ha` | `8.76` | 71 |
| EP-01 | `ep01_composite_score` | `42.9` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.458` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `True` | 100 |
|  | `waterway_count_epz` | `290` | 100 |
| EP-04 | `hospital_count_epz` | `10` | 100 |
|  | `prison_count_epz` | `2` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `24.08` | 100 |
|  | `nearest_airport_type` | `medium_airport` | 100 |
|  | `nearest_airport_class` | `medium_airport` | 100 |
|  | `nearest_military_class` | `other` | 90 |
|  | `nearest_military_km` | `15.46` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `20.80` | 60 |
|  | `hi06_quality` | `medium` | 100 |
|  | `flight_path_distance_km` | `12.04` | 100 |
|  | `hi01_comment` | `Nearest: Deblin Military Air Base (medium_airport) at 24.1 km; Nearest large: 76.1 km; Nearest me...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `15.46` | 90 |
|  | `nearest_military_class` | `other` | 90 |
|  | `nearest_high_consequence_military_km` | `20.80` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `80` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.01880` | 100 |
|  | `nh01_pga_2475yr_g` | `0.07084` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `moderate` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `110.00` | 85 |
|  | `pga_475yr_g` | `0.01880` | 100 |
|  | `depth_to_bedrock_m` | `29.98` | 99 |
| NH-04 | `slope_angle_deg` | `3.35` | 98 |
|  | `slope_stability_class` | `gentle` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `76.24` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `110.00` | 85 |
|  | `depth_to_bedrock_m` | `29.98` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `343.45` | 100 |
|  | `elevation_m` | `116.39` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `10.19` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `23.05` | 100 |
|  | `extreme_precip_mm` | `0.29` | 100 |
| NH-12 | `extreme_temp_max_c` | `22.85` | 100 |
|  | `extreme_temp_min_c` | `-8.38` | 100 |
| NS-01 | `cooling_source_type` | `major_river` | 100 |
|  | `cooling_source_name` | `Zagożdżonka` | 100 |
|  | `cooling_source_hyriv_id` | `20332507` | 100 |
|  | `cooling_distance_km` | `5.65` | 100 |
|  | `cooling_flow_m3s` | `502.35` | 100 |
|  | `water_stress_score` | `0.017` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.04` | 100 |
|  | `nearest_hv_line_km` | `5.08` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `5772.00` | 100 |
| NS-04 | `favourable_land_pct` | `75.40` | 100 |
|  | `favourable_area_ha` | `15.45` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `20.61` | 100 |
|  | `largest_contiguous_ha` | `187.47` | 98 |
|  | `patch_count` | `8` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `0.308` | 44 |
|  | `wdpa_nearest_distance_km` | `2.299` | 68 |
|  | `ecological_natural_pct` | `21.30` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `high` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 51.58293, 'lon': 21.54779, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'PL', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 68347.80842841431, 'overlap': False, 'sitecode': 'PLB140013', 'sitename': 'Ostoja Kozienicka', 'sitetype': 'A', 'distance_km': 0.308, 'direction_deg': 215.7, 'conservation_score': None}, {'area_ha': 28249.684540179453, 'overlap': False, 'sitecode': 'PLH140035', 'sitename': 'Puszcza Kozienicka', 'sitetype': 'B', 'distance_km': 3.264, 'direction_deg': 213.7, 'conservation_score': 0.4117647058823529}, {'area_ha': 30806.06051697608, 'overlap': False, 'sitecode': 'PLB140004', 'sitename': 'Dolina Środkowej Wisły', 'sitetype': 'A', 'distance_km': 4.659, 'direction_deg': 322.3, 'conservation_score': None}, {'area_ha': 921.9950455805233, 'overlap': False, 'sitecode': 'PLH140023', 'sitename': 'Bagna Orońskie', 'sitetype': 'B', 'distance_km': 10.252, 'direction_deg': 24.0, 'conservation_score': 0.14285714285714285}, {'area_ha': 1276.4505867369946, 'overlap': False, 'sitecode': 'PLH140033', 'sitename': 'Podebłocie', 'sitetype': 'B', 'distance_km': 10.841, 'direction_deg': 67.1, 'conservation_score': 0.0}, {'area_ha': 1579.2387907035793, 'overlap': False, 'sitecode': 'PLH140030', 'sitename': 'Łękawica', 'sitetype': 'B', 'distance_km': 17.324, 'direction_deg': 317.4, 'conservation_score': 0.0}, {'area_ha': 31853.84706779897, 'overlap': False, 'sitecode': 'PLH140016', 'sitename': 'Dolina Dolnej Pilicy', 'sitetype': 'B', 'distance_km': 28.104, 'direction_deg': 278.8, 'conservation_score': 0.5}, {'area_ha': 35391.780448327896, 'overlap': False, 'sitecode': 'PLB140003', 'sitename': 'Dolina Pilicy', 'sitetype': 'A', 'distance_km': 28.104, 'direction_deg': 279.2, 'conservation_score': None}], 'n2k_sac_count': 5, 'n2k_spa_count': 3, 'reference_date': '1738022400000', 'sensitivity_class': 'high', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': 68347.80842841431, 'n2k_nearest_sitecode': 'PLB140013', 'n2k_nearest_sitename': 'Ostoja Kozienicka', 'n2k_nearest_sitetype': 'A', 'n2k_sites_within_5km': 3, 'n2k_area_fraction_5km': 0.7972, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 5, 'n2k_sites_within_25km': 6, 'n2k_area_fraction_16km': 0.6326, 'n2k_area_fraction_25km': 0.4033, 'n2k_nearest_distance_km': 0.308, 'n2k_max_conservation_score': 0.5, 'n2k_total_protected_area_ha': 198426.87}` | 100 |
|  | `wdpa_result_json` | `{'lat': 51.58293, 'lon': 21.54779, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'PL', 'country_iso3': 'POL', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 25920.73242187, 'overlap': False, 'site_id': 148557, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 2.299, 'name_english': 'Kozienicki Park Krajobrazowy', 'iucn_category': 'V', 'designation_name': 'Landscape Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 69862.2578125, 'overlap': False, 'site_id': 177680, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 5.334, 'name_english': 'Nadwiślański (powiat garwoliński, miński i otwocki)', 'iucn_category': 'Not Assigned', 'designation_name': 'Protected Landscape Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 29.331699369999995, 'overlap': False, 'site_id': 177653, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.187, 'name_english': 'Źródło Królewskie', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 87.04940033, 'overlap': False, 'site_id': 396177, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.083, 'name_english': 'Guść', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 121.95639801, 'overlap': False, 'site_id': 115257, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.853, 'name_english': 'Brzeźniczka', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 273.92370604999996, 'overlap': False, 'site_id': 177426, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 8.564, 'name_english': 'Krępiec', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 65.17009735, 'overlap': False, 'site_id': 145350, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 9.182, 'name_english': 'Zagożdżon', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 12.63339996, 'overlap': False, 'site_id': 145232, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 12.857, 'name_english': 'Torfy Orońskie', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 77.88130188, 'overlap': False, 'site_id': 145352, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 12.913, 'name_english': 'Załamanek', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 50.59780121000001, 'overlap': False, 'site_id': 177526, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 13.052, 'name_english': 'Ponty Dęby', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 81.853302, 'overlap': False, 'site_id': 124035, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 13.156, 'name_english': 'Pionki', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 36.51229858, 'overlap': False, 'site_id': 124054, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 13.526, 'name_english': 'Ponty im. Teodora Zielińskiego', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 17.07449913, 'overlap': False, 'site_id': 396200, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.959, 'name_english': 'Dęby Biesiadne im. Mariana Pulkowskiego', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 23.738899229999998, 'overlap': False, 'site_id': 177456, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 16.032, 'name_english': 'Leniwa', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 168.97650146, 'overlap': False, 'site_id': 177498, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 16.504, 'name_english': 'Okólny Ług', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 6.02619982, 'overlap': False, 'site_id': 115953, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 17.731, 'name_english': 'Kopiec Kościuszki', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 39.57130051, 'overlap': False, 'site_id': 115318, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.122, 'name_english': 'Ciszek', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 58.539100649999995, 'overlap': False, 'site_id': 115337, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.164, 'name_english': 'Czerwony Krzyż', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 33522.85546875, 'overlap': False, 'site_id': 115125, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.917, 'name_english': 'Pradolina Wieprza', 'iucn_category': 'Not Assigned', 'designation_name': 'Protected Landscape Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 28.97940063, 'overlap': False, 'site_id': 122888, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.975, 'name_english': 'Olszyny', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 86.70279694, 'overlap': False, 'site_id': 115836, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.388, 'name_english': 'Jedlnia im. Andrzeja Kowalczewskiego', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 94.00720215, 'overlap': False, 'site_id': 116180, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.776, 'name_english': 'Ługi Helenowskie', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 19.969900130000003, 'overlap': False, 'site_id': 122841, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.817, 'name_english': 'Miodne', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Kozienicki Park Krajobrazowy', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 25920.73242187, 'wdpa_nearest_site_id': 148557, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 1, 'wdpa_area_fraction_5km': 0.0919, 'wdpa_iucn_ii_iii_count': 0, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 13, 'wdpa_sites_within_25km': 23, 'wdpa_area_fraction_16km': 0.3505, 'wdpa_area_fraction_25km': 0.2457, 'wdpa_iucn_iv_v_vi_count': 21, 'wdpa_nearest_designation': 'Landscape Park', 'wdpa_nearest_distance_km': 2.299, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'V', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'IV', 'wdpa_total_protected_area_ha': 130686.34, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `502.35` | 100 |
| RI-03 | `aquifer_type` | `sedimentary carbonates` | 99 |
| RI-04 | `pop_density_5km` | `261.61` | 100 |
|  | `pop_density_16km` | `93.01` | 100 |
|  | `pop_density_25km` | `83.01` | 100 |
|  | `pop_density_80km` | `155.85` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.081` | 100 |
|  | `projected_pop_25km_60yr` | `128079` | 100 |

### Porto Romano Power Station (AL, cancelled)

`site_id`: `e6ecead0-54d1-41fe-8268-1253d0d7ef3e`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `2.94` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `800.00` | 100 |
| BF-02 | `favourable_area_ha` | `42.12` | 100 |
|  | `buildable_area_ha` | `5.75` | 100 |
|  | `largest_contiguous_ha` | `616.36` | 98 |
|  | `site_area_ha` | `5.75` | 71 |
| EP-01 | `ep01_composite_score` | `56.0` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.333` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `22` | 100 |
|  | `prison_count_epz` | `3` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `25.11` | 100 |
|  | `nearest_airport_type` | `large_airport` | 100 |
|  | `nearest_airport_class` | `large_airport` | 100 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_military_km` | `2.16` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `2.16` | 60 |
|  | `hi06_quality` | `high` | 100 |
|  | `flight_path_distance_km` | `12.56` | 100 |
|  | `hi01_comment` | `Nearest: Tirana International Airport Mother Teresa (large_airport) at 25.1 km; Nearest large: 25...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `not_applicable` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `not_applicable` | 100 |
| HI-06 | `nearest_military_km` | `2.16` | 90 |
|  | `nearest_military_class` | `depot` | 90 |
|  | `nearest_high_consequence_military_km` | `2.16` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `66` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.39298` | 100 |
|  | `nh01_pga_2475yr_g` | `0.79056` | 96 |
| NH-02 | `nearest_fault_km` | `3.31` | 100 |
|  | `fault_name` | `ALCF003` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.387` | 100 |
| NH-03 | `liquefaction_suscept` | `very_high` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `68.50` | 85 |
|  | `pga_475yr_g` | `0.39298` | 100 |
|  | `depth_to_bedrock_m` | `21.55` | 99 |
| NH-04 | `slope_angle_deg` | `3.03` | 98 |
|  | `slope_stability_class` | `gentle` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `58.78` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `True` | 100 |
|  | `mining_void_distance_km` | `4.908` | 28 |
| NH-06 | `bearing_capacity_kpa` | `68.50` | 85 |
|  | `depth_to_bedrock_m` | `21.55` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `1.84` | 100 |
|  | `storm_surge_class` | `fluvial_proxy` | 1 |
|  | `elevation_m` | `-0.17` | 100 |
| NH-09 | `river_distance_km` | `0.00` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `8.43` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `41.41` | 100 |
|  | `extreme_precip_mm` | `0.40` | 100 |
| NH-12 | `extreme_temp_max_c` | `25.87` | 100 |
|  | `extreme_temp_min_c` | `6.38` | 100 |
| NS-01 | `cooling_source_type` | `river` | 100 |
|  | `cooling_source_name` | `Erzeni` | 100 |
|  | `cooling_source_hyriv_id` | `20581859` | 100 |
|  | `cooling_distance_km` | `8.07` | 100 |
|  | `cooling_flow_m3s` | `18.02` | 100 |
|  | `water_stress_score` | `1.063` | 100 |
|  | `water_stress_label` | `Extremely High` | 100 |
| NS-02 | `nearest_substation_km` | `2.94` | 100 |
|  | `nearest_hv_line_km` | `3.76` | 100 |
|  | `hv_line_voltage_kv` | `110` | 95 |
|  | `grid_export_capacity_mw` | `800.00` | 100 |
| NS-04 | `favourable_land_pct` | `23.70` | 100 |
|  | `favourable_area_ha` | `42.12` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `5.75` | 100 |
|  | `largest_contiguous_ha` | `616.36` | 98 |
|  | `patch_count` | `4` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `None` | 44 |
|  | `wdpa_nearest_distance_km` | `7.485` | 68 |
|  | `ecological_natural_pct` | `48.70` | 100 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `unknown` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 41.371141, 'lon': 19.425201, 'error': 'Natura 2000 does not cover AL. Use S-15 WDPA for protected area data.', 'source': 'natura2000_eea_wfs', 'quality': 'insufficient', 'n2k_overlap': None, 'country_code': 'AL', 'is_eu_member': False, 'nearby_sites': [], 'n2k_sac_count': 0, 'n2k_spa_count': 0, 'reference_date': None, 'sensitivity_class': 'unknown', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': None, 'n2k_nearest_sitecode': None, 'n2k_nearest_sitename': None, 'n2k_nearest_sitetype': None, 'n2k_sites_within_5km': 0, 'n2k_area_fraction_5km': None, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 0, 'n2k_sites_within_25km': 0, 'n2k_area_fraction_16km': None, 'n2k_area_fraction_25km': None, 'n2k_nearest_distance_km': None, 'n2k_max_conservation_score': None, 'n2k_total_protected_area_ha': 0.0}` | 100 |
|  | `wdpa_result_json` | `{'lat': 41.371141, 'lon': 19.425201, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'AL', 'country_iso3': 'ALB', 'is_eu_member': False, 'nearby_areas': [{'area_ha': 650.0, 'overlap': False, 'site_id': 11664, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 7.485, 'name_english': 'Rrushkull', 'iucn_category': 'IV', 'designation_name': 'Managed Nature Reserve (category IV IUCN)', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 2000.0, 'overlap': False, 'site_id': 555787199, 'is_ramsar': False, 'is_emerald': True, 'distance_km': 7.62, 'name_english': 'Managed Nature Reserve Rrushkulli-Ishem / Rezerva natyrore e Menaxhuar Rrushkull-Ishem.', 'iucn_category': 'Not Reported', 'designation_name': 'Emerald Network', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'Regional'}, {'area_ha': 30000.0, 'overlap': False, 'site_id': 555787266, 'is_ramsar': False, 'is_emerald': True, 'distance_km': 24.713, 'name_english': 'Shengjin-Ishem.', 'iucn_category': 'Not Reported', 'designation_name': 'Emerald Network', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'Regional'}], 'wdpa_overlap': False, 'n2k_deduplicated': False, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Rrushkull', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 650.0, 'wdpa_nearest_site_id': 11664, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 0, 'wdpa_area_fraction_5km': 0.0, 'wdpa_iucn_ii_iii_count': 0, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 2, 'wdpa_sites_within_25km': 3, 'wdpa_area_fraction_16km': 0.0098, 'wdpa_area_fraction_25km': 0.0107, 'wdpa_iucn_iv_v_vi_count': 1, 'wdpa_nearest_designation': 'Managed Nature Reserve (category IV IUCN)', 'wdpa_nearest_distance_km': 7.485, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'IV', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'IV', 'wdpa_total_protected_area_ha': 32650.0, 'wdpa_international_designation_count': 2}` | 100 |
| RI-02 | `cooling_flow_m3s` | `18.02` | 100 |
| RI-03 | `aquifer_type` | `low permeability` | 99 |
| RI-04 | `pop_density_5km` | `399.01` | 100 |
|  | `pop_density_16km` | `280.01` | 100 |
|  | `pop_density_25km` | `153.07` | 100 |
|  | `pop_density_80km` | `105.37` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.118` | 100 |
|  | `projected_pop_25km_60yr` | `170081` | 100 |

### Duernrohr power station (AT, retired)

`site_id`: `6e7fc4d8-636d-411a-baef-e138a5a07acc`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `0.20` | 100 |
|  | `hv_line_voltage_kv` | `380` | 95 |
|  | `grid_export_capacity_mw` | `802.00` | 100 |
| BF-02 | `favourable_area_ha` | `288.97` | 100 |
|  | `buildable_area_ha` | `10.15` | 100 |
|  | `largest_contiguous_ha` | `10.15` | 98 |
|  | `site_area_ha` | `10.15` | 71 |
| EP-01 | `ep01_composite_score` | `72.0` | 100 |
| EP-02 | `road_density_km_per_km2` | `1.130` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `14` | 100 |
|  | `prison_count_epz` | `3` | 100 |
|  | `care_home_count_epz` | `6` | 100 |
| HI-01 | `nearest_airport_km` | `10.48` | 100 |
|  | `nearest_airport_type` | `heliport` | 100 |
|  | `nearest_airport_class` | `heliport` | 100 |
|  | `nearest_military_class` | `training_area` | 90 |
|  | `nearest_military_km` | `7.93` | 90 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
|  | `nearest_high_consequence_military_km` | `10.98` | 60 |
|  | `hi06_quality` | `medium` | 100 |
|  | `flight_path_distance_km` | `7.06` | 100 |
|  | `hi01_comment` | `Nearest: Tulln Heliport (heliport) at 10.5 km; Nearest large: 53.6 km; Nearest medium: 58.7 km; W...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `high` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `high` | 100 |
| HI-06 | `nearest_military_km` | `7.93` | 90 |
|  | `nearest_military_class` | `training_area` | 90 |
|  | `nearest_high_consequence_military_km` | `10.98` | 60 |
|  | `nearest_high_consequence_military_class` | `depot` | 60 |
| HI-07 | `transmitter_count_10km` | `313` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.08665` | 100 |
|  | `nh01_pga_2475yr_g` | `0.20149` | 96 |
| NH-02 | `nearest_fault_km` | `23.87` | 100 |
|  | `fault_name` | `ATCF008` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.022` | 100 |
| NH-03 | `liquefaction_suscept` | `high` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `bearing_capacity_kpa` | `84.70` | 85 |
|  | `pga_475yr_g` | `0.08665` | 100 |
|  | `depth_to_bedrock_m` | `31.75` | 99 |
| NH-04 | `slope_angle_deg` | `5.46` | 98 |
|  | `slope_stability_class` | `moderate` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `84.17` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `84.70` | 85 |
|  | `depth_to_bedrock_m` | `31.75` | 99 |
| NH-07 | `nearest_volcano_km` | `None` | 34 |
|  | `nh07_hazard_class` | `negligible` | 100 |
| NH-08 | `coast_distance_km` | `333.29` | 100 |
|  | `elevation_m` | `192.34` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `11.05` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `25.25` | 100 |
|  | `extreme_precip_mm` | `0.25` | 100 |
| NH-12 | `extreme_temp_max_c` | `23.44` | 100 |
|  | `extreme_temp_min_c` | `-5.12` | 100 |
| NS-01 | `cooling_source_type` | `major_river` | 100 |
|  | `cooling_source_name` | `Danube` | 100 |
|  | `cooling_source_hyriv_id` | `20416147` | 100 |
|  | `cooling_distance_km` | `1.92` | 100 |
|  | `cooling_flow_m3s` | `1917.98` | 100 |
|  | `water_stress_score` | `0.028` | 100 |
|  | `water_stress_label` | `Low` | 100 |
| NS-02 | `nearest_substation_km` | `0.20` | 100 |
|  | `nearest_hv_line_km` | `0.20` | 100 |
|  | `hv_line_voltage_kv` | `380` | 95 |
|  | `grid_export_capacity_mw` | `802.00` | 100 |
| NS-04 | `favourable_land_pct` | `92.20` | 100 |
|  | `favourable_area_ha` | `288.97` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `10.15` | 100 |
|  | `largest_contiguous_ha` | `10.15` | 98 |
|  | `patch_count` | `6` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `1.744` | 44 |
|  | `wdpa_nearest_distance_km` | `6.718` | 68 |
|  | `ecological_natural_pct` | `2.10` | 100 |
|  | `n2k_overlap` | `False` | 44 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `moderate` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 48.32611, 'lon': 15.923333, 'error': None, 'source': 'natura2000_eea_wfs', 'quality': 'high', 'n2k_overlap': False, 'country_code': 'AT', 'is_eu_member': True, 'nearby_sites': [{'area_ha': 17762.86734510324, 'overlap': False, 'sitecode': 'AT1216V00', 'sitename': 'Tullnerfelder Donau-Auen', 'sitetype': 'A', 'distance_km': 1.744, 'direction_deg': 51.9, 'conservation_score': None}, {'area_ha': 17532.648108491016, 'overlap': False, 'sitecode': 'AT1216000', 'sitename': 'Tullnerfelder Donau-Auen', 'sitetype': 'B', 'distance_km': 1.744, 'direction_deg': 54.0, 'conservation_score': 0.2857142857142857}, {'area_ha': 79810.5841487624, 'overlap': False, 'sitecode': 'AT1211000', 'sitename': 'Wienerwald - Thermenregion', 'sitetype': 'A', 'distance_km': 10.784, 'direction_deg': 151.2, 'conservation_score': None}, {'area_ha': 51906.31323891189, 'overlap': False, 'sitecode': 'AT1211A00', 'sitename': 'Wienerwald - Thermenregion', 'sitetype': 'B', 'distance_km': 13.39, 'direction_deg': 144.3, 'conservation_score': 0.2413793103448276}, {'area_ha': 24280.328698218746, 'overlap': False, 'sitecode': 'AT1207000', 'sitename': 'Kamp- und Kremstal', 'sitetype': 'A', 'distance_km': 15.954, 'direction_deg': 318.4, 'conservation_score': None}, {'area_ha': 14491.788784162361, 'overlap': False, 'sitecode': 'AT1207A00', 'sitename': 'Kamp- und Kremstal', 'sitetype': 'B', 'distance_km': 18.531, 'direction_deg': 312.7, 'conservation_score': 0.2727272727272727}, {'area_ha': 18042.758645718503, 'overlap': False, 'sitecode': 'AT1205A00', 'sitename': 'Wachau', 'sitetype': 'B', 'distance_km': 22.375, 'direction_deg': 272.5, 'conservation_score': 0.0967741935483871}, {'area_ha': 16903.23308733804, 'overlap': False, 'sitecode': 'AT1209000', 'sitename': 'Westliches Weinviertel', 'sitetype': 'A', 'distance_km': 23.441, 'direction_deg': 2.1, 'conservation_score': None}, {'area_ha': 2258.001573599967, 'overlap': False, 'sitecode': 'AT1302000', 'sitename': 'Naturschutzgebiet Lainzer Tiergarten', 'sitetype': 'C', 'distance_km': 25.535, 'direction_deg': 126.6, 'conservation_score': 0.0}, {'area_ha': 639.4409474540143, 'overlap': False, 'sitecode': 'AT1303000', 'sitename': 'Landschaftsschutzgebiet Liesing (Teil A, B und C)', 'sitetype': 'C', 'distance_km': 29.009, 'direction_deg': 130.9, 'conservation_score': 0.0}], 'n2k_sac_count': 6, 'n2k_spa_count': 6, 'reference_date': '1733961600000', 'sensitivity_class': 'moderate', 'n2k_combined_count': 2, 'n2k_nearest_area_ha': 17762.86734510324, 'n2k_nearest_sitecode': 'AT1216V00', 'n2k_nearest_sitename': 'Tullnerfelder Donau-Auen', 'n2k_nearest_sitetype': 'A', 'n2k_sites_within_5km': 2, 'n2k_area_fraction_5km': 0.2745, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 5, 'n2k_sites_within_25km': 8, 'n2k_area_fraction_16km': 0.195, 'n2k_area_fraction_25km': 0.2582, 'n2k_nearest_distance_km': 1.744, 'n2k_max_conservation_score': 0.2857, 'n2k_total_protected_area_ha': 243627.96}` | 100 |
|  | `wdpa_result_json` | `{'lat': 48.32611, 'lon': 15.923333, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'AT', 'country_iso3': 'AUT', 'is_eu_member': True, 'nearby_areas': [{'area_ha': 95047.5390625, 'overlap': False, 'site_id': 9409, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.718, 'name_english': 'Wienerwald', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 95048.4921875, 'overlap': False, 'site_id': 555513780, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 6.718, 'name_english': 'Wienerwald', 'iucn_category': 'VI', 'designation_name': 'Biosphere Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 67.28721619, 'overlap': False, 'site_id': 555513775, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 14.694, 'name_english': 'Rauchbuchberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 564.2131958, 'overlap': False, 'site_id': 555513718, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 15.086, 'name_english': 'Troppberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3845.47729492, 'overlap': False, 'site_id': 31431, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.5, 'name_english': 'Eichenhain', 'iucn_category': 'V', 'designation_name': 'Nature Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 325.12475586, 'overlap': False, 'site_id': 555513757, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 19.941, 'name_english': 'Mauerbach-Dombachgraben', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 390.22302246, 'overlap': False, 'site_id': 169150, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 20.369, 'name_english': 'Stockerauer Au', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 508.03967285000004, 'overlap': False, 'site_id': 555513747, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.33, 'name_english': 'Sattel-Baunzen', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 3508.6965332, 'overlap': False, 'site_id': 555633003, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.958, 'name_english': 'Biosphärenpark PZ', 'iucn_category': 'VI', 'designation_name': 'Biosphere Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1975.9036865199998, 'overlap': False, 'site_id': 555597905, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.958, 'name_english': 'LSG Penzing, Teil A, Wienerwald', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 6056.88037109, 'overlap': False, 'site_id': 555633004, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 21.96, 'name_english': 'Biosphärenpark EZ', 'iucn_category': 'VI', 'designation_name': 'Biosphere Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 177.70547485, 'overlap': False, 'site_id': 102738, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.064, 'name_english': 'Göttweiger Berg und seine Umgebung', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 32791.03515625, 'overlap': False, 'site_id': 19170, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.452, 'name_english': 'Kamptal', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 106.01174164, 'overlap': False, 'site_id': 555513726, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.471, 'name_english': 'Altenberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 77.14048767, 'overlap': False, 'site_id': 102891, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 22.978, 'name_english': 'Sandstein-Wienerwald', 'iucn_category': 'V', 'designation_name': 'Nature Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 440.87426758000004, 'overlap': False, 'site_id': 555513770, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.142, 'name_english': 'Hainbach-Hengstlberg', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 1975.9036865199998, 'overlap': False, 'site_id': 555597908, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.374, 'name_english': 'LSG Penzing, Teil C, Sonderzone Sport', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 328.55706787, 'overlap': False, 'site_id': 555633002, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.389, 'name_english': 'Biosphärenpark KZ MA49 Pfaffenberg NWR-V', 'iucn_category': 'II', 'designation_name': 'Biosphere Park', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 93.08149719, 'overlap': False, 'site_id': 555590828, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 23.585, 'name_english': 'Deutschwald', 'iucn_category': 'IV', 'designation_name': 'Nature Reserve', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}, {'area_ha': 45853.25390625, 'overlap': False, 'site_id': 31410, 'is_ramsar': False, 'is_emerald': False, 'distance_km': 24.836, 'name_english': 'Wachau und Umgebung', 'iucn_category': 'V', 'designation_name': 'Landscape Protection Area', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'National'}], 'wdpa_overlap': False, 'n2k_deduplicated': True, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Wienerwald', 'wdpa_ramsar_count': 0, 'wdpa_nearest_area_ha': 95047.5390625, 'wdpa_nearest_site_id': 9409, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 0, 'wdpa_area_fraction_5km': 0.0, 'wdpa_iucn_ii_iii_count': 1, 'wdpa_ramsar_nearest_km': None, 'wdpa_sites_within_16km': 4, 'wdpa_sites_within_25km': 20, 'wdpa_area_fraction_16km': 0.1563, 'wdpa_area_fraction_25km': 0.2242, 'wdpa_iucn_iv_v_vi_count': 19, 'wdpa_nearest_designation': 'Landscape Protection Area', 'wdpa_nearest_distance_km': 6.718, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'V', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': 'II', 'wdpa_total_protected_area_ha': 289181.44, 'wdpa_international_designation_count': 0}` | 100 |
| RI-02 | `cooling_flow_m3s` | `1917.98` | 100 |
| RI-03 | `aquifer_type` | `sedimentary sands` | 99 |
| RI-04 | `pop_density_5km` | `109.82` | 100 |
|  | `pop_density_16km` | `106.42` | 100 |
|  | `pop_density_25km` | `129.06` | 100 |
|  | `pop_density_80km` | `184.62` | 100 |
| RI-06 | `pop_growth_rate_pct` | `0.233` | 100 |
|  | `projected_pop_25km_60yr` | `264777` | 100 |

### Karapinar Konya Şeker power station (TR, cancelled)

`site_id`: `a6478cb9-5b8c-4d64-bbe6-3d3ed6a3da2c`

| Criterion | Context key | Resolved value | Anchor fill % |
| --- | --- | --- | ---: |
| BF-01 | `nearest_substation_km` | `1.72` | 100 |
|  | `hv_line_voltage_kv` | `154` | 95 |
|  | `grid_export_capacity_mw` | `2000.00` | 100 |
| BF-02 | `favourable_area_ha` | `243.52` | 100 |
|  | `buildable_area_ha` | `312.24` | 100 |
|  | `largest_contiguous_ha` | `1247.24` | 98 |
|  | `site_area_ha` | `5.09` | 71 |
| EP-01 | `ep01_composite_score` | `59.0` | 100 |
| EP-02 | `road_density_km_per_km2` | `0.337` | 100 |
|  | `has_motorway_access` | `True` | 100 |
| EP-03 | `major_river_barrier` | `False` | 100 |
|  | `waterway_count_epz` | `0` | 100 |
| EP-04 | `hospital_count_epz` | `1` | 100 |
|  | `prison_count_epz` | `0` | 100 |
|  | `care_home_count_epz` | `0` | 100 |
| HI-01 | `nearest_airport_km` | `70.12` | 100 |
|  | `nearest_airport_type` | `small_airport` | 100 |
|  | `nearest_airport_class` | `small_airport` | 100 |
|  | `hi06_quality` | `no_features_found` | 100 |
|  | `flight_path_distance_km` | `35.06` | 100 |
|  | `hi01_comment` | `Nearest: Aksaray Airport (small_airport) at 70.1 km; Nearest large: 91.9 km; Within 30 km: 0; Sou...` | 100 |
| HI-02 | `nearest_seveso_km` | `None` | 4 |
|  | `hi02_quality` | `low` | 100 |
| HI-04 | `nearest_flammable_storage_km` | `None` | 4 |
|  | `hi04_quality` | `low` | 100 |
| HI-06 | `nearest_military_km` | `None` | 90 |
| HI-07 | `transmitter_count_10km` | `15` | 100 |
| NH-01 | `nh01_pga_475yr_g` | `0.13244` | 100 |
|  | `nh01_pga_2475yr_g` | `0.30831` | 96 |
| NH-02 | `nearest_fault_km` | `50.00` | 100 |
|  | `fault_name` | `none_in_search_radius` | 100 |
|  | `fault_slip_rate_mm_yr` | `0.000` | 100 |
| NH-03 | `liquefaction_suscept` | `moderate` | 98 |
|  | `nh03_quality` | `medium` | 100 |
|  | `nh03_source` | `zhu_global_1km` | 100 |
|  | `pga_475yr_g` | `0.13244` | 100 |
|  | `depth_to_bedrock_m` | `29.89` | 99 |
| NH-04 | `slope_angle_deg` | `1.64` | 98 |
|  | `slope_stability_class` | `flat` | 98 |
|  | `nh04_dem_cog_slope_max_deg` | `23.02` | 98 |
| NH-05 | `karst_present` | `False` | 100 |
|  | `karst_severity` | `none` | 100 |
|  | `mining_void_present` | `False` | 100 |
| NH-06 | `bearing_capacity_kpa` | `None` | 85 |
|  | `depth_to_bedrock_m` | `29.89` | 99 |
| NH-07 | `nearest_volcano_km` | `70.98` | 34 |
|  | `volcano_name` | `Hasandag-Keciboyduran Volcanic Complex` | 34 |
|  | `nh07_hazard_class` | `low` | 100 |
| NH-08 | `coast_distance_km` | `138.44` | 100 |
|  | `elevation_m` | `990.54` | 100 |
| NH-09 | `river_distance_km` | `None` | 4 |
|  | `flood_zone_class_500yr` | `negligible` | 100 |
| NH-10 | `max_wind_speed_ms` | `7.76` | 100 |
| NH-11 | `spi12_min` | `None` | 0 |
|  | `mean_annual_precip_mm` | `10.38` | 100 |
|  | `extreme_precip_mm` | `0.11` | 100 |
| NH-12 | `extreme_temp_max_c` | `27.82` | 100 |
|  | `extreme_temp_min_c` | `-7.18` | 100 |
| NS-01 | `cooling_source_type` | `small_river` | 100 |
|  | `cooling_source_name` | `HYRIV-20660735` | 100 |
|  | `cooling_source_hyriv_id` | `20660735` | 100 |
|  | `cooling_distance_km` | `11.36` | 100 |
|  | `cooling_flow_m3s` | `0.14` | 100 |
|  | `water_stress_score` | `1.275` | 100 |
|  | `water_stress_label` | `Extremely High` | 100 |
| NS-02 | `nearest_substation_km` | `1.72` | 100 |
|  | `nearest_hv_line_km` | `3.01` | 100 |
|  | `hv_line_voltage_kv` | `154` | 95 |
|  | `grid_export_capacity_mw` | `2000.00` | 100 |
| NS-04 | `favourable_land_pct` | `77.50` | 100 |
|  | `favourable_area_ha` | `243.52` | 100 |
|  | `favourable_area_method` | `comment_buildable_x_fav_pct` | 100 |
| NS-05 | `buildable_area_ha` | `312.24` | 100 |
|  | `largest_contiguous_ha` | `1247.24` | 98 |
|  | `patch_count` | `1` | 98 |
| NS-08 | `n2k_nearest_distance_km` | `None` | 44 |
|  | `wdpa_nearest_distance_km` | `7.231` | 68 |
|  | `ecological_natural_pct` | `0.70` | 100 |
|  | `wdpa_overlap` | `False` | 100 |
|  | `n2k_sensitivity_class` | `unknown` | 100 |
|  | `wdpa_sensitivity_class` | `low` | 100 |
|  | `n2k_result_json` | `{'lat': 37.716, 'lon': 33.554, 'error': 'Natura 2000 does not cover TR. Use S-15 WDPA for protected area data.', 'source': 'natura2000_eea_wfs', 'quality': 'insufficient', 'n2k_overlap': None, 'country_code': 'TR', 'is_eu_member': False, 'nearby_sites': [], 'n2k_sac_count': 0, 'n2k_spa_count': 0, 'reference_date': None, 'sensitivity_class': 'unknown', 'n2k_combined_count': 0, 'n2k_nearest_area_ha': None, 'n2k_nearest_sitecode': None, 'n2k_nearest_sitename': None, 'n2k_nearest_sitetype': None, 'n2k_sites_within_5km': 0, 'n2k_area_fraction_5km': None, 'n2k_overlap_sitecodes': [], 'n2k_sites_within_16km': 0, 'n2k_sites_within_25km': 0, 'n2k_area_fraction_16km': None, 'n2k_area_fraction_25km': None, 'n2k_nearest_distance_km': None, 'n2k_max_conservation_score': None, 'n2k_total_protected_area_ha': 0.0}` | 100 |
|  | `wdpa_result_json` | `{'lat': 37.716, 'lon': 33.554, 'error': None, 'source': 'wdpa_protected_planet', 'quality': 'high', 'country_code': 'TR', 'country_iso3': 'TUR', 'is_eu_member': False, 'nearby_areas': [{'area_ha': 202.0, 'overlap': False, 'site_id': 902878, 'is_ramsar': True, 'is_emerald': False, 'distance_km': 7.231, 'name_english': 'Meke Maar', 'iucn_category': 'Not Reported', 'designation_name': 'Wetland of International Importance (Ramsar Site)', 'is_world_heritage': False, 'is_biosphere_reserve': False, 'designation_jurisdiction': 'International'}], 'wdpa_overlap': False, 'n2k_deduplicated': False, 'wdpa_overlap_ids': [], 'sensitivity_class': 'low', 'wdpa_nearest_name': 'Meke Maar', 'wdpa_ramsar_count': 1, 'wdpa_nearest_area_ha': 202.0, 'wdpa_nearest_site_id': 902878, 'wdpa_iucn_ia_ib_count': 0, 'wdpa_sites_within_5km': 0, 'wdpa_area_fraction_5km': 0.0, 'wdpa_iucn_ii_iii_count': 0, 'wdpa_ramsar_nearest_km': 7.231, 'wdpa_sites_within_16km': 1, 'wdpa_sites_within_25km': 1, 'wdpa_area_fraction_16km': 0.0061, 'wdpa_area_fraction_25km': 0.0025, 'wdpa_iucn_iv_v_vi_count': 0, 'wdpa_nearest_designation': 'Wetland of International Importance (Ramsar Site)', 'wdpa_nearest_distance_km': 7.231, 'wdpa_world_heritage_count': 0, 'wdpa_nearest_iucn_category': 'Not Reported', 'wdpa_biosphere_reserve_count': 0, 'wdpa_strictest_iucn_category': None, 'wdpa_total_protected_area_ha': 202.0, 'wdpa_international_designation_count': 1}` | 100 |
| RI-02 | `cooling_flow_m3s` | `0.14` | 100 |
| RI-03 | `aquifer_type` | `volcanic rocks` | 99 |
| RI-04 | `pop_density_5km` | `414.35` | 100 |
|  | `pop_density_16km` | `44.45` | 100 |
|  | `pop_density_25km` | `22.59` | 100 |
|  | `pop_density_80km` | `39.55` | 100 |
| RI-06 | `pop_growth_rate_pct` | `-0.250` | 100 |
|  | `projected_pop_25km_60yr` | `48622` | 100 |

