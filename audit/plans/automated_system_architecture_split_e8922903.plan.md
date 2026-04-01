<!-- man_hours: 1.5 -->
---
name: Automated System Architecture Split
overview: Restructure the automated system requirement into a dedicated architecture specification set under `architecture/specs`, while preserving requirements traceability via a lightweight pointer file in `requirements`.
todos:
  - id: create-arch-spec-folder
    content: Create `architecture/specs` and add architecture index plus 7 module-level spec files with consistent template sections.
    status: completed
  - id: migrate-s10-content
    content: Migrate and split content from `requirements/08_automated_system.md` into the new architecture files with clear ownership by module.
    status: completed
  - id: add-traceability-map
    content: Add S10 subsection-to-file traceability mapping in `architecture/specs/00_index.md`.
    status: completed
  - id: requirements-pointer
    content: Replace `requirements/08_automated_system.md` with a concise pointer document to architecture specs.
    status: completed
  - id: update-requirements-index
    content: Update `requirements/00_index.md` wording to indicate S10 technical detail now resides under `architecture/specs`.
    status: completed
  - id: review-consistency
    content: Run a documentation consistency pass for naming, cross-links, and non-duplication between requirements and architecture docs.
    status: completed
isProject: false
---

# Move And Split Automated System Spec

## Goal

Convert the current single document `[requirements/08_automated_system.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/08_automated_system.md)` into a maintainable architecture spec set under `[architecture/specs](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs)` using module-level boundaries aligned with implementation domains (DB, backend, connectors, scoring, operations).

## Target Structure

Create these files:

- `[architecture/specs/00_index.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/00_index.md)`
- `[architecture/specs/01_system_overview.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/01_system_overview.md)`
- `[architecture/specs/02_data_model_postgres.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/02_data_model_postgres.md)`
- `[architecture/specs/03_backend_services.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/03_backend_services.md)`
- `[architecture/specs/04_connector_framework.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/04_connector_framework.md)`
- `[architecture/specs/05_screening_scoring_engine.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/05_screening_scoring_engine.md)`
- `[architecture/specs/06_execution_observability.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/06_execution_observability.md)`
- `[architecture/specs/07_test_validation_strategy.md](/Users/terbolence/projects/snn/atoms_vs_ashes/architecture/specs/07_test_validation_strategy.md)`

Update these existing files:

- `[requirements/08_automated_system.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/08_automated_system.md)` → replace with short pointer/traceability note to `architecture/specs/*`.
- `[requirements/00_index.md](/Users/terbolence/projects/snn/atoms_vs_ashes/requirements/00_index.md)` → keep current table row, but clarify that section S10 details live in architecture specs.

## Content Allocation Rules

- Preserve original intent and requirements language, but relocate implementation detail to architecture files.
- Keep each architecture file focused on one responsibility with:
  - purpose/scope
  - component boundaries and interfaces
  - inputs/outputs and data contracts
  - non-functional requirements (performance, reliability, traceability)
  - acceptance criteria and test hooks
- Add a traceability section in `architecture/specs/00_index.md` mapping old S10 subsections to new files.

## Gold-Standard Additions (Within Existing Scope)

- Define canonical module contracts for connectors (request policy, retries, caching, validation, persistence).
- Add explicit run observability requirements (structured logs, run IDs, error taxonomy, summary artifacts).
- Separate unit/integration/e2e validation responsibilities into a dedicated testing spec.
- Keep architecture docs implementation-ready without prematurely locking exact code filenames.

## Acceptance Checks

- Every section of original `08_automated_system.md` is represented in at least one `architecture/specs` file.
- Requirements index remains navigable and traceable.
- No duplication between requirements and architecture docs beyond the pointer and minimal context.
- New structure supports iterative refinement of DB, backend, connectors, and scoring independently.
