# Aggregated architecture specifications

**Generated:** 2026-03-24  
**Source folder:** `architecture/specs/`  

This file concatenates all Markdown architecture specification files for convenience. The canonical, maintained sources remain the individual files under `architecture/specs/`. Relative links inside embedded sections are unchanged from the originals.

---

## Included files (order)

- `architecture/specs/00_index.md`
- `architecture/specs/01_system_overview.md`
- `architecture/specs/02_data_model_postgres.md`
- `architecture/specs/03_backend_services.md`
- `architecture/specs/04_connector_framework.md`
- `architecture/specs/05_screening_scoring_engine.md`
- `architecture/specs/06_execution_observability.md`
- `architecture/specs/07_test_validation_strategy.md`

---

## Source: `architecture/specs/00_index.md`

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

---

## Source: `architecture/specs/01_system_overview.md`

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
| Connector framework     | PostgreSQL domain tables (natural/human/radio/EP/infra) | Typed attribute values with provenance metadata     |
| Screening engine        | PostgreSQL `screening_verdicts`                 | Pass/fail/caution per criterion per site per SMR design |
| Scoring engine          | PostgreSQL `ranking_scores`, `composite_rankings` | Per-criterion and composite scores per site per SMR |
| Output generators       | Filesystem (CSV, JSON, MD, XLSX, GeoJSON, HTML) | Reproducible report artifacts per run               |

---

## Source: `architecture/specs/02_data_model_postgres.md`

# 2. Data Model — PostgreSQL

## 2.1 Purpose

This document specifies the PostgreSQL database schema, field definitions, data ingestion pipeline, and data quality requirements for the site evaluation system.

**Traceability:** Requirements S10.3.

---

## 2.2 Schema Overview

```sql
-- Core tables
sites                  -- Primary site records
site_ownership         -- Ownership stakes per site (from GEM ownership CSV)
criteria               -- Criterion definitions and weights
smr_designs            -- SMR reactor designs (NuScale, BWRX-300, etc.)

-- Domain tables (one row per site, typed columns per criterion)
site_natural_hazards   -- NH-01..NH-14: seismic, geological, flood, volcano, etc.
site_human_hazards     -- HI-01..HI-08: aviation, military, industrial, etc.
site_radiological      -- RI-01..RI-06: population density, geology for disposal
site_emergency_planning-- EP-01..EP-05: road access, amenities, waterways
site_infrastructure_v2 -- NS-01..NS-13: grid, cooling, land, transport

-- Decision tables (per site × per SMR design)
screening_verdicts     -- Pass/fail/caution/inconclusive per criterion per SMR
ranking_scores         -- 1–5 score per criterion per SMR with score_low/score_high
composite_rankings     -- Weighted composite score and rank per SMR

-- Observations and audit
site_observations      -- Structured comments per site per criterion
countries              -- Country metadata and regulatory info
data_sources           -- Data provenance tracking
audit_log              -- Change tracking for all updates
```

**Extensions required:** PostGIS (geometry/geography types, spatial indexing).

---

## 2.3 Core Fields — `sites` Table

The site database must encompass both essential siting attributes and extended metadata drawn from the Global Coal Plant Tracker (`sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx`).

| Field                 | Type         | Description                                      |
| --------------------- | ------------ | ------------------------------------------------ |
| site_id               | UUID         | Unique identifier for the site                   |
| name                  | VARCHAR      | Plant or site name (preferred value from source) |
| alternative_names     | VARCHAR[]    | Other plant names/local names (array)            |
| country_code          | CHAR(2)      | ISO 3166-1 alpha-2 code                          |
| country_name          | VARCHAR      | Full country name (from source)                  |
| latitude              | DECIMAL(9,6) | WGS84 latitude                                   |
| longitude             | DECIMAL(9,6) | WGS84 longitude                                  |
| location_accuracy     | VARCHAR      | Accuracy descriptor per data source              |
| local_area            | VARCHAR      | Smallest admin region (e.g., county, taluk)      |
| subnational_unit      | VARCHAR      | Province/state                                   |
| region                | VARCHAR      | Region/grouping (from source)                    |
| plant_type            | ENUM         | Coal, Lignite, Gas, Thermal, Other               |
| installed_capacity_mw | DECIMAL      | Current or historical installed capacity (MW)    |
| status                | ENUM         | Operating, Retired, Planned_Closure              |
| start_year            | INTEGER      | Commissioning/start year                         |
| retired_year          | INTEGER      | Year of full retirement (if applicable)          |
| planned_retirement    | DATE         | Official/planned closure date if available       |
| coal_phaseout_year    | INTEGER      | Scheduled year for phaseout per plan             |
| grid_voltage_kv       | INTEGER      | Transmission connection voltage (if available)   |
| grid_capacity_mw      | DECIMAL      | Estimated available export capacity              |
| cooling_water_source  | VARCHAR      | River/lake/sea/cooling tower name                |
| site_area_ha          | DECIMAL      | Available site area in hectares                  |
| elevation_m           | DECIMAL      | Site elevation above mean sea level              |
| owner_operator        | VARCHAR      | Current owner/operator                           |
| parent_company        | VARCHAR      | Parent entity if applicable                      |
| combustion_technology | VARCHAR      | Boiler or combustion process type                |
| coal_type             | VARCHAR      | Coal grade e.g. lignite, bituminous              |
| coal_source           | VARCHAR      | Mine or region source                            |
| net_zero_year         | INTEGER      | Net-zero target year if declared                 |
| location              | VARCHAR      | Text location description                        |
| permits               | VARCHAR      | Permit reference(s) if present                   |
| permit_date           | DATE         | Date of most recent permit (if parsed)           |
| owner_gem_id          | VARCHAR      | Owner GEM entity ID (if present)                 |
| parent_gem_id         | VARCHAR      | Parent GEM entity ID (if present)                |
| gem_unit_phase_id     | VARCHAR      | GEM unit/phase ID (source row key)               |
| gem_location_id       | VARCHAR      | GEM location ID                                  |
| wiki_url              | VARCHAR      | Wikipedia URL if present                         |
| last_verified         | TIMESTAMP    | Last data verification date                      |

