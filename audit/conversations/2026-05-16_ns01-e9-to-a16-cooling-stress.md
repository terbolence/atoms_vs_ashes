# man_hours: 1.4
# NS-01 — Cooling water: E9 retired, A16 avoidance + sub-score refactor

**Date:** 2026-05-16
**Plan:** `audit/plans/ns01_e9_to_a16_avoidance.md`
**Lesson:** `experts/quality/lessons_learned.md` LL-036.
**Backlog:** `IMPROVEMENTS.md` IMP-0007.

## Outcome

- E9 hard fail (`cooling_source_type in ['none', null] and dry_cooling_viable == false`)
  retired. It had been structurally unreachable in the merged DB (0 / 2 904
  site-SMR pairs ever triggered it; latest run `score-d51c7c6b`).
- A16 (`avoidance_penalty`) introduced: `cooling_distance_km > 10 and
  water_stress_label in ('High', 'Extremely High')`. DB sanity dry-run:
  fires on 18 / 361 sites (17 TR, 1 PL).
- NS-01 phase flipped from `[exclusionary, ranking]` to
  `[avoidance, ranking]`; `participates_in_composite` now `True`.
- Source-type sub-score (A, 0.44) refactored against the HydroRIVERS
  connector vocabulary (`major_river / river / small_river / stream`);
  `strahler_order` references dropped (column never persisted).
- Water-stress sub-score (C, 0.31) re-keyed on categorical
  `water_stress_label` instead of the raw `water_stress_score` axis the
  connector caps near 2.1.
- Seasonal-drought sub-score (D, 0.20) removed because `spi12_min` has
  no connector and is not a DB column. Remaining A / B / C weights
  re-normalised from 0.35 / 0.20 / 0.25 to 0.44 / 0.25 / 0.31. Backlog
  for an ERA5 / SPEI connector captured as IMP-0007.
- `dry_cooling_viable` is now a derived context value:
  `country_code in {TR, CY, MT, ES, PT, GR} AND water_stress_label ==
  'Extremely High'` ⇒ False; otherwise True.

## Key decisions (user-approved 2026-05-16)

1. **E9 fate — option C.** Convert E9 to an A-code avoidance penalty
   (verdict `caution`) rather than rewriting the exclusion or dropping
   it. Justification: dry / hybrid cooling is the engineering fallback
   at screening, so a hard exclusion on cooling-water adequacy was not
   normatively required even at full data fidelity.
2. **`dry_cooling_viable` source — option (i).** Add a derived-context
   rule rather than wait on an LLM-promoted scalar or drop the clause.
   Conservative default (`True` everywhere outside the arid set) keeps
   the source-type 0-band out of reach for typical CEE sites.
3. **Source-type taxonomy — option A.** Refactor the bands to the
   HydroRIVERS vocabulary and drop the `strahler_order` references; do
   not extend the connector this sweep.
4. **Drought sub-score — option (i).** Drop the sub-score; re-normalise
   weights; track the ERA5/SPEI connector as an IMPROVEMENTS.md item
   (IMP-0007) rather than soft-failing this sweep on a missing data
   source.
5. **Water-stress sub-score — confirmed.** Use the categorical
   `water_stress_label` for band conditions (per
   `.cursor/rules/data-quality-discipline.mdc`: hard-data raw scores
   should not be overloaded with quality categories).
6. **Matrix doc — ok.** Phase row updated to `Rank + avoid`, pass-mark
   line updated, A1-A15 → A1-A16 listing extended.
7. **Operating constraint — local-only.** No live API; all validation
   ran against the existing merged DB and the in-process band evaluator.

## Files touched

- `config/scoring_specs/ns_non_safety.yaml` (NS-01 only)
- `config/scoring_rubrics/ns_non_safety.yaml` (NS-01 only)
- `src/atoms_vs_ashes/scoring/merge_context_derivations.py`
- `report/methodology/exclusionary_floors.md` (regenerated)
- `report/sites_evaluation/07_criteria_non_safety.md` (NS-01 subsection)
- `docs/expert_siting_criteria_evaluation_matrix.md` (summary table + NS-01 section + A1-A16 map)
- `experts/quality/lessons_learned.md` (LL-036)
- `IMPROVEMENTS.md` (IMP-0007)
- `tests/scoring/test_ns01_refactor.py` (new, 45 cases)
- `tests/scoring/test_exclusionary_floors_doc.py` (waiver removed)
- `tests/scoring/test_safety_floor_pipeline.py` (NS-01 parametrisation removed)
- `tests/scoring/test_suitable_sites_audit.py` (assertion inverted)
- `audit/plans/ns01_e9_to_a16_avoidance.md` (mirror)
- `architecture/plans/ns01_e9_to_a16_avoidance.md` (mirror)

## Validation

- `pytest tests/scoring/test_ns01_refactor.py` — 45 / 45 passed.
- `pytest tests/scoring tests/criterion_spec` (excluding pre-existing
  streamlit-import errors and one unrelated `run_id_filter` kwarg
  regression) — 242 / 242 passed.
- DB sanity SELECT against `atoms_vs_ashes_merged` confirms the A16
  trigger fires on 18 / 361 sites (17 TR, 1 PL) — matches the
  empirical water-stress distribution.
- Compiler parity test (`test_non_recipe_criteria_remain_byte_equivalent`)
  green after spec + rubric `notes:` blocks were synced.

## Pre-existing failures (out of scope)

- `tests/scoring/test_sensitivity_latest_scoring_parent.py::test_sensitivity_suite_uses_resolved_scoring_parent_everywhere`
  — `TypeError: ... missing 1 required keyword-only argument: 'run_id_filter'`.
  Verified pre-existing on `dev` HEAD before this change.
- `tests/criterion_spec/test_preview_descriptor.py` and
  `tests/criterion_spec/test_threshold_reset_flow.py` collection errors
  because `streamlit` is not installed in the local venv.
- `tests/test_connector_db_compatibility.py::TestConnectorPersistLiveDB::*` —
  `psycopg2.errors.InsufficientPrivilege` on the test DB. Pre-existing.

## Open follow-ups

- **IMP-0007** — implement ERA5 / SPEI seasonal-drought connector, then
  re-introduce the NS-01 drought sub-score (revert weights to
  0.35 / 0.20 / 0.25 / 0.20) and fix NH-11's similarly dead
  `spi12_min` clause.
- **IMP-0002** — sweep the remaining `db_fields.api` anchors for
  identical "phantom-column" gaps (HI-02 / HI-04 / HI-05 / NH-13 /
  NS-05 / etc.) using the same §O pre-edit ritual.
- **Arid country set tuning.** The current set
  `{TR, CY, MT, ES, PT, GR}` is conservative for the project geography;
  revisit if scope expands beyond CEE + WB or if a real
  climate-classification connector lands.
