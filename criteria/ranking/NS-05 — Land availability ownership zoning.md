<!-- man_hours: 0.4 -->
# NS-05 — Land availability / ownership / zoning

Status: **accepted current state** for the ranking phase. Cross-reference: `criteria/avoidance/NS-05_A15_land_availability.md`.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-05 — Land availability / ownership / zoning |
| Phases | `[avoidance, ranking]` |
| Primary metric | Runtime recipe uses `largest_contiguous_ha`; hand bands also list `buildable_area_ha` and `patch_count` as context |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` — ranking phase with `avoidance_penalty`, not `exclude` |
| Weight | factor 5; normalised 1.8% |
| Related screen | A15 avoidance caution when `largest_contiguous_ha < 14` |
| Threshold metadata | `NS-05.A15`, default 14 ha, bounds 5-50 ha |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is A15 aligned with the score pivot? | Yes. Runtime bands are compiled from the A15 threshold and move with threshold overrides. | Accept current state. |
| Do hand-written bands equal runtime bands? | No. The spec compiler replaces hand-written composite land bands with a `higher_is_better` recipe over `largest_contiguous_ha`. | Accept as current runtime behavior. |
| Does `zoning_hard_block` currently affect scoring? | No. No model column or derivation was found, and the compiled recipe removes the hand-band 0 clause. | Document as inert text, not active scoring. |
| Is NULL contiguous area treated as failure? | No. NULL does not satisfy `< 14` and falls through to unscored pass-mark behavior. | Accept current NULL policy for this documentation pass. |

## Score Bands

Configured hand bands remain visible in YAML and the legacy rubric:

| Score | Configured hand condition |
| ---: | --- |
| 9-10 | `buildable_area_ha >= 50 and largest_contiguous_ha >= 25` |
| 7-8 | `buildable_area_ha >= 25 and largest_contiguous_ha >= 14` |
| 5-6 | `buildable_area_ha >= 14 and largest_contiguous_ha >= 10` |
| 3-4 | `buildable_area_ha >= 8 or largest_contiguous_ha >= 5` |
| 1-2 | `buildable_area_ha < 8 and largest_contiguous_ha < 5` |
| 0 | `zoning_hard_block == true` |

Accepted runtime bands from the compiled spec are:

| Score | Runtime condition |
| ---: | --- |
| 9-10 | `largest_contiguous_ha >= 70.0` |
| 7-8 | `largest_contiguous_ha >= 28.0` |
| 5-6 | `largest_contiguous_ha >= 14.0` |
| 3-4 | `largest_contiguous_ha >= 7.0` |
| 1-2 | `largest_contiguous_ha >= 2.8` |
| 0 | `largest_contiguous_ha < 2.8` |

## Metric Truth And Data Quality

Primary source fields are `site_infrastructure_v2.buildable_area_ha`, `largest_contiguous_ha`, and `patch_count`; A15 and the runtime recipe use `largest_contiguous_ha`. `buildable_area_ha` remains report context and must not be treated as a substitute for contiguous industrial land.

The avoidance audit found 357 rows with non-null `largest_contiguous_ha`, 86 below 14 ha, 271 at or above 14 ha, and 6 rows with NULL contiguous area in a local extract.

## Examples

| Example | Inputs | Current runtime result |
| --- | --- | --- |
| Bedzin power station, PL | `largest_contiguous_ha = 13.42` | Score 3.5; A15 caution. |
| Ada Yesildag Enerji power station, TR | `largest_contiguous_ha = 14.0` | Score 5.5; A15 pass at the boundary. |
| Tychy power station, PL | `largest_contiguous_ha = 14.09` | A15 pass just above threshold. |
| Bitola power station, MK | `largest_contiguous_ha = 145.73` | Score 9.5 in local bundle; A15 pass. |

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-05 phases, hand bands, A15 condition, recipe, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror with hand bands.
- `config/scoring_specs/threshold_metadata.yaml`: `NS-05.A15` metadata.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-05/BF-02 and A15 mapping.
- `criteria/avoidance/NS-05_A15_land_availability.md`: runtime recipe evidence, NULL policy, and examples.

## Artifact Footer

Documentation-only ranking pass. No scoring specs, rubrics, code, tests, audit logs, or man-hours registry entries were changed.
