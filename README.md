# Atoms vs Ashes

SMR siting assessment tooling (screening, scoring, sensitivity, and data-acquisition connectors) for coal-to-nuclear candidate sites in Central / Eastern / Southern Europe.

This README lists **common operational commands**. Deeper methodology lives under [`report/methodology/`](report/methodology/) (entry points: [`sensitivity_analysis.md`](report/methodology/sensitivity_analysis.md), [`failure_analysis.md`](report/methodology/failure_analysis.md), [`exclusionary_floors.md`](report/methodology/exclusionary_floors.md), [`swing_weight_audit.md`](report/methodology/swing_weight_audit.md), [`criterion_correlation.md`](report/methodology/criterion_correlation.md), [`ssr1_traceability.md`](report/methodology/ssr1_traceability.md), [`assumption_register.md`](report/methodology/assumption_register.md)); connector behaviour is documented in [`src/ava_client/README.md`](src/ava_client/README.md).

---

## Environment

From the repository root:

```bash
cd /path/to/atoms_vs_ashes
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Database URL and credentials live in `.env`. For merged scoring / sensitivity work, set the database name explicitly when needed:

```bash
export POSTGRES_DB=atoms_vs_ashes_merged   # example — match your deployment
```

---

## Scoring (CLI)

The main CLI is `atoms-vs-ashes` (or `python -m atoms_vs_ashes`). Always pass `--db-profile` (`api`, `llm`, or `merged`) so the process hits the intended PostgreSQL database.

```bash
# Full 0–10 scoring + composites + verdicts (merged DB)
atoms-vs-ashes --db-profile merged score run

# Sensitivity suite (weights / MC / country; optional stages via --include)
atoms-vs-ashes --db-profile merged score sensitivity --preset production
```

`score sensitivity` options are defined in [`src/atoms_vs_ashes/scoring/_cli.py`](src/atoms_vs_ashes/scoring/_cli.py).

---

## Phase 1.6 — refined sensitivity (driver script)

End-to-end run (OAT importance, regulatory matrix, banding, consolidated audit) — typical production invocation:

```bash
POSTGRES_DB=atoms_vs_ashes_merged \
python -m scripts.run_phase_1_6_sensitivity \
  --db-profile merged \
  --mc-stages 10000 \
  --top-n-country 20 \
  2>&1 | tee logs/phase_1_6_refined_run.log
```

Methodology and frozen reference outcomes: [`report/methodology/sensitivity_analysis.md`](report/methodology/sensitivity_analysis.md).

---

## Phase 1.6 — regenerate sensitivity figures

PNG charts are **not** produced by the sensitivity driver itself; they are generated offline from the CSV + consolidated audit markdown that the driver already wrote.

Install plotting dependencies once (matplotlib is an optional extra):

```bash
pip install -e ".[report_plots]"
```

Then regenerate all four figures. The latest reference run is `20260425_*`; pass the corresponding paths explicitly:

```bash
python -m scripts.plot_phase_1_6_sensitivity \
  --oat-csv   audit/post_processing/06_scoring/20260425_oat_importance.csv \
  --bands-csv audit/post_processing/06_scoring/20260425_site_bands.csv \
  --audit-md  audit/post_processing/06_scoring/20260425_phase1_6_sensitivity.md \
  --out-dir   audit/post_processing/06_scoring/figures/20260425
```

Without arguments the script falls back to the historical 2026-04-23 defaults (kept for diff visibility).

Implementation: [`src/scripts/plot_phase_1_6_sensitivity.py`](src/scripts/plot_phase_1_6_sensitivity.py), [`src/scripts/_phase_1_6_sensitivity_figures.py`](src/scripts/_phase_1_6_sensitivity_figures.py).

---

## Phase 1.6 — extended banding & national analysis

Runs against the rows the refined sensitivity driver already wrote (no new scenarios): emits **A–H** global bands, per-SMR bands, **per-country** bands (within-country percentiles), country Jaccard summaries, a regional MD and one MD + PNG per country under `report/output/sensitivity/<stamp>/`.

```bash
POSTGRES_DB=atoms_vs_ashes_merged \
python -m scripts.run_phase_1_6_extended_analysis \
  --db-profile merged \
  --audit-dir audit/post_processing/06_scoring \
  --report-dir report/output/sensitivity \
  2>&1 | tee logs/phase_1_6_extended_analysis.log
