# man_hours: 1.0
# Conversation log: NH-10 — phase/action norms alignment + connector caveat

**Date:** 2026-05-16 · **Plan:** [`audit/plans/exclusionary_sweep_13877396.plan.md`](../plans/exclusionary_sweep_13877396.plan.md) · **Working file:** `~/.cursor/plans/exclusionary_sweep_13877396.plan.md`

## Trigger

Continuation of the `exclusionary_sweep` chat. Assigned to-do `nh10`: "Run §O pre-edit analysis for NH-10, including wind metric/unit verification." User instruction after the §O matrix landed: "Make it what the norms impose."

## Findings (pre-edit)

1. **Phase / action mismatch.** Spec and rubric both declared `phases: [ranking]` while `fail_conditions[0]` carried `action: exclude`. The rubric's `is_exclusionary` (`src/atoms_vs_ashes/scoring/rubric.py` ~L160) is the disjunction of `"exclusionary" in phases` and `any fc.action == "exclude"` — so it returned True regardless of the declared phase, and `participates_in_composite = is_ranking and not is_exclusionary` returned False. NH-10's declared `weight_factor: 3` / `normalised_weight_pct: 1.1` therefore never entered the composite, despite the YAML implying otherwise. This is the §M anti-pattern "Removing the only `exclude`-action fail_condition without also removing `exclusionary` from `phases` (or vice versa)" run in reverse.
2. **Norms read on `exclude`.** IAEA SSG-18 (Meteorological and Hydrological Hazards in Site Evaluation) and SSG-35 Table I-1 treat extreme winds as a design-basis input rather than a site exclusion. The project's own `docs/expert_siting_criteria_evaluation_matrix.md` § NH-10 row (line 134 of the summary table) lists Phase = `Rank`, weight 1.4 %, no E-code, with the descriptor "Extreme wind hazard incompatible with reference design without major premium" — i.e. design-addressable, ranking-only. No norm cited or claimed by the project supports a hard exclusion at any specific wind speed.
3. **Phantom DB column.** `db_fields.api` listed `site_natural_hazards.extreme_wind_ms`. `\d site_natural_hazards` confirms the column does not exist. The reference leaks into scored bundles as `raw_misses` (e.g. `report/output/chapters/05_country_and_site_profiles/data/RO_turceni_power_station_site_detail.json:42`). This was already triaged in `IMPROVEMENTS.md::IMP-0002`.
4. **Metric vs threshold mismatch.** `max_wind_speed_ms` is set by the ERA5 batch (`src/atoms_vs_ashes/connectors/copernicus_era5/batch.py` L332) as `wind.wind_gust_50yr_ms or wind.max_wind_gust_ms`. `wind_gust_50yr_ms` is computed by GEV fit on annual maxima of the **monthly-means** dataset of the i10fg gust variable (`copernicus_era5/client.py` ~L820-870). Annual-max-of-monthly-means smooths peak instantaneous gusts aggressively. DB confirmation across all 361 sites in `atoms_vs_ashes_merged.site_natural_hazards`: range 5.41 – 14.44 m/s; mean 9.07; 100 % of sites land in band [9-10] (`< 25`). The 49 m/s envelope is unreachable by construction. NOAA NCEI cannot fill the gap for European stations either (LL-015).
5. **Threshold widget.** `config/scoring_specs/threshold_metadata.yaml` already carries the user-tunable knob (`metric: max_wind_speed_ms`, `op: ">"`, `default 49`, bounds 35-80, sources cited as IAEA SSG-9 §6.49 and EN 1991-1-4). Verified post-edit that the override path still rewrites `condition_expr` for `review_flag` actions: `compile_bundle(..., fail_thresholds={"NH-10": {"project_wind_envelope": 60.0}})` produces `condition_expr: "max_wind_speed_ms > 60"` and records the override.

## Decisions (user signed off)

1. **Phases / action.** Make NH-10 what the norms impose: `phases: [ranking]` only, `fail_conditions[0].action: review_flag` (no `exclude`). User: "Make it what the norms impose. It is not for me to decide if this is exclusionary or not."
2. **Phantom field.** Drop `site_natural_hazards.extreme_wind_ms` from `db_fields.api`. User: "drop the reference."
3. **`pass_mark` on the (former) exclude.** Not applicable post-decision-1: `review_flag` actions do not consume `pass_mark`.
4. **Metric remediation.** Surface as a future improvement rather than block this sweep. User: "(i). note the improvements we can make in IMPROVEMENTS.md."
5. **Schema-add vs YAML-only cleanup.** Keep `db_fields` structurally as-is, just drop the phantom field. User: "keep as is."

## Changes (post-edit)

- **`config/scoring_specs/nh_natural_hazards.yaml` NH-10**
  - `db_fields.api` reduced to `[site_natural_hazards.max_wind_speed_ms]` (phantom `extreme_wind_ms` removed).
  - `fail_conditions[0].action`: `exclude` → `review_flag`. `condition_expr` (`max_wind_speed_ms > 49`) and `code` (`project_wind_envelope`) preserved so the threshold widget continues to work.
  - Descriptor on the fail_condition rewritten to surface the SSG-18 / SSG-35 framing: "Fujita-equivalent gust > 49 m/s (177 km/h); review for design-margin and vendor envelope. Per SSG-18 and SSG-35 Table I-1 this is a design-basis matter, not a site exclusion."
  - Band 1-2 descriptor wording cleaned ("ranking penalty only" was a leftover from the `[avoidance, ranking]` framing). Band 0 descriptor extended to clarify "design premium expected, not a site exclusion."
  - New multi-line `notes:` block documenting (a) the matrix-doc Rank classification, (b) the ERA5 monthly-means metric caveat, (c) the IMP-0008 connector follow-up, (d) the silent-de-weighting consequence the change repairs.
  - `band_recipe: {kind: lower_is_better, fail_code: project_wind_envelope}` left intact (cosmetic with no `score5_pivot`; bands are hand-written, in line with NH-01 / NH-08).

