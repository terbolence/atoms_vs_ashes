<!-- man_hours: 1.0 -->
# NH-13 - Forest / wildfire

Status: final

Phase: `ranking`

Primary metric: `combustible_veg_pct`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 3, normalised weight 1.1%).

## Specialist Recommendation
Do not change NH-13 YAML in this worker. Local evidence confirms the rubric metric `combustible_veg_pct` is not populated, and the available wildfire bundle field is also NULL in current examples; existing follow-up material identifies the wildfire connector/data pipeline as non-functional.

## Final State
NH-13 remains unscored at this screening stage and is routed to deferred connector/schema work plus Stage 3 wildfire characterization where relevant. No combustible-vegetation value is invented and no alias is added without populated local evidence.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`; `participates_in_composite` is `true`. | Finalized as unresolved for measured ranking behavior. |
| Score logic | Local compiled evidence gives matched-band counts `{'unscored': 361}`. | Do not add an alias or score curve change without populated combustible-vegetation evidence. |
| Data quality | Raw misses: `site_natural_hazards.combustible_veg_pct`=361; current bundle examples also show `wildfire_combustible_pct` as NULL. | Route to deferred wildfire connector/schema work and Stage 3 characterization. |
| Filter relationship | Ranking-only wildfire criterion. It has no fail conditions; current field coverage leaves it neutral/unscored. | Preserve current YAML. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `combustible_veg_pct < 5` | < 5% forest/grassland; no fire scars. | 0 |
| 7-8 | `combustible_veg_pct < 15` | 5-15%; < 1 large fire/decade. | 0 |
| 5-6 | `combustible_veg_pct < 35` | 15-35%; 1-3 fires/decade. | 0 |
| 3-4 | `combustible_veg_pct <= 60` | 35-60%; 3-6 fires/decade. | 0 |
| 1-2 | `combustible_veg_pct > 60` | > 60%; > 6 fires/decade. | 0 |
| unscored | no compiled band matched | pass-mark default, not evidence of a favourable band | 361 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only NH-only compiled-spec evaluation using local scoring helpers. No API, enrichment, web, or remote calls were made.
- `combustible_veg_pct`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.combustible_veg_pct`=361.

## Fail, Avoidance, And Review Conditions
No fail, avoidance, screen, or review conditions are defined.

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| unscored | `e6ecead0` Porto Romano Power Station | AL | 5 | `combustible_veg_pct`=NULL | unscored |
| unscored | `c8f15aca` Nikola Tesla power station | RS | 5 | `combustible_veg_pct`=NULL | unscored |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-13 — Forest and wildfire.md`.
- Validation: local NH-only scoring validation confirms `{"unscored": 361}`; no YAML behavior changed for this criterion.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
