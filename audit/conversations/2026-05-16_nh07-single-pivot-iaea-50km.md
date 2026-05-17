# man_hours: 1.4
# Conversation log: NH-07 — single-pivot fix to IAEA-anchored 50 km + NULL-as-best

**Date:** 2026-05-16 · **Plan:** `audit/plans/nh07_single_pivot_iaea_50km.md` · **Working file:** `/Users/terbolence/.cursor/plans/nh07_single_pivot_iaea_50km_2c7d4f31.plan.md`

## Trigger

User report: NH-07 (Volcanism) hard-fails 121 of 361 candidate sites in the merged DB. Asked: "Use `experts/scoring/scoring_criterion_review.md` and verify and fix this criterion."

## Findings (pre-edit)

1. **Pivot mis-anchored.** Spec YAML had `score5_pivot: 300` and `E4.condition_expr: "nearest_volcano_km < 300"`. The 300 km is the Smithsonian-GVP connector's *search radius* (every Holocene volcano within 300 km is loaded for the per-site hazard report). The IAEA-anchored credible PDC envelope is **50 km** (SSG-21 §3.5-3.7 / SSG-9 §6.36 / SSG-35 Table I-1). `config/scoring_specs/threshold_metadata.yaml` correctly held `default 50, bounds 25-200` the entire time — the spec drifted away from it during the earlier single-pivot sweep, which promoted the legacy score-5 ranking boundary (300 km) to the exclusion pivot.
2. **NULL silently penalised.** 240 of 361 sites (66 %) have `nearest_holocene_volcano_km = NULL` because the connector ran successfully and found no Holocene volcano within its 300 km search. The recipe-derived top band (`>= 1500.0`) did not match NULL, so those sites fell through every band and scored **5.0** (the band evaluator's no-data default) instead of **9-10**.
3. **DB histogram (361 sites):** NULL=240, < 50 km = 0, < 100 km = 8, < 150 km = 36, < 200 km = 77, < 300 km = 121. Min non-null = 70.98 km (Hasandag-Keciboyduran Volcanic Complex, TR). Max = 291.97 km.
4. **Scored examples diagnostic (current pivot=300):** Every non-null site (4 of 4 sampled) was hard-failing E4 even though the closest one (70.98 km) is above the IAEA-anchored 50 km envelope and above the connector's own VEI 4 avoidance distance (40 km).

## Decisions (user signed off)

1. `score5_pivot = 50` (IAEA-anchored).
2. Add `null_policy: best` to `BandRecipeSpec`; apply to NH-07.
3. Rewrite rubric YAML bands to the recipe-derived ladder.
4. Bundle a soft `review_flag` for the connector avoidance signal. Constraint accepted: only `nh07_hazard_class` is persisted as a structured column, so the flag is a coarse single-column proxy rather than three granular sub-signals. Granular split deferred.

## Changes (post-edit)

- **`src/atoms_vs_ashes/criterion_spec/schema.py`** — added `null_policy: BandRecipeNullPolicy | None` to `BandRecipeSpec` with full docstring.
- **`src/atoms_vs_ashes/criterion_spec/_band_recipes.py`** — `_higher_is_better` accepts `null_policy`; `bands_from_recipe` rejects `null_policy='best'` for incompatible recipe kinds.
- **`config/scoring_specs/nh_natural_hazards.yaml` NH-07** — `score5_pivot: 50`, `condition_expr: "nearest_volcano_km < 50"`, `band_recipe.null_policy: best`, bands explicitly rebuilt to 5x/2x/1x/0.5x/0.2x ladder with `is null` disjunct on top band, `db_fields.api` extended with `nh07_hazard_class`, new `R1` review_flag, full `notes:` block.
- **`config/scoring_rubrics/nh_natural_hazards.yaml` NH-07** — same band/condition rewrite; R1 review_flag added; duplicate `weight_factors`/`weight_basis_source` block removed; `notes:` block added.
- **`src/scripts/generate_scoring_examples.py`** — detects `null_policy='best'` via the top band's expression (compiled Criterion does not retain the recipe), includes NULL rows in the sample, forces at least one NULL row in the top band so the user can audit the NULL-as-best behaviour directly.
- **Tests** — `test_band_recipes.py` (3 new tests for null_policy), `test_nh07_review_flag.py` (4 new tests), `test_excl_expr_derived_from_pivot.py`, `test_compiler_parity.py`, `test_threshold_propagation.py`, `test_search_sentinel_bands.py` updated.
- **`report/methodology/exclusionary_floors.md`** — regenerated.
- **`experts/quality/lessons_learned.md`** — appended `LL-033`.

## Validation

- Drift guard: `compile_bundle` succeeds; `derived_exclusion_exprs['NH-07']='nearest_volcano_km < 50'`.
- Targeted pytest (113 tests across criterion_spec + scoring NH-07-related modules): **all pass**.
- Broad pytest excluding pre-existing failures (`test_sensitivity_latest_scoring_parent.py`, `test_active_profile.py`, `test_profile_resolution.py`): **2202 passed, 9 pre-existing failures unrelated to NH-07** (`test_run_fix09_ep01_composite_recalc.py` has an `ImportError: cannot import name 'composite_from_sub_scores'` and `TestRI04FullCycle::test_evaluate_ri04_fail` returns `'pass' == 'fail'` — both confirmed pre-existing via `git stash`).
- DB impact (forecast): **121 → 0** sites hard-fail E4; 240 NULL sites score **5.0 → 9.5**.
- Scored-examples post-edit confirms: top band includes one NULL site (Hungary, `negligible`, score 9.5) and one site at 250 km from Kula volcano (Turkey, score 9.5); 5-6 band has the closest non-null site at 70.98 km (Hasandag, score 5.5, verdict `pass`); 3-4 / 1-2 / 0 bands have no sites.

## Open items (deferred)

- Granular soft-flag split (in 5 km / VEI ≥ 4 in 40 km / recent eruption in 100 km) — requires connector + schema changes to persist the three sub-signals.
- Two pre-existing test failures (`composite_from_sub_scores` ImportError + RI-04 evaluator regression) — flagged for the next maintenance pass; not in scope for the NH-07 fix.
