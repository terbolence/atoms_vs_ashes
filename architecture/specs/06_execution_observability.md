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
