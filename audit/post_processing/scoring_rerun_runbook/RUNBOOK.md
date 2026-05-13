<!-- man_hours: 0.6 -->
# Scoring Rerun Runbook — Operator-Run Commands

This is the operator-run runbook for the SP-F scoring rerun.
Same-server commands are grouped to run **serially** (so we don't get
kicked off the free public endpoints). Cross-group commands are
**parallel-safe** because they target different infrastructure or
purely local files.

The agent will not run full batches. Each section below gives:

- Server / dataset under load.
- Pre-flight gate (must be true before the run command is safe).
- Run command (`tee`s into `logs/...` so the agent can read the log).
- Tail command to monitor progress.

Always invoke commands from the repo root (`/Users/terbolence/projects/atoms_vs_ashes`).
All `enrich` subcommands need `PYTHONPATH=src` only when called as a
script; `atoms-vs-ashes enrich` resolves via the installed console
entry point.

---

## Server / Group Matrix

| Group | Server / Source | Sub-runs | Concurrency | Raw-response logging |
| --- | --- | --- | --- | --- |
| A | OSM Overpass (`overpass-api.de`) | HI-06 rest-of-DB rerun | **serial only** within group | ✅ `site_raw_responses` (`connector_slug=osm`) + disk |
| B | Local CSVs (EEA E-PRTR, Seveso) | HI-02 / HI-03 / HI-04 backfills | local only; parallel-safe | n/a — no HTTP response. Criterion tables are the system of record. |
| C | Copernicus DEM (AWS Open Data) | NH-04 optional refresh | independent of A/B/D/E | ✅ `site_raw_responses` (`connector_slug=copernicus_dem`, raster extraction) + disk |
| D | Local NetCDF (ERA5 monthly means) | NH-11 sub-score recompute | local only; parallel-safe | ✅ `site_raw_responses` (`connector_slug=copernicus_era5`, raster extraction) + disk |
| E | (blocked) — needs source decision | HI-05 hazmat, HI-08 nuclear | DO NOT run until E1/E2 below resolved | future scripts will log per the rule |
| F | Local DB + scoring engine | SP-F score run + anchor delta | run **after** A–D complete | n/a — writes to `ranking_scores` / `composite_rankings` / `screening_verdicts` |

You can run any of `B`, `C`, `D` in parallel terminals while `A` is
streaming. `A` must stay alone in its terminal. `F` waits for A–D.

---

## Group A — OSM Overpass (serial)

### A1. HI-06 SP-F rerun — rest of the database

The Austria smoke run (8 sites) is already persisted under
`run_id=hi06_spf_20260512_182652`. The `--requery-enriched` flag is
intentionally not used; the script auto-skips sites already carrying
the SP-F marker on `hi06_comment`. The default search radius is 25 km.

- Server: `https://overpass-api.de/api/interpreter`
- Approx. work: ~353 sites × 1 query + ~12 s pacing + retries
  ≈ 70–90 min wall time.
- Pre-flight gate: probe report
  `audit/post_processing/hi06_probe/probe_report.md` verdicts must all
  be `ok` or `no_features_in_radius`. (Already verified for AT_Timelkam,
  AT_Riedersbach, RO_Braila, DE_Cottbus.)

Run:

```bash
PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm \
  2>&1 | tee logs/hi06_spf_full.log
```

Tail:

```bash
tail -F logs/hi06_spf_full.log
```

Optional staged variants (still serial — pick one at a time):

```bash
# Only the Romania anchor sites Ovidiu flagged:
PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm \
  --country RO 2>&1 | tee logs/hi06_spf_ro.log

# Force re-process a single site that already carries the SP-F marker:
PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm \
  --requery-enriched --site-id <SITE_UUID> 2>&1 | tee -a logs/hi06_spf_singleton.log
```

---

## Group B — Local CSV connectors (parallel-safe)

Both backfills read pre-downloaded CSVs from
`src/data/sources/eea_industrial/facilities.csv` and the local Seveso
data tree. They do not hit any external server, so they can run in
parallel with group A or with each other.

### B1. HI-02 / HI-03 / HI-04 — EEA Industrial (E-PRTR + IED)

Pre-flight gate: `ls src/data/sources/eea_industrial/facilities.csv`
must exist. (Verified present at 2026-05-12.)

Run:

```bash
.venv/bin/atoms-vs-ashes enrich eea-industrial --all \
  2>&1 | tee logs/eea_industrial_rerun.log
```

Tail:

```bash
tail -F logs/eea_industrial_rerun.log
```

### B2. HI-02 — Seveso supplemental (optional)

Pre-flight gate: at least one of these must be true; otherwise the
command will print the missing-files error.

```bash
.venv/bin/atoms-vs-ashes enrich seveso --dry-run
```

