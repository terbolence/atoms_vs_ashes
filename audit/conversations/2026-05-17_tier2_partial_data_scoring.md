<!-- man_hours: 1.0 -->
# Conversation — Tier 2 partial data scoring

**Date:** 2026-05-17  
**Plan:** `/Users/terbolence/.cursor/plans/tier2_partial_data_fcda7049.plan.md`  
**FCM:** `audit/feature_completion_matrices/2026-05-17_tier2_partial_data_scoring.md`

## Summary

Implemented Bucket C (8 criteria) scoring/context repair without DB writes or live API calls: derivations (`ep03` relief proxy, HI sentinels including `not_applicable`, `ri03` aquifer screening, RI-05 GHSL/low-density fallback), NH-11 partial sub-score aggregation + `extreme_precip` sub-score, YAML rubric/spec sync, read-only `audit_phase2_partial_data.py`, tests, coverage report, and track memos.

## Read-only audit (local DB)

- Cohort: 362 site rows per criterion.
- HI-02/03/04: 0% candidate unscored after `not_applicable` sentinel fix (was 13%).
- RI-05: 34.5% unscored (down from ~55%); GHSL proxy helps where density supports it; distance km still required for margin bands.
- EP-03: 0% unscored via barrier interim (GEE relief 0% fill locally).
- RI-03: 0.6% unscored; stdev ~1.27 on aquifer screening ladder.

## Deferred (user scope)

- Consent-gated `score run` and DB backfills (HI-03 toxic km, RI-03 vulnerability enum, EP-03 GEE batch).
