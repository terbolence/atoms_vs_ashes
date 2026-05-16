<!-- man_hours: 0.35 -->
# HI-03 - Toxic and gas releases - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. The current compiled ranking state is retained as the documented screening runtime state. Completed-search NULL semantics, recipe/report band drift, and unavailable source-type evidence are routed to Stage 3 characterization or a later schema/compiler improvement.

Phase: `[avoidance, ranking]`  
Primary metric: `nearest_toxic_source_km`  
Source spec/rubric: `config/scoring_specs/hi_human_induced.yaml`; `config/scoring_rubrics/hi_human_induced.yaml`  
Composite participation: **true**  
Avoidance relationship: `A8` emits `avoidance_penalty` when `nearest_toxic_source_km < 8`.

## Decision Matrix

| Element | Current state |
| --- | --- |
| A8 hard threshold | Internally consistent at `< 8 km`; threshold metadata default is 8 km with bounds 3-25 km. |
| Runtime ranking bands | Accepted as current runtime documentation. They are compiled from `band_recipe: higher_is_better`; hand-written/report bands are shadowed. |
| Top numeric band | `>= 40 km`, beyond the current 30 km EEA industrial search radius; no local row reaches 9-10. |
| NULL behavior | NULLs remain unscored/A8 inconclusive even when connector comments indicate completed search/no source. |
| Source typing | `toxic_source_type` is listed in `db_fields.api` but is not a local ORM column or alias. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `nearest_toxic_source_km >= 40.0` | 0 |
| 7-8 | `nearest_toxic_source_km >= 16.0` | 34 |
| 5-6 | `nearest_toxic_source_km >= 8.0` | 24 |
| 3-4 | `nearest_toxic_source_km >= 4.0` | 13 |
| 1-2 | `nearest_toxic_source_km >= 1.6` | 9 |
| 0 | `nearest_toxic_source_km < 1.6` | 9 |
| Unscored | No concrete distance / no completed-search sentinel | 272 |

## Metric Truth And Data Quality

`nearest_toxic_source_km`, `hi03_quality`, and `hi03_comment` are stored on `site_human_hazards`. No `hi03_search_completed` sentinel is derived today, unlike HI-02, HI-04, HI-05, and HI-08. `toxic_source_type` is not available locally, so the ranking path cannot distinguish cloud-forming external sources from broader industrial/toxic categories.

The active recipe also ignores the hand-written `has_mitigation` 0-band. `has_mitigation` is supplied only as an explicit NULL helper for legacy rubric clauses, not as real mitigation evidence.

## Scored Examples

| Band | Site | Country | `nearest_toxic_source_km` | Score | A8 relationship |
| --- | --- | --- | ---: | ---: | --- |
| 7-8 | Riedersbach power station | AT | 21.88 | 7.5 | no A8 caution |
| 5-6 | Mellach power station | AT | 10.21 | 5.5 | no A8 caution |
| 3-4 | Enns Power Station | AT | 5.36 | 3.5 | A8 caution |
| 1-2 | Borsod power station | HU | 3.00 | 1.5 | A8 caution |
| 0 | Duernrohr power station | AT | 0.69 | 0.0 | A8 caution |
| 9-10 | No local rows | - | - | - | Empty band |

## Specialist recommendation

Retain the current YAML for this worker and document the compiled recipe behavior as the active screening runtime. The available local evidence supports scoring concrete `nearest_toxic_source_km` values, but it does not support assigning source types, completed-search NULL outcomes, or mitigation-based 0-band decisions. The top 9-10 band is empty because the recipe-derived threshold is beyond the documented search radius, which should be reviewed with compiler and data-source context before changing thresholds.

Stage 3 characterization should confirm source type, toxic-cloud relevance, completed-search status, and site-specific consequence screening for nearby sources. A deferred schema/compiler improvement should add `hi03_search_completed` and source-type semantics before any favourable NULL scoring or source-class-specific bands are used.

## Final state

No YAML change is implemented. HI-03 remains scoreable only for concrete `nearest_toxic_source_km` values under the compiled recipe path; NULL rows remain neutral unscored evidence gaps in the current screening runtime. The unavailable `toxic_source_type` and non-evidenced `has_mitigation` clauses are retained as documented limitations, not used to invent scoring values.

## Sources And Validation

Sources: `config/scoring_specs/hi_human_induced.yaml`, `config/scoring_rubrics/hi_human_induced.yaml`, `config/scoring_specs/threshold_metadata.yaml`, `criteria/avoidance/HI-03_A8_toxic_gas_releases.md`, `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`, `src/atoms_vs_ashes/connectors/eea_industrial/batch.py`, `src/atoms_vs_ashes/db/models.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, threshold metadata, avoidance audit, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
