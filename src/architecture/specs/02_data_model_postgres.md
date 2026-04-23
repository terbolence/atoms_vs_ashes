<!-- man_hours: 12.0 -->
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
