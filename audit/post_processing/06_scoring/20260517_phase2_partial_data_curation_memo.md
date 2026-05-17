<!-- man_hours: 1.0 -->
# Phase 2 Partial Data Curation Memo

Generated at: 2026-05-17T12:40:07.050581+00:00

Coverage: `audit/post_processing/06_scoring/20260517_phase2_data_coverage_report.md`
Detail CSV: `audit/post_processing/06_scoring/20260517_phase2_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_phase2_partial_data_summary.csv`

Read-only audit of working-tree scoring logic; no DB writes.

## EP-03

- Rows reviewed: 362
- `relief_m_per_10km`: nulls 362/362, range None to None, stdev None
- `ep03_gee_relief_16km_m`: nulls 362/362, range None to None, stdev None
- `major_river_barrier`: nulls 0/362, range 0.0 to 1.0, stdev 0.36211527133731086
- `waterway_count_epz`: nulls 0/362, range 0.0 to 566.0, stdev 62.10076652885229
- `ep03_quality`: nulls 0/362, range None to None, stdev None
- `emergency_run_id`: nulls 0/362, range None to None, stdev None
- `emergency_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 2.8888014436142515, range 1.5 to 9.5
- Verdict: scoreable_with_derivation · class B

## HI-02

- Rows reviewed: 362
- `nearest_seveso_km`: nulls 347/362, range 5.24 to 29.49, stdev 9.590188786065733
- `nearest_ied_km`: nulls 362/362, range None to None, stdev None
- `hi02_quality`: nulls 0/362, range None to None, stdev None
- `hi02_search_completed`: nulls 0/362, range 1.0 to 1.0, stdev 0.0
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 0.4431536055059004, range 5.5 to 9.5
- Verdict: scoreable_with_sentinel · class A

## HI-03

- Rows reviewed: 362
- `nearest_toxic_source_km`: nulls 272/362, range 0.0 to 29.69, stdev 8.367879524725758
- `toxic_source_type`: nulls 362/362, range None to None, stdev None
- `hi03_quality`: nulls 0/362, range None to None, stdev None
- `hi03_search_completed`: nulls 0/362, range 1.0 to 1.0, stdev 0.0
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 2.090710094949036, range 1.5 to 9.5
- Verdict: scoreable_with_sentinel · class A

## HI-04

- Rows reviewed: 362
- `nearest_flammable_storage_km`: nulls 347/362, range 5.24 to 29.49, stdev 9.590188786065733
- `nearest_pipeline_km`: nulls 362/362, range None to None, stdev None
- `hi04_quality`: nulls 0/362, range None to None, stdev None
- `hi04_search_completed`: nulls 0/362, range 1.0 to 1.0, stdev 0.0
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 0.4431536055059004, range 5.5 to 9.5
- Verdict: scoreable_with_sentinel · class A

## NH-09

- Rows reviewed: 362
- `river_distance_km`: nulls 362/362, range None to None, stdev None
- `nearest_river_km`: nulls 349/362, range 0.0 to 0.0, stdev 0.0
- `flood_zone_class_500yr`: nulls 0/362, range None to None, stdev None
- `flood_zone_class`: nulls 0/362, range None to None, stdev None
- `elevation_above_design_flood_m`: nulls 362/362, range None to None, stdev None
- `natural_run_id`: nulls 0/362, range None to None, stdev None
- `natural_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 0.3726546108146904, range 5.5 to 7.5
- Verdict: scoreable_with_derivation · class A

## NH-11

- Rows reviewed: 362
- `spi12_min`: nulls 362/362, range None to None, stdev None
- `snow_months_per_year`: nulls 362/362, range None to None, stdev None
- `mean_annual_precip_mm`: nulls 0/362, range 8.64 to 66.44, stdev 6.997804870272018
- `mean_annual_precip_corrected_mm`: nulls 0/362, range 262.656 to 2019.7759999999998, stdev 212.73326805626934
- `extreme_precip_mm`: nulls 0/362, range 0.11 to 0.82, stdev 0.08701079776368446
- `extreme_precip_corrected_mm`: nulls 0/362, range 3.344 to 24.927999999999997, stdev 2.6451282520160073
- `freezing_days_per_year`: nulls 362/362, range None to None, stdev None
- `natural_run_id`: nulls 0/362, range None to None, stdev None
- `natural_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 1.4555966384603052, range 2.0 to 10.0
- Verdict: scoreable_with_partial_metrics · class B

## RI-03

- Rows reviewed: 362
- `aquifer_type`: nulls 2/362, range None to None, stdev None
- `ri03_aquifer_screening_class`: nulls 2/362, range None to None, stdev None
- `groundwater_vulnerability_class`: nulls 362/362, range None to None, stdev None
- `ri03_quality`: nulls 0/362, range None to None, stdev None
- `radiological_run_id`: nulls 0/362, range None to None, stdev None
- `radiological_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 2/362, stdev 1.2722484752574381, range 1.5 to 7.5
- Verdict: scoreable_with_derivation · class A

## RI-05

- Rows reviewed: 362
- `nearest_city_50k_km`: nulls 198/362, range 0.63 to 97.01, stdev 22.35709191692302
- `nearest_city_pop`: nulls 198/362, range 53848.0 to 2131034.0, stdev 315476.6490068151
- `pop_density_16km`: nulls 0/362, range 1.85 to 3209.0, stdev 414.0541735381743
- `pop_total_16km`: nulls 0/362, range 1489.0 to 2580574.0, stdev 332968.6970613527
- `ri05_required_distance_km`: nulls 73/362, range 8.0 to 48.0, stdev 7.5114164039610225
- `ri05_distance_margin_pct`: nulls 198/362, range -96.667 to 1112.625, stdev 205.02711794830262
- `radiological_run_id`: nulls 0/362, range None to None, stdev None
- `radiological_fetched_at`: nulls 0/362, range None to None, stdev None
- Candidate scores: unscored 0/362, stdev 3.3245075367559815, range 0.0 to 9.5
- Verdict: scoreable_with_derivation · class B
