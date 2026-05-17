<!-- man_hours: 0.3 -->
# HI-01 OurAirports — preview, approve, apply

Operational notes for running the **preview → approve → apply** workflow
introduced for HI-01 (`AirportProximityResult` → `site_human_hazards`).

The same shape is mirrored for HI-06 / FIX-04 under
`audit/post_processing/hi06_fix04_preview/README.md`.

---

## What each command does

| Step    | Touches DB?  | External HTTP                      | Script                                                                                          |
|---------|--------------|------------------------------------|-------------------------------------------------------------------------------------------------|
| Preview | **No**       | OurAirports CSV (cached if recent) | [`src/scripts/preview_ourairports_vs_db.py`](../../../src/scripts/preview_ourairports_vs_db.py) |
| Apply   | **Yes**      | OurAirports CSV (cached if recent) | [`src/scripts/run_p10_ourairports_batch.py`](../../../src/scripts/run_p10_ourairports_batch.py) |

Preview emits two artefacts:

- **JSONL** (`logs/hi01_preview_all.jsonl`): one line per site with the
  full computed payload, the current DB row (HI-01 columns only) and a
  per-column diff list.
- **Markdown report** (`audit/post_processing/hi01_preview/hi01_preview_report.md`):
  human-readable summary with per-column change counts and the first
  N affected sites.

Apply continues to use the existing P10 batch unchanged (it commits
per-site).

---

## Start and tail — preview (all sites, no DB writes)

**Terminal 1 — run:**

```bash
cd /Users/terbolence/projects/atoms_vs_ashes
mkdir -p logs audit/post_processing/hi01_preview
PYTHONPATH=src .venv/bin/python src/scripts/preview_ourairports_vs_db.py \
  --jsonl logs/hi01_preview_all.jsonl \
  --report audit/post_processing/hi01_preview/hi01_preview_report.md \
  > logs/hi01_preview_all.log 2>&1
```

**Terminal 2 — follow log:**

```bash
tail -f /Users/terbolence/projects/atoms_vs_ashes/logs/hi01_preview_all.log
```

After the run, read the report:

```bash
less /Users/terbolence/projects/atoms_vs_ashes/audit/post_processing/hi01_preview/hi01_preview_report.md
```

Optional smoke run scoped to one country:

```bash
PYTHONPATH=src .venv/bin/python src/scripts/preview_ourairports_vs_db.py --country RO
```

---

## Start and tail — apply (all sites, **DB writes**)

Run **only after** you have read the report and given explicit approval
per [`experts/connectors/api_enrichment_operations.md`](../../../experts/connectors/api_enrichment_operations.md). The legacy P10
batch processes every site in `sites` when no filter is passed.

**Terminal 1 — run:**

```bash
cd /Users/terbolence/projects/atoms_vs_ashes
mkdir -p logs
PYTHONPATH=src .venv/bin/python src/scripts/run_p10_ourairports_batch.py \
  > logs/hi01_apply_all.log 2>&1
```

**Terminal 2 — follow log:**

```bash
tail -f /Users/terbolence/projects/atoms_vs_ashes/logs/hi01_apply_all.log
```

After the apply completes, append a session entry to
[`audit/conversations/`](../../conversations/) recording the run ID
(printed at the top of the log) and the artefact paths.

---

## Tolerances used by the diff

| Column                                | Tolerance |
|----------------------------------------|-----------|
| `nearest_airport_km`                   | 0.01 km   |
| `flight_path_distance_km`              | 0.01 km   |
| `nearest_airport_runway_length_m`      | 1.0 m     |
| All other columns (strings, bools, int) | exact     |

Decimal columns from PostgreSQL are coerced to `float` before comparison;
`False` and `None` are kept distinct (no boolean-to-numeric collapse).

Pure-logic tests:
[`tests/scripts/test_preview_ourairports_vs_db.py`](../../../tests/scripts/test_preview_ourairports_vs_db.py).
