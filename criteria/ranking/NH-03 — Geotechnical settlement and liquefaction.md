<!-- man_hours: 1.0 -->
# NH-03 - Geotechnical - settlement and liquefaction

Status: final

Phase: `exclusionary`, `ranking`

Primary metric: `liquefaction_suscept`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **no** (weight factor 7, normalised weight 2.5%).

## Specialist Recommendation
Implement the safe review-only option from the existing exclusionary analysis: keep the current scoring bands and E2 floor unchanged, but add an `R2` review flag when `liquefaction_suscept` is `high` or `very_high` and `has_remedy` is unmeasured. The current database has `has_remedy` NULL for all 361 sites, so a score-changing conservative rewrite would reclassify too much of the screening pool without measured remedy evidence.

## Final State
`R2` now routes high/very-high susceptibility with unmeasured remedy evidence to Stage 3 geotechnical characterization. Scores and hard E2 behavior remain unchanged: explicitly absent remedy evidence still triggers E2, while unknown remedy evidence is surfaced as a review flag instead of being converted into invented remedy status.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `exclusionary`, `ranking`; `participates_in_composite` is `false`. | Finalized with review-only Stage 3 routing for unmeasured remedy evidence. |
| Score logic | Local compiled evidence gives matched-band counts `{'3-4': 1, '5-6': 210, '7-8': 4, '9-10': 137, 'unscored': 9}`. | Keep score bands unchanged; do not convert unknown remedy status into a measured value. |
| Data quality | Raw misses: `site_natural_hazards.bearing_capacity_kpa`=53; `site_natural_hazards.depth_to_bedrock_m`=5; `site_natural_hazards.groundwater_depth_m`=361; `site_natural_hazards.liquefaction_suscept`=9. | Add `R2` review flag for high/very-high susceptibility with `has_remedy is null`. |
| Filter relationship | Dual exclusionary/ranking. `E2` is an `exclude` action with `pass_mark: 5.0`; current high+NULL treatment is the decision issue. | Preserve E2; add R2 review-only routing. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `liquefaction_suscept in ['very_low', 'none']` | Negligible susceptibility (Stage-1 favourable default). | 137 |
| 7-8 | `liquefaction_suscept == 'low'` | Low susceptibility; favourable at screening grade. | 4 |
| 5-6 | `liquefaction_suscept == 'moderate' or (liquefaction_suscept == 'high' and (has_remedy == true or has_remedy is null)) or (liquefaction_suscept == 'very_high' and has_remedy == true)` | Moderate susceptibility, or high/very-high with documented (or pending for `high`) mitigation. | 210 |
| 3-4 | `liquefaction_suscept == 'very_high' and has_remedy is null` | Very-high susceptibility with unknown remedy status (caught by safety floor). | 1 |
| 1-2 | `liquefaction_suscept in ['high', 'very_high'] and has_remedy == false` | High or very-high susceptibility with explicitly no documented mitigation (E2 hard fail). | 0 |
| unscored | no compiled band matched | pass-mark default, not evidence of a favourable band | 9 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `liquefaction_suscept`: present 352/361, NULL 9, top values moderate=149, very_low=137, high=61, low=4, very_high=1.
- `has_remedy`: present 0/361, NULL 361, top values none.
- `bearing_capacity_kpa`: present 308/361, NULL 53, min 53.5, max 133, mean 86.2955.
- `depth_to_bedrock_m`: present 356/361, NULL 5, min 0.19, max 57.08, mean 20.6447.
- `groundwater_depth_m`: present 0/361, NULL 361, top values none.
- `nh03_quality`: present 361/361, NULL 0, top values medium=352, no_data=9.
- Raw misses: `site_natural_hazards.bearing_capacity_kpa`=53; `site_natural_hazards.depth_to_bedrock_m`=5; `site_natural_hazards.groundwater_depth_m`=361; `site_natural_hazards.liquefaction_suscept`=9.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `E2` | `exclude` | `liquefaction_suscept in ['high', 'very_high'] and has_remedy == false` | 0 | 1 |
| `R2` | `review_flag` | `liquefaction_suscept in ['high', 'very_high'] and has_remedy is null` | 62 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `90820fe3` Mellach power station | AT | 9.5 | `liquefaction_suscept`=very_low<br>`has_remedy`=NULL | matched current logic |
| 9-10 | `c7afd455` Avdan power station | TR | 9.5 | `liquefaction_suscept`=very_low<br>`has_remedy`=NULL | matched current logic |
| 7-8 | `fac3d0b5` Zelwa power station | BY | 7.5 | `liquefaction_suscept`=low<br>`has_remedy`=NULL | matched current logic |
| 7-8 | `1ce7624e` Atlas Enerji İskenderun power station | TR | 7.5 | `liquefaction_suscept`=low<br>`has_remedy`=NULL | matched current logic |
| 5-6 | `6e7fc4d8` Duernrohr power station | AT | 5.5 | `liquefaction_suscept`=high<br>`has_remedy`=NULL | matched current logic |
| 5-6 | `0b187a1d` Leczna Power Station (Bogdanka SA) | PL | 5.5 | `liquefaction_suscept`=moderate<br>`has_remedy`=NULL | matched current logic |
| 3-4 | `e6ecead0` Porto Romano Power Station | AL | 3.5 | `liquefaction_suscept`=very_high<br>`has_remedy`=NULL | matched current logic |
| unscored | `ce39538c` Ağan power station | TR | 5 | `liquefaction_suscept`=NULL<br>`has_remedy`=NULL | unscored |
| unscored | `a96dc545` Cenal power station | TR | 5 | `liquefaction_suscept`=NULL<br>`has_remedy`=NULL | unscored |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: derived context values such as `has_remedy`, landlocked country flags, and BF-02 required/ideal area fields.

## Artifact Footer
- Landed file: `criteria/ranking/NH-03 — Geotechnical settlement and liquefaction.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; R2 is review-only and score-neutral.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
