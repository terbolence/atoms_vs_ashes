# NH-07 — Single-pivot fix to IAEA-anchored 50 km + NULL-as-best handling

UUID: `2c7d4f31` · Created 2026-05-16 · Working file at `/Users/terbolence/.cursor/plans/`

## Task

NH-07 (Volcanism) hard-fails 121 of 361 candidate sites in the merged DB even though **zero** of them are within the IAEA-anchored 50 km pyroclastic-density-current (PDC) envelope. Two structural defects:

1. **Pivot mis-anchored.** `score5_pivot` was set to 300 km — the connector's *search radius* (every Holocene volcano in 300 km is loaded for hazard assessment) — instead of the IAEA SSG-21 §3.5 / SSG-9 §6.36 / SSG-35 Table I-1 exclusionary envelope (50 km). The previous single-pivot sweep picked up the legacy score-5 ranking-grade boundary and promoted it to the exclusion expression. `threshold_metadata.yaml` has correctly held `default 50, bounds 25-200` the entire time — the spec drifted away from it.
2. **NULL silently penalised.** 240 of 361 sites (66 %) have `nearest_holocene_volcano_km = NULL` because the connector ran successfully and found no Holocene volcano within its 300 km search radius. That NULL is positive evidence of safety, yet the recipe-derived top band condition (`>= 1500.0`) doesn't match NULL, so those 240 sites fall through every band and silently score 5.0. The legacy hand-written rubric band carried an `is null` disjunct; the recipe-driven rebuild dropped it.

## Decisions (signed off)

- `score5_pivot = 50` (IAEA-anchored). Confirmed against threshold_metadata.yaml default + connector AVOIDANCE_VEI4_DISTANCE_KM proximity.
- Extend `band_recipe` schema with optional `null_policy: best`. When set, the top band's condition is prefixed with `<metric> is null or `. Exclusion expression is unaffected (NULL never triggers a `<` comparison).
- Rewrite rubric YAML NH-07 bands to recipe-derived ladder (5x / 2x / 1x / 0.5x / 0.2x of pivot). Discard the legacy 300 km score-5 boundary.
- Bundle a soft review-flag for connector avoidance signals. Constraint: only `nh07_hazard_class` is persisted, so we get one coarse flag (`nh07_hazard_class == 'avoidance'`, 6 sites today) rather than the three granular signals (in 5 km edifice / VEI4 in 40 km / recent eruption in 100 km). The granular split would require a connector + schema change and is out of scope here.

## Invariants (system prompt §G)

1. Spec YAML `score5_pivot` is the single source of truth for the top of the score-5 band, the band ladder, and the E4 hard-fail expression.
2. Rubric YAML mirrors spec YAML (post-rewrite); drift guard enforces this for opted-in criteria.
3. `band_recipe.null_policy=best` only affects the top band's expression. It does not affect the exclusion expression, the drift guard, or any other criterion.
4. `nh07_hazard_class` review flag fires independently of E4; it does not change the score.

## Implementation steps