---

## 2.4 Extended Data

Store as JSONB or relational columns as appropriate:

- Conversion to (fuel/type/GEM unit ID)
- Alternate fuel(s)
- Subregion, major area
- Captive (boolean), captive industry and residential use
- CHP (combined heat/power) and capacity factor
- Plant age, heat rate, emission factor
- Annual and lifetime CO₂ estimates (as available)
- Remaining plant lifetime estimate
- "China capacity payment recipient" (specific markets)
- Data provenance: for each field, original source and extraction date

> All provided columns from the original GEM tracker should be ingested and stored to support traceability, extended analytics, and downstream enrichment, even if not mapped to the current core siting model.

---

## 2.5 Ownership Data — `site_ownership` Table

A separate ownership table captures the corporate ownership structure for each plant/unit. One site may have multiple ownership rows (one per stakeholder in the ownership chain).

**Source:** GEM ownership dataset, ingested from CSV.

| Field                  | Type    | Source Column                                  | Description                                                  |
| ---------------------- | ------- | ---------------------------------------------- | ------------------------------------------------------------ |
| ownership_id           | UUID    | (generated)                                    | Primary key                                                  |
| site_id                | UUID    | (joined via `gem_location_id` / `gem_unit_id`) | FK to `sites`                                                |
| parent_gem_entity_id   | VARCHAR | Parent GEM Entity ID                           | GEM identifier for the parent entity                         |
| parent_name            | VARCHAR | Parent                                         | Parent company name                                          |
| parent_reg_country     | VARCHAR | Parent Registration Country                    | Country where the parent entity is registered                |
| parent_hq_country      | VARCHAR | Parent Headquarters Country                    | Country where the parent entity is headquartered             |
| project                | VARCHAR | Project                                        | Project or plant name as recorded in the ownership dataset   |
| share_pct              | DECIMAL | Share                                          | Ownership share (percentage)                                 |
| ownership_path         | VARCHAR | Ownership Path                                 | Full chain describing how the parent relates to the project  |
| immediate_owner        | VARCHAR | Immediate Project Owner                        | Direct owner of the project                                  |
| immediate_owner_gem_id | VARCHAR | Immediate Project Owner GEM Entity ID          | GEM identifier for the immediate owner                       |
| tracker                | VARCHAR | Tracker                                        | Source tracker identifier (e.g. "Global Coal Plant Tracker") |
| status                 | VARCHAR | Status                                         | Plant status as recorded in the ownership dataset            |
| capacity_mw            | DECIMAL | Capacity (MW)                                  | Capacity as recorded in the ownership dataset                |
| gem_location_id        | VARCHAR | GEM location ID                                | Join key to `sites.gem_location_id`                          |
| gem_unit_id            | VARCHAR | GEM unit ID                                    | GEM unit-level identifier                                    |

**Join strategy:** Link to `sites` via `gem_location_id` (preferred) or `gem_unit_id` → `sites.gem_unit_phase_id`. Where neither matches, flag the row for manual review.

**Design notes:**

- A single site will typically have multiple ownership rows representing different stakeholders and ownership paths.
- `share_pct` values across all rows for a given site/unit should sum to approximately 100%, but this is not enforced as a hard constraint (partial data is common).
- `status` and `capacity_mw` in this table may differ from the `sites` table if the ownership dataset was snapshotted at a different time; the `sites` table is authoritative for siting purposes.

---

## 2.6 Design Notes

