---
step: "13_data_post_processing §2.2"
title: Column readability audit
date: 2026-04-18
author: machine-assisted (Cursor agent)
inputs:
  - src/atoms_vs_ashes/db/models.py (5 ORM domain classes)
  - export/export_databases.py (COLUMN_MAPPINGS dict + auto-fallback logic)
  - requirements/05_siting_criteria.md (phase / category per criterion)
  - audit/post_processing/01_requirements_coverage/20260418_gaps.md
---

# Column readability audit — 2026-04-18

## 1. Executive summary

| Metric | Count |
| --- | --- |
| Total domain columns (5 ORM classes) | **251** |
| Explicit `COLUMN_MAPPINGS` entries | **62** |
| — of which dead keys (no matching DB column) | **2** |
| Effective explicit mappings | **60** |
| Auto-fallback mapped (`_quality`/`_comment`/`_source` not in dict) | **75** |
| — of which assigned wrong PHASE prefix | **42** |
| Totally unmapped (no clear name at all) | **116** |
| Columns flagged as cryptic or ambiguous | **12** |

All 191 proposed names below carry `needs_approval: Y`. No schema changes or code edits are made by this audit.

---

## 2. Methodology

1. Listed every `mapped_column()` attribute across the 5 domain classes in `models.py`, excluding infrastructure columns (`site_id`, `fetched_at`, `run_id`).
2. Cross-referenced each column name against the `COLUMN_MAPPINGS` dict in `export_databases.py` (62 entries).
3. Identified columns that would be caught by the auto-fallback logic (lines 166–182 of `export_databases.py`): columns starting with `nh`/`hi`/`ri`/`ep`/`ns` and ending with `_quality`/`_comment`/`_source`, not already in `COLUMN_MAPPINGS`.
4. For each unmapped or auto-mapped column, proposed a clear name following the established convention.
5. Assigned the correct PHASE prefix (`EXCL`/`AVOID`/`RANK`) per criterion, based on the category assignments in `requirements/05_siting_criteria.md` and `20260418_gaps.md`.

### Naming convention

```
<PHASE>_<CATEGORY>_<NUMBER>_<Description>_<MEASURE_TYPE>_<UNIT>
```

| Segment | Values |
| --- | --- |
| PHASE | `EXCL` (exclusionary gate), `AVOID` (avoidance threshold), `RANK` (ranking only) |
| CATEGORY | `NH`, `HI`, `RI`, `EP`, `NS` |
| NUMBER | Two-digit zero-padded (`01`–`14`); `05b` for the subsidence sub-criterion |
| Description | CamelCase descriptor of the metric |
| MEASURE_TYPE | `VALUE` (data), `QUALITY` (quality grade), `COMMENT` (narrative), `SOURCE` (provenance) |
| UNIT | Physical unit: `g`, `km`, `m`, `deg`, `degC`, `pct`, `ha`, `m_per_s`, `m3_per_s`, `mm_per_yr`, `kV`, `MW`, `kPa`, `per_km2`, `people`, `count`, `months`, `fraction`, `score`, `bool`, `class`, `text`, `json` |

---

## 3. Findings

### 3.1 Dead keys in `COLUMN_MAPPINGS`

Two entries in the dict do not match any column in the ORM models:

| COLUMN_MAPPINGS key | Mapped clear name | Issue |
| --- | --- | --- |
| `liquefaction_susceptibility` | `EXCL_NH_03_LiquefactionSusc_VALUE_class` | DB column is `liquefaction_suscept` (truncated). Mapping never fires. |
| `nh03_source` | `EXCL_NH_03_Liquefaction_SOURCE_text` | `SiteNaturalHazards` has no `nh03_source` column. |

**Recommendation:** Fix the key to `liquefaction_suscept`; remove `nh03_source` or add the column if provenance tracking is desired.

### 3.2 Phase-label inconsistencies in existing mappings

The existing `COLUMN_MAPPINGS` uses `EXCL` for HI-01 and HI-02, but the requirements classify both as **Avoidance** (LLM prompt keys A1–A4 and A7). Similarly, NS-02 and NS-03 use `RANK` but are classified as **Avoidance + Rank**.

| Criterion | Existing PHASE | Correct PHASE (per requirements) | Columns affected |
| --- | --- | --- | --- |
| HI-01 | `EXCL` | `AVOID` | 7 mappings |
| HI-02 | `EXCL` | `AVOID` | 4 mappings |
| NS-02 | `RANK` | `AVOID` | 7 mappings |
| NS-03 | `RANK` | `AVOID` | 6 mappings |

**Impact:** 24 existing clear names carry the wrong phase prefix. This is cosmetic for internal use but misleading in stakeholder-facing exports.

**Recommendation:** Batch-update the 24 PHASE prefixes in `COLUMN_MAPPINGS` if/when the clear-naming scheme is finalised. For new proposals in this audit, the **correct** phase is used. For new columns within criteria that already have explicit mappings (e.g. new NS-02 columns), the existing PHASE is preserved to avoid within-criterion inconsistency until the batch update.

### 3.3 Auto-fallback phase errors

The auto-fallback at lines 166–182 of `export_databases.py` uses a simplistic rule:

```
NH/HI → EXCL    RI/EP → AVOID    NS → RANK
```

This assigns the wrong phase to 42 of 75 auto-mapped columns:

| Criterion range | Fallback assigns | Correct PHASE | Wrong columns |
| --- | --- | --- | --- |
| NH-06 | EXCL | RANK | 2 |
| NH-08, NH-09 | EXCL | AVOID | 4 |
| NH-10 through NH-14 | EXCL | RANK | 12 |
| HI-03, HI-04, HI-06 | EXCL | AVOID | 6 |
| HI-05, HI-07, HI-08 | EXCL | RANK | 6 |
| RI-01 through RI-03, RI-05, RI-06 | AVOID | RANK | 10 |
| EP-02 through EP-05 | AVOID | RANK | 8 |

Remaining 33 auto-mapped columns (NH-04, NH-05, NH-05b, NH-07, NS-*) get the correct or defensible phase.

**Recommendation:** Replace the three-rule fallback with a lookup table keyed by criterion ID, reusing the `criteria` DB table's `phase` / `category` columns.

### 3.4 Missing mappings for recently added columns

Migrations 016 and 017 added columns that are in the ORM model but have no `COLUMN_MAPPINGS` entry:

