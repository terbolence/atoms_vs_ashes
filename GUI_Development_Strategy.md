# Running the scoring GUI (Streamlit)

This project ships a small Streamlit app under `src/atoms_vs_ashes/gui/`. The console entry point is **`atoms-gui`**, which is only available **after** you install the package **into a virtual environment** with the **`gui`** optional dependency.

If anything below fails, read **Troubleshooting** at the end.

---

## Dev and production quick start

**Convention**

| Mode | Install | Typical command | Use when |
|------|---------|-----------------|----------|
| **Development** | Editable (`-e`) so code changes apply without reinstall | `atoms-gui` or `streamlit run …` from repo root | You are editing `src/atoms_vs_ashes/gui/` or nearby Python |
| **Production** | Non-editable install from a tag / CI build | `streamlit run` with **headless** + **bind address** (often behind nginx / TLS) | You deploy a fixed version for others to use |

**Default URL and port:** **http://localhost:8501** (port **8501**). See [§7 View the app](#7-view-the-app-in-your-browser) for custom ports and SSH.

---

### Development mode

**First-time full setup** (macOS / Linux / zsh — from repo root):

```bash
cd "/path/to/atoms_vs_ashes"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[gui,dev]'
atoms-gui
```

`dev` pulls in pytest and related tooling so you can run `python -m pytest tests/gui -v` while iterating. If you do not need tests in this venv, use `'.[gui]'` only.

**After the first setup** (same machine, venv already exists):

```bash
cd "/path/to/atoms_vs_ashes"
source .venv/bin/activate
atoms-gui
```

**Optional dev tweaks** (same venv; pick what you want):

```bash
# More verbose Streamlit logs while debugging
streamlit run src/atoms_vs_ashes/gui/app.py --logger.level=debug
```

Saving Python files under `src/atoms_vs_ashes/gui/` triggers Streamlit’s **rerun** behaviour in the browser (no reinstall needed with `-e`).

---

### Production mode

**First-time full setup** (dedicated server or clean venv — non-editable install):

```bash
cd "/path/to/atoms_vs_ashes"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install '.[gui]'
streamlit run src/atoms_vs_ashes/gui/app.py \
  --server.headless true \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --browser.gatherUsageStats false
```

- **`--server.headless true`** — do not try to open a browser on the server.
- **`--server.address 0.0.0.0`** — listen on all interfaces so a reverse proxy or another host can reach the app (omit or use `127.0.0.1` if you only want local access).
- Put **HTTPS and auth** in front of this in real deployments (e.g. nginx, Cloudflare, corporate SSO); Streamlit alone is not a hardened edge server.

**After the first setup** (redeploy same venv, or activate an existing one):

```bash
cd "/path/to/atoms_vs_ashes"
source .venv/bin/activate
streamlit run src/atoms_vs_ashes/gui/app.py \
  --server.headless true \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --browser.gatherUsageStats false
```

**Note:** The **`atoms-gui`** script is tuned for **interactive** use (`--server.headless false` in code). For production-style runs, prefer the explicit **`streamlit run …`** line above so flags stay under your control.

---

## GUI development strategy

Roadmap for evolving the Streamlit application alongside data ingestion, connector batches, and LLM assessments. Treat each track with the **same quality bar** as the scoring engine: automated tests, audit artefacts, explicit operator consent for any live external calls, and documented **run_id** provenance.

### 1. Adding new sites in scope for the database

**Objective.** Expand the canonical site catalogue in PostgreSQL so new coal-plant / conversion candidates appear in run-profile scope, scoring, and **Results** without one-off SQL.

**Product / engineering direction**

- Align GUI workflows (or documented CLI companions) with established ingestion paths (GEM XLSX, supplementary YAML-defined sites, screening) described in **`README.md`** and **`src/architecture/specs/03_backend_services.md`**. Every new site needs stable identifiers, geometry, and merge inputs consumed by **`merge_resolver`**.
- Make the distinction explicit in the UI: **rows present in the DB** versus **sites included in the active run profile** (`scope.country_codes`, `scope.site_ids`, `site_status_in`, SMR keys) so operators do not confuse catalogue growth with “in current run”.
- After bulk adds, run screening / merge validation; reconcile counts and file summaries under **`audit/post_processing/`** when appropriate.

**Checks and gold-standard practices**

- Schema changes via **Alembic** only; apply **`./.venv/bin/python -m alembic upgrade head`** in every environment.
- Idempotent loads, transactional batches, and clear audit trails for bulk inserts.
- **`pytest`** for modules that touch schemas, merge paths, or GUI data loaders (`tests/gui`, relevant `tests/` packages).
- Refresh **`report/methodology/`** or connector notes when new attributes affect scoring inputs.

