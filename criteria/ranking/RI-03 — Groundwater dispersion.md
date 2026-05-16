<!-- man_hours: 0.7 -->
RI-03 - Groundwater dispersion - Ranking audit (FINAL RECOMMENDATION)

Phase: **[ranking]**. Primary metric: `groundwater_vulnerability_class`. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **1.8 %**.

Status: **FINAL RECOMMENDATION - evidence-limited at screening stage.** The score curve is monotonic in concept, but the active local DB path does not populate the classification names used by the bands. No YAML-only change is implemented because the available scalar evidence does not establish the intended vulnerability class or sensitive-receptor terms.

1. Decision matrix

| Element | Current evidence | Audit finding | Decision state |
| --- | --- | --- | --- |
| Phase and action | `phases: [ranking]`; no exclusionary conditions. | Ranking-only; no soft flag or exclusionary behavior. | Accepted. |
| Primary metric | Spec/rubric use `groundwater_vulnerability_class`. | The ORM has no scalar field with this name. | Blocking metric-source issue. |
| Declared supporting fields | Bands also reference `no_aquifer_in_5km` and `sensitive_wells_10km`. | No local code or derived-context implementation was found for these names. | Route derivation/source design to Stage 3 or connector/schema follow-up. |
| Actual local fields | `SiteRadiological` has `aquifer_type` and `groundwater_flow_dir`; `aquifer_type` is populated for 359/361 sites. | Existing evidence is not sufficient to evaluate the declared vulnerability bands without a mapping. | Route mapping/derivation to Stage 3 or connector/schema follow-up. |
| Runtime result | Read-only local scoring over 361 sites gives **361/361** `unscored` results at score **5.0**. | RI-03 currently contributes neutral default scores. | Final documented state is evidence-limited, not score-accepted. |

2. Declared score-curve boundary table

| Score | Declared condition | Descriptor | Current runtime viability |
| ---: | --- | --- | --- |
| 9-10 | `aquifer_type == 'confined' or no_aquifer_in_5km == true` | Confined aquifer with strong retardation OR no major aquifer in 5 km. | Partially viable only if `aquifer_type` exactly equals `confined`; no `no_aquifer_in_5km` derivation found. |
| 7-8 | `groundwater_vulnerability_class == 'low' and sensitive_wells_10km == 0` | Low-vulnerability unconfined; no proximate sensitive wells. | Inactive under current ORM/source path. |
| 5-6 | `groundwater_vulnerability_class == 'moderate'` | Moderate vulnerability; standard monitoring sufficient. | Inactive under current ORM/source path. |
| 3-4 | `groundwater_vulnerability_class == 'high'` | High vulnerability; sensitive wells within 10 km; dedicated GW programme. | Inactive under current ORM/source path. |
| 1-2 | `aquifer_type == 'karst' or groundwater_vulnerability_class == 'very_high'` | Karst / highly conductive with sensitive downstream uses proximate. | Partially viable only if `aquifer_type` exactly equals `karst`; vulnerability class is absent. |

Current merged DB score distribution: **361** sites in neutral **5.0 unscored** state. This is not an accepted score-curve population.

3. Metric truth and data quality

The local `SiteRadiological` table currently exposes `aquifer_type`, `groundwater_flow_dir`, `ri03_quality`, and `ri03_comment`. The declared `groundwater_vulnerability_class` is absent for **361/361** scoring contexts. `aquifer_type` is present for **359/361** sites, while `groundwater_flow_dir` is not populated in the local merged DB.

`ri03_quality` resolved as `medium` for 359 sites and `low` for 2 sites in the local scoring pass, but those quality flags cannot make the current bands meaningful because the main classification metric is missing.

4. Runtime examples

| Site | Country | Available RI-03 evidence | Declared anchor misses | Current score |
| --- | --- | --- | --- | ---: |
| Porto Romano Power Station | AL | `aquifer_type=low permeability`, `groundwater_flow_dir=NULL`, `ri03_quality=medium` | `groundwater_vulnerability_class` | 5.0 `unscored` |
| Duernrohr power station | AT | `aquifer_type=sedimentary sands`, `groundwater_flow_dir=NULL`, `ri03_quality=medium` | `groundwater_vulnerability_class` | 5.0 `unscored` |

5. Specialist recommendation

Adopt the evidence-limited option for the current screening release. The local `aquifer_type` field is present for **359/361** sites, and `ri03_quality` resolves as `medium` for **359** sites and `low` for **2** sites, but those fields do not measure `groundwater_vulnerability_class`, `no_aquifer_in_5km`, or `sensitive_wells_10km`. Mapping labels such as `low permeability` or `sedimentary sands` directly into vulnerability scores would introduce an undocumented hydrogeological classification at ranking stage.

RI-03 should therefore remain unmeasured at this stage for structured scoring. Stage 3 characterization, or a deferred connector/schema improvement before the next structured scoring baseline, should define the groundwater vulnerability class, sensitive-well count, and no-aquifer condition from traceable hydrogeological evidence before RI-03 is used as a groundwater dispersion ranking signal.

6. Final state

| Element | Final state |
| --- | --- |
| Documentation decision | Resolved from pending-decision audit to evidence-limited final recommendation. |
| YAML implementation | No change to `config/scoring_specs/ri_radiological.yaml` or `config/scoring_rubrics/ri_radiological.yaml`; a scoreable fix requires new derived fields or source evidence. |
| Screening interpretation | The neutral **5.0** / `unscored` runtime output is a placeholder caused by missing structured vulnerability metrics, not groundwater dispersion evidence. |
| Stage 3 / deferred work | Define and persist `groundwater_vulnerability_class`, `no_aquifer_in_5km`, and `sensitive_wells_10km`, or replace the score recipe only after a documented metric-design decision and validation. |
| Report wording | Describe RI-03 as unmeasured at this stage when the structured bundle lacks those fields, and route the pathway to groundwater characterization rather than assigning a site-level suitability conclusion. |

7. Source citations

- `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml` - RI-03 primary metric, bands, and weight.
- `report/version 1.01/sites_evaluation/05_criteria_radiological.md` - RI-03 rationale and intended aquifer/pathway scoring.
- `src/atoms_vs_ashes/db/models.py` - actual `SiteRadiological` RI-03 scalar fields.
- Static source search for `groundwater_vulnerability_class`, `no_aquifer_in_5km`, and `sensitive_wells_10km` - no active Python implementation found.
- Read-only local scoring pass, 2026-05-16 - 361 merged sites, no live API calls.

8. Validation

Validation performed before this final recommendation: static YAML/spec comparison, ORM/source search, and read-only local scoring pass over 361 merged sites using `compile_bundle`, `build_context_for_site`, and `evaluate_criterion_value`.