- Where multiple similar fields exist (e.g. name, local name, other name), store all for completeness.
- For optional/nullable fields, use NULL or default per SQL conventions.
- Extended fields should be accessible to downstream site profiling and audit logging.
- Consider partitioning bulky unstructured fields (e.g. raw tracker row as JSONB) for reproducibility.

---

## 2.7 Ingestion Pipeline

### 2.7.1 Source Data

| Source                       | Format                                                                                 | Target Table(s)                    |
| ---------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------- |
| Global Coal Plant Tracker    | XLSX (`sources/global_coal_plant_tracker/Global-Coal-Plant-Tracker-January-2026.xlsx`) | `sites`, domain tables             |
| GEM Ownership Dataset        | CSV                                                                                    | `site_ownership`                   |
| Beyond Fossil Fuels Database | CSV                                                                                    | `sites` (supplementary attributes) |

### 2.7.2 Site Ingestion Steps

1. **Download** — Global Coal Plant Tracker (CSV/XLSX) and Beyond Fossil Fuels database (CSV). Already available at source path above.
2. **Filter** — Ingest only entries for countries within the defined region: Poland, Czech Republic, Slovakia, Hungary, Austria, Slovenia, Croatia, Bosnia and Herzegovina, Serbia, Montenegro, Kosovo, Albania, North Macedonia, Romania, Bulgaria, Moldova, Ukraine, Belarus, Estonia, Latvia, Lithuania, Armenia, and Turkey.
3. **Parse, deduplicate, normalise** — Performed in code after the database structure is defined, not in Excel.
4. **Geocoordinate verification** — Confirm geocoordinates are present for all records. No geocoding needed unless additional sites without coordinates are identified later.
5. **Supplementary sites** — Manually add the two Romanian supplementary sites (Braila-Chiscani, FPCU Feldioara), ensuring their attributes align with the field mappings of other records.
6. **Load** — Insert prepared dataset into PostgreSQL with full audit logging for all data ingestion steps.
7. **Data quality report** — Generate a report focused on completeness, field-level consistency, and regional coverage, to verify that all required plants/sites in the defined countries are included.

### 2.7.3 Ownership Ingestion Steps

1. **Load CSV** — Read the GEM ownership CSV.
2. **Filter** — Retain only rows whose `GEM location ID` matches a `gem_location_id` in the `sites` table (i.e. plants within the in-scope region).
3. **Map columns** — Map CSV headers to `site_ownership` fields per the table in section 2.5.
4. **Join to sites** — Resolve `site_id` foreign key via `gem_location_id` (preferred) or `gem_unit_id` → `sites.gem_unit_phase_id`.
5. **Flag unmatched rows** — Ownership rows that cannot be joined to any site are logged as warnings and stored in a `_staging_unmatched_ownership` table for manual review.
6. **Load** — Insert matched ownership records into `site_ownership` with audit logging.
7. **Validation** — Verify that every site with ownership data has at least one ownership row, and that `share_pct` values per site/unit are plausible (warn if sum deviates significantly from 100%).

### 2.7.4 Audit Logging

Every ingestion step shall write to the `audit_log` table with:

- Timestamp
- Operation type (insert, update, delete, deduplicate)
- Affected `site_id`(s)
- Before/after values for updates
- Source file and row reference

---

## 2.8 Acceptance Criteria

- All in-scope countries are represented with at least one site record.
- Zero records with missing latitude/longitude after ingestion.
- All GEM tracker columns are stored (core fields or JSONB extended data).
- Ownership records are linked to sites via GEM location/unit IDs; unmatched rows are flagged, not silently dropped.
- Data quality report can be regenerated at any time from the loaded data.
- Audit log captures every mutation with full provenance.

---

## Source: `architecture/specs/03_backend_services.md`

# 3. Backend Services

## 3.1 Purpose

This document specifies the backend orchestration layer: pipeline coordination, configuration management, CLI entry points, output generation, and the data validation module.

**Traceability:** Requirements S10.4, S10.7, S10.8 (items 1–3).

---

## 3.2 Pipeline Orchestration

The backend provides the top-level execution flow that ties all modules together.

### 3.2.1 Pipeline Stages

```
Ingest → Enrich (connectors) → Screen → Score → Rank → Report
```

| Stage      | Description                                                    | Upstream Dependency                     |
| ---------- | -------------------------------------------------------------- | --------------------------------------- |
| **Ingest** | Load and normalise source data into PostgreSQL                 | Source files on disk                    |
| **Enrich** | Run connector framework to populate site attributes            | Ingested site records                   |
| **Screen** | Apply exclusionary and avoidance criteria                      | Enriched site attributes                |
| **Score**  | Compute criterion scores and composite ranking                 | Screening results + enriched attributes |
| **Rank**   | Sort sites by composite score, apply sensitivity analysis      | Scored sites                            |
| **Report** | Generate output artifacts (CSV, JSON, MD, XLSX, GeoJSON, HTML) | Ranked results                          |

### 3.2.2 Execution Modes

