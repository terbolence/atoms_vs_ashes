<!-- man_hours: 1.0 -->
# Tier 2 Partial Data Parallel Band Workflows

Plan: `/Users/terbolence/.cursor/plans/tier2_partial_data_fcda7049.plan.md`

Scope: Bucket C — EP-03, HI-02, HI-03, HI-04, NH-09, NH-11, RI-03, RI-05. Baseline `20260517T104618_459ae424`, SMR `nuscale_voygr6`.

## Shared prep

1. Read `experts/quality/lessons_learned.md` (LL-027, LL-029, LL-030, LL-031, LL-036–038, LL-015, LL-017, LL-018, LL-022).
2. Run `PYTHONPATH=src python src/scripts/audit_phase2_partial_data.py --coverage-only`.
3. Confirm coverage verdict `scoreable_*` before YAML edits.

## Tracks (summary)

| Track | Criterion | Verdict | Class | STOP markers |
| --- | --- | --- | --- | --- |
| A | EP-03 | scoreable_with_derivation | A (+ B interim) | STOP_DB_WRITE for DEM backfill |
| B | HI-02 | scoreable_with_sentinel | A | STOP_CONNECTOR for Seveso refresh |
| C | HI-03 | scoreable_with_sentinel | A | STOP_DB_WRITE for toxic backfill |
| D | HI-04 | scoreable_with_sentinel | A | same as HI-02 |
| E | NH-09 | scoreable_with_derivation | A | STOP_CONNECTOR for HydroRIVERS |
| F | NH-11 | scoreable_with_partial_metrics | B | STOP_LIVE_API for drought indices |
| G | RI-03 | scoreable_with_derivation | A | STOP_DB_WRITE for vulnerability enum |
| H | RI-05 | scoreable_with_derivation | B | STOP_CONNECTOR for GISCO city refresh |

Per-track memos: `audit/post_processing/06_scoring/phase2_track_<CRITERION>_curation_memo.md`.

**Approval:** YAML integration complete in-repo; consent-gated rescore still required for DB before/after proof.
