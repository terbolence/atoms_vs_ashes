<!-- man_hours: 0.7 -->
# NH-11 framing decision — A / B / C

**Status: CLOSED — Option B selected on 2026-05-13.**

**Decision: B** — Leave NH-11 scoping climate-typical precipitation. No
edit to `config/scoring_rubrics/nh_natural_hazards.yaml` or
`config/scoring_specs/nh_natural_hazards.yaml`. The reviewer expectation
"low extreme daily precipitation should be favourable" is recorded as a
scope limitation; `extreme_precip_mm` stays declared in `db_fields.api`
for future use but is not consumed. Re-visit if a project decision is
made to add an NH-15 "tornado / extreme weather" criterion.

A note documenting the limitation is added to
[`data_gaps_followup.md`](data_gaps_followup.md) under "Out-of-scope
follow-ups".

---
*Original A/B/C options preserved below for the record.*

## Context

Reviewer comments #100 (Timelkam) and #573 (Brăila) read NH-11 as
"low extreme daily precipitation should be favourable". The current rubric
(`nh_natural_hazards.yaml` lines 269–307) decomposes NH-11 into three
sub-scores:

1. `drought_spi12` — SPI-12 12-month drought index.
2. `snow_burden` — months/year with snow on the ground.
3. `annual_precip` — `mean_annual_precip_mm` with a **400–800 mm optimal
   window**.

The `extreme_precip_mm` column is listed in `db_fields.api` but is **not
consumed by any sub-score**. The reviewer's "low extreme daily precipitation"
framing is therefore not represented in the score at all.

Anchor evidence:

- Timelkam annual precip = 1117 mm → annual sub-score lands [5, 6] →
  composite NH-11 = 4.0 (low).
- Brăila annual precip = 432 mm (typical) → annual sub-score lands [9, 10],
  but `extreme_precip_mm` is unused in either case.

## Options

### A. Add a fourth `extreme_precip` sub-score

Re-balance the three existing sub-scores from `0.333/0.333/0.334` to
`0.25/0.25/0.25/0.25` and introduce a new sub-score whose bands favour
low extreme 1-day precipitation:

```yaml
- key: extreme_precip
  weight: 0.25
  primary_metric: extreme_precip_mm
  bands:
    - {score_range: [9, 10], condition_expr: "extreme_precip_mm < 50", ...}
    - {score_range: [7, 8],  condition_expr: "extreme_precip_mm < 80", ...}
    - {score_range: [5, 6],  condition_expr: "extreme_precip_mm < 120", ...}
    - {score_range: [3, 4],  condition_expr: "extreme_precip_mm < 200", ...}
    - {score_range: [1, 2],  condition_expr: "extreme_precip_mm >= 200", ...}
```

Pros:
- Directly answers the reviewer's framing.
- Uses the field already declared in `db_fields.api`.
- Independent of the annual-precip band so the existing "optimal annual
  window" semantics is preserved.

Cons:
- Connector coverage of `extreme_precip_mm` is partial across the cohort
  (sampled non-null in ≤ 40% of sites per the May-2026 SP-D run); sites
  where the field is null would have only three sub-scores firing, and the
  `aggregation.mean_of_sub_scores` would silently drop the new term.
  Either (a) accept silent attrition, or (b) add a sentinel branch
  (`extreme_precip_mm is null and nh11_search_completed == true`) that maps
  to a defined score.
- Numeric breakpoints (50 / 80 / 120 / 200 mm) need a defensible source
  (IPCC AR6 regional 1-day-max climatology? IAEA SSG-18 guidance?).

### B. Document a scope limitation, do not edit NH-11

Add a note to `report/sites_evaluation/05_criteria_natural_hazards.md`
§ NH-11 explaining that the current scope captures **annual-mean
precipitation** and **multi-year drought**, not 1-day extremes. The
reviewer expectation is partially addressed via the SPI-12 sub-score
(severe wet/dry years) but not via daily intensity. Document the decision
in this audit folder and close FB-LL-11 as "won't fix in this milestone".

Pros:
- Zero scoring change, zero re-score risk.
- Honest about the connector limitation (`extreme_precip_mm` coverage is
  partial).
- Defers the breakpoint-justification problem.

Cons:
- Reviewer #100 / #573 expectations remain unmet.
- "Low extreme precip" sites continue to score the same as "high extreme
  precip" sites with the same annual mean.

### C. Re-band the existing `annual_precip` sub-score to include an
extreme-precip term

Keep three sub-scores but rewrite the `annual_precip` sub-score's
condition expressions to combine annual mean **and** `extreme_precip_mm`
within a single band. For example, the [9, 10] band becomes:

```yaml
- {score_range: [9, 10],
   condition_expr: "(mean_annual_precip_mm >= 400 and mean_annual_precip_mm <= 800) and (extreme_precip_mm < 80 or extreme_precip_mm is null)",
   descriptor: "Optimal annual mean and benign 1-day extremes."}
```

Pros:
- Single sub-score; no aggregation re-balancing.
- Preserves the existing weight share.

Cons:
- Less crisp than option A: a site with optimal annual mean but high
  extreme daily precipitation drops out of [9, 10] but the engine cannot
  isolate which part of the AND fired the demotion.
- Coupling makes future tuning harder.
- Same connector-coverage caveat as option A.

## Recommendation (engineering view, non-binding)

Option **A** maps cleanest to the reviewer's framing and respects the
existing rubric structure. The connector-coverage caveat is real but
addressable via the sentinel pattern that we already use in HI-02 /
HI-04 / HI-05 / HI-08. Option B is acceptable as a milestone-end posture
if the project decides not to extend the NH-11 scope this cycle.

## Decision required

User to choose **A**, **B**, or **C** (or "leave open, re-visit in SP-G").
The implementation step (rubric YAML + spec YAML + connector verification)
is gated behind that choice; no edit lands until the user signs off.