```

Pass `--stamp 20260425` to align artefact naming with the current reference run (or any prior sensitivity stamp); `--no-figures` to skip PNG generation. Outputs:

- Audit CSVs: `{stamp}_site_bands.csv`, `{stamp}_site_bands_nuscale_voygr6.csv`, one file per SMR, per-country bands, and `{stamp}_country_rankings_summary(.csv|_nuscale.csv)`.
- Reports: `report/output/sensitivity/<stamp>/00_regional_summary.md` + `national/{CC_name}.md` (+ `figures/`).

Implementation: [`src/scripts/run_phase_1_6_extended_analysis.py`](src/scripts/run_phase_1_6_extended_analysis.py), [`src/scripts/_phase_1_6_extended_stages.py`](src/scripts/_phase_1_6_extended_stages.py), [`src/atoms_vs_ashes/scoring/_band_rules.py`](src/atoms_vs_ashes/scoring/_band_rules.py).

---

## Phase 1.6 — IAEA-style audit artefacts

Three regulator-facing artefacts are regenerated independently of the
sensitivity / extended-stages drivers:

```bash
# Swing-weight audit (declared vs observed-range weights)
.venv/bin/python -m scripts.generate_swing_weight_audit --db-profile merged

# Exclusionary-floor documentation (rubric → pass marks → DB conditions)
.venv/bin/python -m scripts.generate_exclusionary_floors

# IAEA SSR-1 ↔ project-criterion traceability matrix
.venv/bin/python -m scripts.generate_ssr1_traceability

# Failure-mode analysis (why sites failed scoring).
# Default: 1 global pack + 8 per-SMR packs (NuScale featured).
# Outputs: CSVs under audit/.../, figures under report/output/sensitivity/<stamp>/figures/failure/{,per_smr/<key>/},
# and methodology MDs under report/methodology/{failure_analysis,failure_analysis_<smr_key>}.md.
.venv/bin/python -m scripts.generate_failure_analysis \
  --db-profile merged --stamp 20260425

# NuScale-only refresh (also re-renders the global pack):
.venv/bin/python -m scripts.generate_failure_analysis \
  --db-profile merged --stamp 20260425 --smr-nuscale

# Per-SMR-only (skip global; pick any subset of vendor flags):
.venv/bin/python -m scripts.generate_failure_analysis \
  --db-profile merged --stamp 20260425 --skip-global \
  --smr-nuscale --smr-geh --smr-holtec --smr-oklo \
  --smr-rollsroyce --smr-xenergy \
  --smr-terrapower-nominal --smr-terrapower-peak
```

The criterion correlation heatmap is produced standalone or as part of
the extended analysis:

```bash
.venv/bin/python -m scripts._phase_1_6_figures_correlation --db-profile merged
```

Outputs land under [`report/methodology/`](report/methodology/) and
[`audit/post_processing/06_scoring/`](audit/post_processing/06_scoring/).

---

## Inspecting run results (DB-first)

Alembic revision `034_persist_analytics` introduces a provenance layer (`runs`, `dataset_snapshot`) plus 12 analytics tables (composite components, bands, country summaries / rankings, OAT, weight-profile stability, threshold roll-up, failure outcomes / aggregates, swing weights, correlations, country balance check). Every row carries a `run_id` so a single pipeline invocation is fully reproducible from the DB without touching the CSV trees.

The `inspect_run` CLI exposes the most common audit queries; output is JSON on stdout for easy `jq` / pipeline composition:

```bash
# Top 10 sites per country for a given SMR within a run
python -m scripts.inspect_run \
  --db-profile merged --run-id <run_id> \
  top-n-per-country --smr-key nuscale_voygr6 --n 10

# All criterion-level score components for one site/SMR/profile
python -m scripts.inspect_run \
  --db-profile merged --run-id <run_id> \
  site-criterion-scores --site-id <uuid> --smr-key nuscale_voygr6

# Composite + band + active stability profiles in one shot
python -m scripts.inspect_run \
  --db-profile merged --run-id <run_id> \
  site-sensitivity-profile --site-id <uuid> --smr-key nuscale_voygr6

# Why did this pair fail? Bucket + verdict trail
python -m scripts.inspect_run \
  --db-profile merged --run-id <run_id> \
  failure-explanation --site-id <uuid> --smr-key nuscale_voygr6

# Threshold-direction roll-up (per criterion, ±25 % weight perturbation)
python -m scripts.inspect_run \
  --db-profile merged --run-id <run_id> \
  threshold-summary
