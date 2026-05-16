<!-- man_hours: 0.7 -->
RI-01 - Atmospheric dispersion (wind, stability, BLH) - Ranking audit (FINAL RECOMMENDATION)

Phase: **[ranking]**. Primary metric: composite of atmospheric sub-scores. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **2.1 %**.

Status: **FINAL RECOMMENDATION - evidence-limited at screening stage.** The declared RI-01 bands remain the intended atmospheric-dispersion score shape, but the active DB/context path does not populate the metric names used by the spec. No YAML-only change is implemented because any scoreable fix requires a connector, schema, or derived-context update.

1. Decision matrix

| Element | Current evidence | Audit finding | Decision state |
| --- | --- | --- | --- |
| Phase and weight | YAML declares `phases: [ranking]`, weight factor 6, normalised weight 2.1 %. | Ranking-only; no exclusionary condition or soft flag. | Accepted. |
| Aggregation | `weighted_mean_of_sub_scores`, rounded to 0.1, using wind-rose 40 %, stable-atmosphere 35 %, mixing-height 25 %. | The aggregation recipe matches `report/version 1.01/sites_evaluation/05_criteria_radiological.md`. | Accepted as the intended scoring shape. |
| Declared metric anchors | Spec/rubric list `site_radiological.wind_rose_json`, `pg_class_f_fraction`, `pg_class_e_fraction`, and `mean_mixing_height_m`. | These anchors are absent from `SiteRadiological` in the current ORM. | Blocking metric-source issue. |
| Actual local fields | `SiteRadiological` has `prevailing_wind_dir`, `avg_wind_speed_ms`, and `mixing_height_m`; the ERA5 batch writes `mixing_height_m`, not `mean_mixing_height_m`. | Some RI-01 evidence exists locally, but not under the names the bands evaluate. | Route mapping/derivation to Stage 3 or connector/schema follow-up. |
| Runtime result | Read-only local scoring over 361 sites gives **361/361** `partial_unscored` results at score **5.0**. | Current RI-01 contributes neutral default scores, not atmospheric dispersion evidence. | Final documented state is evidence-limited, not score-accepted. |

2. Declared score-curve boundary table

| Sub-score | Weight | Score | Condition | Descriptor |
| --- | ---: | ---: | --- | --- |
| `wind_rose_favourability` | 0.40 | 9-10 | `wind_city_offset_deg >= 135` | Offset >= 135 deg. |
| `wind_rose_favourability` | 0.40 | 7-8 | `wind_city_offset_deg >= 90` | 90-135 deg. |
| `wind_rose_favourability` | 0.40 | 5-6 | `wind_city_offset_deg >= 45` | 45-90 deg. |
| `wind_rose_favourability` | 0.40 | 3-4 | `wind_city_offset_deg >= 22` | 22-45 deg. |
| `wind_rose_favourability` | 0.40 | 1-2 | `wind_city_offset_deg < 22` | < 22 deg. |
| `stable_atmosphere_pct` | 0.35 | 9-10 | `pg_fe_fraction < 10` | < 10 % F+E hours. |
| `stable_atmosphere_pct` | 0.35 | 7-8 | `pg_fe_fraction < 20` | 10-20 %. |
| `stable_atmosphere_pct` | 0.35 | 5-6 | `pg_fe_fraction < 30` | 20-30 %. |
| `stable_atmosphere_pct` | 0.35 | 3-4 | `pg_fe_fraction < 40` | 30-40 %. |
| `stable_atmosphere_pct` | 0.35 | 1-2 | `pg_fe_fraction >= 40` | > 40 %. |
| `mean_mixing_height` | 0.25 | 9-10 | `mean_mixing_height_m > 800` | > 800 m. |
| `mean_mixing_height` | 0.25 | 7-8 | `mean_mixing_height_m >= 600` | 600-800 m. |
| `mean_mixing_height` | 0.25 | 5-6 | `mean_mixing_height_m >= 400` | 400-600 m. |
| `mean_mixing_height` | 0.25 | 3-4 | `mean_mixing_height_m >= 200` | 200-400 m. |
| `mean_mixing_height` | 0.25 | 1-2 | `mean_mixing_height_m < 200` | < 200 m. |

