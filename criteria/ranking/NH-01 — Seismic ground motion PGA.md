<!-- man_hours: 0.8 -->
# NH-01 - Seismic ground motion (PGA)

Status: accepted-current-state

Phase: `ranking`, `avoidance`

Primary metric: `pga_2475yr_g`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **yes** (weight factor 9, normalised weight 3.2%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `ranking`, `avoidance`; `participates_in_composite` is `true`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'0': 9, '1-2': 26, '3-4': 75, '5-6': 115, '7-8': 33, '9-10': 87, 'unscored': 16}`. | Document current compiled behavior, not a proposed change. |
| Data quality | Raw misses: `site_natural_hazards.nh01_pga_2475yr_g`=16; `site_natural_hazards.vs30_ms`=361. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Threshold metadata | `threshold_metadata.yaml` exposes `A10` as `pga_2475yr_g > 0.5 g` with bounds 0.2-1.5 g. | Record the metadata relationship. |
| Filter relationship | Ranking plus avoidance. `A10` is an `avoidance_penalty` above 0.5 g; `data_review_pga` is a review flag above 0.9 g. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `pga_2475yr_g <= 0.1` | Well below the risk boundary. | 87 |
| 7-8 | `pga_2475yr_g <= 0.2` | Low risk relative to the score-5 boundary. | 33 |
| 5-6 | `pga_2475yr_g <= 0.5` | At or below the score-5 risk boundary. | 115 |
| 3-4 | `pga_2475yr_g < 0.75` | Above the score-5 boundary; specialist review required. | 75 |
| 1-2 | `pga_2475yr_g < 1.0` | High risk, with little residual margin. | 26 |
| 0 | `pga_2475yr_g >= 1.0` | Outside the acceptance envelope. | 9 |
| unscored | no compiled band matched | pass-mark default, not evidence of a favourable band | 16 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `pga_2475yr_g`: present 345/361, NULL 16, min 0.0109, max 1.1438, mean 0.3525.
- `nh01_pga_475yr_g`: present 361/361, NULL 0, min 0, max 0.5642, mean 0.1645.
- `vs30_ms`: present 0/361, NULL 361, top values none.
- Raw misses: `site_natural_hazards.nh01_pga_2475yr_g`=16; `site_natural_hazards.vs30_ms`=361.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `A10` | `avoidance_penalty` | `pga_2475yr_g > 0.5` | 110 | 0 |
| `data_review_pga` | `review_flag` | `pga_2475yr_g > 0.9` | 17 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `68aabff9` Lelchitsy power station | BY | 9.5 | `pga_2475yr_g`=0.0109<br>`nh01_pga_475yr_g`=0.0017 | matched current logic |
| 9-10 | `a7eeee6e` Siechnice power station | PL | 9.5 | `pga_2475yr_g`=0.046<br>`nh01_pga_475yr_g`=0.0177 | matched current logic |
| 7-8 | `20bce4f5` Porici power station | CZ | 7.5 | `pga_2475yr_g`=0.103<br>`nh01_pga_475yr_g`=0.0241 | matched current logic |
| 7-8 | `059b3ad4` Torony power station | HU | 7.5 | `pga_2475yr_g`=0.1299<br>`nh01_pga_475yr_g`=0.0577 | matched current logic |
| 5-6 | `6e7fc4d8` Duernrohr power station | AT | 5.5 | `pga_2475yr_g`=0.2015<br>`nh01_pga_475yr_g`=0.0867 | matched current logic |
| 5-6 | `0248611c` Kangal power station | TR | 5.5 | `pga_2475yr_g`=0.3099<br>`nh01_pga_475yr_g`=0.156 | matched current logic |
| 3-4 | `e8b6e342` Yeniyurt power station | TR | 3.5 | `pga_2475yr_g`=0.5044<br>`nh01_pga_475yr_g`=0.2594 | matched current logic |
| 3-4 | `1624a526` İskenderun power station | TR | 3.5 | `pga_2475yr_g`=0.5456<br>`nh01_pga_475yr_g`=0.2688 | matched current logic |
| 1-2 | `161660e7` DOSAB cogeneration plant | TR | 1.5 | `pga_2475yr_g`=0.751<br>`nh01_pga_475yr_g`=0.3993 | matched current logic |
| 1-2 | `e6ecead0` Porto Romano Power Station | AL | 1.5 | `pga_2475yr_g`=0.7906<br>`nh01_pga_475yr_g`=0.393 | matched current logic |
| 0 | `737b6d06` Yeniköy power station | TR | 0 | `pga_2475yr_g`=1.0019<br>`nh01_pga_475yr_g`=0.449 | matched current logic |
| 0 | `8e7f6abf` Kemerköy power station | TR | 0 | `pga_2475yr_g`=1.041<br>`nh01_pga_475yr_g`=0.4704 | matched current logic |
| unscored | `95872473` Cherkasy power station | UA | 5 | `pga_2475yr_g`=NULL<br>`nh01_pga_475yr_g`=0 | unscored |
| unscored | `02253fcc` Prydniprovska power station | UA | 5 | `pga_2475yr_g`=NULL<br>`nh01_pga_475yr_g`=0 | unscored |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-01 — Seismic ground motion PGA.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
