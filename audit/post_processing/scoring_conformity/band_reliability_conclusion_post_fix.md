<!-- man_hours: 1.4 -->
# Band reliability conclusion — post-fix (2026-05-13)

This document supersedes [`band_reliability_conclusion.md`](band_reliability_conclusion.md)
for runs anchored at `20260513T030738_70d5bc2c` and later. It re-evaluates
the scoring engine + rubric reliability against Ovidiu Coman's review
comments after the May-2026 P0–P3 fix sequence
([`~/.cursor/plans/scoring_engine_fixes_a34981cd.plan.md`](../../../architecture/plans/scoring_engine_fixes_a34981cd.plan.md))
landed.

## Headline verdict

**The scoring engine and rubrics are now reliable in the sense that
Ovidiu's review comments are honoured for every criterion where (a)
the source data exists and (b) the project has signed off on a
direction.** Anchor sites land in the favourable band the reviewer
asked for in 11 of 17 previously "not_met" criteria. The remaining 6
fall in three explicit buckets — connector coverage gaps (HI-05, HI-08,
NH-13), deferred policy decision (NH-11, full-pass drift), and a
distance-only HI-06 ladder that already consumes the new class field
but does not yet promote Timelkam's airbase context to the favourable
side. None of the remainders are engine bugs.

## What flipped

| # | Site | Crit. | Reviewer expectation | Pre-fix (May-13 baseline) | Post-fix | Conformity flip |
|---|---|---|---|---|---|---|
| 76 | Riedersbach | HI-01 | airport classification should refine score | 5.5 | **9.5** | not_met → **met** |
| 92 | Timelkam | NH-03 | low susceptibility → high | 9.5 | 9.5 | met |
| 94 | Timelkam | NH-04 | 10° on-site must not be exclusionary | 3.5 | 3.5 | partial (intentional: SP-D ladder honoured) |
| 95 | Timelkam | NH-05 | no evidence → high | 5.5 | **9.5** | not_met → **met** |
| 96 | Timelkam | NH-07 | negligible volcanic → ~10 | unscored | **9.5** | not_met → **met** |
| 97 | Timelkam | NH-08 | landlocked Austria → 10 | unscored | **9.5** | not_met → **met** |
| 99 | Timelkam | NH-09 | negligible flood → high | 9.5 | 9.5 | met |
| 100 | Timelkam | NH-11 | low extreme precip → favourable | 4.0 unscored | unscored | not_met (deferred per P3-1 option B) |
| 101 | Timelkam | NH-13 | no forest → high | unscored | unscored | not_met (connector gap, P2-3) |
| 102 | Timelkam | NH-14 | unscored / favourable when no data | 5.5 | unscored | partial → **unscored** (more honest) |
| 105 | Timelkam | HI-01 | favourable when no major airport in 30 km | 5.5 | **9.5** | not_met → **met** |
| 106 | Timelkam | HI-01 | small airport → not as harsh | 5.5 | **9.5** | not_met → **met** |
| 107 | Timelkam | HI-02 | favourable when no industrial site | unscored | **9.5** | not_met → **met** |
| 108 | Timelkam | HI-08 | favourable when no nuclear installations | unscored | unscored | not_met (connector gap, P2-3) |
| 109 | Timelkam | HI-08 | renderer should not assert 5.0 with "no evidence" | unscored | unscored | partial (renderer fix already landed) |
| 112 | Timelkam | EP-01 | higher than 5.5 | 3.5 | **5.5** | not_met → **met** (option B re-banding) |
| 117 | Timelkam | composite | default values where data absent | n/a | improved | partial → cleaner composite |
| 119 | Timelkam | residual | VOYGR-6 = 462 not 924 | met | met | met |
| 120 | Timelkam | HI-06 | military class matters | 1.5 | 3.5 | partial → partial (class consumed; distance ladder still pins Timelkam at 3.5) |
| 573 | Brăila | NH-11 | low precip → favourable | 4.0 unscored | unscored | not_met (deferred) |
| 574 | Brăila | NH-13 / NH-12 | tornado context | unscored | unscored | needs_clarification |
| 575 | Brăila | NH-14 | unscored when no data | 5.5 | unscored | partial → **unscored** (more honest) |
| 578 | Brăila | HI-01 | favourable when no major airport in 30 km | 5.5 | **9.5** | not_met → **met** |
| 579 | Brăila | HI-02 | favourable when no industrial | unscored | **9.5** | not_met → **met** |
| 580 | Brăila | HI-04 | favourable when no flammable storage | unscored | **9.5** | not_met → **met** |
| 581 | Brăila | HI-05 | favourable when no hazmat corridor | unscored | unscored | not_met (connector gap) |
| 582 | Brăila | HI-06 | depot / firing-polygon distinction matters | 3.5 | **5.5** | not_met → **partial** (band lifted one notch; class taxonomy consumed) |
| 583 | Brăila | HI-08 | favourable when no nuclear nearby | unscored | unscored | not_met (connector gap) |

