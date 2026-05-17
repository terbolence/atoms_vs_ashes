<!-- man_hours: 1.2 -->
# Partial Data Curation Memo — EP-03

Generated at: 2026-05-17T12:32:39.933579+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_partial_data_summary.csv`

Read-only audit of working-tree scoring logic. No DB writes.

## Operational closure update — no GEE access

The user confirmed on 2026-05-17 that this environment does not have Google
Earth Engine access. The measured relief component of EP-03 is therefore
closed/deferred for this pass rather than force-filled. Treat
`ep03_gee_relief_16km_m` as unavailable cohort data until IMP-0012 lands a
non-GEE relief source. An interrupted Copernicus DEM workaround produced only
partial rows; those partial numeric relief values were cleared so they cannot
affect a GUI scoring run.

## Field classification

| Field | Class | Notes |
| --- | --- | --- |
| `major_river_barrier` | measured | See workflow doc |
| `waterway_count_epz` | measured | See workflow doc |
| `ep03_gee_relief_16km_m` | measured | See workflow doc |
| `relief_m_per_10km` | derived | See workflow doc |
| `ep03_quality` | measured | See workflow doc |
| `ep03_comment` | measured | See workflow doc |
| `emergency_run_id` | measured | See workflow doc |
| `emergency_fetched_at` | measured | See workflow doc |

## Distribution

- Rows reviewed: 362
- `major_river_barrier`: nulls 0/362, range 0.0 to 1.0, stdev 0.36211527133731086
- `waterway_count_epz`: nulls 0/362, range 0.0 to 566.0, stdev 62.10076652885229
- `ep03_gee_relief_16km_m`: nulls 362/362, range None to None, stdev None
- `relief_m_per_10km`: nulls 362/362, range None to None, stdev None
- `ep03_quality`: nulls 0/362, range None to None, stdev None
- `ep03_comment`: nulls 0/362, range None to None, stdev None
- `emergency_run_id`: nulls 0/362, range None to None, stdev None
- `emergency_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 0/362 (0.0%)
- Candidate stdev: 2.8888014436142515, range 1.5 to 9.5

## Band hits (candidate)

- `No measured relief; open river/waterway context (interim screening).`: 305
- `No measured relief; major river barrier (interim).`: 55
- `No measured relief; major river barrier with limited crossings (interim).`: 1
- `No measured relief; manageable barrier/waterway context (interim).`: 1

Approve implementation for this criterion? (User gate — Wave 2 implemented in coordinator session.)
