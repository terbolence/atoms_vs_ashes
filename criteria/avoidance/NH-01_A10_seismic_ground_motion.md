<!-- man_hours: 0.8 -->
# NH-01 A10 Seismic Ground Motion

Status: accepted-current-state

Phase: `ranking`, `avoidance`

Primary metric: `pga_2475yr_g`

A-code: `A10`

Host criterion: `NH-01` - Seismic ground motion (PGA)

## Decision Matrix

| Audit point | Current evidence | Decision |
| --- | --- | --- |
| A10 trigger | `config/scoring_specs/nh_natural_hazards.yaml` defines `A10` as `pga_2475yr_g > 0.5`; the compiled criterion emits the same expression. | Accept current behavior. |
| Score-5 boundary | Current and compiled score 5-6 band is `pga_2475yr_g <= 0.5`; values just over the boundary score 3.5 and trigger A10. | Accept current behavior. |
| Metric naming | Spec `db_fields.api` uses prefixed names `nh01_pga_475yr_g` and `nh01_pga_2475yr_g`; ORM storage uses bare `pga_475yr_g` and `pga_2475yr_g`. `build_context_for_site()` strips the `nh01_` prefix and exposes both keys. | No alias defect for scoring. |
| Recipe drift | Spec uses `band_recipe: {kind: lower_is_better, fail_code: A10, metric: pga_2475yr_g}`. Default threshold metadata is 0.5 g, and compiled bands rebuild to 0.1, 0.2, 0.5, 0.75, 1.0 g. | No band/threshold drift found. |
| `derive_expr_from_recipe` suitability | A10 is an `avoidance_penalty`, not an exclusionary `exclude` fail condition. The compiler's `derive_expr_from_recipe` path is deliberately scoped to exclusionary single-pivot checks; A10 instead uses threshold metadata to move the fail expression and recipe bands together. | No change needed. |
| Threshold metadata | `threshold_metadata.yaml` sets metric `pga_2475yr_g`, op `>`, default and recommended value `0.5`, units `g`, bounds `0.2` to `1.5`. These agree with the A10 condition and score-5 boundary. | Accept current metadata. |
| False positives | Local DB latest A10 run `score-d51c7c6b`: 110 `caution` verdicts, all with `pga_2475yr_g > 0.5`; no raw pass values appear in caution rows. | No false positives found. |
| False negatives | Latest A10 run: 235 `pass` verdicts, all with `pga_2475yr_g <= 0.5`; 16 NULL metric rows are `inconclusive`, not `pass`. | No false negatives found in local evidence. |

## Current And Final Scoring Bands

Final state is current state. No scoring spec, rubric, or threshold metadata edit is proposed.

| Score band | Current/final condition | Interpretation |
| --- | --- | --- |
| 9-10 | `pga_2475yr_g <= 0.10` | Very low long-return seismic demand. |
| 7-8 | `pga_2475yr_g <= 0.20` | Low long-return seismic demand. |
| 5-6 | `pga_2475yr_g <= 0.50` | At or below the A10 design-envelope boundary; acceptable with vendor-specific confirmation. |
| 3-4 | `pga_2475yr_g < 0.75` | Above the A10 boundary; specialist seismic review and avoidance penalty. |
| 1-2 | `pga_2475yr_g < 1.00` | High long-return seismic demand. |
| 0 | `pga_2475yr_g >= 1.00` | Extreme long-return seismic demand. |

Fail and review conditions:

| Code | Action | Current/final expression | Status |
| --- | --- | --- | --- |
| `A10` | `avoidance_penalty` | `pga_2475yr_g > 0.5` | Accepted. Values exactly 0.5 g pass; values above 0.5 g trigger A10. |
| `data_review_pga` | `review_flag` | `pga_2475yr_g > 0.9` | Accepted as a data-validity surface, not the A-code gate. |

## Transition Note

This document records the accepted current implementation for A10. Earlier concerns about prefixed database fields do not apply to runtime scoring because `merge_resolver.resolve_scalar()` first looks for the prefixed column and then falls back to the stripped bare ORM field. A checked context for Maritsa 3 exposed both `nh01_pga_2475yr_g` and `pga_2475yr_g` as `0.49969`.

Threshold overrides are also coherent. A local compile with `fail_thresholds: {NH-01: {A10: 0.6}}` produced score 5-6 at `pga_2475yr_g <= 0.6` and A10 at `pga_2475yr_g > 0.6`.

## Local DB Examples

Local DB query basis: `site_natural_hazards` joined to `sites`; latest persisted A10 verdict run by `prompt_key='A10'` was `score-d51c7c6b`.

