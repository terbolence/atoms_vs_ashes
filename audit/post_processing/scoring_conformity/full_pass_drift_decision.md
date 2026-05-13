<!-- man_hours: 0.7 -->
# Full-pass drift decision — A / B / C

**Status: DEFERRED on 2026-05-13.**

**Decision: deferred** — Leave as-is. No change to
`src/atoms_vs_ashes/scoring/_safety_floor.py` and no change to the
`pass_mark` declarations in the rubric YAMLs. The `:floor` mechanism
continues to fire as currently configured (E_RI04:floor 174 sites,
E3:floor 155 sites, E4:floor 121 sites). Revisit alongside the SP-G
NH-04 slope-fusion calibration when the source data improves.

The report narrative that pins to the canonical May-2 full-pass landscape
(36 sites) does not match the current post-SP-D landscape (11 sites);
this divergence is acknowledged and will be re-curated at report-rev
time, not by retro-fitting the rubric.

---
*Original A/B/C options preserved below for the record.*

## Context

The `:floor` mechanism in `src/atoms_vs_ashes/scoring/_safety_floor.py`
(introduced as part of the SP-D safety-floor rework, anchored in
`report/methodology/exclusionary_floors.md`) triggers a synthetic
`<E-code>:floor` exclusion when a ranking score lands below a per-rubric
`pass_mark` even though the explicit `condition_expr` of the exclusionary
fail did not match. This guarantees that a site cannot quietly pass the
ranking phase with a fundamental hazard far below the project pass-mark.

`cohort_reliability.json` records the full-pass count across the three
persisted runs:

| Run | Full-pass count | Composite-null (failed) | Source of failures |
|---|---:|---:|---|
| `score-214bab4e` (canonical, May 2) | **36** | 109 | E1 / E2:floor / E3 / E7 / E8 only |
| `feedback_rerun_20260509` (May 9, post SP-D) | **11** | 332 | + `E_RI04:floor`, `E3:floor`, `E4:floor` |
| `20260513T030738_70d5bc2c` (latest, May 13) | **11** | 330 | same |

The drop from 36 → 11 full-pass sites is dominated by three new
`:floor`-style exclusions:

- `E_RI04:floor` (RI-04 below floor) — 174 sites.
- `E3:floor` (NH-04 slope below floor) — 155 sites.
- `E4:floor` (NH-07 volcano below floor, mostly TR sites near Aegean
  volcanism) — 121 sites.

Per-country: HU lost all 2 May-2 full-passes, RO lost all 3, HR / SK lost
their 1 each, TR went from 16 → 5, UA from 11 → 5, PL from 2 → 1. Only
PL still retains a single full-pass that survived the new floors.

## Options

### A. Accept the drift (current behaviour)

Keep the `:floor` mechanism as-is. The reduced full-pass count is the
honest answer for a cohort where the new exclusionary semantics flag
sites that the canonical run was implicitly tolerating.

Pros:
- Conservative defensible posture: a site cannot pass with NH-04 slope
  below the project pass-mark even if the explicit `E3` `condition_expr`
  is configured laxly.
- Reviewer #117 ("default values where data absent") is partially
  answered: the floor surfaces sites where data is genuinely missing or
  the slope is severe, instead of letting the implicit 5.0 default carry
  them through.
- No re-score risk; no method change.

Cons:
- The cohort full-pass landscape now looks much sparser than the report
  narrative pinned to the canonical run; the shortlist of country
  exemplars needs to be re-curated.
- Some sites whose floor failures are driven by NH-04 slope (where the
  GEE / DEM resolution is known to over-estimate by a band per the SP-F
  cross-source summary) are arguably false positives.

### B. Roll back the `:floor` mechanism

Remove `_safety_floor.py` from the scoring pipeline; let the explicit
`E1-E8` `condition_expr` predicates be the only source of exclusionary
verdicts. This returns the full-pass count to roughly the canonical 36.

Pros:
- Largest restoration of the canonical full-pass landscape.
- Removes a layer the reviewer did not ask for.

Cons:
- Re-opens the original safety problem: a site can land in band [3, 4]
  for NH-04 (slope at e.g. 19°) without `E3` firing if the
  `condition_expr` is set conservatively, and still appear in a
  shortlist.
- Conflicts with the SP-D documentation in
  `report/methodology/exclusionary_floors.md` and with the regression
  test `test_safety_floor_pipeline.py`.
- Loses an explicit auditable signal of "below pass-mark" for ranking
  scores.

### C. Pin to the canonical baseline (lift the floors that fire most)

Keep the `:floor` mechanism but disable it for the three rubrics that
drive most of the 25-site drop (RI-04, NH-04, NH-07) by removing their
`pass_mark` declaration in the rubric YAML. This restores most of the
canonical full-pass count while preserving the floor mechanism for the
other rubrics (notably E2 / E3 for the geotechnical-anchor criteria).

Pros:
- Closest analogue of the canonical baseline that the report narrative
  is pinned to.
- Surgical: only the rubrics where the floor over-fires lose the
  floor, not the entire mechanism.

Cons:
- The choice of which rubrics keep their floor becomes a political
  decision rather than a methodological one. Why RI-04 in particular —
  because TR sites near Aegean volcanism dominate it, not because the
  RI-04 metric is unreliable.
- A future cohort with different geographical centre of gravity may
  surface different floor regressions; this option requires re-tuning
  every cohort change.

## Recommendation (engineering view, non-binding)

Option **A** is the methodologically cleanest choice and aligns with the
SP-D rework that the user signed off on previously. Option C is the
"least cohort change" choice if the report narrative needs to keep
citing roughly the same full-pass landscape as the canonical run.
Option B is not recommended — it loses an auditable signal that has
already paid for itself in flagging the NH-04 over-estimation problem.

## Decision required

User to choose **A**, **B**, or **C** (or "leave open, re-visit after the
NH-04 slope-fusion calibration in SP-G"). No change to `_safety_floor.py`
or to the rubric `pass_mark` declarations lands until the user signs
off.
