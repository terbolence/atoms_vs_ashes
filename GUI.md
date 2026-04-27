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
- For pages that load countries / SMRs from the database: a working **PostgreSQL** connection in **`.env`** (same as for `atoms-vs-ashes`). Pages that only edit YAML / preview the rubric can work without DB access until you hit a DB-backed widget.

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

The home view is the landing text. Use the **sidebar** (left) to switch between pages such as **SMR Catalogue**, **Run Profile**, **Threshold editor**, **Run dashboard**, and so on.

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

## 8. Database (when you need live country / SMR lists)

The **Run profile** page queries Postgres for countries and SMR designs. Ensure:

1. `.env` in the repo root contains your DB settings (see project `README.md`).
2. You export anything your deployment needs, e.g.:

   ```bash
   export POSTGRES_DB=atoms_vs_ashes_merged
   ```

3. Start the GUI **from the repo root** with the venv activated so relative paths like `config/run_profiles/` resolve correctly.

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
