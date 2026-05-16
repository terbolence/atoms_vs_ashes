<!-- man_hours: 1.8 -->
# NH-09 A11 River Flooding - Avoidance Sweep

Status: final-with-known-follow-up
Phase: [avoidance, ranking]
Primary ranking evidence: `flood_zone_class_500yr`, derived from local `flood_zone_class`
A-code: `A11` (`avoidance_penalty`, verdict `caution`)
A11 condition: `river_distance_km < 4 and elevation_above_design_flood_m < 30.5`

## Decision

Use the flood-zone class as the active Stage 1-2 ranking evidence for NH-09 and keep A11 as a static compound caution. The NH-09 `band_recipe` has been removed from `config/scoring_specs/nh_natural_hazards.yaml` so the existing hand-written bands are now the compiled runtime bands. The `A11` entry has also been removed from `config/scoring_specs/threshold_metadata.yaml` because a single editable `river_distance_km` threshold cannot preserve the fixed `30.5 m` vertical-separation clause.

This is the best available-data treatment under the siting-expert prompt: do not invent unmeasured freeboard, quote and use the measured screening evidence that exists, and route missing site-specific hydrology to Stage 3 characterization. It also restores the signed SP-D direction that `none` / `negligible` flood-zone class is favorable evidence and should not fall through to an unscored neutral default.

## Final Runtime Treatment

| Score | Active condition |
| --- | --- |
| 9-10 | `flood_zone_class_500yr in ['none', 'negligible'] or river_distance_km >= 10 or elevation_above_design_flood_m >= 30.5` |
| 7-8 | `flood_zone_class_500yr == 'low' or river_distance_km >= 4 or elevation_above_design_flood_m >= 30.5` |
| 5-6 | `flood_zone_class_500yr == 'moderate' or river_distance_km >= 2` |
| 3-4 | `flood_zone_class_500yr == 'high'` |
| 1-2 | `flood_zone_class_500yr in ['very_high', 'catastrophic']` |
| 0 | `flood_zone_class_500yr == 'catastrophic' and (has_remedy == false or has_remedy is null)` |

A11 remains static:

```text
river_distance_km < 4 and elevation_above_design_flood_m < 30.5
```

The static A11 treatment means missing `elevation_above_design_flood_m` does not by itself create an avoidance caution. A close river-distance value with missing freeboard is handled through ranking evidence and Stage 3 hydrology follow-up unless both distance and freeboard are measured below the project floor.

## Decision Basis

| Evidence | Decision implication |
| --- | --- |
| `flood_zone_class` is locally available and aliased to `flood_zone_class_500yr`. | Use flood-zone class for Stage 1-2 ranking bands. |
| `nearest_river_km` is sparse in local exported evidence and only aliases to `river_distance_km` when present. | Do not make distance-only bands the primary runtime ladder. |
| `elevation_above_design_flood_m` has no model column or derivation found in local source. | Do not invent freeboard or force A11 caution on unknown freeboard. |
| The previous `band_recipe: flood_distance_or_elevation` ignored flood-zone class and generated an `8.0 km` top band instead of the signed `10 km` / class-based ladder. | Remove the recipe for NH-09. |
| The previous threshold sidecar exposed A11 as a single `river_distance_km < 4` control. | Remove A11 from threshold metadata until compound threshold editing can preserve freeboard. |

## Report-Facing Wording

For report text, describe NH-09 as a screening-grade river-flood criterion using the available flood-zone class first, with river distance and design-flood freeboard used when measured. Avoid saying a site "passes" NH-09 solely because freeboard is missing. Use wording such as: "The available flood-zone class supports progression toward Stage 3 characterization, but design-flood freeboard remains unmeasured and should be confirmed by site-specific hydrology."

## Remaining Risks And Stage 3 Follow-Up

- `elevation_above_design_flood_m` remains unavailable. Stage 3 should measure design-flood water level, local ground elevation, levee condition, drainage pathways, and compound flood scenarios before clearing A11.
- The local flood-zone class is a screening field, not a licensing hydrology model. If national flood maps or site surveys show higher exposure, they override the Stage 1-2 band.
- NH-09 is no longer single-pivot threshold-tunable. Reintroduce A11 threshold metadata only with a compound editor that can render `river_distance_km < X and elevation_above_design_flood_m < 30.5`.

## Source Citations

| Source | Evidence used |
| --- | --- |
| `report/version 1.01/output/writing plan/prompts/specialists/siting_expert.md` | Missing measured values must not be invented; missing evidence routes to Stage 3. |
| `config/scoring_specs/nh_natural_hazards.yaml` | Final active NH-09 bands, static A11 condition, and removal of `band_recipe`. |
| `config/scoring_rubrics/nh_natural_hazards.yaml` | Legacy mirror already carried the class-based NH-09 bands. |
| `config/scoring_specs/threshold_metadata.yaml` | A11 single-metric override removed for NH-09. |
| `src/atoms_vs_ashes/scoring/merge_context_derivations.py` | Aliases `flood_zone_class` to `flood_zone_class_500yr` and `nearest_river_km` to `river_distance_km`. |
| `src/atoms_vs_ashes/scoring/bands.py` | NULL comparison semantics and unscored default behavior. |
| `src/atoms_vs_ashes/db/models.py` | `SiteNaturalHazards` has `flood_zone_class` and `nearest_river_km`; no `elevation_above_design_flood_m` field was found. |
| `report/version 1.01/output/feedback/plans/SP-D_band_proposals/NH-09.md` | Signed proposal expecting `none` / `negligible` flood-zone class to score 9-10. |

Final status: final-with-known-follow-up. The scoring spec now uses the best local NH-09 ranking evidence, while the missing freeboard measurement remains an explicit Stage 3 hydrology item.
