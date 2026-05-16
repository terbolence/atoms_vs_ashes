<!-- man_hours: 0.8 -->
# BF-02 - Land / nuclear-island footprint

Status: accepted-current-state

Phase: `basic_filter`, `ranking`

Primary metric: `buildable_area_ha, largest_contiguous_ha, required_area_ha, ideal_area_ha`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 5, normalised weight 1.8%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `basic_filter`, `ranking`; `participates_in_composite` is `true`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'1-2': 123, '3-4': 29, '5-6': 25, '7-8': 29, '9-10': 155}`. | Document current compiled behavior, not a proposed change. |
| Data quality | Raw misses: `site_infrastructure_v2.largest_contiguous_ha`=6; `sites.site_area_ha`=105. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Filter relationship | Basic-filter note plus ranking score. `B2` is a `screen_flag` with `false`, so it records the land-footprint pivot without creating an automatic fail. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `largest_contiguous_ha >= ideal_area_ha and buildable_area_ha >= ideal_area_ha` | Contiguous and buildable >= ideal area (70 ha/module). | 155 |
| 7-8 | `largest_contiguous_ha >= required_area_ha and buildable_area_ha >= required_area_ha` | Contiguous and buildable >= required area (50 ha/module). | 29 |
| 5-6 | `buildable_area_ha >= required_area_ha * 0.8` | 80-100% of required area with documented expansion / layout flexibility. | 25 |
| 3-4 | `buildable_area_ha >= required_area_ha * 0.5` | 50-80% of required area; phased layout required. | 29 |
| 1-2 | `buildable_area_ha < required_area_ha * 0.5` | < 50% of required area; insufficient for nuclear island at screening. | 123 |
| 0 | `buildable_area_ha == 0` | No useable land. | 0 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `buildable_area_ha`: present 361/361, NULL 0, min 0.01, max 800.17, mean 96.0063.
- `largest_contiguous_ha`: present 355/361, NULL 6, min 0.01, max 1256.51, mean 238.769.
- `site_area_ha`: present 256/361, NULL 105, min 0.01, max 800.17, mean 55.7975.
- `required_area_ha`: present 361/361, NULL 0, min 50, max 50, mean 50.
- `ideal_area_ha`: present 361/361, NULL 0, min 70, max 70, mean 70.
- Raw misses: `site_infrastructure_v2.largest_contiguous_ha`=6; `sites.site_area_ha`=105.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `B2` | `screen_flag` | `false` | 0 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `85257083` Gacko Thermal Power Plant | BA | 9.5 | `buildable_area_ha`=96.78<br>`largest_contiguous_ha`=96.78<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 9-10 | `c657c5c3` Diler (Akbayir) Elbistan power station | TR | 9.5 | `buildable_area_ha`=314.13<br>`largest_contiguous_ha`=1256.51<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 7-8 | `82011c29` Banovici power station | BA | 7.5 | `buildable_area_ha`=55.98<br>`largest_contiguous_ha`=155.44<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 7-8 | `f5be4e73` Skawina power station | PL | 7.5 | `buildable_area_ha`=50.6<br>`largest_contiguous_ha`=50.6<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 5-6 | `99d712ac` Voitsberg power station | AT | 5.5 | `buildable_area_ha`=41.4<br>`largest_contiguous_ha`=41.4<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 5-6 | `66bdc30c` Stalowa Wola power station | PL | 5.5 | `buildable_area_ha`=45.54<br>`largest_contiguous_ha`=45.54<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 3-4 | `021c723b` St Andrae power station | AT | 3.5 | `buildable_area_ha`=39.03<br>`largest_contiguous_ha`=39.03<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 3-4 | `c39819ef` Konin power station | PL | 3.5 | `buildable_area_ha`=28.33<br>`largest_contiguous_ha`=28.33<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 1-2 | `e6ecead0` Porto Romano Power Station | AL | 1.5 | `buildable_area_ha`=5.75<br>`largest_contiguous_ha`=616.36<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |
| 1-2 | `3d2d4c37` Tychy power station | PL | 1.5 | `buildable_area_ha`=14.09<br>`largest_contiguous_ha`=14.09<br>`required_area_ha`=50<br>`ideal_area_ha`=70 | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: derived context values such as `has_remedy`, landlocked country flags, and BF-02 required/ideal area fields.

## Artifact Footer
- Landed file: `criteria/ranking/BF-02 — Land and nuclear-island footprint.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
