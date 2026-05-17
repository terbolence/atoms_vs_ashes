<!-- man_hours: 1.2 -->
# Partial Data Combined Approval — 2026-05-17

Read-only audit: `audit/post_processing/06_scoring/20260517_partial_data_{detail,summary}.csv` and per-criterion curation memos.

| Criterion | Approve implementation? | Candidate unscored % | Candidate stdev | Acceptance | Notes |
| --- | --- | ---: | ---: | --- | --- |
| EP-03 | **Closed for this pass — GEE relief deferred** | 0% | 2.89 | Interim accepted | Barrier/waterway scoring remains available; measured relief needs non-GEE source tracked in `IMPROVEMENTS.md` IMP-0012 |
| HI-02 | **Conditional — implemented** | 13% | 1.56 | ≤5% unscored | Auditor fix: `not_applicable` is not favourable evidence; 47 out-of-coverage rows remain unscored |
| HI-03 | **Yes — implemented** | 13% | 2.35 | ≤5% unscored | `hi03_search_completed` + null-best bands |
| HI-04 | **Conditional — implemented** | 13% | 1.56 | ≤5% unscored | Auditor fix mirrors HI-02; 47 out-of-coverage rows remain unscored |
| NH-09 | **Yes — implemented** | 4% | 0.47 | stdev ≥0.5 | Spread improved; 13 river-null unscored |
| NH-11 | **Yes — implemented after auditor fix** | 0% | 1.46 | stdev ≥0.5 | Uses corrected ERA5 monthly-means precipitation proxies; ranking-grade only |
| RI-03 | **Yes — implemented** | 0.6% | 1.27 | ≥95% scored | Aquifer-only ladder |
| RI-05 | **Conditional — implemented** | 34.5% | 3.11 | ≤20% unscored | GHSL population proxy helps; rows with population but no distance remain unscored |

**Post-rescore consent:** Run `score run` on baseline run after user approval to persist `ranking_scores` and update `20260517_logic_only_after_rescore.md`.

**EP-03 closure note:** No further GEE-dependent work should be attempted in
this pass. Partial `ep03_gee_relief_16km_m` rows from the interrupted DEM
experiment were cleared, leaving measured relief unavailable until IMP-0012
supersedes it with a complete non-GEE cohort source.
