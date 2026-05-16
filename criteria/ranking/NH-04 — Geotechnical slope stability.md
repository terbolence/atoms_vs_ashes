<!-- man_hours: 1.0 -->
# NH-04 - Geotechnical - slope stability

Status: final

Phase: `exclusionary`, `ranking`

Primary metric: `slope_angle_deg`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **no** (weight factor 5, normalised weight 1.8%).

## Specialist Recommendation
Accept the current strict-above-25-degree E3 behavior in the active spec/rubric. The measured local field is a mean slope proxy over a 1 km buffer, not a footprint slope measurement, so exactly 25 degrees should remain on the score-5 boundary and values above 25 degrees should remain the exclusionary screening trigger.

## Final State
No NH-04 YAML behavior was changed in this worker. The threshold metadata operator mismatch (`>=` versus active `>`) remains a threshold-editor reconciliation item outside this worker's allowed file scope; Stage 3 should confirm footprint slope, runout, and slope-stability mechanisms before any site-specific interpretation.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `exclusionary`, `ranking`; `participates_in_composite` is `false`. | Finalized as current active behavior. |
| Score logic | Local compiled evidence gives matched-band counts `{'3-4': 3, '5-6': 84, '7-8': 177, '9-10': 88, 'unscored': 9}`. | Keep strict `> 25` E3 trigger and `<= 25` score-5 boundary. |
| Data quality | Raw misses: `site_natural_hazards.nh04_dem_cog_slope_max_deg`=9; `site_natural_hazards.slope_angle_deg`=9; `site_natural_hazards.slope_stability_class`=9. | Treat mean-slope proxy limits as a Stage 3 footprint/runout characterization need. |
| Threshold metadata | `threshold_metadata.yaml` exposes `E3` as `slope_angle_deg >= 25`, while current bands/exclusion use the strict above-25-degree boundary. | Record as an out-of-scope threshold-editor reconciliation item. |
| Filter relationship | Dual exclusionary/ranking. `E3` is an `exclude` action with `pass_mark: 5.0`; the current slope score floor catches values above 25 degrees. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `slope_angle_deg <= 5.0` | Well below the risk boundary. | 88 |
| 7-8 | `slope_angle_deg <= 10.0` | Low risk relative to the score-5 boundary. | 177 |
| 5-6 | `slope_angle_deg <= 25.0` | At or below the score-5 risk boundary. | 84 |
| 3-4 | `slope_angle_deg < 37.5` | Above the score-5 boundary; specialist review required. | 3 |
| 1-2 | `slope_angle_deg < 50.0` | High risk, with little residual margin. | 0 |
| 0 | `slope_angle_deg >= 50.0` | Outside the acceptance envelope. | 0 |
| unscored | no compiled band matched | pass-mark default, not evidence of a favourable band | 9 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `slope_angle_deg`: present 352/361, NULL 9, min 0.65, max 31.48, mean 8.1418.
- `slope_stability_class`: present 352/361, NULL 9, top values moderate=178, gentle=76, steep=56, very_steep=30, flat=11.
- `nh04_dem_cog_slope_max_deg`: present 352/361, NULL 9, min 7.64, max 89.5, mean 70.0543.
- Raw misses: `site_natural_hazards.nh04_dem_cog_slope_max_deg`=9; `site_natural_hazards.slope_angle_deg`=9; `site_natural_hazards.slope_stability_class`=9.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `E3` | `exclude` | `slope_angle_deg > 25` | 3 | 3 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `3a06636d` Selena power station | TR | 9.5 | `slope_angle_deg`=0.65<br>`slope_stability_class`=flat | matched current logic |
| 9-10 | `4cf7f820` Te-Tol power station | SI | 9.5 | `slope_angle_deg`=3.33<br>`slope_stability_class`=gentle | matched current logic |
| 7-8 | `cd84938d` Turów power station | PL | 7.5 | `slope_angle_deg`=5.02<br>`slope_stability_class`=moderate | matched current logic |
| 7-8 | `021d1717` Star Refinery Socar power station | TR | 7.5 | `slope_angle_deg`=7.59<br>`slope_stability_class`=moderate | matched current logic |
| 5-6 | `202d797d` ZW Nowa power station | PL | 5.5 | `slope_angle_deg`=10.01<br>`slope_stability_class`=steep | matched current logic |
| 5-6 | `0ada7b2a` Tekirdağ Malkara power station | TR | 5.5 | `slope_angle_deg`=12.8<br>`slope_stability_class`=steep | matched current logic |
| 3-4 | `33d83e11` Zeltweg power station | AT | 3.5 | `slope_angle_deg`=26.02<br>`slope_stability_class`=very_steep | matched current logic |
| 3-4 | `008a3366` Trbovlje power station | SI | 3.5 | `slope_angle_deg`=27.25<br>`slope_stability_class`=very_steep | matched current logic |
| unscored | `e75c63e5` Stanari Thermal Power Plant | BA | 5 | `slope_angle_deg`=NULL<br>`slope_stability_class`=NULL | unscored |
| unscored | `274ec928` Komorany power station | CZ | 5 | `slope_angle_deg`=NULL<br>`slope_stability_class`=NULL | unscored |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-04 — Geotechnical slope stability.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
