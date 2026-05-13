<!-- man_hours: 0.5 -->
# Phase 4 GATE — please read before approving any DB write

Date: 2026-05-10. Mode: read-only / dry-run only. No DB writes have
been performed. This document is the gate the SP-F log-driven backfill
plan asks you to clear before Phase 5.

## Headline finding (please read first)

**Both connectors propose 0 DB writes** — for HI-01 (ourairports) and
HI-06 (osm military), running the new `replay_ourairports_from_csv.py`
and the extended `replay_osm_military_from_logs.py` against every site
in the database, in either `--only-nulls` (default, non-destructive) or
`--overwrite-with-better` (explicit opt-in) mode, results in:

```
HI-01:  361 sites, 0 writes (830 skip-noop, 253 skip-no-replay)
HI-06:  361 sites, 0 writes (318 skip-noop, 765 skip-no-replay)
```

The offline log-driven pass is therefore *idempotent and inert* against
the current cached state. The data the reviewer asked us to recover
into the SP-F columns (`nearest_airport_runway_length_m`,
`nearest_military_class`, `nearest_high_consequence_military_*`) is
**not present in the cached CSV / DB-stored OSM payloads**. Backfilling
those columns now requires fresh upstream data (a new OurAirports
runway pass and / or a new OSM Overpass call) — and your standing
policy defers all live API calls.

## Gate questions for you

You have three orthogonal decisions:

1. **HI-01 / HI-06 `--only-nulls` write pass.** With 0 proposed writes,
   running it is a true no-op. Permission is **not required** to skip
   Phase 5. **Default proposal: skip Phase 5 for both connectors.**
2. **`--overwrite-with-better` for either connector.** Same dry-run
   forecast (0 writes), same recommendation: **skip**.
3. **Live API re-enrichment** (out of scope for this plan). The 253
   NULL `nearest_airport_runway_length_m` rows and the 255 NULL
   `nearest_military_class` rows can only be filled by a fresh API
   pass, which is explicitly deferred per your policy.

If you confirm the default (skip Phase 5 for both connectors), I will
proceed straight to Phase 6 (closeout) — SP-H backlog rows updated to
record the offline pass as "no writes warranted; live re-run gated".

## Where the evidence lives

| File | Purpose |
|------|---------|
| `audit/post_processing/sp_f_log_replay/hi01_ourairports_audit.md` | Phase 1 read-only audit for HI-01 (rubric → DB → parser → log map; null census; parser-gap report). |
| `audit/post_processing/sp_f_log_replay/hi06_osm_military_audit.md` | Same for HI-06. |
| `audit/post_processing/sp_f_log_replay/phase2_closeout.md` | Phase 2 decision: no parser code changes; the one fixable item that touches scoring (`nearest_military_airfield_km` derivation in `merge_context_derivations.py`) is deferred behind your scoring-impact gate. |
| `audit/post_processing/sp_f_log_replay/hi01_three_site_preview.md` | Per-site dry-run preview for the 3 representative HI-01 sites. |
| `audit/post_processing/sp_f_log_replay/hi06_three_site_summary.json` | Per-site dry-run preview for the 3 representative HI-06 sites (skip-noop demonstrators). |
| `audit/post_processing/sp_f_log_replay/hi01_full_dry_run_summary.json` | Full 361-site `--only-nulls --dry-run` (HI-01). |
| `audit/post_processing/sp_f_log_replay/hi01_full_overwrite_dry_run.json` | Full 361-site `--overwrite-with-better --dry-run` (HI-01). |
| `audit/post_processing/sp_f_log_replay/hi06_full_dry_run_summary.json` | Full 361-site `--only-nulls --dry-run` (HI-06). |
| `audit/post_processing/sp_f_log_replay/hi06_full_overwrite_dry_run.json` | Full 361-site `--overwrite-with-better --dry-run` (HI-06). |

## Why the writes count is 0 — short version

### HI-01 (ourairports)

- All legacy columns are populated for 361/361 sites; the SP-F columns
  `nearest_airport_class` and `nearest_airport_scheduled_service` are
  populated 361/361 too.
- The only NULL is `nearest_airport_runway_length_m` on 253 sites. For
  every one of those 253 sites the recorded `nearest_airport_name`
  resolves to an airport `ident` that **exists** in
  `sources/ourairports/airports.csv` — but **does not exist** in
  `sources/ourairports/runways.csv`. These are heliports, sport
  airfields, and a handful of small/medium fields that genuinely have
  no runway record upstream. A re-parse of the cached CSVs adds zero
  new runway-length values.

### HI-06 (osm military)

- Every site has an OSM raw payload row in `site_raw_responses`.
- 106 sites: payload contains 1+ military element → SP-F class is
  populated → replay matches → skip-noop.
- 255 sites: payload contains 0 military elements (the original
  Overpass call returned an empty list for the radius) → replay
  produces NULL → skip-no-replay.
- The 1:1 correlation (`class IS NULL` ⟺ `log has 0 elements`) is
  perfect across all 361 sites. There are no orphans where a class
  could be recovered from data already in hand.

## What this plan deliberately did NOT do (re-confirmed)

- Did **not** call any external API.
- Did **not** mutate `composite_rankings` or trigger `score run` /
  `score sensitivity` (GUI-only per your policy).
- Did **not** touch the legacy HI-01 / HI-06 columns.
- Did **not** edit the canonical plan at
  `/Users/terbolence/.cursor/plans/feedback_rework_execution_ff6b91ad.plan.md`.

## Sign-off

Tick one:

- [ ] **Default (skip Phase 5 for both connectors).** I'll proceed to
  Phase 6 — SP-H backlog rows updated, audit conversation appended,
  man-hours regenerated. No DB writes will happen.
- [ ] **Run HI-01 `--only-nulls` anyway** (0 writes expected; harmless
  but pointless).
- [ ] **Run HI-06 `--only-nulls` anyway** (same).
- [ ] **Run HI-01 `--overwrite-with-better`** (0 writes expected).
- [ ] **Run HI-06 `--overwrite-with-better`** (0 writes expected).
- [ ] **Open the live-API consent gate for re-enrichment** (separate
  conversation; out of scope for this plan).
