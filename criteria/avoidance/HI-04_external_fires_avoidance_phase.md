<!-- man_hours: 0.7 -->
# HI-04 External fires - avoidance-phase audit

Status: pending-decision.

## Phase And Metric Header

- Criterion: `HI-04` - External fires.
- Configured phases: `[avoidance, ranking]`.
- Primary metric: `nearest_flammable_storage_km`.
- Related local fields: `nearest_pipeline_km`, `hi04_quality`, derived `hi04_search_completed`.
- Current A-code: none. `fail_conditions: []`.
- Current role: participates in the 0-10 weighted ranking composite and is shown as an avoidance/screening-role criterion, but it emits no `avoidance` screening verdicts.

## No-A-Code Decision Matrix

| Question | Local evidence | Decision |
| --- | --- | --- |
| Does HI-04 currently host an active A-code? | No. The HI-04 spec/rubric has `fail_conditions: []`; compiled rubric has `fail_conditions = 0`; `expected_avoidance_codes(HI-04) = []`; local DB has 0 `screening_verdicts` rows for `criterion_id = 'HI-04'`. | Accepted current behavior: no active HI-04 A-code. |
| Is an A-code already assigned to flammable/toxic/explosive storage? | Yes. `A7` is anchored on `HI-02`, both in the code catalog and report appendix, with synopsis/threshold for major-hazard storage. Local DB confirms all `A7` verdict rows are `HI-02` verdicts. | Do not create a duplicate HI-04 A7 alias without a mapping decision. |
| Does the current `avoidance` phase by itself create caution/fail verdicts? | No. The avoidance evaluator only walks `fail_conditions` with `action = 'avoidance_penalty'`. With no HI-04 fail condition, the phase is a role/UI/documentation signal only. | Defensible as documentation-only avoidance phase, subject to pending scoring-band cleanup below. |
| Is there current DB evidence that an HI-04 A-code would change today's site outcomes? | No. In `atoms_vs_ashes_merged`, `min(nearest_flammable_storage_km) = 5.24`; 0 rows are below the HI-04 pass-distance boundary of 4 km, and 0 rows are below an A7-like 5 km distance. | No immediate behavior-changing A-code issue found. |
| Should HI-04 get a new A-code now? | Not from current local evidence. The source requirement says "Screen + Rank", but the active A-code inventory already uses `A7` for major-hazard storage under HI-02. | Recommended no-A-code state unless the project decides to split external-fire storage/pipeline risk from A7. |

## Current Scoring Bands

The current HI-04 bands are:

| Score range | Condition | Meaning |
| --- | --- | --- |
| `[9,10]` | `(nearest_flammable_storage_km is null and hi04_search_completed == true) or nearest_flammable_storage_km > 15` | Completed search found no major flammable storage in radius, or nearest storage is beyond 15 km. |
| `[7,8]` | `nearest_flammable_storage_km >= 8` | 8-15 km. |
| `[5,6]` | `nearest_flammable_storage_km >= 4` | 4-8 km, the ranking pass band. |
| `[3,4]` | `nearest_flammable_storage_km >= 1` | 1-4 km. |
| `[1,2]` | `nearest_flammable_storage_km < 1` | Less than 1 km. |
| `[0,0]` | `nearest_flammable_storage_km < 0.2 and has_mitigation == false` | Intended adjacent-facility severe band. This band is currently unreachable because the broader `< 1 km` band is evaluated first, and `has_mitigation` is not supplied by HI-04 local context. |

Ranking behavior is otherwise coherent: `HI-04` is not exclusionary, so `participates_in_composite` is true; below-pass bands reduce the ranking score but do not create a `caution` or `fail` verdict.

## NULL And Alias Policy

- `nearest_flammable_storage_km is null` is favorable only when `hi04_search_completed == true`.
- `hi04_search_completed` is derived from `hi04_quality`. Completed values are `ok`, `verified`, `high`, `medium`, `low`, `screening`, `screening_default`, and `approximate`.
- `hi04_quality is null`, `no_data`, `failed`, `insufficient`, or `not_applicable` means the search did not complete for scoring purposes. With a null distance, HI-04 becomes unscored and receives the neutral pass-mark default `5.0`.
- `nearest_pipeline_km` is present in schema/spec docs but is not populated in the local merged DB and is not used by the current scoring bands.
- No local alias maps another field into `nearest_flammable_storage_km` or `nearest_pipeline_km`.
- `has_mitigation` is not a HI-04 DB field, schema column, documented alias, or derived context name. It should not be treated as available unless a future connector or derivation explicitly supplies it.

## Local DB Evidence

Read-only DB profile: `atoms_vs_ashes_merged`.

Counts from `site_human_hazards`:

| Measure | Count |
| --- | ---: |
| Total HI rows | 361 |
| `nearest_flammable_storage_km is null` | 346 |
| `hi04_quality is null` | 0 |
| Search-completed quality values | 314 |
| Populated flammable-storage distances | 15 |
| Populated `nearest_pipeline_km` | 0 |
| Rows below 4 km HI-04 pass-distance boundary | 0 |
| Rows below 5 km A7-like storage boundary | 0 |

Expected band distribution from local fields:

| Expected band | Count |
| --- | ---: |
| `[9,10]` from null distance plus completed search | 299 |
| `[9,10]` from distance greater than 15 km | 9 |
| `[7,8]` | 2 |
| `[5,6]` | 4 |
| Unscored/null-not-completed | 47 |

Latest persisted ranking examples from run `score-d51c7c6b`:

