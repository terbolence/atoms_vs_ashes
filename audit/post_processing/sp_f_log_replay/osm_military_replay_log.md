<!-- man_hours: 0.1 -->
# HI-06 / OSM military — replay log

Per-pass DB-write log for `src/scripts/replay_osm_military_from_logs.py`.
Each pass appends a row.

## 2026-05-10 (Phase 4 dry-run forecast; Phase 5 gate decision)

| Field | Value |
|-------|-------|
| Mode  | `--only-nulls` and `--overwrite-with-better` both surveyed in `--dry-run`. |
| Sites considered | 361 (full DB) |
| With logged military payload | 361 |
| With NULL `nearest_military_class` AND log has 0 elements | 255 (perfect 1:1 correlation; nothing to recover) |
| With populated class AND log has 1+ elements | 106 (replay matches DB → skip-noop) |
| `with_high_consequence` | 37 (already populated in DB; replay matches) |
| Rows with writes | **0** (255 sites have empty payloads; 106 sites already match) |
| DB writes committed | **0** (Phase 5 not invoked because dry-run shows no writes warranted) |
| Source           | `site_raw_responses WHERE connector_slug = 'osm'` (DB JSONB; 361 rows) |
| Reason for 0 writes | Every NULL SP-F class corresponds to a logged OSM payload that already had 0 military elements at the time of the original Overpass call. The information needed to populate the 255 NULL `nearest_military_class` rows was never in the log to begin with. |
| Next action | Wait on user gate. Live OSM Overpass re-enrichment (deferred per project policy) is the only path to populate the missing 255 SP-F class values and the 324 NULL `nearest_high_consequence_military_*` columns. |
| Run command | `PYTHONPATH=src .venv/bin/python src/scripts/replay_osm_military_from_logs.py --dry-run --only-nulls --json-summary audit/post_processing/sp_f_log_replay/hi06_full_dry_run_summary.json` |
| Operator | `agent` (offline replay; no live HTTP) |
