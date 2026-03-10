## 10. Automated Site Evaluation System

### 10.1 System Objectives

An automated evaluation system shall be developed to:

1. Programmatically manage the power plant database and site attributes.
2. Connect to external data APIs to retrieve criterion-specific data for each site.
3. Apply the screening criteria and scoring matrix algorithmically.
4. Generate reproducible site evaluation outputs and ranking tables.
5. Enable rapid re-evaluation when data is updated or criteria weights are adjusted.

### 10.2 Architecture

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

### 10.3 Component 1: Power Plant Database (PostgreSQL)

**Objective:** Ingest the coal/thermal plant inventory and maintain it as the central data store.

**Schema Design:**

```sql
-- Core tables
sites                  -- Primary site records
site_attributes        -- Key-value attribute storage per site
site_infrastructure    -- Grid, cooling, transport details
site_scores            -- Criterion scores per site
criteria               -- Criterion definitions and weights
screening_results      -- Exclusionary/avoidance pass/fail records
ranking_results        -- Final composite scores and ranks

-- Reference tables
countries              -- Country metadata and regulatory info
data_sources           -- Data provenance tracking
data_quality_flags     -- Quality assessment per dataset per site
audit_log              -- Change tracking for all updates
```

**Key Fields per Site:**

| Field | Type | Description |
|---|---|---|
| site_id | UUID | Unique identifier |
| name | VARCHAR | Plant/site name |
| country_code | CHAR(2) | ISO 3166-1 alpha-2 |
| latitude | DECIMAL(9,6) | WGS84 latitude |
| longitude | DECIMAL(9,6) | WGS84 longitude |
| plant_type | ENUM | Coal, Lignite, Gas, Thermal, Other |
| installed_capacity_mw | DECIMAL | Current/historical installed capacity |
| status | ENUM | Operating, Retired, Planned_Closure |
| retirement_date | DATE | Actual or planned |
| owner_operator | VARCHAR | Current owner/operator |
| grid_voltage_kv | INTEGER | Transmission connection voltage |
| grid_capacity_mw | DECIMAL | Available export capacity |
| cooling_water_source | VARCHAR | River name, lake, sea, cooling tower |
| site_area_ha | DECIMAL | Available site area in hectares |
| elevation_m | DECIMAL | Site elevation above mean sea level |
| last_verified | TIMESTAMP | Last data verification date |

**Ingestion Process:**

1. Download Global Coal Plant Tracker (CSV) and Beyond Fossil Fuels database (CSV).
2. Parse, deduplicate, and normalise records.
3. Geocode any records missing coordinates.
4. Manually add the two Romanian supplementary sites (Braila-Chiscani, FPCU Feldioara).
5. Load into PostgreSQL with full audit logging.
6. Generate data quality report on completeness and consistency.

### 10.4 Component 2: Data Validation and Web Search Update Module

**Objective:** Verify and update the status of each power plant by cross-referencing current public sources.

**Scope:** For each site in the database, validate:

| Attribute | Verification Source |
|---|---|
| Operational status | National energy regulator, company websites, news |
| Installed capacity | ENTSO-E, company reports |
| Retirement timeline | National coal phase-out plans, EU NECP documents |
| Grid connection | National TSO grid maps, ENTSO-E |
| Cooling water source | Satellite imagery, OSM, national water agencies |
| Owner/operator | Company registries, energy databases |
| Site area | Satellite imagery, cadastral data |

**Process:**

1. For each site, execute structured web searches targeting authoritative sources.
2. Compare retrieved data against database records.
3. Flag discrepancies for manual review.
4. Update verified records with source URLs and verification timestamps.
5. Log all changes in the audit trail.

**Implementation Constraints:**

- Respect rate limits and terms of service of all data sources.
- Prioritise primary-region sites (Romania, Serbia, Armenia) for manual verification.
- Secondary-region sites may use automated verification with spot-check sampling.

### 10.5 Component 3: API Connector Framework

**Objective:** Programmatically retrieve geospatial, environmental, and demographic data for each site from external databases.

**Connector Specifications:**

