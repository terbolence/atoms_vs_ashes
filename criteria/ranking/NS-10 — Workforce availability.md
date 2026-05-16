<!-- man_hours: 0.4 -->
# NS-10 — Workforce availability

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-10 — Workforce availability |
| Phases | `[ranking]` |
| Primary metric in spec | `workforce_tier` |
| Locally sourced fields found | `ns10_quality` and `ns10_comment`; no sourced `workforce_tier` found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 4; normalised 1.4% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `workforce_tier` sourced into scoring? | No local source, schema column, context field, persist mapping, or derivation was found for `workforce_tier`. | Final state is deferred/unscored until a tier source or measured proxy derivation exists. |
| Is there related evidence? | Eurostat projection code writes `ns10_quality` and `ns10_comment`; the LLM schema exposes `workforce_notes`. | Candidate Stage 3 evidence, not a current scoring tier. |
| Is current scoring meaningful? | PL feedback bundle rows are 5.0 unscored; coverage shows only 44.63% for quality/comment. | Do not interpret current defaults as measured workforce availability. |
| Is there an exclusion/avoidance relationship? | None. NS-10 is rank-only with `fail_conditions: []`. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `workforce_tier == 'excellent'` |
| 7-8 | `workforce_tier == 'strong_industrial'` |
| 5-6 | `workforce_tier == 'adequate'` |
| 3-4 | `workforce_tier == 'tight'` |
| 1-2 | `workforce_tier == 'severe_bottleneck'` |

No band recipe is declared. Without `workforce_tier`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The report chapter says NS-10 uses qualitative tiers and notes Eurostat fill around 45%. The current source path seen locally carries commentary/quality, not a categorical tier. The LLM schema has `workforce_notes`, and context exposes `ns10_quality` and `ns10_comment`.

`coverage_latest.md` reports NS-10 at 44.63% coverage for `ns10_quality` and `ns10_comment`. PL bundle examples show `score_0_10 = 5.0`, `quality_flag = unscored`, `confidence = medium`, and no raw misses because no data source is attached to the tier field.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 NS-10 rows; mean/min/max all 5.0. |
| PL feedback bundle row | `no_band_matched — pass-mark default (unscored)`, `quality = medium`, no raw misses. |
| Coverage report | 44.63% for `ns10_quality` and `ns10_comment`; no `workforce_tier` field listed. |

## Specialist Recommendation

Keep NS-10 as a rank-only criterion, but document it as deferred/unscored until workforce availability is represented by a sourced `workforce_tier` or measured proxy fields. Current quality/comment evidence can support narrative caveats, but it does not provide the categorical scoring value expected by the YAML bands.

Do not rewrite the bands around unspecific comment fields. Stage 3 characterization should confirm industrial labour depth, specialist training pathways, housing and mobility constraints, and nuclear-relevant skill availability before assigning a tier.

## Final State

NS-10 remains in the scoring spec as the target workforce taxonomy, but current rows are unmeasured at this stage. The 5.0 default is an unscored placeholder and should not be described as adequate workforce supply. No YAML edit is made because a safe scoring change requires a populated `workforce_tier`, explicit measured workforce proxies, or a schema/connector update.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-10 primary metric, bands, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-10 rank-only rationale.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing workforce tiers.
- `src/atoms_vs_ashes/connectors/eurostat_projections/batch.py`: writes NS-10 quality/comment proxy evidence.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: no sourced `workforce_tier`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: NS-10 coverage line.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
