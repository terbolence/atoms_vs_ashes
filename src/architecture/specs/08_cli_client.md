# 08 — CLI Client: Data Acquisition & Analysis Runner

**Project:** SMR Siting Assessment — Automated Site Evaluation System

**Spec version:** 1.0

**Date:** April 2026

**Status:** DRAFT — awaiting approval on open decisions (§10)

---

## 1. Purpose and Scope

The CLI client is a standalone command-line orchestrator that drives data acquisition and analysis for a given set of power plant sites. It:

1. Accepts plant identifiers as input (multiple identification schemes)
2. Resolves each identifier to site coordinates (via DB or inline)
3. Executes all implemented connectors and analysis modules against each site
4. Streams structured, human-readable logs to the terminal in real time
5. Writes per-endpoint Markdown integration snapshots to `tests/integrationSnapshots/`
6. Produces a summary report upon completion

The client **imports from** the `atoms_vs_ashes` server package (connectors, analysis, config, models) but **lives in a separate package directory** and has its own CLI entry point. It replaces `scripts/live_integration_snapshots.py` as the canonical data-acquisition tool.

### 1.1 What the Client Is NOT

- It is not a web server, REST API, or daemon process.
- It does not persist results to the database by default (that remains the server pipeline's job). Snapshot writing is to the filesystem only.
- It does not implement new analysis logic — it orchestrates existing modules.

---

## 2. Package Layout

```
src/
  atoms_vs_ashes/          # server package (existing)
  ava_client/              # client package (new)
    __init__.py
    __main__.py            # python -m ava_client
    cli.py                 # Click entry point
    config.py              # client-specific config (inherits from server Settings)
    resolver.py            # site ID resolution logic
    runner.py              # orchestration engine
    snapshot.py            # Markdown snapshot writer
    display.py             # rich terminal output helpers
    phases/                # one module per execution phase
      __init__.py
      health.py            # Phase 1: health checks
      connectors.py        # Phase 2: connector data fetching
      analysis.py          # Phase 3: analysis module execution
      summary.py           # Phase 4: summary report generation
```

### 2.1 Entry Point Registration

```toml
# pyproject.toml addition
[project.scripts]
ava-client = "ava_client.cli:main"
```

Invocable as:
```bash
ava-client <command> [options]
# or
python -m ava_client <command> [options]
```

### 2.2 Dependencies (additions to project)

| Package | Version | Purpose |
|---------|---------|---------|
| `rich` | `>=13.7` | Live progress panels, color tables, spinners, Markdown rendering |

All other dependencies (`click`, `httpx`, `structlog`, `pyyaml`, `shapely`, `pyproj`) are already present via the `atoms_vs_ashes` server package.

---

## 3. Input Specification

### 3.1 Site Selection Modes

The client supports four mutually exclusive site selection modes:

| Mode | Flag | Example | DB required? |
|------|------|---------|-------------|
| By site UUID | `--site-id UUID` (repeatable) | `--site-id 3fa85f64-5717-4562-b3fc-2c963f66afa6` | Yes |
| By country | `--country CC` (repeatable) | `--country RO --country PL` | Yes |
| All sites | `--all` | `--all` | Yes |
| Ad-hoc coordinates | `--coords LAT,LON[:NAME]` (repeatable) | `--coords 44.15,23.12:Rovinari` | No |

When using DB-backed modes (`--site-id`, `--country`, `--all`), the client queries the `sites` table for coordinates, name, and country code. When using `--coords`, no database connection is required — useful for testing, one-off investigations, or running against sites not yet ingested.

If no mode is specified, the client prints usage help and exits with code 2.

### 3.2 Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--config PATH` | `click.Path` | `config/default.yml` | Path to YAML config file |
| `--verbose` / `-v` | flag | `False` | Enable DEBUG-level logging |
| `--run-id TEXT` | `str` | auto-generated | Explicit run ID for traceability |
| `--output-dir PATH` | `click.Path` | `tests/integrationSnapshots` | Directory for snapshot files |
| `--format` | `choice` | `rich` | Terminal output format: `rich` (live panels), `plain` (simple text), `json` (structured) |
| `--dry-run` | flag | `False` | Run health checks only, no data fetching |
| `--skip` | `multiple choice` | none | Skip specific phases: `corine`, `osm`, `population`, `egdi`, `seismic`, `analysis` |
| `--max-sites N` | `int` | `0` (all) | Limit number of sites processed (for quick tests) |
| `--concurrency N` | `int` | `1` | Max parallel site processing (future; serial by default) |
| `--no-snapshots` | flag | `False` | Disable snapshot file writing (log to terminal only) |

### 3.3 Subcommands

```
ava-client run [site-selection] [options]    # full acquisition + analysis
ava-client health [options]                  # health checks only
ava-client list-sites [--country CC] [--status STATUS]  # list available sites from DB
ava-client show-config                       # dump resolved configuration
```

The `run` command is the primary workhorse. `health`, `list-sites`, and `show-config` are utility commands.

---

## 4. Execution Phases

The `run` command executes four sequential phases. Each phase logs structured events and writes snapshots independently, so a failure in one phase does not prevent the others from completing.

### Phase 1 — Health Checks

For every active connector (not in `--skip`), verify upstream API reachability:

| Connector | Health endpoint |
|-----------|----------------|
| CORINE | ArcGIS REST `MapServer?f=json` |
| OSM | Overpass `/status` |
| Population | Overpass `/status` (shared with OSM) |
| EGDI Geology | WFS `GetCapabilities` |
| Seismic Hazard | EFEHR REST `models` endpoint |

**Behavior:**
- Each check runs with a 10s timeout.
- Results are displayed as a color-coded table (green PASS / red FAIL / yellow SKIP).
- If a connector fails health check, it is auto-skipped for subsequent phases with a warning.
- Snapshot written: `health_checks.md`

### Phase 2 — Connector Data Fetching

For each resolved site, call every active connector endpoint:

| Connector group | Endpoints | Rate limiting |
|----------------|-----------|---------------|
| CORINE | `fetch()`, `classify()` | 2s between sites |
| OSM | `fetch_populated_places`, `fetch_amenities`, `fetch_road_density`, `fetch_waterways`, `fetch_airports`, `fetch_military_areas`, `fetch_transmitters`, `fetch_power_infrastructure`, `fetch_land_use` | 5s between sites, 3s between endpoint groups |
| Population | `fetch()` | 5s between sites |
| EGDI | `fetch_all()` | per-connector default |
| Seismic | `fetch_all()` | per-connector default |

**Behavior:**
- Each endpoint call is timed.
- Responses are cached in memory (keyed by `site.country + endpoint`) for use by Phase 3.
- Failed individual calls log a warning and continue — partial failure is tolerated.
- Snapshots written: one file per endpoint group (e.g., `osm_airports.md`, `corine_classify.md`, `population_fetch.md`).

### Phase 3 — Analysis Module Execution

Using cached data from Phase 2, run every implemented analysis module:

| Module | Input source | Criterion |
|--------|-------------|-----------|
| `aviation_hazard` | OSM airports | HI-01 |
| `military_proximity` | OSM military | HI-06 |
| `transmitter_proximity` | OSM transmitters | HI-07 |
| `grid_proximity` | OSM power infra | NS-02 |
| `land_availability` | OSM land use | NS-05 |
| `wildfire_context` | CORINE features | NH-13 |
| `ecological_sensitivity` | CORINE features | NS-08 |
| `site_topography` | CORINE features | NS-04 |
| `laydown_area` | CORINE features | NS-13 |
| `population_projection` | Population result | RI-06 |
| `coal_site_analysis` | Site metadata | NS-05 |

**Behavior:**
- Analysis modules are pure functions — they do not make API calls.
- If input data is missing (Phase 2 failure), the analysis is skipped for that site with an error snapshot entry.
- Snapshots written: one file per analysis module (e.g., `analysis_aviation_hazard.md`).

### Phase 4 — Summary Report

After all phases complete, generate a summary:

- Total sites processed
- Per-phase success/failure counts
- Per-connector and per-analysis pass/fail/skip breakdown
- Total elapsed wall time
- List of snapshot files written

The summary is:
1. Displayed in the terminal (as a rich table or JSON depending on `--format`)
2. Written to `{output_dir}/run_summary_{run_id}.md`

---

## 5. Terminal Output Specification

### 5.1 `rich` Format (default)

The `rich` output mode uses a live-updating terminal display:

```
┌─────────────────────────────────────────────────────────────┐
│  AVA Client — Run 20260402T183000_a1b2c3d4                  │
│  Sites: 23 │ Config: config/default.yml │ Skip: none        │
└─────────────────────────────────────────────────────────────┘

Phase 1/4: Health Checks
┌──────────────┬─────────────────────┬────────┬──────────┐
│ Connector    │ Endpoint            │ Status │ Elapsed  │
├──────────────┼─────────────────────┼────────┼──────────┤
│ CORINE       │ EEA ArcGIS REST     │ PASS   │ 342 ms   │
│ OSM          │ Overpass API        │ PASS   │ 128 ms   │
│ Population   │ Overpass            │ PASS   │ 128 ms   │
│ EGDI         │ WFS GetCapabilities │ PASS   │ 1204 ms  │
│ Seismic      │ EFEHR REST          │ FAIL   │ 10002 ms │
└──────────────┴─────────────────────┴────────┴──────────┘
⚠ Seismic Hazard will be skipped (health check failed)

Phase 2/4: Connector Fetch  [████████░░░░░░░░░░░░] 8/23 sites
  Current: PL — Bełchatów │ osm.fetch_airports │ 1.2s
  Last: CZ — Tušimice │ OK (all 14 endpoints)
```

Key elements:
- **Header panel**: run metadata at a glance.
- **Phase tables**: results rendered as color-coded tables after each phase.
- **Progress bar**: per-phase progress with current site and endpoint indication.
- **Live status line**: updates in place showing what's executing right now.
- **Warnings**: yellow-highlighted inline when a connector fails or data is missing.
- **Final summary table**: aggregated counts at the end.

### 5.2 `plain` Format

Mirrors the output style of the existing `scripts/live_integration_snapshots.py` — sequential print lines suitable for pipe/redirect:

```
[1/4] Health checks...
  CORINE        EEA ArcGIS REST     PASS  342ms
  OSM           Overpass API        PASS  128ms
  ...
[2/4] Connector fetch — 23 sites...
  [1/23] RO Rovinari... osm_airports OK (7 elements, 312ms)
  [1/23] RO Rovinari... osm_military OK (2 elements, 289ms)
  ...
```

### 5.3 `json` Format

One JSON object per event on stdout, one per line (JSONL / newline-delimited JSON). Suitable for programmatic consumption:

```json
{"phase":"health","connector":"corine","status":"pass","elapsed_ms":342}
{"phase":"fetch","site":"Rovinari","country":"RO","endpoint":"osm_airports","status":"ok","element_count":7,"elapsed_ms":312}
```

---

## 6. Structured Logging

The client uses `structlog` (via `atoms_vs_ashes.logging`) for all structured log events. Logs are written to **stderr** so they don't interfere with stdout output formats.

### 6.1 Log Events

Every log event includes `run_id` (bound via contextvars).

| Event | Level | Context fields |
|-------|-------|---------------|
| `client_start` | INFO | `run_id`, `site_count`, `skip`, `output_dir` |
| `site_resolved` | INFO | `site_name`, `country`, `lat`, `lon`, `source` (db/coords) |
| `health_check` | INFO | `connector`, `status`, `elapsed_ms` |
| `fetch_start` | DEBUG | `site_name`, `connector`, `endpoint` |
| `fetch_ok` | INFO | `site_name`, `connector`, `endpoint`, `element_count`, `elapsed_ms` |
| `fetch_error` | WARNING | `site_name`, `connector`, `endpoint`, `error`, `elapsed_ms` |
| `analysis_ok` | INFO | `site_name`, `module`, `criterion_id`, `elapsed_ms` |
| `analysis_error` | WARNING | `site_name`, `module`, `criterion_id`, `error` |
| `snapshot_written` | INFO | `filename`, `path`, `site_count` |
| `phase_complete` | INFO | `phase`, `success`, `failed`, `skipped`, `elapsed_ms` |
| `client_complete` | INFO | `run_id`, `total_sites`, `total_elapsed_s`, `snapshot_count` |

---

## 7. Snapshot File Specification

### 7.1 Output Directory

Default: `{project_root}/tests/integrationSnapshots/`

Overridable via `--output-dir`. The directory is created if it does not exist.

### 7.2 File Naming Convention

Snapshots follow the existing naming convention established by `scripts/live_integration_snapshots.py`:

| Category | Filename pattern | Example |
|----------|-----------------|---------|
| Health | `health_checks.md` | `health_checks.md` |
| Connector | `{connector}_{endpoint}.md` | `osm_airports.md`, `corine_classify.md` |
| Analysis | `analysis_{module}.md` | `analysis_aviation_hazard.md` |
| Summary | `run_summary_{run_id}.md` | `run_summary_20260402T183000_a1b2c3d4.md` |

### 7.3 Snapshot Format

Each snapshot file follows this Markdown template (compatible with existing snapshots):

```markdown
<!-- man_hours: 0.0 -->
# {Title} ({Criterion ID})

**Generated:** {ISO 8601 UTC timestamp}
**Run ID:** {run_id}
**Description:** {one-line description}
**Sites:** {N} processed, {M} successful, {K} failed

---

## {Country Code} - {Site Name}

- **Coordinates:** {lat}, {lon}
- **Status:** PASS | FAIL | SKIP ({elapsed} ms)
- **Summary:** {one-line result summary}

<details>
<summary>Full response</summary>

```json
{pretty-printed JSON response}
```

</details>

---

(repeat per site)
```

### 7.4 Overwrite Policy

Snapshot files are **overwritten** on each run. The `run_summary_{run_id}.md` file is unique per run and never overwrites previous summaries.

---

## 8. Error Handling

### 8.1 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All phases completed, no failures |
| 1 | Partial failure (some sites or endpoints failed, others succeeded) |
| 2 | Usage error (bad arguments, missing required flags) |
| 3 | Configuration error (config file not found, invalid YAML) |
| 4 | No sites resolved (all identifiers failed to resolve) |
| 5 | All connectors failed health check (nothing to run) |

### 8.2 Partial Failure Strategy

The client follows the project's established partial-failure convention (from `experts/connectors/software_architect.md` §K.6):

- If one site fails, log and continue to the next.
- If one endpoint fails for a site, log and continue to the next endpoint.
- If all endpoints of a connector fail across all sites, mark the connector as degraded in the summary.
- The run is never aborted early unless zero sites can be resolved or zero connectors pass health checks.

### 8.3 Retry

API calls use the retry settings from `config/default.yml`:
- `max_retries: 3`
- `base_delay_s: 2`
- `max_delay_s: 60`
- Exponential backoff with jitter

Retries are logged at DEBUG level.

---

## 9. Site Resolution Logic (`resolver.py`)

### 9.1 DB-Backed Resolution

```python
def resolve_from_db(
    session: Session,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    all_sites: bool = False,
) -> list[ResolvedSite]:
```

Queries the `sites` table. Returns a list of `ResolvedSite` dataclass instances:

```python
@dataclass
class ResolvedSite:
    name: str
    country: str
    lat: float
    lon: float
    site_id: uuid.UUID | None
    source: str   # "db" or "coords"
```

### 9.2 Coordinate-Based Resolution

```python
def resolve_from_coords(
    coord_specs: list[str],
) -> list[ResolvedSite]:
```

Parses `LAT,LON[:NAME]` strings. If no name is provided, generates one from coordinates (e.g., `"site_44.15_23.12"`).

### 9.3 Validation

- Coordinates must be within the 23-country bounding box (lat 35–60, lon 12–45). Out-of-bounds coordinates generate a warning but are not rejected.
- UUIDs that don't match any site in the DB cause a warning and are skipped.
- Country codes not in `config.in_scope_countries` cause a warning but are still processed.

---

## 10. Open Decisions (Require Your Approval)

| # | Question | Recommendation | Impact |
|---|----------|---------------|--------|
| 1 | **Package name**: `ava_client` vs `atoms_vs_ashes_client`? | `ava_client` — short, distinct, ergonomic CLI name | Entry point name, import paths |
| 2 | **`rich` dependency**: Add `rich>=13.7`? | Yes — gold-standard CLI output is not achievable with plain print | New dependency |
| 3 | **GEM tracker ID support** (`--gem-id`): Worth adding as an input mode? | Defer — adds complexity for low-frequency use case; can be added later | Input flexibility |
| 4 | **DB requirement**: Should `--coords` mode bypass DB entirely (no connection needed), or always require DB? | Bypass — makes the client usable without PostgreSQL for testing and CI | Deployment flexibility |
| 5 | **Deprecate `scripts/live_integration_snapshots.py`**: Remove after client is stable? | Yes — the client subsumes its functionality | Cleanup |
| 6 | **Snapshot diff mode** (`--diff`): compare current run against previous snapshots and highlight changes? | Defer to v1.1 — useful but non-essential for initial delivery | Feature scope |
| 7 | **Parallel site processing** (`--concurrency N`): implement now or stub? | Stub the flag, implement serial only in v1.0. Parallelism adds complexity around rate limiting | Delivery scope |

---

## 11. Relationship to Existing Components

```
┌──────────────────────────────────────────────────────┐
│                     ava-client CLI                     │
│  (ava_client.cli → runner → phases/*)                 │
│                                                        │
│  ┌─────────┐  ┌───────────┐  ┌──────────────────┐    │
│  │resolver │  │ snapshot   │  │ display (rich)   │    │
│  │         │  │ writer     │  │ progress/tables  │    │
│  └────┬────┘  └─────┬─────┘  └──────────────────┘    │
│       │              │                                  │
│       │              └──────► tests/integrationSnapshots/│
│       ▼                                                 │
│  ┌──────────────────────────────────────────────┐      │
│  │  atoms_vs_ashes (server package — imported)   │      │
│  │                                                │      │
│  │  connectors/   analysis/   config   logging    │      │
│  │  osm  corine  population  egdi  seismic        │      │
│  │  db/models (Site query for resolution)         │      │
│  └──────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 11.1 Import Boundary

The client imports the following from `atoms_vs_ashes`:

| Module | What it uses |
|--------|-------------|
| `config.Settings` | Configuration loading |
| `logging.{configure_logging, get_logger, new_run_id}` | Structured logging |
| `connectors.*` | All connector classes |
| `analysis.*` | All analysis functions |
| `db.engine.{init_engine, session_scope}` | DB session (only when DB-backed modes are used) |
| `db.models.Site` | Site queries for resolution |
| `geo.*` | Utility functions (haversine, bbox, etc.) |

The client **never** imports from `pipeline`, `ingest`, or `screening` — those are server-pipeline concerns.

---

## 12. Configuration

The client reads the same `config/default.yml` as the server. No client-specific config section is needed in v1.0.

A future `client:` section could include:

```yaml
client:
  default_output_dir: "tests/integrationSnapshots"
  rate_limit_overrides:
    osm: 5.0        # seconds between requests
    corine: 2.0
  snapshot_max_json_items: 50
  rich_theme: "monokai"
```

---

## 13. Testing Strategy

| Test type | Location | Scope |
|-----------|----------|-------|
| Unit: resolver | `tests/test_ava_client_resolver.py` | Coordinate parsing, validation, edge cases |
| Unit: snapshot writer | `tests/test_ava_client_snapshot.py` | Markdown generation, truncation, encoding |
| Unit: display | `tests/test_ava_client_display.py` | Table formatting, progress tracking |
| Integration: CLI | `tests/test_ava_client_cli.py` | Click runner with mocked connectors |
| E2E: live run | manual / CI | `ava-client run --coords 44.15,23.12:Rovinari --max-sites 1` |

---

## 14. Delivery Estimate

| Component | Estimated hours |
|-----------|----------------|
| `cli.py` + `__main__.py` (Click scaffolding) | 3 |
| `resolver.py` (site resolution) | 2 |
| `runner.py` (orchestration engine) | 4 |
| `phases/health.py` | 1 |
| `phases/connectors.py` | 4 |
| `phases/analysis.py` | 3 |
| `phases/summary.py` | 2 |
| `snapshot.py` (Markdown writer) | 2 |
| `display.py` (rich terminal) | 3 |
| `config.py` | 1 |
| Tests | 4 |
| Integration + wiring | 2 |
| **Total** | **31** |

---

## 15. Migration Path from `scripts/live_integration_snapshots.py`

1. The client subsumes all functionality of the existing script.
2. The snapshot file format is backward-compatible (same Markdown structure, same filenames).
3. After the client is stable and verified to produce equivalent output, `scripts/live_integration_snapshots.py` is deleted.
4. The `scripts/` directory retains `man_hours_report.py` and any future utility scripts.

---

## Traceability

| Requirement | Addressed by |
|------------|-------------|
| Architecture §04 (Connector Framework) | Phase 2 — uses all existing connectors via their public API |
| Architecture §06 (Execution & Observability) | §6 — structured logging with run_id, event taxonomy, elapsed_ms |
| Architecture §07 (Test & Validation) | §13 — unit, integration, and E2E testing strategy |
| `experts/connectors/software_architect.md` §K (Operational rules) | §8 — retry, partial failure, idempotency |
