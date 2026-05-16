<!-- man_hours: 1.4 -->
# NH-09 - River flooding

Status: final

Phase: `avoidance`, `ranking`

Primary metric: `river_distance_km`; active ranking evidence also uses `flood_zone_class_500yr`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 8, normalised weight 2.8%).

## Specialist Recommendation
Use the measured `flood_zone_class_500yr` branch as the Stage 1-2 ranking signal and do not let sparse river-distance/freeboard fields suppress it. The local flood-zone class is present for all 361 sites and is `negligible` for all rows; distance/freeboard remain Stage 3 hydrology confirmation inputs.

## Final State
NH-09 is closed with explicit bands in the NH spec/rubric and no distance/elevation recipe. Local NH-only validation after the YAML change gives `{'9-10': 361}`. A11 remains an avoidance caution tied to distance/freeboard where those values are measured; absent freeboard is not converted into an invented value.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `avoidance`, `ranking`; `participates_in_composite` is `true`. | Finalized with explicit flood-zone-class bands. |
| Score logic | Post-change local NH-only validation gives matched-band counts `{'9-10': 361}`. | Use measured `flood_zone_class_500yr` as the screening-stage ranking signal. |
| Data quality | Raw misses: `site_natural_hazards.elevation_above_design_flood_m`=361; `site_natural_hazards.river_distance_km`=348. | Treat distance/freeboard gaps as Stage 3 hydrology inputs, not as invented adverse values. |
| Threshold metadata | `threshold_metadata.yaml` exposes `A11` at 4 km with 30.5 m vertical separation. | Keep A11 static until compound threshold editing can preserve the fixed freeboard clause. |
| Filter relationship | Ranking plus avoidance. `A11` is an `avoidance_penalty`; current local flood-zone scoring is resolved from class evidence. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `flood_zone_class_500yr in ['none', 'negligible'] or river_distance_km >= 10 or elevation_above_design_flood_m >= 30.5` | Favourable flood-zone class or large measured separation. | 361 |
| 7-8 | `flood_zone_class_500yr == 'low' or river_distance_km >= 4 or elevation_above_design_flood_m >= 30.5` | Low class or project boundary met. | 0 |
| 5-6 | `flood_zone_class_500yr == 'moderate' or river_distance_km >= 2` | Moderate class or near-boundary distance. | 0 |
| 3-4 | `flood_zone_class_500yr == 'high'` | High class; Stage 3 flood-defense characterization priority. | 0 |
| 1-2 | `flood_zone_class_500yr in ['very_high', 'catastrophic']` | Severe measured flood class. | 0 |
| 0 | `flood_zone_class_500yr == 'catastrophic' and (has_remedy == false or has_remedy is null)` | Reserved for catastrophic class without remedy evidence. | 0 |
| unscored | no compiled band matched | no measured class/distance/freeboard branch matched | 0 |

## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through NH-only compiled-spec evaluation using local scoring helpers. No API, enrichment, web, or remote calls were made.
- `river_distance_km`: present 13/361, NULL 348, min 0, max 0, mean 0.
- `elevation_above_design_flood_m`: present 0/361, NULL 361, top values none.
- `flood_zone_class_500yr`: present 361/361, NULL 0, top values negligible=361.
- Raw misses: `site_natural_hazards.elevation_above_design_flood_m`=361; `site_natural_hazards.river_distance_km`=348.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `A11` | `avoidance_penalty` | `river_distance_km < 4 and elevation_above_design_flood_m < 30.5` | 0 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `e6ecead0` Porto Romano Power Station | AL | 9.5 | `river_distance_km`=0<br>`elevation_above_design_flood_m`=NULL<br>`flood_zone_class_500yr`=negligible | matched accepted logic |
| 9-10 | `d30af109` Kolubara B power station | RS | 9.5 | `river_distance_km`=NULL<br>`elevation_above_design_flood_m`=NULL<br>`flood_zone_class_500yr`=negligible | matched accepted logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: aliases from `flood_zone_class` to `flood_zone_class_500yr` and from `nearest_river_km` to `river_distance_km`.

## Artifact Footer
- Landed file: `criteria/ranking/NH-09 — River flooding.md`.
- Validation: local NH-only scoring validation after YAML synchronization: `{"9-10": 361}`.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
