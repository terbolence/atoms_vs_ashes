# Priority Work Queue (Incomplete Items Only)

Work through **top to bottom**. **🔴** = exclusionary; **🟠** = avoidance / exclusionary-equivalent.

Links point to the per-criterion sections in [`exclusionary_data_sources_access_plan.md`](exclusionary_data_sources_access_plan.md) and [`avoidance_data_sources_access_plan.md`](avoidance_data_sources_access_plan.md).

> **Updated 2026-04-17** — coverage numbers reflect the honest post-wiring-fix report (`reports/coverage_20260417.md`). The previous report (2026-04-14) was measuring only `*_quality`/`*_comment` metadata due to phantom column names in `RELEVANT_ENRICHMENT_FIELDS`; those have been corrected. Items marked ✅ below were previously listed as "not done" but are now confirmed complete.

| Priority | Tier | ID | Work item | Type | Status | Notes |
| -------- | ---- | -- | --------- | ---- | ------ | ----- |
| ✅ | 🔴 | [E7](exclusionary_data_sources_access_plan.md#e7--protected-natural-areas) | ~~Fix `RELEVANT_ENRICHMENT_FIELDS["E7"]` + re-run coverage~~ | Code | **Done** | E7 now 85.8% fill (Natura2000 + WDPA data was already in DB). |
| 1 | 🟠 | [A5–A6](avoidance_data_sources_access_plan.md#a5a6--military-installations) | **FIX-04** OSM military + HV-line batch | Batch run | ⏳ not run | `nearest_military_km`, `nearest_hv_line_km`, `nearest_substation_km` all 0%. ~91 min batch, no API key needed. |
| 2 | 🔴 | [E1](exclusionary_data_sources_access_plan.md#e1--capable-fault-proximity) | **S-18** EFSM20 seismogenic faults | Batch run | ✅ impl done · ⏳ batch not run | Connector + CLI (`download-efsm20`, `efsm20-faults`) fully wired. E1 at 52.5%; `nearest_fault_km` only 28.6% fill; `fault_slip_rate_mm_yr` 0%. Needs batch execution. |
| 3 | 🔴 | [E9](exclusionary_data_sources_access_plan.md#e9--insufficient-cooling-water) | **S-29 / S-30 / S-33** hydrology stack | Batch run | ✅ impl done · ⏳ batch not run | All three connectors + CLI fully wired (`hydrorivers`, `glofas-discharge`, `water-stress`). E9 at 87.5% but `water_stress_score` 0%. Recommended order: S-29 → S-33 → S-30 (per LL-009). |
| 4 | 🔴 | [E4](exclusionary_data_sources_access_plan.md#e4--volcanism) | **S-07** Smithsonian GVP | Batch run | ✅ impl done · ⏳ batch not run | Connector + CLI (`smithsonian-gvp`) fully wired. E4 at 66.7%; `nearest_holocene_volcano_km` only 33.3% fill. |
| 5 | 🟠 | [A11](avoidance_data_sources_access_plan.md#a11--river--coastal-flood) | **Nearest-river top-up** | Data gap | ⚠️ partial | A11 at 75.9%; `nearest_river_km` only 3.6%. S-29 HydroRIVERS connector now available (impl done). |
| 6 | 🟠 | [A13](avoidance_data_sources_access_plan.md#a13--grid-adequacy) / NS-02 | **FIX-04 (grid sub-task)** HV substation/line proximity | Batch run | ⏳ not run | A13 at 49.9%; `nearest_hv_line_km` + `nearest_substation_km` both 0%. Covered in FIX-04 batch. |
| 7 | 🟠 | [A15](avoidance_data_sources_access_plan.md#a15--site-area) / NS-05 | **FIX-03 top-up** OSM `patch_count` + `largest_contiguous_ha` | Data gap | ⚠️ partial | A15 at 73.7%; `buildable_area_ha` 99.7% ✅, `largest_contiguous_ha` 68.9%, `patch_count` 0%. CLI `site-area` registered. |
| 8 | 🟠 | [A7–A8](avoidance_data_sources_access_plan.md#a7a8--seveso--toxic-industrial) | **Seveso/EEA top-up** | Data gap | ⚠️ partial | A7 at 56.5% (`nearest_seveso_km` 2.2%, `nearest_industrial_km` 24.0%); A8 at 74.3% (`nearest_toxic_source_km` 22.9%). Connectors implemented. |
| 9 | 🔴 | [E8](exclusionary_data_sources_access_plan.md#e8--emergency-plan-infeasibility) | **EP-04 top-up** (care homes, hospitals, prisons) | Data gap | ⚠️ partial | E8 at 85.8% overall; EP-04 at 31.7% (`hospital_count_epz`, `care_home_count_epz`, `prison_count_epz` all 14.6%). |
| 10 | — | — | **S-03** OneGeology | Batch run | ✅ impl done · ⏳ batch not run | Connector + CLI (`onegeology`) fully wired. Non-EU geology supplement (NH-02/05). |
| 11 | — | — | **S-04 / S-06 / S-09 / S-11 / S-17** Tier B–D batch runs | Batch run | ✅ all impl done · ⏳ batches not run | ERA5 (`era5`), GFMS (`gfms`), NOAA NCEI (`noaa-ncei`), Eurostat Projections (`eurostat-projections`) — wired. **S-06 GEE** code present but **disabled by default** (no Google app review); opt-in via config + `[earth-engine]` extra. |
| 12 | — | — | Remaining Tier C–D sources (§4 in [implementation tiers](implementation_tiers_and_phases.md)) | Per tables | ⏳ not done | S-05 Sentinel Hub, S-21 SoilGrids, S-23 ELSUS, S-24 USGS VS30, S-26 EGMS, S-27 GEM Fossil, S-28 Marine, S-31 GRanD, S-32 JRC Surface Water, S-34 ESWD, S-35 EFFIS, S-38 Natural Earth, S-40–S-45. |
