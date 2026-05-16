<!-- man_hours: 0.5 -->
RI-06 - Population projections (60-yr design life) - Ranking audit (CURRENT STATE ACCEPTED)

Phase: **[ranking]**. Primary metric: `pop_growth_rate_pct`. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **1.8 %**.

Status: **current state accepted.** No blocking scoring issue was found for the active ranking behavior. RI-06 is a ranking-only demographic-change proxy over the reference design life.

1. Decision matrix

| Element | Current state | Audit finding |
| --- | --- | --- |
| Phase and action | `phases: [ranking]`; no fail conditions. | Ranking-only, with no exclusionary, avoidance, or review flag. |
| Primary metric | `site_radiological.pop_growth_rate_pct`. | Field exists and is populated for all 361 local merged sites. |
| Supporting metric | `site_radiological.projected_pop_25km_60yr`. | Field exists and is populated for all 361 local merged sites. |
| Score direction | Lower population growth is better; decline receives the highest band. | Monotonic and aligned with the report rationale for demographic drift over the design life. |
| Threshold metadata | No RI-06 entry in `threshold_metadata.yaml`. | Expected: no user-controllable fail threshold or soft flag. |

2. Score-curve boundary table

| Score | `pop_growth_rate_pct` condition | Descriptor | Merged DB count (361 sites) |
| ---: | --- | --- | ---: |
| 9-10 | `< -0.5` | Declining (< -0.5 %/yr). | 92 |
| 7-8 | `< 0` | -0.5 % to 0 %. | 116 |
| 5-6 | `<= 0.3` | 0 % to +0.3 %. | 38 |
| 3-4 | `<= 1.0` | +0.3 % to +1.0 %. | 67 |
| 1-2 | `> 1.0` | > +1.0 %. | 48 |

3. Metric truth and data quality

RI-06 uses GHSL population-derived projection fields persisted in `site_radiological`: annualised `pop_growth_rate_pct` and `projected_pop_25km_60yr`. The local merged DB has both fields populated for **361/361** sites, with no raw misses. Quality resolved as `ghsl_pop_100m_r2023a` in the local scoring pass.

This criterion captures future population burden for ranking only. It does not duplicate RI-04's current EPZ density score or RI-05's population-centre distance avoidance; it changes the composite based on projected demographic pressure.

4. Scored examples from the merged DB

| Band | Site | Country | `pop_growth_rate_pct` | `projected_pop_25km_60yr` | Score | Verdict |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 9-10 | St Andrae power station | AT | -0.687 | 109,431 | 9.5 | pass |
| 9-10 | Gacko Thermal Power Plant | BA | -1.650 | 6,368 | 9.5 | pass |
| 7-8 | Porto Romano Power Station | AL | -0.118 | 170,081 | 7.5 | pass |
| 7-8 | Timelkam power station | AT | -0.174 | 257,843 | 7.5 | pass |
| 5-6 | Duernrohr power station | AT | 0.233 | 264,777 | 5.5 | pass |
| 5-6 | Enns Power Station | AT | 0.269 | 617,485 | 5.5 | pass |
| 3-4 | Mellach power station | AT | 0.430 | 583,716 | 3.5 | pass |
| 3-4 | Voitsberg power station | AT | 0.503 | 471,844 | 3.5 | pass |
| 1-2 | Malesice power station | CZ | 1.059 | 1,734,076 | 1.5 | pass |
| 1-2 | Ağan power station | TR | 1.276 | 105,962 | 1.5 | pass |

5. Composite and soft-flag relationship

RI-06 contributes its 1.8 % normalised weight to the ranking composite. It has no A-code, E-code, review flag, or pass-mark floor. Low RI-06 scores reduce ranking only; they do not remove a site or create a caution verdict.

6. Source citations

- `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml` - RI-06 phases, primary metric, bands, and weight.
- `report/version 1.01/sites_evaluation/05_criteria_radiological.md` - RI-06 rationale and growth-rate bands.
- `src/atoms_vs_ashes/db/models.py` - `SiteRadiological` population-projection fields.
- `tests/test_connector_ghsl_pop.py` and `tests/test_connector_eurostat_projections.py` - local connector/test coverage references for RI-06 data sources.
- Read-only local scoring pass, 2026-05-16 - 361 merged sites, no live API calls.

7. Validation

Validation performed: static spec/rubric comparison, ORM field check, and read-only local scoring over 361 merged sites using `compile_bundle`, `build_context_for_site`, and `evaluate_criterion_value`.