| Site | Country | Flammable storage km | `hi04_quality` | Score | Evidence |
| --- | --- | ---: | --- | ---: | --- |
| Duernrohr power station | AT | null | high | 9.5 | Completed search, no storage found in radius. |
| Bedzin power station | PL | 25.66 | high | 9.5 | Distance greater than 15 km. |
| Jaworzno power station | PL | 14.85 | high | 7.5 | 8-15 km band. |
| Ruse Iztok power station | BG | 5.24 | high | 5.5 | 4-8 km pass band. |
| Porto Romano Power Station | AL | null | not_applicable | 5.0 | Search not completed for scoring; unscored pass-mark default. |

Synthetic local scoring probe:

| Context | Current result | Meaning |
| --- | --- | --- |
| `nearest_flammable_storage_km = 0.1`, `has_mitigation = false` | `[1,2]`, score 1.5 | The intended `[0,0]` adjacent/no-mitigation band is shadowed. |
| `nearest_flammable_storage_km = 0.1`, no `has_mitigation` | `[1,2]`, score 1.5 | Same result with production-shaped context. |
| `nearest_flammable_storage_km = null`, `hi04_search_completed = true` | `[9,10]`, score 9.5 | Sentinel favorable branch works. |
| `nearest_flammable_storage_km = null`, `hi04_search_completed = false` | Unscored, score 5.0 | Null without completed search is not treated as favorable evidence. |

## Transition Note

HI-04's `avoidance` phase appears to be an intentional screen/documentation role rather than a missing A-code host. The current hard-screen inventory already assigns major-hazard storage to `A7` under `HI-02`; adding an HI-04 A-code would either duplicate A7, require an A7 split/alias decision, or create a new A-code outside the current A1-A16 inventory.

No scoring spec or rubric change was made in this sweep. If the project wants active external-fire screening later, it should first decide whether to:

| Option | Change | Consequence |
| --- | --- | --- |
| Keep current A-code mapping | Leave `fail_conditions: []` on HI-04. | HI-04 remains ranking plus documentation-only avoidance phase; A7 remains under HI-02. |
| Split A7 semantics | Keep A7 under HI-02 for Seveso/IED storage and define a separate HI-04 storage/pipeline threshold as a new or remapped code. | Requires catalog, appendix, threshold metadata, spec, tests, and report updates. |
| Add HI-04 as an A7 alias | Emit A7 from both HI-02 and HI-04. | Risks duplicate caution rows and ambiguous ownership unless verdict uniqueness/reporting rules are redesigned. |

## Pending Decisions

1. Decide whether to reorder or rewrite the `[0,0]` severe band. Exact issue: the evaluator uses first matching band order, so `nearest_flammable_storage_km < 1` shadows `nearest_flammable_storage_km < 0.2 and has_mitigation == false`. Also, `has_mitigation` is absent from local context.
2. Decide whether `nearest_pipeline_km` should remain documented but inactive, be removed from the HI-04 metric language, or receive a connector/derivation before pipeline proximity affects scoring.
3. Decide whether future external-fire hard screening should stay covered by HI-02/A7 or receive its own A-code. Current local evidence supports no immediate A-code addition.

## Source Citations

- `config/scoring_specs/hi_human_induced.yaml` and `config/scoring_rubrics/hi_human_induced.yaml`: HI-04 phases, fields, bands, and empty `fail_conditions`.
- `config/scoring_specs/threshold_metadata.yaml`: no HI-04 threshold entry; A-code threshold metadata starts with currently active fail-condition codes.
- `src/atoms_vs_ashes/scoring/_codes.py`: `A7` is anchored to `HI-02`; no HI-04 avoidance code exists in the catalog.
- `src/atoms_vs_ashes/scoring/avoidance.py`: avoidance verdicts are emitted only for `action = 'avoidance_penalty'` fail conditions.
- `src/atoms_vs_ashes/scoring/rubric.py`: `HI-04` is both avoidance-role and ranking; because it is not exclusionary, it participates in the composite.
- `src/atoms_vs_ashes/scoring/bands.py`: bands are evaluated first-match; no-band matches return unscored pass-mark default.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`: `hi04_search_completed` is derived from `hi04_quality` and controls favorable null semantics.
- `src/atoms_vs_ashes/db/models.py`: `nearest_flammable_storage_km`, `nearest_pipeline_km`, and `hi04_quality` exist on `site_human_hazards`; `has_mitigation` does not.
- `src/atoms_vs_ashes/connectors/eea_industrial/batch.py`: EEA industrial results populate HI-04 flammable-storage quality and comments.
- `tests/scoring/test_search_sentinel_bands.py` and `tests/scoring/test_safe_eval_disjuncts.py`: sentinel favorable branch and null/error disjunct behavior are regression-tested.
- `tests/gui/test_threshold_editor_palette.py`: HI-04 is intentionally displayed as avoidance-role from the source-of-truth phases.
- `report/sites_evaluation/04_criteria_human_induced.md`, `report/requirements/05_siting_criteria.md`, and `docs/expert_siting_criteria_evaluation_matrix.md`: HI-04 is documented as Screen + Rank / avoidance-suitability and uses the flammable-storage/pipeline metric language.
- `report/sites_evaluation/10_appendices.md`: A7 maps to HI-02 major-hazard storage, not HI-04.
- Local DB queries run on `atoms_vs_ashes_merged` during this audit.

## Final Status

No active HI-04 A-code is recommended from current local evidence. The criterion's no-A-code state is defensible as documentation-only avoidance phase usage because A7 is already owned by HI-02 and HI-04 still ranks external-fire distance in the composite.

The documentation remains pending-decision because the `[0,0]` HI-04 severe band is unreachable and the pipeline metric is documented but not populated or scored. These issues did not change current local DB outcomes, but they should be resolved before treating HI-04's low-end ranking ladder as fully accepted.
