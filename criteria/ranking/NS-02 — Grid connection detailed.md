<!-- man_hours: 0.4 -->
# NS-02 — Grid connection (detailed)

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation. Cross-reference: `criteria/avoidance/NS-02_A13_grid_connection.md`.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-02 — Grid connection (detailed) |
| Phases | `[avoidance, ranking]` |
| Primary metric | `nearest_hv_line_km` and `hv_line_voltage_kv`; capacity cap from `grid_export_capacity_mw` in the compiled spec |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` — ranking phase with `avoidance_penalty`, not `exclude` |
| Weight | factor 8; normalised 2.8% |
| Aggregation | `min_of_sub_scores`, then capped by the compiled capacity-margin band |
| Related screen | A13 avoidance caution: `grid_export_capacity_mw < 462` |
| Threshold metadata | `NS-02.A13`, default 462 MW, bounds 100-1500 MW |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Does A13 use the intended metric? | Yes. The active expression and threshold sidecar both use `grid_export_capacity_mw < 462`. | No decision needed for the A13 predicate itself. |
| Do ranking bands align with the A13 floor? | The current `capacity_margin` recipe uses the A13 pivot as the score-5 boundary. | Accept the aligned recipe as the final ranking state. |
| Is NULL capacity a failure or unknown? | A13 treats NULL as inconclusive, while the capacity band caps ranking to 0. | Keep the conservative ranking cap, but document NULL as unmeasured capacity evidence that must be characterized in Stage 3. |
| Are distance and voltage still useful ranking axes? | Yes. `nearest_hv_line_km` and `hv_line_voltage_kv` are persisted and scored as sub-scores. | Accept current axes. |

## Current Ranking Logic

| Component | Metric | Current bands / behavior |
| --- | --- | --- |
| Distance to grid | `nearest_hv_line_km` | 9-10 `< 1`; 7-8 `<= 5`; 5-6 `<= 15`; 3-4 `<= 30`; 1-2 `> 30`. |
| Voltage class | `hv_line_voltage_kv` | 9-10 `>= 400`; 7-8 `>= 220`; 5-6 `>= 110`; 3-4 `>= 33`; 1-2 `< 33` or unknown. |
| Capacity cap | `grid_export_capacity_mw` | Compiled from `band_recipe: {kind: capacity_margin, fail_code: A13}`. Current recipe alignment: 9-10 `>= 646.8`; 7-8 `>= 554.4`; 5-6 `>= 462`; 3-4 `>= 369.6`; 1-2 `> 0`; 0 `<= 0` or NULL. |

This means a site below the 462 MW A13 floor no longer receives a score-5-or-better capacity band under the compiled recipe. The remaining limitation is NULL capacity: it is unmeasured at this stage and must not be described as confirmed lack of grid headroom, even though the current ranking cap remains conservative.

## Metric Truth And Data Quality

Primary source fields are `site_infrastructure_v2.nearest_substation_km`, `nearest_hv_line_km`, `hv_line_voltage_kv`, and `grid_export_capacity_mw`. Local avoidance evidence reported 361 infrastructure rows, 360 non-null capacity values, 1 NULL capacity value, 343 non-null voltage values, and full nearest-HV-line coverage.

NULL capacity currently has split semantics: A13 evaluates it as inconclusive, while ranking treats it as no capacity for the compiled cap. ENTSO-E connector notes cited in the avoidance doc define NULL as no per-unit match and no GEM installed-capacity fallback, not confirmed absence of grid capacity.

## Examples

| Example | Inputs | Current behavior |
| --- | --- | --- |
| Kangal power station, TR | 457 MW, 0.12 km HV, voltage NULL | Capacity is below the 462 MW A13 floor; the screening record supports an A13 caution and Stage 3 grid-export characterization. |
| Stalowa Wola power station, PL | 444 MW, 0.15 km HV, 110 kV | Capacity is below the 462 MW A13 floor; the aligned capacity band is below score 5 even though distance and voltage remain useful ranking evidence. |
| Novaky power station, SK | 472 MW, 0.40 km HV, 110 kV | Capacity is just above the 462 MW floor; the site sits in the limited-margin capacity band and remains contingent on Stage 3 grid studies. |
| FPCU Feldioara, RO | capacity NULL, 3.31 km HV, 110 kV | Capacity is unmeasured at this stage; A13 is inconclusive and the current ranking cap is a conservative data-quality treatment, not a measured no-capacity finding. |

## Specialist Recommendation

Accept the `capacity_margin` recipe that places the score-5 boundary at the A13 floor of 462 MW. That keeps screening-stage ranking consistent with the avoidance caution: measured capacity below the reference export requirement remains a grid-characterization concern, while measured capacity at or above 462 MW can contribute to the middle or upper ranking bands depending on margin.

Do not change the NULL policy in YAML in this pass. NULL `grid_export_capacity_mw` is unmeasured at this stage: the site record lacks a measured export-capacity value, and the screening report should route that gap to Stage 3 grid characterization rather than infer a measured shortfall. The existing score-0 cap for NULL capacity can remain as a conservative ranking data-quality treatment until the compiler supports an inconclusive capacity cap or a separate confidence field.

## Final State

NS-02 is finalized as a screen-plus-rank criterion for the ranking sweep. The final documented behavior is: distance and voltage sub-scores rank measured grid geometry; the `capacity_margin` recipe uses 462 MW as the score-5 capacity boundary; A13 remains an avoidance caution for measured capacity below 462 MW; and NULL capacity is recorded as unmeasured screening evidence requiring Stage 3 grid-export characterization.

No scoring YAML change is landed here because the current recipe already aligns the score-5 capacity boundary with A13, and changing NULL handling would require a compiler/schema policy decision rather than a documentation-only ranking sweep edit.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-02 phases, sub-scores, A13 condition, and capacity-margin recipe.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `config/scoring_specs/threshold_metadata.yaml`: `NS-02.A13` threshold metadata.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-02 screen-plus-rank and A13/BF-01 mapping.
- `criteria/avoidance/NS-02_A13_grid_connection.md`: threshold/NULL decision evidence and local examples.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
