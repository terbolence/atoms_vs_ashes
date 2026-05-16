<!-- man_hours: 0.5 -->
RI-02 - Surface water dispersion - Ranking audit (CURRENT STATE ACCEPTED)

Phase: **[ranking]**. Primary metric: `cooling_flow_m3s`. Source spec/rubric: `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml`. Composite participation: **yes**, `participates_in_composite: true`, normalised weight **1.8 %**.

Status: **current state accepted.** No blocking scoring issue was found for the active ranking behavior. RI-02 is a ranking-only dilution proxy that cross-links to the structured cooling-flow field in `site_infrastructure_v2`.

1. Decision matrix

| Element | Current state | Audit finding |
| --- | --- | --- |
| Phase and action | `phases: [ranking]`; no fail conditions. | Ranking-only, no exclusionary or avoidance behavior. |
| Primary metric | `cooling_flow_m3s` from `site_infrastructure_v2.cooling_flow_m3s`. | Field exists and is populated for all 361 local merged sites. |
| Score direction | Higher river/cooling-flow proxy is better. | Monotonic and aligned with the report rationale for liquid-pathway dilution. |
| Threshold metadata | No RI-02 entry in `threshold_metadata.yaml`. | Expected: no user-controllable fail threshold or soft flag. |
| Data quality | Quality is not a dedicated RI-02 flag on the cross-linked infrastructure field. | Non-blocking caveat; scores are populated, but quality-band widening is not driven by an RI-02 quality flag. |

2. Score-curve boundary table

| Score | `cooling_flow_m3s` condition | Descriptor | Merged DB count (361 sites) |
| ---: | --- | --- | ---: |
| 9-10 | `cooling_flow_m3s > 500` | > 500 m3/s. | 27 |
| 7-8 | `cooling_flow_m3s >= 100` | 100-500 m3/s. | 39 |
| 5-6 | `cooling_flow_m3s >= 30` | 30-100 m3/s. | 35 |
| 3-4 | `cooling_flow_m3s >= 10` | 10-30 m3/s. | 68 |
| 1-2 | `cooling_flow_m3s < 10` | < 10 m3/s. | 192 |

3. Metric truth and data quality

RI-02 uses the same structured cooling-flow metric as the cooling-water assessment: `site_infrastructure_v2.cooling_flow_m3s`. This is a surface-water dilution proxy, not a radionuclide transport model. The active merged DB has `cooling_flow_m3s` populated for **361/361** sites, with no raw metric misses in the local scoring pass.

The criterion has no fail conditions and no RI-specific threshold metadata. Low data quality can widen bands only if the scoring context supplies a low quality flag; in the current cross-linked path, criterion quality resolved as `None` for all 361 local rows.

4. Scored examples from the merged DB

| Band | Site | Country | `cooling_flow_m3s` | Score | Verdict |
| --- | --- | --- | ---: | ---: | --- |
| 9-10 | Duernrohr power station | AT | 1917.98 | 9.5 | pass |
| 9-10 | Enns Power Station | AT | 1563.09 | 9.5 | pass |
| 7-8 | Mellach power station | AT | 118.16 | 7.5 | pass |
| 7-8 | Riedersbach power station | AT | 156.18 | 7.5 | pass |
| 5-6 | Zeltweg power station | AT | 70.92 | 5.5 | pass |
| 5-6 | Kakanj Thermal Power Plant | BA | 50.72 | 5.5 | pass |
| 3-4 | Porto Romano Power Station | AL | 18.02 | 3.5 | pass |
| 3-4 | St Andrae power station | AT | 10.56 | 3.5 | pass |
| 1-2 | Timelkam power station | AT | 6.45 | 1.5 | pass |
| 1-2 | Voitsberg power station | AT | 7.51 | 1.5 | pass |

5. Composite and soft-flag relationship

RI-02 contributes its 1.8 % normalised weight to the ranking composite. It has no A-code, E-code, review flag, or pass-mark floor. Low RI-02 scores reduce ranking only; they do not remove a site or create a caution verdict.

6. Source citations

- `config/scoring_specs/ri_radiological.yaml` and `config/scoring_rubrics/ri_radiological.yaml` - RI-02 phases, primary metric, bands, and weight.
- `report/version 1.01/sites_evaluation/05_criteria_radiological.md` - RI-02 rationale and score bands.
- `src/atoms_vs_ashes/db/models.py` - `site_infrastructure_v2.cooling_flow_m3s` field.
- Read-only local scoring pass, 2026-05-16 - 361 merged sites, no live API calls.

7. Validation

Validation performed: static spec/rubric comparison, ORM field check, and read-only local scoring over 361 merged sites using `compile_bundle`, `build_context_for_site`, and `evaluate_criterion_value`.
