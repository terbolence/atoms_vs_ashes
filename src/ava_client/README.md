# AVA Client — Data Acquisition & Analysis Runner

CLI orchestrator that drives data acquisition and analysis for SMR siting assessment.
It imports from the `atoms_vs_ashes` server package and runs all implemented connectors
and analysis modules against a given set of power-plant sites.

## Installation

From the project root:

```bash
pip install -e .
```

This installs both the `atoms-vs-ashes` server package and the `ava-client` CLI.

Verify installation:

```bash
ava-client --version
```

## Quick Start — Built-in Test Sites

The fastest way to run the client uses three hardcoded test sites
(Rovinari/RO, Belchatow/PL, Tusimice/CZ). **No database required.**

```bash
# Full run with 3 test sites (all connectors + analysis)
ava-client run --test-sites

# Skip slow connectors for a faster test
ava-client run --test-sites --skip egdi --skip seismic

# Health checks only (no data fetching)
ava-client run --test-sites --dry-run

# Verbose logging
ava-client run --test-sites -v
```

## Ad-hoc Coordinates

Provide one or more sites as `LAT,LON[:NAME]`:

```bash
ava-client run --coords 44.15,23.12:Rovinari --coords 51.26,19.33:Belchatow
```

If no name is given after the colon, one is generated from the coordinates.

## Command Reference

### `ava-client run`

| Option | Default | Description |
|--------|---------|-------------|
| `--config PATH` | `config/default.yml` | YAML config file |
| `--coords LAT,LON[:NAME]` | — | Ad-hoc site (repeatable) |
| `--test-sites` | `False` | Use 3 built-in test sites |
| `-v` / `--verbose` | `False` | DEBUG-level logging |
| `--run-id TEXT` | auto | Explicit run ID |
| `--output-dir PATH` | `tests/integrationSnapshots` | Snapshot directory |
| `--skip PHASE` | none | Skip: `corine`, `osm`, `population`, `egdi`, `seismic`, `analysis` |
| `--max-sites N` | 0 (all) | Limit sites processed |
| `--dry-run` | `False` | Health checks only |
| `--no-snapshots` | `False` | Disable snapshot file writing |

### `ava-client health`

Run health checks for all upstream APIs:

```bash
ava-client health
ava-client health --skip egdi --skip seismic
```

### `ava-client show-config`

Dump the resolved YAML configuration:

```bash
ava-client show-config
```

## Parallel Processing

Phase 2 (connector fetch) runs four API worker threads in parallel:

| Worker | API | Rate Limit |
|--------|-----|------------|
| Overpass | OSM + Population (overpass-api.de) | 1 req at a time, 5 s between sites |
| CORINE | EEA ArcGIS REST | 2 s between sites |
| EGDI | EGDI WFS | 1 s between requests |
| Seismic | EFEHR REST | 0.5 s between requests |

Each worker respects its API's rate limit independently. No API blocks another.

## Output

Snapshots are written to `tests/integrationSnapshots/` (one Markdown file per
connector endpoint and analysis module). A unique `run_summary_{run_id}.md`
is generated for each run.

## Module Invocation

The client can also be run as a Python module:

```bash
python -m ava_client run --test-sites
```