| Example type | Site | Country | `pga_2475yr_g` | `pga_475yr_g` | Quality/source | Expected A10 outcome |
| --- | --- | --- | ---: | ---: | --- | --- |
| Passing low PGA | Lelchitsy power station | BY | 0.01092 | 0.00169 | high / `efehr_eshm13` | Pass. |
| Passing low PGA | Zarnowiec power station | PL | 0.01860 | 0.00649 | high / `efehr_eshm13` | Pass. |
| Boundary pass | Maritsa 3 power station | BG | 0.49969 | 0.20186 | high / `efehr_eshm13` | Pass, below 0.5 g. |
| Boundary fail | Yeniyurt power station | TR | 0.50438 | 0.25941 | high / `efehr_eshm13` | A10 caution, above 0.5 g. |
| High PGA fail | Bingol power station | TR | 1.14380 | 0.55519 | high / `efehr_eshm13` | A10 caution plus data-review expression. |
| High PGA fail | Tekirdag Malkara power station | TR | 1.13274 | 0.56420 | high / `efehr_eshm13` | A10 caution plus data-review expression. |
| NULL 2475-year metric | Kramatorskaya power station | UA | NULL | 0.00000 | medium / `gem_global_v2023` | Inconclusive, not pass and not A10 caution. |
| NULL 2475-year metric | Myronivskyi power station | UA | NULL | 0.00000 | medium / `gem_global_v2023` | Inconclusive, not pass and not A10 caution. |

Aggregate local evidence:

| Check | Count |
| --- | ---: |
| `site_natural_hazards` rows | 361 |
| Rows with `pga_2475yr_g` present | 345 |
| Rows with `pga_2475yr_g > 0.5` | 110 |
| Rows with `pga_2475yr_g <= 0.5` | 235 |
| Rows with `pga_2475yr_g is null` | 16 |
| Latest A10 persisted pass verdicts | 235 |
| Latest A10 persisted caution verdicts | 110 |
| Latest A10 persisted inconclusive verdicts | 16 |

The 16 NULL rows all have `nh01_source='gem_global_v2023'`, `nh01_quality='medium'`, and `pga_475yr_g` between 0.00000 and 0.01008 g. This supports the current policy of treating missing 2475-year PGA as inconclusive rather than inferring an A10 pass from the 475-year fallback.

## NULL And Alias Policy

| Case | Current policy | Accepted rationale |
| --- | --- | --- |
| `pga_2475yr_g` present | Bands and A10 evaluate directly on `pga_2475yr_g`. | This is the normative A10 metric and threshold metadata metric. |
| `pga_2475yr_g` exactly `0.5` | Score 5.5 and A10 pass. | The fail expression is strict greater-than: `> 0.5`. |
| `pga_2475yr_g` NULL | No band matches; scoring returns the pass-mark default with `unscored` note; A10 verdict is `inconclusive`. | NULL means 2475-year PGA is missing, not confirmed safe. |
| Prefixed DB field `nh01_pga_2475yr_g` | Resolver strips the `nh01_` prefix and reads the bare ORM field `pga_2475yr_g`; context contains both names. | Avoids false negatives from spec/ORM naming mismatch. |
| `vs30_ms` in `db_fields.api` | Current ORM has no typed `vs30_ms`; resolver records it as a raw miss. | Non-behavioral for A10 because no band or fail expression uses `vs30_ms`. |

## Source Citations

- `config/scoring_specs/nh_natural_hazards.yaml`: NH-01 phases, metric, db_fields, bands, A10 expression, review flag, and `band_recipe`.
- `config/scoring_rubrics/nh_natural_hazards.yaml`: legacy rubric parity for NH-01 bands and A10 expression.
- `config/scoring_specs/threshold_metadata.yaml`: A10 metric, operator, default/recommended value, units, rationale, sources, and bounds.
- `src/atoms_vs_ashes/criterion_spec/_band_recipes.py`: `lower_is_better` recipe emits the 0.2x, 0.4x, 1.0x, 1.5x, and 2.0x PGA ladder.
- `src/atoms_vs_ashes/criterion_spec/compiler.py`: threshold overrides rebuild fail expressions; recipe-linked bands rebuild from the same pivot.
- `src/atoms_vs_ashes/scoring/merge_resolver.py`: prefixed field fallback and dual context exposure.
- `src/atoms_vs_ashes/scoring/bands.py`: NULL operands do not match numeric bands; no-match result is `unscored`.
- `src/atoms_vs_ashes/scoring/exclusionary.py` and `src/atoms_vs_ashes/scoring/avoidance.py`: avoidance fail evaluations become A-code verdicts and matched A-code fails are promoted to `caution`.
- `src/atoms_vs_ashes/scoring/_codes.py`: A10 catalog synopsis, anchored to `NH-01`.
- `docs/connector_reports/seismic_hazard_s01_sample_report.md`: `pga_2475yr_g` definition and GEM fallback NULL semantics.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NH-01 normative basis and A10 vendor-envelope note.

## Final Status

Accepted-current-state. No behavior-changing issue was found for NH-01 A10. No scoring spec, rubric, threshold metadata, or shared documentation change is required.
