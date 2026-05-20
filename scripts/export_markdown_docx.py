# man_hours: 3.0
"""Export one or more markdown files to .docx using report_format.json.

Example::

    python scripts/export_markdown_docx.py \\
        report/version\\ 1.02/output/report/chapters/01_introduction.md \\
        --out-dir report/version\\ 1.02/output/report/build/format_samples
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from report_docx_postprocess import postprocess_docx
from report_format_config import (
    DEFAULT_FORMAT_PATH,
    ReportFormatConfig,
    ensure_reference_docx,
)

from build_report import rewrite_image_paths, strip_identifier_tokens, strip_specialist_comments


def export_markdown(
    source: Path,
    output: Path,
    *,
    fmt: ReportFormatConfig,
    reference_docx: Path,
    skip_postprocess: bool = False,
) -> Path:
    source = source.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    text = source.read_text(encoding="utf-8")
    text = strip_specialist_comments(text)
    text = rewrite_image_paths(text, source)
    text = strip_identifier_tokens(text)
    text = fmt.title_page_markdown() + text

    staging_md = output.with_suffix(".staging.md")
    staging_md.write_text(text, encoding="utf-8")

    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH; install pandoc first.")

    cmd = [
        "pandoc",
        str(staging_md),
        "-o", str(output),
        "--from=markdown+pipe_tables+header_attributes+fenced_code_blocks",
        "--to=docx",
        "--standalone",
        f"--reference-doc={reference_docx}",
        "--metadata", f"title={source.stem.replace('_', ' ')}",
    ]
    subprocess.run(cmd, check=True)

    if not skip_postprocess:
        postprocess_docx(output, fmt)

    staging_md.unlink(missing_ok=True)
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sources", nargs="+", type=Path, help="Markdown files to export")
    parser.add_argument(
        "--format",
        type=Path,
        default=DEFAULT_FORMAT_PATH,
        help="Path to report_format.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: <report_root>/build/format_samples)",
    )
    parser.add_argument("--skip-postprocess", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fmt = ReportFormatConfig.load(args.format)
    out_dir = args.out_dir or (fmt.build_path("output_docx").parent / "format_samples")
    reference_docx = ensure_reference_docx(fmt)

    written: list[Path] = []
    for source in args.sources:
        if not source.exists():
            print(f"ERROR: source not found: {source}", file=sys.stderr)
            return 1
        output = out_dir / f"{source.stem}.docx"
        export_markdown(
            source,
            output,
            fmt=fmt,
            reference_docx=reference_docx,
            skip_postprocess=args.skip_postprocess,
        )
        written.append(output)
        print(f"Wrote: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