| Connector | Target API | Data Retrieved | Protocol |
|---|---|---|---|
| Seismic Connector | USGS Earthquake API + GEM/SHARE | Historical earthquakes within 300 km, PGA values | REST/JSON |
| Flood Connector | EU Floods Directive WMS/WFS | Flood zones intersecting 5 km buffer | OGC WMS/WFS |
| Meteorology Connector | Copernicus CDS API (ERA5) | Temperature, wind, precipitation extremes | CDS API (Python) |
| Population Connector | WorldPop / Eurostat GISCO | Population within 5/16/25/80 km radii | GeoTIFF + REST |
| Protected Areas Connector | WDPA API + Natura 2000 | Protected areas within 10 km | REST/GIS |
| Land Use Connector | CORINE WMS | Land cover classification at site | OGC WMS |
| Grid Connector | ENTSO-E Transparency API | Nearest substation, capacity data | REST/XML |
| Volcano Connector | Smithsonian GVP | Holocene volcanoes within 300 km | Web scraping/JSON |
| Industrial Hazards Connector | SEVESO Directive registers + OSM | SEVESO facilities within 10 km | Mixed |
| Transport Connector | OSM Overpass API | Road/rail/waterway within 5 km | REST/JSON |

**Implementation Requirements:**

- Each connector shall be implemented as an independent, testable module.
- All API responses shall be cached with configurable expiration (default: 30 days).
- Failed requests shall be logged and retried with exponential backoff.
- Data shall be stored in the PostgreSQL database with full provenance metadata.
- Each connector shall include a data quality validation step before storage.

### 10.6 Component 4: Screening and Scoring Engine

**Objective:** Apply exclusionary/avoidance criteria and the weighted scoring matrix programmatically.

**Functions:**

1. **Exclusionary Screen:** For each site, evaluate all exclusionary criteria (E1–E9). Record pass/fail with justification. Sites failing any criterion are flagged as "Excluded."
2. **Avoidance Screen:** For remaining sites, evaluate avoidance criteria (A1–A15). Apply configurable thresholds. Record results.
3. **Score Assignment:** For candidate sites, compute scores (1–5) for each ranking criterion based on retrieved data and predefined scoring rubrics.
4. **Composite Scoring:** Apply criterion weights and compute composite scores per the formula in Section 8.3.
5. **Ranking:** Sort candidate sites by composite score.
6. **Sensitivity Analysis:** Implement weight perturbation and Monte Carlo score uncertainty analysis per Section 8.4.

### 10.7 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Database | PostgreSQL 16+ with PostGIS extension | Mature RDBMS with native geospatial support |
| Backend Language | Python 3.11+ | Extensive geospatial, scientific, and API ecosystem |
| ORM / DB Access | SQLAlchemy + psycopg2 | Industry-standard Python-PostgreSQL interface |
| Geospatial Processing | GeoPandas, Shapely, Rasterio | Geospatial analysis and raster data handling |
| API Clients | requests, cdsapi, OWSLib | HTTP and OGC service clients |
| Data Processing | pandas, numpy | Tabular data manipulation and numerical computation |
| Visualisation | folium, matplotlib | Interactive maps and static charts |
| Reporting | Jinja2 + markdown | Templated report generation |
| Configuration | YAML / environment variables | Configurable thresholds, weights, API keys |
| Testing | pytest | Unit and integration testing |
| Version Control | Git | All code and configuration under version control |

### 10.8 Software Development Process

Development shall follow established software engineering practices:

1. **Requirements analysis:** This document serves as the system requirements specification.
2. **Architecture design:** Component diagram, API interface definitions, database schema (documented in code repository).
3. **Implementation:** Modular development with clear separation of concerns.
4. **Unit testing:** Each connector, screening function, and scoring function shall have unit tests with ≥80% code coverage.
5. **Integration testing:** End-to-end pipeline tests using a sample of known sites.
6. **Validation:** Cross-check automated screening results against manual evaluation of 3–5 reference sites.
7. **Documentation:** Code documentation, API usage guide, and deployment instructions.
