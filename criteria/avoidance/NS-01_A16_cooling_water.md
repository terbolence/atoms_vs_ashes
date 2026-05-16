<!-- man_hours: 1.1 -->
# NS-01 A16 - Cooling water / ultimate heat sink

Status: **accepted-current-state**. No behavior-changing scoring issue was found in this sweep.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-01 - Cooling water / ultimate heat sink |
| Phase | `[avoidance, ranking]` |
| A-code | A16 |
| Action | `avoidance_penalty` / caution, not hard exclusion |
| Active A16 condition | `cooling_distance_km > 10 and water_stress_label in ['High', 'Extremely High']` |
| Pass mark | 5.0 for ranking score; no NS-01 exclusionary floor remains |
| Aggregation | `weighted_mean_of_sub_scores`, rounded to 0.1 |
| Composite participation | `true` |
| Primary evidence fields | `cooling_source_type`, `cooling_distance_km`, `cooling_flow_m3s`, `water_stress_score`, `water_stress_label` |
| Derived helper | `dry_cooling_viable`, used only by the source-type 0-band |

## Decision Matrix

| Question | Evidence checked | Decision |
| --- | --- | --- |
| Does A16 replace the retired E9 hard fail? | Specs and rubrics now expose only A16 under NS-01 fail conditions; tests assert no `exclude` action and no E9 catalogue entry. | Accept current state. |
| Is A16 tied to the intended active condition? | Current condition is exactly distance greater than 10 km plus WRI label `High` or `Extremely High`. Local replay found 18 / 361 triggers, all matching that expression. | Accept current state. |
| Does `dry_cooling_viable` drive avoidance? | A16 does not reference `dry_cooling_viable`. Local replay includes A16 triggers with `dry_cooling_viable == True` and non-triggers with `dry_cooling_viable == False`. | Accept current state. |
| Is `dry_cooling_viable` still useful? | It is derived as `False` only for arid/hot-summer countries with `water_stress_label == 'Extremely High'`; otherwise `True`. It only reaches the source-type 0-band when no cooling source is present. | Keep as derived sub-score helper. |
| Are source and distance semantics aligned to connector data? | HydroRIVERS emits `major_river`, `river`, `small_river`, and `stream`; distance is km to the selected reach; local bundle replay has no NULLs in the 361-row country-bundle set. | Accept current state. |
| Are false positives or false negatives visible locally? | For 361 local country-bundle rows, expression mismatch count was 0 false positives and 0 false negatives. | No behavior issue found. |
| Is threshold metadata missing for A16? | `threshold_metadata.yaml` has no NS-01/A16 entry. The expression is a two-field compound condition, so it remains a fixed best-practice envelope rather than a GUI numeric override. | Accept current state. |

## Final Scoring Bands

NS-01 is a three-part weighted composite. The drought/SPI-12 sub-score from the old E9-era design is intentionally absent until a connector writes a durable `spi12_min` field.

| Sub-score | Weight | Primary metric | Current bands |
| --- | ---: | --- | --- |
| `source_type` | 0.44 | `cooling_source_type` | 9-10 `major_river`; 7-8 `river`; 5-6 `small_river`; 3-4 `stream`; 1-2 `cooling_source_type is null` with no source within practical distance; 0 only when no source and `dry_cooling_viable == false`. |
| `distance_to_source` | 0.25 | `cooling_distance_km` | 9-10 `< 0.5`; 7-8 `< 2`; 5-6 `< 5`; 3-4 `<= 10`; 1-2 `> 10`. |
| `water_stress` | 0.31 | `water_stress_label` | 9-10 `Low`; 7-8 `Low-Medium`; 5-6 `Medium-High`; 3-4 `High`; 1-2 `Extremely High`. |

The A16 avoidance flag is independent of the aggregate score. A site can score above 5.0 and still receive A16 if the two active A16 inputs are true, for example a `major_river` site more than 10 km away in a `High` stress basin.

## Transition Note

The 2026-05-16 refactor retired the old E9 hard fail:

`cooling_source_type in ['none', null] and dry_cooling_viable == false`

That condition was structurally unreachable in the current scoring context. Earlier audit evidence recorded 0 / 2,904 site-SMR pairs triggering E9, while `dry_cooling_viable` was not then available in context. The accepted replacement is A16: a caution-level avoidance penalty for cooling-source distance greater than 10 km combined with `High` or `Extremely High` WRI Aqueduct baseline water stress.

This is a behavior change already landed before this sweep. This sweep found no additional behavior-changing issue and documents the current state as accepted.

## Local Evidence

Local DB files were not present as `.db`, `.sqlite`, `.sqlite3`, or `.duckdb` files in the workspace. The local evidence used here is the committed audit trail plus a local in-process replay of the country bundle data in `report/output/bundles/feedback_rerun_20260509/*_country_bundle.json` against the current NS-01 rubric.

Local replay results:

