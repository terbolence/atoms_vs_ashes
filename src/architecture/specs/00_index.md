<!-- man_hours: 1.5 -->
# Architecture Specifications — Index

**Project:** SMR Siting Assessment — Automated Site Evaluation System

**Source Requirement:** `requirements/08_automated_system.md` (Section 10)

**Version:** 1.0

**Date:** March 2026

---

## Specification Files

| File                                                             | Module                       | Scope                                                                                     |
| ---------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------- |
| [01_system_overview.md](01_system_overview.md)                   | System Overview              | Objectives, high-level architecture, technology stack, development process                |
| [02_data_model_postgres.md](02_data_model_postgres.md)           | Data Model (PostgreSQL)      | Schema design, field definitions, ingestion pipeline, data quality                        |
| [03_backend_services.md](03_backend_services.md)                 | Backend Services             | Pipeline orchestration, configuration management, CLI entry points                        |
| [04_connector_framework.md](04_connector_framework.md)           | Connector Framework          | API connector contracts, per-connector specs, caching, retry policies                     |
| [05_screening_scoring_engine.md](05_screening_scoring_engine.md) | Screening and Scoring Engine | Exclusionary/avoidance screens, score assignment, composite ranking, sensitivity analysis |
| [06_execution_observability.md](06_execution_observability.md)   | Execution and Observability  | Structured logging, run lifecycle, error taxonomy, post-run reporting                     |
| [07_test_validation_strategy.md](07_test_validation_strategy.md) | Test and Validation Strategy | Unit, integration, and end-to-end testing; manual cross-validation                        |

---

## Traceability to Requirements (Section 10)

| Requirements Subsection                        | Architecture File(s)                                                                                             |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 10.1 System Objectives                         | [01_system_overview.md](01_system_overview.md)                                                                   |
| 10.2 Architecture                              | [01_system_overview.md](01_system_overview.md)                                                                   |
| 10.3 Component 1: Power Plant Database         | [02_data_model_postgres.md](02_data_model_postgres.md)                                                           |
| 10.4 Component 2: Data Validation Module       | [03_backend_services.md](03_backend_services.md) (noted: not required at this time)                              |
| 10.5 Component 3: API Connector Framework      | [04_connector_framework.md](04_connector_framework.md)                                                           |
| 10.6 Component 4: Screening and Scoring Engine | [05_screening_scoring_engine.md](05_screening_scoring_engine.md)                                                 |
| 10.7 Technology Stack                          | [01_system_overview.md](01_system_overview.md)                                                                   |
| 10.8 Software Development Process              | [01_system_overview.md](01_system_overview.md), [07_test_validation_strategy.md](07_test_validation_strategy.md) |

---

## Cross-References

- Requirements index: `requirements/00_index.md`
- Siting criteria (inputs to screening): `requirements/05_siting_criteria.md`
- Scoring matrix (inputs to scoring engine): `requirements/06_scoring_matrix.md`
- Data requirements (inputs to connectors): `requirements/07_data_requirements.md`