The CLI shall support:

- **Full run** — Execute all stages end-to-end.
- **Stage-selective run** — Execute from a specified stage onward (e.g. re-score without re-ingesting).
- **Dry run** — Validate configuration and report what would be executed without making changes.
- **Single-site run** — Execute pipeline for one site (useful for debugging and validation).

---

## 3.3 Configuration Management

All tuneable parameters shall be externalised in YAML configuration files and/or environment variables:

| Category             | Examples                                   | Storage               |
| -------------------- | ------------------------------------------ | --------------------- |
| Database connection  | Host, port, credentials, database name     | Environment variables |
| API keys             | CDS, ENTSO-E, etc.                         | Environment variables |
| Screening thresholds | Distance buffers, magnitude cutoffs        | YAML                  |
| Scoring rubrics      | Score bands per criterion                  | YAML                  |
| Criterion weights    | Weight per criterion for composite scoring | YAML                  |
| Cache policy         | TTL per connector (default: 30 days)       | YAML                  |
| Retry policy         | Max retries, backoff base/cap              | YAML                  |

Sensitive values (credentials, API keys) shall never appear in YAML files or version control.

---

## 3.4 CLI Interface

Entry point: a single CLI command (e.g. `python -m atoms_vs_ashes`) with subcommands:

| Subcommand | Description                                       |
| ---------- | ------------------------------------------------- |
| `ingest`   | Run data ingestion pipeline                       |
| `enrich`   | Run connector framework for all or selected sites |
| `screen`   | Run exclusionary and avoidance screening          |
| `score`    | Compute scores and rankings                       |
| `report`   | Generate output artifacts                         |
| `run`      | Execute full pipeline (ingest through report)     |
| `validate` | Run configuration and data quality checks         |

Common flags: `--config <path>`, `--dry-run`, `--site-id <uuid>`, `--verbose`, `--run-id <id>`.

---

## 3.5 Output Generation

### 3.5.1 Artifacts

| Artifact              | Format                 | Content                                                      |
| --------------------- | ---------------------- | ------------------------------------------------------------ |
| Ranked site list      | CSV, JSON              | All candidate sites with composite scores and ranks          |
| Site profile reports  | Markdown               | Per-site detailed evaluation with all criterion results      |
| Scoring matrix export | XLSX                   | Full matrix: sites x criteria with scores and weights        |
| Maps                  | GeoJSON, HTML (folium) | Spatial visualisation of site locations and scores           |
| Run summary           | Markdown               | Pipeline execution metadata, connector health, error summary |

### 3.5.2 Reproducibility

Every run shall produce artifacts tagged with a `run_id` and timestamp. Previous outputs shall be preserved (not overwritten) unless explicitly requested.

---

## 3.6 Data Validation Module

> **Note:** The web-search-based validation module described in requirements S10.4 is not required at this time, as the source data is already current. This section documents the interface for future activation.

If activated, this module would:

1. Query web sources to verify plant operational status.
2. Update site attributes where discrepancies are found.
3. Log all changes to the audit trail.

The module interface shall be defined so it can be plugged in later without modifying the pipeline orchestration.

---

## 3.7 Acceptance Criteria

- Full pipeline can be executed via a single CLI command.
- Individual stages can be run independently.
- Configuration changes (weights, thresholds) do not require code changes.
- All outputs are tagged with run metadata for traceability.

---

## Source: `architecture/specs/04_connector_framework.md`

# 4. Connector Framework

## 4.1 Purpose

This document specifies the API connector framework: the common contract all connectors must follow, per-connector specifications, and cross-cutting concerns (caching, retries, rate limiting, validation, provenance).

**Traceability:** Requirements S10.5.

---

## 4.2 Connector Contract

Every connector shall be implemented as an independent, testable module conforming to a common interface.

### 4.2.1 Interface

Each connector must implement:

| Method                          | Responsibility                                                          |
| ------------------------------- | ----------------------------------------------------------------------- |
| `fetch(site) → RawResponse`     | Retrieve data from external API for a given site (lat/lon + parameters) |
| `validate(raw) → ValidatedData` | Apply schema and quality checks to raw response                         |
| `persist(validated, site_id)`   | Store validated data in PostgreSQL with provenance metadata             |
| `health_check() → Status`       | Verify API reachability and authentication before a batch run           |

### 4.2.2 Data Flow

```
Site record (lat, lon, params)
    │
    ▼
┌──────────┐     cache hit?     ┌───────────┐
│  fetch() │────── yes ────────▶│ return    │
│          │                    │ cached    │
│          │────── no ─────┐    └───────────┘
└──────────┘               │
                           ▼
                   ┌──────────────┐
                   │ External API │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ validate()   │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ persist()    │
                   └──────────────┘
```

---

## 4.3 Cross-Cutting Requirements

### 4.3.1 Caching

