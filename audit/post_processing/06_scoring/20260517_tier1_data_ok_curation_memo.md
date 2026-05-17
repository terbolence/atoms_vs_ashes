<!-- man_hours: 1.0 -->
# Tier 1 Data OK Curation Memo

Generated at: 2026-05-17T12:31:43.022159+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_tier1_data_ok_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_tier1_data_ok_summary.csv`

This is a read-only audit. It evaluates working-tree scoring logic in memory and does not write DB rows.

## HI-07

- Rows reviewed: 362
- `transmitter_count`: nulls 1/362, range 3.0 to 968.0, stdev 137.62704201259413
- `nearest_transmitter_km`: nulls 1/362, range 0.0 to 17.92, stdev 2.9217313272967718
- `transmitter_type`: nulls 1/362, range None to None, stdev None
- `hi07_quality`: nulls 1/362, range None to None, stdev None
- `hi07_comment`: nulls 1/362, range None to None, stdev None
- `human_run_id`: nulls 0/362, range None to None, stdev None
- `human_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 1/362, stdev 1.5605358899970945, range 1.5 to 9.5
- Field classification: see `experts/quality/data_science_siting_curator.md` curation format.

## NH-10

- Rows reviewed: 362
- `max_wind_speed_ms`: nulls 0/362, range 5.41 to 14.44, stdev 1.810845531217882
- `nh10_quality`: nulls 0/362, range None to None, stdev None
- `nh10_comment`: nulls 0/362, range None to None, stdev None
- `natural_run_id`: nulls 0/362, range None to None, stdev None
- `natural_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 0/362, stdev 2.288105429183464, range 1.5 to 9.5
- Field classification: see `experts/quality/data_science_siting_curator.md` curation format.

## NH-12

- Rows reviewed: 362
- `extreme_temp_max_c`: nulls 0/362, range 19.54 to 33.32, stdev 2.77930233299586
- `extreme_temp_min_c`: nulls 0/362, range -12.29 to 7.93, stdev 5.184267150600822
- `nh12_quality`: nulls 0/362, range None to None, stdev None
- `nh12_comment`: nulls 0/362, range None to None, stdev None
- `natural_run_id`: nulls 0/362, range None to None, stdev None
- `natural_fetched_at`: nulls 0/362, range None to None, stdev None
- Baseline ranking rows found: 0/362
- Candidate scores: unscored 0/362, stdev 0.7962969652835877, range 3.5 to 8.5
- Field classification: see `experts/quality/data_science_siting_curator.md` curation format.
