<!-- man_hours: 0.4 -->
# NS-12 — Regulatory / political environment

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-12 — Regulatory / political environment |
| Phases | `[ranking]` |
| Primary metric in spec | `policy_tier` |
| Locally sourced fields found | `ns12_quality` and `ns12_comment`; no sourced `policy_tier` found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 6; normalised 2.1% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `policy_tier` sourced into scoring? | No local source, schema column, context field, persist mapping, or derivation was found for `policy_tier`. | Final state is deferred/unscored until a curated tier source or measured policy proxy exists. |
| Is there related policy evidence? | Eurostat projections batch writes `ns12_quality = low` and `ns12_comment` from `policy_proxy`; LLM schema exposes `regulatory_notes`. | Candidate narrative evidence, not a current scoring tier. |
| Is current scoring meaningful? | Coverage shows 100% comment/quality coverage, but PL bundle rows are still 5.0 unscored because no tier is present. | Do not interpret current defaults as measured policy feasibility. |
| Is there an exclusion/avoidance relationship? | None. NS-12 is rank-only with `fail_conditions: []`; it must not override safety exclusions. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `policy_tier == 'strong_enabling'` |
| 7-8 | `policy_tier == 'clear_support'` |
| 5-6 | `policy_tier == 'feasible'` |
| 3-4 | `policy_tier == 'uncertain'` |
| 1-2 | `policy_tier == 'hostile'` |

No band recipe is declared. Without `policy_tier`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The report chapter describes a country-level lookup table curated from Eurostat metadata, IAEA PRIS, and national policy documents. The local implementation evidence found comment/quality fields and a low-confidence policy proxy, but not a categorical `policy_tier` that can match the YAML bands.

`coverage_latest.md` reports NS-12 at 100% for `ns12_quality` and `ns12_comment`; that is evidence coverage, not scoring-tier coverage. PL bundle rows show `score_0_10 = 5.0`, `quality_flag = unscored`, `confidence = low`, and no raw misses because the missing tier is not wired as a data source.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 NS-12 rows; mean/min/max all 5.0. |
| PL feedback bundle row | `no_band_matched — pass-mark default (unscored)`, `quality = low`, no raw misses. |
| Coverage report | 100% for `ns12_quality` and `ns12_comment`, but no `policy_tier` field listed. |

## Specialist Recommendation

Keep NS-12 as a rank-only criterion, but document it as deferred/unscored until a curated `policy_tier` or traceable country-level policy proxy is available. The current quality/comment coverage is not equivalent to a measured regulatory or political ranking value, and the screening report must not imply licensing readiness or policy approval from a default score.

Do not rewrite bands around low-confidence comment fields. Stage 3 characterization should confirm the applicable national regulatory pathway, consenting schedule risks, and programme-level policy assumptions before assigning a tier.

## Final State

NS-12 remains in the scoring spec as the target regulatory/political taxonomy, but current rows are unmeasured at this stage for scoring purposes. The 5.0 default is an unscored placeholder and should not be described as feasible policy support. No YAML edit is made because a safe scoring change requires a sourced `policy_tier`, curated policy lookup, or schema/connector update.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-12 primary metric, bands, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-12 rank-only rationale.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing policy tiers.
- `src/atoms_vs_ashes/connectors/eurostat_projections/batch.py`: writes NS-12 policy proxy comments.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: no sourced `policy_tier`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: NS-12 coverage line.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
