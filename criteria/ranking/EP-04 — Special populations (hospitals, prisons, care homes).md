<!-- man_hours: 0.25 -->
# EP-04 - Special populations (hospitals, prisons, care homes) - ranking state

Status: **ACCEPTED CURRENT STATE** for ranking documentation. No blocking scoring issue was identified in this pass.

Phase: `[ranking]`  
Primary metric: `special_pop_count`  
Source spec/rubric: `config/scoring_specs/ep_emergency_planning.yaml`; `config/scoring_rubrics/ep_emergency_planning.yaml`  
Composite participation: **true**

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted. Lower special-population burden scores better. |
| Derived metric | `special_pop_count` is derived from `hospital_count_epz`, `prison_count_epz`, and `care_home_count_epz`. |
| Current DB coverage | 361/361 local merged rows have the three count fields needed for derivation. |
| Cross-phase relationship | None. EP-04 has no exclusion, avoidance, or review flag. |

## Current Score Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `special_pop_count <= 2` | 24 |
| 7-8 | `special_pop_count <= 8` | 81 |
| 5-6 | `special_pop_count <= 25` | 118 |
| 3-4 | `special_pop_count <= 60` | 68 |
| 1-2 | `special_pop_count > 60` | 70 |
| Unscored | No band matched | 0 |

## Metric Truth And Data Quality

`hospital_count_epz`, `prison_count_epz`, `care_home_count_epz`, `ep04_quality`, and `ep04_comment` are stored on `site_emergency_planning`. `special_pop_count` is derived in `merge_context_derivations.py` by summing the three counts, treating missing individual counts as zero when at least one count is present.

The criterion has the standard one-band quality floor for low-quality uncertainty. Current local recompute examples used medium-quality EP-04 rows.

## Scored Examples

| Band | Site | Country | `special_pop_count` | Score |
| --- | --- | --- | ---: | ---: |
| 9-10 | St Andrae power station | AT | 2 | 9.5 |
| 7-8 | Bugojno Thermal Power Project | BA | 5 | 7.5 |
| 5-6 | Porto Romano Power Station | AL | 25 | 5.5 |
| 3-4 | Mellach power station | AT | 47 | 3.5 |
| 1-2 | Enns Power Station | AT | 71 | 1.5 |

## Sources And Validation

Sources: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `docs/expert_siting_criteria_evaluation_matrix.md`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/scoring/merge_context_derivations.py`.

Validation: local-only spec compile and merged-DB band recompute. No live API, enrichment, web, code, tests, or YAML changes.
