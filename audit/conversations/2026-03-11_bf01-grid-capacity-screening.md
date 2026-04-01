<!-- man_hours: 0.5 -->
# BF-01 Grid Capacity Screening Check Implementation

**Date:** 2026-03-11
**Session ID:** grid-capacity-screening-check

## Objective

Implement the first screening check (BF-01: Grid Capacity Basic Filter) using the existing `screening_results` table, establishing the reusable screening framework that all subsequent criteria will follow.

## Key Decisions

- **No new tables needed** — the existing `screening_results`, `criteria`, and `data_quality_flags` tables provide the scalable pattern for all screening checks.
- **7 deployable SMR designs, 8 capacity thresholds** — Kairos Power / KP-FHR (Hermes) excluded from all screening (0 MWe test reactor). TerraPower Natrium checked at both nominal (345 MWe) and peak (500 MWe) capacity.
- **Pass verdict = any SMR fits** — a site passes BF-01 if it can accommodate at least the smallest deployable SMR (Oklo Aurora, 75 MWe). The value JSON captures which specific SMR types are compatible.
- **Capacity resolution** — `grid_capacity_mw` is preferred; falls back to `installed_capacity_mw` as proxy. Missing data produces `inconclusive` verdict with a `DataQualityFlag`.
- **Screening framework** — base class with registry pattern (`@register_check` decorator) so future checks self-register on import and can be discovered by the runner.
- **Config-driven thresholds** — all SMR specs and screening parameters live in `config/default.yml`, not hard-coded.

## Files Changed

- `config/default.yml` — added `smr_types` (8 entries) and `basic_filters.bf_01_grid_capacity` to screening section
- `src/atoms_vs_ashes/config.py` — added `screening`, `smr_types`, `basic_filters` property accessors
- `alembic/versions/002_seed_screening_criteria.py` — new migration seeding BF-01 criterion row
- `src/atoms_vs_ashes/screening/__init__.py` — new package init with re-exports and auto-registration
- `src/atoms_vs_ashes/screening/base.py` — new `ScreeningCheck` ABC, `CheckSummary`, registry functions
- `src/atoms_vs_ashes/screening/grid_capacity.py` — new `GridCapacityCheck` implementation with pure-logic `evaluate_site()` function
- `src/atoms_vs_ashes/pipeline/runner.py` — added `run_screening()` orchestration function
- `src/atoms_vs_ashes/cli.py` — wired `screen` command with `--criteria` filter option
- `tests/test_screening_grid_capacity.py` — 23 unit tests covering all 8 boundary thresholds, justification text, Kairos exclusion, and value structure

## Outcome

Completed — all 41 tests pass (18 existing + 23 new). The screening framework is ready for additional criteria (BF-02 land area, E1-E9 exclusionary, A1-A15 avoidance) to be added following the same pattern. Run with `atoms-vs-ashes screen` or `atoms-vs-ashes screen --criteria BF-01`.
