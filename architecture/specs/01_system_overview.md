# 1. System Overview

## 1.1 Purpose

This document defines the high-level architecture, objectives, technology stack, and development process for the Automated Site Evaluation System.

**Traceability:** Requirements S10.1, S10.2, S10.7, S10.8.

---

## 1.2 System Objectives

The automated evaluation system shall:

1. Programmatically manage the power plant database and site attributes.
2. Connect to external data APIs to retrieve criterion-specific data for each site.
3. Apply the screening criteria and scoring matrix algorithmically.
4. Generate reproducible site evaluation outputs and ranking tables.
5. Enable rapid re-evaluation when data is updated or criteria weights are adjusted.

---

## 1.3 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     AUTOMATED EVALUATION SYSTEM                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  DATA LAYER │    │  PROCESSING     │    │  OUTPUT LAYER   │  │
│  │             │    │  LAYER          │    │                 │  │
│  │ PostgreSQL  │───▶│  Screening      │───▶│  Ranked site    │  │
│  │ Database    │    │  Engine         │    │  list (CSV/JSON)│  │
│  │             │    │                 │    │                 │  │
│  │ - Sites     │    │  Scoring Engine │    │  Site profile   │  │
│  │ - Criteria  │    │                 │    │  reports (MD)   │  │
│  │ - Scores    │    │  Sensitivity    │    │                 │  │
│  │ - Metadata  │    │  Analyser       │    │  Scoring matrix │  │
│  └──────┬──────┘    └────────┬────────┘    │  export (XLSX)  │  │
│         │                    │             │                 │  │
│  ┌──────▼──────┐    ┌────────▼────────┐    │  Maps (GeoJSON/ │  │
│  │  API        │    │  Validation &   │    │  HTML)          │  │
│  │  CONNECTORS │    │  Web Search     │    └─────────────────┘  │
│  │             │    │  Update Module  │                          │
│  │ - GEM/USGS  │    │                 │                          │
│  │ - Copernicus│    │ - Verify plant  │                          │
│  │ - CDS/ERA5  │    │   status        │                          │
│  │ - Eurostat  │    │ - Update attrs  │                          │
│  │ - OSM       │    │ - Log changes   │                          │
│  │ - ENTSO-E   │    └─────────────────┘                          │
│  │ - WorldPop  │                                                 │
│  │ - WDPA      │                                                 │
│  └─────────────┘                                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer            | Responsibility                                                                    | Detailed Spec                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Data Layer       | PostgreSQL + PostGIS; stores sites, criteria, scores, metadata, audit logs        | [02_data_model_postgres.md](02_data_model_postgres.md)                                                             |
| API Connectors   | Independent modules retrieving external geospatial/environmental/demographic data | [04_connector_framework.md](04_connector_framework.md)                                                             |
| Processing Layer | Screening, scoring, sensitivity analysis; validation module                       | [05_screening_scoring_engine.md](05_screening_scoring_engine.md), [03_backend_services.md](03_backend_services.md) |
| Output Layer     | Ranked lists, site profiles, scoring exports, maps                                | [03_backend_services.md](03_backend_services.md)                                                                   |

---

## 1.4 Technology Stack

| Layer                 | Technology                            | Rationale                                           |
| --------------------- | ------------------------------------- | --------------------------------------------------- |
| Database              | PostgreSQL 16+ with PostGIS extension | Mature RDBMS with native geospatial support         |
| Backend Language      | Python 3.11+                          | Extensive geospatial, scientific, and API ecosystem |
| ORM / DB Access       | SQLAlchemy + psycopg2                 | Industry-standard Python-PostgreSQL interface       |
| Geospatial Processing | GeoPandas, Shapely, Rasterio          | Geospatial analysis and raster data handling        |
| API Clients           | requests, cdsapi, OWSLib              | HTTP and OGC service clients                        |
| Data Processing       | pandas, numpy                         | Tabular data manipulation and numerical computation |
| Visualisation         | folium, matplotlib                    | Interactive maps and static charts                  |
| Reporting             | Jinja2 + markdown                     | Templated report generation                         |
| Configuration         | YAML / environment variables          | Configurable thresholds, weights, API keys          |
| Testing               | pytest                                | Unit and integration testing                        |
| Version Control       | Git                                   | All code and configuration under version control    |

---

## 1.5 Software Development Process

Development shall follow established software engineering practices:

1. **Requirements analysis:** The requirements specification (`requirements/`) serves as the system requirements baseline.
2. **Architecture design:** This `architecture/specs/` directory documents component boundaries, API interface definitions, and database schema.
3. **Implementation:** Modular development with clear separation of concerns. Each module is independently testable.
4. **Testing:** See [07_test_validation_strategy.md](07_test_validation_strategy.md) for the full testing approach.
5. **Documentation:** Code documentation, API usage guide, and deployment instructions shall be maintained alongside the codebase.

---

## 1.6 Interfaces Between Modules

| Producer                | Consumer                                        | Data Contract                                       |
| ----------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Data ingestion pipeline | PostgreSQL `sites` table                        | Normalised site records with audit trail            |
| Connector framework     | PostgreSQL `site_attributes`, `site_scores`     | Typed attribute values with provenance metadata     |
| Screening engine        | PostgreSQL `screening_results`                  | Pass/fail per criterion per site with justification |
| Scoring engine          | PostgreSQL `ranking_results`                    | Composite scores per site                           |
| Output generators       | Filesystem (CSV, JSON, MD, XLSX, GeoJSON, HTML) | Reproducible report artifacts per run               |
