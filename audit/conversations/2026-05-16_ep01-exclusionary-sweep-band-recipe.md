<!-- man_hours: 0.6 -->
# 2026-05-16 — EP-01 exclusionary sweep + `band_recipe` consolidation

## Scope

Run the §O pre-edit analysis for **EP-01 — Emergency-plan feasibility (composite)** under the exclusionary sweep plan (`~/.cursor/plans/exclusionary_sweep_13877396.plan.md`), apply the resulting D1-D7 decisions, and resolve the side-quest discovery that the EP-01 hand-written bands were being silently overridden by the recipe.

## Inputs

- Plan: `~/.cursor/plans/exclusionary_sweep_13877396.plan.md`
- System prompt: `prompts/ScoringCriteriaSystemPrompt.md`
- Spec + rubric: `config/scoring_specs/ep_emergency_planning.yaml`, `config/scoring_rubrics/ep_emergency_planning.yaml`, `config/scoring_specs/threshold_metadata.yaml`
- Engine code paths: `criterion_spec/compiler.py`, `criterion_spec/_excl_from_pivot.py`, `scoring/bands.py`, `scoring/_safety_floor.py`, `scoring/exclusionary.py`, `scoring/merge_resolver.py`, `scoring/merge_context_derivations.py`
- DB schema: `src/atoms_vs_ashes/db/models.py::SiteEmergencyPlanning`
- Audit anchors: `audit/post_processing/scoring_conformity/ep01_direction_decision.md`, `report/methodology/exclusionary_floors.md`
- Feedback docs: `report/output/feedback/plans/SP-D_band_proposals/EP-01.md`, `report/output/feedback/plans/SP-D_data_sanity/EP-01.md`

## §O pre-edit analysis — key findings

1. **Trauma-centre + hospital clauses were dead code.** `nearest_trauma_center_km` and `nearest_hospital_km` were referenced by E8's compound expression and the `hospital_overlay` screen flag, plus declared in `db_fields.api`, but neither column exists on `site_emergency_planning` and no connector populates them. The `OR` disjunct in E8 was silently producing "inconclusive" verdicts via `safe_eval(... or None)` instead of the intended hard-fail. Removed.
2. **`run_fix09_ep01_composite_recalc.py` was broken AND unused.** Imported a non-existent `composite_from_sub_scores`. Live DB had zero drift between stored and recomputed composite. Deleted (plus its test).
3. **EP-01 hand-written bands were silently overridden by `band_recipe`.** The compiler at `criterion_spec/compiler.py:168-177` calls `derive_bands_from_recipe(...)` and overwrites the YAML bands whenever a recipe is present and a pivot resolves. The pivot was being pulled from `threshold_metadata.yaml::E8.default_value = 30`, so the engine was running `[>=82.5 / 65 / 30 / 22.5 / 15 / <15]`, not the YAML's `[>=85 / 70 / 42 / 35 / 30 / <30]`. The FB-LL-12 (2026-05-13) decision to "soften the pass mark from 55 → 42" was a no-op at the engine layer for the same reason.
4. **Phase 0.5 sanity claim was stale.** `report/output/feedback/plans/SP-D_band_proposals/EP-01.md` claimed "95% populated" for columns that do not exist. Corrected.

## Decisions taken (with user)

- **D1 — Trauma-distance clause removed from E8.** OSM connector follow-up logged as IMP-0001 in `IMPROVEMENTS.md`.
- **D2 — `hospital_overlay` screen_flag removed.** Cross-criterion dead-anchor sweep logged as IMP-0002.
- **D3 — `nearest_hospital_km` / `nearest_trauma_center_km` removed from `db_fields.api`.** No downstream consumers; `merge_resolver` will stop logging them in `raw_misses`.
- **D4 — `threshold_metadata.yaml` E8 rationale rewritten** to drop the obsolete "secondary trauma-centre clause" wording and anchor the value as norm-derived (DRV-02 / IAEA hard floor at composite = 30/100).
- **D5 — `run_fix09_ep01_composite_recalc.py` deleted** along with its test.
- **D6 — Pass-mark default is "whatever the norms require"** (composite 30, scored at band 5-6 mid-point 5.5).
- **D7 — Phase 0.5 data-sanity doc corrected.**
- **Side-quest (Option A) — embrace the recipe.** The hand-written EP-01 bands have been rewritten in both spec and rubric YAMLs to match what the recipe derives. `score5_pivot: 30` is now explicit. `derive_expr_from_recipe: true` and `pass_mark: 5.0` were added to E8 so the drift guard locks the exclusion expression to the same pivot going forward and the safety floor fires together with the hard fail.

