<!-- man_hours: 3.0 -->
# Man-Hours Summary

**Generated:** 2026-03-24T21:52:03Z  
**Source:** `audit/man_hours_registry.yml`

---

## Totals by Category

| Category | Files | Hours |
| --- | ---: | ---: |
| Requirements & Analysis | 14 | 109.0 |
| Architecture & Design | 8 | 56.5 |
| Implementation | 29 | 166.9 |
| Testing | 10 | 31.1 |
| Database & Migrations | 6 | 16.2 |
| Configuration & DevOps | 6 | 14.0 |
| Research & Data Sources | 10 | 94.0 |
| AI Prompts & Tooling | 1 | 8.0 |
| Project Management & QA | 17 | 19.0 |
| **Project Total** | **101** | **514.8** |

---

## Detailed Breakdown

### Requirements & Analysis

**Subtotal:** 14 files, 109.0 hours

| File | Hours |
| --- | ---: |
| `requirements/01_overview.md` | 32.0 |
| `requirements/05_siting_criteria.md` | 16.0 |
| `requirements/04_siting_methodology.md` | 12.0 |
| `requirements/07_data_requirements.md` | 10.0 |
| `requirements/03_regulatory_framework.md` | 8.0 |
| `requirements/06_scoring_matrix.md` | 6.0 |
| `requirements/09_business_case.md` | 6.0 |
| `requirements/02_deliverables.md` | 4.0 |
| `requirements/10_execution_plan.md` | 4.0 |
| `requirements/00_index.md` | 3.0 |
| `requirements/11_quality_assurance.md` | 3.0 |
| `requirements/08_automated_system.md` | 2.0 |
| `requirements/12_references.md` | 2.0 |
| `requirements/draft_requirements.md` | 1.0 |

### Architecture & Design

**Subtotal:** 8 files, 56.5 hours

| File | Hours |
| --- | ---: |
| `architecture/specs/02_data_model_postgres.md` | 12.0 |
| `architecture/specs/05_screening_scoring_engine.md` | 10.0 |
| `architecture/specs/01_system_overview.md` | 8.0 |
| `architecture/specs/04_connector_framework.md` | 8.0 |
| `architecture/specs/03_backend_services.md` | 6.0 |
| `architecture/specs/06_execution_observability.md` | 6.0 |
| `architecture/specs/07_test_validation_strategy.md` | 5.0 |
| `architecture/specs/00_index.md` | 1.5 |

### Implementation

**Subtotal:** 29 files, 166.9 hours

| File | Hours |
| --- | ---: |
| `src/atoms_vs_ashes/analysis/emergency_plan.py` | 16.0 |
| `src/atoms_vs_ashes/db/models.py` | 16.0 |
| `src/atoms_vs_ashes/analysis/proximity_land.py` | 14.0 |
| `src/atoms_vs_ashes/connectors/corine.py` | 14.0 |
| `src/atoms_vs_ashes/ingest/sites.py` | 14.0 |
| `src/atoms_vs_ashes/analysis/epz_population.py` | 12.0 |
| `src/atoms_vs_ashes/connectors/population.py` | 12.0 |
| `src/atoms_vs_ashes/connectors/osm.py` | 10.0 |
| `src/atoms_vs_ashes/ingest/osm_area.py` | 8.0 |
| `src/atoms_vs_ashes/ingest/ownership.py` | 8.0 |
| `src/atoms_vs_ashes/screening/grid_capacity.py` | 8.0 |
| `src/atoms_vs_ashes/screening/land_area.py` | 6.0 |
| `src/atoms_vs_ashes/screening/base.py` | 5.0 |
| `src/atoms_vs_ashes/cli.py` | 4.0 |
| `src/atoms_vs_ashes/geo.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/quality_report.py` | 4.0 |
| `src/atoms_vs_ashes/pipeline/runner.py` | 4.0 |
| `src/atoms_vs_ashes/config.py` | 3.0 |
| `src/atoms_vs_ashes/db/engine.py` | 2.0 |
| `src/atoms_vs_ashes/logging.py` | 1.5 |
| `src/atoms_vs_ashes/screening/__init__.py` | 0.5 |
| `src/atoms_vs_ashes/connectors/__init__.py` | 0.2 |
| `src/atoms_vs_ashes/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/__main__.py` | 0.1 |
| `src/atoms_vs_ashes/analysis/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/db/README.md` | 0.1 |
| `src/atoms_vs_ashes/db/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/ingest/__init__.py` | 0.1 |
| `src/atoms_vs_ashes/pipeline/__init__.py` | 0.1 |

