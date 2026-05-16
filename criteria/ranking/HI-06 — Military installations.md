<!-- man_hours: 0.35 -->
# HI-06 - Military installations - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. Current compiled spec behavior is retained as the documented screening runtime state, while the class-aware rubric/data-model mismatch and A5/A6 field mismatch are routed to deferred scoring-spec synchronization with impact review.

Phase: `[avoidance, ranking]`  
Primary metric: `nearest_military_km` on the active spec path  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: `A5` and `A6` emit `avoidance_penalty` conditions, but the active spec still references missing `military_type`.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Active spec ranking bands | Accepted as current runtime documentation. They are compiled from `band_recipe: higher_is_better` using A5 pivot 30 km: `>=150`, `>=60`, `>=30`, `>=15`, `>=6`, `<6`. |
| Active A-code fields | A5/A6 use `military_type`, which is not a local ORM column or alias. |
| Legacy/default rubric | Contains class-aware SP-F bands using `nearest_military_class` and `nearest_high_consequence_military_*`. |
| Runtime evidence | Local resolver recompute: 174 rows in 0, 90 in 1-2, 62 in 3-4, 35 unscored; no rows reach 5-6 or better under active spec. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `nearest_military_km >= 150.0` | 0 |
| 7-8 | `nearest_military_km >= 60.0` | 0 |
| 5-6 | `nearest_military_km >= 30.0` | 0 |
| 3-4 | `nearest_military_km >= 15.0` | 62 |
| 1-2 | `nearest_military_km >= 6.0` | 90 |
| 0 | `nearest_military_km < 6.0` | 174 |
| Unscored | No `nearest_military_km` | 35 |

## Metric Truth And Data Quality

`site_human_hazards` stores `nearest_military_km`, `nearest_military_class`, `nearest_high_consequence_military_km`, `nearest_high_consequence_military_class`, `military_count`, `hi06_quality`, and `hi06_comment`. It does not store `military_type`.

The active compiled path is distance-only and can penalize low-consequence `other` military features. The class-aware rubric path distinguishes `airfield`, `depot`, `training_area`, and `other`, but it is not the active spec/profile runtime while `config/scoring_specs` retains the recipe and `military_type` A-code expressions.

## Scored Examples

| Band | Site | Country | Active spec evidence | Score |
| --- | --- | --- | --- | ---: |
| 0 | Porto Romano Power Station | AL | `nearest_military_km = 2.16`; `military_type = null` | 0.0 |
| 1-2 | Duernrohr power station | AT | `nearest_military_km = 7.93`; `military_type = null` | 1.5 |
| 3-4 | Riedersbach power station | AT | `nearest_military_km = 19.00`; `military_type = null` | 3.5 |
| Unscored | Gacko Thermal Power Plant | BA | no military feature distance | 5.0 |
| 5-6 / 7-8 / 9-10 | No local rows | - | Empty bands | - |

## Specialist recommendation

Do not change YAML in this worker. The strongest technical direction is to resynchronize `config/scoring_specs` with the class-aware rubric and populated fields (`nearest_military_class`, `nearest_high_consequence_military_km`, and `nearest_high_consequence_military_class`), but that would materially change scoring for a large share of rows. It also requires deliberate treatment of A5/A6 avoidance expressions currently tied to missing `military_type`.

Stage 3 characterization should classify nearby installations by function and consequence class, then confirm whether A5/A6 should use training-area and depot semantics directly. A deferred scoring implementation should include a local impact dry run before replacing the active distance-only recipe.

## Final state

No YAML change is implemented. HI-06 remains scoreable under the current compiled distance-only screening runtime, with 174 rows in 0, 90 in 1-2, 62 in 3-4, and 35 unscored in the documented recompute. The class-aware rubric remains the recommended next implementation target, but it is a parent/user scoring-policy action rather than a low-risk documentation-worker edit.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `config/scoring_specs/threshold_metadata.yaml`, `criteria/avoidance/HI-06_A5-A6_military_installations.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/analysis/military_proximity.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, threshold metadata, avoidance audit, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
