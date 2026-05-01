# Normative references (local PDFs)

PDFs in this tree are **gitignored** (see `.gitignore`: `sources/regulations/**/*.pdf`). Place downloads here for offline citation and review; they are project inputs, not omitted from “the project” — only from version control.

- Add acquisition notes next to unusual sources in `docs/large_assets_required.txt` or team docs if a path must exist for report reproducibility.
- Regenerate the size manifest after adding large PDFs: `python src/scripts/list_large_files.py --write-doc`.

Folder layout is by publisher or topic (e.g. `dos/`, `iaea/`). Keep filenames stable so report paths and the required-assets list stay valid.
