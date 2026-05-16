<!-- man_hours: 0.4 -->
# NS-07 — Environmental impact (non-radiological)

Status: **FINAL RECOMMENDATION IMPLEMENTED** for the ranking documentation. Cross-reference: `criteria/avoidance/NS-07_environmental_impact_avoidance_phase.md`.

## Header

| Field | Current state |
| --- | --- |
| Criterion | NS-07 — Environmental impact (non-radiological) |
| Phases | `[avoidance, ranking]` |
| Primary metric in spec | `env_impact_tier` |
| Locally sourced field | `env_impact_notes`; no sourced `env_impact_tier` was found |
| Source spec / rubric | `config/scoring_specs/ns_non_safety.yaml`; `config/scoring_rubrics/ns_non_safety.yaml` |
| Composite participation | `true` in the compiled criterion, but current rows are unscored defaults |
| Weight | factor 5; normalised 1.8% |
| Related screen | No A-code or fail condition currently defined |

## Decision Matrix

| Question | Current state | Finding |
| --- | --- | --- |
| Does NS-07 currently define an avoidance A-code? | No. `fail_conditions: []` and no threshold sidecar entry. | Accept current no-A-code state unless project scope changes. |
| Is `env_impact_tier` sourced into scoring? | No. Schema/context/persist expose `env_impact_notes`, `ns07_quality`, and `ns07_comment`, not `env_impact_tier`. | Final state is deferred/unscored until a tier source or derivation exists. |
| Is current scoring meaningful? | Avoidance audit found all local DB NS-07 ranking rows at 5.0 unscored. | Do not interpret current defaults as measured environmental-impact evidence. |
| Does NS-07 duplicate NS-01/NS-08? | Adjacent but distinct. NS-01 handles cooling stress; NS-08 handles protected-area ecology; NS-07 is broader EIA complexity. | Keep separate if the tier source is fixed. |

## Current Score Bands

| Score | Current spec condition |
| ---: | --- |
| 9-10 | `env_impact_tier == 'industrial'` |
| 7-8 | `env_impact_tier == 'few_sensitivities'` |
| 5-6 | `env_impact_tier == 'typical'` |
| 3-4 | `env_impact_tier == 'significant'` |
| 1-2 | `env_impact_tier == 'showstopper_risk'` |

No band recipe is declared. Without a sourced tier, rows fall through to the pass-mark default and are marked unscored.

## Metric Truth And Data Quality

The DB model contains `env_impact_notes`, `ns07_quality`, and `ns07_comment`. The LLM schema exposes `env_impact_notes`; persist and context mapping also reference the notes field. No local alias or derived value converts notes into `env_impact_tier`.

The avoidance audit found 361 infrastructure rows with `env_impact_notes`, `ns07_quality`, and `ns07_comment` all NULL, and 22,937 NS-07 ranking rows at `score_0_10 = 5.0`, `quality_flag = unscored`, `confidence = insufficient`.

## Examples

| Example | Current behavior |
| --- | --- |
| Mugla power station, TR | Default 5.0 unscored in audited ranking rows. |
| Trbovlje power station, SI | Default 5.0 unscored. |
| Kolubara A power station, RS | Default 5.0 unscored. |
| St Andrae power station, AT | Default 5.0 unscored. |

## Specialist Recommendation

Keep NS-07 as a separate rank-only environmental-complexity criterion with no active A-code in this pass. The screening record does not currently contain a sourced `env_impact_tier`, and free-text notes cannot be converted into scoring bands without a schema or derivation decision.

The final recommendation is to document NS-07 as deferred/unscored at the screening stage and route the evidence gap to Stage 3 environmental characterization. Stage 3 should establish the non-radiological EIA constraints that are not already captured by NS-01 cooling stress or NS-08 protected-area ecology, then populate `env_impact_tier` or a traceable replacement metric.

## Final State

NS-07 remains in the scoring spec as the target ranking taxonomy, but current rows are unmeasured at this stage. The default 5.0 score is an unscored placeholder, not evidence of typical conversion challenge or standard EIA feasibility. No YAML edit is made because defining a new A-code or deriving tiers from text would be behavior-changing and requires connector/schema work outside this ranking-documentation implementation.

## Source Citations

- `config/scoring_specs/ns_non_safety.yaml`: NS-07 phases, primary metric, empty fail conditions, and bands.
- `config/scoring_rubrics/ns_non_safety.yaml`: legacy rubric mirror.
- `docs/expert_siting_criteria_evaluation_matrix.md`: NS-07 screen-plus-rank narrative and no A-code mapping.
- `report/version 1.01/sites_evaluation/07_criteria_non_safety.md`: report-facing EIA complexity bands.
- `src/atoms_vs_ashes/db/models.py`, `llm/schemas.py`, `llm/persist.py`, and `llm/context.py`: notes field exists; tier field does not.
- `criteria/avoidance/NS-07_environmental_impact_avoidance_phase.md`: local DB evidence and pending decision matrix.

## Artifact Footer

Documentation-only final recommendation. No scoring specs, rubrics, code, audit logs, or man-hours registry entries were changed.
