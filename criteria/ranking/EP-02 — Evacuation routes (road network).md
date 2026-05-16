<!-- man_hours: 0.25 -->
# EP-02 - Evacuation routes (road network) - ranking state

Status: **ACCEPTED CURRENT STATE** for ranking documentation. No blocking scoring issue was identified in this pass.

Phase: `[ranking]`  
Primary metric: `road_density_km_per_km2`  
Source spec/rubric: `config/scoring_specs/ep_emergency_planning.yaml`; `config/scoring_rubrics/ep_emergency_planning.yaml`  
Composite participation: **true**

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted. Road density increases score; top band also requires motorway access. |
| Review flag | `data_caveat_ll017` fires when `road_density_km_per_km2 == 0`; it is a review flag only and does not change the ranking score. |
| Threshold metadata | None. EP-02 has no user-tunable fail threshold. |
| Current DB coverage | 361/361 local merged rows have `road_density_km_per_km2` and `has_motorway_access`. |

## Current Score Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `road_density_km_per_km2 >= 2.0 and has_motorway_access == true` | 0 |
| 7-8 | `road_density_km_per_km2 >= 1.0` | 38 |
| 5-6 | `road_density_km_per_km2 >= 0.5` | 149 |
| 3-4 | `road_density_km_per_km2 >= 0.3` | 125 |
| 1-2 | `road_density_km_per_km2 < 0.3` | 49 |
| Unscored | No band matched | 0 |

## Metric Truth And Data Quality

`road_density_km_per_km2`, `total_road_km`, `has_motorway_access`, `ep02_quality`, and `ep02_comment` are stored on `site_emergency_planning`. The scoring expression consumes `road_density_km_per_km2` and `has_motorway_access`; `total_road_km` is supporting evidence only.

NULL road-density values would be unscored at the pass-mark default. Exact zero values trigger `data_caveat_ll017`, reflecting the local LL-017 silent-null concern. Current local examples in this recompute used medium-quality EP-02 rows.

## Scored Examples

| Band | Site | Country | Road density | Motorway access | Score |
| --- | --- | --- | ---: | --- | ---: |
| 7-8 | Duernrohr power station | AT | 1.130 | true | 7.5 |
| 5-6 | Mellach power station | AT | 0.968 | true | 5.5 |
| 3-4 | Porto Romano Power Station | AL | 0.333 | true | 3.5 |
| 1-2 | Banovici power station | BA | 0.250 | false | 1.5 |
| 9-10 | No local rows | - | - | - | - |

## Sources And Validation

Sources: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_resolver.py`.

Validation: local-only spec compile and merged-DB band recompute. No live API, enrichment, web, code, tests, or YAML changes.