### 2. Orchestrated API sweep across all connectors

**Objective.** Drive the full **data-acquisition / enrichment batch** in a single coordinated plan: health checks, phased connector execution, rate limiting, and summarised outcomes — not ad-hoc per-slug runs — matching the intent of **`src/ava_client/runner.py`** and **`src/ava_client/README.md`**.

**Product / engineering direction**

- Define a **sweep manifest** (ordered connectors, skip sets, concurrency) derived from **`config/default.yml`** and operational guidance in **`prompts/runAPIs.md`** (`atoms-vs-ashes enrich <slug>`, `--run-id`, `--db-profile api`).
- Surface orchestration from the GUI or a single CLI wrapper with **one run_id**, structured logging, resume-friendly behaviour, and optional **heartbeat / cancel** patterns consistent with **`src/atoms_vs_ashes/gui/_runner.py`** (Scoring Engine).
- Wire **post-sweep verification**: e.g. **`python -m scripts.scan_api_db_anomalies`** (Phase 1 sanity bounds), enrichment coverage reports, and **`connector_errors`** review — with outputs linked or summarised for operators.

**Checks and gold-standard practices**

- **`prompts/runAPIs.md`** escalation (dry-run → smoke → small batch → larger scopes): obtain **explicit consent** before live batches per **`.cursor/rules/live-api-safety.mdc`**.
- Respect **raw-response logging** policy where connectors persist payloads (**`.cursor/rules/raw-response-logging.mdc`**).
- Never bypass rate limits without updating **`config/default.yml`** and documenting the change.

### 3. Orchestrated LLM sweep across servers / tiers

**Objective.** Run the **LLM assessment pipeline** comprehensively — all configured criterion keys and tiers that the orchestrator supports — with deduplication and observability comparable to API enrichment.

**Product / engineering direction**

- Integrate **`LlmOrchestrator`** parameters (`tier`, `site_ids`, `country_codes`, `dry_run`, `force_rerun` per **`src/atoms_vs_ashes/llm/orchestrator.py`**) into a repeatable “full sweep” preset for staging and production.
- Provide GUI or CLI entry points that mirror scoring ergonomics: start, **heartbeat**/log tail, cancellation, and a clear completion summary (**AssessmentSummary**).
- Plan **merge / promotion** steps and **post-LLM anomaly sweeps** on the merged database (`atoms_vs_ashes_merged`) following patterns in **`audit/post_processing/`** so Results reflect promoted fields.

**Checks and gold-standard practices**

- Follow **`.cursor/rules/llm-dedup-safety.mdc`** and project dedup strategy (**`src/architecture/plans/smart_run_dedup_strategy.md`**) to avoid duplicate spend and inconsistent verdicts.
- Regression-test prompt / context changes; keep batch **run_id** traceability and audit markdown.

### 4. Cross-cutting quality bar (all GUI roadmap items)

- **Automated tests:** `python -m pytest tests/gui -v` for Streamlit regressions; extend to **`tests/scoring`** / **`tests/criterion_spec`** when profile loading or DB-backed definitions change.
- **Migrations and environments:** Same `.env` and **`POSTGRES_DB`** conventions as **`README.md`**; document any new GUI dependency under **`pyproject.toml`** `[gui]` extras.
- **Documentation:** Update this file’s operational sections when shipping new controls; keep methodology artefacts consistent when published metrics move.
- **Security:** No secrets in Streamlit session state; credentials only via environment / deployment configuration.

---

## 0. What you need

- Repository cloned locally.
- **Python 3.11+** (the project declares `requires-python = ">=3.11"`).
- A terminal (**zsh** on macOS is fine; note the quoting rules in step 4).
- A working **PostgreSQL** connection in **`.env`** (same as for `atoms-vs-ashes`). The GUI is now DB-backed end-to-end: countries, SMR designs, **and** the active run profile all live in Postgres, so a reachable database is required for the app to boot.
- Apply migrations once (and again any time you pull): `./.venv/bin/python -m alembic upgrade head`. Alembic revision **039** seeds the singleton `active_run_profile` row that powers the **Run Profile** page.

---

## 1. Open a terminal in the repository root

```bash
cd "/path/to/atoms_vs_ashes"
```

Use the real path to your clone (the folder that contains `pyproject.toml` and `src/`).

---

## 2. Create a virtual environment (once per machine / clone)

**Do not use** the system / Homebrew `pip` to install this project. On macOS, Homebrew’s Python is marked **PEP 668** “externally managed”, so `pip install` fails with `externally-managed-environment`. A **venv** avoids that.

