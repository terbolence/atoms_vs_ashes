<!-- man_hours: 0.6 -->
RI-04 - Population density (EPZ rings) - Ranking audit (CURRENT STATE ACCEPTED)

Phase: **[ranking]**. Primary metric: minimum of four EPZ-ring population-density sub-scores. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **2.8 %**.

Status: **current state accepted.** The current YAML intentionally keeps RI-04 ranking-only. Population-centre distance avoidance (A12) is anchored on RI-05, not RI-04.

1. Decision matrix

| Element | Current state | Audit finding |
| --- | --- | --- |
| Phase and action | `phases: [ranking]`; no fail conditions. | Ranking-only; no A-code, E-code, or review flag. |
| Aggregation | `min_of_sub_scores` across 5 km, 16 km, 25 km, and 80 km rings. | The densest controlling ring sets the criterion score, matching the report note. |
| Primary metric truth | `site_radiological.pop_density_5km`, `pop_density_16km`, `pop_density_25km`, `pop_density_80km`. | All four fields are populated for all 361 local merged sites. |
| A12 relationship | Spec notes state RI-04 density is not an exclusionary or avoidance gate; A12 lives on RI-05. | Locked by local tests that assert RI-04 has no fail conditions and no A12. |
| Threshold metadata | No RI-04 entry in `threshold_metadata.yaml`. | Expected: no user-controllable fail threshold. |

2. Score-curve boundary table

| Score | 5 km density | 16 km density | 25 km density | 80 km density | Merged DB count (361 sites) |
| ---: | --- | --- | --- | --- | ---: |
| 9-10 | `< 25` | `< 50` | `< 50` | `< 25` | 2 |
| 7-8 | `< 100` | `< 150` | `< 150` | `< 75` | 47 |
| 5-6 | `< 250` | `< 300` | `< 300` | `< 150` | 89 |
| 3-4 | `< 500` | `< 600` | `< 600` | `< 300` | 91 |
| 1-2 | `>= 500` | `>= 600` | `>= 600` | `>= 300` | 132 |

Counts are based on the final `min_of_sub_scores` result: a site lands in the lowest band triggered by any of the four rings.

3. Metric truth and data quality

RI-04 uses GHSL 100 m population-derived densities persisted in `site_radiological`. The local merged DB has all four density fields populated for **361/361** sites, with no raw misses. Quality resolved as `ghsl_pop_100m_r2023a` in the local scoring pass.

The metric is a screening-grade demographic burden proxy, not an emergency-planning feasibility decision. Low RI-04 scores reduce the ranking composite; they do not create a caution or failure verdict.

4. Scored examples from the merged DB

| Band | Site | Country | 5 km | 16 km | 25 km | 80 km | Score | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 9-10 | METES power station | TR | 10.66 | 12.69 | 33.53 | 17.28 | 9.5 | pass |
| 9-10 | Sinop Akfen power station | TR | 21.32 | 16.66 | 24.70 | 14.84 | 9.5 | pass |
| 7-8 | Zeltweg power station | AT | 8.35 | 54.71 | 96.56 | 72.12 | 7.5 | pass |
| 7-8 | Gacko Thermal Power Plant | BA | 47.69 | 9.61 | 5.91 | 43.38 | 7.5 | pass |
| 5-6 | Mellach power station | AT | 165.18 | 248.21 | 284.52 | 103.29 | 5.5 | pass |
| 5-6 | Riedersbach power station | AT | 145.57 | 110.82 | 153.35 | 134.57 | 5.5 | pass |
| 3-4 | Porto Romano Power Station | AL | 399.01 | 280.01 | 153.07 | 105.37 | 3.5 | pass |
| 3-4 | Duernrohr power station | AT | 109.82 | 106.42 | 129.06 | 184.62 | 3.5 | pass |
| 1-2 | Glinica power station | BA | 842.49 | 142.24 | 84.67 | 49.34 | 1.5 | pass |
| 1-2 | Tuzla Thermal Power Plant | BA | 505.97 | 280.36 | 158.73 | 100.56 | 1.5 | pass |

5. Composite and soft-flag relationship

RI-04 contributes its 2.8 % normalised weight to the ranking composite. It has no soft-flag relationship of its own. The related population-centre avoidance code A12 is documented and implemented under RI-05; any RI-05/A12 defect should be resolved there without reintroducing RI-04 as an avoidance criterion.

6. Source citations

- `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml` - RI-04 phases, sub-score bands, aggregation, notes, and weight.
- `report/version 1.01/sites_evaluation/05_criteria_radiological.md` - RI-04 rationale and ring table.
- `src/atoms_vs_ashes/db/models.py` - `SiteRadiological` population-density fields.
- `tests/scoring/test_ri04_no_exclusion.py` and `tests/scoring/test_suitable_sites_audit.py` - RI-04 ranking-only and A12-on-RI-05 assertions.
- Read-only local scoring pass, 2026-05-16 - 361 merged sites, no live API calls.

7. Validation

Validation performed: static spec/rubric comparison, ORM field check, targeted test review for RI-04 no-exclusion behavior, and read-only local scoring over 361 merged sites using `compile_bundle`, `build_context_for_site`, and `evaluate_criterion_value`.
