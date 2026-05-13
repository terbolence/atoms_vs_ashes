<!-- man_hours: 0.4 -->
# v2 close-out post-processing artefacts

Per-phase artefacts produced while executing
`/Users/terbolence/.cursor/plans/v2_close-out_plan_dd550fd1.plan.md`
(report v2 close-out — Tier B + EPRI).

The plan defines eight phases (P1–P8). This folder collects the
**post-apply / post-run gate evidence** for each phase that needs an
out-of-band verification artefact. Phase-specific deliverables that
already have a natural home elsewhere (preview reports, EPRI weight
deltas, country and site bundle exports, regenerated chapters) stay in
their canonical locations and are not duplicated here.

## P1 — FIX-04 all-sites apply (HI-06 + HI-07 + NS-02)

The literal plan step was:

> Run `src/scripts/run_fix04_osm_avoidance_batch.py` for all sites with
> `--no-skip-populated` so previously-cached domains are refreshed.
> ... Post-apply: re-run `src/scripts/preview_fix04_osm_vs_db.py` and
> confirm the change count drops near zero.

The actual execution (2026-05-11 17:37 UTC) followed an explicitly
approved **path deviation**:

- Apply was driven via
  [`src/scripts/apply_fix04_from_preview_jsonl.py`](../../../src/scripts/apply_fix04_from_preview_jsonl.py)
  — replays the existing
  [`logs/hi06_fix04_preview.jsonl`](../../../logs/hi06_fix04_preview.jsonl)
  through the live `_persist_*` functions imported from
  `run_fix04_osm_avoidance_batch.py`. **No Overpass calls.** The user
  challenge — "do we not already have data for this?" — was correct:
  the preview JSONL had complete payloads for all 361 sites, generated
  less than 24 hours earlier. Re-querying would have wasted ~7-9 h of
  Overpass quota and risked drift between preview-approved values and
  actually-applied values.
- The "post-apply re-preview" gate is fulfilled by
  [`src/scripts/verify_fix04_db_vs_jsonl.py`](../../../src/scripts/verify_fix04_db_vs_jsonl.py)
  — a DB-only, no-Overpass full-cohort comparator that reuses the
  preview diff helpers. Its sole job is to answer "does the DB now
  match what the preview promised?". A residual diff > 0 would be a
  hard stop, not a sign of OSM churn.

### Artefacts (P1)

- [`hi06_fix04_post_apply_verify.md`](../hi06_fix04_preview/hi06_fix04_post_apply_verify.md)
  — initial post-apply verification (2026-05-11 17:37 UTC).
  **361 / 361 in sync, 0 residual diffs.**
- [`p1_fix04_recheck_verify.md`](./p1_fix04_recheck_verify.md)
  — independent re-verification at the time the v2 close-out P1 todo
  was executed; confirms the DB has not drifted since the apply.
  **361 / 361 in sync, 0 residual diffs.**
- Apply log: [`logs/hi06_fix04_apply.log`](../../../logs/hi06_fix04_apply.log).
- Verifier log: [`logs/hi06_fix04_verify.log`](../../../logs/hi06_fix04_verify.log)
  (initial) and
  [`logs/hi06_fix04_p1_recheck.log`](../../../logs/hi06_fix04_p1_recheck.log)
  (recheck).
- Source JSONL preserved verbatim in
  [`logs/hi06_fix04_preview.jsonl`](../../../logs/hi06_fix04_preview.jsonl)
  — do not regenerate; this is the source-of-truth payload the
  applied DB state matches.

### HI-01 — explicit no-op

The plan also calls out HI-01 as a no-op:
[`audit/post_processing/hi01_preview/hi01_preview_report.md`](../hi01_preview/hi01_preview_report.md)
showed **0 changes / 361 sites**. The 22 RO sites had already been
applied earlier; OurAirports has produced no new diffs since. **No HI-01
apply was triggered as part of the v2 close-out.**

## How to extend this folder for later phases

When a later phase produces a one-off close-out artefact that would not
naturally live in `audit/post_processing/<connector>/` or
`audit/post_processing/sp_*/`, add it here under
`p<N>_<short_slug>_*.md` and append a section to this README pointing
at it. Do **not** mirror artefacts that already have a canonical home.
