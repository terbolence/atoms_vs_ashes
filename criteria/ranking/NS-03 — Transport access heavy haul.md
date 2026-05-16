<!-- man_hours: 0.4 -->
# NS-03 — Transport access (heavy haul road / rail / port)

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation. Cross-reference: `criteria/avoidance/NS-03_A14_transport_access.md`.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-03 — Transport access (heavy haul road / rail / port) |
| Phases | `[avoidance, ranking]` |
| Primary metric | Weighted mean of road, rail, and waterway distance sub-scores; A14 uses `heavy_haul_capable` |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` — ranking phase with `avoidance_penalty`, not `exclude` |
| Weight | factor 8; normalised 2.8% |
| Aggregation | `weighted_mean_of_sub_scores`, rounded to 0.1 |
| Related screen | A14 avoidance caution: `heavy_haul_capable == false` |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Are the road/rail/waterway distance ladders internally consistent? | Yes. The three sub-score ladders are monotonic and use persisted distance fields where present. | Accept current ranking ladders. |
| Does A14 fire on missing heavy-haul evidence? | No. `heavy_haul_capable == false` is false when the value is NULL. | Treat NULL as unmeasured screening evidence in documentation; do not convert it to a caution without connector/schema work. |
| Does the current connector emit explicit false? | The avoidance audit found local OSM parser behavior returning `True` or `None`, with no explicit `False` examples in inspected bundles. | Route confirmed-negative capability to a deferred connector improvement. |
| What happens when all transport distances are missing? | Missing sub-scores fall back to unscored 5.0 and aggregate as partial/unscored. | Document as unmeasured at this stage and require Stage 3 route characterization. |

## Current Ranking Logic

| Component | Weight | Metric | Score bands |
| --- | ---: | --- | --- |
| Road | 0.50 | `nearest_highway_km` | 9-10 `< 2`; 7-8 `<= 10`; 5-6 `<= 25`; 3-4 `<= 50`; 1-2 `> 50`. |
| Rail | 0.30 | `nearest_rail_km` | 9-10 `< 1`; 7-8 `<= 5`; 5-6 `<= 15`; 3-4 `<= 30`; 1-2 `> 30`. |
| Waterway | 0.20 | `nearest_waterway_km` | 9-10 `< 2`; 7-8 `<= 10`; 5-6 `<= 30`; 3-4 `<= 75`; 1-2 `> 75` / no navigable waterway. |
| A14 | n/a | `heavy_haul_capable` | `false` triggers caution; `true` and NULL currently do not trigger. |

## Metric Truth And Data Quality

Primary source fields are `site_infrastructure_v2.nearest_highway_km`, `nearest_rail_km`, `nearest_waterway_km`, and `heavy_haul_capable`. The avoidance audit inspected local site bundles and found 33 `true`, 11 NULL, and 0 `false` values for `heavy_haul_capable`; all sampled A14 checks were `not_triggered`.

NULL distance sub-scores fall back to pass-mark defaults rather than hard penalties. This is useful for incomplete OSM coverage, but the all-missing case can still display 5.0 with insufficient confidence.

## Examples

| Example | Inputs | Current behavior |
| --- | --- | --- |
| AT Timelkam power station | `heavy_haul_capable = true`; 1.51 km road / 0.06 km rail / waterway NULL | Score 9.0; A14 not triggered. |
| RO Braila power station | `true`; 3.44 km road / 3.52 km rail / 5.49 km waterway | Score 8.0; A14 not triggered. |
| CZ Pocerady power station | `heavy_haul_capable = NULL`; all three distances NULL | Score 5.0; A14 not triggered. |
| ME Bar power station | `heavy_haul_capable = NULL`; all three distances NULL | Score 5.0; A14 not triggered. |

## Specialist Recommendation

Accept the road, rail, and waterway distance ladders as the ranking state for measured local transport geometry. They are monotonic, use persisted local fields where available, and provide screening-stage differentiation without implying that any route has been proven suitable for heavy haul.

Do not tighten A14 in YAML during this pass. The local evidence shows `heavy_haul_capable` is currently a three-state screening signal in practice: `true` for a found route or proxy, NULL for undetermined, and no inspected explicit `false` examples. Treating NULL as a measured negative would invent capability evidence. The final recommendation is to keep the current predicate for runtime stability, document NULL and all-distance-missing cases as unmeasured at this stage, and defer a connector/schema improvement that can distinguish confirmed no-path evidence from unknown route evidence.

## Final State

NS-03 is finalized as a screen-plus-rank criterion for the ranking sweep with no YAML edits. Measured `nearest_highway_km`, `nearest_rail_km`, and `nearest_waterway_km` values rank transport access. `heavy_haul_capable == false` remains the A14 caution predicate, but NULL heavy-haul capability is not positive evidence; it is a Stage 3 characterization item for route survey, bridge/axle-load confirmation, and logistics-envelope review. All-three-missing transport rows remain unscored defaults in the current engine and must be described as unmeasured, not as adequate access.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-03 phases, sub-scores, A14 condition, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-03 screen-plus-rank and A14 mapping.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing road/rail/waterway bands.
- `criteria/avoidance/NS-03_A14_transport_access.md`: A14 reachability, NULL semantics, and local examples.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
