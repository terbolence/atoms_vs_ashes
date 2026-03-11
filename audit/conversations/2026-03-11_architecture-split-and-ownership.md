# Architecture Split and Ownership Table

**Date:** 2026-03-11
**Session ID:** a09a0fc4-ad25-46ec-91df-37797854d867

## Objective

1. Determine whether a UI is needed for API health monitoring during batch runs (concluded: terminal + structured logs is sufficient).
2. Move `requirements/08_automated_system.md` into a dedicated `architecture/specs/` folder, splitting it into module-level specification files.
3. Add a `site_ownership` table to the PostgreSQL data model to ingest GEM ownership CSV data.
4. Set up a project audit trail (conversations + plans logging).

## Key Decisions

- **No UI needed initially** — CLI-first with structured JSON logging, progress bars, and post-run summary reports. UI deferred until needed by non-technical stakeholders.
- **Module-level split** chosen over file-level split for the architecture specs (7 modules: system overview, data model, backend services, connectors, screening/scoring, observability, testing).
- **Requirements pointer pattern** — `requirements/08_automated_system.md` replaced with a concise pointer document linking to architecture specs, preserving traceability.
- **Ownership table** — new `site_ownership` table with 14 columns mapped from GEM ownership CSV, joined to `sites` via `gem_location_id` (preferred) or `gem_unit_id`. Unmatched rows flagged to staging table rather than silently dropped.
- **Audit trail** — `audit/conversations/` and `audit/plans/` folders created with a Cursor rule enforcing logging per IAEA QA 13.1.6.

## Files Changed

- `architecture/specs/00_index.md` — Created: architecture index with S10 traceability map
- `architecture/specs/01_system_overview.md` — Created: objectives, architecture diagram, tech stack, dev process
- `architecture/specs/02_data_model_postgres.md` — Created: PostgreSQL schema, field definitions, ingestion pipeline; later updated with `site_ownership` table and ownership ingestion steps
- `architecture/specs/03_backend_services.md` — Created: pipeline orchestration, CLI, configuration, output generation
- `architecture/specs/04_connector_framework.md` — Created: connector contract, 10 connector specs, caching/retry/rate-limit policies, error taxonomy
- `architecture/specs/05_screening_scoring_engine.md` — Created: exclusionary/avoidance screening, scoring rubrics, composite ranking, sensitivity analysis
- `architecture/specs/06_execution_observability.md` — Created: structured logging, run lifecycle, progress tracking, post-run summary
- `architecture/specs/07_test_validation_strategy.md` — Created: unit/integration/E2E testing, connector contract tests, smoke tests
- `requirements/08_automated_system.md` — Modified: replaced with pointer document to architecture specs
- `requirements/00_index.md` — Modified: updated table of contents and Phase 1 mapping to reference architecture specs
- `audit/README.md` — Created: audit trail conventions and naming rules
- `audit/plans/` — Created: seeded with existing plan files
- `audit/conversations/` — Created: seeded with retroactive logs for prior sessions
- `.cursor/rules/audit-trail.mdc` — Created: always-apply rule enforcing conversation and plan logging

## Outcome

Completed — Architecture specs established (8 files), ownership table added, audit trail operational.
