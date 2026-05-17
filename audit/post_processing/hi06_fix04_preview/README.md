<!-- man_hours: 0.3 -->
# FIX-04 OSM avoidance — preview, approve, apply

Operational notes for running the **preview → approve → apply** workflow
introduced for FIX-04 (OSM Overpass: military → HI-06, transmitters →
HI-07, HV power → NS-02).

Sibling of `audit/post_processing/hi01_preview/README.md`.

---

## What each command does

| Step    | Touches DB?  | External HTTP  | Script                                                                                                |
|---------|--------------|----------------|-------------------------------------------------------------------------------------------------------|
| Preview | **No**       | Overpass (real) | [`src/scripts/preview_fix04_osm_vs_db.py`](../../../src/scripts/preview_fix04_osm_vs_db.py)           |
| Apply   | **Yes**      | Overpass (real) | [`src/scripts/run_fix04_osm_avoidance_batch.py`](../../../src/scripts/run_fix04_osm_avoidance_batch.py) |

> **Important:** the preview is **not free** — it calls Overpass with
> the same query mix as the apply (military / power / transmitters per
> site). Honour [`experts/connectors/api_enrichment_operations.md`](../../../experts/connectors/api_enrichment_operations.md) and
> the FIX-04 in-script delays before scoping the run to all sites.

Why a separate script? `run_fix04_osm_avoidance_batch.py` is already
780 lines (above the project's 300-line file-size limit per
`.cursor/rules/file-size-limits.mdc`). The preview is implemented as a
sibling that **imports** the existing parsers (`_parse_military`,
`_parse_power`, `_parse_transmitters`) and the `OverpassClient`, so the
fetch+parse logic is identical and the apply path stays untouched.

---

## Artefacts

- **JSONL** (`logs/hi06_fix04_preview.jsonl`): one line per site with
  the full per-domain parsed payload, the current DB row (HI-06 / HI-07
  / NS-02 columns), per-domain fetch errors, and a per-column diff list.
- **Markdown report**
  (`audit/post_processing/hi06_fix04_preview/hi06_fix04_preview_report.md`):
  per-domain change counts (HI-06 highlighted as a separate section)
  and the first N affected sites.

---

## Start and tail — preview (all sites, no DB writes)

**Terminal 1 — run:**

```bash
cd /Users/terbolence/projects/atoms_vs_ashes
mkdir -p logs audit/post_processing/hi06_fix04_preview
PYTHONPATH=src .venv/bin/python src/scripts/preview_fix04_osm_vs_db.py \
  --jsonl logs/hi06_fix04_preview.jsonl \
  --report audit/post_processing/hi06_fix04_preview/hi06_fix04_preview_report.md \
  > logs/hi06_fix04_preview.log 2>&1
```

**Terminal 2 — follow log:**

```bash
tail -f /Users/terbolence/projects/atoms_vs_ashes/logs/hi06_fix04_preview.log
```

After the run, read the report:

```bash
less /Users/terbolence/projects/atoms_vs_ashes/audit/post_processing/hi06_fix04_preview/hi06_fix04_preview_report.md
```

Optional smoke run scoped to one country:

```bash
PYTHONPATH=src .venv/bin/python src/scripts/preview_fix04_osm_vs_db.py --country RO
```

---

## Start and tail — apply (all sites, **DB writes**)

Run **only after** you have read the report and given explicit approval
per [`experts/connectors/api_enrichment_operations.md`](../../../experts/connectors/api_enrichment_operations.md). The legacy
batch processes every site in `sites` when no filter is passed and
**skips already-enriched sites** by default; pass `--no-skip-populated`
if you want to re-run them.

**Terminal 1 — run:**

```bash
cd /Users/terbolence/projects/atoms_vs_ashes
mkdir -p logs
PYTHONPATH=src .venv/bin/python src/scripts/run_fix04_osm_avoidance_batch.py \
  > logs/hi06_fix04_apply.log 2>&1
```

**Terminal 2 — follow log:**

```bash
tail -f /Users/terbolence/projects/atoms_vs_ashes/logs/hi06_fix04_apply.log
```

After the apply completes, append a session entry to
[`audit/conversations/`](../../conversations/) recording the run ID
(printed at the top of the log) and the artefact paths.

---

## Tolerances used by the diff

| Column                                                                                | Tolerance |
|---------------------------------------------------------------------------------------|-----------|
| `nearest_military_km`, `nearest_transmitter_km`, `nearest_hv_line_km`, `nearest_substation_km` | 0.01 km   |
| All other columns (counts, voltages, names, quality strings)                          | exact     |

Decimal columns from PostgreSQL are coerced to `float` before
comparison; `False` and `None` are kept distinct (no boolean-to-numeric
collapse).

`hi06_comment`, `hi07_comment`, `ns02_comment` are **excluded** from
the diff matrix to keep the report readable; their full content is
retained in the JSONL payloads.

Pure-logic helpers:
[`src/scripts/_preview_fix04_diff.py`](../../../src/scripts/_preview_fix04_diff.py).