| Migration | Columns added | Criterion |
| --- | --- | --- |
| 016 | `water_stress_score`, `water_stress_label`, `ns01_source` | NS-01 |
| 017 | `ep01_terrain_score`, `ep01_evacuation_feasible` | EP-01 |

---

## 4. Per-table audit

Legend for the **Status** column:

- **mapped** — explicit entry in `COLUMN_MAPPINGS` that matches a real DB column
- **dead** — entry in `COLUMN_MAPPINGS` that does NOT match any DB column
- **auto** — caught by the auto-fallback (may have wrong PHASE)
- **unmapped** — no clear name generated at all

Legend for the **Flag** column:

- **OK** — name is self-explanatory
- **cryptic** — abbreviation or jargon that a non-specialist would not understand
- **ambiguous** — name could be interpreted multiple ways
- **dead** — mapping key does not match any DB column

### 4.1 SiteNaturalHazards (78 columns)

#### NH-01 Seismic ground motion (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 1 | `pga_475yr_g` | mapped | `EXCL_NH_01_PeakGroundAccel475yr_VALUE_g` | OK | — |
| 2 | `pga_2475yr_g` | mapped | `EXCL_NH_01_PeakGroundAccel2475yr_VALUE_g` | OK | — |
| 3 | `spectral_accel_json` | unmapped | `EXCL_NH_01_SpectralAccelResponse_VALUE_json` | OK | Y |
| 4 | `nh01_source` | mapped | `EXCL_NH_01_SeismicGroundMotion_SOURCE_text` | OK | — |
| 5 | `nh01_quality` | mapped | `EXCL_NH_01_SeismicGroundMotion_QUALITY_assessment` | OK | — |
| 6 | `nh01_comment` | mapped | `EXCL_NH_01_SeismicGroundMotion_COMMENT_text` | OK | — |

#### NH-02 Surface rupture / faults (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 7 | `nearest_fault_km` | mapped | `EXCL_NH_02_NearestFaultDist_VALUE_km` | OK | — |
| 8 | `fault_name` | mapped | `EXCL_NH_02_FaultName_VALUE_text` | OK | — |
| 9 | `fault_slip_rate_mm_yr` | mapped | `EXCL_NH_02_FaultSlipRate_VALUE_mm_per_yr` | OK | — |
| 10 | `nh02_source` | mapped | `EXCL_NH_02_SurfaceRupture_SOURCE_text` | OK | — |
| 11 | `nh02_quality` | mapped | `EXCL_NH_02_SurfaceRupture_QUALITY_assessment` | OK | — |
| 12 | `nh02_comment` | mapped | `EXCL_NH_02_SurfaceRupture_COMMENT_text` | OK | — |

#### NH-03 Liquefaction (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 13 | `liquefaction_suscept` | unmapped | `EXCL_NH_03_LiquefactionSusc_VALUE_class` | OK | Y |
| 14 | `soil_type` | unmapped | `EXCL_NH_03_SoilType_VALUE_text` | OK | Y |
| 15 | `groundwater_depth_m` | unmapped | `EXCL_NH_03_GroundwaterDepth_VALUE_m` | OK | Y |
| 16 | `nh03_quality` | mapped | `EXCL_NH_03_Liquefaction_QUALITY_assessment` | OK | — |
| 17 | `nh03_comment` | mapped | `EXCL_NH_03_Liquefaction_COMMENT_text` | OK | — |

Dead mappings for NH-03: `liquefaction_susceptibility` (key mismatch → should be `liquefaction_suscept`), `nh03_source` (column does not exist).

#### NH-04 Slope stability (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 18 | `slope_angle_deg` | unmapped | `EXCL_NH_04_SlopeAngle_VALUE_deg` | OK | Y |
| 19 | `slope_stability_class` | unmapped | `EXCL_NH_04_SlopeStabilityClass_VALUE_class` | OK | Y |
| 20 | `landslide_inventory_notes` | unmapped | `EXCL_NH_04_LandslideInventory_COMMENT_text` | OK | Y |
| 21 | `nh04_quality` | auto | `EXCL_NH_04_SlopeStability_QUALITY_assessment` | OK | Y |
| 22 | `nh04_comment` | auto | `EXCL_NH_04_SlopeStability_COMMENT_text` | OK | Y |
| 23 | `nh04_dem_cog_slope_max_deg` | unmapped | `EXCL_NH_04_DemCogSlopeMax_VALUE_deg` | cryptic | Y |
| 24 | `nh04_gee_slope_max_deg` | unmapped | `EXCL_NH_04_GeeSlopeMax_VALUE_deg` | ambiguous | Y |
| 25 | `nh04_gee_slope_mean_deg` | unmapped | `EXCL_NH_04_GeeSlopeMean_VALUE_deg` | ambiguous | Y |
| 26 | `nh04_gee_terrain_class` | unmapped | `EXCL_NH_04_GeeTerrainClass_VALUE_class` | OK | Y |
| 27 | `nh04_slope_discrepancy` | unmapped | `EXCL_NH_04_SlopeDiscrepancy_VALUE_text` | ambiguous | Y |
| 28 | `nh04_slope_fusion_method` | unmapped | `EXCL_NH_04_SlopeFusionMethod_VALUE_text` | OK | Y |
| 29 | `nh04_cross_source_summary` | unmapped | `EXCL_NH_04_CrossSourceSummary_COMMENT_text` | OK | Y |

#### NH-05 Karst (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 30 | `karst_present` | unmapped | `EXCL_NH_05_KarstPresent_VALUE_bool` | OK | Y |
| 31 | `karst_severity` | unmapped | `EXCL_NH_05_KarstSeverity_VALUE_class` | OK | Y |
| 32 | `karst_formation_type` | unmapped | `EXCL_NH_05_KarstFormationType_VALUE_text` | OK | Y |
| 33 | `nh05_quality` | auto | `EXCL_NH_05_Karst_QUALITY_assessment` | OK | Y |
| 34 | `nh05_comment` | auto | `EXCL_NH_05_Karst_COMMENT_text` | OK | Y |

#### NH-05b Subsidence & collapse (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 35 | `mining_void_present` | unmapped | `EXCL_NH_05b_MiningVoidPresent_VALUE_bool` | OK | Y |
| 36 | `subsidence_risk_class` | unmapped | `EXCL_NH_05b_SubsidenceRiskClass_VALUE_class` | OK | Y |
| 37 | `collapse_mechanism` | unmapped | `EXCL_NH_05b_CollapseMechanism_VALUE_text` | OK | Y |
| 38 | `nh05b_quality` | auto | `EXCL_NH_05b_Subsidence_QUALITY_assessment` | OK | Y |
| 39 | `nh05b_comment` | auto | `EXCL_NH_05b_Subsidence_COMMENT_text` | OK | Y |

