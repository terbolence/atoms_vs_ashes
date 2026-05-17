<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — HI-02

Generated at: 2026-05-17T12:32:39.944716+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `nearest_seveso_km` | measured | See workflow doc |
| `nearest_ied_km` | measured | See workflow doc |
| `hi02_quality` | measured | See workflow doc |
| `hi02_search_completed` | derived | See workflow doc |
| `human_run_id` | measured | See workflow doc |
| `human_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `nearest_seveso_km`: nulls 347/362, range 5.24 to 29.49, stdev 9.590188786065733
- `nearest_ied_km`: nulls 362/362, range None to None, stdev None
- `hi02_quality`: nulls 0/362, range None to None, stdev None
- `hi02_search_completed`: nulls 0/362, range 0.0 to 1.0, stdev 0.33658621059299726
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 47/362 (13.0%)
- Candidate stdev: 1.557490266215243, range 5.0 to 9.5

## Band hits (candidate)

- `> 20 km, or completed Seveso search found nothing in radius.`: 309
- `no_band_matched — pass-mark default (unscored)`: 47
- `5-10 km (project A7 pass-mark).`: 4
- `10-20 km.`: 2

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
