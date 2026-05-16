<!-- man_hours: 1.0 -->
# NH-14 - Combined hazards

Status: final

Phase: `ranking`

Primary metric: `nh_min_resolved_score`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 3, normalised weight 1.1%).

## Specialist Recommendation
Keep NH-14 as the derived combined-hazard criterion and allow it to resolve only when at least five underlying NH criteria have real matched bands. After the NH-08/NH-09/NH-10 recipe-bypass fixes, enough upstream inputs resolve for most sites without changing the NH-14 schema or engine.

## Final State
No NH-14 YAML behavior was changed in this worker. Local NH-only validation after upstream YAML changes gives `{'0': 9, '3-4': 1, '5-6': 180, '7-8': 95, '9-10': 42, 'unscored': 34}`. Remaining unscored rows have fewer than five resolved underlying NH criteria and are routed to Stage 3 characterization rather than assigned a synthetic combined-hazard value.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Finalized as derived behavior after upstream NH fixes. |
| Score logic | Post-change local NH-only validation gives matched-band counts `{'0': 9, '3-4': 1, '5-6': 180, '7-8': 95, '9-10': 42, 'unscored': 34}`. | Keep the five-resolved-input gate and do not invent combined-hazard values for unresolved rows. |
| Data quality | Raw misses: `site_natural_hazards.nh14_combined_index`=361. | Use engine-derived inputs; the raw combined-index field remains unused/unmeasured. |
| Filter relationship | Ranking-only derived combined-hazard criterion. It has no fail conditions. | Preserve current YAML; behavior changes arise from upstream criteria resolving. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `nh_resolved_count >= 5 and nh_min_resolved_score >= 7 and nh_count_below_7 == 0` | At least 5 underlying NH criteria resolved, all >= 7; no interaction pair below 7. | 42 |
| 7-8 | `nh_resolved_count >= 5 and nh_min_resolved_score >= 5 and nh_count_below_7 <= 1` | At least 5 resolved, min >= 5, at most one criterion below 7. | 95 |
| 5-6 | `nh_resolved_count >= 5 and nh_min_resolved_score >= 3 and nh_count_below_5 <= 1` | At least 5 resolved, exactly one moderate hazard or moderate interaction only. | 180 |
| 3-4 | `nh_resolved_count >= 5 and nh_count_below_5 >= 2 and nh_min_resolved_score >= 1` | Two or more underlying hazards below 5. | 1 |
| 1-2 | `nh_resolved_count >= 5 and nh_min_resolved_score < 1 and nh_min_resolved_score > 0` | One severe resolved hazard below 1 combined with another moderate hazard. | 0 |
| 0 | `nh_resolved_count >= 5 and nh_min_resolved_score == 0` | Combined consequence reaches the lowest combined-hazard band. | 9 |
| unscored | no compiled band matched | Fewer than 5 underlying NH criteria resolved. | 34 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only NH-only compiled-spec evaluation using local scoring helpers and `_inject_nh14_derived_metrics()`. No API, enrichment, web, or remote calls were made.
- `nh_resolved_count`: present 361/361, NULL 0, min 4, max 6, mean 5.6731.
- `nh_min_resolved_score`: present 361/361, NULL 0, min 0, max 9.5, mean 4.9252.
- `nh_count_below_5`: present 361/361, NULL 0, min 0, max 2, mean 0.3158.
- `nh_count_below_7`: present 361/361, NULL 0, min 0, max 3, mean 1.4488.
- `nh14_combined_index`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.nh14_combined_index`=361.

## Fail, Avoidance, And Review Conditions
No fail, avoidance, screen, or review conditions are defined.

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `90820fe3` Mellach power station | AT | 9.5 | `nh_resolved_count`=6<br>`nh_min_resolved_score`=7.5<br>`nh_count_below_5`=0<br>`nh_count_below_7`=0 | matched accepted logic |
| 7-8 | `532bfb42` Enns Power Station | AT | 7.5 | `nh_resolved_count`=6<br>`nh_min_resolved_score`=5.5<br>`nh_count_below_5`=0<br>`nh_count_below_7`=1 | matched accepted logic |
| 5-6 | `6e7fc4d8` Duernrohr power station | AT | 5.5 | `nh_resolved_count`=6<br>`nh_min_resolved_score`=5.5<br>`nh_count_below_5`=0<br>`nh_count_below_7`=2 | matched accepted logic |
| 3-4 | `e6ecead0` Porto Romano Power Station | AL | 3.5 | `nh_resolved_count`=5<br>`nh_min_resolved_score`=1.5<br>`nh_count_below_5`=2<br>`nh_count_below_7`=2 | matched accepted logic |
| 0 | `992a4bf0` Aksa Akrilik power station | TR | 0 | `nh_resolved_count`=5<br>`nh_min_resolved_score`=0<br>`nh_count_below_5`=1<br>`nh_count_below_7`=1 | matched accepted logic |
| unscored | `398cc0f2` Deven power station | BG | 5 | `nh_resolved_count`=4<br>`nh_min_resolved_score`=5.5<br>`nh_count_below_5`=0<br>`nh_count_below_7`=2 | fewer than 5 resolved inputs |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/engine.py`: `_inject_nh14_derived_metrics()` computes the derived combined-hazard inputs from resolved underlying NH scores.

## Artifact Footer
- Landed file: `criteria/ranking/NH-14 — Combined hazards.md`.
- Validation: local NH-only scoring validation after upstream YAML synchronization: `{"0": 9, "3-4": 1, "5-6": 180, "7-8": 95, "9-10": 42, "unscored": 34}`.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
