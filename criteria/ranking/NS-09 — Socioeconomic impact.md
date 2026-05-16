<!-- man_hours: 0.4 -->
# NS-09 — Socioeconomic impact

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-09 — Socioeconomic impact |
| Phases | `[ranking]` |
| Primary metric in spec | `socio_tier` |
| Supporting fields in spec | `site_socioeconomic.unemployment_pct`, `site_socioeconomic.gdp_per_capita_eur`; LLM `ns09_socioeconomic_text` |
| Locally sourced fields found | `ns09_quality` and `ns09_comment`; no sourced `socio_tier` found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 5; normalised 1.8% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `socio_tier` sourced into scoring? | No local source, schema column, context field, persist mapping, or derivation was found for `socio_tier`. | Final state is deferred/unscored until a tier source or measured proxy derivation exists. |
| Are the socioeconomic numeric fields present in the infrastructure context? | No. Context only lists `ns09_quality` and `ns09_comment`; `unemployment_pct` and `gdp_per_capita_eur` are listed in the spec under `site_socioeconomic`. | Do not rewrite bands around unavailable numeric fields in this pass. |
| Is current scoring meaningful? | PL feedback bundle rows are pass-mark default 5.0 with `quality_flag = unscored`; coverage shows only 44.63% for quality/comment. | Do not interpret current defaults as measured socioeconomic alignment. |
| Is there an exclusion/avoidance relationship? | None. NS-09 is rank-only with `fail_conditions: []`. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `socio_tier == 'strong_alignment'` |
| 7-8 | `socio_tier == 'net_positive'` |
| 5-6 | `socio_tier == 'neutral'` |
| 3-4 | `socio_tier == 'mixed'` |
| 1-2 | `socio_tier == 'opposition'` |

No band recipe is declared. Without `socio_tier`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The report chapter frames NS-09 as qualitative tiers anchored on Eurostat NUTS-2 indicators plus LLM evidence. The current DB model section inspected for `SiteInfrastructureV2` contains only `ns09_quality` and `ns09_comment` for NS-09. The Eurostat projections batch writes those comment/quality fields, not a scoring tier.

`coverage_latest.md` reports NS-09 at 44.63% coverage for `ns09_quality` and `ns09_comment`. Local PL bundle rows show raw misses for `site_socioeconomic.unemployment_pct` and `site_socioeconomic.gdp_per_capita_eur` and remain unscored at 5.0.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 NS-09 rows; mean/min/max all 5.0. |
| PL feedback bundle row | `no_band_matched — pass-mark default (unscored)`, `quality = medium`, raw misses for `site_socioeconomic.unemployment_pct` and `gdp_per_capita_eur`. |
| Coverage report | 44.63% for `ns09_quality` and `ns09_comment`; no tier field listed. |

## Specialist Recommendation

Keep NS-09 as a rank-only criterion, but document it as deferred/unscored until the project has a sourced `socio_tier` or a traceable local derivation from measured socioeconomic fields. The available quality/comment fields are evidence notes, not measured scoring values, and the spec-listed unemployment and GDP fields are not locally available in the current scoring context.

Do not create a numeric scoring ladder from absent fields. Stage 3 characterization should establish the socioeconomic baseline, labour-market and regional-development evidence, and stakeholder context before a tier is populated or derived.

## Final State

NS-09 remains in the scoring spec as the target socioeconomic taxonomy, but current screening rows are unmeasured at this stage. The 5.0 pass-mark default is an unscored placeholder and should not be described as neutral, net positive, or mixed socioeconomic impact. No YAML edit is made because the safe implementation requires a populated `socio_tier`, measured proxy fields, or a schema/connector update.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-09 primary metric, bands, DB fields, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-09 rank-only rationale.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing tiers and data anchors.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: no sourced `socio_tier`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: NS-09 coverage line.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
