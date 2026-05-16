<!-- man_hours: 1.0 -->
# NH-02 - Seismic surface rupture (capable faults)

Status: final

Phase: `exclusionary`, `ranking`

Primary metric: `nearest_fault_km`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **no** (weight factor 9, normalised weight 3.2%).

## Specialist Recommendation
Accept the current 5 km score-5 / E1 screening pivot in `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml` for this ranking close-out. The local measured field is populated for all 361 sites, and the active spec/rubric already use the 5 km pivot consistently. The separate 8 km threshold metadata entry remains a threshold-editor reconciliation item outside this worker's allowed file scope.

## Final State
No NH-02 YAML behavior was changed in this worker. Ranking documentation is closed on the active 5 km compiled behavior; sites close to the pivot remain candidates for Stage 3 capable-fault confirmation rather than being reinterpreted from screening evidence alone.

## Decision Matrix
| Audit point | Current evidence | Final documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `exclusionary`, `ranking`; `participates_in_composite` is `false`. | Finalized as current active behavior. |
| Score logic | Local compiled evidence gives matched-band counts `{'0': 12, '1-2': 16, '3-4': 22, '5-6': 18, '7-8': 49, '9-10': 244}`. | Keep the active 5 km score-5 / E1 pivot in ranking docs. |
| Data quality | No raw misses were recorded for declared API fields in the local evidence query. | Use measured local values only; near-pivot cases route to Stage 3 capable-fault confirmation. |
| Threshold metadata | `threshold_metadata.yaml` exposes `E1` with default/recommended 8 km, while current no-override compiled behavior uses 5 km from `band_recipe.score5_pivot`. | Record as an out-of-scope threshold-editor reconciliation item. |
| Filter relationship | Dual exclusionary/ranking. `E1` is an `exclude` action with `pass_mark: 5.0`; as a result this criterion does not participate in the weighted composite. | Preserve the existing phase/action relationship. |

## Accepted Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `nearest_fault_km >= 25.0` | Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level. | 244 |
| 7-8 | `nearest_fault_km >= 10.0` | Clear separation from mapped capable faults; comfortably above the 5.0 km score boundary. | 49 |
| 5-6 | `nearest_fault_km >= 5.0` | Borderline acceptable separation: meets the 5.0 km score boundary; check against the 8 km conservative screen and local capability evidence. | 18 |
| 3-4 | `nearest_fault_km >= 2.5` | Below the 5.0 km score boundary; close enough to require detailed paleoseismic review and likely site rejection if the fault is capable. | 22 |
| 1-2 | `nearest_fault_km >= 1.0` | Very close to a mapped fault; severe surface-rupture concern with little practical siting margin. | 16 |
| 0 | `nearest_fault_km < 1.0` | Within or adjacent to a mapped fault trace; surface rupture cannot be screened out. | 12 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `nearest_fault_km`: present 361/361, NULL 0, min 0.09, max 50, mean 34.0124.
- `fault_name`: present 361/361, NULL 0, top values none_in_search_radius=173, TRCF037=22, TRCF045=14, TRCF005=10, TRCF002=8.
- `fault_slip_rate_mm_yr`: present 361/361, NULL 0, min 0, max 22.694, mean 1.429.
- No raw misses were recorded for declared API fields in the local evidence query.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `E1` | `exclude` | `nearest_fault_km < 5` | 50 | 50 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `fecb62d9` Bandırma III power station | TR | 9.5 | `nearest_fault_km`=25.14<br>`fault_slip_rate_mm_yr`=0.862 | matched current logic |
| 9-10 | `9f4a0d6c` Bydgoszcz power station | PL | 9.5 | `nearest_fault_km`=50<br>`fault_slip_rate_mm_yr`=0 | matched current logic |
| 7-8 | `dd413ee8` Çankırı Orta power station | TR | 7.5 | `nearest_fault_km`=10.06<br>`fault_slip_rate_mm_yr`=1.095 | matched current logic |
| 7-8 | `3a06636d` Selena power station | TR | 7.5 | `nearest_fault_km`=16.73<br>`fault_slip_rate_mm_yr`=0.5 | matched current logic |
| 5-6 | `75f807aa` Bingöl power station | TR | 5.5 | `nearest_fault_km`=5.14<br>`fault_slip_rate_mm_yr`=1.049 | matched current logic |
| 5-6 | `b90e80f9` Eti Maden Bandirma power station | TR | 5.5 | `nearest_fault_km`=6.92<br>`fault_slip_rate_mm_yr`=0.837 | matched current logic |
| 3-4 | `86996d34` Petkim power station | TR | 3.5 | `nearest_fault_km`=2.67<br>`fault_slip_rate_mm_yr`=1.414 | matched current logic |
| 3-4 | `0155b913` Kongora Thermal Power Plant | BA | 3.5 | `nearest_fault_km`=3.56<br>`fault_slip_rate_mm_yr`=0.173 | matched current logic |
| 1-2 | `59f96677` Dinar power station | TR | 1.5 | `nearest_fault_km`=1.02<br>`fault_slip_rate_mm_yr`=1.732 | matched current logic |
| 1-2 | `0ca0b969` Gönen power station | TR | 1.5 | `nearest_fault_km`=1.85<br>`fault_slip_rate_mm_yr`=1.732 | matched current logic |
| 0 | `a9385c82` Pljevlja power station | ME | 0 | `nearest_fault_km`=0.09<br>`fault_slip_rate_mm_yr`=0.173 | matched current logic |
| 0 | `ba1f1f36` Bandırma Elektrik power station | TR | 0 | `nearest_fault_km`=0.56<br>`fault_slip_rate_mm_yr`=2.586 | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-02 — Seismic surface rupture capable faults.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: audit/man-hours reconciliation deferred to parent worker per assignment scope.
