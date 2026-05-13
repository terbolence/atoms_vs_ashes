<!-- man_hours: 0.7 -->
# Cohort reliability — interpretation

Layered analysis on top of the raw counts in [`cohort_reliability.md`](cohort_reliability.md). All numbers are for SMR `nuscale_voygr6` on the project's three persisted runs.

## Full-pass drift (the headline number)

| Run | Full pass | Failed exclusionary | Failed avoidance only | Composite mean |
|---|---:|---:|---:|---:|
| `score-214bab4e` (May 2, canonical) | **36** | 109 | 216 | 5.33 |
| `feedback_rerun_20260509` (May 9) | **11** | 332 | 18 | 5.85 |
| `20260513T030738_70d5bc2c` (May 13, latest) | **11** | 330 | 20 | 6.08 |

The new rubric loses **25 of 36** full-pass sites (-69 %). The composite mean rises (sites that still pass score higher on average, because the bands distinguish favorable conditions better), but the screen is much more conservative.

## Country-level losses (canonical → latest)

| Country | Canonical | Latest | Δ |
|---|---:|---:|---:|
| HR | 1 | 0 | -1 |
| HU | 2 | 0 | -2 |
| PL | 2 | 1 | -1 |
| RO | **3** | **0** | **-3** |
| SK | 1 | 0 | -1 |
| TR | 16 | 5 | -11 |
| UA | 11 | 5 | -6 |
| _all others_ | 0 | 0 | 0 |
| **Total** | **36** | **11** | **-25** |

Notably:

- Reviewer comment **#568** ("In an early table you mention for Romania 1 site not 3") asked which RO full-pass count is canonical. With the new rubric the RO full-pass count is **0**, so the report would need a third value anyway.
- TR and UA collectively lose 17 of their 27 canonical full-pass sites — these are the two countries the report relied on for the cross-country comparison narrative.

## What is driving the new exclusionary failures

The fail-prompt breakdown shows the structural reason:

| Prompt | Canonical fails | Latest fails | New in latest |
|---|---:|---:|---|
| `E_RI04:floor` | 0 | 174 | yes |
| `E3:floor` (NH-04 slope) | 0 | 155 | yes |
| `E4:floor` (NH-07 volcanism) | 0 | 121 | yes |
| `E2:floor` (NH-03 liquefaction) | 0 | 61 | yes |
| `E1` (NH-02 fault) | 50 | 63 | partial increase |
| `E_RI04` (population) | 0 | 49 | yes |
| `E2` (NH-03 liquefaction sharp) | 0 | 1 | yes |

The `:floor` variant is the SP-D / SP-E safety-floor mechanism: when underlying data is insufficient to clear the criterion, the engine pessimistically applies the exclusion rather than letting an "unscored" criterion drift to pass-mark. This is the rubric design intent (it answers FB-LL-02 for the screening tier), but it also produces the massive full-pass drift documented in the rework-execution audit log.

**This drift has not been formally accepted.** The audit log records three options (A: accept and regenerate, B: roll back floor mechanism, C: pin to canonical anchor) and notes that none of them has been signed off.

## Reviewer-targeted criterion reliability (latest run)

For each reviewer-anchored criterion, what fraction of sites still defaults to 5.0 unscored vs how often the favorable high-band actually fires:

