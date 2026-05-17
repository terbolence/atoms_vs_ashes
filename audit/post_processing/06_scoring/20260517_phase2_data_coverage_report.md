<!-- man_hours: 1.5 -->
# Phase 2 Partial Data Coverage Report

Generated at: 2026-05-17T12:40:06.938234+00:00

Baseline run: `20260517T104618_459ae424` · SMR: `nuscale_voygr6`

Read-only cohort fill for Bucket C criteria. Verdicts gate band work per
`criteria/tier2_partial_data_parallel_workflows.md`.

## EP-03

- Cohort rows: **362**
- `relief_m_per_10km`: 0.0% fill (0/362)
- `ep03_gee_relief_16km_m`: 0.0% fill (0/362)
- `major_river_barrier`: 100.0% fill (362/362)
- `waterway_count_epz`: 100.0% fill (362/362)
- `ep03_quality`: 100.0% fill (362/362)
- `emergency_run_id`: 100.0% fill (362/362)
- `emergency_fetched_at`: 100.0% fill (362/362)
- `ep03_quality` distribution: medium=362
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **2.8888014436142515**
- **Verdict:** `scoreable_with_derivation`
- **Remediation class:** `B`

## HI-02

- Cohort rows: **362**
- `nearest_seveso_km`: 4.1% fill (15/362)
- `nearest_ied_km`: 0.0% fill (0/362)
- `hi02_quality`: 100.0% fill (362/362)
- `hi02_search_completed`: 100.0% fill (362/362)
- `human_run_id`: 100.0% fill (362/362)
- `human_fetched_at`: 100.0% fill (362/362)
- `hi02_quality` distribution: low=153, high=94, medium=68, not_applicable=47
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **0.4431536055059004**
- **Verdict:** `scoreable_with_sentinel`
- **Remediation class:** `A`

## HI-03

- Cohort rows: **362**
- `nearest_toxic_source_km`: 24.9% fill (90/362)
- `toxic_source_type`: 0.0% fill (0/362)
- `hi03_quality`: 100.0% fill (362/362)
- `hi03_search_completed`: 100.0% fill (362/362)
- `human_run_id`: 100.0% fill (362/362)
- `human_fetched_at`: 100.0% fill (362/362)
- `hi03_quality` distribution: low=153, high=94, medium=68, not_applicable=47
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **2.090710094949036**
- **Verdict:** `scoreable_with_sentinel`
- **Remediation class:** `A`

## HI-04

- Cohort rows: **362**
- `nearest_flammable_storage_km`: 4.1% fill (15/362)
- `nearest_pipeline_km`: 0.0% fill (0/362)
- `hi04_quality`: 100.0% fill (362/362)
- `hi04_search_completed`: 100.0% fill (362/362)
- `human_run_id`: 100.0% fill (362/362)
- `human_fetched_at`: 100.0% fill (362/362)
- `hi04_quality` distribution: low=153, high=94, medium=68, not_applicable=47
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **0.4431536055059004**
- **Verdict:** `scoreable_with_sentinel`
- **Remediation class:** `A`

## NH-09

- Cohort rows: **362**
- `river_distance_km`: 0.0% fill (0/362)
- `nearest_river_km`: 3.6% fill (13/362)
- `flood_zone_class_500yr`: 100.0% fill (362/362)
- `flood_zone_class`: 100.0% fill (362/362)
- `elevation_above_design_flood_m`: 0.0% fill (0/362)
- `natural_run_id`: 100.0% fill (362/362)
- `natural_fetched_at`: 100.0% fill (362/362)
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **0.3726546108146904**
- **Verdict:** `scoreable_with_derivation`
- **Remediation class:** `A`

## NH-11

- Cohort rows: **362**
- `spi12_min`: 0.0% fill (0/362)
- `snow_months_per_year`: 0.0% fill (0/362)
- `mean_annual_precip_mm`: 100.0% fill (362/362)
- `mean_annual_precip_corrected_mm`: 100.0% fill (362/362)
- `extreme_precip_mm`: 100.0% fill (362/362)
- `extreme_precip_corrected_mm`: 100.0% fill (362/362)
- `freezing_days_per_year`: 0.0% fill (0/362)
- `natural_run_id`: 100.0% fill (362/362)
- `natural_fetched_at`: 100.0% fill (362/362)
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **1.4555966384603052**
- **Verdict:** `scoreable_with_partial_metrics`
- **Remediation class:** `B`

## RI-03

- Cohort rows: **362**
- `aquifer_type`: 99.4% fill (360/362)
- `ri03_aquifer_screening_class`: 99.4% fill (360/362)
- `groundwater_vulnerability_class`: 0.0% fill (0/362)
- `ri03_quality`: 100.0% fill (362/362)
- `radiological_run_id`: 100.0% fill (362/362)
- `radiological_fetched_at`: 100.0% fill (362/362)
- `ri03_quality` distribution: medium=360, low=2
- Candidate unscored: **2/362** (0.6%)
- Candidate score stdev: **1.2722484752574381**
- **Verdict:** `scoreable_with_derivation`
- **Remediation class:** `A`

## RI-05

- Cohort rows: **362**
- `nearest_city_50k_km`: 45.3% fill (164/362)
- `nearest_city_pop`: 45.3% fill (164/362)
- `pop_density_16km`: 100.0% fill (362/362)
- `pop_total_16km`: 100.0% fill (362/362)
- `ri05_required_distance_km`: 79.8% fill (289/362)
- `ri05_distance_margin_pct`: 45.3% fill (164/362)
- `radiological_run_id`: 100.0% fill (362/362)
- `radiological_fetched_at`: 100.0% fill (362/362)
- Candidate unscored: **0/362** (0.0%)
- Candidate score stdev: **3.3245075367559815**
- **Verdict:** `scoreable_with_derivation`
- **Remediation class:** `B`

