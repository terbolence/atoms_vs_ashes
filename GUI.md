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

The **Results** page replaces the previous *Country Drill-Down*, *Near Miss*, and *Sensitivity* screens. It opens with a run-picker dropdown listing every persisted run (cancelled / rolled-back runs do not appear) and exposes four tabs:

- **Country** — DB-backed per-country breakdown (pairs scored, pairs passed, mean composite). Augmented with the per-country margins and worst-offender chart when a metrics bundle is loaded.
- **Top sites** — DB-backed ranking of (site × SMR) pairs by composite score, with toggles for "passed both floors only" and a row-limit slider.
- **Near miss** — Reads the metrics bundle; shows a clear hint when none is present (this analysis is computed offline by `generate_failure_analysis.py`).
- **Sensitivity** — DB-backed snapshot for sensitivity runs (MC iterations, weight-profile breakdown, country-balance, threshold sweep) plus optional metrics-bundle extras (per-pair MC distribution, OAT importance, weight-perturbation diff tables).

Loading a `*_metrics.json` bundle is **optional** — every tab now renders meaningful content from the database after a successful run on **Scoring Engine**. The bundle simply unlocks the heavier offline panels.

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
