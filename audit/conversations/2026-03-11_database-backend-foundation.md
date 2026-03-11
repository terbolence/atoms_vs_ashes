# Database + Backend Foundation

**Date:** 2026-03-11
**Session ID:** N/A

## Objective
Implement the full data infrastructure foundation: PostgreSQL/PostGIS database, schema, Python backend scaffold, data ingestion pipeline (GEM Coal Plant Tracker + ownership), CLI orchestration, configuration, structured logging, and test suite.

## Key Decisions
- Used PostgreSQL 17 + PostGIS 3.6 (Homebrew; PG16 lacked PostGIS bindings) — satisfies the "16+" spec requirement.
- Adopted src-layout Python project with pyproject.toml and editable install.
- Alembic manages schema migrations; a single initial migration creates all 13 application tables + 4 custom enums.
- GEM entity ID fields widened from VARCHAR(60) to TEXT — source data contains semicolon-separated multi-ID values with percentages.
- Pandas `dtype=str` turns NaN into literal `"nan"` string; all `_str_or_none` helpers now filter `nan`/`NaN`/`None` strings.
- Site deduplication operates at GEM location ID level (one site per location, not per unit).
- Ownership share sums exceed 100% for multi-unit sites — this is expected GEM data behavior (per-unit shares summed at location level). Validation warns but does not reject.

## Files Changed
- `.gitignore` — created with Python/venv/IDE/data exclusions
- `.env.example` — database and API key template
- `docker-compose.yml` — PostgreSQL + PostGIS container definition
- `pyproject.toml` — project metadata, dependencies, CLI entry point, pytest config
- `alembic.ini` — Alembic configuration
- `alembic/env.py` — Alembic environment with model metadata
- `alembic/script.py.mako` — migration template
- `alembic/versions/001_initial_schema.py` — initial migration (all tables, enums, indexes)
- `config/default.yml` — in-scope countries, source paths, supplementary sites, weights, thresholds
- `src/atoms_vs_ashes/__init__.py` — package init
- `src/atoms_vs_ashes/__main__.py` — `python -m atoms_vs_ashes` entry
- `src/atoms_vs_ashes/cli.py` — Click CLI with ingest/validate/run/enrich/screen/score/report subcommands
- `src/atoms_vs_ashes/config.py` — YAML + env settings loading with Pydantic
- `src/atoms_vs_ashes/logging.py` — structlog JSON logging with run_id propagation
- `src/atoms_vs_ashes/db/__init__.py` — db package
- `src/atoms_vs_ashes/db/engine.py` — SQLAlchemy engine/session management
- `src/atoms_vs_ashes/db/models.py` — all 13 ORM models matching architecture/specs/02_data_model_postgres.md
- `src/atoms_vs_ashes/ingest/__init__.py` — ingest package
- `src/atoms_vs_ashes/ingest/sites.py` — GEM Coal Plant Tracker ingestion + supplementary sites
- `src/atoms_vs_ashes/ingest/ownership.py` — ownership ingestion, linking, staging, validation
- `src/atoms_vs_ashes/pipeline/__init__.py` — pipeline package
- `src/atoms_vs_ashes/pipeline/runner.py` — pipeline orchestration (ingest + validate)
- `src/atoms_vs_ashes/pipeline/quality_report.py` — data quality report generator
- `src/atoms_vs_ashes/connectors/__init__.py` — connector placeholder
- `tests/__init__.py` — test package
- `tests/conftest.py` — shared fixtures
- `tests/test_config.py` — config loading tests (4)
- `tests/test_models.py` — model schema tests (3)
- `tests/test_ingest_sites.py` — site ingestion helper tests (9)
- `tests/test_ingest_ownership.py` — ownership helper tests (2)
- `tests/test_integration_db.py` — live DB integration tests (8)

## Outcome
Completed — all plan items delivered:
- 363 sites ingested (361 GEM + 2 supplementary Romanian) across 20 countries
- 3,228 ownership records linked with 0 unmatched
- 0 missing coordinates
- 26/26 tests passing
- CLI fully functional: `python -m atoms_vs_ashes ingest`, `validate`, `run`