- All API responses shall be cached with configurable expiration (default: 30 days).
- Cache key: connector name + site_id + query parameters hash.
- Cache storage: PostgreSQL table or local filesystem (configurable).
- Stale cache may be used as fallback when the API is unreachable, with a data quality flag set.

### 4.3.2 Retry and Backoff

- Failed requests shall be retried with exponential backoff.
- Default policy: max 3 retries, base delay 2 s, maximum delay 60 s, jitter enabled.
- Per-connector override via YAML configuration.
- After all retries are exhausted, the failure is logged and the site is flagged for manual review.

### 4.3.3 Rate Limiting

- Each connector shall respect the target API's rate limits.
- A configurable requests-per-second cap shall be enforced per connector.
- Batch runs shall process sites with concurrent workers per connector, bounded by the rate limit.

### 4.3.4 Validation

- Each connector shall define an expected response schema (required fields, types, value ranges).
- Responses failing validation are logged as data quality issues, not silently discarded.
- Partial data (e.g. some fields present, others missing) shall be stored with appropriate quality flags.

### 4.3.5 Provenance

- Every stored data point shall record:
  - Source API and endpoint
  - Request timestamp
  - Response timestamp
  - Cache status (fresh / cached / stale-fallback)
  - Connector version
  - Run ID

---

## 4.4 Connector Specifications

| Connector          | Target API                       | Data Retrieved                                   | Protocol          | Query Parameters                       |
| ------------------ | -------------------------------- | ------------------------------------------------ | ----------------- | -------------------------------------- |
| Seismic            | USGS Earthquake API + GEM/SHARE  | Historical earthquakes within 300 km, PGA values | REST/JSON         | lat, lon, radius 300 km, min magnitude |
| Flood              | EU Floods Directive WMS/WFS      | Flood zones intersecting 5 km buffer             | OGC WMS/WFS       | bbox from site + 5 km buffer           |
| Meteorology        | Copernicus CDS API (ERA5)        | Temperature, wind, precipitation extremes        | CDS API (Python)  | lat, lon, date range, variables        |
| Population         | WorldPop / Eurostat GISCO        | Population within 5/16/25/80 km radii            | GeoTIFF + REST    | lat, lon, radius set                   |
| Protected Areas    | WDPA API + Natura 2000           | Protected areas within 10 km                     | REST/GIS          | lat, lon, radius 10 km                 |
| Land Use           | CORINE WMS                       | Land cover classification at site                | OGC WMS           | point or small bbox at site            |
| Grid               | ENTSO-E Transparency API         | Nearest substation, capacity data                | REST/XML          | area code or lat/lon                   |
| Volcano            | Smithsonian GVP                  | Holocene volcanoes within 300 km                 | Web scraping/JSON | lat, lon, radius 300 km                |
| Industrial Hazards | SEVESO Directive registers + OSM | SEVESO facilities within 10 km                   | Mixed             | lat, lon, radius 10 km                 |
| Transport          | OSM Overpass API                 | Road/rail/waterway within 5 km                   | REST/JSON         | bbox or radius query                   |

---

## 4.5 Error Taxonomy

| Error Class      | Examples                                      | Handling                                          |
| ---------------- | --------------------------------------------- | ------------------------------------------------- |
| `TransientError` | Timeout, HTTP 429/503                         | Retry with backoff                                |
| `AuthError`      | HTTP 401/403, expired token                   | Log, halt connector, alert                        |
| `SchemaError`    | Unexpected response format                    | Log, flag data quality, store partial if possible |
| `NotFoundError`  | No data for location (HTTP 404, empty result) | Store "no data" result with flag                  |
| `RateLimitError` | Quota exceeded                                | Back off, resume after cooldown                   |

---

## 4.6 Acceptance Criteria

- Each connector can be run independently against a single site and produce valid output.
- Health checks pass for all connectors before a batch run proceeds.
- Cached responses are served without hitting external APIs when within TTL.
- All error classes are handled and logged with appropriate severity.
- Provenance metadata is present for every persisted data point.

---

## Source: `architecture/specs/05_screening_scoring_engine.md`

# 5. Screening and Scoring Engine

## 5.1 Purpose

This document specifies the screening, scoring, ranking, and sensitivity analysis components of the evaluation system.

**Traceability:** Requirements S10.6.

**Upstream references:**

- Siting criteria definitions: `requirements/05_siting_criteria.md`
- Scoring matrix and weighting: `requirements/06_scoring_matrix.md`

---

## 5.2 Exclusionary Screening

### 5.2.1 Objective

For each site, evaluate all exclusionary criteria (E1–E9). Any site failing one or more exclusionary criteria is flagged as **"Excluded"** and removed from further scoring.

### 5.2.2 Process

