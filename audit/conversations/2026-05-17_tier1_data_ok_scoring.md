<!-- man_hours: 1.8 -->
# Tier 1 Data OK Scoring Implementation

Date: 2026-05-17

## Scope

Implemented Phase 1 / Bucket B Tier 1 Data OK scoring repair for `HI-07`, `NH-10`, and `NH-12` only. No connector work, live API calls, external model calls, migrations, backfills, or DB-writing score runs were performed.

## Expert Artifacts Used

Local project prompts were read and applied as implementation guidance: `experts/connectors/software_architect.md`, `experts/connectors/senior_software_engineer.md`, `experts/quality/auditor.md`, `experts/quality/siting_expert.md`, and `experts/quality/lessons_learned.md`. The new local prompt `experts/quality/data_science_siting_curator.md` was added for future distribution-aware scoring repairs.

## Implementation Summary

- Opened and closed the feature matrix at `audit/feature_completion_matrices/2026-05-17_tier1_data_ok_scoring.md`.
- Added read-only audit tooling in `src/scripts/audit_tier1_data_ok.py` and generated `audit/post_processing/06_scoring/20260517_tier1_data_ok_detail.csv`, `audit/post_processing/06_scoring/20260517_tier1_data_ok_summary.csv`, and `audit/post_processing/06_scoring/20260517_tier1_data_ok_curation_memo.md`.
- Updated `HI-07` to use count/distance fields with the `transmitter_count -> transmitter_count_10km` alias and deferred unsupported `transmitter_power_class`.
- Updated `NH-10` relative bands for the observed smoothed ERA5 monthly-means gust proxy while preserving the 49 m/s design-envelope review flag.
- Updated `NH-12` tmax/tmin sub-score aggregation and null semantics so fully missing temperature evidence remains unscored.
- Repaired unscored handling so GUI/site-profile consumers do not present `quality_flag=unscored` rows as real pass-mark `5.0` evidence.
- Updated criterion docs for accepted columns, before/after status, metric caveats, and deferred fields.

## Audit Result

The local read-only audit returned 362 site rows for `nuscale_voygr6`. The requested baseline run/smr did not have matching local `ranking_scores` rows (`0/362` found), so the generated artifacts document candidate working-tree logic and distributions rather than a persisted before/after DB rescore.

## Verification

Focused tests passed:

```bash
PYTHONPATH=src python -m pytest tests/scoring/test_context_derivations.py tests/scoring/test_tier1_data_ok_bands.py tests/gui/test_site_detail_bars.py tests/scripts/test_audit_tier1_data_ok.py tests/scripts/test_site_profile_unscored_rendering.py tests/scoring/test_compiler_parity.py::test_nh10_wind_envelope_is_review_only_with_fixed_bands -q
```

Result: `46 passed in 1.07s`.

Lints were checked for the edited Python/test files with no reported linter errors.

## Deferred

A persisted before/after scoring comparison requires a DB-writing score run or backfill and remains gated on explicit user consent.

## Follow-Up Auditor Pass

The user requested an auditor review and scored-site examples after implementation. A read-only auditor pass was recorded at `audit/post_processing/06_scoring/20260517_tier1_data_ok_auditor_review.md`.

Fixes from that pass:

- `src/scripts/generate_scoring_examples.py` now resolves `site_human_induced` to the human-hazards ORM table, applies derived context before example scoring, includes site names/coordinates, supports sub-score aggregate examples, and escapes Markdown table cells.
- HI-07 favorable bands were adjusted after the scored examples showed sparse/distant completed-search sites were only reaching 5-6. The updated ladder gives 9-10 to count `<= 5` with nearest transmitter `> 10 km`, 7-8 to count `<= 10` with nearest transmitter `> 5 km`, and keeps dense/nearby lower bands unchanged.
- Generated scored-site example Markdown files for `HI-07`, `NH-10`, and `NH-12` under `audit/post_processing/06_scoring/`.

## Consented GUI-Visible Scoring Run

The user approved the local DB-writing scoring run after the command scope and write targets were described.

Run details:

- Run id: `score-tier1-data-ok-20260517T124032Z`
- DB profile: `merged` (`atoms_vs_ashes_merged`)
- Active profile: `baseline`
- Scope: 361 scored sites x 1 SMR (`nuscale_voygr6`)
- Writes reported by CLI: 17,328 `ranking_scores`, 7,943 `screening_verdicts`, 361 `composite_rankings`
- Warnings: catalog/rubric mismatch remains `E9` missing from rubric and `A16` extra in rubric, pre-existing to this Tier 1 GUI visibility run.

GUI visibility checks:

- `runs` row exists with `run_kind='scoring'`, `status='completed'`, and latest completed scoring timestamp.
- Results run-picker auto-selects newest completed scoring runs (`src/atoms_vs_ashes/gui/_results_run_picker.py`).
- Persisted Tier 1 rows for the new run:
  - `HI-07`: 361 rows, score range 1.5-9.5
  - `NH-10`: 361 rows, score range 1.5-9.5
  - `NH-12`: 361 rows, score range 3.5-8.5
- Post-score read-only audit artifacts:
  - `audit/post_processing/06_scoring/20260517_gui_visible_tier1_data_ok_detail.csv`
  - `audit/post_processing/06_scoring/20260517_gui_visible_tier1_data_ok_summary.csv`
  - `audit/post_processing/06_scoring/20260517_gui_visible_tier1_data_ok_curation_memo.md`
