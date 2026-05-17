<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — NH-09

Generated at: 2026-05-17T12:32:39.963745+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `nearest_river_km` | measured | See workflow doc |
| `river_distance_km` | derived | See workflow doc |
| `flood_zone_class` | measured | See workflow doc |
| `flood_zone_class_500yr` | derived | See workflow doc |
| `elevation_above_design_flood_m` | measured | See workflow doc |
| `natural_run_id` | measured | See workflow doc |
| `natural_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `nearest_river_km`: nulls 349/362, range 0.0 to 0.0, stdev 0.0
- `river_distance_km`: nulls 349/362, range 0.0 to 0.0, stdev 0.0
- `flood_zone_class`: nulls 0/362, range None to None, stdev None
- `flood_zone_class_500yr`: nulls 0/362, range None to None, stdev None
- `elevation_above_design_flood_m`: nulls 362/362, range None to None, stdev None
- `natural_run_id`: nulls 0/362, range None to None, stdev None
- `natural_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 13/362 (3.6%)
- Candidate stdev: 0.4658182635183631, range 5.0 to 7.5

## Band hits (candidate)

- `Low flood-zone class OR >= 4-6 km river separation; meets project A11.`: 349
- `no_band_matched — pass-mark default (unscored)`: 13

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
