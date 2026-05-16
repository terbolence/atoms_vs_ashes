<!-- man_hours: 0.3 -->
# HI-05 - Transport hazards (hazmat road / rail / pipe) - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. `nearest_hazmat_corridor_km` and `hi05_quality` remain unmeasured at this stage. The current runtime state is documented as a screening-stage data gap and routed to Stage 3 characterization or a later connector/schema improvement.

Phase: `[ranking]`  
Primary metric: `nearest_hazmat_corridor_km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: none. HI-05 is ranking-only.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation only because no local rows can exercise the metric. |
| Metric alias | `nearest_hazmat_corridor_km` aliases to `hazmat_route_distance_km`, but the local merged DB has no populated values in this pass. |
| Sentinel | `hi05_search_completed` is derived from `hi05_quality`; `hi05_quality` was absent for 361/361 rows. |
| Runtime evidence | 361/361 rows are unscored with raw misses for `nearest_hazmat_corridor_km` and `hi05_quality`. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | Completed search with null distance, or `nearest_hazmat_corridor_km > 10` | 0 |
| 7-8 | `nearest_hazmat_corridor_km >= 5` | 0 |
| 5-6 | `nearest_hazmat_corridor_km >= 2` | 0 |
| 3-4 | `nearest_hazmat_corridor_km >= 1` | 0 |
| 1-2 | `nearest_hazmat_corridor_km < 1` | 0 |
| 0 | `nearest_hazmat_corridor_km < 0.1 and has_pinch_point == true` | 0 |
| Unscored | No metric / no completed-search sentinel | 361 |

## Metric Truth And Data Quality

`hazmat_route_distance_km`, `hi05_quality`, and `hi05_comment` are stored on `site_human_hazards`; `nearest_hazmat_corridor_km` is a resolver alias. The current bands also reference `has_pinch_point`, which is not a current local schema column or derived context value.

With both distance and quality absent, the criterion returns the neutral pass-mark default (`5.0`, unscored) for every local row. This should be read as missing screening evidence, not as absence of transport hazards.

## Scored Examples

No local scored examples are available. Representative unscored rows include Porto Romano Power Station (AL) and Duernrohr power station (AT): both have `nearest_hazmat_corridor_km = null`, `hi05_search_completed = false`, and score `5.0` with `unscored`.

## Specialist recommendation

Retain the current YAML for this worker and treat HI-05 as unmeasured at this stage. The current spec/rubric ladder is coherent, but 361/361 local rows lack both the hazmat-corridor metric and the quality sentinel needed to distinguish completed searches from missing evidence. The inactive `has_pinch_point` 0-band also lacks a local measured field.

Stage 3 characterization should identify major hazmat road, rail, and pipeline corridors near the candidate footprint, populate `hazmat_route_distance_km` and `hi05_quality`, and decide whether pinch-point evidence is a measured scoring input or a separate qualitative review item.

## Final state

No YAML change is implemented. HI-05 remains in the composite as a ranking criterion, but local rows stay at the neutral unscored runtime state (`5.0`, `unscored`) until corridor distance and quality evidence are populated. This is a screening-stage limitation, not a transport-hazard clearance.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/atoms_vs_ashes/scoring/merge_resolver.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