- **`config/scoring_rubrics/nh_natural_hazards.yaml` NH-10**
  - Same `db_fields` cleanup, same `action` flip, same descriptors. Concise mirror of the spec `notes:` block (cross-references to the spec for the full rationale).

- **`tests/scoring/test_compiler_parity.py`**
  - `test_exclusionary_numeric_recipes_emit_concrete_band_values`: NH-10 dropped from the `audited` list and from the `overrides` map. Inline comment notes the post-2026-05-16 status.

- **`tests/scoring/test_safety_floor_pipeline.py`**
  - `test_low_score_hard_expression_only_criteria_do_not_floor_fail`: NH-10 parametrize entry removed. Inline comment notes the LL-037 reasoning.

- **`tests/scoring/test_exclusionary_floors_doc.py`**
  - `NO_FLOOR_WAIVERS` reduced from `{EP-01/E8, NH-10/project_wind_envelope, NS-08/E7}` to `{EP-01/E8, NS-08/E7}`. Inline comment explains why NH-10 no longer needs a waiver.

- **`report/methodology/exclusionary_floors.md`**
  - Regenerated via `python -m scripts.generate_exclusionary_floors`. NH-10 was never in the doc (no `pass_mark`); regen is a no-op for NH-10 and incidentally adds a previously-missing E8 / EP-01 row that had drifted out of the on-disk file independently. The on-disk doc now matches the generator output byte-for-byte (test passes).

- **`experts/quality/lessons_learned.md`**
  - Appended `LL-037: declared phases must agree with fail_conditions[].action; and the metric must support the threshold the rubric asserts`. Two-invariant write-up: phase/action consistency + metric/threshold consistency.

- **`IMPROVEMENTS.md`**
  - Appended `IMP-0008: Re-source max_wind_speed_ms from hourly ERA5 i10fg for NH-10`. Captures the deferred connector fix that the rubric change relies on for honest interpretation.

## Validation

- **Drift validation.** `compile_bundle(load_template_bundle("config/scoring_specs"))` succeeds. NH-10 carries no `derive_expr_from_recipe` opt-in (recipe has no `score5_pivot`), so the existing drift guard is satisfied vacuously — same behaviour as NH-01 / NH-08.
- **Phase / action consistency.** Programmatic check confirms post-edit: `is_exclusionary=False`, `participates_in_composite=True` for both spec-loaded and rubric-loaded NH-10 (1.1 % composite weight is now actually applied).
- **Threshold propagation.** `compile_bundle(..., fail_thresholds={"NH-10": {"project_wind_envelope": 60.0}})` rewrites the `review_flag`'s `condition_expr` to `max_wind_speed_ms > 60` and records the override. The user-tunable widget continues to work.
- **Targeted pytest** (29 tests, `tests/scoring/test_compiler_parity.py`, `test_safety_floor_pipeline.py`, `test_exclusionary_floors_doc.py`): all pass.
- **Broad pytest** (`tests/scoring tests/criterion_spec --ignore` of two streamlit-import tests `test_preview_descriptor.py` + `test_threshold_reset_flow.py` that fail with `ModuleNotFoundError: streamlit` in this venv, unrelated to scoring): **241 passed, 1 pre-existing failure** (`tests/scoring/test_sensitivity_latest_scoring_parent.py::test_sensitivity_suite_uses_resolved_scoring_parent_everywhere`, `TypeError: ... missing 1 required keyword-only argument: 'run_id_filter'` — already documented as pre-existing in the NH-07 audit log).
- **DB impact dry-run** (`atoms_vs_ashes_merged`, 361 sites). Pre-change: 0 hard-fails on `project_wind_envelope`, 0 floors, all sites in band [9-10], NH-10 silently absent from composite weights. Post-change: 0 review-flags fire (the metric never reaches 49 m/s; identical screening outcome on the live DB), all sites in band [9-10] (unchanged), NH-10 contributes 1.1 % to the composite (regained). No site moves bands and no site changes verdict; the change is a YAML/runtime consistency repair, not a band edit.

## Open items (deferred)

- **IMP-0008** — Re-source `wind_gust_50yr_ms` from hourly ERA5 i10fg rather than monthly means. Required before the 49 m/s review threshold can be exercised against the data. Live-API consent ritual applies (heavier CDS dataset).
- **GUI popover snapshot regen** — the popover for `project_wind_envelope` will now render with the `review_flag` label palette (blue) rather than the previous (incorrectly red, since `is_exclusionary` was True) palette. Snapshot tests for the GUI popover (`tests/criterion_spec/test_preview_descriptor.py`) cannot be run in this venv (missing `streamlit`); flagged for the next GUI-snapshot pass.
- **Pre-existing `test_sensitivity_latest_scoring_parent` failure** — same one logged in the NH-07 / NS-08 sweep audit logs; not in scope here.
