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

# Failure-mode analysis (why sites failed scoring) — funnel, per-criterion,
# per-country, per-SMR, multi-failure histogram + tables + methodology MD.
.venv/bin/python -m scripts.generate_failure_analysis \
  --db-profile merged --stamp 20260425
```

The criterion correlation heatmap is produced standalone or as part of
the extended analysis:

```bash
.venv/bin/python -m scripts._phase_1_6_figures_correlation --db-profile merged
```

Outputs land under [`report/methodology/`](report/methodology/) and
[`audit/post_processing/06_scoring/`](audit/post_processing/06_scoring/).

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