If you **do not** already have `.venv`:

```bash
python3 -m venv .venv
```

If `python3` is too old, install a newer Python (e.g. from python.org or Homebrew) and use that binary in the command above.

---

## 3. Activate the virtual environment

**macOS / Linux (bash or zsh):**

```bash
source .venv/bin/activate
```

Your prompt should usually show `(.venv)`. **Every new terminal** must run `source .venv/bin/activate` again before installing or running.

**Windows (cmd):**

```bash
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```bash
.venv\Scripts\Activate.ps1
```

---

## 4. Install the package **and** the GUI extras

With the venv **activated**, run **exactly** (quotes are required in **zsh**):

```bash
python -m pip install -U pip
python -m pip install -e '.[gui]'
```

Why this shape:

- **`python -m pip`** guarantees you install into **the same interpreter** as the `python` from your activated venv.
- **Single quotes** around `'.[gui]'` stop **zsh** from treating `[gui]` as a filename glob (`zsh: no matches found: .[gui]`).

Double quotes also work: `python -m pip install -e ".[gui]"`.

---

## 5. Confirm the launcher is on your PATH

Still with the venv activated:

```bash
which python
which atoms-gui
```

You should see paths under `.venv/bin/`. If `atoms-gui` is “not found”, step 4 did not complete successfully—re-run it and check for errors.

---

## 6. Start the GUI

For **dev vs production** one-liners (full setup and “after first setup”), see **[Dev and production quick start](#dev-and-production-quick-start)** at the top of this file.

**Typical development:**

```bash
atoms-gui
```

Keep this terminal window open while you use the app. Press **Ctrl+C** in that terminal to stop the server.

**Alternative (equivalent to `atoms-gui` for local dev):**

```bash
streamlit run src/atoms_vs_ashes/gui/app.py
```

---

## 7. View the app in your browser

Streamlit binds a **local web server** and serves the UI over HTTP.

| Item | Value |
|------|--------|
| **Default port** | **8501** |
| **Default URL** | **http://localhost:8501** (same as **http://127.0.0.1:8501**) |

**What usually happens**

1. After `atoms-gui` starts, Streamlit prints several lines, including something like:
   - `Local URL: http://localhost:8501`
   - `Network URL: http://192.168.x.x:8501` (optional: other devices on your LAN)
2. On many setups, your **default browser opens automatically** to the Local URL.

**If no browser tab opens**

Open one manually and go to:

```text
http://localhost:8501
```

If that fails, use the exact **Local URL** line Streamlit printed in the terminal (copy-paste it).

**Sidebar pages (Streamlit multipage)**

