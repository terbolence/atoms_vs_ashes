<!-- man_hours: 1.0 -->
# NH-11 - Extreme precipitation (rain, snow, drought)

Status: final

Phase: `ranking`

Primary metric: `spi12_min, snow_months_per_year, mean_annual_precip_mm`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 3, normalised weight 1.1%).

## Specialist Recommendation
Do not change NH-11 YAML in this worker. The local drought, snow, and freezing inputs are unmeasured for all 361 sites, and the populated precipitation field appears unit-incompatible with annual-total band labels. A scoring rewrite would require connector/schema/unit correction, not a desk-study reinterpretation.

## Final State
NH-11 remains a documented Stage 3 / deferred connector improvement item. The current aggregate returns a score-like 4.0 from partial inputs, but it is not accepted here as a measured ranking signal because two primary sub-scores are unmeasured and the precipitation units are unresolved.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Finalized as unresolved for measured ranking behavior. |
| Score logic | Local evidence shows all 361 rows return a partial aggregate from sparse inputs; NH-only validation labels the criterion `unscored` for all 361 rows. | Do not change YAML; route to connector/schema/unit correction. |
| Data quality | Raw misses: `site_natural_hazards.freezing_days_per_year`=361; `site_natural_hazards.snow_months_per_year`=361; `site_natural_hazards.spi12_min`=361. | Treat missing drought/snow/freezing evidence and precipitation unit uncertainty as Stage 3 / deferred connector work. |
| Filter relationship | Ranking-only aggregated meteorology criterion. It has no fail conditions; current sub-score inputs are incomplete. | Preserve current YAML until measured inputs are corrected. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 7-8 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 5-6 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 3-4 | Partial aggregate value falls in this range | Not accepted as a measured matched band while primary sub-scores are unmeasured. | 361 |
| 1-2 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| 0 | Final aggregate score in this range | Aggregated sub-score result | 0 |
| unscored | No matched final band in NH-only validation | Unresolved measured-input status for this close-out. | 361 |

## Sub-Score Logic
Aggregation: `{'cap_if_any_sub_score_below': {'cap_score': 5.0, 'threshold': 3.0}, 'method': 'mean_of_sub_scores', 'round_to': 1.0}`.

`drought_spi12` primary metric `spi12_min` weight `0.333`:
| Score band | Condition | Descriptor |
| --- | --- | --- |
| 9-10 | `spi12_min > -1.0` | SPI-12 > -1.0. |
| 7-8 | `spi12_min > -1.5` | -1.5 to -1.0. |
| 5-6 | `spi12_min > -2.0` | -2.0 to -1.5. |
| 3-4 | `spi12_min > -2.5` | -2.5 to -2.0. |
| 1-2 | `spi12_min <= -2.5` | < -2.5. |

`snow_burden` primary metric `snow_months_per_year` weight `0.333`:
| Score band | Condition | Descriptor |
| --- | --- | --- |
| 9-10 | `snow_months_per_year <= 1` | Negligible. |
| 7-8 | `snow_months_per_year <= 3` | Mild winter zone. |
| 5-6 | `snow_months_per_year <= 5` | CEE typical. |
| 3-4 | `snow_months_per_year <= 7` | Significant winter constraint. |
| 1-2 | `snow_months_per_year >= 8` | Arctic-grade design. |

`annual_precip` primary metric `mean_annual_precip_mm` weight `0.334`:
| Score band | Condition | Descriptor |
| --- | --- | --- |
| 9-10 | `mean_annual_precip_mm >= 400 and mean_annual_precip_mm <= 800` | Optimal. |
| 7-8 | `(mean_annual_precip_mm >= 300 and mean_annual_precip_mm < 400) or (mean_annual_precip_mm > 800 and mean_annual_precip_mm <= 1000)` | Manageable. |
| 5-6 | `(mean_annual_precip_mm >= 200 and mean_annual_precip_mm < 300) or (mean_annual_precip_mm > 1000 and mean_annual_precip_mm <= 1500)` | Tail risks emerging. |
| 3-4 | `(mean_annual_precip_mm >= 100 and mean_annual_precip_mm < 200) or (mean_annual_precip_mm > 1500 and mean_annual_precip_mm <= 2500)` | Significant adaptation. |
| 1-2 | `mean_annual_precip_mm < 100 or mean_annual_precip_mm > 2500` | Severe. |
## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only NH-only compiled-spec evaluation using local scoring helpers. No API, enrichment, web, or remote calls were made.
- `spi12_min`: present 0/361, NULL 361, top values none.
- `snow_months_per_year`: present 0/361, NULL 361, top values none.
- `mean_annual_precip_mm`: present 361/361, NULL 0, min 8.64, max 66.44, mean 25.1103.
- `extreme_precip_mm`: present 361/361, NULL 0, min 0.11, max 0.82, mean 0.2622.
- `freezing_days_per_year`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.freezing_days_per_year`=361; `site_natural_hazards.snow_months_per_year`=361; `site_natural_hazards.spi12_min`=361.

## Fail, Avoidance, And Review Conditions
No fail, avoidance, screen, or review conditions are defined.

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 3-4 | `e6ecead0` Porto Romano Power Station | AL | 4 | `spi12_min`=NULL<br>`snow_months_per_year`=NULL<br>`mean_annual_precip_mm`=41.41<br>sub_scores=annual_precip:1.5, drought_spi12:5, snow_burden:5 | partial_unscored |
| 3-4 | `c8f15aca` Nikola Tesla power station | RS | 4 | `spi12_min`=NULL<br>`snow_months_per_year`=NULL<br>`mean_annual_precip_mm`=22.08<br>sub_scores=annual_precip:1.5, drought_spi12:5, snow_burden:5 | partial_unscored |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-11 — Extreme precipitation rain snow and drought.md`.
- Validation: local NH-only scoring validation confirms unresolved measured inputs; no YAML behavior changed for this criterion.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
