<!-- man_hours: 0.4 -->
# NS-06 — Existing infrastructure reuse

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-06 — Existing infrastructure reuse |
| Phases | `[ranking]` |
| Primary metric in spec | `reuse_tier` |
| Locally sourced metric | `reusable_infra_score` exists in schema/context/persist mapping; `reuse_tier` was not found as a sourced field |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but unscored rows are excluded from weighted composite contribution by quality/confidence filtering |
| Weight | factor 5; normalised 1.8% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `reuse_tier` sourced into scoring? | No local source, schema column, context field, persist mapping, or derivation was found for `reuse_tier`. | Do not treat current 5.0 defaults as measured ranking evidence. |
| Is there a related source field? | Yes. `reusable_infra_score` exists on `SiteInfrastructureV2`, in LLM schema, context, and persist mapping. | Candidate future derivation input, but not scoreable while coverage is 0.0%. |
| Is current scoring meaningful? | Coverage report shows NS-06 at 0.0%; PL bundle examples show pass-mark default 5.0 with `quality_flag = unscored`. | Final state is deferred/unscored pending Stage 3 characterization or a populated source field. |
| Is there an avoidance/soft-flag relationship? | None. NS-06 is rank-only with `fail_conditions: []`. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `reuse_tier == 'strong'` |
| 7-8 | `reuse_tier == 'solid'` |
| 5-6 | `reuse_tier == 'moderate'` |
| 3-4 | `reuse_tier == 'limited'` |
| 1-2 | `reuse_tier == 'contaminated'` |

No band recipe is declared. With no sourced `reuse_tier`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The DB model has `reusable_infra_score`, `ns06_quality`, and `ns06_comment`, plus Earth Engine support fields such as `ns06_gee_built_fraction` and `ns06_gee_demolition_class`. The report chapter says GEE-based coverage is currently disabled and LLM is the primary signal, but the current scoring spec does not score `reusable_infra_score`; it scores `reuse_tier`.

`coverage_latest.md` reports `reusable_infra_score`, `ns06_quality`, and `ns06_comment` at 0.0% coverage. Local PL bundle rows show NS-06 at `score_0_10 = 5.0`, `quality_flag = unscored`, `confidence = insufficient`.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle NS-06 rows | Mean/min/max all 5.0 across 63 PL sites; individual rows are `no_band_matched — pass-mark default (unscored)`. |
| Coverage report | 0.0% for `reusable_infra_score`, `ns06_quality`, and `ns06_comment`. |

## Specialist Recommendation

Do not replace `reuse_tier` with `reusable_infra_score` in YAML during this pass. The related numeric field exists locally, but the documented coverage is 0.0%, so any direct scoring ladder would create an apparent measured ranking signal where the screening record does not yet contain measured reuse evidence.

Keep NS-06 as a rank-only criterion with a deferred/unscored final state until reusable-infrastructure evidence is populated or a local derivation is implemented. Stage 3 characterization should identify which civil, grid, cooling, buildings, demolition, and contamination attributes are reusable and then either populate `reuse_tier` or define a traceable derivation from measured fields.

## Final State

NS-06 remains in the scoring spec as the target ranking taxonomy, but the accepted screening-stage interpretation is that current rows are unmeasured at this stage. The pass-mark default is a scoring-engine placeholder with `quality_flag = unscored`; it should not be reported as a neutral reuse assessment or as evidence that infrastructure reuse is moderate. No YAML edit is made because a safe scoring change requires populated reuse evidence or a schema/derivation update outside this worker's scope.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-06 phase, `reuse_tier` primary metric, and categorical bands.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-06 rank-only rationale and NS-11 overlap note.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing reuse tiers and disabled GEE note.
- `src/atoms_vs_ashes/db/models.py`: `reusable_infra_score`, `ns06_quality`, and `ns06_comment`.
- `src/atoms_vs_ashes/llm/schemas.py`, `persist.py`, and `context.py`: source path for `reusable_infra_score`, not `reuse_tier`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: 0.0% NS-06 coverage.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
