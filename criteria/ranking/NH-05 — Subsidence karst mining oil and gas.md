<!-- man_hours: 0.8 -->
# NH-05 - Subsidence / karst / mining / oil & gas

Status: accepted-current-state

Phase: `ranking`

Primary metric: `mining_void_distance_km`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 7, normalised weight 2.5%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'1-2': 7, '3-4': 20, '5-6': 87, '7-8': 25, '9-10': 222}`. | Document current compiled behavior, not a proposed change. |
| Data quality | Raw misses: `site_natural_hazards.karst_formation_type`=278; `site_natural_hazards.mining_void_distance_km`=261; `site_natural_hazards.subsidence_risk_class`=361. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Threshold metadata | `threshold_metadata.yaml` exposes `E6` as an editable 2 km mine-feature review pivot, but both `E5` and `E6` are review-only false expressions today. | Record the metadata relationship. |
| Filter relationship | Ranking-only geotechnical review signal. `E5` and `E6` are review flags with `false`, so no automatic score or exclusion effect is applied. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `karst_severity == 'none' and subsidence_risk_class in [null, 'none'] and (mining_void_distance_km >= 10.0 or mining_void_distance_km is null)` | No karst; mine-feature distance well above the score-5 pivot (or unknown). | 222 |
| 7-8 | `karst_severity in [null, 'none'] and subsidence_risk_class in [null, 'none', 'low'] and (mining_void_distance_km >= 4.0 or mining_void_distance_km is null)` | Clear mine-distance margin with low geotechnical proxy risk (or unknown). | 25 |
| 5-6 | `karst_severity in [null, 'none', 'moderate'] and (mining_void_distance_km is null or mining_void_distance_km >= 2.0) and subsidence_risk_class in [null, 'none', 'low', 'moderate', 'high']` | At or above the mine-distance score-5 pivot; review possible. | 87 |
| 3-4 | `mining_void_distance_km >= 1.0 and mining_void_distance_km < 2.0 and karst_severity != 'high'` | Below the mine-distance pivot but not extreme. | 20 |
| 1-2 | `mining_void_distance_km < 1.0 or karst_severity == 'high'` | Close mine feature or high karst proxy; severe review signal. | 7 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `mining_void_distance_km`: present 100/361, NULL 261, min 0.13, max 13.222, mean 4.6105.
- `karst_severity`: present 361/361, NULL 0, top values none=278, moderate=82, high=1.
- `karst_formation_type`: present 83/361, NULL 278, top values carbonate (Continuous carbonate rocks)=46, carbonate (Discontinuous carbonate rocks)=36, mixed (Mixed carbonate and evaporite rocks)=1.
- `subsidence_risk_class`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.karst_formation_type`=278; `site_natural_hazards.mining_void_distance_km`=261; `site_natural_hazards.subsidence_risk_class`=361.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `E5` | `review_flag` | `false` | 0 | 0 |
| `E6` | `review_flag` | `false` | 0 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `1719d38b` Trebisov power station | SK | 9.5 | `mining_void_distance_km`=10.206<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 9-10 | `7b4d3f8f` Burnaz power station | TR | 9.5 | `mining_void_distance_km`=NULL<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 7-8 | `44d40276` Olomouc power station | CZ | 7.5 | `mining_void_distance_km`=4.005<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 7-8 | `3bd2a957` Myronivskyi power station | UA | 7.5 | `mining_void_distance_km`=5.355<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 5-6 | `20bce4f5` Porici power station | CZ | 5.5 | `mining_void_distance_km`=2.211<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 5-6 | `0b187a1d` Leczna Power Station (Bogdanka SA) | PL | 5.5 | `mining_void_distance_km`=12.016<br>`karst_severity`=moderate<br>`subsidence_risk_class`=NULL | matched current logic |
| 3-4 | `06defca3` Martinska power station | SK | 3.5 | `mining_void_distance_km`=1.146<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 3-4 | `1c059a42` Malesice power station | CZ | 3.5 | `mining_void_distance_km`=1.601<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 1-2 | `43e5b2b4` Karvina power station | CZ | 1.5 | `mining_void_distance_km`=0.13<br>`karst_severity`=none<br>`subsidence_risk_class`=NULL | matched current logic |
| 1-2 | `aa0bdb5e` Miljevina power station | BA | 1.5 | `mining_void_distance_km`=0.571<br>`karst_severity`=moderate<br>`subsidence_risk_class`=NULL | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-05 — Subsidence karst mining oil and gas.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