| Check | Result |
| --- | ---: |
| Country-bundle site rows with NS-01 infrastructure fields | 361 |
| `cooling_source_type` NULL | 0 |
| `cooling_distance_km` NULL | 0 |
| `water_stress_label` NULL | 0 |
| A16 true | 18 |
| Rows satisfying active A16 expression | 18 |
| False positives vs active expression | 0 |
| False negatives vs active expression | 0 |
| Distance > 10 km but stress below High | 60 |
| High/Extremely High stress but distance <= 10 km | 60 |
| `dry_cooling_viable == false` | 18 |
| `dry_cooling_viable == false` and A16 true | 3 |

Representative replay examples:

| Site | Inputs | Current NS-01 score | A16 result | Note |
| --- | --- | ---: | --- | --- |
| Blachownia power station, PL | `small_river`, 10.75 km, `High`, dry viable `True` | 4.0 | true | Shows A16 does not depend on `dry_cooling_viable == false`. |
| Alpu power station, TR | `river`, 10.09 km, `Extremely High`, dry viable `False` | 4.0 | true | Just over the distance threshold and extreme stress. |
| Karapinar Konya Seker power station, TR | `small_river`, 11.36 km, `Extremely High`, dry viable `False` | 3.0 | true | Low scoring and A16 flagged. |
| Naren Karabiga power station, TR | 9.92 km, `High` | 5.0 | false | Boundary check: 10 km itself is not enough; A16 is strictly `> 10`. |
| Guney Akdeniz power station, TR | 34.97 km, `Medium-High` | 6.0 | false | Long distance alone does not trigger A16. |
| Yeniyurt power station, TR | 27.27 km, `Low` | 6.0 | false | Long distance plus low stress remains ranking-only. |
| Borsod power station, HU | `major_river`, 0.49 km, `Low` | 10.0 | false | Strong pass example. |
| Vidin Works power station, BG | `major_river`, 1.43 km, `Low` | 9.0 | false | Strong pass example. |

The refactor audit also recorded a read-only merged-DB sanity check with the same A16 population: 18 / 361 sites, consisting of 17 TR sites and 1 PL site.

## NULL And Alias Policy

- `cooling_source_type is null` means HydroRIVERS did not find a source within the configured search radius. In current local country-bundle evidence, this did not occur.
- `cooling_distance_km is null` means no matched cooling source distance is available. It does not trigger A16 because the active expression requires `cooling_distance_km > 10`.
- `water_stress_label is null` means no WRI Aqueduct label is available. It does not trigger A16 because the active expression requires `High` or `Extremely High`.
- There is no NS-01 alias rule in `merge_context_derivations.py`; NS-01 uses persisted `site_infrastructure_v2` fields directly.
- `dry_cooling_viable` is a derived context name, not a DB column. Caller-supplied values take precedence, but production scoring derives it from `country_code` and `water_stress_label`.
- The derived helper defaults to `True` unless the country is in `{TR, CY, MT, ES, PT, GR}` and the water-stress label is `Extremely High`.

## Residual Documentation Gaps

- Some historical requirement text still mentions E9 as "insufficient cooling water". That is stale after the 2026-05-16 refactor, but it is documentation drift rather than active scoring behavior. This sweep did not edit shared report or requirement files by instruction.
- Older generated site bundles may contain saved NS-01 justifications that reference the removed `site_natural_hazards.spi12_min` raw miss. The replay above used raw infrastructure inputs against the current rubric, not those stale saved scores.
- The future drought/SPI-12 sub-score remains deferred until a connector writes a durable metric. That is tracked as IMP-0007 and is not part of current A16 behavior.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml` and `config/scoring_rubrics/ns_non_safety.yaml`: current NS-01 phase, DB fields, sub-score bands, and A16 condition.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: `DERIVED_CONTEXT_NAMES` includes `dry_cooling_viable`; `_derive_dry_cooling_viable` implements the arid-country plus `Extremely High` heuristic.
- `tests/scoring/test_ns01_refactor.py`: regression coverage for phase, composite participation, source-type bands, water-stress label bands, A16 boundary behavior, derived helper behavior, and representative composite scores.
- `tests/scoring/test_suitable_sites_audit.py`: audit catalogue asserts NS-01 E9 is absent and A16 is present.
- `tests/scoring/test_safety_floor_pipeline.py`: NS-01 is deliberately omitted from exclusionary floor assertions because the E9 floor was retired.
- `docs/expert_siting_criteria_evaluation_matrix.md`: A16 criterion map and NS-01 rank-plus-avoid narrative.
- `report/sites_evaluation/07_criteria_non_safety.md`: current NS-01 report-facing scoring summary.
- `docs/connector_reports/ns01_cooling_fix06_sample_report.md`: HydroRIVERS/WRI metric semantics, NULL meanings, and 363-site connector coverage notes.
- `audit/conversations/2026-05-16_ns01-e9-to-a16-cooling-stress.md`: accepted transition record and original DB sanity check.

## Final Status

Accepted current state. A16 is the active avoidance condition for NS-01. `dry_cooling_viable` remains a derived sub-score helper only, not an avoidance gate. No scoring spec or rubric edit is recommended from this criterion sweep.
