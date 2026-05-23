# v1.03 Phase 1 — Rubric and engine correction

**Date:** 2026-05-23
**Session ID:** 32453c09-1209-4649-9968-a16deacc6735
**Plan:** `/Users/terbolence/.cursor/plans/v1.03_phase_1_engine_1f325760.plan.md`
**Master plan pointer:** `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md` §Phase 1
**FCM:** `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md`

## Objective

Close the four engine-layer reviewer items (#43 weights normalisation, #104 SSG-9
"capable fault" mapping, #105 NH-02 screening radius made user-tunable, #183 HI-01
strips small airfields and helipads) at the rubric, scoring engine, connector and
methodology layers — without touching country / site profile prose, which is
rendered downstream and will be re-rendered in Phase 2 against the new rubric.

## Key Decisions

- **#43.** The runtime normaliser in `scoring/rubric.py` is correct (it always
  sums to 1.0 over the composite-participating active set). The defect was that
  the published `normalised_weight_pct` in the rubric YAMLs and the methodology
  / Stage-2 Markdown tables were hand-authored against the unfiltered catalogue
  and reproduced the reviewer's 97.4 % figure. Fixed by treating the runtime
  normalisation as the single source of truth and adding a new script
  `src/scripts/normalise_published_weights.py` that rewrites every published
  surface from it. An engine-side `sum == 1.0` assertion now traps any future
  drift, and `tests/scoring/test_weight_sum_invariant.py` parametrises over
  profile × basis × deactivation states.
- **#104 + #105 (clarified by user).** The user clarified that the NH-02
  screening radius is not "5 km" or "8 km" — it is a UI parameter the user can
  override per run profile. The 8 km norm default (SSG-9 rev. 1) stays, bounds
  in `threshold_metadata.yaml` were widened to `[0.1, 500.0]`, and every
  downstream artefact (band recipes, exclusion expression, methodology,
  requirements, sites_evaluation) now reads the active pivot dynamically. The
  EFSM20 connector lost its hard-coded `E1_THRESHOLD_KM` and now persists
  distance only; the verdict is applied downstream by the scoring engine.
  EGDI now filters by SSG-9 capability before computing the nearest fault, so
  EFSM20 and EGDI agree on what counts as a capable feature.
- **#183.** Only large and medium commercial airports (and military airports)
  contribute to HI-01 scoring penalties. Small / GA / heliport classes are now
  informational columns only (`nearest_any_airport_km` and per-class fields)
  and never enter the band or fail-condition logic. A1 was retired across the
  rubric stack, the avoidance check, the merge-context derivation, the
  methodology, and the appendix entry.
- **Out of scope for Phase 1 (intentionally deferred).** The user clarified
  that HI-01 / NH-02 avoidance LLM prompts under
  `src/atoms_vs_ashes/llm/prompts/` are labelling directives, not scoring
  inputs; updating them does not change scoring behaviour. They will be
  refreshed in Phase 4 alongside the prose / profile rerun.
- **Swing-weight audit.** Declared column was refreshed against the new
  composite normalisation; the Swing column still reflects v1.02 ranking rows
  and will be regenerated in Phase 2 against the `v1_3_national_50000` rerun.
  This is recorded as a note inside `report/version 1.03/methodology/swing_weight_audit.md`.

## Files Changed

### Scoring engine and configuration

- `src/atoms_vs_ashes/scoring/engine.py` — added the `sum == 1.0` invariant.
- `src/scripts/normalise_published_weights.py` — new script (single source of
  truth for published `normalised_weight_pct` values and the related markdown
  tables; idempotent).
- `config/scoring_rubrics/*.yaml` and `config/scoring_specs/*.yaml` —
  `normalised_weight_pct` fields rewritten by the script.
- `config/scoring_specs/threshold_metadata.yaml` — NH-02 E1 default kept at
  8 km, bounds widened to [0.1, 500.0], rationale rephrased to cite SSG-9 rev. 1.
