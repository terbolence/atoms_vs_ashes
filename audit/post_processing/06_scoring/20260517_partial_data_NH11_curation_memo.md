<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — NH-11

Generated at: 2026-05-17T12:32:39.973591+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `spi12_min` | measured | See workflow doc |
| `snow_months_per_year` | measured | See workflow doc |
| `mean_annual_precip_mm` | measured | See workflow doc |
| `mean_annual_precip_corrected_mm` | derived | See workflow doc |
| `extreme_precip_mm` | measured | See workflow doc |
| `extreme_precip_corrected_mm` | derived | See workflow doc |
| `freezing_days_per_year` | measured | See workflow doc |
| `natural_run_id` | measured | See workflow doc |
| `natural_fetched_at` | measured | See workflow doc |

## Distribution

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
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 0/362 (0.0%)
- Candidate stdev: 1.4555966384603052, range 2.0 to 10.0

## Band hits (candidate)

- `aggregated(mean_of_sub_scores)`: 362

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
