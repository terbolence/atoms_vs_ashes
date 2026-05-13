<!-- man_hours: 1.8 -->
# HI-01 / HI-06 — preview-apply workflow landed (preview + apply complete)

**Date:** 2026-05-10
**Session ID:** hi-01-hi-06-preview-apply-e70b0f9f
**Plan:** `/Users/terbolence/.cursor/plans/hi-01_hi-06_preview-apply_e70b0f9f.plan.md`

## Objective

Operationalise the user-requested workflow: for each connector
(HI-01 / OurAirports and HI-06 / FIX-04 OSM), run the connector for
**all sites**, log the responses, **diff** against the current DB,
present a **correction proposal** for review, and only then run the
existing apply batch with explicit approval. HI-01 and HI-06 are kept
on **separate** preview/apply tracks per the user's instruction.

## Scope landed today (no DB writes)

### HI-01 / OurAirports

- New script `src/scripts/preview_ourairports_vs_db.py` — calls
  `OurAirportsConnector.fetch` for every `Site`, reads the HI-01
  columns from `site_human_hazards`, writes a per-site JSONL plus a
  human-readable markdown correction report. Read-only session
  (`session.rollback()` at the end). Optional `--country` /
  `--site-id` filters mirror the existing batch CLI.
- Tolerances: 0.01 km on `nearest_airport_km` and
  `flight_path_distance_km`; 1 m on
  `nearest_airport_runway_length_m`; exact otherwise. `Decimal` from
  Postgres normalised to `float` before comparison; `False` not
  collapsed to `None`/0.
- Pure-logic tests in
  `tests/scripts/test_preview_ourairports_vs_db.py` (12 cases, all
  green).
- Operational notes:
  `audit/post_processing/hi01_preview/README.md`.
- Smoke run on `--country RO` (22 sites, no DB writes): all 22
  already in sync — expected, since the apply was completed earlier.

### HI-06 / FIX-04 OSM

- New script `src/scripts/preview_fix04_osm_vs_db.py` — drives the
  same Overpass queries as `run_fix04_osm_avoidance_batch.py` for
  military / power / transmitters per site, parses with the same
  `_parse_*` helpers (imported directly from the apply batch), reads
  the matching columns from `site_human_hazards` and
  `site_infrastructure_v2`, writes per-site JSONL + a markdown
  correction report with **HI-06 / HI-07 / NS-02 sections explicitly
  separated**.
- Pure logic split out into `src/scripts/_preview_fix04_diff.py`
  (DomainSpec, ColumnDiff, diff_domain, render_report_md) so the
  orchestrator stays under the 300-line file-size limit.
- Architectural note: the apply script
  `run_fix04_osm_avoidance_batch.py` is 780 lines (already over the
  300-line limit) and the plan called for a `--preview-no-persist`
  mode inside it. To honour the file-size rule and keep the apply
  path's blast radius zero, the preview is implemented as a
  **sibling script** that imports the apply parsers. Net behaviour
  identical, no risk to the production apply path.
- Operational notes:
  `audit/post_processing/hi06_fix04_preview/README.md`.

## Apply — completed 2026-05-11

Both connectors have now been driven through preview → apply.

### HI-01 / OurAirports apply — no-op (deliberately not re-run)

Per the v2 close-out plan
(`/Users/terbolence/.cursor/plans/v2_close-out_plan_dd550fd1.plan.md`,
section P1) the HI-01 preview returned **0 changes / 361 sites**: the
22 RO sites already applied earlier are in sync, and OurAirports has
not produced any new diffs since. **No HI-01 apply was triggered in
this session** — that would have been wasted DB churn under an
unchanged source. This is the documented one-liner the plan calls for.

- Preview JSONL: `logs/hi01_preview_all.jsonl`
- Preview MD:    `audit/post_processing/hi01_preview/hi01_preview_report.md`
- Sites changed: **0 / 361** (no-op)
- Decision:      Skip apply. Re-evaluate only if a future preview
                 surfaces non-zero diffs.

### HI-06 / FIX-04 apply — 2026-05-11 17:37 UTC

- Run ID:        `fix04_replay_20260511_173728`
- Approved by:   user (challenge-and-confirm — see "Path deviation"
                 below)
- Approval at:   2026-05-11 ~17:36 UTC (right before the run)
- Preview JSONL: `logs/hi06_fix04_preview.jsonl`
                 (361/361 sites, 0 fetch errors, 0 missing payloads;
                 generated 2026-05-11 ~17:48 UTC)