- `config/scoring_rubrics/nh_natural_hazards.yaml` — fallback rubric stack
  aligned to 8 km norm default.
- `config/scoring_rubrics/hi_human_induced.yaml` and
  `config/scoring_specs/hi_human_induced.yaml` — A1 retired, small-class
  favourable band dropped, `nearest_light_airport_km` removed from conditions,
  A4 restricted to large/medium.
- `src/atoms_vs_ashes/criterion_spec/_band_recipe_faults.py` — band-5
  descriptor now reads the active pivot dynamically.
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py` —
  `nearest_light_airport_km` removed from the derived scoring context.

### Connectors

- `src/atoms_vs_ashes/connectors/efsm20_faults/models.py` — removed
  `E1_THRESHOLD_KM` and `capable_fault_within_8km`; expanded
  `CAPABLE_ACTIVITY_CLASSES` docstring to cite SSG-9 rev. 1.
- `src/atoms_vs_ashes/connectors/efsm20_faults/parsers.py` and `batch.py` —
  distance-only persistence; observation text rewritten.
- `src/scripts/run_efsm20_faults.py` — progress / summary output rewritten.
- `src/atoms_vs_ashes/connectors/egdi_geology/parsers.py` — added
  `_EGDI_CAPABLE_ACTIVITIES` and `_is_capable_feature`; `build_fault_assessment`
  now filters by capability before nearest-distance.
- `src/atoms_vs_ashes/connectors/ourairports/parsers.py` and `models.py` —
  `nearest_airport_km` restricted to large/medium for scoring;
  `nearest_any_airport_km` added for transparency; flight-path proxy restricted
  to large/medium; `_check_avoidance_violations` rewritten without A1.

### Methodology and report (engine-layer prose only)

- `report/version 1.03/methodology/business_logic.md` — NH-02 and HI-01
  rewritten.
- `report/version 1.03/methodology/methodology.md` — NH-02 mentions updated.
- `report/version 1.03/methodology/exclusionary_floors.md` — regenerated.
- `report/version 1.03/methodology/swing_weight_audit.md` — Declared column
  refreshed; Phase 2 dependency for Swing column documented inline.
- `report/version 1.03/sites_evaluation/02_master_weights.md` — regenerated
  programmatically.
- `report/version 1.03/sites_evaluation/03_criteria_natural_hazards.md` and
  `04_criteria_human_induced.md` — NH-02 and HI-01 rewritten.
- `report/version 1.03/sites_evaluation/10_appendices.md` — A1-A4 entry
  updated.
- `report/version 1.03/requirements/05_1_siting_criteria_natural_hazards.md` —
  NH-02 entries rephrased to "norm default 8 km, configurable per run profile".
- `report/version 1.03/output/report/chapters/03_stage_2_site_selection.md` —
  Tables 3.2-3.6 regenerated programmatically.

### Tests

- `tests/scoring/test_weight_sum_invariant.py` — new.
- `tests/criterion_spec/test_excl_expr_derived_from_pivot.py` —
  parametrised NH-02 threshold propagation, bounds, and rubric ↔ spec stack
  consistency tests added.
- `tests/test_connector_egdi_geology.py` — two capability-filter tests
  added.
- `tests/test_connectors_efsm20_faults.py` — schema and observation
  assertions rewritten for distance-only persistence.
- `tests/test_connectors_ourairports.py` — `TestAvoidanceViolations` rebuilt
  around A2 / A4 / A4_flight_path only; `test_small_airfield_proximity_no_longer_violates`
  added.
- `tests/scoring/test_context_derivations.py` — asserts
  `nearest_light_airport_km` is not emitted into the scoring context.
- `tests/scoring/test_search_sentinel_bands.py` — HI-01 v4 sentinel and A1
  retirement assertions added.
- `tests/scoring/test_compiler_parity.py` and `tests/scoring/test_run_profile.py` —
  out-of-bounds test value raised to 1000 km after bounds widening.

### Triage and master plan

- `report/version 1.03/output/report/feedback/synthesised_comments/atoms_vs_ashes_report_feedback_triage.yaml` —
  `closure_status` moved to `in-progress` for #43 / #104 / #105 / #183 with
  multi-line `closure_evidence` and `verification_method` blocks pointing at
  the concrete file paths and tests.
- `report/version 1.03/output/report/feedback/feedback_implementation_master_plan.md` —
  Phase 1 header annotated "Phase 1 closed on 2026-05-23"; explanation that
  closure rolls to `done` only after the Phase 2 rerun re-renders the
  rerun-dependent surfaces.
- `audit/feature_completion_matrices/2026-05-23_v1_03_feedback_closure.md` —
  §2 rows for #43 / #104 / #105 / #183 updated with concrete satisfying files
  and `Phase 1 implemented` status (rows that depend on the rerun are flagged
  rerun-dependent and deferred to Phase 2).

## Verification

- `pytest tests/scoring/test_weight_sum_invariant.py tests/criterion_spec/test_excl_expr_derived_from_pivot.py
  tests/test_connector_egdi_geology.py tests/test_connectors_efsm20_faults.py
  tests/test_connectors_ourairports.py tests/scoring/test_search_sentinel_bands.py
  tests/scoring/test_context_derivations.py tests/scoring/test_compiler_parity.py
  tests/scoring/test_run_profile.py` — 286 passed; 1 pre-existing failure in
  `test_compiler_parity.py::test_non_recipe_criteria_remain_byte_equivalent`
  caused by a stable `?` vs `§` mojibake in `weight_basis_source` on a fixed set
  of criteria, unrelated to this phase.
- `PYTHONPATH=src .venv/bin/python src/scripts/normalise_published_weights.py`
  re-run after the first invocation reports `No changes (already normalised).
  Composite participants: 41; sum of published percentages: 100.000000%` —
  idempotency confirmed.

## Trace (per `AGENTS.md` §Definition of Done)

GUI run-profile NH-02 threshold input → `config/scoring_specs/threshold_metadata.yaml`
NH-02 E1 (bounds [0.1, 500.0]) → run-profile loader (`scoring/_load_run_profile.py`)
→ `criterion_spec/_band_recipe_faults.py` band recipe → `scoring/engine.py`
(sum==1.0 invariant) → score persistence in country / site bundles (rerun-dependent,
Phase 2) → Chapter 5 site profile NH-02 line (Phase 2) → reviewer reads the
configured radius back in their profile prose.

## Addendum — B1 validation audit and B4 provenance/verdict renderer

The first close-out marked todo 3 (`p1b_nh02_5km`) complete after subphase 1B
parts B1 (canonical-source widening), B2 (rubric stack alignment), B3 (EFSM20
distance-only persistence), B5 (SSG-9 docstring + EGDI capability filter) and
B6 (methodology) had landed. On review the user flagged that B1's
downstream-clamp validation audit and B4 (bundle provenance + dynamic verdict
renderer) had been skipped. This addendum closes both items.

### B1 — downstream clamp audit

- `src/atoms_vs_ashes/gui/_threshold_editor_widgets.py` `threshold_input`
  sources `min_value` / `max_value` from `fc.bounds_min` / `fc.bounds_max`
  (no hard-coded numeric clamp).
- `src/atoms_vs_ashes/criterion_spec/preview.py` `build_failcondition_preview`
  forwards `spec.bounds.min` / `spec.bounds.max` from
  `threshold_metadata.yaml` unmodified.
- `rg "clamp|assert.*pivot|assert.*threshold"` across
  `src/atoms_vs_ashes/criterion_spec/` and `src/atoms_vs_ashes/runprofile/`
  returns zero matches — no narrow guard inside the spec compiler, the
  band-recipe code paths, the run-profile persister, or `_safety_floor`.
- EFSM20 connector header (`src/atoms_vs_ashes/connectors/efsm20_faults/models.py`)
  now documents the `SEARCH_RADIUS_KM = 50.0` degrade-case explicitly: a
  run-profile NH-02 E1 above this window cannot be detected by the
  connector and the engine treats "no fault detected" as "outside the E1
  radius". Operators widening past 50 km must also widen `SEARCH_RADIUS_KM`
  deliberately.

A user-typed value anywhere in `[0.1, 500.0]` therefore reaches the score
engine intact through GUI → run profile → compiler → engine.

### B4 — bundle provenance and dynamic verdict renderer

- New module `src/atoms_vs_ashes/reporting/run_profile_provenance.py`:
  - Reads NH-02 E1 from the run's `CompiledScoringSnapshot` (the existing
    Phase-1 reproducibility record stored at scoring time).
  - Falls back to `config/scoring_specs/threshold_metadata.yaml`
    `default_value` when no snapshot is linked (older runs, ad-hoc bundle
    exports). Returns `None` if neither source resolves; the renderer
    degrades gracefully.
  - Generic shape: extend `run_profile_provenance(...)` (not the callers)
    when the next UI-tunable threshold lands.
- Site bundle JSON now carries a `provenance` block next to `metadata`
  (`src/atoms_vs_ashes/reporting/site_bundle.py`); country bundle JSON
  carries the same block (`src/atoms_vs_ashes/reporting/country_bundle.py`).
- Site-profile evidence renderer
  (`src/scripts/_site_profile_intelligence.py` `evidence_for`) accepts an
  optional `provenance` kwarg. For NH-02 the renderer now emits an extra
  signal `"E1 verdict (radius R km): inside|outside the SSG-9 capable-
  fault screening envelope"` computed from the active threshold instead of
  any Python constant. When the distance or threshold is missing, the
  signal is omitted (no stale verdict).
