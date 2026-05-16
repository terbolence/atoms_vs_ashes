<!-- man_hours: 0.3 -->
# HI-08 - Other nuclear installations - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. `nearest_nuclear_km` and `hi08_quality` remain unmeasured at this stage. The current runtime state is documented as a screening-stage data gap and routed to Stage 3 characterization or a later connector/schema improvement.

Phase: `[ranking]`  
Primary metric: `nearest_nuclear_km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: none. HI-08 is ranking-only.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation only because no local rows can exercise the metric or completed-search sentinel. |
| Metric coverage | 0/361 local merged rows have `nearest_nuclear_km`; 0/361 have `hi08_quality`. |
| Sentinel | `hi08_search_completed` is derived from `hi08_quality`; it is false for all rows in this pass. |
| Runtime evidence | 361/361 rows are unscored with raw misses for `nearest_nuclear_km` and `hi08_quality`. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | Completed search with null distance, or `nearest_nuclear_km > 100` | 0 |
| 7-8 | `nearest_nuclear_km >= 50` | 0 |
| 5-6 | `nearest_nuclear_km >= 20` | 0 |
| 3-4 | `nearest_nuclear_km >= 5` | 0 |
| 1-2 | `nearest_nuclear_km < 5` | 0 |
| Unscored | No metric / no completed-search sentinel | 361 |

## Metric Truth And Data Quality

`nearest_nuclear_km`, `nearest_nuclear_name`, `hi08_quality`, and `hi08_comment` are stored on `site_human_hazards`, but were not populated in the local merged DB used for this pass. The current rubric comments note that reactor-type distinction is a future follow-up; today only nearest distance is represented.

With both distance and quality absent, NULL is not treated as "no installation found"; it is missing evidence and returns neutral pass-mark default (`5.0`, unscored). This should be read as an evidence gap, not as absence of other nuclear installations.

## Scored Examples

No local scored examples are available. Representative unscored rows include Porto Romano Power Station (AL) and Duernrohr power station (AT): both have `nearest_nuclear_km = null`, `hi08_search_completed = false`, and score `5.0` with `unscored`.

## Specialist recommendation

Retain the current YAML for this worker and treat HI-08 as unmeasured at this stage. The current spec/rubric ladder is coherent, but 361/361 local rows lack both the nuclear-installation distance and the quality sentinel needed to distinguish completed searches from missing evidence. Facility type semantics are also not represented in the current local score inputs.

Stage 3 characterization should confirm the nearest relevant nuclear installation, its distance, and its facility type or interface relevance. If the project wants this criterion to score before Stage 3, a deferred connector/schema update should populate `nearest_nuclear_km`, `nearest_nuclear_name`, and `hi08_quality` before re-documenting band counts.

## Final state

No YAML change is implemented. HI-08 remains in the composite as a ranking criterion, but local rows stay at the neutral unscored runtime state (`5.0`, `unscored`) until nuclear-installation proximity and quality evidence are populated. This is a screening-stage limitation, not a finding that no interface exists.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/atoms_vs_ashes/llm/prompts/ranking.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