| Criterion | rows | unscored / =5.0 | favorable (>=8) | mid (4.5-6.5) | mean | reviewer-stance gap |
|---|---:|---:|---:|---:|---:|---|
| HI-01 | 361 | 0 | **0** | 238 | 4.82 | AND-clause bug; 0 of 361 sites get the favorable branch |
| HI-02 | 361 | 346 | 9 | 350 | 5.13 | sentinel branch fires for only 2.5 % of sites |
| HI-04 | 361 | 346 | 9 | 350 | 5.13 | same as HI-02 |
| HI-05 | 361 | 361 | **0** | 361 | 5.0 | sentinel branch never fires |
| HI-06 | 361 | 35 (=5.0) | 0 | 97 | 2.85 | rubric does not use new classification fields |
| HI-08 | 361 | 361 | **0** | 361 | 5.0 | sentinel branch never fires |
| NH-03 | 361 | 9 | 137 | 158 | 6.67 | works well; 38 % of sites favorable |
| NH-04 | 361 | 9 | 3 | 166 | 4.65 | favorable branch rare |
| NH-05 | 361 | 0 | 3 | 306 | 5.48 | favorable branch rare |
| NH-07 (volcanism) | 361 | 240 unscored | **0** | 240 | 4.07 | favorable branch never fires |
| NH-08 (coastal) | 361 | 361 | **0** | 361 | 5.0 | landlocked branch never fires |
| NH-09 (river flood) | 361 | 0 | **361** | 0 | 9.5 | works perfectly (every site favorable) |
| NH-11 (precipitation) | 361 | 0 | 0 | 0 | **4.0** flat | every site at 4.0; rubric does not consume `extreme_precip_mm` |
| NH-13 (wildfire) | 361 | 361 | **0** | 361 | 5.0 | favorable branch never fires |
| NH-14 (combined) | 361 | 66 unscored | 3 | 273 | 5.01 | unscored behavior works for 18 % of sites |
| EP-01 | 361 | 0 (=5.0) | 0 | 88 | 3.14 | direction-reversal (canonical 5.19 → latest 3.14) |
| RI-04 | 361 | 0 | 2 | 89 | 3.82 | unchanged from canonical; dual-mode `E_RI04` fires at 174 sites |

Pattern: the rubric's favorable branches are **technically present** but, for 6 of the 17 reviewer-targeted criteria, fire on **0 sites in 361** (HI-01, HI-05, HI-08, NH-07, NH-08, NH-13). This is a structural data-path/derivation problem in the engine, not a rubric design problem. Specifically:

- `country_is_landlocked` (NH-08) is presumably populated from the country dimension but not joined into the score-time context for any site.
- `*_search_completed` derived flags (HI-02, HI-04, HI-05, HI-08) only fire when the quality column is explicitly populated; absent that, sites default to "unscored".
- `nearest_volcano_km is null` (NH-07) does not fire for sites without a stored volcanism row.

Compare to **NH-09 river flood**, where the favorable branch fires on 361 of 361 sites because `flood_zone_class_500yr in ['none','negligible']` is a directly-stored, definite enum. The contrast confirms that the favorable-branch logic is sound *when the underlying data is populated end-to-end*.

## Cross-cutting observations

1. **Reviewer #117 "60–80 % composite score-range concern" is not resolved.** Latest run composite p25 / p50 / p75 = 5.78 / 6.14 / 6.27 (range about 6.0–7.0). Composites are still clustered in the pass-mark-to-low-favorable band, except that more sites are now classified as exclusionary fails (so they don't contribute a composite at all). The implicit "everything looks the same" critique would benefit from a Monte-Carlo or sensitivity rerun against the new rubric — currently the only sensitivity sweep is `sens-7b609bd0` against the canonical rubric.

2. **Reviewer #565 "BF-01 depends on how many modules"** is resolved structurally: BF-01 is no longer in the composite (`phases: [basic_filter]` only). But the renderer / chapter narrative should now describe headroom as a multiple of the reference SMR module, per the rubric comment, and that wording is not confirmed end-to-end.

3. **Reviewer #568 RO full-pass reconciliation.** Cross-chapter numeric lint (`cross_chapter_numeric_lint.py`) guards the reconciliation in the canonical narrative (3 sites = RO full-pass per `04_results_and_findings.md`). The latest rubric produces 0 full-pass sites for RO. Either the report narrative needs a third update or the rubric drift needs to be rolled back.

4. **No GUI sensitivity run on the new rubric exists.** All sensitivity runs in the local DB (`sens-7b609bd0`, `sens-e01d74b7`, ...) use the canonical snapshot `scdef-cfc651693c89f428` or earlier. The latest scoring snapshot `scdef-85e7a461ec02b7d6` has no paired sensitivity run. Without that, the reliability "Conditional / Reliable" tiers (A–H per FB-LL definitions) cannot be evaluated for the new rubric.

## Net cohort verdict

- The rubric is more conservative (good) and more discriminating among the remaining pass sites (composite p50 5.32 → 6.14).
- But the cohort behaviour shows **engine/data-path defaulting** for 6 reviewer-anchored criteria where the rubric defines a favorable branch but the engine never reaches it.
- The full-pass drift has **not been accepted** by reviewer/policy.
- No current sensitivity run exists for the new rubric, so band stability cannot be characterized.

The cohort signals do not yet support a clean "scoring bands are reliable" claim.
