<!-- man_hours: 1.6 -->
# National Sensitivity Finish

**Date:** 2026-05-17
**Session ID:** 0416da94-b0e4-4958-8f7e-8ec91fcbaa9f

## Objective

Implement the National Sensitivity Finish Plan without editing the plan
file itself. The user required separated regional and national
sensitivity/stability flows in both UI and server-side code, plus good
Results-page UX: the selected Results tool should automatically resolve
the correct scoring or sensitivity run pool rather than requiring a
manual `Run pool` toggle.

## Key Decisions

- Kept `score sensitivity` as the regional sensitivity command.
- Added a separate `score national-sensitivity` command and national
  service module.
- Added `national_sensitivity` as a distinct `runs.run_kind`.
- Changed regional sensitivity stability persistence to regional scope
  only; national sensitivity writes country-scoped stability separately.
- Split the Scoring Engine page into `Regional Sensitivity Run` and
  `National Sensitivity Run` sections with separate GUI run handles.
- Reworked Results routing so the selected tool determines run kind.
- Split national Results data/rendering into dedicated national modules.
- Split PDF rendering modules to stay under Python file-size limits while
  preserving the public `atoms_vs_ashes.gui.reports.pdf` import surface.

## Files Changed

- `audit/feature_completion_matrices/2026-05-17_national_sensitivity_gui.md`
  — closed the live matrix rows for the GUI/server/results/report fix.
- `src/atoms_vs_ashes/scoring/national_suite.py` — new national
  sensitivity service.
- `src/atoms_vs_ashes/scoring/_cli_national_sensitivity.py` — new Click
  command for national sensitivity.
- `src/atoms_vs_ashes/scoring/_cli.py` — registered the national command.
- `src/alembic/versions/047_add_national_sensitivity_run_kind.py` — added
  `national_sensitivity` enum value.
- `src/atoms_vs_ashes/db/models_analytics.py` — ORM enum update.
- `src/atoms_vs_ashes/db/models_analytics_part3.py` and
  `src/atoms_vs_ashes/db/migrations/_046_national_sensitivity.py` —
  widened national summary `family` to fit scenario-family values.
- `src/atoms_vs_ashes/gui/screen_pages/04_run_dashboard.py` — separated
  regional and national sensitivity launch sections.
- `src/atoms_vs_ashes/gui/_runner.py` — added
  `start_national_sensitivity_run`.
- `src/atoms_vs_ashes/gui/_results_page_main.py`,
  `src/atoms_vs_ashes/gui/_results_run_picker.py`, and
  `src/atoms_vs_ashes/gui/_results_tool_routing.py` — tool-driven run
  routing.
- `src/atoms_vs_ashes/gui/_results_data_national_sens.py` and
  `src/atoms_vs_ashes/gui/_results_render_national_sens.py` — national
  Results data and renderer.
- `src/atoms_vs_ashes/gui/_results_data_stability.py` and
  `src/atoms_vs_ashes/gui/_results_render_stability.py` — explicit
  regional/national stability reader and renderer paths.
- `src/atoms_vs_ashes/gui/reports/*` PDF and country-sensitivity modules
  — surfaced national sensitivity/stability in country reports and split
  PDF renderer modules.
- `tests/gui/*` and existing national scoring tests — added negative
  acceptance coverage for runner separation, Results routing, stability
  scope separation, and national report payloads.
- `audit/man_hours_registry.yml` and `audit/man_hours_summary.md` —
  updated effort metadata.

## Outcome

Completed — the national sensitivity feature now has separated server,
GUI, Results, stability, and report surfaces. Regional and national paths
are no longer mixed in the normal UI, and Results tool selection drives
the required run kind automatically.

Validation:

- `.venv/bin/python -m pytest tests/gui`
- `.venv/bin/python -m pytest tests/scoring/test_national_ranking.py tests/scoring/test_national_oat.py tests/scoring/test_national_sensitivity_persist.py tests/scoring/test_national_mc_rank.py tests/scripts/test_phase_1_6_national_sensitivity.py`
- `.venv/bin/python -m atoms_vs_ashes score national-sensitivity --help`

## Follow-Up: Single-SMR National GUI

The user requested that National Sensitivity work on one SMR for now,
while leaving future multi-SMR support possible.

Implementation:

- Added `--smr-key` to `score national-sensitivity`.
- Added `smr_key` to `NationalSensitivityConfig` and converted it into a
  single-SMR `RunScope` inside `national_suite.py`.
- Passed the scope into national weight/MC inputs, OAT, profile rank
  deltas, MC rank simulation, and national stability persistence.
- Moved the GUI national launcher into `src/atoms_vs_ashes/gui/_runner_national.py`.
- Updated the Scoring Engine page’s National Sensitivity Run section to
  derive its SMR from the saved `Sites & SMR Setup -> SMR technologies`
  selection rather than maintaining a second local selector.
- Disabled national runs unless the saved active profile has exactly one
  SMR technology, preserving the current single-SMR requirement and a
  clear future path to multi-SMR support.
- Moved `Minimum national pairs` into Advanced settings as a small-sample
  warning threshold.

Validation:

- `.venv/bin/python -m pytest tests/gui/test_runner.py tests/scoring/test_national_suite_single_smr.py`
- `.venv/bin/python -m atoms_vs_ashes score national-sensitivity --help`

## Follow-Up: Sensitivity Iteration Defaults

The user requested professional default iteration counts for both
Regional and National Sensitivity while preserving manual lower values
for faster exploratory runs.

Implementation:

- Set both Scoring Engine sensitivity controls to default to `10,000`.
- Updated GUI help text to describe `10,000` as the default and `50,000+`
  as a heavier final-confirmation option.
- Aligned the core sensitivity fallback default with `10,000`.
- Updated the active merged DB profile from `5,000` to `10,000`.

Validation:

- `.venv/bin/python -m pytest tests/scoring/test_sensitivity_cli.py tests/gui/test_runner.py tests/scoring/test_national_suite_single_smr.py`

## Follow-Up: National Run Progress Panel

The user reported that National Sensitivity showed a `Started nat-sens-*`
toast and then immediately displayed "No sensitivity run in flight."

Root cause:

- `score national-sensitivity` was running and writing heartbeat progress.
- The status panel fragment still read the legacy `sens_handle` key.
- After the GUI split regional and national handles, National Sensitivity
  stored its handle in `national_sens_handle`, so the fragment looked in
  the wrong session-state slot.

Implementation:

- Added separate status fragments for `regional_sens_handle` and
  `national_sens_handle`.
- Kept the legacy `sens_handle` route as a fallback.
- Added a friendly status label for `national_sensitivity:mc_summary`.

Validation:

- `.venv/bin/python -m pytest tests/gui/test_run_status_panel.py tests/gui/test_runner.py tests/scoring/test_national_suite_single_smr.py`
