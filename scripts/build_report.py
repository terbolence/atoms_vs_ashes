"""Assemble the Atoms vs Ashes report and export a formatted `.docx`.

Layout and typography are controlled by
``report/version 1.02/output/report/writing plan/report_format.json``.

Run with ``python scripts/build_report.py`` from the repository root.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from make_reference_docx import build_reference_docx
from report_docx_postprocess import postprocess_docx
from report_format_config import DEFAULT_FORMAT_PATH, ReportFormatConfig


REPO_ROOT = Path(__file__).resolve().parent.parent

REPORT_TITLE = "Atoms vs Ashes: Coal-to-Nuclear Siting Assessment"
REPORT_SUBTITLE = "Stage 1 and Stage 2 Siting Study for Central, Eastern and Southern Europe"

COUNTRY_ISO_ORDER: list[str] = [
    "AT", "BA", "BG", "BY", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
]

BANNED_TOKEN_PATTERNS = [
    re.compile(r"sens-[0-9a-f]{8}"),
    re.compile(r"score-[0-9a-f]{8}"),
    re.compile(r"7b609bd0"),
    re.compile(r"214bab4e"),
    re.compile(r"20260502_sensitivity_mc_10000"),
    re.compile(r"/sensitivity/20260425b?/"),
    re.compile(r"\bp16_20260425T[0-9a-zA-Z_]+"),
    re.compile(r"\b20260425T[0-9a-zA-Z_]+"),
]

SPECIALIST_BLOCK_OPEN = re.compile(r"<!--\s*specialist\s+[^>]*-->")
SPECIALIST_BLOCK_CLOSE = re.compile(r"<!--\s*/specialist\s+[^>]*-->")


@dataclass
class Section:
    path: Path
    heading_shift: int = 0
    rename_top_heading: str | None = None


def discover_chapter5_sections(chapters: Path) -> list[Section]:
    sections: list[Section] = []
    chapter5_root = chapters / "05_country_and_site_profiles"

    chapter5_main = chapters / "05_country_and_site_profiles.md"
    if chapter5_main.exists():
        sections.append(Section(chapter5_main))

    for iso in COUNTRY_ISO_ORDER:
        country_file = chapter5_root / f"{iso}_country_prototype.md"
        if country_file.exists():
            sections.append(Section(country_file, heading_shift=1))
            for site_file in sorted((chapter5_root / "sites").glob(f"{iso}_*.md")):
                sections.append(Section(site_file, heading_shift=2))

    for name in (
        "recommended_top5_sites.md",
        "consolidated_failure_section.md",
        "02_ukraine_occupied_territory_caveat_plan.md",
    ):
        path = chapter5_root / name
        if path.exists():
            sections.append(Section(path, heading_shift=1))

    return sections


def discover_sections(
    chapters: Path,
    annexes: Path,
    include_ukraine_caveat: bool = True,
) -> list[Section]:
    sections: list[Section] = []
    for name in (
        "00_acronyms.md",
        "01_introduction.md",
        "02_stage_1_site_survey.md",
        "03_stage_2_site_selection.md",
        "04_results_and_findings.md",
    ):
        path = chapters / name
        if path.exists():
            sections.append(Section(path))

    sections.extend(discover_chapter5_sections(chapters))

    if not include_ukraine_caveat:
        sections = [
            s for s in sections
            if s.path.name != "02_ukraine_occupied_territory_caveat_plan.md"
        ]

    for name in (
        "06_recommendations_for_detailed_site_evaluation.md",
        "07_final_remarks.md",
        "08_references.md",
    ):
        path = chapters / name
        if path.exists():
            sections.append(Section(path))

    for annex in sorted(annexes.glob("annex_*.md")):
        sections.append(Section(annex))

    return sections


def rewrite_image_paths(content: str, source_path: Path) -> str:
    source_dir = source_path.parent

    def _rewrite(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        url = match.group("url")
        trailing = match.group("trailing") or ""

        if url.startswith(("http://", "https://", "mailto:", "#", "/")):
            return match.group(0)

        if url.endswith(".html"):
            candidate_png = source_dir / url.replace(".html", ".png")
            if candidate_png.exists():
                url = url.replace(".html", ".png")
            else:
                return ""

        target = (source_dir / url).resolve()
        if target.exists():
            return f"{prefix}{target.as_posix()}{trailing}"
        return match.group(0)

    content = re.sub(
        r"(?P<prefix>!\[[^\]]*\]\()(?P<url>[^)]+?)(?P<trailing>[^)]*\))",
        _rewrite,
        content,
    )
    content = re.sub(
        r"(?P<prefix>(?<!!)\[[^\]]+\]\()(?P<url>[^)]+?)(?P<trailing>[^)]*\))",
        _rewrite,
        content,
    )
    return content


def shift_headings(content: str, shift: int) -> str:
    if shift <= 0:
        return content

    def _shift(match: re.Match[str]) -> str:
        hashes = match.group(1)
        rest = match.group(2)
        return "#" * min(6, len(hashes) + shift) + rest

    return re.sub(r"^(#{1,6})( .*)$", _shift, content, flags=re.MULTILINE)


def strip_specialist_comments(content: str) -> str:
    content = SPECIALIST_BLOCK_OPEN.sub("", content)
    return SPECIALIST_BLOCK_CLOSE.sub("", content)


def strip_identifier_tokens(content: str) -> str:
    for pattern in BANNED_TOKEN_PATTERNS:
        content = pattern.sub(
            "the project's 10,000-iteration Monte Carlo sensitivity analysis",
            content,
        )
    return content


def prepare_section(section: Section) -> str:
    text = section.path.read_text(encoding="utf-8")
    text = strip_specialist_comments(text)
    text = rewrite_image_paths(text, section.path)
    text = shift_headings(text, section.heading_shift)
    return strip_identifier_tokens(text)


def build_merged_markdown(
    sections: list[Section],
    merged_path: Path,
) -> tuple[int, list[str]]:
    merged_path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    for section in sections:
        if section.path.exists():
            parts.append(prepare_section(section))
            parts.append("\n\n")

    merged = "".join(parts).strip() + "\n"
    merged_path.write_text(merged, encoding="utf-8")

    missing_figures: list[str] = []
    for ref in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", merged):
        if ref.startswith("http"):
            continue
        if not Path(ref).exists():
            missing_figures.append(ref)

    return len([s for s in sections if s.path.exists()]), missing_figures


def run_pandoc(merged_md: Path, output_docx: Path, reference_docx: Path) -> None:
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH; install pandoc first.")

    cmd = [
        "pandoc",
        str(merged_md),
        "-o", str(output_docx),
        "--from=markdown+pipe_tables+header_attributes+fenced_code_blocks",
        "--to=docx",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        f"--reference-doc={reference_docx}",
        "--metadata", f"title={REPORT_TITLE}",
        "--metadata", f"subtitle={REPORT_SUBTITLE}",
    ]
    subprocess.run(cmd, check=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--format",
        type=Path,
        default=DEFAULT_FORMAT_PATH,
        help="Path to report_format.json",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--merged-md", type=Path, default=None)
    parser.add_argument("--keep-merged", action="store_true")
    parser.add_argument(
        "--include-ukraine-caveat",
        dest="include_ukraine_caveat",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no-include-ukraine-caveat",
        dest="include_ukraine_caveat",
        action="store_false",
    )
    parser.add_argument("--skip-postprocess", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fmt = ReportFormatConfig.load(args.format)

    reference_docx = fmt.build_path("reference_docx")
    output_docx = args.out or fmt.build_path("output_docx")
    merged_md = args.merged_md or fmt.build_path("merged_markdown")
    reference_docx.parent.mkdir(parents=True, exist_ok=True)

    if not reference_docx.exists():
        print(f"reference.docx missing; building from {fmt.path} ...")
        build_reference_docx(reference_docx, fmt)

    sections = discover_sections(
        fmt.chapters_dir,
        fmt.annexes_dir,
        include_ukraine_caveat=args.include_ukraine_caveat,
    )
    section_count, missing_figures = build_merged_markdown(sections, merged_md)

    print(f"Merged {section_count} markdown files -> {merged_md}")
    if missing_figures:
        print(f"WARNING: {len(missing_figures)} referenced figures not found on disk:")
        for ref in missing_figures[:10]:
            print(f"  - {ref}")
        if len(missing_figures) > 10:
            print(f"  ... and {len(missing_figures) - 10} more.")

    print(f"Running pandoc -> {output_docx} ...")
    run_pandoc(merged_md, output_docx, reference_docx)

    if not args.skip_postprocess:
        stats = postprocess_docx(output_docx, fmt)
        print(
            f"Post-processed body paragraphs: {stats['body_paragraphs']} "
            f"| tables restyled: {stats['tables']}"
        )

    if not args.keep_merged:
        try:
            merged_md.unlink()
        except FileNotFoundError:
            pass

    print(f"Wrote: {output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