1. Load enriched site data from domain tables (e.g. `site_natural_hazards`, `site_infrastructure_v2`).
2. For each exclusionary criterion and each SMR design, evaluate the site against the defined threshold.
3. Record a `screening_verdicts` row per site × criterion × SMR design, including:
   - Criterion ID and SMR key
   - Verdict (pass / fail / caution / inconclusive)
   - Justification text (e.g. "PGA 0.35g exceeds 0.3g threshold at site coordinates")
   - Confidence level (high / medium / low)
   - Data source reference
4. Sites with **any** fail verdict for a given SMR design are flagged as excluded for that design.

### 5.2.3 Configuration

All exclusionary thresholds shall be defined in YAML configuration, not hard-coded. This enables threshold adjustment without code changes.

---

## 5.3 Avoidance Screening

### 5.3.1 Objective

For sites that pass exclusionary screening, evaluate avoidance criteria (A1–A15). Avoidance results do not exclude sites but are recorded as risk flags and may influence scoring.

### 5.3.2 Process

1. For each non-excluded site, evaluate all avoidance criteria against configurable thresholds per SMR design.
2. Record results in `screening_verdicts` with the same structure as exclusionary results (verdict = "caution" for avoidance concerns).
3. Avoidance verdicts are carried forward into the scoring stage as input context.

---

## 5.4 Score Assignment

### 5.4.1 Objective

For each candidate site (passed exclusionary screen), compute a score of 1–5 for every ranking criterion based on retrieved data and predefined scoring rubrics.

### 5.4.2 Scoring Rubrics

Each criterion shall have a mapping from data values to scores defined in YAML:

```yaml
# Example rubric structure
criterion_id: R1_seismic
score_bands:
  5: { max_pga: 0.05 }
  4: { max_pga: 0.10 }
  3: { max_pga: 0.15 }
  2: { max_pga: 0.20 }
  1: { max_pga: 0.30 }
```

Rubrics shall be versioned alongside the configuration to support audit and reproducibility.

### 5.4.3 Missing Data

When data for a criterion is unavailable:

- Assign a configurable default score (e.g. 3) or mark as "unscored."
- Write a `site_observations` record with impact "negative" and the reason for missing data.
- Include the missing-data count in the run summary.

---

## 5.5 Composite Scoring and Ranking

### 5.5.1 Formula

Composite score per site:

```
S_composite = Σ (w_i × s_i) / Σ w_i
```

Where `w_i` is the weight for criterion `i` and `s_i` is the assigned score.

Weights are defined in YAML configuration per the scoring matrix in `requirements/06_scoring_matrix.md`.

### 5.5.2 Ranking

Sites are sorted by descending composite score. Ties are broken by:

1. Fewer avoidance flags.
2. Higher installed capacity.
3. Alphabetical by site name (deterministic fallback).

### 5.5.3 Output

Per-criterion scores are stored in `ranking_scores` (one row per site × criterion × SMR design, with `score_low`/`score_high` for uncertainty). Aggregate results are stored in `composite_rankings`:

- site_id, smr_key
- composite_score, composite_low, composite_high
- rank
- confidence
- run_id, timestamp

---

## 5.6 Sensitivity Analysis

### 5.6.1 Weight Perturbation

Systematically vary criterion weights within a defined range (e.g. ±20%) and re-rank to identify:

- Sites whose rank is stable across weight variations.
- Criteria that most influence the ranking order.

### 5.6.2 Monte Carlo Score Uncertainty

For each site-criterion pair, model score uncertainty as a distribution (e.g. ±0.5 around assigned score). Run N iterations (configurable, default 1000), recompute composite scores, and report:

- Mean and standard deviation of rank per site.
- Probability of each site appearing in top-N.

### 5.6.3 Configuration

Sensitivity analysis parameters (perturbation range, number of iterations, score uncertainty model) shall be defined in YAML.

---

## 5.7 Acceptance Criteria

- All exclusionary criteria produce deterministic pass/fail results for a given dataset.
- Score assignment is fully reproducible given the same data, rubrics, and weights.
- Changing weights in YAML produces updated rankings without code changes.
- Sensitivity analysis results are included in the output artifacts.
- Every screening and scoring decision is traceable to source data and configuration version.

---

## Source: `architecture/specs/06_execution_observability.md`

# 6. Execution and Observability

## 6.1 Purpose

This document specifies the structured logging, run lifecycle, error handling, and post-run reporting requirements. These ensure that batch runs across hundreds of sites and tens of API calls per site are transparent, debuggable, and auditable from the terminal.

**Traceability:** Derived from S10.5 (retry/logging requirements), S10.8 (development practices), and operational needs identified during architecture design.

---

## 6.2 Run Lifecycle

### 6.2.1 Run Identity

Every pipeline execution is assigned a unique `run_id` (UUID or timestamp-based). All log entries, database writes, and output artifacts are tagged with this ID.

### 6.2.2 Run States

```
INITIALISING → RUNNING → COMPLETING → SUCCEEDED | FAILED | PARTIAL
```

