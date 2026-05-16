<!-- man_hours: 0.4 -->
# NS-01 — Cooling water / ultimate heat sink

Status: **accepted current state** for the ranking phase. Cross-reference: `criteria/avoidance/NS-01_A16_cooling_water.md`.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-01 — Cooling water / ultimate heat sink |
| Phases | `[avoidance, ranking]` |
| Primary metric | Composite of `cooling_source_type`, `cooling_distance_km`, and `water_stress_label` |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` — ranking phase with no `exclude` action |
| Weight | factor 8; normalised 2.8% |
| Aggregation | `weighted_mean_of_sub_scores`, rounded to 0.1 |
| Related screen | A16 avoidance caution when `cooling_distance_km > 10 and water_stress_label in ['High', 'Extremely High']` |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is the ranking score still active after the E9 retirement? | Yes. E9 is gone; NS-01 remains `[avoidance, ranking]` and participates in the composite. | Accept current state. |
| Does A16 change the ranking score? | No. A16 emits an avoidance `caution`; the weighted sub-score remains separate. | Accept current state. |
| Is `dry_cooling_viable` a ranking helper or avoidance gate? | Helper only. It is used only in the source-type 0-band when no source is found and dry cooling is not viable. | Accept current state. |
| Is threshold metadata expected? | No NS-01/A16 sidecar exists; A16 is a two-field compound condition rather than a single GUI-tunable numeric threshold. | Accept current state. |

## Score Bands

| Component | Weight | Metric | Score logic |
| --- | ---: | --- | --- |
| `source_type` | 0.44 | `cooling_source_type` | 9-10 `major_river`; 7-8 `river`; 5-6 `small_river`; 3-4 `stream`; 1-2 no HydroRIVERS source within practical distance; 0 only when no source and `dry_cooling_viable == false`. |
| `distance_to_source` | 0.25 | `cooling_distance_km` | 9-10 `< 0.5`; 7-8 `< 2`; 5-6 `< 5`; 3-4 `<= 10`; 1-2 `> 10`. |
| `water_stress` | 0.31 | `water_stress_label` | 9-10 `Low`; 7-8 `Low-Medium`; 5-6 `Medium-High`; 3-4 `High`; 1-2 `Extremely High`. |

Local evidence from the avoidance sweep replay found 361 country-bundle rows with all three active infrastructure fields non-null. A16 matched 18 rows exactly; no false positives or false negatives were found against the active expression.

## Metric Truth And Data Quality

Primary source fields live on `site_infrastructure_v2`: `cooling_source_type`, `cooling_source_name`, `cooling_source_hyriv_id`, `cooling_distance_km`, `cooling_flow_m3s`, `water_stress_score`, and `water_stress_label`. `dry_cooling_viable` is derived from `country_code` plus `water_stress_label`; it is not a stored DB column.

NULL semantics are conservative: NULL source/distance/stress values do not trigger A16 unless the expression can be proven true. The seasonal drought/SPI-12 sub-score remains deferred until a durable connector writes `spi12_min`; this is tracked as `IMPROVEMENTS.md` IMP-0007.

## Examples

| Example | Inputs | Ranking result | A16 |
| --- | --- | ---: | --- |
| Borsod power station, HU | `major_river`, 0.49 km, `Low` | 10.0 | false |
| Vidin Works power station, BG | `major_river`, 1.43 km, `Low` | 9.0 | false |
| Blachownia power station, PL | `small_river`, 10.75 km, `High` | 4.0 | true |
| Alpu power station, TR | `river`, 10.09 km, `Extremely High` | 4.0 | true |

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-01 phases, sub-scores, aggregation, A16 condition, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-01 rank-plus-avoid narrative and A16 mapping.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing scoring summary.
- `criteria/avoidance/NS-01_A16_cooling_water.md`: accepted A16 audit, local replay counts, and examples.

## Artifact Footer

Documentation-only ranking pass. No scoring specs, rubrics, code, tests, audit logs, or man-hours registry entries were changed.
