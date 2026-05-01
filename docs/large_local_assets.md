# Large local assets (stewardship)

Binaries and caches stay **out of git** so the repository stays cloneable and lean. They remain **first-class inputs** for screening, analysis, and report writing — they are only excluded from version control, not from the project.

## What we track in-repo

| Artefact | Purpose |
| --- | --- |
| [.gitignore](../.gitignore) | Declares patterns that must never be committed (WDPA shapes, rasters, PDFs, exports, …). |
| [large_assets.md](large_assets.md) | **Auto-generated** manifest of everything ≥ 2 MiB present on disk when you run the scanner (sizes and paths vary by machine). |
| [large_assets_required.txt](large_assets_required.txt) | **Human-maintained** list of files we expect for writing or citing key deliverables; optional gate via `--verify`. |

## Commands (from repository root)

Regenerate the size manifest (commit when you want the doc snapshot updated):

```bash
python src/scripts/list_large_files.py --write-doc
```

Check that every path in `large_assets_required.txt` exists locally:

```bash
python src/scripts/list_large_files.py --verify
```

List large files to stdout without writing the doc:

```bash
python src/scripts/list_large_files.py
```

## Workflow

1. **Clone** the repo; large inputs are **not** included.
2. **Restore** ignored assets from team storage (e.g. shared Drive), connector downloads, or manual drops under `sources/` and `report/` as documented in the manifest “How to obtain” column and data-acquisition specs under `src/dataAcquisition/specifications/`.
3. **Regenerate** `docs/large_assets.md` after large pulls so everyone sees what this checkout actually contains.
4. When a deliverable **depends on a specific file**, add its repo-relative path to `large_assets_required.txt` so `python src/scripts/list_large_files.py --verify` can catch a missing PDF or spreadsheet before writing or publishing.

## Smaller ignored files

The scanner only lists files **≥ 2 MiB**. Normative PDFs under ~2 MiB still follow the same gitignore rules; keep them under `sources/regulations/` (and optionally extend `large_assets_required.txt` even when they are small).