#### NH-06 Foundation conditions (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 40 | `bearing_capacity_kpa` | unmapped | `RANK_NH_06_BearingCapacity_VALUE_kPa` | OK | Y |
| 41 | `depth_to_bedrock_m` | unmapped | `RANK_NH_06_DepthToBedrock_VALUE_m` | OK | Y |
| 42 | `nh06_quality` | auto | `RANK_NH_06_Foundation_QUALITY_assessment` | OK | Y |
| 43 | `nh06_comment` | auto | `RANK_NH_06_Foundation_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK` for NH-06.

#### NH-07 Volcanism (EXCL)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 44 | `nearest_holocene_volcano_km` | unmapped | `EXCL_NH_07_NearestVolcanoDist_VALUE_km` | OK | Y |
| 45 | `volcano_name` | unmapped | `EXCL_NH_07_VolcanoName_VALUE_text` | OK | Y |
| 46 | `nh07_quality` | auto | `EXCL_NH_07_Volcanism_QUALITY_assessment` | OK | Y |
| 47 | `nh07_comment` | auto | `EXCL_NH_07_Volcanism_COMMENT_text` | OK | Y |

#### NH-08 Coastal flooding (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 48 | `distance_to_coast_km` | unmapped | `AVOID_NH_08_CoastDistance_VALUE_km` | OK | Y |
| 49 | `storm_surge_risk` | unmapped | `AVOID_NH_08_StormSurgeRisk_VALUE_class` | OK | Y |
| 50 | `tsunami_risk` | unmapped | `AVOID_NH_08_TsunamiRisk_VALUE_class` | OK | Y |
| 51 | `nh08_quality` | auto | `AVOID_NH_08_CoastalFlooding_QUALITY_assessment` | OK | Y |
| 52 | `nh08_comment` | auto | `AVOID_NH_08_CoastalFlooding_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `AVOID` for NH-08.

#### NH-09 River flooding (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 53 | `flood_zone_class` | unmapped | `AVOID_NH_09_FloodZoneClass_VALUE_class` | OK | Y |
| 54 | `nearest_river_km` | unmapped | `AVOID_NH_09_NearestRiverDist_VALUE_km` | OK | Y |
| 55 | `dam_break_exposure` | unmapped | `AVOID_NH_09_DamBreakExposure_VALUE_bool` | OK | Y |
| 56 | `nh09_quality` | auto | `AVOID_NH_09_RiverFlooding_QUALITY_assessment` | OK | Y |
| 57 | `nh09_comment` | auto | `AVOID_NH_09_RiverFlooding_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `AVOID` for NH-09.

#### NH-10 Extreme winds (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 58 | `max_wind_speed_ms` | unmapped | `RANK_NH_10_MaxWindSpeed_VALUE_m_per_s` | OK | Y |
| 59 | `nh10_quality` | auto | `RANK_NH_10_ExtremeWinds_QUALITY_assessment` | OK | Y |
| 60 | `nh10_comment` | auto | `RANK_NH_10_ExtremeWinds_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

#### NH-11 Extreme precipitation (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 61 | `extreme_precip_mm` | unmapped | `RANK_NH_11_ExtremePrecip_VALUE_mm` | OK | Y |
| 62 | `nh11_quality` | auto | `RANK_NH_11_ExtremePrecip_QUALITY_assessment` | OK | Y |
| 63 | `nh11_comment` | auto | `RANK_NH_11_ExtremePrecip_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

#### NH-12 Extreme temperatures (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 64 | `extreme_temp_max_c` | unmapped | `RANK_NH_12_ExtremeTempMax_VALUE_degC` | OK | Y |
| 65 | `extreme_temp_min_c` | unmapped | `RANK_NH_12_ExtremeTempMin_VALUE_degC` | OK | Y |
| 66 | `nh12_quality` | auto | `RANK_NH_12_ExtremeTemp_QUALITY_assessment` | OK | Y |
| 67 | `nh12_comment` | auto | `RANK_NH_12_ExtremeTemp_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

#### NH-13 Forest / wildfire (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 68 | `wildfire_combustible_pct` | unmapped | `RANK_NH_13_CombustibleLandPct_VALUE_pct` | OK | Y |
| 69 | `wildfire_wui_ha` | unmapped | `RANK_NH_13_WildfireUrbanInterfaceArea_VALUE_ha` | cryptic | Y |
| 70 | `nh13_quality` | auto | `RANK_NH_13_Wildfire_QUALITY_assessment` | OK | Y |
| 71 | `nh13_comment` | auto | `RANK_NH_13_Wildfire_COMMENT_text` | OK | Y |
| 72 | `nh13_gee_modis_burn_months` | unmapped | `RANK_NH_13_GeeModisBurnMonths_VALUE_months` | cryptic | Y |
| 73 | `nh13_gee_fire_recurrence_class` | unmapped | `RANK_NH_13_GeeFireRecurrenceClass_VALUE_class` | OK | Y |
| 74 | `nh13_gee_burn_fraction_mean` | unmapped | `RANK_NH_13_GeeBurnFractionMean_VALUE_fraction` | OK | Y |
| 75 | `nh13_cross_source_summary` | unmapped | `RANK_NH_13_CrossSourceSummary_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