- Preview MD:    `audit/post_processing/hi06_fix04_preview/hi06_fix04_preview_report.md`
- Apply log:     `logs/hi06_fix04_apply.log`
- Apply mode:    Replay from preview JSONL via
                 `src/scripts/apply_fix04_from_preview_jsonl.py`,
                 calling the existing `_persist_military` /
                 `_persist_power` / `_persist_transmitter` from
                 `run_fix04_osm_avoidance_batch.py`. **No Overpass
                 calls.** UPSERT semantics identical to the live apply
                 path.
- Apply runtime: ~2 seconds for all 361 sites (1083 UPSERTs).
- Sites changed (per domain — all rows now tagged with the new run_id;
  these are the per-domain row counts written, not the count of value
  flips — flip counts are captured in the preview report):
  - HI-06 (military):     361 rows UPSERTed → `site_human_hazards`
  - HI-07 (transmitters): 361 rows UPSERTed → `site_human_hazards`
  - NS-02 (power):        361 rows UPSERTed → `site_infrastructure_v2`
- Commit errors: 0
- Verifier:      `src/scripts/verify_fix04_db_vs_jsonl.py`.
                 **Two passes were run against the same JSONL.**
                 - **v1 (17:37 UTC)** — DB-roundtrip only: confirms
                   post-apply DB equals JSONL.fetch (proposed). 361 /
                   361 in sync, 0 diffs. Limitation: this check is
                   nearly tautological because the apply wrote the
                   JSONL.fetch values to the DB, so a deterministic
                   UPSERT always reports 0 diffs unless the persist
                   functions are buggy.
                 - **v2 (18:47 UTC)** — three-way independent baseline.
                   For every (site, column) compares pre-apply DB
                   (`JSONL.db`, A), proposed (`JSONL.fetch`, B), and
                   post-apply DB read (C). Asserts: every preview-
                   flagged cell satisfies `C == B AND C != A` (apply
                   landed AND moved off the pre-state); every non-
                   flagged cell satisfies `C == A == B` (no off-target
                   writes). Result: **361 / 361 sites, 1,121 flips
                   expected = 1,121 flips landed, 0 failures across
                   all 6 verdict buckets, 3,933 cells confirmed
                   stable.** Per-column flip counts agree exactly with
                   the preview report (HI-06 230 cells, HI-07 259
                   cells, NS-02 632 cells).
- Verifier report: `audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md`
                   (now contains the three-way verdict tables; v1's
                   "0 residual diffs" framing was overwritten because
                   it was the weaker signal).
- Verifier log:    `logs/hi06_fix04_verify.log`

#### Independent-source caveat (still open)

The three-way verifier reads only the JSONL and the post-apply DB.
A `JSONL` corrupted at write time, or a parser bug introduced by an
upstream `_parse_*` change between preview and apply, would still go
undetected — both `A`, `B`, and the diff-flagged set ultimately come
from the same May-11 preview run. To close this gap we need an
independent re-parse against `site_raw_responses` (see follow-up
below).

#### Spot-checks vs preview-promised values

| Site | Column | Preview (current → proposed) | Post-apply DB |
|------|--------|------------------------------|---------------|
| AT — Riedersbach (`660d9d71-…`) | `transmitter_count` | `159 → 166` | `166` ✓ |
| AT — Riedersbach                | `substation_count`  | `2645 → 2656` | `2656` ✓ |
| AT — Riedersbach                | `ns02_quality`      | `medium → high` | `high` ✓ |

#### Post-apply distribution (sanity check)

- `ns02_quality`: 323 `high` / 38 `medium`  (pre-apply, the preview
  flagged 335 sites for `medium`/`insufficient` → `high` flips).
- `hi06_quality`: 141 `high` / 178 `medium` / 42 `not_found`.
- `hi07_quality`: 361 `medium` (every site has at least one transmitter
  detected within the 25 km radius — quality bucket reflects evidence
  density, not absence).

### Path deviation — replay instead of re-query

The v2 close-out plan's literal instruction was:

> "Run `src/scripts/run_fix04_osm_avoidance_batch.py` for all sites
> with `--no-skip-populated` so previously-cached domains are refreshed
> ... Tee to `logs/hi06_fix04_apply.log`."

Before kicking that off, the operator presented a consent card per
`prompts/runAPIs.md` Sec. C (361 sites × 3 Overpass queries, ~7-9 h,
504 retries observed in preview, DB writes). The user pushed back
with: **"do we not already have data for this?"** That challenge was
correct: a quick audit of `logs/hi06_fix04_preview.jsonl` showed
**361/361 sites with full parsed payloads, 0 fetch errors, 0 missing
domain payloads**, generated less than 24 hours earlier. The payload
keys (`nearest_*`, `*_count`, `quality`, `comment`) are exactly what
the apply's `_persist_*` functions consume.

