# Infrastructure, Export, and Database Cloning Plan

> **Status:** In Progress
> **Date:** 2026-04-12

## Context

- PostgreSQL 17 is running **natively** on macOS (not Docker)
- Migration `006_schema_overhaul.py` exists on disk but has **not been run** yet
- All 46 GEM Excel columns are already mapped: 28 as explicit `Site` columns + 19 in `extended_data` JSONB (verified -- none missing)
- No Excel export feature exists yet (`report` CLI command is a stub)
- Database switching is env-driven via `POSTGRES_DB` in `src/atoms_vs_ashes/config.py`

---

## 1. Fix: Auto-save Plans for Audit

**Why it didn't save:** The existing rule in `.cursor/rules/audit-trail.mdc` says "copy the full plan content to `audit/plans/`" but only as a general instruction. The `CreatePlan` tool writes to Cursor's internal storage, and the agent did not follow through with a file write.

**Fix:** Update the audit-trail rule to make the instruction unambiguous and immediate:

- Add explicit wording: "Immediately after any `CreatePlan` tool call, the agent MUST write the identical plan content to `architecture/plans/<name>.md` AND copy to `audit/plans/<name>.md`"
- Also save the just-completed overhaul plan to `audit/plans/006_database_schema_overhaul.md` (it was already written to `architecture/plans/` but not to `audit/plans/`)

---

## 2. Run Migration 006 on Native PostgreSQL

Steps (sequential):

1. Verify PostgreSQL 17 is running: `pg_isready -h localhost -p 5432`
2. Verify the `atoms_vs_ashes` database exists: `psql -U atoms -d atoms_vs_ashes -c "SELECT version();"`
3. Run the migration: `cd <project_root> && alembic upgrade head`
4. Verify new tables exist
5. Verify data is intact: `SELECT count(*) FROM sites;` should match the ingested count

After this, DBeaver will show all new domain tables with their typed columns.

---

## 3. Excel Column Verification (result)

**All 46 columns are present.** No action needed. Breakdown:

- **28 explicit `Site` columns:** GEM unit/phase ID, GEM location ID, Country/Area (as `country_code` + `country_name`), Wiki URL, Plant name, Plant name (other) + Plant name (local) (as `alternative_names` array), Owner, Owner GEM Entity ID, Parent, Parent GEM Entity ID, Capacity (MW), Status, Start year, Retired year, Planned retirement, Coal phaseout year, Net zero year, Combustion technology, Coal type, Coal source, Location, Local area, Subnational unit, Region, Latitude, Longitude, Location accuracy, Permits, Permit Date
- **19 in `extended_data` JSONB** (defined in `src/atoms_vs_ashes/ingest/sites.py` `_EXTENDED_COLUMNS`): Unit name, Conversion to (fuel), Conversion to (GEM unit ID), Alternate Fuel, Major area, Subregion, Permit Parsed, Captive, Captive industry use, Captive residential use, CHP, Capacity factor, Plant age, Heat rate, Emission factor, Annual CO2, Remaining plant lifetime, Lifetime CO2, China capacity payment recipient

---

## 4. Excel Export Feature

Create a new CLI command: `atoms-vs-ashes export --output <path.xlsx>`

### File: `src/atoms_vs_ashes/pipeline/export.py` (new)

Uses `pandas` + `openpyxl` (both already dependencies). Queries all tables and writes a multi-sheet XLSX with sheets for Sites (flattened), Ownership, Natural Hazards, Human Hazards, Radiological, Emergency Planning, Infrastructure, Screening Verdicts, Observations, and SMR Designs.

---

## 5. Database Clone for LLM Population

### 5.1 Create the LLM database

```sql
CREATE DATABASE atoms_vs_ashes_llm TEMPLATE atoms_vs_ashes OWNER atoms;
```

### 5.2 Switching mechanism

Add a `--db-profile` CLI option mapping `api` -> `atoms_vs_ashes`, `llm` -> `atoms_vs_ashes_llm`.

### 5.3 Update Alembic to read from env vars for DB targeting.