#### NH-14 Combined hazards (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 76 | `combined_hazard_notes` | unmapped | `RANK_NH_14_CombinedHazardNotes_COMMENT_text` | OK | Y |
| 77 | `nh14_quality` | auto | `RANK_NH_14_CombinedHazards_QUALITY_assessment` | OK | Y |
| 78 | `nh14_comment` | auto | `RANK_NH_14_CombinedHazards_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

---

### 4.2 SiteHumanHazards (35 columns)

#### HI-01 Aircraft crash (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 79 | `nearest_airport_km` | mapped | `EXCL_HI_01_AirportDistance_VALUE_km` | OK | — |
| 80 | `nearest_airport_name` | mapped | `EXCL_HI_01_AirportName_VALUE_text` | OK | — |
| 81 | `nearest_airport_type` | mapped | `EXCL_HI_01_AirportType_VALUE_text` | OK | — |
| 82 | `flight_path_distance_km` | mapped | `EXCL_HI_01_FlightPathDist_VALUE_km` | OK | — |
| 83 | `airport_count` | mapped | `EXCL_HI_01_AirportCount_VALUE_count` | OK | — |
| 84 | `hi01_quality` | mapped | `EXCL_HI_01_AircraftCrash_QUALITY_assessment` | OK | — |
| 85 | `hi01_comment` | mapped | `EXCL_HI_01_AircraftCrash_COMMENT_text` | OK | — |

Phase note: existing mappings use `EXCL`; correct phase per requirements is `AVOID` (see §3.2).

#### HI-02 Industrial explosions (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 86 | `nearest_seveso_km` | mapped | `EXCL_HI_02_SevesoDistance_VALUE_km` | OK | — |
| 87 | `nearest_industrial_km` | mapped | `EXCL_HI_02_IndustrialDistance_VALUE_km` | OK | — |
| 88 | `hi02_quality` | mapped | `EXCL_HI_02_IndustrialExplosion_QUALITY_assessment` | OK | — |
| 89 | `hi02_comment` | mapped | `EXCL_HI_02_IndustrialExplosion_COMMENT_text` | OK | — |

Phase note: same as HI-01 — existing uses `EXCL`, correct is `AVOID`.

#### HI-03 Toxic / gas releases (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 90 | `nearest_toxic_source_km` | unmapped | `AVOID_HI_03_ToxicSourceDist_VALUE_km` | OK | Y |
| 91 | `hi03_quality` | auto | `AVOID_HI_03_ToxicReleases_QUALITY_assessment` | OK | Y |
| 92 | `hi03_comment` | auto | `AVOID_HI_03_ToxicReleases_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `AVOID`.

#### HI-04 External fires (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 93 | `nearest_flammable_storage_km` | unmapped | `AVOID_HI_04_FlammableStorageDist_VALUE_km` | OK | Y |
| 94 | `nearest_pipeline_km` | unmapped | `AVOID_HI_04_PipelineDist_VALUE_km` | OK | Y |
| 95 | `hi04_quality` | auto | `AVOID_HI_04_ExternalFires_QUALITY_assessment` | OK | Y |
| 96 | `hi04_comment` | auto | `AVOID_HI_04_ExternalFires_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `AVOID`.

#### HI-05 Transport hazards (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 97 | `hazmat_route_distance_km` | unmapped | `RANK_HI_05_HazmatRouteDist_VALUE_km` | OK | Y |
| 98 | `hi05_quality` | auto | `RANK_HI_05_TransportHazards_QUALITY_assessment` | OK | Y |
| 99 | `hi05_comment` | auto | `RANK_HI_05_TransportHazards_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

#### HI-06 Military installations (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 100 | `nearest_military_km` | unmapped | `AVOID_HI_06_MilitaryDist_VALUE_km` | OK | Y |
| 101 | `nearest_military_name` | unmapped | `AVOID_HI_06_MilitaryName_VALUE_text` | OK | Y |
| 102 | `military_count` | unmapped | `AVOID_HI_06_MilitaryCount_VALUE_count` | ambiguous | Y |
| 103 | `hi06_quality` | auto | `AVOID_HI_06_Military_QUALITY_assessment` | OK | Y |
| 104 | `hi06_comment` | auto | `AVOID_HI_06_Military_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `AVOID`. `military_count` is ambiguous — count within what radius?

#### HI-07 Electromagnetic interference (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 105 | `nearest_transmitter_km` | unmapped | `RANK_HI_07_TransmitterDist_VALUE_km` | OK | Y |
| 106 | `transmitter_type` | unmapped | `RANK_HI_07_TransmitterType_VALUE_text` | OK | Y |
| 107 | `transmitter_count` | unmapped | `RANK_HI_07_TransmitterCount_VALUE_count` | ambiguous | Y |
| 108 | `hi07_quality` | auto | `RANK_HI_07_EMI_QUALITY_assessment` | OK | Y |
| 109 | `hi07_comment` | auto | `RANK_HI_07_EMI_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`. `transmitter_count` is ambiguous — count within what radius?

#### HI-08 Other nuclear installations (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 110 | `nearest_nuclear_km` | unmapped | `RANK_HI_08_NuclearInstDist_VALUE_km` | OK | Y |
| 111 | `nearest_nuclear_name` | unmapped | `RANK_HI_08_NuclearInstName_VALUE_text` | OK | Y |
| 112 | `hi08_quality` | auto | `RANK_HI_08_OtherNuclear_QUALITY_assessment` | OK | Y |
| 113 | `hi08_comment` | auto | `RANK_HI_08_OtherNuclear_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `EXCL` instead of `RANK`.

---

### 4.3 SiteRadiological (31 columns)

#### RI-04 Population density (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 114 | `pop_density_5km` | mapped | `AVOID_RI_04_PopDensity5km_VALUE_per_km2` | OK | — |
| 115 | `pop_density_16km` | mapped | `AVOID_RI_04_PopDensity16km_VALUE_per_km2` | OK | — |
| 116 | `pop_density_25km` | mapped | `AVOID_RI_04_PopDensity25km_VALUE_per_km2` | OK | — |
| 117 | `pop_density_80km` | mapped | `AVOID_RI_04_PopDensity80km_VALUE_per_km2` | OK | — |
| 118 | `pop_total_5km` | mapped | `AVOID_RI_04_PopTotal5km_VALUE_people` | OK | — |
| 119 | `pop_total_16km` | mapped | `AVOID_RI_04_PopTotal16km_VALUE_people` | OK | — |
| 120 | `pop_total_25km` | mapped | `AVOID_RI_04_PopTotal25km_VALUE_people` | OK | — |
| 121 | `pop_total_80km` | mapped | `AVOID_RI_04_PopTotal80km_VALUE_people` | OK | — |
| 122 | `ri04_quality` | mapped | `AVOID_RI_04_PopulationDensity_QUALITY_assessment` | OK | — |
| 123 | `ri04_comment` | mapped | `AVOID_RI_04_PopulationDensity_COMMENT_text` | OK | — |