### Testing

**Subtotal:** 10 files, 31.1 hours

| File | Hours |
| --- | ---: |
| `tests/test_connectors_osm.py` | 6.0 |
| `tests/test_screening_grid_capacity.py` | 5.0 |
| `tests/test_screening_land_area.py` | 5.0 |
| `tests/conftest.py` | 4.0 |
| `tests/test_integration_db.py` | 4.0 |
| `tests/test_ingest_sites.py` | 3.0 |
| `tests/test_models.py` | 2.0 |
| `tests/test_config.py` | 1.0 |
| `tests/test_ingest_ownership.py` | 1.0 |
| `tests/__init__.py` | 0.1 |

### Database & Migrations

**Subtotal:** 6 files, 16.2 hours

| File | Hours |
| --- | ---: |
| `alembic/versions/001_initial_schema.py` | 10.0 |
| `alembic/versions/004_seed_epz_emergency_criteria.py` | 2.5 |
| `alembic/versions/002_seed_screening_criteria.py` | 1.5 |
| `alembic/env.py` | 1.0 |
| `alembic/versions/003_seed_bf02_criterion.py` | 1.0 |
| `alembic/script.py.mako` | 0.2 |

### Configuration & DevOps

**Subtotal:** 6 files, 14.0 hours

| File | Hours |
| --- | ---: |
| `config/default.yml` | 4.0 |
| `.cursor/rules/man-hours.mdc` | 3.0 |
| `scripts/man_hours_report.py` | 3.0 |
| `.cursor/rules/audit-trail.mdc` | 2.0 |
| `pyproject.toml` | 1.5 |
| `docker-compose.yml` | 0.5 |

### Research & Data Sources

**Subtotal:** 10 files, 94.0 hours

| File | Hours |
| --- | ---: |
| `sources/atoms_vs_ashes_data_source_inventory.md` | 40.0 |
| `sources/regulations/epri/maps/EPRI-SitingGuide_map.md` | 8.0 |
| `sources/regulations/iaea/maps/SSG-35_map.md` | 8.0 |
| `sources/regulations/iaea/maps/GSG-10_map.md` | 6.0 |
| `sources/regulations/iaea/maps/SSG-18_map.md` | 6.0 |
| `sources/regulations/iaea/maps/SSG-9_map.md` | 6.0 |
| `sources/regulations/iaea/maps/NS-G-3.6_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSG-21_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSG-79_map.md` | 5.0 |
| `sources/regulations/iaea/maps/SSR-1_map.md` | 5.0 |

### AI Prompts & Tooling

**Subtotal:** 1 files, 8.0 hours

| File | Hours |
| --- | ---: |
| `gpt/expert_system_data_sources_and_integrations.md` | 8.0 |

### Project Management & QA

**Subtotal:** 17 files, 19.0 hours

| File | Hours |
| --- | ---: |
| `audit/plans/SMR_land_area_estimations.md` | 4.0 |
| `audit/plans/grid_capacity_screening_check_1fb3af4b.plan.md` | 3.0 |
| `audit/README.md` | 2.0 |
| `audit/plans/automated_system_architecture_split_e8922903.plan.md` | 1.5 |
| `audit/plans/data_source_pricing_update_3872d49e.plan.md` | 1.5 |
| `audit/plans/split_requirements_by_phase_ace3875d.plan.md` | 1.5 |
| `audit/plans/project_audit_trail_setup_3b3c0d91.plan.md` | 1.0 |
| `audit/conversations/2026-03-11_database-backend-foundation.md` | 0.8 |
| `audit/conversations/2026-03-10_methodology-and-data-pricing.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-expansion.md` | 0.5 |
| `audit/conversations/2026-03-10_requirements-split.md` | 0.5 |
| `audit/conversations/2026-03-11_architecture-split-and-ownership.md` | 0.5 |
| `audit/conversations/2026-03-11_bf01-grid-capacity-screening.md` | 0.5 |
| `audit/conversations/2026-03-24_gpt-pro-expert-prompt-data-sources.md` | 0.5 |
| `audit/conversations/2026-03-11_process-diagram.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-architecture.md` | 0.2 |
| `audit/conversations/2026-03-24_aggregated-requirements.md` | 0.2 |

---

*Report generated by `scripts/man_hours_report.py` at 2026-03-24T21:52:03Z*
