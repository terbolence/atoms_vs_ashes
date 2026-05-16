<!-- man_hours: 0.8 -->
# NH-06 - Foundation conditions (bearing, bedrock, groundwater)

Status: accepted-current-state

Phase: `ranking`

Primary metric: `bearing_capacity_kpa`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 5, normalised weight 1.8%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'0': 14, '3-4': 98, '5-6': 249}`. | Document current compiled behavior, not a proposed change. |
| Data quality | Raw misses: `site_natural_hazards.bearing_capacity_kpa`=53; `site_natural_hazards.depth_to_bedrock_m`=5; `site_natural_hazards.groundwater_depth_m`=361. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Filter relationship | Ranking-only support criterion. Poor foundation bands affect ranking only; hard exclusions remain in NH-03/NH-04/NH-05. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `bearing_capacity_kpa > 200 and depth_to_bedrock_m < 5 and groundwater_depth_m > 5` | Bearing > 200 kPa; bedrock < 5 m; GW > 5 m. | 0 |
| 7-8 | `bearing_capacity_kpa >= 150 and depth_to_bedrock_m <= 10 and groundwater_depth_m >= 3` | Bearing 150-200 kPa; bedrock 5-10 m; GW 3-5 m. | 0 |
| 5-6 | `bearing_capacity_kpa >= 80` | Typical European mixed conditions (bearing 80-150 kPa). | 249 |
| 3-4 | `bearing_capacity_kpa >= 50 or depth_to_bedrock_m > 20 or groundwater_depth_m < 2` | Bearing 50-80 kPa; bedrock > 20 m; GW < 2 m. | 98 |
| 1-2 | `bearing_capacity_kpa < 50` | Bearing < 50 kPa or persistent artesian GW. | 0 |
| 0 | `default` | Reserved (cross-link to NH-03/NH-05 exclusions only). | 14 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `bearing_capacity_kpa`: present 308/361, NULL 53, min 53.5, max 133, mean 86.2955.
- `depth_to_bedrock_m`: present 356/361, NULL 5, min 0.19, max 57.08, mean 20.6447.
- `groundwater_depth_m`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.bearing_capacity_kpa`=53; `site_natural_hazards.depth_to_bedrock_m`=5; `site_natural_hazards.groundwater_depth_m`=361.

## Fail, Avoidance, And Review Conditions
No fail, avoidance, screen, or review conditions are defined.

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 5-6 | `0ae8917b` Pribram power station | CZ | 5.5 | `bearing_capacity_kpa`=80<br>`depth_to_bedrock_m`=21.29<br>`groundwater_depth_m`=NULL | matched current logic |
| 5-6 | `a23d073a` Ugljevik power station | BA | 5.5 | `bearing_capacity_kpa`=88<br>`depth_to_bedrock_m`=18.05<br>`groundwater_depth_m`=NULL | matched current logic |
| 3-4 | `5a57ae0a` Murcki-Staszic power station | PL | 3.5 | `bearing_capacity_kpa`=53.5<br>`depth_to_bedrock_m`=24.28<br>`groundwater_depth_m`=NULL | matched current logic |
| 3-4 | `ab151830` Plomin power station | HR | 3.5 | `bearing_capacity_kpa`=77.3<br>`depth_to_bedrock_m`=18.2<br>`groundwater_depth_m`=NULL | matched current logic |
| 0 | `d3b5a049` Bedzin power station | PL | 0 | `bearing_capacity_kpa`=NULL<br>`depth_to_bedrock_m`=18.49<br>`groundwater_depth_m`=NULL | matched current logic |
| 0 | `161660e7` DOSAB cogeneration plant | TR | 0 | `bearing_capacity_kpa`=NULL<br>`depth_to_bedrock_m`=11.61<br>`groundwater_depth_m`=NULL | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-06 — Foundation conditions.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