#### RI-05 Population centres distance (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 124 | `nearest_city_50k_km` | unmapped | `RANK_RI_05_NearestCity50kDist_VALUE_km` | OK | Y |
| 125 | `nearest_city_name` | unmapped | `RANK_RI_05_NearestCityName_VALUE_text` | OK | Y |
| 126 | `nearest_city_pop` | unmapped | `RANK_RI_05_NearestCityPop_VALUE_people` | OK | Y |
| 127 | `ri05_quality` | auto | `RANK_RI_05_PopCentres_QUALITY_assessment` | OK | Y |
| 128 | `ri05_comment` | auto | `RANK_RI_05_PopCentres_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### RI-06 Population projections (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 129 | `pop_growth_rate_pct` | unmapped | `RANK_RI_06_PopGrowthRate_VALUE_pct` | OK | Y |
| 130 | `projected_pop_25km_60yr` | unmapped | `RANK_RI_06_ProjectedPop25km60yr_VALUE_people` | OK | Y |
| 131 | `ri06_quality` | auto | `RANK_RI_06_PopProjections_QUALITY_assessment` | OK | Y |
| 132 | `ri06_comment` | auto | `RANK_RI_06_PopProjections_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### RI-01 Atmospheric dispersion (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 133 | `prevailing_wind_dir` | unmapped | `RANK_RI_01_PrevailingWindDir_VALUE_text` | OK | Y |
| 134 | `avg_wind_speed_ms` | unmapped | `RANK_RI_01_AvgWindSpeed_VALUE_m_per_s` | OK | Y |
| 135 | `mixing_height_m` | unmapped | `RANK_RI_01_MixingHeight_VALUE_m` | OK | Y |
| 136 | `ri01_quality` | auto | `RANK_RI_01_AtmosphericDispersion_QUALITY_assessment` | OK | Y |
| 137 | `ri01_comment` | auto | `RANK_RI_01_AtmosphericDispersion_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### RI-02 Surface water dispersion (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 138 | `nearest_river_flow_m3s` | unmapped | `RANK_RI_02_NearestRiverFlow_VALUE_m3_per_s` | OK | Y |
| 139 | `ri02_quality` | auto | `RANK_RI_02_SurfaceWaterDispersion_QUALITY_assessment` | OK | Y |
| 140 | `ri02_comment` | auto | `RANK_RI_02_SurfaceWaterDispersion_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### RI-03 Groundwater dispersion (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 141 | `aquifer_type` | unmapped | `RANK_RI_03_AquiferType_VALUE_text` | OK | Y |
| 142 | `groundwater_flow_dir` | unmapped | `RANK_RI_03_GroundwaterFlowDir_VALUE_text` | OK | Y |
| 143 | `ri03_quality` | auto | `RANK_RI_03_GroundwaterDispersion_QUALITY_assessment` | OK | Y |
| 144 | `ri03_comment` | auto | `RANK_RI_03_GroundwaterDispersion_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

---

### 4.4 SiteEmergencyPlanning (29 columns)

#### EP-01 Emergency plan feasibility (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 145 | `ep01_composite_score` | mapped | `AVOID_EP_01_EmergencyPlanScore_VALUE_score` | OK | — |
| 146 | `ep01_road_score` | mapped | `AVOID_EP_01_RoadScore_VALUE_score` | OK | — |
| 147 | `ep01_special_pop_score` | mapped | `AVOID_EP_01_SpecialPopScore_VALUE_score` | OK | — |
| 148 | `ep01_geography_score` | mapped | `AVOID_EP_01_GeographyScore_VALUE_score` | OK | — |
| 149 | `ep01_population_score` | mapped | `AVOID_EP_01_PopulationScore_VALUE_score` | OK | — |
| 150 | `ep01_terrain_score` | unmapped | `AVOID_EP_01_TerrainScore_VALUE_score` | OK | Y |
| 151 | `ep01_evacuation_feasible` | unmapped | `AVOID_EP_01_EvacuationFeasible_VALUE_bool` | OK | Y |
| 152 | `ep01_quality` | mapped | `AVOID_EP_01_EmergencyPlanFeasibility_QUALITY_assessment` | OK | — |
| 153 | `ep01_comment` | mapped | `AVOID_EP_01_EmergencyPlanFeasibility_COMMENT_text` | OK | — |

#### EP-02 Evacuation routes (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 154 | `road_density_km_per_km2` | unmapped | `RANK_EP_02_RoadDensity_VALUE_km_per_km2` | OK | Y |
| 155 | `total_road_km` | unmapped | `RANK_EP_02_TotalRoadLength_VALUE_km` | OK | Y |
| 156 | `has_motorway_access` | unmapped | `RANK_EP_02_MotorwayAccess_VALUE_bool` | OK | Y |
| 157 | `ep02_quality` | auto | `RANK_EP_02_EvacuationRoutes_QUALITY_assessment` | OK | Y |
| 158 | `ep02_comment` | auto | `RANK_EP_02_EvacuationRoutes_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### EP-03 Physical geography constraints (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 159 | `major_river_barrier` | unmapped | `RANK_EP_03_MajorRiverBarrier_VALUE_bool` | OK | Y |
| 160 | `waterway_count_epz` | unmapped | `RANK_EP_03_WaterwayCountEPZ_VALUE_count` | OK | Y |
| 161 | `ep03_quality` | auto | `RANK_EP_03_GeographyConstraints_QUALITY_assessment` | OK | Y |
| 162 | `ep03_comment` | auto | `RANK_EP_03_GeographyConstraints_COMMENT_text` | OK | Y |
| 163 | `ep03_gee_relief_16km_m` | unmapped | `RANK_EP_03_GeeRelief16km_VALUE_m` | cryptic | Y |
| 164 | `ep03_gee_mountain_barrier_score` | unmapped | `RANK_EP_03_GeeMountainBarrierScore_VALUE_score` | cryptic | Y |
| 165 | `ep03_cross_source_summary` | unmapped | `RANK_EP_03_CrossSourceSummary_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### EP-04 Special populations (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 166 | `hospital_count_epz` | unmapped | `RANK_EP_04_HospitalCountEPZ_VALUE_count` | OK | Y |
| 167 | `prison_count_epz` | unmapped | `RANK_EP_04_PrisonCountEPZ_VALUE_count` | OK | Y |
| 168 | `care_home_count_epz` | unmapped | `RANK_EP_04_CareHomeCountEPZ_VALUE_count` | OK | Y |
| 169 | `ep04_quality` | auto | `RANK_EP_04_SpecialPopulations_QUALITY_assessment` | OK | Y |
| 170 | `ep04_comment` | auto | `RANK_EP_04_SpecialPopulations_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

