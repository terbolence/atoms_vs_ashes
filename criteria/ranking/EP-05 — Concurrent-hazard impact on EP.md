<!-- man_hours: 0.3 -->
# EP-05 - Concurrent-hazard impact on EP - ranking state

Status: **FINAL RECOMMENDATION IMPLEMENTED**. `ep05_concurrent_index` remains unmeasured at this stage. The current runtime state is documented as a screening-stage data gap and routed to Stage 3 characterization or a later schema/derivation improvement.

Phase: `[ranking]`  
Primary metric: `ep05_concurrent_index`  
Source spec/rubric: `config/scoring_specs/ep_emergency_planning.yaml`; `config/scoring_rubrics/ep_emergency_planning.yaml`  
Composite participation: **true**

## Decision Matrix

| Element | Current state |
| --- | --- |
| Ranking bands | Accepted as current runtime documentation only. The categorical ladder is coherent but cannot fire without `ep05_concurrent_index`. |
| Available local field | `concurrent_hazard_notes` exists on `site_emergency_planning`; 0/361 local merged rows had notes in this recompute. |
| Runtime evidence | 361/361 rows are unscored with raw miss `site_emergency.ep05_concurrent_index`. |
| Cross-phase relationship | None. EP-05 has no fail conditions; it is ranking-only. |

## Current Runtime Bands

| Score | Runtime condition | Merged DB count |
| ---: | --- | ---: |
| 9-10 | `ep05_concurrent_index == 'none'` | 0 |
| 7-8 | `ep05_concurrent_index == 'weak'` | 0 |
| 5-6 | `ep05_concurrent_index == 'manageable'` | 0 |
| 3-4 | `ep05_concurrent_index == 'multiple'` | 0 |
| 1-2 | `ep05_concurrent_index == 'severe'` | 0 |
| Unscored | No band matched because index is absent | 361 |

## Metric Truth And Data Quality

`site_emergency_planning` currently stores `concurrent_hazard_notes`, `ep05_quality`, and `ep05_comment`. The LLM prompt/persistence path references `concurrent_hazard_notes`; the scoring YAML references `ep05_concurrent_index`. No local derived context name or alias currently bridges notes into the categorical index.

Current NULL behavior is neutral pass-mark default (`5.0`, unscored). That is the appropriate screening-stage treatment while the concurrent-hazard index is absent; it should not be interpreted as evidence that concurrent hazards are absent.

## Scored Examples

No local scored examples are available. Representative unscored rows include Porto Romano Power Station (AL) and Duernrohr power station (AT): both have `ep05_concurrent_index = null` and score `5.0` with `unscored`.

## Specialist recommendation

Retain the current YAML for this worker and treat EP-05 as unmeasured at this stage. The available local field is `concurrent_hazard_notes`, and the local recompute found 0/361 rows with notes; there is no measured categorical `ep05_concurrent_index` or deterministic derivation to support assigning one.

Stage 3 characterization should build the concurrent-hazard index from site-specific EP, natural-hazard, and human-induced-hazard interactions. If the project wants EP-05 to score before Stage 3, the safer deferred implementation is a documented schema or resolver derivation that persists `ep05_concurrent_index` before changing band behavior.

## Final state

No YAML change is implemented. EP-05 remains in the composite as a ranking criterion, but local rows with missing concurrent-hazard index evidence stay at the neutral unscored runtime state (`5.0`, `unscored`). This is a screening-stage limitation, not an indication that concurrent-hazard EP interactions are negligible.

## Sources And Validation

Sources: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `src/atoms_vs_ashes/db/models.py`, `src/atoms_vs_ashes/llm/persist.py`, `src/atoms_vs_ashes/llm/context.py`, `src/atoms_vs_ashes/scoring/merge_resolver.py`.

Validation: local-only documentation review against the specialist prompt, scoring spec, scoring rubric, and current criterion evidence. No live API, enrichment, web, code, tests, or YAML changes.