| # | File | Change |
| --- | --- | --- |
| 1 | `src/atoms_vs_ashes/criterion_spec/schema.py` | Add `null_policy: Literal['unscored', 'best'] \| None = None` to `BandRecipeSpec` with docstring. |
| 2 | `src/atoms_vs_ashes/criterion_spec/_band_recipes.py` | `_higher_is_better` accepts `null_policy`; when `best`, prepend `<m> is null or ` to top band condition. Validate that `null_policy=best` is only used with `higher_is_better` (raise for incompatible kinds). Plumb through `bands_from_recipe` dispatch. |
| 3 | `config/scoring_specs/nh_natural_hazards.yaml` NH-07 | `score5_pivot: 50`; `condition_expr: "nearest_volcano_km < 50"`; `band_recipe.null_policy: best`; bands explicit YAML rebuilt to recipe ladder with `is null` disjunct on 9-10; `db_fields.api` extended with `site_natural_hazards.nh07_hazard_class`; new `fail_condition R1` review_flag on `nh07_hazard_class == 'avoidance'`; `notes:` block updated. |
| 4 | `config/scoring_rubrics/nh_natural_hazards.yaml` NH-07 | Same band/condition rewrite as spec YAML. Add R1 review_flag. Remove duplicate `weight_factors`/`weight_basis_source` lines. |
| 5 | `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` | NH-07 expectation `< 300` → `< 50`. |
| 6 | `tests/scoring/test_compiler_parity.py` | NH-07 score-5 expectation `>= 300.0` → `>= 50.0`. |
| 7 | `tests/criterion_spec/test_preview_descriptor.py` | NH-07 descriptor reflects new pivot. |
| 8 | `tests/scoring/test_threshold_band_runtime.py` | NH-07 override expectations refreshed for pivot=50. |
| 9 | `tests/scoring/test_threshold_propagation.py` | NH-07 default pivot=50. |
| 10 | `tests/criterion_spec/test_band_recipe_null_policy.py` (new) | Unit tests for `null_policy=best` behaviour on `_higher_is_better`; failure cases for incompatible kinds. |
| 11 | `tests/scoring/test_nh07_review_flag.py` (new) | Smoke: a site with `nh07_hazard_class='avoidance'` emits the R1 review_flag without affecting score; a site with `'low'` or `'negligible'` does not. |
| 12 | `src/scripts/generate_scoring_examples.py` | When `band_recipe.null_policy=='best'`, also fetch a sample of NULL rows for the top band so the post-edit table proves the 240 NULL sites correctly score 9-10. |
| 13 | `report/methodology/exclusionary_floors.md` | Regenerate via `python -m scripts.generate_exclusionary_floors_doc`. |
| 14 | `prompts/lessons_learned.md` | Append `LL-033 — NH-07 conflated screening radius with exclusion distance`. |
| 15 | `audit/plans/nh07_single_pivot_iaea_50km.md` + `architecture/plans/nh07_single_pivot_iaea_50km.md` | Mirror plan per audit-trail rule. |
| 16 | `audit/conversations/2026-05-16_nh07-single-pivot-iaea-50km.md` | Conversation log. |
| 17 | `audit/man_hours_registry.yml` + `audit/man_hours_summary.md` | Update man-hours. |

## Validation (system prompt §L — produced and archived, not chat-dumped)

- E1 enumeration table (current + proposed) saved to plan file.
- Drift guard re-run against compile_bundle.
- `pytest tests/criterion_spec tests/scoring -x -k 'nh07 or volcan or null_policy or propagation or parity or preview or drift or excl'`.
- Broad `pytest -x --deselect tests/scoring/test_sensitivity_latest_scoring_parent.py` smoke (this test is a pre-existing deselect, unrelated to NH-07).
- GUI smoke: `atoms-gui` already running in terminal 1; confirm threshold widget shows 50 km default, slider bounded 25-200.

## DB impact dry-run (system prompt §K — forecast)

- Current: 121 hard-fail E4.
- Proposed: **0** hard-fail E4 (no site closer than 70.98 km to a Holocene volcano).
- 240 NULL sites: score 5.0 → 9.5 (correct).
- 115 `low` non-null sites: redistribute across 5-6 / 7-8 / 9-10 based on distance.
- 6 `avoidance` non-null sites: same scoring as `low` per E4, plus a new R1 review_flag entry.

## Risks / open items

- **Soft-flag granularity.** Bundled flag uses single `nh07_hazard_class == 'avoidance'` proxy because the three connector sub-signals are not persisted as separate DB columns. If the user wants granularity, a follow-up plan must (a) add `in_pyroclastic_zone_5km`, `vei4_within_40km`, `recent_eruption_within_100km` columns to `site_natural_hazards`, (b) write them from the connector, (c) backfill from `nh07_comment` or re-run the connector.
- **`null_policy` is currently a single-flag extension**, not a full enum. If a future criterion needs "NULL means worst", we extend cleanly.