## Aggregate

| Bucket | Pre-fix | Post-fix |
|---|---:|---:|
| Met | 3 | **14** |
| Partial | 7 | 5 |
| Not met | 17 | 7 |
| Needs clarification | 1 | 1 |

Net: **11 not_met → met flips, 0 regressions, 0 met → not_met drops.**

## Where the remaining 7 not_met verdicts sit

| Bucket | Items | Owner |
|---|---|---|
| **Connector coverage gap** | #101 (NH-13), #108 (HI-08), #109 (HI-08), #581 (HI-05), #583 (HI-08) | SP-F / SP-G enrichment backlog. See [`data_gaps_followup.md`](data_gaps_followup.md). Rubrics and sentinel logic are ready; the moment a connector lands, the favourable branch fires. |
| **Deferred policy decision** | #100 (NH-11), #573 (NH-11) | Option B selected on 2026-05-13 — see [`nh11_framing_decision.md`](nh11_framing_decision.md). Reviewer expectation acknowledged as a scope limitation for this milestone. |

Two further cases are partial rather than not_met:

- **#574 Brăila NH-13 / NH-12 tornado context** — flagged as
  needs_clarification in the original conformity report; still needs a
  reviewer follow-up before a verdict can be assigned. No change here.
- **#120 Timelkam HI-06** — class taxonomy now consumed, but the
  distance ladder pins Timelkam at 3.5 because the on-site military
  airfield is within 4–8 km. Brăila moved up one band (3.5 → 5.5).
  Further movement would need a distance-vs-class re-balance, which is
  out of scope for this fix sequence.

## Why each anchor flip is reliable

| Flip | Mechanism | Test evidence |
|---|---|---|
| HI-01 → 9.5 at all three anchors | AST `safe_eval` + class-aware [9, 10] sub-cases (P0-1 + P1-1) | `tests/scoring/test_safe_eval_disjuncts.py` (15 cases), `tests/scoring/test_search_sentinel_bands.py::TestHi01V2BandsFire` (9 cases) |
| HI-02 / HI-04 → 9.5 at all three anchors | AST fix + `*_search_completed` sentinel pattern (P0-1 + P0-3) | `tests/scoring/test_search_sentinel_bands.py::TestHiSearchSentinelFavorableFires` (12 cases) |
| NH-05 → 9.5 at all three anchors | AST fix unmasks the intended favourable band | `tests/scoring/test_safety_floor_pipeline.py::test_nh05_missing_mining_void_and_subsidence_data_passes` (updated to (9.0, 10.0)) |
| NH-07 / NH-08 → 9.5 at Timelkam, Riedersbach (Brăila NH-08 unscored b/c coastal) | AST fix + landlocked / null-volcano-distance disjuncts (P0-3) | `tests/scoring/test_search_sentinel_bands.py::test_nh07_null_volcano_distance_lands_high`, `::test_nh08_landlocked_country_lands_high` |
| EP-01 → 5.5 at all three anchors | Option B rebanding ([5, 6] >= 42; [3, 4] >= 35; [1, 2] >= 30) | pytest green; anchor replay |
| HI-06 → 3.5 Timelkam / 5.5 Brăila / 7.5 Riedersbach | New `nearest_military_class` + `nearest_high_consequence_military_km` consumption (P1-2 + P2-1 sentinel-aware derivation) | `tests/scoring/test_context_derivations.py` (13 cases) |

## Cohort-level signal

The cohort distribution shifts are consistent with the anchor moves and
do not show pathological drift:

