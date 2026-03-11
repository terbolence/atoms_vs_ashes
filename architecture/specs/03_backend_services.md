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