If `Minerva CSV: found` or `National files: ...` then proceed; if both
are missing, **skip B2** — the EEA E-PRTR coverage in B1 is enough for
this pass. To run the supplemental once the data files are present:

```bash
.venv/bin/atoms-vs-ashes enrich seveso --all \
  2>&1 | tee logs/seveso_rerun.log
```

Tail:

```bash
tail -F logs/seveso_rerun.log
```

---

## Group C — Copernicus DEM (parallel-safe; optional)

NH-04 already stores `slope_angle_deg` as the **footprint mean** from
the Copernicus connector, and the rubric / spec changes plus the new
`slope_angle_mean_deg` alias make that explicit. No rerun is strictly
needed.

Run this **only if** you want to refresh slope/elevation numbers for
sites whose Copernicus DEM rows look stale (verify with the dry-run
first):

```bash
.venv/bin/atoms-vs-ashes enrich copernicus-dem --dry-run
```

Then for the full refresh (separate terminal from group A is fine —
different server):

```bash
.venv/bin/atoms-vs-ashes enrich copernicus-dem --all \
  2>&1 | tee logs/copernicus_dem_refresh.log
```

Tail:

```bash
tail -F logs/copernicus_dem_refresh.log
```

---

## Group D — ERA5 (parallel-safe; local)

`enrich era5` is a Tier-2 local recompute against pre-downloaded
NetCDFs in `src/data/sources/era5/`. It does NOT hit the Copernicus CDS
API — see the docstring on `enrich_era5` in `src/atoms_vs_ashes/cli.py`.
Use this to recompute NH-11 sub-scores (drought / snow / precipitation)
after the SP-F rubric rebanding.

Pre-flight gate:

```bash
.venv/bin/atoms-vs-ashes enrich era5 --check-data
```

The `monthly-means` and `era5-land` files should both report `✓`.
(Verified present at 2026-05-12.)

Run:

```bash
.venv/bin/atoms-vs-ashes enrich era5 --all \
  2>&1 | tee logs/era5_recompute.log
```

Tail:

```bash
tail -F logs/era5_recompute.log
```

This is local-only computation and is parallel-safe with everything
else.

---

## Group E — Blocked (do not run yet)

Both require a concrete decision before any rerun is meaningful.

### E1. HI-05 — Major hazmat corridor classifier (blocked)

The current `hazmat_route_distance_km` field is populated from a
generic "nearest road/railway" proxy and does not distinguish a major
hazmat corridor (e.g. AGTC railway, E-road carrying ADR Class 1/2/7
traffic). The SP-F bands explicitly say "score only major hazmat
corridors, not every ordinary road or railway".

Decision required before any rerun:

1. Pick a corridor definition. Options:
   - Trans-European Transport Network (TEN-T) **Core Network** roads
     and the TEN-T rail Freight Core (curated GeoPackage from
     ec.europa.eu).
   - UNECE AGTC railway corridor master list.
   - OSM-tagged `route=road` relations with `network=e-road` plus rail
     freight master routes.
2. Confirm whether "major" requires hazmat-specific tagging
   (`hazmat=*`, `route=ferry`, etc.) or simply means the corridor class.

Once the classifier spec is approved, the agent can wire it; until
then `hazmat_route_distance_km` should stay as-is and the new bands
treat missing data as unscored (already the case in the SP-F rubric).

### E2. HI-08 — Other nuclear installations (blocked)

`nearest_nuclear_km` and `nearest_nuclear_name` are currently populated
only via the LLM enrichment path (`llm/persist.py`). There is no
structured connector for IAEA PRIS / ENSREG / etc.

Decision required before any rerun:

1. Pick a source. Recommended order:
   - IAEA PRIS (Power Reactor Information System) — JSON export.
   - ENSREG installation list — CSV / official site lists.
   - Public Wikipedia / nuclear-energy-agency curated lists as
     fall-backs only.
2. Decide how to handle co-located cases (favorable vs neutral vs low,
   per the SP-F bands).

Once a source is chosen, the agent can build a one-shot loader
(probably `src/scripts/run_hi08_nuclear_proximity.py`) and a probe-only
script the same way HI-06 was handled.

### E3. NH-11 — Braila / Timelkam value verification (blocked on data review)

The SP-F plan requires verifying the implausible NH-11 values for
Braila and Timelkam before the Option A bands take full effect. This is
a data-review task, not a connector run — please flag the offending
rows in `site_natural_hazards` for Braila and Timelkam (look at
`mean_annual_precip_mm`, `snow_months_per_year`, `spi12_min`) and
either confirm or correct them before re-running scoring regression.
The `enrich era5` run in Group D will refresh the inputs; manual review
catches data-entry / unit errors that the connector cannot.

---

## Group F — Scoring regression (local; run after A–D)

Local-only — no external API. Captures the SP-F effect on the
Ovidiu-commented anchor sites (Timelkam, Riedersbach, Braila) by
comparing a new `score run` against the existing baseline
`feedback_rerun_20260509`.

