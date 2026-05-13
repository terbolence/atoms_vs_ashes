<!-- man_hours: 0.3 -->
# Scoring Conformity Assessment

This folder answers two questions, with audited evidence rather than narrative:

1. Have Ovidiu Coman's scoring-related comments been implemented?
2. Are the current scoring bands reliable as applied to **persisted scoring results**, not only as edited YAML or signed-off plans?

The assessment was run from local files and the local database. **No live APIs were called and no new scoring or sensitivity job was triggered.**

## Files

| File | Purpose |
|---|---|
| [`ovidiu_comment_conformity.md`](ovidiu_comment_conformity.md) | Per-comment status: implemented / partially / not / deferred / needs_clarification / ack. |
| [`ovidiu_comment_conformity.csv`](ovidiu_comment_conformity.csv) | Machine-readable version of the above. |
| [`implementation_audit.md`](implementation_audit.md) | Theme-by-theme verification of FB-LL acceptance against the current repository state. |
| [`run_inventory.md`](run_inventory.md) / [`run_inventory.json`](run_inventory.json) | Read-only inventory of persisted scoring runs in the local DB. |
| [`anchor_delta_canonical_vs_latest.md`](anchor_delta_canonical_vs_latest.md) | `score-214bab4e` → `20260513T030738_70d5bc2c` anchor-site deltas. |
| [`anchor_delta_feedbackrerun_vs_latest.md`](anchor_delta_feedbackrerun_vs_latest.md) | `feedback_rerun_20260509` → `20260513T030738_70d5bc2c` anchor-site deltas. |
| [`anchor_score_conformity.md`](anchor_score_conformity.md) | Anchor-site scores compared against reviewer expectations. |
| [`cohort_reliability.md`](cohort_reliability.md) / [`cohort_reliability.json`](cohort_reliability.json) | Cohort-wide raw data: unscored counts, mean / favorable / mid distribution, fail prompts, per-country full-pass. |
| [`cohort_reliability_summary.md`](cohort_reliability_summary.md) | Interpretation of the cohort signals. |
| [`band_reliability_conclusion.md`](band_reliability_conclusion.md) | Final rating + required actions. |

## Scripts that produced the artifacts

- [`src/scripts/build_scoring_conformity_matrix.py`](../../../src/scripts/build_scoring_conformity_matrix.py)
- [`src/scripts/inventory_scoring_runs.py`](../../../src/scripts/inventory_scoring_runs.py)
- [`src/scripts/compare_anchor_scores.py`](../../../src/scripts/compare_anchor_scores.py) (existing project tool)
- [`src/scripts/cohort_reliability_summary.py`](../../../src/scripts/cohort_reliability_summary.py)

## Final rating

**Conditionally reliable / partially implemented.** See [`band_reliability_conclusion.md`](band_reliability_conclusion.md). 25 of 45 reviewer comments are fully implemented at scoring time; 12 are partial; 3 are not implemented. The block to a full "Reliable" rating is a small, identifiable set of issues (HI-01 / HI-06 rubric gaps, engine favorable-branch firing, NH-11 framing, EP-01 direction reversal, full-pass drift acceptance, EPRI provenance in renderer, paired sensitivity run for the new rubric).
