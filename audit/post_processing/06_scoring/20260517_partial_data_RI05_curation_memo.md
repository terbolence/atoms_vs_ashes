<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — RI-05

Generated at: 2026-05-17T12:32:39.986995+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `nearest_city_50k_km` | measured | See workflow doc |
| `nearest_city_pop` | measured | See workflow doc |
| `pop_density_16km` | measured | See workflow doc |
| `pop_total_16km` | measured | See workflow doc |
| `ri05_required_distance_km` | derived | See workflow doc |
| `ri05_distance_margin_pct` | derived | See workflow doc |
| `ri05_quality` | measured | See workflow doc |
| `ri05_comment` | measured | See workflow doc |
| `radiological_run_id` | measured | See workflow doc |
| `radiological_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `nearest_city_50k_km`: nulls 198/362, range 0.63 to 97.01, stdev 22.35709191692302
- `nearest_city_pop`: nulls 0/362, range 0.0 to 2580574.0, stdev 297114.17001499265
- `pop_density_16km`: nulls 0/362, range 1.85 to 3209.0, stdev 414.0541735381743
- `pop_total_16km`: nulls 0/362, range 1489.0 to 2580574.0, stdev 332968.6970613527
- `ri05_required_distance_km`: nulls 73/362, range 8.0 to 48.0, stdev 7.5114164039610225
- `ri05_distance_margin_pct`: nulls 198/362, range -96.667 to 1112.625, stdev 205.02711794830262
- `ri05_quality`: nulls 0/362, range None to None, stdev None
- `ri05_comment`: nulls 0/362, range None to None, stdev None
- `radiological_run_id`: nulls 0/362, range None to None, stdev None
- `radiological_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 125/362 (34.5%)
- Candidate stdev: 3.1072450193820056, range 0.0 to 9.5

## Band hits (candidate)

- `no_band_matched — pass-mark default (unscored)`: 125
- `Nearest >=50k population-centre proxy exceeds required distance by >= 50 %.`: 75
- `No >=50k population-centre proxy within screening envelope.`: 73
- `Nearest >=50k population-centre proxy misses required distance by > 25 %.`: 69
- `Nearest >=50k population-centre proxy meets required distance (pass mark).`: 6
- `Nearest >=50k population-centre proxy misses required distance by <= 25 %.`: 6
- `Nearest >=50k population-centre proxy exceeds required distance by 25-50 %.`: 5
- `Site embedded within 5 km of a >1M population centre.`: 3

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