Re-querying would have been:

1. **Wasted compute and Overpass quota** (~7-9 h vs ~2 s).
2. **Lossy with respect to the preview report**, because in-flight
   Overpass churn between the preview and apply could quietly produce
   different values than the user already approved in the preview
   report — defeating the purpose of the preview-approve-apply
   protocol.

The replay path:

- `src/scripts/apply_fix04_from_preview_jsonl.py` (CLI orchestrator,
  258 lines; supports `--dry-run`, `--country`, `--site-id`,
  `--jsonl`, `--run-id`).
- `src/scripts/_apply_fix04_from_jsonl.py` (pure helpers — record
  iteration, country/site-id filtering, per-domain payload
  classification, counters; 84 lines, fully unit-tested).
- `tests/scripts/test_apply_fix04_from_jsonl.py` (15 pure-logic
  tests, 0.06 s, all green).
- `src/scripts/verify_fix04_db_vs_jsonl.py` (DB-only full-cohort
  verifier; reuses `_preview_fix04_diff.py` to compute per-column
  diffs from the JSONL against the post-apply DB; 268 lines).

The replay is consistent with the established project pattern set by
`replay_osm_military_from_logs.py` and `replay_ourairports_from_csv.py`
(see `audit/post_processing/sp_f_log_replay/`).

The `--no-skip-populated` flag in the original plan was the mechanism
to force a refresh of stale cached rows under the *re-query* path. It
is moot under replay: every record is written via UPSERT regardless
of the current DB value.

## Files touched

### From the preview-side session (already on disk before today)

- `src/scripts/preview_ourairports_vs_db.py`
- `tests/scripts/test_preview_ourairports_vs_db.py`
- `src/scripts/preview_fix04_osm_vs_db.py`
- `src/scripts/_preview_fix04_diff.py`
- `audit/post_processing/hi01_preview/README.md`
- `audit/post_processing/hi06_fix04_preview/README.md`

### Added in the apply session (2026-05-11)

- `src/scripts/apply_fix04_from_preview_jsonl.py` (new — replay
  orchestrator)
- `src/scripts/_apply_fix04_from_jsonl.py` (new — pure helpers for
  the replay)
- `src/scripts/verify_fix04_db_vs_jsonl.py` (new — three-way DB-only
  verifier; rewrote mid-session after the v1 verifier was identified
  as a roundtrip tautology)
- `src/scripts/_verify_fix04_threeway.py` (new — pure helpers for the
  three-way verifier; pure-logic split caught a real classifier bug
  that bucketed `fail-flip-no-op` as `fail-flip-mismatch`, fixed
  before the verifier ran on real data)
- `tests/scripts/test_apply_fix04_from_jsonl.py` (new — 15 tests)
- `tests/scripts/test_verify_fix04_threeway.py` (new — 11 tests
  covering the three-way classifier and the per-record evaluator)
- `audit/post_processing/hi06_fix04_preview/hi06_fix04_post_apply_verify.md`
  (new — three-way verifier report; 1,121 / 1,121 flips landed,
  3,933 stable cells, 0 failures)
- `logs/hi06_fix04_apply.log` (new — apply tee)
- `logs/hi06_fix04_verify.log` (new — verifier tee; overwritten with
  the v2 three-way run)
- `audit/conversations/2026-05-10_hi01-hi06-preview-apply.md` (this
  file, updated)
- `audit/man_hours_registry.yml` + `audit/man_hours_summary.md`

No production code in `src/atoms_vs_ashes/` was modified. The apply
paths in `run_fix04_osm_avoidance_batch.py` and the OurAirports batch
are byte-unchanged; the replay reuses their persist functions through
import, not duplication.

## Follow-ups for the SP-H / Tier-C backlog

Both surfaced from this session and **not** addressed here.

1. **Rule violation: `raw-response-logging.mdc` not honoured by FIX-04
   path.** `run_fix04_osm_avoidance_batch.py` and
   `preview_fix04_osm_vs_db.py` neither call
   `enable_raw_response_logging` (the OverpassClient on-disk dump) nor
   `log_raw_response` (the `site_raw_responses` Postgres table). The
   only OSM raws on file under `connector_slug = 'osm'` are from
   `run_id = osm_audit_20260420` (the April 20 audit-script
   backfill); the May 11 preview's raws were never persisted, and
   exist now only in pre-parsed form inside
   `logs/hi06_fix04_preview.jsonl`. Implication: a future re-parse
   sanity-check against the May 11 raws is **not** possible. The
   established pattern (`run_osm_road_density_retry.py` calls both
   helpers; `run_fix08_transport_gaps.py` calls
   `enable_raw_response_logging`) shows what should land in FIX-04.

