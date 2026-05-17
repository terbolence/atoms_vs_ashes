<!-- man_hours: 1.0 -->
# Partial Data Curation Memo — RI-03

Generated at: 2026-05-17T12:32:39.981989+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `aquifer_type` | measured | See workflow doc |
| `ri03_aquifer_screening_class` | derived | See workflow doc |
| `groundwater_vulnerability_class` | measured | See workflow doc |
| `ri03_quality` | measured | See workflow doc |
| `ri03_comment` | measured | See workflow doc |
| `radiological_run_id` | measured | See workflow doc |
| `radiological_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `aquifer_type`: nulls 2/362, range None to None, stdev None
- `ri03_aquifer_screening_class`: nulls 2/362, range None to None, stdev None
- `groundwater_vulnerability_class`: nulls 362/362, range None to None, stdev None
- `ri03_quality`: nulls 0/362, range None to None, stdev None
- `ri03_comment`: nulls 362/362, range None to None, stdev None
- `radiological_run_id`: nulls 0/362, range None to None, stdev None
- `radiological_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 2/362 (0.6%)
- Candidate stdev: 1.2722484752574381, range 1.5 to 7.5

## Band hits (candidate)

- `Moderate-permeability aquifer screening proxy.`: 258
- `Low-permeability aquifer screening proxy.`: 85
- `Karst aquifer screening proxy.`: 17
- `no_band_matched — pass-mark default (unscored)`: 2

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