The home view is **Sites & SMR Setup** — that is also the primary editor for the active run profile (countries, SMR designs in scope, qualification mode, top-N, near-miss gap, and a focused per-SMR mini-editor). Use the **sidebar** (left) to switch to **Site Selection Criteria**, **Scoring Engine**, or **Results**. Each screen name is a link; a single **i**-style info icon on the right shows the full description on **hover** (native browser tooltip; no separate help chip, no click). There is no profile picker — the active profile is one DB row you edit on **Sites & SMR Setup** (see [§9 Run profile management](#9-run-profile-management-db-backed)); the live values surface on that page itself, so the sidebar stays reserved for navigation only.

The **Results** page replaces the previous *Country Drill-Down*, *Near Miss*, and *Sensitivity* screens. It opens with a run-picker dropdown (cancelled / rolled-back runs are absent because their transaction was discarded), a sticky control row (weight-profile picker, country focus, *include eliminated sites* toggle), and a six-metric KPI strip summarising the run. Below those it exposes five tabs:

- **Coverage** — Per-country survivor / near-miss / deep-fail matrix derived live from `composite_rankings.passed_exclusionary` / `.passed_avoidance` joined with `screening_verdicts` and the rubric. Each row is a country; clicking a row pivots the page-level country focus so the **Sites** tab drills into it. Renders as an Altair stacked bar above an `st.dataframe` with status emojis.
- **Sites** — Country site ledger on the left (rank, status, composite with progress column, MC band, # failed criteria, top blocking criterion, worst gap %) with a side-column site-detail drawer on the right. The drawer shows a header card (composite + MC range, location, capacity), red / amber failed-criteria cards (each with a tiny inline gauge and the gap in raw + %), green strengths cards, a per-criterion bar across the rubric, and a single-row family-contribution stack from `composite_score_components`. When the page country focus is *(All)*, the ledger falls back to a regional top-100 view.
- **Regional** — Altair chart: composite as a coloured point with a **grey MC low–high rule** (forest-plot style), plus an expander **“How to read this chart”**. Below that, a full-width **`st.pydeck_chart`** map (larger viewport than the old `st.map`): hover tooltips show site, country, SMR, rank, composite, MC band, and pass flags; marker colour follows **composite quartiles** within the current filter, size scales with composite, and failed exclusionary pairs render fainter. Default layout is **stacked** (chart then map); optional checkbox **Side-by-side chart + map** restores a two-column view. Filters: country multiselect (pre-populated from the page-level country focus), pass-only toggle, row-limit slider.
- **Stability** — Sensitivity-only ledger of A–H stability bands joined with the largest-N Monte-Carlo composite stats. Lists each (site × SMR) pair with band, top-5/10/30% hit rates, MC mean / low / high, and scenarios scored. Filterable by band and accompanied by a band-counts bar. Shows an `st.info` and bails out for scoring-only runs.
- **Sensitivity** — DB-backed snapshot for sensitivity runs (MC iterations, weight-profile breakdown, country-balance, threshold sweep) plus optional metrics-bundle extras (per-pair MC distribution, OAT importance, weight-perturbation diff tables).

When the run only covers a single SMR (the default for NuScale-only runs), the ledger and the drawer drop the `smr_key` column / chip — each row is then unambiguously a site. The Regional bar / map and Stability ledger keep `smr_key` visible because Phase-2 use cases include cross-SMR comparison.

Loading a `*_metrics.json` bundle is **optional** — every tab now renders meaningful content from the database after a successful run on **Scoring Engine**. The bundle is only used by the **Sensitivity** tab to surface the heavier offline panels. The retired *Country*, *Top sites*, and *Near miss* tabs are subsumed by the new Coverage / Sites / Regional flow (and the drawer covers near-miss diagnostics via its gap cards).

Two screens are intentionally hidden from the sidebar to keep the day-to-day surface tight, but stay reachable by URL when you need the long form:

- **Run Profile (advanced)** — `http://localhost:8501/run_profile` — every `RunProfile` field, including sensitivity defaults and `run_label`.
- **SMR Catalogue (advanced)** — `http://localhost:8501/smr_catalogue` — every `smr_designs` field (cooling, EPZ, regulatory status, …) for every design, in scope or not.

**Use a different port** (e.g. 8501 is already taken)

```bash
streamlit run src/atoms_vs_ashes/gui/app.py --server.port 8502
```

Then open **http://localhost:8502** (or whatever port you chose).

**Headless / remote machine**

If you SSH into a server, Streamlit still listens on a port; you may need port forwarding, for example:

```bash
ssh -L 8501:127.0.0.1:8501 user@host
```

Then open **http://localhost:8501** on your **local** machine while the app runs on the remote host.

---

## 8. Database (required for the GUI)

The GUI talks to Postgres for **every** page now: country / SMR catalogues, threshold overrides, **and** the active run profile. Ensure:

1. `.env` in the repo root contains your DB settings (see project `README.md`).
2. You export anything your deployment needs, e.g.:

   ```bash
   export POSTGRES_DB=atoms_vs_ashes_merged
   ```

3. Run migrations the first time and after every pull:

   ```bash
   ./.venv/bin/python -m alembic upgrade head
   ```

   Alembic revision **039** creates and seeds the singleton `active_run_profile` row that backs the **Run Profile** page.

4. Start the GUI **from the repo root** with the venv activated so relative paths like `audit/.runtime/` resolve correctly.

---

## 9. Run profile management (DB-backed)

The repo no longer ships hand-edited `config/run_profiles/*.yaml` presets. The **active run profile** is one row in the `active_run_profile` Postgres table (alembic 039). The GUI is the source of truth: every page reads from the row, and **Sites & SMR Setup** (with *Run Profile (advanced)* as a fallback) is the only writer.

### Workflow — Sites & SMR Setup (primary)

1. Open **Sites & SMR Setup** (the home screen, also reachable via `http://localhost:8501/`).
2. Edit the day-to-day knobs inline:
   - **Scope**: `Countries` and `SMR designs` multiselects (empty = all).
   - **SMR design parameters (in scope)**: a focused `data_editor` for the four required `smr_designs` fields — `smr_key` (read-only), `name`, `capacity (MWe)`, `land (ha)`. Edit and click **Save SMR designs** to persist to the `smr_designs` table.
   - **Scoring**: `Qualification mode` (radio with rich info-icon explanation), `Top-N per country` (number input), `Near-miss gap %` (slider with rich info-icon explanation).
   - **Advanced (rare)** expander — `weight_profile`, `expert_override`, `notes`, `scope.site_ids`, the `unscored_*` knobs, `weight_overrides`, and the `output.stamp` slug. Most users never open this.
3. The page shows an **Unsaved changes** badge when widget values diverge from the DB row.
4. Click **Save active profile**. The new profile is validated (Pydantic + bounds) and upserted into the DB. Other pages re-read on their next render.
5. Click **Discard changes & reload from DB** to throw away unsaved widget edits and pull the live row again.

**Sites & SMR Setup** hides — and persists unchanged — the fields that have a single sensible value: `run_label` (auto-stamped slug), `db_profile` (always `merged`), `spec_dir` (`config/scoring_specs`), `output.audit_dir`, `output.report_dir`, every `sensitivity.*` field, and `scope.site_status_in`. Edit them on *Run Profile (advanced)* if needed.

### Workflow — Run Profile (advanced) screen (fallback)

`http://localhost:8501/run_profile` shows the full inline editor for every `RunProfile` field, organised into expanders for *Run identity*, *Pipeline*, *Scope*, *Scoring*, *Sensitivity*, *Output*. It is hidden from the sidebar but still routable; use it when you need to edit a hidden field (e.g. tweak `mc_iterations` for a one-off sensitivity stress).

`fail_thresholds` stays on **Site Selection Criteria** (it has its own per-row preview and bounds-checking).

### How runs are launched

The CLI engine still consumes a YAML profile. When you press **Start scoring** / **Start sensitivity** on **Scoring Engine**, the GUI:

1. Loads the live `active_run_profile` row from the DB.
2. Serialises it to `audit/.runtime/active_profile.<run_id>.yaml`.
3. Passes that path to `score run --profile …`.
4. Prunes any `audit/.runtime/active_profile.*.yaml` files older than 24 h (in-flight runs are kept regardless).

The transient YAML is what gets fingerprinted in run provenance, so audits stay byte-identical to a CLI run that pointed at the same content directly.

### SMR Catalogue scope filter

The **SMR Catalogue (advanced)** page (`/smr_catalogue`, hidden from the sidebar) defaults to showing only the SMRs in `scope.smr_keys` of the active profile. Toggle **Show all designs (out-of-scope)** at the top of the page to edit / inspect every row in the DB regardless of scope. A blue banner reminds you when the filter is active. For day-to-day edits to the four required fields (`name`, `capacity_mwe`, `land_requirement_ha`) of the in-scope designs, prefer the inline mini-editor on **Sites & SMR Setup**.

### Recovering a broken row

If the singleton row is somehow deleted or corrupted, every page surfaces an explicit error message. Re-seed by running `./.venv/bin/python -m alembic downgrade 038 && ./.venv/bin/python -m alembic upgrade head` (this re-applies revision 039 and re-inserts the seed payload).

---

## Quick copy-paste (macOS / zsh, from repo root)

The same blocks also appear under **[Dev and production quick start](#dev-and-production-quick-start)** at the top.

**Development — first setup**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[gui,dev]'
atoms-gui
```

Then open **http://localhost:8501** in a browser if one does not open by itself.

**Development — after first setup**

```bash
cd "/path/to/atoms_vs_ashes"
source .venv/bin/activate
atoms-gui
```

**Production** — use the non-editable `pip install '.[gui]'` and `streamlit run … --server.headless true --server.address 0.0.0.0` block from the top section (not duplicated here so flags stay in one place).

---

## Troubleshooting

| Symptom | Cause | Fix |
|--------|--------|-----|
| `zsh: no matches found: .[gui]` | zsh globbing | Use `python -m pip install -e '.[gui]'` (quoted). |
| `error: externally-managed-environment` | System / Homebrew `pip` without a venv | Use steps 2–4: create and **activate** `.venv`, then `python -m pip install -e '.[gui]'`. |
| `command not found: atoms-gui` | Package not installed in this venv, or venv not activated | `source .venv/bin/activate` then re-run step 4. |
| Blank page / connection refused | Wrong URL or server not running | Confirm the terminal still shows Streamlit running; open **http://localhost:8501** (or the port in the terminal). |
| `Address already in use` / port conflict | Another app (or another Streamlit) uses 8501 | Use `--server.port 8502` (see section 7) or stop the other process. |
| Streamlit asks for an email on first run | Streamlit onboarding | You can dismiss it; it is optional. |
| GUI pages error on DB calls | No DB / wrong `POSTGRES_*` | Fix `.env` and `POSTGRES_DB`; confirm `atoms-vs-ashes` works against the same DB. |
| `ModuleNotFoundError: streamlit` | GUI extra not installed in the interpreter you run | Use `python -m pip install -e '.[gui]'` with **this** venv’s `python`. |
