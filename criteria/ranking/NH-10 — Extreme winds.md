<!-- man_hours: 1.2 -->
# NH-10 - Extreme winds

Status: final

Phase: `ranking`

Primary metric: `max_wind_speed_ms`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 3, normalised weight 1.1%).

## Specialist Recommendation
Use the fixed 25 / 30 / 36 / 42 / 49 m/s wind score curve already written in the spec/rubric comments, and keep `project_wind_envelope` as a review flag only. The threshold-metadata recipe was overfitting ranking bands to the 49 m/s review threshold and split the current 5.41-14.44 m/s local range without a screening-stage basis.

## Final State
The NH-10 spec no longer declares a band recipe, so compiled scoring uses the explicit fixed wind bands. Local NH-only validation after the YAML change gives `{'9-10': 361}`; the 49 m/s threshold remains a review signal for Stage 3 wind-load confirmation, not an exclusionary or avoidance outcome.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Finalized with explicit fixed wind bands. |
| Score logic | Post-change local NH-only validation gives matched-band counts `{'9-10': 361}`. | Remove the threshold-metadata-driven band recipe and use the fixed 25 / 30 / 36 / 42 / 49 m/s bands. |
| Data quality | No raw misses were recorded for declared API fields in the local evidence query. | Keep the metric caveat: current wind values are relative screening evidence, not design-basis gust confirmation. |
| Threshold metadata | `threshold_metadata.yaml` exposes `project_wind_envelope` at 49 m/s. | Keep the threshold as a review flag only; it no longer rebuilds the ranking bands. |
| Filter relationship | Ranking-only design-basis criterion. `project_wind_envelope` is a review flag, not an exclusion or avoidance penalty. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `max_wind_speed_ms < 25` | Low wind region in the current screening dataset. | 361 |
| 7-8 | `max_wind_speed_ms < 30` | Moderate wind exposure if measured. | 0 |
| 5-6 | `max_wind_speed_ms < 36` | Elevated exposure; Stage 3 wind-load confirmation. | 0 |
| 3-4 | `max_wind_speed_ms < 42` | High exposure; enhanced design-basis review. | 0 |
| 1-2 | `max_wind_speed_ms <= 49` | Borderline review-flag envelope. | 0 |
| 0 | `max_wind_speed_ms > 49` | Outside project review envelope; not an exclusionary screen. | 0 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only NH-only compiled-spec evaluation using local scoring helpers. No API, enrichment, web, or remote calls were made.
- `max_wind_speed_ms`: present 361/361, NULL 0, min 5.41, max 14.44, mean 9.0706.
- No raw misses were recorded for declared API fields in the local evidence query.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `project_wind_envelope` | `review_flag` | `max_wind_speed_ms > 49` | 0 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `958e4d82` Rovinari power station | RO | 9.5 | `max_wind_speed_ms`=5.41 | matched accepted logic |
| 9-10 | `66bdc30c` Stalowa Wola power station | PL | 9.5 | `max_wind_speed_ms`=9.81 | matched accepted logic |
| 9-10 | `67e5a20f` Bugojno Thermal Power Project | BA | 9.5 | `max_wind_speed_ms`=10.66 | matched accepted logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-10 — Extreme winds.md`.
- Validation: local NH-only scoring validation after YAML synchronization: `{"9-10": 361}`.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
