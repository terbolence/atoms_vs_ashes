<!-- man_hours: 0.8 -->
# NH-12 - Extreme temperatures

Status: accepted-current-state

Phase: `ranking`

Primary metric: `extreme_temp_max_c, extreme_temp_min_c`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 4, normalised weight 1.4%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'7-8': 2, '9-10': 359}`. | Document current compiled behavior, not a proposed change. |
| Data quality | No raw misses were recorded for declared API fields in the local evidence query. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Filter relationship | Ranking-only aggregated temperature criterion. It has no fail conditions and currently resolves from both max/min temperature fields. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | Final aggregate score in this range | Aggregated sub-score result | 359 |
| 7-8 | Final aggregate score in this range | Aggregated sub-score result | 2 |
| 5-6 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 3-4 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 1-2 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 0 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| unscored | No matched final band / neutral default | Unscored or unresolved aggregate | 0 |

## Sub-Score Logic
Aggregation: `{'cap_if_any_sub_score_below': None, 'method': 'min_of_sub_scores', 'round_to': None}`.

`tmax` primary metric `extreme_temp_max_c` weight `None`:
| Score band | Condition | Descriptor |
| --- | --- | --- |
| 9-10 | `extreme_temp_max_c < 33` | Tmax < 33 C. |
| 7-8 | `extreme_temp_max_c < 36` | 33-36 C. |
| 5-6 | `extreme_temp_max_c < 39` | 36-39 C. |
| 3-4 | `extreme_temp_max_c <= 42` | 39-42 C. |
| 1-2 | `extreme_temp_max_c > 42` | > 42 C. |

`tmin` primary metric `extreme_temp_min_c` weight `None`:
| Score band | Condition | Descriptor |
| --- | --- | --- |
| 9-10 | `extreme_temp_min_c > -15` | Tmin > -15 C. |
| 7-8 | `extreme_temp_min_c > -20` | -15 to -20 C. |
| 5-6 | `extreme_temp_min_c > -25` | -20 to -25 C. |
| 3-4 | `extreme_temp_min_c >= -30` | -25 to -30 C. |
| 1-2 | `extreme_temp_min_c < -30` | < -30 C. |
## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `extreme_temp_max_c`: present 361/361, NULL 0, min 19.54, max 33.32, mean 25.3094.
- `extreme_temp_min_c`: present 361/361, NULL 0, min -12.29, max 7.93, mean -3.3942.
- No raw misses were recorded for declared API fields in the local evidence query.

## Fail, Avoidance, And Review Conditions
No fail, avoidance, screen, or review conditions are defined.

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `e6ecead0` Porto Romano Power Station | AL | 9.5 | `extreme_temp_max_c`=25.87<br>`extreme_temp_min_c`=6.38<br>sub_scores=tmax:9.5, tmin:9.5 | matched current logic |
| 9-10 | `2b03f2e2` Morava power station | RS | 9.5 | `extreme_temp_max_c`=26.13<br>`extreme_temp_min_c`=-4.05<br>sub_scores=tmax:9.5, tmin:9.5 | matched current logic |
| 7-8 | `e05ff795` Silopi (Şırnak) power station | TR | 7.5 | `extreme_temp_max_c`=33.32<br>`extreme_temp_min_c`=-1.2<br>sub_scores=tmax:7.5, tmin:9.5 | matched current logic |
| 7-8 | `98019711` Şırnak Silopi (CİNER) power station | TR | 7.5 | `extreme_temp_max_c`=33.32<br>`extreme_temp_min_c`=-1.2<br>sub_scores=tmax:7.5, tmin:9.5 | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-12 — Extreme temperatures.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
