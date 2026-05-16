<!-- man_hours: 0.4 -->
# NS-08 — Ecological sensitivity (Natura 2000 / WDPA)

Status: **accepted current runtime state** for the ranking documentation pass, with the composite caveat below.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-08 — Ecological sensitivity (Natura 2000 / WDPA) |
| Phases | `[exclusionary, ranking]` |
| Primary metric | `n2k_nearest_distance_km`; WDPA distance and `ecological_natural_pct` are co-metrics |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `false` in current runtime because the criterion is exclusionary and has an `exclude` action |
| Weight | factor 6; normalised 2.1% in YAML, but not used by weighted composite under current `participates_in_composite` logic |
| Related exclusion | E7 `exclude` when `site_within_strict_protected == true` |
| Related review flag | R1 when `n2k_sensitivity_class == 'high' or wdpa_sensitivity_class == 'high'` |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is strict protected overlap handled as exclusionary? | Yes. E7 excludes strict Natura 2000 / WDPA cases via `site_within_strict_protected`. | Accept current state. |
| Is proximity still scored for ranking displays? | Yes. Ranking rows exist and use Natura 2000 / WDPA distances plus ecological natural percentage. | Accept current state. |
| Does NS-08 affect weighted composite? | No. `participates_in_composite` is false for exclusionary criteria. | Document current runtime caveat. |
| Are NULL distances positive evidence or missing data? | Current notes define NULL as no protected area found within the 25 km connector search radius. | Accept current NULL semantics. |

## Score Bands

| Score | Current condition |
| ---: | --- |
| 9-10 | Both Natura 2000 and WDPA distances are NULL or `> 25 km`, and `ecological_natural_pct` is NULL or `< 15`. |
| 7-8 | Both network distances are NULL or `>= 10 km`. |
| 5-6 | Both network distances are NULL or `>= 5 km`. |
| 3-4 | Both network distances are NULL or `>= 2 km`; ecological review penalty, not exclusionary by itself. |
| 1-2 | Either Natura 2000 or WDPA distance is non-null and `< 2 km`. |
| 0 | `site_within_strict_protected == true` (E7 exclusion). |

No band recipe is declared. The exclusion and review flags are evaluated separately from the ranking row.

## Metric Truth And Data Quality

Primary source fields are `site_infrastructure_v2.n2k_nearest_distance_km`, `wdpa_nearest_distance_km`, `ecological_natural_pct`, overlap booleans, sensitivity classes, and result JSON fields. `site_within_strict_protected` is derived in `merge_context_derivations._derive_ns08_strictness` from Natura 2000 overlap, strict WDPA IUCN categories, and international designations.

`coverage_latest.md` reports NS-08 at 73.66% aggregate coverage, with `ecological_natural_pct`, sensitivity classes, and comments at 100%, while Natura 2000 overlap/distance fields are 44.6%. The spec notes define NULL distance as no protected-area evidence within the connector search radius, not unsourced data.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 scored NS-08 rows; mean 6.99, min 3.5, max 7.5. |
| PL feedback bundle ranking row | Example row scored 7.5 with band `"10-25 km OR natural land 15-30 %."`, `quality_flag = high`, and no raw misses. |
| PL feedback bundle E7 rows | Mixed pass/inconclusive examples appear in historical bundle output; current spec derivation should be used for final E7 interpretation. |

## Composite Caveat

NS-08 is a dual-phase criterion whose ranking rows are useful for display and site-profile explanation. Under the current scoring code, however, any criterion with `exclusionary` phase or an `exclude` action has `participates_in_composite = false`. This documentation pass records that runtime behavior and does not propose a scoring-code change.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-08 phases, E7/R1 conditions, strict-overlap notes, NULL semantics, and bands.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-08 screen-plus-rank and E7 mapping.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing bands and data anchor.
- `src/atoms_vs_ashes/db/models.py`: Natura 2000, WDPA, and ecological-natural fields.
- `src/atoms_vs_ashes/scoring/rubric.py`: `participates_in_composite` runtime rule.

## Artifact Footer

Documentation-only ranking pass. No scoring specs, rubrics, code, tests, audit logs, or man-hours registry entries were changed.