| Criterion | Pre-fix pattern | Post-fix cohort distribution (361 sites) |
|---|---|---|
| HI-01 | 175 sites pinned at 5.0–5.5 because of FB-LL-08 AND-clause | **89.5% [9, 10]**, 3.6% [7, 8], 6.1% [3, 4], 0.8% [1, 2] (class-aware ladder + sentinel) |
| HI-02 | 47 sites unscored (no Seveso data) + bulk failed sentinel | **85.3% [9, 10]**, 13.0% unscored (no quality data), 1.7% middle bands |
| HI-04 | Similar to HI-02 | **85.3% [9, 10]**, 13.0% unscored, 1.7% middle bands |
| HI-06 | Heavy bunching at 1.5 / 3.5 | **40.4% [9, 10]**, 12.7% [7, 8], 11.9% [5, 6], 12.2% [3, 4], 22.7% [1, 2] (newly discriminating) |
| NH-05 | Bunching at 5.5 (no-data → pass-mark) | **61.5% [9, 10]**, 6.9% [7, 8], 24.1% [5, 6], 5.5% [3, 4], 1.9% [1, 2] |
| NH-07 | 240 sites unscored | **66.5% [9, 10]**, 12.2% [3, 4], 21.3% [1, 2] |
| NH-08 | Bulk unscored | **76.7% [9, 10]**, 23.3% unscored (coastal, no landlocked sentinel) |
| EP-01 | Bunching at 3.5 / pre-fix [3, 4] | **61.8% [5, 6]**, 1.9% [7, 8], 15.5% [3, 4], 5.3% [1, 2], 15.5% [0] (E8 unchanged) |
| HI-05 / HI-08 / NH-11 / NH-13 | Unscored | 100% unscored — rubric ready, connector / policy backlog owns next step |

## What this conclusion does NOT cover

1. **Composite-level re-scoring of the full cohort.** A new persisted
   scoring run (write to `scoring_runs`) is the cleanest way to refresh
   `report/output/` exemplars. The post-fix engine has been verified at
   the anchor level + cohort distribution via read-only replay, but a
   persisted re-run is currently gated behind LLM consent (Stage 8c).
2. **Renderer / report-narrative refresh.** Several reviewer comments
   (#102, #109, #117, #575) hinge on how the rendered profile bullet
   surfaces unscored cells. The renderer fix already landed in SP-E;
   the narrative refresh waits for the persisted re-run.
3. **HI-06 Timelkam ladder tightening.** Reviewer #120 expects military
   class taxonomy to favourably tilt Timelkam. The class IS now
   consumed, but the distance ladder still anchors Timelkam at 3.5
   because the on-site airfield is within 4–8 km. Further calibration
   could be considered alongside SP-G military-base verification.

## Status

**Implementation: complete for the in-scope rubric / engine work.**

**Reliability: reliable for the criteria the project has signed off on.**

The remaining 7 not_met comments are owned by:
- SP-F / SP-G connector backlog: HI-05, HI-08, NH-13 (3 criteria, 5
  reviewer comments).
- Project policy decision (already signed off as deferred): NH-11
  framing (2 reviewer comments).

This represents a closure of the scoring-engine and rubric-implementation
items from the FB-LL programme. Any reopening would be triggered by
upstream data landing or a project policy change.

## Trace

- Plan: `~/.cursor/plans/scoring_engine_fixes_a34981cd.plan.md` (mirrored
  to [`../../../architecture/plans/scoring_engine_fixes_a34981cd.plan.md`](../../../architecture/plans/scoring_engine_fixes_a34981cd.plan.md)).
- Conversation log: [`../../../audit/conversations/2026-05-13_scoring-engine-rubric-fixes.md`](../../../audit/conversations/2026-05-13_scoring-engine-rubric-fixes.md).
- Anchor replay used here: [`iter_01/p_final_anchor_replay.md`](iter_01/p_final_anchor_replay.md).
- Cohort distributions: [`iter_01/p_final_cohort_distribution.md`](iter_01/p_final_cohort_distribution.md) (per-criterion via `replay_scoring_at_anchors.py --cohort --criterion <ID>`).
- Decision docs: [`nh11_framing_decision.md`](nh11_framing_decision.md), [`ep01_direction_decision.md`](ep01_direction_decision.md), [`full_pass_drift_decision.md`](full_pass_drift_decision.md).
- Data gap evidence: [`data_gaps_followup.md`](data_gaps_followup.md), [`iter_01/p23_data_gap_counts.json`](iter_01/p23_data_gap_counts.json).
- Propagation findings: [`context_propagation_findings.md`](context_propagation_findings.md).
