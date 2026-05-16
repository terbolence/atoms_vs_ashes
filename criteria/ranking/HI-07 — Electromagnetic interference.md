<!-- man_hours: 0.3 -->
# HI-07 - Electromagnetic interference - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. The current scoreable surface is retained as the documented screening runtime state. The unanchored `nearest_transmitter_km` and unavailable `transmitter_power_class` evidence are routed to deferred schema/spec cleanup.

Phase: `[ranking]`  
Primary metric: `transmitter_count_10km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: none. HI-07 is ranking-only.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation only. Only count-only bands can fire through the normal resolver. |
| Anchored fields | `db_fields.api` lists only `site_human_induced.transmitter_count_10km`; resolver aliases it to `transmitter_count`. |
| Unanchored band fields | `nearest_transmitter_km` is populated in schema but not listed in `db_fields.api`; `transmitter_power_class` is not a local schema column. |
| Runtime evidence | Local resolver recompute: 5 rows in 5-6 and 356 unscored. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `transmitter_count_10km == 0` | 0 |
| 7-8 | `transmitter_count_10km <= 2 and nearest_transmitter_km > 5` | 0 |
| 5-6 | `transmitter_count_10km <= 5` | 5 |
| 3-4 | `nearest_transmitter_km < 2` | 0 through resolver because field is not anchored |
| 1-2 | `nearest_transmitter_km < 0.5 and transmitter_power_class == 'very_high'` | 0 through resolver because power class is unavailable |
| Unscored | Count >5 and no anchored distance/power fields available to match lower bands | 356 |

## Metric Truth And Data Quality

`site_human_hazards` stores `nearest_transmitter_km`, `transmitter_type`, `transmitter_count`, `hi07_quality`, and `hi07_comment`. `transmitter_count_10km` is an alias to `transmitter_count`. No local `transmitter_power_class` column or derivation was found.

Because `nearest_transmitter_km` is not in `db_fields.api`, the normal resolver does not expose it to the band evaluator for HI-07. This means dense transmitter environments with nearby transmitters often become neutral unscored rows instead of matching the lower bands.

## Scored Examples

| Band | Site | Country | Runtime evidence | Score |
| --- | --- | --- | --- | ---: |
| 5-6 | Gacko Thermal Power Plant | BA | `transmitter_count_10km = 3` | 5.5 |
| 5-6 | Miljevina power station | BA | `transmitter_count_10km = 5` | 5.5 |
| Unscored | Porto Romano Power Station | AL | count 66, no anchored lower-band distance/power fields | 5.0 |
| Unscored | Duernrohr power station | AT | count 313, no anchored lower-band distance/power fields | 5.0 |
| 9-10 / 7-8 / 3-4 / 1-2 | No local resolver rows | - | Empty bands | - |

## Specialist recommendation

Retain the current YAML for this worker. Adding `nearest_transmitter_km` to `db_fields.api` is a plausible low-level spec cleanup, but it would make lower bands newly scoreable for dense transmitter environments and should be paired with an impact check. `transmitter_power_class` remains unmeasured locally, so the 1-2 band cannot be fully supported without schema or derivation work.

Stage 3 characterization should confirm transmitter distance, transmitter type, and power class where EMI is relevant to safety-related communications or controls. A deferred scoring update should either add anchored distance and power-class evidence or explicitly rework HI-07 as a count-only screening proxy.

## Final state

No YAML change is implemented. HI-07 remains partly scoreable under the current count-only screening runtime, with 5 rows in 5-6 and 356 neutral unscored rows in the documented recompute. The unanchored distance field and missing power-class field are documented limitations, not grounds for invented lower-band scores.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/atoms_vs_ashes/scoring/merge_resolver.py`, `src/atoms_vs_ashes/analysis/transmitter_proximity.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
