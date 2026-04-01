<!-- man_hours: 2.0 -->
## 10. Automated Site Evaluation System

> **This section has been expanded into detailed architecture specifications.**
> The full technical design is maintained in [`architecture/specs/`](../architecture/specs/00_index.md).

### Summary

An automated evaluation system shall be developed to programmatically manage the power plant database, connect to external data APIs, apply screening criteria and scoring matrices, and generate reproducible site evaluation outputs and ranking tables.

### Architecture Specification Files

| Spec                                                                                   | Scope                                                                      |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| [01_system_overview.md](../architecture/specs/01_system_overview.md)                   | Objectives, high-level architecture, technology stack, development process |
| [02_data_model_postgres.md](../architecture/specs/02_data_model_postgres.md)           | Database schema, field definitions, ingestion pipeline, data quality       |
| [03_backend_services.md](../architecture/specs/03_backend_services.md)                 | Pipeline orchestration, configuration management, CLI entry points         |
| [04_connector_framework.md](../architecture/specs/04_connector_framework.md)           | API connector contracts, per-connector specs, caching, retry policies      |
| [05_screening_scoring_engine.md](../architecture/specs/05_screening_scoring_engine.md) | Exclusionary/avoidance screens, scoring, ranking, sensitivity analysis     |
| [06_execution_observability.md](../architecture/specs/06_execution_observability.md)   | Structured logging, run lifecycle, error handling, post-run reporting      |
| [07_test_validation_strategy.md](../architecture/specs/07_test_validation_strategy.md) | Unit, integration, and end-to-end testing; manual cross-validation         |

### Traceability

The original content of this document (S10.1–S10.8) maps to the architecture specs as follows:

| Original Subsection               | Architecture File(s)                                   |
| --------------------------------- | ------------------------------------------------------ |
| 10.1 System Objectives            | 01_system_overview                                     |
| 10.2 Architecture                 | 01_system_overview                                     |
| 10.3 Power Plant Database         | 02_data_model_postgres                                 |
| 10.4 Data Validation Module       | 03_backend_services (noted: not required at this time) |
| 10.5 API Connector Framework      | 04_connector_framework                                 |
| 10.6 Screening and Scoring Engine | 05_screening_scoring_engine                            |
| 10.7 Technology Stack             | 01_system_overview                                     |
| 10.8 Software Development Process | 01_system_overview, 07_test_validation_strategy        |
