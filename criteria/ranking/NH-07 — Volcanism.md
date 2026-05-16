<!-- man_hours: 0.8 -->
# NH-07 - Volcanism

Status: accepted-current-state

Phase: `exclusionary`, `ranking`

Primary metric: `nearest_volcano_km`

Source spec/rubric: `config/scoring_specs/nh_natural_hazards.yaml` / `config/scoring_rubrics/nh_natural_hazards.yaml`

Composite participation: **no** (weight factor 10, normalised weight 3.5%).

## Decision Matrix
| Audit point | Current evidence | Documentation decision |
| --- | --- | --- |
| Phase/composite | Phases are `exclusionary`, `ranking`; `participates_in_composite` is `false`. | Accept current behavior for documentation. |
| Score logic | Local compiled evidence gives matched-band counts `{'5-6': 8, '7-8': 97, '9-10': 256}`. | Document current compiled behavior, not a proposed change. |
| Data quality | Raw misses: `site_natural_hazards.nearest_volcano_km`=240; `site_natural_hazards.volcano_name`=240. | Treat missing data as a metric-truth caveat; do not infer hard safety facts from neutral defaults. |
| Threshold metadata | `threshold_metadata.yaml` exposes `E4` at 50 km, matching the current compiled exclusion pivot. | Record the metadata relationship. |
| Filter relationship | Dual exclusionary/ranking. `E4` is an `exclude` action at the 50 km pivot; `R1` is a review flag for the connector hazard class. | Preserve the existing phase/action relationship. |

## Current Compiled Score Curve
| Score band | Current compiled condition / logic | Descriptor | Local DB count |
| --- | --- | --- | ---: |
| 9-10 | `nearest_volcano_km is null or nearest_volcano_km >= 250.0` | Very strong margin above the score-5 boundary (or connector confirmed no in-radius signal). | 256 |
| 7-8 | `nearest_volcano_km >= 100.0` | Clear margin above the score-5 boundary. | 97 |
| 5-6 | `nearest_volcano_km >= 50.0` | At or above the score-5 boundary. | 8 |
| 3-4 | `nearest_volcano_km >= 25.0` | Below the score-5 boundary but not extreme. | 0 |
| 1-2 | `nearest_volcano_km >= 10.0` | Materially below the score-5 boundary. | 0 |
| 0 | `nearest_volcano_km < 10.0` | Well inside the hazard envelope or with insufficient margin. | 0 |


## Metric Truth And Data Quality
Local evidence basis: 361-site active merged DB, read-only local PostgreSQL query through `ScoringEngine._precompute_site()` using the compiled scoring specs. No API, enrichment, web, or remote calls were made.
- `nearest_volcano_km`: present 121/361, NULL 240, min 70.98, max 291.97, mean 184.3782.
- `volcano_name`: present 121/361, NULL 240, top values Kula=54, Erciyes Volcanic Complex=42, Hasandag-Keciboyduran Volcanic Complex=13, Nisyros=6, Nemrut Dagi=4.
- `nh07_hazard_class`: present 361/361, NULL 0, top values negligible=240, low=115, avoidance=6.
- Raw misses: `site_natural_hazards.nearest_volcano_km`=240; `site_natural_hazards.volcano_name`=240.

## Fail, Avoidance, And Review Conditions
| Code | Action | Expression | Trigger count | Floor count |
| --- | --- | --- | ---: | ---: |
| `E4` | `exclude` | `nearest_volcano_km < 50` | 0 | 0 |
| `R1` | `review_flag` | `nh07_hazard_class == 'avoidance'` | 6 | 0 |

## Local Scored Examples
| Band | Site | Country | Score | Key values | Notes |
| --- | --- | --- | ---: | --- | --- |
| 9-10 | `0ca4ff78` Şevketiye Lapseki power station | TR | 9.5 | `nearest_volcano_km`=250.43<br>`nh07_hazard_class`=low | matched current logic |
| 9-10 | `27fc89b3` Lagisza power station | PL | 9.5 | `nearest_volcano_km`=NULL<br>`nh07_hazard_class`=negligible | matched current logic |
| 7-8 | `4ca3c560` Soma power station | TR | 7.5 | `nearest_volcano_km`=102.63<br>`nh07_hazard_class`=low | matched current logic |
| 7-8 | `3e5f4317` Sanko Yumurtalık power station | TR | 7.5 | `nearest_volcano_km`=188.18<br>`nh07_hazard_class`=low | matched current logic |
| 5-6 | `a6478cb9` Karapinar Konya Şeker power station | TR | 5.5 | `nearest_volcano_km`=70.98<br>`nh07_hazard_class`=low | matched current logic |
| 5-6 | `8e7f6abf` Kemerköy power station | TR | 5.5 | `nearest_volcano_km`=82.87<br>`nh07_hazard_class`=avoidance | matched current logic |

## Source Citations
- `config/scoring_specs/nh_natural_hazards.yaml` and `config/scoring_rubrics/nh_natural_hazards.yaml`: criterion phases, bands, fail conditions, weights, and data fields.
- `config/scoring_specs/threshold_metadata.yaml`: threshold metadata for the criterion code noted above.
- `docs/expert_siting_criteria_evaluation_matrix.md`: normative basis, phase classification, and scoring-weight context.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` is false for ranking criteria that are also exclusionary or have an `exclude` fail condition.
- `src/atoms_vs_ashes/scoring/bands.py`: no matched band returns the neutral 5.0 `unscored` result.

## Artifact Footer
- Landed file: `criteria/ranking/NH-07 — Volcanism.md`.
- Validation: local compiled-spec evidence query against the 361-site DB; no behavior-changing tests were required because this run changed documentation only.
- Audit: conversation log and man-hours registry updated for this documentation sweep.
