<!-- man_hours: 0.5 -->
# FIX-01 Controller Fixes & Expansions

**Date:** 2026-04-02
**Session ID:** c30115eb-f8e9-4cf8-ac76-66b5d1f71a3b

## Objective

Implement the full FIX-01 specification: 9 fixes (A–I) to existing connectors and analysis modules, 11 criterion expansions (A–K) adding new analysis modules, package refactoring, configuration updates, full-cycle integration tests, and integration snapshots.

## Key Decisions

- Refactored monolithic connector files (`corine.py`, `osm.py`, `population.py`) into packages with `client.py`, `models.py`, and backward-compatible `__init__.py` re-exports
- Created shared `analysis/_provenance.py` utility for DataSource and DataQualityFlag management (FIX-01-G/H)
- Renamed EP-01 sub-score keys from `"EP-02"`, `"EP-03"` etc. to `"ep01_roads"`, `"ep01_special_pop"` etc. to prevent criterion ID collision (FIX-01-D)
- Added `PlantBoundary` dataclass and plant-boundary parsing functions to OSM connector to resolve pre-existing import inconsistency in `test_connectors_osm.py` and `ingest/osm_area.py`
- All 11 expansion modules use pure-function `assess_*()` for testability, with separate `assess_and_persist()` for DB integration
- Created cursor rule `.cursor/rules/integration-tests.mdc` to enforce full-cycle integration test requirement

## Files Changed

### Deleted (replaced by packages)
- `src/atoms_vs_ashes/connectors/corine.py` — replaced by `connectors/corine/` package
- `src/atoms_vs_ashes/connectors/osm.py` — replaced by `connectors/osm/` package
- `src/atoms_vs_ashes/connectors/population.py` — replaced by `connectors/population/` package

### New — Connector Packages (FIX-01-A)
- `src/atoms_vs_ashes/connectors/corine/__init__.py` — re-exports
- `src/atoms_vs_ashes/connectors/corine/client.py` — CorineConnector
- `src/atoms_vs_ashes/connectors/corine/models.py` — CRITERION_IDS, CLC constants, dataclasses
- `src/atoms_vs_ashes/connectors/osm/__init__.py` — re-exports
- `src/atoms_vs_ashes/connectors/osm/client.py` — OverpassClient + plant boundary functions
- `src/atoms_vs_ashes/connectors/osm/models.py` — CRITERION_IDS, OsmElement, PlantBoundary
- `src/atoms_vs_ashes/connectors/population/__init__.py` — re-exports
- `src/atoms_vs_ashes/connectors/population/client.py` — PopulationConnector
- `src/atoms_vs_ashes/connectors/population/models.py` — CRITERION_IDS, PopulationResult

### New — Shared Utilities
- `src/atoms_vs_ashes/analysis/_provenance.py` — ensure_data_source(), write_quality_flag()
- `src/atoms_vs_ashes/ingest/models.py` — GEM-related CRITERION_IDS

### New — Expansion Analysis Modules (EXP A–K)
- `src/atoms_vs_ashes/analysis/wildfire_context.py` — NH-13
- `src/atoms_vs_ashes/analysis/ecological_sensitivity.py` — NS-08
- `src/atoms_vs_ashes/analysis/site_topography.py` — NS-04
- `src/atoms_vs_ashes/analysis/laydown_area.py` — NS-13
- `src/atoms_vs_ashes/analysis/aviation_hazard.py` — HI-01
- `src/atoms_vs_ashes/analysis/military_proximity.py` — HI-06
- `src/atoms_vs_ashes/analysis/transmitter_proximity.py` — HI-07
- `src/atoms_vs_ashes/analysis/grid_proximity.py` — NS-02
- `src/atoms_vs_ashes/analysis/population_projection.py` — RI-06
- `src/atoms_vs_ashes/analysis/coal_site_analysis.py` — NS-05 coal reuse
- `src/atoms_vs_ashes/analysis/land_availability.py` — NS-05 contiguous land

### Modified — Fixes Applied (FIX-01-C through I)
- `src/atoms_vs_ashes/analysis/emergency_plan.py` — sub-score labels, population radius, provenance, quality flags, logging
- `src/atoms_vs_ashes/analysis/epz_population.py` — RI-04 dual persistence, provenance, quality flags, logging
- `src/atoms_vs_ashes/analysis/proximity_land.py` — provenance, quality flags, logging
- `src/atoms_vs_ashes/connectors/__init__.py` — package imports
- `config/default.yml` — OSM settings, analysis configuration section

### New — Testing & Snapshots
- `tests/test_integration_full_cycle.py` — 45 full-cycle integration tests
- `tests/test_connector_db_compatibility.py` — extended scanner for ingest/models.py
- `src/dataAcquisition/integrationSnapshots/FIX-01_integration_snapshot.md` — result snapshot

### New — Rules
- `.cursor/rules/integration-tests.mdc` — integration test requirement rule

## Outcome

Completed — 282 tests pass (45 new + 237 pre-existing), 0 failures, 0 errors. All 9 fixes and 11 expansions implemented per specification.
