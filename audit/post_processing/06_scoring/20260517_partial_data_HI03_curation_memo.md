<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — HI-03

Generated at: 2026-05-17T12:32:39.948817+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `nearest_toxic_source_km` | measured | See workflow doc |
| `toxic_source_type` | measured | See workflow doc |
| `hi03_quality` | measured | See workflow doc |
| `hi03_search_completed` | derived | See workflow doc |
| `human_run_id` | measured | See workflow doc |
| `human_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `nearest_toxic_source_km`: nulls 272/362, range 0.0 to 29.69, stdev 8.367879524725758
- `toxic_source_type`: nulls 362/362, range None to None, stdev None
- `hi03_quality`: nulls 0/362, range None to None, stdev None
- `hi03_search_completed`: nulls 0/362, range 0.0 to 1.0, stdev 0.33658621059299726
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 47/362 (13.0%)
- Candidate stdev: 2.3465717806049864, range 1.5 to 9.5

## Band hits (candidate)

- `> 25 km, or completed toxic-source search found nothing in radius.`: 233
- `no_band_matched — pass-mark default (unscored)`: 47
- `15-25 km.`: 28
- `8-15 km (project A8 pass-mark).`: 23
- `3-8 km.`: 19
- `< 3 km.`: 12

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
