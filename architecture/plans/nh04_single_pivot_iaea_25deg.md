# NH-04 — Anchor scoring to IAEA SSG-9 25° envelope (single-pivot)

**Slug:** `nh04_single_pivot_iaea_25deg`
**Plan file (working copy):** `~/.cursor/plans/nh04_single_pivot_iaea_25deg_982a1d15.plan.md`
**Repository mirrors (per audit-trail.mdc):**
- `architecture/plans/nh04_single_pivot_iaea_25deg.md`
- `audit/plans/nh04_single_pivot_iaea_25deg.md`

## 1. Goal

Align NH-04 (Geotechnical — slope stability) bands and the E3 hard exclusion to the IAEA SSG-9 §6.34 / NUREG-0800 §2.5.5 **25° mitigable envelope on competent rock**, controlled by a single pivot (`band_recipe.score5_pivot = 25`). The GUI threshold widget, the recipe-rebuilt 0-10 bands, and the hard E3 expression all move together. Honour the user's "input number IS the band-5 boundary" requirement.

## 2. Context (pre-change defect)

- `band_recipe.score5_pivot` was `8` after the FB-NH-02 single-pivot refactor; `config/scoring_specs/threshold_metadata.yaml::NH-04.E3.default_value` was `25` (IAEA-anchored). The GUI widget showed 25 but the compiler used 8 — the widget number did not match the actual band-5 boundary or the hard expression.
- The metric `site_natural_hazards.slope_angle_deg` is the **mean slope over a 1 km buffer** (Copernicus DEM 30 m via `copernicus_dem/parsers.py::compute_slope_stats`). Across the merged DB, average buffer-mean is 8.14° and average buffer-max is 70.05°. With pivot=8, **158 of 352 sites hard-failed E3** — many of them flat coastal-bluff or foothill sites where the buffer captures nearby terrain, not the plant pad.
- The rubric YAML (legacy `load_rubric_bundle` path) carried hand-written band cuts `<1 / <3 / <8 / <15 / <25 / >=25` that disagreed with the spec compiler's recipe-rebuilt ladder.

## 3. Scope

1. Set `band_recipe.score5_pivot = 25` and `condition_expr = "slope_angle_deg > 25"` in both spec and rubric YAMLs.
2. Rewrite rubric YAML's hand-written bands to the recipe-aligned ladder `<=5 / <=10 / <=25 / <37.5 / <50 / >=50`.
3. Add explicit `notes:` blocks in both YAMLs documenting the slope-at-distance metric defect.
4. Append `LL-032` to `prompts/lessons_learned.md` for institutional memory.
5. Add a propagation regression test that locks the `RunProfile.fail_thresholds → compile_bundle → Criterion (bands + fail_conditions) → engine` chain.
6. Update existing tests (`test_excl_expr_derived_from_pivot`, `test_safety_floor_pipeline`, `test_threshold_band_runtime`) to the new defaults; switch `test_safety_floor_pipeline` floor fixtures to NH-03 (the canonical floor-reachable criterion now).
7. Regenerate `report/methodology/exclusionary_floors.md`.

## 4. Out of scope (deferred)

- Splitting NH-04 into "on-site footprint slope" + "runout / lateral-hazard buffer signal". Requires:
  - Persisting `pct_above_30`, `p95_deg` from `compute_slope_stats` into `site_natural_hazards` (Alembic migration).
  - Adding a screen_flag fail_condition for runout review.
  - Optional: re-run the Copernicus DEM connector with a 200 m buffer to compute true on-site footprint slope.
- Cleaning up `threshold_metadata.yaml::NH-04.E3.op` from `>=` to `>` so the widget metadata matches the recipe-derived strict operator.

## 5. Steps executed (this run)

