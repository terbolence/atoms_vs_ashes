<!-- man_hours: 0.3 -->
# EP-01 - Emergency-plan feasibility (composite) - ranking state

Status: **ACCEPTED CURRENT STATE** for ranking documentation. The exclusionary decision is already closed in `criteria/exclusionary/EP-01 — Emergency-plan feasibility (composite).md`.

Phase: `[exclusionary, ranking]`  
Primary metric: `ep01_composite_score`  
Source spec/rubric: `config/scoring_specs/ep_emergency_planning.yaml`; `config/scoring_rubrics/ep_emergency_planning.yaml`  
Composite participation: **false**. `EP-01` is ranking-phase, but `action: exclude` on `E8` makes `Criterion.participates_in_composite` false by design.

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted. Bands match the compiled `score_percent_higher_is_better` recipe. |
| Exclusion relationship | `E8` excludes when `ep01_composite_score < 30`; `pass_mark: 5.0` also enables the safety-floor path. |
| Threshold metadata | `EP-01/E8` uses `ep01_composite_score < 30`, default 30 points, bounds 10-60. |
| Current DB coverage | 361/361 local merged rows have `ep01_composite_score`. |

## Current Score Bands

Local validation used `POSTGRES_DB=atoms_vs_ashes_merged`, `config/scoring_specs`, and the normal resolver/evaluator path.

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `ep01_composite_score >= 82.5` | 0 |
| 7-8 | `ep01_composite_score >= 65` | 107 |
| 5-6 | `ep01_composite_score >= 30` | 249 |
| 3-4 | `ep01_composite_score >= 22.5` | 4 |
| 1-2 | `ep01_composite_score >= 15` | 1 |
| 0 | `ep01_composite_score < 15` | 0 |

## Metric Truth And Data Quality

`ep01_composite_score` is stored on `site_emergency_planning`. The emergency-plan analysis also stores sub-scores (`ep01_road_score`, `ep01_special_pop_score`, `ep01_geography_score`, `ep01_population_score`, `ep01_terrain_score`), but the ranking criterion consumes only the composite scalar. There are no local NULL composites in the merged DB.

The criterion's quality floor is one band for low-quality uncertainty. In the current local merged DB, the examples observed during this pass used high-quality EP-01 rows.

## Scored Examples

| Band | Site | Country | Metric | Score | Screening relationship |
| --- | --- | --- | ---: | ---: | --- |
| 7-8 | Duernrohr power station | AT | 72.0 | 7.5 | E8 pass |
| 5-6 | Porto Romano Power Station | AL | 56.0 | 5.5 | E8 pass |
| 3-4 | Bydgoszcz power station | PL | 24.3 | 3.5 | E8 fail |
| 1-2 | Kosice power station | SK | 18.5 | 1.5 | E8 fail |
| 9-10 / 0 | No local rows | - | - | - | Empty bands in this recompute |

## Sources And Validation

Sources: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `config/scoring_specs/threshold_metadata.yaml`, `criteria/exclusionary/EP-01 — Emergency-plan feasibility (composite).md`, `src/atoms_vs_ashes/scoring/rubric.py`, `src/atoms_vs_ashes/criterion_spec/compiler.py`.

Validation: local-only spec compile and merged-DB band recompute. No live API, enrichment, web, code, tests, or YAML changes.