#### EP-05 Concurrent hazard impact (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 171 | `concurrent_hazard_notes` | unmapped | `RANK_EP_05_ConcurrentHazardNotes_COMMENT_text` | OK | Y |
| 172 | `ep05_quality` | auto | `RANK_EP_05_ConcurrentHazard_QUALITY_assessment` | OK | Y |
| 173 | `ep05_comment` | auto | `RANK_EP_05_ConcurrentHazard_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `AVOID` instead of `RANK`.

---

### 4.5 SiteInfrastructureV2 (78 columns)

#### NS-01 Cooling water (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 174 | `cooling_source_type` | mapped | `RANK_NS_01_CoolingSourceType_VALUE_text` | OK | — |
| 175 | `cooling_source_name` | mapped | `RANK_NS_01_CoolingSourceName_VALUE_text` | OK | — |
| 176 | `cooling_distance_km` | mapped | `RANK_NS_01_CoolingDistance_VALUE_km` | OK | — |
| 177 | `cooling_flow_m3s` | mapped | `RANK_NS_01_CoolingFlow_VALUE_m3_per_s` | OK | — |
| 178 | `water_stress_score` | unmapped | `RANK_NS_01_WaterStressScore_VALUE_score` | OK | Y |
| 179 | `water_stress_label` | unmapped | `RANK_NS_01_WaterStressLabel_VALUE_text` | OK | Y |
| 180 | `ns01_source` | auto | `RANK_NS_01_CoolingWaterAvail_SOURCE_text` | OK | Y |
| 181 | `ns01_quality` | mapped | `RANK_NS_01_CoolingWaterAvail_QUALITY_assessment` | OK | — |
| 182 | `ns01_comment` | mapped | `RANK_NS_01_CoolingWaterAvail_COMMENT_text` | OK | — |

#### NS-02 Grid connection (RANK per existing; correct phase is AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 183 | `nearest_substation_km` | mapped | `RANK_NS_02_SubstationDistance_VALUE_km` | OK | — |
| 184 | `substation_name` | mapped | `RANK_NS_02_SubstationName_VALUE_text` | OK | — |
| 185 | `nearest_hv_line_km` | mapped | `RANK_NS_02_HVLineDistance_VALUE_km` | OK | — |
| 186 | `hv_line_voltage_kv` | mapped | `RANK_NS_02_HVLineVoltage_VALUE_kV` | OK | — |
| 187 | `hv_line_count` | unmapped | `RANK_NS_02_HVLineCount_VALUE_count` | ambiguous | Y |
| 188 | `substation_count` | unmapped | `RANK_NS_02_SubstationCount_VALUE_count` | ambiguous | Y |
| 189 | `grid_export_capacity_mw` | mapped | `RANK_NS_02_GridExportCapacity_VALUE_MW` | OK | — |
| 190 | `ns02_quality` | mapped | `RANK_NS_02_GridConnection_QUALITY_assessment` | OK | — |
| 191 | `ns02_comment` | mapped | `RANK_NS_02_GridConnection_COMMENT_text` | OK | — |

Phase note: existing uses `RANK`; correct per requirements is `AVOID` (see §3.2). New proposals use `RANK` to match existing within-criterion names.

#### NS-03 Transport access (RANK per existing; correct phase is AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 192 | `nearest_highway_km` | mapped | `RANK_NS_03_HighwayDistance_VALUE_km` | OK | — |
| 193 | `nearest_rail_km` | mapped | `RANK_NS_03_RailDistance_VALUE_km` | OK | — |
| 194 | `nearest_waterway_km` | mapped | `RANK_NS_03_WaterwayDistance_VALUE_km` | OK | — |
| 195 | `heavy_haul_capable` | mapped | `RANK_NS_03_HeavyHaulCapable_VALUE_bool` | OK | — |
| 196 | `ns03_quality` | mapped | `RANK_NS_03_TransportAccess_QUALITY_assessment` | OK | — |
| 197 | `ns03_comment` | mapped | `RANK_NS_03_TransportAccess_COMMENT_text` | OK | — |

Phase note: existing uses `RANK`; correct per requirements is `AVOID` (see §3.2).

#### NS-04 Site topography (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 198 | `dominant_land_class` | unmapped | `RANK_NS_04_DominantLandClass_VALUE_text` | OK | Y |
| 199 | `dominant_class_pct` | unmapped | `RANK_NS_04_DominantClassPct_VALUE_pct` | OK | Y |
| 200 | `favourable_land_pct` | unmapped | `RANK_NS_04_FavourableLandPct_VALUE_pct` | OK | Y |
| 201 | `moderate_land_pct` | unmapped | `RANK_NS_04_ModerateLandPct_VALUE_pct` | OK | Y |
| 202 | `unfavourable_land_pct` | unmapped | `RANK_NS_04_UnfavourableLandPct_VALUE_pct` | OK | Y |
| 203 | `ns04_quality` | auto | `RANK_NS_04_Topography_QUALITY_assessment` | OK | Y |
| 204 | `ns04_comment` | auto | `RANK_NS_04_Topography_COMMENT_text` | OK | Y |
| 205 | `ns04_gee_terrain_class` | unmapped | `RANK_NS_04_GeeTerrainClass_VALUE_class` | OK | Y |
| 206 | `ns04_gee_relief_range_m` | unmapped | `RANK_NS_04_GeeReliefRange_VALUE_m` | OK | Y |
| 207 | `ns04_gee_grading_class` | unmapped | `RANK_NS_04_GeeGradingClass_VALUE_class` | ambiguous | Y |
| 208 | `ns04_cross_source_summary` | unmapped | `RANK_NS_04_CrossSourceSummary_COMMENT_text` | OK | Y |

#### NS-05 Land availability (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 209 | `buildable_area_ha` | unmapped | `AVOID_NS_05_BuildableArea_VALUE_ha` | OK | Y |
| 210 | `largest_contiguous_ha` | unmapped | `AVOID_NS_05_LargestContiguousArea_VALUE_ha` | OK | Y |
| 211 | `patch_count` | unmapped | `AVOID_NS_05_PatchCount_VALUE_count` | OK | Y |
| 212 | `ns05_quality` | auto | `AVOID_NS_05_LandAvailability_QUALITY_assessment` | OK | Y |
| 213 | `ns05_comment` | auto | `AVOID_NS_05_LandAvailability_COMMENT_text` | OK | Y |

Note: auto-fallback assigns `RANK` instead of `AVOID`.

#### NS-06 Existing infrastructure (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 214 | `reusable_infra_score` | unmapped | `RANK_NS_06_ReusableInfraScore_VALUE_score` | OK | Y |
| 215 | `ns06_quality` | auto | `RANK_NS_06_ExistingInfra_QUALITY_assessment` | OK | Y |
| 216 | `ns06_comment` | auto | `RANK_NS_06_ExistingInfra_COMMENT_text` | OK | Y |
| 217 | `ns06_gee_built_fraction` | unmapped | `RANK_NS_06_GeeBuiltFraction_VALUE_fraction` | OK | Y |
| 218 | `ns06_gee_demolition_class` | unmapped | `RANK_NS_06_GeeDemolitionClass_VALUE_class` | cryptic | Y |
| 219 | `ns06_cross_source_summary` | unmapped | `RANK_NS_06_CrossSourceSummary_COMMENT_text` | OK | Y |

#### NS-07 Environmental impact non-rad (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 220 | `env_impact_notes` | unmapped | `RANK_NS_07_EnvImpactNotes_COMMENT_text` | OK | Y |
| 221 | `ns07_quality` | auto | `RANK_NS_07_EnvImpactNonRad_QUALITY_assessment` | OK | Y |
| 222 | `ns07_comment` | auto | `RANK_NS_07_EnvImpactNonRad_COMMENT_text` | OK | Y |

#### NS-08 Ecological sensitivity (AVOID)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 223 | `ecological_natural_pct` | unmapped | `AVOID_NS_08_EcologicalNaturalPct_VALUE_pct` | OK | Y |
| 224 | `ecological_patch_count` | unmapped | `AVOID_NS_08_EcologicalPatchCount_VALUE_count` | OK | Y |
| 225 | `ecological_largest_patch_ha` | unmapped | `AVOID_NS_08_EcologicalLargestPatch_VALUE_ha` | OK | Y |
| 226 | `n2k_nearest_distance_km` | unmapped | `AVOID_NS_08_Natura2000Distance_VALUE_km` | cryptic | Y |
| 227 | `n2k_overlap` | unmapped | `AVOID_NS_08_Natura2000Overlap_VALUE_bool` | cryptic | Y |
| 228 | `n2k_sensitivity_class` | unmapped | `AVOID_NS_08_Natura2000SensitivityClass_VALUE_class` | cryptic | Y |
| 229 | `n2k_result_json` | unmapped | `AVOID_NS_08_Natura2000Results_VALUE_json` | cryptic | Y |
| 230 | `ns08_source` | auto | `AVOID_NS_08_EcologicalSensitivity_SOURCE_text` | OK | Y |
| 231 | `ns08_quality` | auto | `AVOID_NS_08_EcologicalSensitivity_QUALITY_assessment` | OK | Y |
| 232 | `ns08_comment` | auto | `AVOID_NS_08_EcologicalSensitivity_COMMENT_text` | OK | Y |
| 233 | `wdpa_nearest_distance_km` | unmapped | `AVOID_NS_08_WdpaProtectedAreaDist_VALUE_km` | cryptic | Y |
| 234 | `wdpa_overlap` | unmapped | `AVOID_NS_08_WdpaOverlap_VALUE_bool` | cryptic | Y |
| 235 | `wdpa_sensitivity_class` | unmapped | `AVOID_NS_08_WdpaSensitivityClass_VALUE_class` | cryptic | Y |
| 236 | `wdpa_result_json` | unmapped | `AVOID_NS_08_WdpaResults_VALUE_json` | cryptic | Y |
| 237 | `wdpa_source` | unmapped | `AVOID_NS_08_WdpaProtectedArea_SOURCE_text` | cryptic | Y |
| 238 | `wdpa_quality` | unmapped | `AVOID_NS_08_WdpaProtectedArea_QUALITY_assessment` | cryptic | Y |
| 239 | `wdpa_comment` | unmapped | `AVOID_NS_08_WdpaProtectedArea_COMMENT_text` | OK | Y |

Note: `n2k_*` and `wdpa_*` columns are the most cryptic in the schema. `n2k` = Natura 2000 network; `wdpa` = World Database on Protected Areas. Both are abbreviations that would be opaque to a non-specialist auditor. The `wdpa_*` columns are NOT caught by the auto-fallback because they don't start with `ns`/`nh`/etc.

Note: auto-fallback assigns `RANK` for `ns08_*` instead of `AVOID`.

#### NS-09 Socioeconomic impact (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 240 | `ns09_quality` | auto | `RANK_NS_09_SocioeconomicImpact_QUALITY_assessment` | OK | Y |
| 241 | `ns09_comment` | auto | `RANK_NS_09_SocioeconomicImpact_COMMENT_text` | OK | Y |

#### NS-10 Workforce availability (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 242 | `ns10_quality` | auto | `RANK_NS_10_WorkforceAvailability_QUALITY_assessment` | OK | Y |
| 243 | `ns10_comment` | auto | `RANK_NS_10_WorkforceAvailability_COMMENT_text` | OK | Y |

#### NS-11 Coal-to-nuclear synergies (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 244 | `ns11_quality` | auto | `RANK_NS_11_CoalToNuclearSynergies_QUALITY_assessment` | OK | Y |
| 245 | `ns11_comment` | auto | `RANK_NS_11_CoalToNuclearSynergies_COMMENT_text` | OK | Y |

#### NS-12 Regulatory / political (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 246 | `ns12_quality` | auto | `RANK_NS_12_RegulatoryPolitical_QUALITY_assessment` | OK | Y |
| 247 | `ns12_comment` | auto | `RANK_NS_12_RegulatoryPolitical_COMMENT_text` | OK | Y |

#### NS-13 Construction logistics (RANK)

| # | DB column | Status | Clear name | Flag | Approval |
| --- | --- | --- | --- | --- | --- |
| 248 | `laydown_suitable_ha` | unmapped | `RANK_NS_13_LaydownSuitableArea_VALUE_ha` | OK | Y |
| 249 | `laydown_largest_patch_ha` | unmapped | `RANK_NS_13_LaydownLargestPatch_VALUE_ha` | OK | Y |
| 250 | `ns13_quality` | auto | `RANK_NS_13_ConstructionLogistics_QUALITY_assessment` | OK | Y |
| 251 | `ns13_comment` | auto | `RANK_NS_13_ConstructionLogistics_COMMENT_text` | OK | Y |

---

## 5. Flagged columns (cryptic or ambiguous)

These columns require extra attention because their DB names would not be understood by an external auditor without domain context.

### 5.1 Cryptic abbreviations

| DB column | Abbreviation | Full meaning | Proposed clear name resolves it? |
| --- | --- | --- | --- |
| `n2k_nearest_distance_km` | `n2k` | Natura 2000 (EU ecological network) | Yes — proposed name uses `Natura2000` |
| `n2k_overlap` | `n2k` | Natura 2000 | Yes |
| `n2k_sensitivity_class` | `n2k` | Natura 2000 | Yes |
| `n2k_result_json` | `n2k` | Natura 2000 | Yes |
| `wdpa_nearest_distance_km` | `wdpa` | World Database on Protected Areas | Yes — proposed name uses `WdpaProtectedArea` |
| `wdpa_overlap` | `wdpa` | World Database on Protected Areas | Yes |
| `wdpa_sensitivity_class` | `wdpa` | World Database on Protected Areas | Yes |
| `wdpa_result_json` | `wdpa` | World Database on Protected Areas | Yes |
| `wdpa_source` | `wdpa` | World Database on Protected Areas | Yes |
| `wdpa_quality` | `wdpa` | World Database on Protected Areas | Yes |
| `nh04_dem_cog_slope_max_deg` | `dem_cog` | Digital Elevation Model, Cloud-Optimized GeoTIFF (Copernicus DEM) | Partially — proposed name abbreviates to `DemCog` |
| `wildfire_wui_ha` | `wui` | Wildland–Urban Interface (fire science term) | Yes — proposed name spells out `WildfireUrbanInterfaceArea` |
| `nh13_gee_modis_burn_months` | `gee`, `modis` | Google Earth Engine; MODIS satellite burn-area product | Partially — `Gee` and `Modis` remain in the name as domain-standard identifiers |
| `ep03_gee_relief_16km_m` | `gee` | Google Earth Engine | Partially |
| `ep03_gee_mountain_barrier_score` | `gee` | Google Earth Engine | Partially |
| `ns06_gee_demolition_class` | `gee`, `demolition` | Google Earth Engine; "demolition" classifies whether existing structures need demolition for site reuse | Yes — proposed name uses `GeeDemolitionClass` |

### 5.2 Ambiguous column names

| DB column | Ambiguity | Recommendation |
| --- | --- | --- |
| `slope_angle_deg` vs `nh04_dem_cog_slope_max_deg` vs `nh04_gee_slope_max_deg` | Three slope measurements from different sources — which is canonical? | Add a comment to `models.py` clarifying: `slope_angle_deg` is the fused/primary value; `dem_cog` is from Copernicus DEM COG; `gee` is from Google Earth Engine. The clear-name scheme disambiguates via source prefix. |
| `nh04_slope_discrepancy` | "Discrepancy" between which values? (CopDEM vs GEE vs fused) | Clear name `SlopeDiscrepancy` is adequate once the cross-source summary explains it. |
| `hv_line_count` | Count within what search radius? | Propose updating the column description in `models.py` to specify the radius (e.g. 50 km). The clear name cannot encode this without being unwieldy. |
| `substation_count` | Same radius ambiguity. | Same recommendation. |
| `military_count` | Same radius ambiguity. | Same recommendation. |
| `transmitter_count` | Same radius ambiguity. | Same recommendation. |
| `airport_count` | Already mapped; same ambiguity. | Same recommendation. |
| `ns04_gee_grading_class` | "Grading" could mean soil grading, terrain grading effort, or slope gradient class. | From context (NS-04 = topography), this is terrain-grading difficulty class. Proposed name `GeeGradingClass` is acceptable if documented. |

---

## 6. Recommendations

### 6.1 Immediate actions (before the next Excel export)

1. **Fix dead key**: Change `liquefaction_susceptibility` → `liquefaction_suscept` in `COLUMN_MAPPINGS`.
2. **Remove dead key**: Delete the `nh03_source` entry (column does not exist in `SiteNaturalHazards`).
3. **Add missing EP-01 columns**: Add `ep01_terrain_score` and `ep01_evacuation_feasible` to `COLUMN_MAPPINGS`.
4. **Add missing NS-01 columns**: Add `water_stress_score`, `water_stress_label` to `COLUMN_MAPPINGS`.

### 6.2 Short-term improvements

5. **Complete `COLUMN_MAPPINGS`**: Add the 116 unmapped columns proposed in §4 above. This brings coverage from 24% (60/251) to 100%.
6. **Fix auto-fallback logic**: Replace the three-rule phase assignment with a per-criterion lookup. The `criteria` DB table already has `phase` and `category` columns that can drive this.
7. **Batch-update phase prefixes**: Correct the 24 existing mappings with wrong PHASE labels (HI-01 EXCL→AVOID, HI-02 EXCL→AVOID, NS-02 RANK→AVOID, NS-03 RANK→AVOID). This should be done as a single batch to avoid breaking partial states.

### 6.3 Documentation improvements

8. **Add search-radius annotations**: For `*_count` columns (airport_count, hv_line_count, substation_count, military_count, transmitter_count), document the search radius used by each connector in a column comment or in the `COLUMN_MAPPINGS` description tuple.
9. **Add source-provenance column comments**: For the triple-slope columns (NH-04) and other multi-source columns, add a one-line comment to `models.py` stating which connector writes each column.

### 6.4 Out of scope (requires user sign-off)

10. **DB column renames**: No DB columns should be renamed without explicit user approval. The clear-naming scheme is applied at export time only (via `export_databases.py --clear-names`). If any column rename is desired, it requires a new Alembic migration.

---

## 7. Summary counts

| Status | Column count | % of total |
| --- | --- | --- |
| Explicitly mapped (correct key) | 60 | 24% |
| Explicitly mapped (dead key) | 2 | 1% |
| Auto-fallback mapped | 75 | 30% |
| — with correct PHASE | 33 | 13% |
| — with wrong PHASE | 42 | 17% |
| Totally unmapped | 116 | 46% |
| **Total** | **251** | **100%** |

| Action type | Count |
| --- | --- |
| Proposed new clear names (needs_approval: Y) | 191 |
| Flagged as cryptic | 16 occurrences across 12 distinct columns |
| Flagged as ambiguous | 7 columns |
| Dead COLUMN_MAPPINGS entries to fix | 2 |
| Existing PHASE labels to correct | 24 |
