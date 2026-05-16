<!-- man_hours: 0.35 -->
# HI-02 - Industrial explosions (Seveso / IED) - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. The current compiled ranking bands are retained as the documented screening runtime state. Completed-search NULL sentinel support is routed to a deferred compiler/recipe or YAML-policy change because the active spec path currently rebuilds bands from `band_recipe`.

Phase: `[avoidance, ranking]`  
Primary metric: `nearest_seveso_km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: `A7` emits `avoidance_penalty` when `nearest_seveso_km < 5`.

## Decision Matrix

| Element | Current state |
| --- | --- |
| A7 hard threshold | Internally consistent at `< 5 km`; threshold metadata default is 5 km with bounds 2-15 km. |
| Runtime ranking bands | Accepted as current runtime documentation. They are compiled from `band_recipe: higher_is_better`, not from the hand-written sentinel bands. |
| Hand-written sentinel | `(nearest_seveso_km is null and hi02_search_completed == true)` exists in spec/rubric text but is ignored on the compiled spec path. |
| Current DB evidence | Local resolver recompute: 7 rows in 9-10, 4 in 7-8, 4 in 5-6, 346 unscored. Existing avoidance audit identified 299 completed-search NULL rows currently treated as unscored/inconclusive. |

## Current Runtime Bands

These are the compiled spec-path bands.

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `nearest_seveso_km >= 25.0` | 7 |
| 7-8 | `nearest_seveso_km >= 10.0` | 4 |
| 5-6 | `nearest_seveso_km >= 5.0` | 4 |
| 3-4 | `nearest_seveso_km >= 2.5` | 0 |
| 1-2 | `nearest_seveso_km >= 1.0` | 0 |
| 0 | `nearest_seveso_km < 1.0` | 0 |
| Unscored | No concrete distance / no compiled sentinel band | 346 |

## Metric Truth And Data Quality

`nearest_seveso_km`, `nearest_industrial_km`, `hi02_quality`, and `hi02_comment` are stored on `site_human_hazards`. `hi02_search_completed` is derived from `hi02_quality`, but the active compiled bands do not consume it because the recipe rebuilds the ladder from the A7 pivot.

`nearest_ied_km` is listed in `db_fields.api` but no local ORM column or alias was found in the existing avoidance audit. It is not used by A7 or the current compiled bands, but it creates misleading raw-miss evidence.

## Scored Examples

| Band | Site | Country | `nearest_seveso_km` | Score | A7 relationship |
| --- | --- | --- | ---: | ---: | --- |
| 9-10 | Bedzin power station | PL | 25.66 | 9.5 | no A7 caution |
| 7-8 | Jaworzno power station | PL | 14.85 | 7.5 | no A7 caution |
| 5-6 | Ruse Iztok power station | BG | 5.24 | 5.5 | no A7 caution, just outside 5 km |
| Unscored | Duernrohr power station | AT | null | 5.0 | current compiled A7 inconclusive despite completed-search evidence in prior audit |
| 3-4 / 1-2 / 0 | No local concrete-distance rows | - | - | - | Empty bands |

## Specialist recommendation

Retain the current YAML for this worker and document the compiled recipe behavior as the active screening runtime. The preferred technical direction is to preserve threshold tuning while adding explicit compiler/recipe support for completed-search NULL evidence, but that is not a YAML-only change. Removing `band_recipe` would materially change ranking behavior for the 299 completed-search NULL rows noted in the avoidance audit and should be handled with targeted tests and impact review.

Stage 3 characterization should confirm whether completed-search no-facility evidence should score in the favourable band, and the deferred implementation should either extend the recipe compiler to support that sentinel or remove the recipe with a documented scoring-impact dry run.

## Final state

No YAML change is implemented. HI-02 remains scoreable only for concrete `nearest_seveso_km` values under the compiled recipe path; completed-search NULL rows remain neutral unscored evidence gaps in the current screening runtime. The `nearest_ied_km` field remains a deferred schema/alias cleanup item because it is referenced in `db_fields.api` but not locally available.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `config/scoring_specs/threshold_metadata.yaml`, `criteria/avoidance/HI-02_A7_industrial_explosions.md`, `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, threshold metadata, avoidance audit, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
