<!-- man_hours: 0.35 -->
# HI-01 - Aircraft crash hazard - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. Current ranking behavior is retained as the documented screening runtime state, while the A3 NULL semantics, nearest-major-airport shadowing, and A1/A4 caution-vs-score drift are routed to Stage 3 characterization or a later resolver/schema improvement.

Phase: `[avoidance, ranking]`  
Primary metric: `composite` (class-aware airport and military-airfield expressions)  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: `A1`, `A2`, `A3`, and `A4` emit `avoidance_penalty` verdicts (`caution` when triggered).

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation. Spec/rubric bands match each other, but the documented caveats remain unresolved evidence-model limitations. |
| A-code relationship | A1-A4 are active avoidance conditions and are not user-tunable in `threshold_metadata.yaml`. |
| Runtime evidence | Local resolver recompute produced 323 rows in 9-10, 13 in 7-8, 22 in 3-4, 3 in 1-2, and no unscored rows. |
| Remaining Stage 3/schema issue | Existing avoidance audit found A3 universally inconclusive in replay, A2 can miss major-airport evidence shadowed by a nearer small/heliport feature, and A1/A4 cautions can coexist with a 9.5 score. |

## Current Score Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | No airport in radius; or only small/GA/heliport with no military airbase; or major airport >30 km and no military airbase | 323 |
| 7-8 | Major airport 15-30 km and no overhead flight-path signal | 13 |
| 5-6 | Airport >=8 km or military airbase >=30 km | 0 |
| 3-4 | Major airport <15 km or military airbase <30 km | 22 |
| 1-2 | Large airport <8 km or military airbase <16 km | 3 |
| 0 | Under flight path of major airport | 0 |

## Metric Truth And Data Quality

`site_human_hazards` stores the nearest-airport fields (`nearest_airport_km`, `nearest_airport_type`, `nearest_airport_class`, `flight_path_distance_km`, `hi01_quality`) and military fields populated under HI-06. `nearest_military_airfield_km` is derived from `nearest_high_consequence_military_*` or `nearest_military_class` when the military class is `airfield`; completed-search no-airfield remains `None`.

The current scoring expressions use `nearest_airport_class`, `nearest_airport_km`, `nearest_military_airfield_km`, `under_flight_path`, and `flight_path_distance_km`. `under_flight_path` is derived as `false` when `flight_path_distance_km` is present, so A4 currently fires through the numeric `< 4 km` branch rather than an explicit overhead-route boolean.

## Scored Examples

| Band | Site | Country | Key evidence | Score |
| --- | --- | --- | --- | ---: |
| 9-10 | Duernrohr power station | AT | `nearest_airport_class = heliport`; no military airfield derived | 9.5 |
| 7-8 | Porto Romano Power Station | AL | `large_airport` at 25.11 km | 7.5 |
| 3-4 | Mellach power station | AT | `large_airport` at 10.05 km | 3.5 |
| 1-2 | Glinica power station | BA | `large_airport` at 6.74 km | 1.5 |
| 5-6 / 0 | No local rows in resolver recompute | - | Empty bands | - |

## Specialist recommendation

Retain the current YAML for this worker. The current score curve is internally synchronized between the spec and rubric, and the local recompute produced measured distance/class evidence for all rows. The remaining issues require either new resolver semantics or additional class-specific fields, not a safe YAML-only edit.

Stage 3 characterization should separate completed-search no-military-airfield evidence from genuinely missing military-airfield evidence, collect nearest major/medium airport distance independently of the nearest airport of any class, and confirm whether broad A1/A4 caution flags are intended to influence ranking score or remain independent avoidance flags.

## Final state

No YAML change is implemented. HI-01 remains scoreable under the current screening runtime, with 323 rows in 9-10, 13 in 7-8, 22 in 3-4, 3 in 1-2, and no unscored rows in the documented recompute. The A1-A4 caveats are carried as Stage 3 evidence-model work items rather than converted into invented scoring values.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `criteria/avoidance/HI-01_A1-A4_aircraft_crash_hazard.md`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/atoms_vs_ashes/db/models.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, avoidance audit, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
