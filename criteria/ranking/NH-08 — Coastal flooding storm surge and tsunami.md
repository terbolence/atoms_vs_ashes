<!-- man_hours: 1.4 -->
# NH-08 - Coastal flooding (storm surge, tsunami)

Status: final

Phase: `avoidance`, `ranking`

Primary metric: `coast_distance_km`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 6, normalised weight 2.1%).

## Specialist Recommendation
Use the explicit hand-written coastal-flood bands instead of the distance-only recipe. S-38 Natural Earth now provides measured `coast_distance_km` for all 361 merged sites, while `elevation_m` remains measured for all sites and `country_is_landlocked` is derived locally. Missing coast distance is a data gap, not coastal exposure; inland river settings such as Braila should be handled by NH-09 for river flooding.

## Final State
NH-08 is closed with explicit bands in the NH spec/rubric: landlocked, measured `coast_distance_km > 50`, or elevation >= 50 m AMSL resolves to the favourable screening band when no moderate/high marine proxy contradicts it. Low-elevation sites only receive A9 when measured sea-coast distance is <10 km or positive storm-surge / tsunami proxy evidence exists. Local NH-only validation after S-38 gives `{'9-10': 287, '7-8': 11, '5-6': 4, '3-4': 16, '0-0': 43}` and 64 A9 triggers.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `avoidance`, `ranking`; `participates_in_composite` is `true`. | Finalized with explicit bands that preserve measured elevation and derived landlocked branches. |
| Score logic | S-38 dry run gives complete measured coast-distance coverage for 361 sites. | Use measured sea-coast distance for distance bands; do not infer coastal exposure from non-landlocked country status. |
| Data quality | `coast_distance_km` is populated by Natural Earth 1:50m coastline; `storm_surge_class` remains sparse and `tsunami_zone_flag` remains unavailable. | Treat storm-surge / tsunami classes as positive proxy signals only when populated. |
| Threshold metadata | No active A9 metadata entry was edited in this worker; A9 is kept as a caution expression in YAML. | Do not invent coast distance; preserve A9 as a screening caution. |
| Filter relationship | Ranking plus avoidance. `A9` is an `avoidance_penalty`; low-elevation non-landlocked sites with unresolved coast distance now surface a caution. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `country_is_landlocked == true or coast_distance_km > 50 or elevation_m >= 50` | Landlocked, non-coastal, or elevation-safe at screening scale. | 277 |
| 7-8 | `coast_distance_km >= 10 and storm_surge_class in [null, 'none', 'low', 'fluvial_proxy'] and tsunami_zone_flag in [null, 'none', 'low']` | Measured >=10 km from coast with no moderate/high marine-hazard signal. | 11 |
| 5-6 | `(coast_distance_km >= 5 and coast_distance_km < 10) or (coast_distance_km is null and storm_surge_class == 'fluvial_proxy')` | 5-10 km from coast, or unresolved distance with weak near-coastal GFMS proxy. | 4 |
| 3-4 | `(coast_distance_km >= 2 and coast_distance_km < 5) or storm_surge_class == 'moderate' or tsunami_zone_flag == 'moderate'` | 2-5 km from coast or moderate marine-hazard proxy. | 16 |
| 1-2 | `(coast_distance_km < 2 or storm_surge_class == 'high' or tsunami_zone_flag == 'high') and has_remedy == true` | Severe marine-hazard evidence with documented mitigation. | 0 |
| 0 | `(coast_distance_km < 2 or storm_surge_class == 'high' or tsunami_zone_flag == 'high') and (has_remedy == false or has_remedy is null)` | Severe marine-hazard evidence without documented mitigation. | 43 |
| unscored | no compiled band matched | Missing measured coast distance and no other resolving evidence. | 0 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB plus S-38 Natural Earth dry run. One consented external Natural Earth download was vendored; scoring/backfill runs are local-only after that.
- `coast_distance_km`: S-38 dry-run coverage 361/361; buckets `<2`=49, `2-5`=27, `5-10`=6, `10-50`=36, `>50`=243.
- `storm_surge_class`: present 2/361, NULL 359, top values fluvial_proxy=2.
- `tsunami_zone_flag`: present 0/361, NULL 361, top values none.
- `elevation_m`: present 361/361, NULL 0, min -0.17, max 2450.17, mean 271.9772.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `A9` | `avoidance_penalty` | `(coast_distance_km < 10 or storm_surge_class in ['fluvial_proxy', 'moderate', 'high'] or tsunami_zone_flag in ['moderate', 'high']) and elevation_m < 50` | 64 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `29836b52` Braila power station | RO | 9.5 expected | `coast_distance_km`=81.043<br>`elevation_m`=13.51<br>`country_is_landlocked`=False | inland from sea; Danube flooding belongs to NH-09 |
| 0-2 / A9 | `e6ecead0` Porto Romano Power Station | AL | low expected | `coast_distance_km`=1.836<br>`elevation_m`=-0.17<br>`country_is_landlocked`=False | measured low-lying coastal exposure |
| 7-8 | Varna power station | BG | 7.5 | `coast_distance_km`=13.288<br>`elevation_m`=6.12<br>`storm_surge_class`=fluvial_proxy | near-coastal GFMS proxy; A9 caution remains because proxy evidence is positive |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: derived context values such as `has_remedy`, landlocked country flags, and BF-02 required/ideal area fields.
- `data/cartography/ne_50m_coastline.geojson` and `src/atoms_vs_ashes/connectors/natural_earth/coastline.py`: S-38 measured sea-coast distance source.

## Artifact Footer
- Landed file: `criteria/ranking/NH-08 — Coastal flooding storm surge and tsunami.md`.
- Validation: S-38 dry run over 361 sites: `{"<2": 49, "2-5": 27, "5-10": 6, "10-50": 36, ">50": 243}`; NH-only replay after YAML/backfill: `{"9-10": 287, "7-8": 11, "5-6": 4, "3-4": 16, "0-0": 43}`, A9 triggers `64`.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
