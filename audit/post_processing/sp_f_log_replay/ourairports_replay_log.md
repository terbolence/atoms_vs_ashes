<!-- man_hours: 0.1 -->
# HI-01 / OurAirports — replay log

Per-pass DB-write log for `src/scripts/replay_ourairports_from_csv.py`.
Each pass appends a row.

## 2026-05-10 (Phase 4 dry-run forecast; Phase 5 gate decision)

| Field | Value |
|-------|-------|
| Mode  | `--only-nulls` and `--overwrite-with-better` both surveyed in `--dry-run`. |
| Sites considered | 361 (full DB) |
| Decisions       | `skip-noop=830`, `skip-no-replay=253`, `write-null=0`, `overwrite=0`, `skip-nonnull=0` |
| Rows with writes | **0** (all three SP-F columns either match the DB or have no replayed value) |
| DB writes committed | **0** (Phase 5 not invoked because dry-run shows no writes warranted) |
| Source files    | `sources/ourairports/airports.csv` (12.6 MB, mtime 2026-04-21), `sources/ourairports/runways.csv` (3.94 MB, mtime 2026-05-09) |
| Reason for 0 writes | The 253 NULL `nearest_airport_runway_length_m` are sites whose nearest airport is a heliport / sport airfield / small field with no runway record in `runways.csv` — genuine upstream gap, not a parser bug. |
| Next action | Wait on user gate. Live OurAirports re-enrichment (deferred per project policy) is the only path to populate the missing 253 runway lengths. |
| Run command | `PYTHONPATH=src .venv/bin/python src/scripts/replay_ourairports_from_csv.py --dry-run --only-nulls --json-summary audit/post_processing/sp_f_log_replay/hi01_full_dry_run_summary.json` |
| Operator | `agent` (offline replay; no live HTTP) |
