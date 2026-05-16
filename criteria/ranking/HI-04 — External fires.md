<!-- man_hours: 0.3 -->
# HI-04 - External fires - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. The no-A-code current state is retained as the documented screening runtime state. The unreachable 0-band and inactive `nearest_pipeline_km` evidence are routed to deferred scoring-policy and data-model cleanup rather than changed in YAML by this worker.

Phase: `[avoidance, ranking]`  
Primary metric: `nearest_flammable_storage_km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: no active fail condition. The `avoidance` phase is documentation/UI role only; A7 is currently owned by HI-02.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Active A-code | None. `fail_conditions: []`; no HI-04 screening verdicts are emitted. |
| Ranking bands | Accepted as current runtime documentation. They are mostly scoreable and sentinel-aware, but the final 0-band is shadowed by `< 1 km`. |
| NULL behavior | `nearest_flammable_storage_km is null` scores 9-10 only when `hi04_search_completed == true`. |
| Pipeline field | `nearest_pipeline_km` exists in schema/spec anchors but was 0/361 populated and is not used by bands. |

## Current Score Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | Completed search with null distance, or `nearest_flammable_storage_km > 15` | 308 |
| 7-8 | `nearest_flammable_storage_km >= 8` | 2 |
| 5-6 | `nearest_flammable_storage_km >= 4` | 4 |
| 3-4 | `nearest_flammable_storage_km >= 1` | 0 |
| 1-2 | `nearest_flammable_storage_km < 1` | 0 |
| 0 | `nearest_flammable_storage_km < 0.2 and has_mitigation == false` | 0 |
| Unscored | Null without completed-search evidence | 47 |

## Metric Truth And Data Quality

`nearest_flammable_storage_km`, `nearest_pipeline_km`, `hi04_quality`, and `hi04_comment` are stored on `site_human_hazards`. `hi04_search_completed` is derived from `hi04_quality` and controls favourable NULL scoring. `has_mitigation` is not a real HI-04 DB field, schema column, or derived context value beyond the generic explicit NULL helper.

The active no-A-code state matches the current A-code catalog: major-hazard storage avoidance is covered under HI-02/A7, not HI-04.

## Scored Examples

| Band | Site | Country | `nearest_flammable_storage_km` | Score |
| --- | --- | --- | ---: | ---: |
| 9-10 | Duernrohr power station | AT | null, completed search | 9.5 |
| 7-8 | Jaworzno power station | PL | 14.85 | 7.5 |
| 5-6 | Ruse Iztok power station | BG | 5.24 | 5.5 |
| Unscored | Porto Romano Power Station | AL | null, search not completed | 5.0 |
| 3-4 / 1-2 / 0 | No local rows | - | - |

## Specialist recommendation

Retain the current YAML for this worker. The criterion is already scoreable for measured `nearest_flammable_storage_km` and completed-search NULL evidence, and the documented recompute found no rows in the low-end bands that would be affected by the unreachable 0-band. Reordering or rewriting the 0-band would still be a scoring-policy change because `has_mitigation` is not a measured local field.

Stage 3 characterization should decide whether pipeline proximity is supporting evidence only or a scored external-fire metric, and whether any future external-fire avoidance code should remain covered by HI-02/A7 or receive a distinct HI-04 code.

## Final state

No YAML change is implemented. HI-04 remains scoreable under the current screening runtime, with sentinel-aware favourable scoring for completed searches and missing concrete storage distance. The inactive `nearest_pipeline_km` field and unreachable mitigation-dependent 0-band are documented limitations pending Stage 3 or schema/scoring cleanup.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `criteria/avoidance/HI-04_external_fires_avoidance_phase.md`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`, `src/atoms_vs_ashes/scoring/_codes.py`, `src/atoms_vs_ashes/db/models.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, avoidance note, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