- `src/scripts/_site_profile_markdown.py` reads `bundle["provenance"]`
  once and threads it through every `_family_section` call so the verdict
  reaches the NH section without affecting unrelated families.
- `tests/reporting/test_run_profile_provenance.py` (new):
  - Parametrised snapshot round-trip for thresholds across the full
    widened range (0.5, 1.0, 5.0, 8.0, 10.0, 50.0, 100.0).
  - Metadata-yaml fallback when no snapshot is linked.
  - Provenance block always contains the NH-02 key.
  - Renderer emits `inside` / `outside` correctly across distance ×
    threshold combinations.
  - Renderer omits the verdict line when provenance or distance is
    missing.
- `tests/scripts/test_site_profile_unscored_rendering.py` `_patch_helpers`
  updated to accept the new keyword-only `provenance` parameter.

### Verification

- `pytest tests/reporting/ tests/scoring/test_weight_sum_invariant.py
  tests/criterion_spec/test_excl_expr_derived_from_pivot.py
  tests/test_connector_egdi_geology.py tests/test_connectors_efsm20_faults.py
  tests/test_connectors_ourairports.py tests/scoring/test_search_sentinel_bands.py
  tests/scoring/test_context_derivations.py tests/scoring/test_run_profile.py
  tests/scripts/test_site_profile_unscored_rendering.py` — 313 passed.
- Broad sweep (`pytest -q --ignore=tests/scoring/test_compiler_parity.py`)
  — 2499 passed, 10 pre-existing failures (NH-09 banding,
  `report/methodology/exclusionary_floors.md` legacy-path doc test,
  sensitivity / integration / RI-04 / enrichment-coverage). None touch the
  surfaces edited in this addendum.

## Follow-ups (Phase 2+)

- Run `v1_3_national_50000` against the corrected rubric and refresh
  country bundles, site bundles, ledger CSVs, Chapter 5 site/country profiles,
  Chapter 4 results, and the sensitivity export pack.
- Regenerate the Swing column of `swing_weight_audit.md` against the rerun.
- Roll `closure_status` from `in-progress` to `done` once the rerun-rendered
  surfaces (per-site NH-02 / HI-01 lines, master weights, sensitivity pack)
  match the new rubric end-to-end.
- Investigate the pre-existing `test_compiler_parity` mojibake regression
  outside the Phase 1 surface.
