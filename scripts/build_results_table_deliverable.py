# man_hours: 1.2
"""Build the v1.2 landscape results-table deliverable.

This module is the only supported build path for ``atoms_vs_ashes_results_table``
(``.md``, ``.csv``, and landscape ``.docx``). It always regenerates Markdown from
country ledgers before exporting Word.

Run directly::

    python scripts/build_results_table_deliverable.py

Or through the report build::

    python scripts/build_report.py --side-deliverables-only
    python scripts/build_report.py   # unless --skip-side-deliverables

Do not use ``scripts/export_markdown_docx.py`` on the results-table Markdown.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Mm

from report_docx_postprocess import postprocess_docx
from report_format_config import (
    DEFAULT_FORMAT_PATH,
    ReportFormatConfig,
    ensure_reference_docx,
)
from results_table_data import build_results_markdown
from results_table_model import RESULTS_TABLE_OUTPUT_STEM, configure_from_format

OUTPUT_STEM = RESULTS_TABLE_OUTPUT_STEM

_MANUAL_EXPORT_ERROR = (
    "The results table must be built with scripts/build_results_table_deliverable.py "
    "(or python scripts/build_report.py --side-deliverables-only), which regenerates "
    "Markdown and CSV from country ledgers before exporting DOCX. "
    "export_markdown_docx.py is not supported for this deliverable."
)


def is_results_table_markdown(path: Path) -> bool:
    return path.resolve().stem == OUTPUT_STEM


def reject_manual_results_table_export(path: Path) -> None:
    if is_results_table_markdown(path):
        raise ValueError(_MANUAL_EXPORT_ERROR)


def _run_pandoc(markdown_path: Path, output_docx: Path, reference_docx: Path) -> None:
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH; install pandoc first.")
    markdown_path = markdown_path.resolve()
    output_docx = output_docx.resolve()
    reference_docx = reference_docx.resolve()
    command = [
        "pandoc",
        markdown_path.name,
        "-o",
        str(output_docx),
        "--from=markdown+pipe_tables+header_attributes+fenced_code_blocks",
        "--to=docx",
        "--standalone",
        f"--reference-doc={reference_docx}",
        "--metadata",
        "title=Atoms vs Ashes Results Table",
    ]
    subprocess.run(command, check=True, cwd=markdown_path.parent)


def _set_landscape_a3(docx_path: Path, config: ReportFormatConfig) -> None:
    doc = Document(docx_path)
    margins = config.margins_mm()
    for section in doc.sections:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Mm(420)
        section.page_height = Mm(297)
        section.top_margin = Mm(margins["top"])
        section.bottom_margin = Mm(margins["bottom"])
        section.left_margin = Mm(margins["inside"])
        section.right_margin = Mm(margins["outside"])
    doc.save(docx_path)


def build_results_table_deliverable(
    *,
    format_path: Path = DEFAULT_FORMAT_PATH,
    output_dir: Path | None = None,
) -> dict[str, int | str]:
    fmt = ReportFormatConfig.load(format_path)
    configure_from_format(fmt)
    build_dir = output_dir or fmt.report_root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = build_dir / f"{OUTPUT_STEM}.md"
    csv_path = build_dir / f"{OUTPUT_STEM}.csv"
    output_docx = build_dir / f"{OUTPUT_STEM}.docx"
    stats = build_results_markdown(markdown_path, csv_path, OUTPUT_STEM)
    reference_docx = ensure_reference_docx(fmt)
    _run_pandoc(markdown_path, output_docx, reference_docx)
    postprocess_docx(output_docx, fmt)
    _set_landscape_a3(output_docx, fmt)
    stats.update({
        "markdown": str(markdown_path),
        "csv": str(csv_path),
        "docx": str(output_docx),
    })
    return stats


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", type=Path, default=DEFAULT_FORMAT_PATH)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stats = build_results_table_deliverable(
        format_path=args.format,
        output_dir=args.output_dir,
    )
    print(
        "Built results-table deliverable: "
        f"{stats['docx']} ({stats['selected_site_rows']} site rows, "
        f"{stats['copied_maps']} maps)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
