<!-- man_hours: 1.5 -->
# 2026-05-16 — NH-04 single-pivot anchor to IAEA SSG-9 25° envelope

## Context

User flagged that NH-04 ("Geotechnical: Slope Stability") was hard-failing 158 sites, and that the GUI threshold widget displayed "25,00" while the actual band-5 boundary in the rubric was 8°. Goal: realign so the threshold widget value IS the band-5 boundary and the hard E3 expression, all driven by a single pivot. Companion concern: the metric `slope_angle_deg` is a 1 km buffer mean (not on-site footprint slope), which silently misrepresents what "Maximum acceptable slope angle (degrees)" means in the UI.

User invoked `experts/scoring/scoring_criterion_review.md` for the change.

## Decisions taken (with explicit user sign-off in chat)

1. **Pivot value = 25°.** Threshold widget default, band_recipe.score5_pivot, and the E3 hard expression all anchor to IAEA SSG-9 §6.34 / NUREG-0800 §2.5.5.
2. **155-site rescue is intentional**, not because the user expects rescue, but because the scoring engine must implement the IAEA norm correctly and the data we have must be evaluated against the corrected ladder. The 99.1% band-shift is a direct consequence of replacing the project's idiosyncratic 1/3/8/15/25 ladder with the recipe-derived 5/10/25/37.5/50 IAEA ladder.
3. **Soft-flag ("NH-04 runout/lateral-hazard signal") deferred** to a separate plan. Will require persisting `pct_above_30` / `p95_deg`, an Alembic migration, and connector work.
4. **Hand-written rubric bands abandoned** in favour of recipe-derived ladder. User confirmed: norms (IAEA/EPRI) are the source of truth; the threshold widget is the user-controlled adaptation surface; the drift guard catches regressions.
5. **Metric defect surfaced explicitly** rather than fixed in this change. User said: "I don't want the algorithm to assume that 30 deg at 1km from the site is the same as 30deg on the site. This should be flagged as a design issue and I can give a resolution."

## DB impact dry-run (read-only `atoms_vs_ashes_merged`, no live API)

| Metric | Value |
| --- | --- |
| Sites with slope data | 352 |
| Old hard-fail (E3 at slope > 8°) | 158 |
| New hard-fail (E3 at slope > 25°) | 3 |
| Rescued (old fail, new pass) | 155 |
| Newly failed (old pass, new fail) | 0 |
| Sites that changed band | 99.1% |

Per-SMR breakdown: NH-04's E3 is not SMR-specific, so the impact is uniform across the 8 active designs (`bwrx_300`, `holtec_smr300`, `natrium_nominal`, `natrium_peak`, `nuscale_voygr6`, `oklo_aurora`, `rolls_royce_smr`, `xe_100`).

## Files touched

See plan §6 in `audit/plans/nh04_single_pivot_iaea_25deg.md`.

## Tests

Targeted suites: `tests/criterion_spec/test_preview_descriptor.py`, `tests/scoring/test_safety_floor_pipeline.py`, `tests/scoring/test_exclusionary_floors_doc.py`, `tests/scoring/test_threshold_propagation.py` (new), `tests/criterion_spec/test_excl_expr_derived_from_pivot.py`, `tests/scoring/test_threshold_band_runtime.py` — all green (53 pass).

Broad sweep: `tests/scoring tests/criterion_spec` — 184 pass, 1 deselected (`test_sensitivity_latest_scoring_parent` — pre-existing failure unrelated to NH-04, root cause: `fake_load_pairs` missing `run_id_filter` kwarg in test scaffolding).

## Lessons learned

`LL-032` appended to `experts/quality/lessons_learned.md`: NH-04 slope metric conflates on-site footprint with surrounding terrain.

## Follow-ups

1. Deferred plan: "Split NH-04 into footprint + runout signals" — requires Alembic migration for `pct_above_30` / `p95_deg`, connector re-run with 200 m buffer for on-site slope, and a new screen_flag fail_condition.
2. Cosmetic: align `config/scoring_specs/threshold_metadata.yaml::NH-04.E3.op` from `>=` to `>` so widget metadata matches the recipe-derived strict operator.