## Engine behaviour after the change

| composite | E8 (`< 30`) | Band   | Ranking score | Floor (`pass_mark = 5.0`) |
|----------:|:-----------:|:------:|:-------------:|:-------------------------:|
| 14.9      | True        | [0, 0] | 0.0           | hard suppresses floor     |
| 22.4      | True        | [1, 2] | 1.5           | hard suppresses floor     |
| 29.9      | True        | [3, 4] | 3.5           | hard suppresses floor     |
| 30.0      | False       | [5, 6] | 5.5           | does not fire             |
| 64.9      | False       | [5, 6] | 5.5           | does not fire             |
| 82.4      | False       | [7, 8] | 7.5           | does not fire             |
| 100.0     | False       | [9, 10]| 9.5           | does not fire             |

Bands, exclusion verdict, and ranking are byte-equivalent to the prior runtime behaviour (the recipe was already winning); this change closes a future-edit trap, not a current scoring drift.

## Artifacts touched

- `config/scoring_specs/ep_emergency_planning.yaml`
- `config/scoring_rubrics/ep_emergency_planning.yaml`
- `config/scoring_specs/threshold_metadata.yaml`
- `report/output/feedback/plans/SP-D_band_proposals/EP-01.md`
- `report/methodology/exclusionary_floors.md` (regenerated)
- `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` (EP-01 moved from opt-out to opt-in; NH-03 + NS-08 promoted to the new opt-out exemplars)
- `tests/scoring/test_safety_floor_pipeline.py` (EP-01 removed from the "no floor" parametrize; it now intentionally uses the floor)
- `prompts/lessons_learned.md` (LL-035)
- `IMPROVEMENTS.md` (IMP-0001..IMP-0006; IMP-0003 closed by this chat for EP-01, left open for the rest of the recipe-carrying criteria)
- Deletions: `src/scripts/run_fix09_ep01_composite_recalc.py`, `tests/scripts/test_run_fix09_ep01_composite_recalc.py`

## Test status at hand-off

Targeted EP-01 / compiler / floors-doc / safety-floor / `test_ep_composite` suite: **96 passed, 2 unrelated NS-01 failures** that pre-exist in the working tree from the in-flight NS-08 work (`test_compiler_parity::test_non_recipe_criteria_remain_byte_equivalent[NS-01]` and `test_safety_floor_pipeline::test_low_score_hard_expression_only_criteria_do_not_floor_fail[NS-01-ctx1]`). Confirmed pre-existing via `git stash` round-trip — the failures persist with my EP-01 edits removed.

Broader `tests/scoring tests/criterion_spec` regression: **203 passed, 4 unrelated failures** (the 2 above plus `test_sensitivity_latest_scoring_parent` and `test_suitable_sites_audit`, both downstream of NS-08 / NS-01 working-tree state, all confirmed pre-existing by stash).

## Follow-ups (open as IMPROVEMENTS.md items)

- **IMP-0001** — OSM trauma-centre / hospital distance connector for EP-01 (restores the intended E8 disjunct).
- **IMP-0002** — Cross-criterion sweep of `db_fields.api` anchors that do not resolve to actual columns or derivations.
- **IMP-0003** — Closed for EP-01; left open for HI-02 / HI-03 / HI-06 and any other recipe-carrying criterion whose hand-written bands have not been audited for consistency with their `band_recipe`.
- **IMP-0006** — Extend the drift validator to warn when YAML `bands:` disagrees with the recipe-derived shape (would catch the EP-01 case at load time instead of waiting for an §O pre-edit analysis to spot it).
