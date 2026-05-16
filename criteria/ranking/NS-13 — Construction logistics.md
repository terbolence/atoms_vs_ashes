<!-- man_hours: 0.4 -->
# NS-13 — Construction logistics

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-13 — Construction logistics |
| Phases | `[ranking]` |
| Primary metric in spec | `logistics_tier` |
| Locally sourced fields found | `laydown_suitable_ha`, `laydown_largest_patch_ha`, `ns13_quality`, and `ns13_comment`; no sourced `logistics_tier` found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 4; normalised 1.4% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `logistics_tier` sourced into scoring? | No local source, schema column, context field, persist mapping, or derivation was found for `logistics_tier`. | Final state is deferred/unscored until a tier source or measured laydown derivation exists. |
| Are related laydown metrics sourced? | Yes, schema/context/persist include `laydown_suitable_ha` and `laydown_largest_patch_ha`; coverage currently reports them at 0.0%. | Candidate future inputs, but not scoreable while coverage is 0.0%. |
| Is current scoring meaningful? | PL feedback bundle rows are all 5.0 unscored; coverage shows 0.0% for laydown and NS-13 fields. | Do not interpret current defaults as measured construction logistics. |
| Is there an exclusion/avoidance relationship? | None. NS-13 is rank-only with `fail_conditions: []`. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `logistics_tier == 'excellent'` |
| 7-8 | `logistics_tier == 'generous'` |
| 5-6 | `logistics_tier == 'workable'` |
| 3-4 | `logistics_tier == 'tight'` |
| 1-2 | `logistics_tier == 'severe'` |

No band recipe is declared. Without `logistics_tier`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The report chapter says NS-13 should derive from NS-04, NS-05, NS-03, and LLM construction evidence. The local schema and analysis code expose laydown hectare metrics, and `analysis/laydown_area.py` writes `laydown_suitable_ha`, `laydown_largest_patch_ha`, `ns13_quality`, and `ns13_comment`. The scoring spec currently does not score those numeric fields directly.

`coverage_latest.md` reports 0.0% coverage for `laydown_suitable_ha`, `laydown_largest_patch_ha`, `ns13_quality`, and `ns13_comment`. PL bundle examples show `score_0_10 = 5.0`, `quality_flag = unscored`, `confidence = insufficient`.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 NS-13 rows; mean/min/max all 5.0. |
| PL feedback bundle row | `no_band_matched — pass-mark default (unscored)`, `quality = null`, no raw misses. |
| Coverage report | 0.0% for laydown and NS-13 quality/comment fields. |

## Specialist Recommendation

Keep NS-13 as a rank-only criterion, but document it as deferred/unscored until laydown and logistics evidence is populated. The local schema has plausible laydown fields, yet coverage is 0.0%, so rewriting bands around those fields would create scoring structure without measured screening evidence.

Stage 3 characterization should measure usable laydown area, largest patch, abnormal-load route constraints, grading interfaces, and construction-traffic management constraints before assigning `logistics_tier` or a traceable numeric replacement.

## Final State

NS-13 remains in the scoring spec as the target construction-logistics taxonomy, but current rows are unmeasured at this stage. The 5.0 default is an unscored placeholder and should not be described as workable logistics. No YAML edit is made because a safe scoring change requires populated laydown metrics, a sourced `logistics_tier`, or a schema/connector update.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-13 primary metric, bands, and quality floor.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-13 rank-only rationale and links to NS-01/NS-03/NS-05.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing logistics tiers.
- `src/atoms_vs_ashes/analysis/laydown_area.py`: writes laydown metrics and NS-13 quality/comment.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: laydown fields exist; no sourced `logistics_tier`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: NS-13 coverage line.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