| State        | Meaning                                                                                        |
| ------------ | ---------------------------------------------------------------------------------------------- |
| INITIALISING | Configuration loaded, health checks in progress                                                |
| RUNNING      | Pipeline stages executing                                                                      |
| COMPLETING   | Final output generation and summary                                                            |
| SUCCEEDED    | All stages completed without critical errors                                                   |
| FAILED       | Pipeline halted due to critical error                                                          |
| PARTIAL      | Pipeline completed but with non-critical failures (e.g. some connectors failed for some sites) |

---

## 6.3 Structured Logging

### 6.3.1 Format

All log output shall be structured JSON (one object per line), enabling filtering and aggregation with standard CLI tools (`jq`, `grep`, `rg`).

### 6.3.2 Fields

Every log entry shall include:

| Field         | Type     | Description                                                                      |
| ------------- | -------- | -------------------------------------------------------------------------------- |
| `timestamp`   | ISO 8601 | Event time                                                                       |
| `level`       | enum     | DEBUG, INFO, WARNING, ERROR, CRITICAL                                            |
| `run_id`      | string   | Pipeline run identifier                                                          |
| `stage`       | string   | Pipeline stage (ingest, enrich, screen, score, rank, report)                     |
| `connector`   | string   | Connector name (null if not connector-related)                                   |
| `site_id`     | string   | Site identifier (null if not site-specific)                                      |
| `event`       | string   | Machine-readable event name (e.g. `api_request`, `cache_hit`, `validation_fail`) |
| `message`     | string   | Human-readable description                                                       |
| `duration_ms` | integer  | Operation duration (for timed events)                                            |
| `error_class` | string   | Error taxonomy class (if applicable)                                             |
| `attempt`     | integer  | Retry attempt number (if applicable)                                             |

### 6.3.3 Log Levels

| Level    | Usage                                                                   |
| -------- | ----------------------------------------------------------------------- |
| DEBUG    | Detailed per-request data (disabled by default in batch runs)           |
| INFO     | Stage start/end, site processing progress, connector summaries          |
| WARNING  | Non-critical issues: stale cache used, partial data, data quality flags |
| ERROR    | Request failures after all retries, validation failures                 |
| CRITICAL | Pipeline-halting errors: database unreachable, configuration invalid    |

### 6.3.4 Terminal Output

In addition to the JSON log file, a human-readable progress summary shall be printed to stderr:

```
[12:34:56] Stage: enrich | Progress: 142/387 sites | Seismic: 142 ok, 0 err | Flood: 140 ok, 2 retry
```

This gives immediate visibility during long runs without parsing JSON.

---

## 6.4 Progress Tracking

For batch runs, track and display:

- Total sites to process.
- Sites completed / in-progress / failed per stage.
- Per-connector: success count, retry count, failure count, cache-hit ratio.
- Elapsed time and estimated time remaining.

---

## 6.5 Error Handling

### 6.5.1 Error Taxonomy

Refer to the error classes defined in [04_connector_framework.md](04_connector_framework.md) section 4.5.

### 6.5.2 Escalation Policy

| Severity                                 | Behaviour                                                                       |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| Single connector fails for a single site | Log ERROR, continue with remaining connectors/sites                             |
| Single connector fails for all sites     | Log CRITICAL for that connector, continue other connectors, mark run as PARTIAL |
| Database unreachable                     | Log CRITICAL, halt pipeline                                                     |
| Configuration invalid                    | Log CRITICAL at INITIALISING, halt before any processing                        |

### 6.5.3 Failed-Site Tracking

Maintain an in-memory set of `(site_id, connector, error_class)` tuples for all failures during a run. This set feeds into the post-run summary.

---

## 6.6 Post-Run Summary

At the end of every run, generate a summary report (Markdown) and print a condensed version to the terminal:

### 6.6.1 Summary Contents

| Section          | Content                                                                  |
| ---------------- | ------------------------------------------------------------------------ |
| Run metadata     | run_id, start/end timestamps, duration, final state                      |
| Stage summary    | Per-stage: sites processed, pass/fail counts                             |
| Connector health | Per-connector: requests made, cache hits, retries, failures, avg latency |
| Error digest     | Grouped by error class: count, affected sites, sample error messages     |
| Data quality     | Sites with missing data, sites using stale cache, unscored criteria      |
| Coverage         | Percentage of sites fully enriched, percentage of criteria scored        |

### 6.6.2 Alert Thresholds

Configurable thresholds that trigger warnings in the summary:

| Metric                     | Default Threshold | Alert   |
| -------------------------- | ----------------- | ------- |
| Overall error rate         | > 5%              | WARNING |
| Any connector error rate   | > 10%             | WARNING |
| Site coverage              | < 95%             | WARNING |
| Criteria coverage per site | < 80%             | WARNING |

---

## 6.7 Acceptance Criteria

