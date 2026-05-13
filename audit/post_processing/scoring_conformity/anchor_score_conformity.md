<!-- man_hours: 1.3 -->
# Anchor-site score conformity against reviewer expectations

## Method

Three anchor sites (per the master plan regression matrix):

- AT — Riedersbach power station (`660d9d71-6733-4294-951b-1c58614d58cf`).
- AT — Timelkam power station (`2dcd2c6d-f375-4408-9492-7910662fac03`).
- RO — Brăila power station (`29836b52-a882-4921-95a7-6417e636d9a2`).

Compared three persisted runs, all `nuscale_voygr6`:

| Run | Date | Snapshot | Description |
|---|---|---|---|
| `score-214bab4e` | 2026-05-02 | `scdef-cfc651693c89f428` | Canonical pre-rework anchor; the report narrative is pinned to this. |
| `feedback_rerun_20260509` | 2026-05-09 | `scdef-ef3f619776e43837` | Post-SP-D wave; first run on the new rubric. |
| `20260513T030738_70d5bc2c` | 2026-05-13 | `scdef-85e7a461ec02b7d6` | Latest run; SP-F log-replay landed in between. |

Generated deltas:

- [`anchor_delta_canonical_vs_latest.md`](anchor_delta_canonical_vs_latest.md) — `score-214bab4e` → `20260513T030738_70d5bc2c`. 12 up, 11 down, 40 unchanged.
- [`anchor_delta_feedbackrerun_vs_latest.md`](anchor_delta_feedbackrerun_vs_latest.md) — `feedback_rerun_20260509` → `20260513T030738_70d5bc2c`. 5 up, 4 down, 54 unchanged.
- [`../scoring_rerun_runbook/anchor_delta.md`](../scoring_rerun_runbook/anchor_delta.md) — `feedback_rerun_20260509` → `20260513T030738_70d5bc2c` (the project's existing comparison, narrower criterion list).

Reviewer expectations per anchor come from FB-LL acceptance tests and individual comment texts (cited inline).

## Per-comment anchor verdict (current run = `20260513T030738_70d5bc2c`)

`expected_direction` is what the reviewer asked for; `actual` is the score observed in the current run for the reviewer-anchored site; `conformity` is the verdict.

| # | Site | Crit. | Reviewer expectation | Canonical (May-2) | Current (May-13) | Conformity |
|---|---|---|---|---|---|---|
| 76 | Riedersbach | HI-01 | airport classification should refine score | 5.5 high | 5.5 high | not_met (rubric unchanged) |
| 92 | Timelkam | NH-03 | low susceptibility → high | 5.0 unscored | **9.5** medium | met |
| 94 | Timelkam | NH-04 | 10° on-site must not be exclusionary | 5.5 low | 3.5 low | partial (no exclusion fires; score dropped) |
| 95 | Timelkam | NH-05 | no evidence → high | 5.5 medium | 5.5 medium | not_met (still pass-mark) |
| 96 | Timelkam | NH-06/NH-07 | negligible volcanic → ~10 | 5.0 unscored | 5.0 unscored | **not_met** (rubric branch exists but engine still records unscored) |
| 97 | Timelkam | NH-07/NH-08 | landlocked Austria → 10 | 5.0 unscored | 5.0 unscored | **not_met** (rubric `country_is_landlocked` branch exists but does not fire) |
| 99 | Timelkam | NH-09 | negligible flood zone → high | 5.0 unscored | **9.5** medium | met |
| 100 | Timelkam | NH-11 | low precipitation → favorable | 4.0 low | 4.0 low | **not_met** (rubric does not encode reviewer's framing) |
| 101 | Timelkam | NH-13 | no forest → high | 5.0 unscored | 5.0 unscored | **not_met** (rubric branch exists but engine still records unscored) |
| 102 | Timelkam | NH-14 | unscored OR favorable when no data | 5.0 unscored | 5.5 low | partial (now classified, but not unscored or high - mid-low band) |
| 105 | Timelkam | HI-01 | favorable when no major airport in 30 km | 5.5 high | 5.5 high | not_met (FB-LL-08 AND-clause unfixed) |
| 106 | Timelkam | HI-01 | small airport → not as harsh | 5.5 high | 5.5 high | not_met (rubric does not consume `nearest_airport_class`) |
| 107 | Timelkam | HI-02 | favorable when no industrial site | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |
| 108 | Timelkam | HI-08 | favorable when no nuclear installations | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |
| 109 | Timelkam | HI-08 | same; renderer should not assert 5.0 with "no evidence" | 5.0 unscored | 5.0 unscored | partial (renderer fix landed; score still unscored) |
| 112 | Timelkam | EP-01 | higher than 5.5 | 5.5 high | **3.5** high | **not_met** (rubric tightening moved score AWAY from reviewer's wish) |
| 117 | Timelkam | composite | default values where data absent | n/a | n/a | partial (renderer fix landed; composite-level repair pending HI-01/HI-06 v2) |
| 119 | Timelkam | residual | VOYGR-6 = 462 not 924 | report narrative | report narrative | met (`cross_chapter_numeric_lint` guards) |
| 120 | Timelkam | HI-06 | military class matters | 0.0 low | 1.5 medium | partial (data enriched; rubric still uses raw distance + legacy `military_type`) |
| 573 | Brăila | NH-11 | low precip → favorable | 4.0 low | 4.0 low | **not_met** (same as #100) |
| 574 | Brăila | NH-13/NH-12 | tornado context (clarification needed) | 5.0 unscored | 5.0 unscored | needs_clarification (anchored to wrong row) |
| 575 | Brăila | NH-14 | unscored when no data | 5.0 unscored | 5.5 low | partial (similar to #102) |
| 578 | Brăila | HI-01 | favorable when no major airport in 30 km | 5.5 high | 5.5 high | **not_met** (same as #105) |
| 579 | Brăila | HI-02 | favorable when no industrial | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |
| 580 | Brăila | HI-04 | favorable when no flammable storage | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |
| 581 | Brăila | HI-05 | favorable when no hazmat corridor | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |
| 582 | Brăila | HI-06 | depot/firing-polygon distinction matters | 1.5 medium | 3.5 medium | partial (data enriched; rubric still uses raw distance) |
| 583 | Brăila | HI-08 | favorable when no nuclear nearby | 5.0 unscored | 5.0 unscored | **not_met** (sentinel branch in rubric but engine unscored) |

## Aggregate

Reviewer-anchored scoring expectations evaluated against the current persisted run:

- met outright: 3 (#92, #99, #119).
- partial / direction-of-travel right but not at expectation: 7 (#94, #102, #117, #120, #575, #582, plus #109 renderer).
- not met: 17 (the dominant cluster).
- needs reviewer clarification: 1 (#574).

This is the most important fact for the reliability assessment: **at the very anchor sites the reviewer used to flag the original defects, the current persisted scoring run still does not produce reviewer-expected scores for the majority of those criteria**, even though the rubric YAML carries the matching favorable branches.

## Why the rubric branches do not fire

Comparing the rubric against the anchor outputs surfaces three distinct failure modes, only one of which is a rubric defect:

1. **HI-01 AND-clause (FB-LL-08, rubric defect).** Rubric `[9,10]` requires `nearest_airport_km > 30 AND nearest_military_airfield_km > 60`. Missing military-airfield data drops favorable airport situations to pass-mark. Confirmed at Timelkam, Brăila, Riedersbach. SP-D HI-01 v2 was explicitly deferred pending SP-F airport-class consumption.

2. **HI-02 / HI-04 / HI-05 / HI-08 / NH-07 / NH-13 sentinel branches not firing (engine / data path).** The rubric branches read like `nearest_*_km > X or (nearest_*_km is null and <family>_search_completed == true)`. The `*_search_completed` flag is set by `merge_context_derivations.apply_derived_context_values` from the quality column being non-null and not in `{no_data, failed}`. The anchor sites still record `unscored → unscored` with `score_0_10 = 5.0`, which means **no band matched** — i.e. neither `> X` nor the `is null AND search_completed` branch evaluated `true`. Either the connector did not run (no quality entry), or the quality entry is `no_data` / `failed`, or the per-criterion derived flag is not being computed at score time. This is a data-path / context-derivation gap, not a rubric gap, and it directly blocks FB-LL-01 / FB-LL-02 acceptance for at least 6 reviewer-anchored criteria.

3. **NH-11 framing mismatch (rubric design).** The reviewer's framing of "low extreme daily precipitation should be favorable" does not match the rubric's "optimal annual precipitation 400–800 mm" structure. The `extreme_precip_mm` column is declared as a `db_field` but is not consumed in any sub-score band. This is a substantive rubric design gap that the SP-D wave did not address.

4. **EP-01 direction reversal.** Reviewer expected Timelkam's 5.5 to move higher; the re-banded rubric maps composite 44/100 to `[3,4]`, moving it further from the reviewer's wish. The structural change ("no implicit 5.5 default") landed correctly per the rubric audit, but the specific Timelkam value moved in the opposite direction.

## Acceptance-test cross-check

The FB-LL-01 acceptance test in [`feedback_lessons_learnt.md`](../../../report/output/feedback/plans/feedback_lessons_learnt.md) reads:

> For each anchor site in the regression matrix where the reviewer expected a high score (#97 Austrian coastal flooding, #105 Timelkam airport, #578 Brăila airport), the new rubric produces a score in `[8, 10]`, and the rendered profile bullet cites the favorable branch.

Against the current persisted run:

- #97 Austrian coastal flooding (Timelkam NH-08): score 5.0 unscored. **Fails acceptance.**
- #105 Timelkam HI-01: score 5.5 high. **Fails acceptance.**
- #578 Brăila HI-01: score 5.5 high. **Fails acceptance.**

The FB-LL-01 acceptance test is **not met** by the current persisted run at any of its three named exemplar sites.

The FB-LL-02 acceptance test:

> After SP-E, no rendered bullet emits a numeric score with `Evidence: values not in measurement tables` in the same line.

This is met at the renderer / test level (see `tests/scripts/test_site_profile_unscored_rendering.py`). Whether the rendered chapter-5 site profiles actually surface this depends on a regenerated profile pass, which is currently gated behind LLM consent (Stage 8c, deferred).

## Drift signal

Across the three anchors and 21 criteria (63 cells):

- canonical → latest: 12 up, 11 down, 40 unchanged.
- feedback_rerun → latest: 5 up, 4 down, 54 unchanged.

The May-9 → May-13 movement is small (driven mostly by NH-09 favorable branch firing and BF-02 dropping under the new "required area" definition); the canonical → latest movement is substantially larger and includes drops on `BF-02`, `NH-04`, `NH-14`, `EP-01`. Together with the cohort-level full-pass drift (next document), this confirms the new rubric is genuinely different from the canonical baseline rather than a no-op.

## Implications for the conformity rating

- Rubric YAML edits landed substantively for 12 of 16 reviewer-targeted criteria (per the implementation audit).
- For 6+ of those criteria, the rubric's favorable branch does **not actually fire** at the reviewer-anchored sites in the current persisted run.
- HI-01 and HI-06 remain rubric gaps independent of the engine / data path.
- EP-01 moves away from the reviewer expectation.
- NH-11 was not re-banded against the reviewer's actual framing.

A rating of "reliable / implemented" requires the engine to deliver the rubric's intent at the anchor sites the reviewer flagged. The current run does not yet do that.