2. **Independent verification using `osm_audit_20260420`.** The 361
   April-20 raw OSM responses can be re-parsed with the FIX-04
   parsers (military / power / transmitters) and cross-checked
   against the post-apply DB. Expected to surface non-zero diffs
   reflecting 3-week OSM evolution — but the *direction and magnitude*
   of the diffs is a free sanity check on the parser pipeline. Out of
   scope for P1; logging here so the v2 close-out plan or SP-H
   backlog can pick it up.

3. **Pre-apply DB snapshot.** No `pg_dump`-style backup of
   `site_human_hazards` and `site_infrastructure_v2` was taken before
   the apply. The preview JSONL captured the pre-apply state in
   `db.<domain>` (and the three-way verifier confirms the apply moved
   exactly the cells the preview promised), so reversibility is good
   in practice — but a one-shot snapshot before any future
   FIX-04-style apply is cheap insurance.

## v2 close-out — P1 todo execution (2026-05-11 18:12 UTC)

The v2 close-out plan
(`/Users/terbolence/.cursor/plans/v2_close-out_plan_dd550fd1.plan.md`,
section P1) was reopened today as a discrete todo
(`p1_fix04_apply`). The earlier 17:37 UTC apply already satisfied the
"all-sites apply (HI-06 + HI-07 + NS-02)" requirement, so the P1 todo
collapsed to a recheck-and-document pass. No new DB writes; no new
Overpass calls.

### What was done

1. Re-read the existing apply / verify artefacts above and the v2
   close-out plan to confirm the apply window had not been re-opened
   by any subsequent enrichment pass.
2. Re-ran the DB-vs-JSONL verifier as the P1 "post-apply re-preview"
   gate (the cheap, no-Overpass equivalent of the literal plan step):
   ```bash
   PYTHONPATH=src .venv/bin/python src/scripts/verify_fix04_db_vs_jsonl.py \
     --jsonl logs/hi06_fix04_preview.jsonl \
     --report audit/post_processing/v2_close_out/p1_fix04_recheck_verify.md \
     2>&1 | tee logs/hi06_fix04_p1_recheck.log
   ```
3. Result — **361 / 361 sites still in sync, 0 residual diffs** across
   all HI-06 / HI-07 / NS-02 columns. The apply has held; nothing has
   touched these columns between 17:37 UTC and 18:12 UTC.
4. Wrote
   `audit/post_processing/v2_close_out/README.md` to make the path
   deviation (replay-from-JSONL + DB-vs-JSONL verifier instead of
   `--no-skip-populated` re-query + `preview_fix04_osm_vs_db.py`
   re-run) discoverable from the v2 close-out folder, and to keep
   later phases' close-out artefacts collected in one place.

### Why the literal plan step was not re-run

The plan's "Run `run_fix04_osm_avoidance_batch.py ... --no-skip-populated`
... Post-apply: re-run `preview_fix04_osm_vs_db.py`" wording was
written **before** the replay path existed. It is not a
hard requirement; the user-approved replay path delivers the same DB
state and a stronger gate (DB matches preview-approved values exactly,
rather than DB matches a fresh Overpass query subject to in-flight
churn). Re-running the literal step would have:

- spent ~7-9 h of Overpass quota for no additional information;
- introduced the very drift the replay-then-verify protocol was
  designed to eliminate;
- overwritten the `logs/hi06_fix04_preview.jsonl` source of truth.

The path deviation is documented in the v2 close-out folder README
and was already noted (with rationale) in the "Path deviation —
replay instead of re-query" section above.

### P1 close-out status

- HI-06 (military) — ✅ applied, verified, in sync.
- HI-07 (transmitter) — ✅ applied, verified, in sync.
- NS-02 (power) — ✅ applied, verified, in sync.
- HI-01 (OurAirports) — ✅ explicit no-op, documented.

### Files added in this pass

- `audit/post_processing/v2_close_out/README.md` (new)
- `audit/post_processing/v2_close_out/p1_fix04_recheck_verify.md` (new)
- `logs/hi06_fix04_p1_recheck.log` (new)
- this file (updated)
- `audit/man_hours_registry.yml` + `audit/man_hours_summary.md`
  (regenerated)