```

Forward-only: pre-`034` runs (notably the `20260423` and `20260425` reference snapshots) remain CSV-only by design — see [`assumption_register.md`](report/methodology/assumption_register.md). The DB tables fill in from the next pipeline invocation. Implementation: [`src/atoms_vs_ashes/db/queries.py`](src/atoms_vs_ashes/db/queries.py), [`src/scripts/inspect_run.py`](src/scripts/inspect_run.py).

### Consolidated SMR top-N report

The DB-backed top-N-per-country pack is assembled by `build_nuscale_top10_report`. It joins `country_site_rankings`, `composite_rankings`, `composite_score_components`, `site_bands`, `country_rankings_summary` and `weight_profile_stability` for the chosen SMR, emits per-country PNGs (`<CC>_composite_top10.png`, `<CC>_family_heatmap.png`) plus a single consolidated markdown:

```bash
python -m scripts.build_nuscale_top10_report \
  --db-profile merged \
  --stamp 20260425b \
  --sensitivity-run-id <sensitivity_run_id> \
  --scoring-run-id <scoring_run_id> \
  --smr-key nuscale_voygr6 --top-n 10
# → report/output/sensitivity/20260425b/nuscale_top10.md
# → report/output/sensitivity/20260425b/nuscale_top10/figures/<CC>_*.png
```

Reference snapshot: [`report/output/sensitivity/20260425b/nuscale_top10.md`](report/output/sensitivity/20260425b/nuscale_top10.md). Implementation: [`src/scripts/build_nuscale_top10_report.py`](src/scripts/build_nuscale_top10_report.py) plus the `_nuscale_top10_query.py`, `_nuscale_top10_md.py`, `_nuscale_top10_figures.py` helpers in the same package.

---

## Data acquisition — connectors

### AVA client (runs the implemented connector stack on a site list)

Full command reference: [`src/ava_client/README.md`](src/ava_client/README.md).

```bash
# Quick smoke test (three built-in sites, no DB required for the run itself)
.venv/bin/ava-client run --test-sites

# Upstream API health checks
.venv/bin/ava-client health
```

### Long-running Overpass batch orchestrator (EP-02 / EP-04 / transport interleaved)

Runs from repo root with `src` on `PYTHONPATH` (normal after `pip install -e .`):

```bash
python -m scripts.run_overpass_orchestrator
```

**Detached run + live log tail** (pattern used in the script docstring, adapted to a repo-local log file):

```bash
mkdir -p logs
nohup python -m scripts.run_overpass_orchestrator > logs/overpass_orchestrator.log 2>&1 &
tail -f logs/overpass_orchestrator.log
```

### Other batch / enrichment scripts

Dozens of orchestrated jobs live under [`src/scripts/`](src/scripts/). Invoke them as modules from the repo root, e.g. `python -m scripts.run_ep02_road_density_requery`. Capture output with `tee` when you need an audit trail:

```bash
mkdir -p logs
python -m scripts.<module_name> 2>&1 | tee logs/<module_name>_$(date +%Y%m%d_%H%M%S).log
tail -f logs/<pick_the_file_you_just_created>.log
```

---

## Related documentation

| Topic | Location |
| ----- | -------- |
| Sensitivity method + reference run | [`report/methodology/sensitivity_analysis.md`](report/methodology/sensitivity_analysis.md) |
| Failure-mode analysis (why sites failed) | [`report/methodology/failure_analysis.md`](report/methodology/failure_analysis.md) |
| Exclusionary thresholds & safety floors | [`report/methodology/exclusionary_floors.md`](report/methodology/exclusionary_floors.md) |
| Swing-weight audit | [`report/methodology/swing_weight_audit.md`](report/methodology/swing_weight_audit.md) |
| Criterion correlation flag list | [`report/methodology/criterion_correlation.md`](report/methodology/criterion_correlation.md) |
| IAEA SSR-1 traceability matrix | [`report/methodology/ssr1_traceability.md`](report/methodology/ssr1_traceability.md) |
| Project-wide assumptions | [`report/methodology/assumption_register.md`](report/methodology/assumption_register.md) |
| AVA client / connector phases | [`src/ava_client/README.md`](src/ava_client/README.md) |
| Database profiles / migrations | [`src/atoms_vs_ashes/db/README.md`](src/atoms_vs_ashes/db/README.md) |
| Audit pack layout | [`audit/README.md`](audit/README.md) |