1. **Discover** — read NH-04 in both YAMLs, the matrix doc, the connector (`copernicus_dem/`), the safety-floor module, and the merged-DB statistics. Confirmed 158/352 sites hard-failing under pivot=8.
2. **Dispatch** — `phases: [exclusionary, ranking]` + `action: exclude` ⇒ §E1 + §E4 artifacts. (§E5 deferred.)
3. **Present current state** — truth table + score curve as-is.
4. **Present proposed state** — diff vs. pivot=25 ladder; 99.1% band shift; 155 rescued, 0 newly failed.
5. **AWAIT user sign-off** — received. Confirmed pivot=25, intentional rescue, hand-written bands abandoned in favour of recipe-derived ladder, soft-flag deferred.
6. **Derive YAML** — applied to both `scoring_specs/nh_natural_hazards.yaml` and `scoring_rubrics/nh_natural_hazards.yaml`. Added `notes:` blocks pointing to LL-032.
7. **Prove invariants** — enumeration table over `[-1, 0, 0.5, 4.99, 5.0, ..., 100.0]` proved bands mutually exclusive + exhaustive. Drift guard passes.
8. **Regenerate** — `report/methodology/exclusionary_floors.md` written via `scripts.generate_exclusionary_floors`; doc-sync test passes.
9. **DB impact dry-run** — 352 sites with slope; pre 158 hard-fail, post 3 hard-fail, 155 rescued, 0 newly failed, 99.1% band shift. Per-SMR breakdown is uniform across the 8 active designs because NH-04 has no per-SMR threshold.
10. **Tests** — added `tests/scoring/test_threshold_propagation.py` (5 tests, all green); updated existing tests; broad sweep `tests/scoring tests/criterion_spec` 184 pass / 1 deselect (pre-existing unrelated failure: `test_sensitivity_latest_scoring_parent`).
11. **Audit / plan / lessons** — plan written here, mirrored into repo per audit-trail.mdc; LL-032 appended to `prompts/lessons_learned.md`; conversation log written to `audit/conversations/2026-05-16_nh04-single-pivot-iaea-25deg.md`.

## 6. Files touched

- `config/scoring_specs/nh_natural_hazards.yaml`
- `config/scoring_rubrics/nh_natural_hazards.yaml`
- `prompts/lessons_learned.md` (LL-032 appended)
- `report/methodology/exclusionary_floors.md` (regenerated)
- `tests/scoring/test_threshold_propagation.py` (new)
- `tests/scoring/test_safety_floor_pipeline.py` (floor fixtures moved to NH-03)
- `tests/scoring/test_threshold_band_runtime.py` (override tests aligned to pivot=25)
- `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` (default expectations updated)
- `tests/criterion_spec/test_preview_descriptor.py` (NH-04 descriptor updated)
- `tests/scoring/test_compiler_parity.py` (NH-07 score-5 expectation updated)
- `audit/man_hours_registry.yml` (delta for this conversation)
- `audit/man_hours_summary.md` (regenerated)

## 7. Acceptance checklist

- [x] §G invariants verified (mutual exclusion, exhaustivity, pass_mark/band-5 alignment, drift guard, both YAMLs in sync, file-size limits).
- [x] §L evidence produced (enumeration, drift, doc regen, targeted + broad pytest, GUI smoke, DB dry-run).
- [x] §K dry-run reported with explicit user acceptance of the 99.1% band shift / 155 rescue.
- [x] LL-032 captures the metric / norm mismatch for the deferred "split NH-04" plan.
- [x] Propagation regression test (`test_threshold_propagation.py`) locks the GUI → engine chain.

## 8. Follow-ups for the user

- Confirm the deferred plan ("Split NH-04 into footprint + runout signals") and the Copernicus DEM connector re-run with a 200 m buffer is wanted. If yes, I will draft a separate plan covering: Alembic migration for `pct_above_30` / `p95_deg`, connector re-run plan with the live-API consent ritual, scoring_specs schema split, screen_flag rubric authoring.
- Cosmetic: update `threshold_metadata.yaml::NH-04.E3.op` to `">"` so the widget metadata matches the derived strict operator. Low priority.