- Every log entry is valid JSON with all required fields.
- Terminal progress output updates at least every 10 seconds during batch runs.
- Post-run summary is generated for every run, including failed runs.
- Alert thresholds are configurable in YAML.
- A run can be fully reconstructed (which sites, which connectors, what happened) from its log file alone.

---

## Source: `architecture/specs/07_test_validation_strategy.md`

# 7. Test and Validation Strategy

## 7.1 Purpose

This document specifies the testing approach across unit, integration, and end-to-end levels, as well as manual cross-validation against reference sites.

**Traceability:** Requirements S10.8 (items 4–7).

---

## 7.2 Test Levels

### 7.2.1 Unit Tests

**Scope:** Individual functions and classes within each module.

**Coverage target:** ≥ 80% code coverage per module.

**What to test:**

| Module               | Unit Test Focus                                                          |
| -------------------- | ------------------------------------------------------------------------ |
| Data model           | Schema creation, field validation, ENUM constraints                      |
| Ingestion            | Parsing, deduplication, normalisation, country filtering                 |
| Each connector       | Response parsing, validation logic, cache key generation, error handling |
| Screening engine     | Each exclusionary criterion (E1–E9), each avoidance criterion (A1–A15)   |
| Scoring engine       | Score band assignment, composite score calculation, tie-breaking         |
| Sensitivity analysis | Weight perturbation, Monte Carlo iteration, statistical summary          |
| Output generation    | Report template rendering, CSV/JSON serialisation                        |

**Approach:**

- Use `pytest` with fixtures for database state and mock API responses.
- Connector unit tests shall use recorded (VCR-style) or mocked API responses, never live APIs.
- Screening and scoring tests shall use known-answer test cases: sites with predetermined attributes and expected pass/fail/score outcomes.

### 7.2.2 Integration Tests

**Scope:** End-to-end pipeline using a sample of known sites.

**What to test:**

- Full pipeline execution: ingest → enrich → screen → score → rank → report.
- Database state after each stage is consistent and complete.
- Output artifacts are generated and well-formed.
- Connector caching works correctly (second run uses cache).
- Configuration changes (weights, thresholds) produce expected ranking changes.

**Approach:**

- Use a dedicated test database (separate from production).
- Seed with a small fixture dataset (5–10 sites with known attributes).
- Connectors may use live APIs in integration tests (with caching to avoid repeated calls) or pre-recorded responses.

### 7.2.3 End-to-End Validation

**Scope:** Cross-check automated screening results against manual evaluation.

**Process:**

1. Select 3–5 reference sites with well-documented characteristics.
2. Manually evaluate each reference site against all criteria using the same data sources.
3. Run the automated pipeline on the same sites.
4. Compare:
   - Exclusionary screening results (pass/fail per criterion).
   - Avoidance screening results.
   - Assigned scores per criterion.
   - Final composite scores and ranks.
5. Document discrepancies and resolve (configuration error, data issue, or legitimate interpretation difference).

**Acceptance:** Automated results for reference sites shall match manual evaluation within documented tolerance bounds (e.g. score difference ≤ 0.5 on any criterion).

---

## 7.3 Connector Contract Tests

Each connector shall have a contract test that verifies:

1. **Schema compliance** — Response contains all required fields with correct types.
2. **Boundary behaviour** — Handles edge cases: sites on country borders, sites near poles/antimeridian (if applicable), sites with no nearby features.
3. **Error handling** — Gracefully handles API downtime, malformed responses, and empty results.
4. **Idempotency** — Running the same connector twice for the same site produces identical stored results (or correctly updates provenance timestamps).

---

## 7.4 Smoke Tests

Before any full batch run, execute a smoke test:

1. Run `health_check()` on all connectors.
2. Process 3–5 geographically diverse sites through the full pipeline.
3. Verify all stages complete without errors.
4. Verify output artifacts are generated.

If smoke tests fail, the batch run shall not proceed.

---

## 7.5 Regression Testing

When criteria, thresholds, or weights change:

1. Re-run the pipeline on the reference site set.
2. Compare results to the previous baseline.
3. Document expected vs. actual changes.
4. Update the baseline if changes are intentional.

---

## 7.6 Test Infrastructure

| Component         | Tool                                                    |
| ----------------- | ------------------------------------------------------- |
| Test runner       | pytest                                                  |
| Coverage          | pytest-cov                                              |
| API mocking       | responses, vcrpy, or pytest-httpserver                  |
| Database fixtures | pytest fixtures with SQLAlchemy test sessions           |
| CI integration    | Tests shall be runnable via a single command (`pytest`) |

---

## 7.7 Acceptance Criteria

- All modules have unit tests with ≥ 80% code coverage.
- Integration tests pass on the fixture dataset.
- End-to-end validation against 3–5 reference sites is documented with results.
- Smoke tests gate every batch run.
- Tests can be executed without network access (mocked API responses for unit tests).

---