### F1. Run the SP-F scoring engine

This persists into `ranking_scores`, `composite_rankings`, and
`screening_verdicts` under a fresh `run_id`. It is local computation
against the DB; no external calls.

```bash
.venv/bin/atoms-vs-ashes score run --weight-profile baseline \
  2>&1 | tee logs/score_run_spf.log
```

Tail:

```bash
tail -F logs/score_run_spf.log
```

When the run completes, capture the new `run_id` printed in the
summary payload (or read it from the `ranking_scores` table — it is
the most recent value of `run_id` for `score_0_10 IS NOT NULL`).

### F2. Anchor-site delta report

After F1 finishes, render the before/after table for the anchor sites
and the SP-F-affected criteria.

```bash
PYTHONPATH=src .venv/bin/python src/scripts/compare_anchor_scores.py \
  --before-run-id feedback_rerun_20260509 \
  --after-run-id  <NEW_RUN_ID_FROM_F1> \
  --smr-key nuscale_voygr6 \
  --out audit/post_processing/scoring_rerun_runbook/anchor_delta.md
```

Omit ``--smr-key`` only if you need the full multi-SMR matrix; the
default anchor workflow is **NuScale VOYGR-6** only
(``nuscale_voygr6``).

The script prints a one-line summary
(`up=, down=, unchanged=, missing_before=, missing_after=`) and writes
the full delta table to the `--out` path. Inspect that file before
proceeding to any report-text refresh.

---

## After Groups A–F finish

Hand off to the report-text refresh. No further live calls are needed
at that stage; the report writer reads from the new `run_id` only.

---

## Persistence And Audit

Every Group A / C / D script writes to **two** stores:

1. The **criterion table** for scoring (e.g. `site_human_hazards`,
   `site_natural_hazards`, `site_infrastructure_v2`).
2. The **raw-response audit trail** at:
   - DB row: `site_raw_responses` row per site per run, keyed by
     `(site_id, connector_slug, run_id)`.
   - Disk mirror: `data/raw_responses/<connector_slug>/<run_id>/<site_id>.json`.

Group B (EEA Industrial, Seveso) reads local CSVs — there is no HTTP
response to log. Its system of record is the criterion table itself
(`nearest_seveso_km`, `nearest_industrial_km`, `nearest_toxic_source_km`,
plus per-criterion quality / comment).

Group F (scoring) writes to `ranking_scores`, `composite_rankings`,
and `screening_verdicts` — that is the system of record for scoring.

### Verify after each batch (recommended)

After each Group A / C / D run finishes, run the coverage verifier
with the run's `run_id`:

```bash
PYTHONPATH=src .venv/bin/python src/scripts/verify_raw_response_coverage.py \
  --run-id <RUN_ID>
```

Focus on the row whose `connector_slug` matches the group you just
ran:

- A1 → look for the `osm` row (expect `logged ≈ 361`).
- C  → look for the `copernicus_dem` row.
- D  → look for the `copernicus_era5` row.

Other rows will be `0` because each batch only logs its own connector
slug — that is expected for a single-connector run.

Disk file sanity check (the verifier's disk count is computed under
`src/data/...` which is a pre-existing path quirk; the canonical disk
mirror lives at the repo root):

```bash
ls data/raw_responses/osm/<RUN_ID>/ | head
ls data/raw_responses/copernicus_dem/<RUN_ID>/ | head
ls data/raw_responses/copernicus_era5/<RUN_ID>/ | head
```

A directory with one JSON per site means the disk dual-write succeeded.

## Notes For The Operator

- The Austria HI-06 smoke run on 2026-05-12 21:26 UTC (`run_id =
  hi06_spf_20260512_182652`) is already persisted; rerunning A1 will
  skip those 8 rows unless `--requery-enriched` is passed.
- The Timelkam dual-write smoke run
  (`run_id = hi06_spf_20260512_184148`, 1 site) confirms the SP-F
  HI-06 rerun now writes to `site_raw_responses`.
- The original 8 AT smoke-run rows from `hi06_spf_20260512_182652`
  predate the dual-write fix, so they have criterion-table rows but no
  `site_raw_responses` entry. If you want full coverage there too, run
  this **inside** Group A's terminal (still serial against Overpass):
  ```bash
  PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm \
    --requery-enriched --country AT 2>&1 | tee -a logs/hi06_spf_at_refill.log
  ```
- Group A inter-query delay is configured at 12 s with retry/backoff on
  429/504, so the wall time is dominated by pacing, not raw query
  time. Don't shorten the delay; we already saw a 504 in the AT smoke
  run.
- Keep each terminal output going through `tee` so the agent can read
  the same file you tail.
- If a group A run gets stuck on retries, kill it and resume — the
  script auto-skips already-enriched sites on restart.
