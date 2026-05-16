<!-- man_hours: 0.4 -->
# NS-11 — Coal-to-nuclear synergies

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-11 — Coal-to-nuclear synergies |
| Phases | `[ranking]` |
| Primary metric in spec | `ns11_synergy_index` |
| Locally sourced fields found | `ns11_quality` and `ns11_comment`; no `ns11_synergy_index` model column or derivation was found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 6; normalised 2.1% |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Is `ns11_synergy_index` sourced into scoring? | No local model column, context field, persist mapping, or derivation was found. | Final state is deferred/unscored until a synergy index or measured component derivation exists. |
| Is NS-11 conceptually distinct from NS-06? | Yes. NS-06 is asset reuse; NS-11 is broader coal-to-nuclear conversion synergy and should avoid double counting. | Keep separate, but define the metric. |
| Is current scoring meaningful? | PL feedback bundle rows are all 5.0 unscored; coverage report shows 0.0% for NS-11 quality/comment. | Do not interpret current defaults as measured coal-to-nuclear synergy. |
| Is there an exclusion/avoidance relationship? | None. NS-11 is rank-only with `fail_conditions: []`. | Accept current phase relationship. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `ns11_synergy_index == 'exceptional'` |
| 7-8 | `ns11_synergy_index == 'strong'` |
| 5-6 | `ns11_synergy_index == 'balanced'` |
| 3-4 | `ns11_synergy_index == 'modest'` |
| 1-2 | `ns11_synergy_index == 'minimal'` |

No band recipe is declared. Without `ns11_synergy_index`, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The report chapter describes NS-11 as a composite of NS-02, NS-03, NS-06, and ash-management evidence. The current DB model section inspected for NS-11 contains only `ns11_quality` and `ns11_comment`; `ns11_synergy_index` is referenced by the spec but not persisted.

`coverage_latest.md` reports NS-11 at 0.0% coverage. Local bundle examples show raw misses for `site_infrastructure_v2.ns11_synergy_index` and pass-mark default 5.0.

## Examples

| Example | Current behavior |
| --- | --- |
| PL feedback bundle summary | 63 NS-11 rows; mean/min/max all 5.0. |
| PL feedback bundle row | `no_band_matched — pass-mark default (unscored)`, raw miss `site_infrastructure_v2.ns11_synergy_index`. |
| Coverage report | 0.0% for `ns11_quality` and `ns11_comment`; no synergy index field listed. |

## Specialist Recommendation

Keep NS-11 as a distinct rank-only criterion, but document it as deferred/unscored until the project has a sourced `ns11_synergy_index` or a traceable component derivation. The criterion should not be scored by simply restating NS-02, NS-03, or NS-06, because that would double count grid, transport, and asset-reuse evidence without measuring the broader conversion synergy.

Stage 3 characterization should quantify the brownfield conversion case after grid, transport, reusable infrastructure, remediation, ash-management, and site-integration evidence are measured. Only then should a synergy tier or component score be populated.

## Final State

NS-11 remains in the scoring spec as the target coal-to-nuclear synergy taxonomy, but current rows are unmeasured at this stage. The 5.0 default is an unscored placeholder and should not be described as balanced synergy. No YAML edit is made because the safe implementation requires a populated `ns11_synergy_index`, explicit measured components, or a schema/connector update.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-11 primary metric, DB field declaration, and bands.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-11 rank-only rationale and NS-06 overlap caution.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing synergy tiers.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: no sourced `ns11_synergy_index`.
- `report/version 1.01/requirements/coverage_reports/coverage_latest.md`: NS-11 coverage line.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