Current merged DB score distribution: 361 sites in apparent band **5-6**, all with `partial_unscored`; no populated evidence reaches the sub-score expressions. The apparent band is therefore a neutral default, not a real RI-01 score curve.

3. Metric truth and data quality

Local ERA5 persistence writes `prevailing_wind_dir`, `avg_wind_speed_ms`, `mixing_height_m`, and `ri01_quality`. It also stores richer wind-rose and stability detail in `SiteObservation` payloads, not in scalar ORM fields named by the RI-01 spec. `merge_context_derivations.py` can derive `pg_fe_fraction` only when `pg_class_f_fraction` or `pg_class_e_fraction` are present; they are not present in the active scalar DB path.

Local field coverage from the merged DB: `prevailing_wind_dir` **361/361**, `avg_wind_speed_ms` **361/361**, `mixing_height_m` **361/361** (min 297.70 m, max 681.34 m), but declared anchors `wind_rose_json`, `pg_class_f_fraction`, `pg_class_e_fraction`, and `mean_mixing_height_m` all miss **361/361** rows.

4. Runtime examples

| Site | Country | Available RI-01 evidence | Declared anchor misses | Current score |
| --- | --- | --- | --- | ---: |
| Porto Romano Power Station | AL | `prevailing_wind_dir=NW`, `avg_wind_speed_ms=1.33`, `mixing_height_m=353.22` | `wind_rose_json`, `pg_class_f_fraction`, `pg_class_e_fraction`, `mean_mixing_height_m` | 5.0 `partial_unscored` |
| Duernrohr power station | AT | `prevailing_wind_dir=W`, `avg_wind_speed_ms=1.35`, `mixing_height_m=548.59` | same four declared anchors | 5.0 `partial_unscored` |

5. Specialist recommendation

Adopt the evidence-limited option for the current screening release. The local scalar values `prevailing_wind_dir`, `avg_wind_speed_ms`, and `mixing_height_m` are useful characterization inputs, with observed `mixing_height_m` coverage of **361/361** sites and a local range of **297.70 m** to **681.34 m**, but they do not measure the intended `wind_city_offset_deg` or `pg_fe_fraction` quantities. Re-scoping the YAML around the available scalars would create a different criterion without a documented IAEA/EPRI screening basis for the replacement curve.

RI-01 should therefore remain documented as unmeasured at this stage for structured scoring. Stage 3 characterization, or a deferred connector/schema improvement before the next structured scoring baseline, should derive and persist `wind_city_offset_deg`, `pg_fe_fraction`, and a correctly named mixing-height scalar before RI-01 is treated as an atmospheric dispersion ranking signal.

6. Final state

| Element | Final state |
| --- | --- |
| Documentation decision | Resolved from pending-decision audit to evidence-limited final recommendation. |
| YAML implementation | No change to `config/scoring_specs/ri_radiological.yaml` or `config/scoring_rubrics/ri_radiological.yaml`; the current YAML is not safely repairable without schema or derived-context work. |
| Screening interpretation | The neutral **5.0** / `partial_unscored` runtime output is a placeholder caused by missing structured metrics, not evidence of favourable atmospheric dispersion. |
| Stage 3 / deferred work | Derive or persist `wind_city_offset_deg`, `pg_fe_fraction`, and `mean_mixing_height_m` or update the score recipe after documented metric design and validation. |
| Report wording | Describe RI-01 as unmeasured at this stage when the structured bundle lacks those fields, and route the pathway to atmospheric characterization rather than assigning a site-level suitability conclusion. |

7. Source citations

- `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml` - RI-01 phases, weights, sub-scores, aggregation, and DB anchors.
- `report/version 1.01/sites_evaluation/05_criteria_radiological.md` - RI-01 rationale and sub-score weights.
- `src/atoms_vs_ashes/db/models.py` - actual `SiteRadiological` RI-01 scalar fields.
- `src/atoms_vs_ashes/connectors/copernicus_era5/batch.py` - local ERA5 persistence path.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` - `pg_fe_fraction` derivation rule.
- Read-only local scoring pass, 2026-05-16 - 361 merged sites, no live API calls.

8. Validation

Validation performed before this final recommendation: static YAML/spec comparison, ORM/source search, and a read-only local scoring pass over 361 merged sites using `compile_bundle`, `build_context_for_site`, and `evaluate_criterion_value`.
