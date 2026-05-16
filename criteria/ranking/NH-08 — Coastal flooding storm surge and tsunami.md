<!-- man_hours: 1.0 -->
# NH-08 - Coastal flooding (storm surge, tsunami)

Status: final

Phase: `avoidance`, `ranking`

Primary metric: `coast_distance_km`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 6, normalised weight 2.1%).

## Specialist Recommendation
Use the explicit hand-written coastal-flood bands instead of the distance-only recipe. `coast_distance_km` is unmeasured for all 361 sites, but `elevation_m` is measured for all sites and `country_is_landlocked` is derived locally; those existing branches can be used without inventing a coastal distance. Low-elevation, non-landlocked sites with unresolved coast distance remain unscored and receive an A9 caution for Stage 3 coastal-flood and tsunami confirmation.

## Final State
NH-08 is closed with explicit bands in the NH spec/rubric: landlocked or elevation >= 50 m AMSL resolves to the favourable screening band, while unresolved low-elevation coastal exposure remains a Stage 3 characterization gap. Local NH-only validation after the YAML change gives `{'9-10': 277, 'unscored': 84}`.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `avoidance`, `ranking`; `participates_in_composite` is `true`. | Finalized with explicit bands that preserve measured elevation and derived landlocked branches. |
| Score logic | Post-change local NH-only validation gives matched-band counts `{'9-10': 277, 'unscored': 84}`. | Remove/avoid the distance-only recipe path; unresolved low-elevation non-landlocked cases remain unscored. |
| Data quality | Raw misses: `site_natural_hazards.coast_distance_km`=361; `site_natural_hazards.storm_surge_class`=359; `site_natural_hazards.tsunami_zone_flag`=361. | Use `elevation_m` and `country_is_landlocked` where locally available; route unresolved coastal distance to Stage 3. |
| Threshold metadata | No active A9 metadata entry was edited in this worker; A9 is kept as a caution expression in YAML. | Do not invent coast distance; preserve A9 as a screening caution. |
| Filter relationship | Ranking plus avoidance. `A9` is an `avoidance_penalty`; low-elevation non-landlocked sites with unresolved coast distance now surface a caution. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `country_is_landlocked == true or coast_distance_km > 50 or elevation_m >= 50` | Landlocked, non-coastal, or elevation-safe at screening scale. | 277 |
| 7-8 | `coast_distance_km >= 10 and storm_surge_class in ['none', 'low']` | Measured coastal distance with low surge class. | 0 |
| 5-6 | `coast_distance_km >= 5` | 5-10 km from coast; mitigation feasibility remains a Stage 3 item. | 0 |
| 3-4 | `coast_distance_km >= 2` | 2-5 km from coast; high coastal-flood characterization priority. | 0 |
| 1-2 | `coast_distance_km < 2` | Close coastal exposure if measured. | 0 |
| 0 | `coast_distance_km < 2 and has_remedy == false` | Reserved for measured close exposure with no remedy evidence. | 0 |
| unscored | no compiled band matched | Low-elevation, non-landlocked site with unresolved coastal distance. | 84 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only NH-only compiled-spec evaluation using local scoring helpers. No API, enrichment, web, or remote calls were made.
- `coast_distance_km`: present 0/361, NULL 361, top values none.
- `storm_surge_class`: present 2/361, NULL 359, top values fluvial_proxy=2.
- `tsunami_zone_flag`: present 0/361, NULL 361, top values none.
- `elevation_m`: present 361/361, NULL 0, min -0.17, max 2450.17, mean 271.9772.
- Raw misses: `site_natural_hazards.coast_distance_km`=361; `site_natural_hazards.storm_surge_class`=359; `site_natural_hazards.tsunami_zone_flag`=361.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `A9` | `avoidance_penalty` | `(coast_distance_km < 10 or (coast_distance_km is null and country_is_landlocked != true)) and elevation_m < 50` | 84 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `6e7fc4d8` Duernrohr power station | AT | 9.5 | `coast_distance_km`=NULL<br>`elevation_m`=192.34<br>`country_is_landlocked`=True | matched accepted logic |
| 9-10 | `cdb6adfb` Trypilska power station | UA | 9.5 | `coast_distance_km`=NULL<br>`elevation_m`=97.57<br>`country_is_landlocked`=False | matched accepted logic |
| unscored | `e6ecead0` Porto Romano Power Station | AL | 5 | `coast_distance_km`=NULL<br>`elevation_m`=-0.17<br>`country_is_landlocked`=False | unresolved coastal distance; A9 caution |
| unscored | `c9c85786` Gölovası power station | TR | 5 | `coast_distance_km`=NULL<br>`elevation_m`=19.13<br>`country_is_landlocked`=False | unresolved coastal distance; A9 caution |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: derived context values such as `has_remedy`, landlocked country flags, and BF-02 required/ideal area fields.

## Artifact Footer
- Landed file: `criteria/ranking/NH-08 — Coastal flooding storm surge and tsunami.md`.
- Validation: local NH-only scoring validation after YAML synchronization: `{"9-10": 277, "unscored": 84}`.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
