<!-- man_hours: 1.2 -->
# NS-02 A13 Grid Connection Detailed

Phase: `avoidance, ranking`  
Host criterion: `NS-02` - Grid connection (detailed)  
A-code: `A13` - avoidance penalty, emitted as a `caution` verdict  
Primary A13 metric: `grid_export_capacity_mw`  
Current A13 expression: `grid_export_capacity_mw < 462`  
Threshold metadata: default `462 MW`, operator `<`, bounds `100..1500 MW`

## Status

Status: **IMPLEMENTED - Option A**.

Option A has been implemented narrowly for NS-02/A13. The A13 avoidance predicate remains `grid_export_capacity_mw < 462`, while the capacity-margin score ladder now uses `462 MW` as the score-5/pass boundary. Sites below `462 MW` no longer receive a 5+ score from the capacity band.

## Implemented Decision

Option A from the decision matrix was:

- Make score 5-6 begin at `grid_export_capacity_mw >= 462`.
- Keep A13 as `grid_export_capacity_mw < 462`.
- Recompute upper/lower bands around that boundary.
- Treat this as the direct threshold-consistency fix.

Implemented default capacity bands:

| Score | Condition | Interpretation |
| --- | --- | --- |
| 9-10 | `grid_export_capacity_mw >= 646.8` | At least 40 percent above the 462 MW export need. |
| 7-8 | `grid_export_capacity_mw >= 554.4` | Meets the preferred 20 percent export-capacity margin. |
| 5-6 | `grid_export_capacity_mw >= 462.0` | Meets the A13 hard floor with limited margin. |
| 3-4 | `grid_export_capacity_mw >= 369.6` | Below the A13 hard floor but within 20 percent of the export need. |
| 1-2 | `grid_export_capacity_mw > 0` | Some export path exists but is materially undersized. |
| 0 | `grid_export_capacity_mw <= 0 or grid_export_capacity_mw is null` | No usable export capacity for ranking purposes. |

## Current Scoring Behavior

Current active avoidance:

| Code | Action | Condition | Verdict behavior |
| --- | --- | --- | --- |
| `A13` | `avoidance_penalty` | `grid_export_capacity_mw < 462` | Triggered rows become `caution`; NULL rows are `inconclusive`; non-triggered rows pass A13. |

Current compiled and legacy top-level `capacity_margin` bands:

| Score | Compiled condition | Comment |
| ---: | --- | --- |
| 9-10 | `grid_export_capacity_mw >= 646.8` | 40 percent above 462 MW. |
| 7-8 | `grid_export_capacity_mw >= 554.4` | 20 percent above 462 MW. |
| 5-6 | `grid_export_capacity_mw >= 462.0` | At or above the A13 hard floor. |
| 3-4 | `grid_export_capacity_mw >= 369.6` | Below the A13 hard floor but within 20 percent of the export need. |
| 1-2 | `grid_export_capacity_mw > 0` | Some export path exists but undersized. |
| 0 | `grid_export_capacity_mw <= 0 or grid_export_capacity_mw is null` | Treats NULL as no usable export capacity. |

Current NS-02 subscores:

| Subscore | Metric | Bands | Aggregation role |
| --- | --- | --- | --- |
| `distance_to_grid` | `nearest_hv_line_km` | 9-10 `<1`; 7-8 `<=5`; 5-6 `<=15`; 3-4 `<=30`; 1-2 `>30` | Min-of-subscores ranking axis. |
| `voltage_class` | `hv_line_voltage_kv` | 9-10 `>=400`; 7-8 `>=220`; 5-6 `>=110`; 3-4 `>=33`; 1-2 `<33` | Min-of-subscores ranking axis. |

Current final NS-02 ranking score:

1. Evaluate distance and voltage subscores and aggregate them with `min_of_sub_scores`.
2. Evaluate the compiled top-level capacity band from `capacity_margin`.
3. If the capacity band is lower than the subscore aggregate, cap the final score by the capacity band.
4. Low-quality uncertainty expands score ranges according to the criterion quality floor.

This means capacity can cap a strong distance/voltage site, and the capacity cap now sets the pass boundary at the same 462 MW value used by A13.

## Local DB Evidence

Read-only query basis from the decision pass: local PostgreSQL via `Settings().database.url`, joining `sites` to `site_infrastructure_v2`; no live API/network calls. This implementation did not re-query the database.

Population snapshot:

| Measure | Count |
| --- | ---: |
| `site_infrastructure_v2` rows | 361 |
| `grid_export_capacity_mw` non-NULL | 360 |
| `grid_export_capacity_mw` NULL | 1 |
| Capacity below 462 MW | 180 |
| Capacity at or above 462 MW | 180 |
| Capacity `<= 0` | 0 |
| `nearest_hv_line_km` non-NULL | 361 |
| `hv_line_voltage_kv` non-NULL | 343 |

Boundary and example rows:

| Site | Country | Capacity MW | HV km | Voltage kV | A13 | Implemented score behavior |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Kangal power station | TR | 457 | 0.12 | NULL | caution, 5 MW below threshold | Capacity band now caps below pass mark instead of scoring 7-8. |
| Novaky power station | SK | 472 | 0.40 | 110 | pass, 10 MW above threshold | Final score remains 5.5; capacity band now scores 5-6. |
| Tufanbeyli power station | TR | 450 | 26.75 | 380 | caution, 12 MW below threshold | Final score remains below pass mark from distance/capacity constraints. |
| Stalowa Wola power station | PL | 444 | 0.15 | 110 | caution, 18 MW below threshold | Capacity band now caps below pass mark instead of scoring 7-8. |
| Lagisza power station | PL | 430.1 | 0.21 | 400 | caution, 31.9 MW below threshold | Capacity band now caps below pass mark despite strong distance/voltage geometry. |
| FPCU Feldioara | RO | NULL | 3.31 | 110 | inconclusive | Final score 0.0 because top-level capacity band caps NULL to 0. |

False-positive / false-negative check:

| Direction | Result |
| --- | --- |
| A13 false positives from exact metric rule | None proven. All A13 cautions found in the sample have `grid_export_capacity_mw < 462`. Near-threshold cautions exist, but they are true under the current predicate. |
| A13 false negatives from exact metric rule | None proven for known numeric capacity. Rows with `grid_export_capacity_mw >= 462` pass A13 as specified. |
| Potential semantic false negatives | Capacity `NULL` is not an A13 caution; it is `inconclusive`. There is one local NULL row. This is consistent with expression semantics, but may understate A13 data risk if NULL should be treated as inadequate screening evidence. |
| Potential semantic false positives | Sites just below 462 MW with excellent distance/voltage are cautioned. That is consistent with the numeric A13 floor, and the capacity band now keeps them below the pass mark. |

## NULL and Alias Policy

Current NULL policy, unchanged by Option A:

- A13 avoidance: `grid_export_capacity_mw is null` evaluates as `inconclusive`, not `caution`.
- NS-02 ranking: the capacity band treats NULL as score 0 and can cap the final score to 0.
- Connector meaning: local ENTSO-E documentation says NULL means no per-unit match and no GEM installed-capacity fallback, not a confirmed absence of usable export capacity.

Current alias policy:

- Active A13 host: `NS-02`.
- `BF-01` status: legacy/basic-filter cross-reference only. The threshold metadata comments say BF-01/B1 was retired after SP-F and that NS-02 is the single scored grid-connection criterion.
- Code catalog: `A13` keeps `anchor_aliases=("NS-02", "BF-01")`, so old BF-01 references can still map to the A13 concept.

## Implementation Sources

Files updated for Option A:

- `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`: `capacity_margin` now makes score 5-6 begin at the active A13 pivot.
- `config/scoring_specs/ns_non_safety.yaml`: NS-02 default capacity bands and notes mirror the Option A threshold ladder.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy NS-02 default capacity bands and notes mirror the Option A threshold ladder.
- `tests/criterion_spec/test_band_recipes.py`: unit guard for the recomputed capacity ladder.
- `tests/scoring/test_threshold_band_runtime.py`: runtime guards for default and overridden NS-02/A13 score-5 boundaries.

Relevant sources left unchanged:

- `config/scoring_specs/threshold_metadata.yaml`: `NS-02.A13` already declares the intended `462 MW`, `<`, `grid_export_capacity_mw` threshold.
- `src/atoms_vs_ashes/scoring/avoidance.py`: A13 verdict handling already emits `caution` for true avoidance predicates and `inconclusive` for NULL comparisons.
- `src/atoms_vs_ashes/scoring/bands.py`: top-level bands already cap subscore aggregates when lower.
- `src/atoms_vs_ashes/scoring/_codes.py`: `BF-01` remains a legacy alias only.

## Remaining Risks

- NULL capacity remains split by design: A13 is `inconclusive`, while ranking applies a score-0 capacity cap. That was not changed because the approved decision was only Option A.
- Distance and voltage remain ranking subscores, not A13 predicates. A compound A13 gate would be a separate decision.
- Public/narrative `BF-01` references still exist as legacy continuity references; no BF-01 cleanup was included in this NS-02-only implementation.
