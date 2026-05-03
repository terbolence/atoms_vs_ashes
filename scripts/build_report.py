"""Assemble the Atoms vs Ashes report and export a formatted `.docx`.

The script:

1. Walks a deterministic chapter / annex order built from `report/output/`.
2. Concatenates source markdown into a single merged file.
3. Rewrites relative image paths to absolute paths.
4. Strips the specialist HTML placeholder comments so they do not appear in the
   rendered document.
5. Defensively removes any remaining run-identifier or date-stamp tokens.
6. Normalises heading levels so the final document has a single title, chapters
   at Heading 1, numbered subsections at Heading 2, site blocks at Heading 3.
7. Invokes pandoc with the project reference template and an auto-generated
   table of contents.
8. Post-processes the resulting .docx with python-docx: body alignment (justify),
   line spacing 1.2, table borders, header-row shading, cell vertical alignment,
   numeric column centring, full page-width tables.

Run with `python scripts/build_report.py` from the repository root.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_ROOT = REPO_ROOT / "report" / "output"
CHAPTERS = REPORT_ROOT / "chapters"
ANNEXES = REPORT_ROOT / "annexes"
BUILD_DIR = REPORT_ROOT / "build"
REFERENCE_DOCX = BUILD_DIR / "reference.docx"

REPORT_TITLE = "Atoms vs Ashes: Coal-to-Nuclear Siting Assessment"
REPORT_SUBTITLE = "Stage 1 and Stage 2 Siting Study for Central, Eastern and Southern Europe"

# Country order for Chapter 5.
COUNTRY_ISO_ORDER: list[str] = [
    "AT", "BA", "BG", "BY", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
]

# Identifier tokens that must not reach the rendered manuscript.
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

# Remove specialist placeholder blocks from rendered output; their content
# outside the tags is kept.
SPECIALIST_BLOCK_OPEN = re.compile(r"<!--\s*specialist\s+[^>]*-->")
SPECIALIST_BLOCK_CLOSE = re.compile(r"<!--\s*/specialist\s+[^>]*-->")


@dataclass
class Section:
    """One markdown block to include in the merged file."""

    path: Path
    heading_shift: int = 0   # add N levels to every heading in the source
    rename_top_heading: str | None = None


def discover_chapter5_sections() -> list[Section]:
    """Build the Chapter 5 assembly order deterministically."""
    sections: list[Section] = []
    chapter5_root = CHAPTERS / "05_country_and_site_profiles"

    chapter5_main = CHAPTERS / "05_country_and_site_profiles.md"
    if chapter5_main.exists():
        sections.append(Section(chapter5_main))

    for iso in COUNTRY_ISO_ORDER:
        country_file = chapter5_root / f"{iso}_country_prototype.md"
        if country_file.exists():
            sections.append(Section(country_file, heading_shift=1))

            site_files = sorted(
                (chapter5_root / "sites").glob(f"{iso}_*.md")
            )
            for sf in site_files:
                sections.append(Section(sf, heading_shift=2))

    top5 = chapter5_root / "recommended_top5_sites.md"
    if top5.exists():
        sections.append(Section(top5, heading_shift=1))

    failures = chapter5_root / "consolidated_failure_section.md"
    if failures.exists():
        sections.append(Section(failures, heading_shift=1))

    ua_caveat = chapter5_root / "02_ukraine_occupied_territory_caveat_plan.md"
    if ua_caveat.exists():
        sections.append(Section(ua_caveat, heading_shift=1))

    return sections


def discover_sections(include_ukraine_caveat: bool = True) -> list[Section]:
    """Return the ordered list of markdown sections to merge."""
    sections: list[Section] = []

    for name in ("00_acronyms.md",
                 "01_introduction.md",
                 "02_stage_1_site_survey.md",
                 "03_stage_2_site_selection.md",
                 "04_results_and_findings.md"):
        p = CHAPTERS / name
        if p.exists():
            sections.append(Section(p))

    sections.extend(discover_chapter5_sections())

    if not include_ukraine_caveat:
        sections = [s for s in sections
                    if s.path.name != "02_ukraine_occupied_territory_caveat_plan.md"]

    for name in ("06_recommendations_for_detailed_site_evaluation.md",
                 "07_final_remarks.md",
                 "08_references.md"):
        p = CHAPTERS / name
        if p.exists():
            sections.append(Section(p))

    for annex in sorted(ANNEXES.glob("annex_*.md")):
        sections.append(Section(annex))

    return sections


def rewrite_image_paths(content: str, source_path: Path) -> str:
    """Rewrite relative markdown image and link URLs to absolute paths."""
    source_dir = source_path.parent

    def _rewrite(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        url = match.group("url")
        trailing = match.group("trailing") or ""

        if url.startswith(("http://", "https://", "mailto:", "#", "/")):
            return match.group(0)

        # Pandoc cannot embed interactive HTML maps. Swap to the .png sibling
        # when it exists.
        if url.endswith(".html"):
            candidate_png = source_dir / url.replace(".html", ".png")
            if candidate_png.exists():
                url = url.replace(".html", ".png")
            else:
                # Drop interactive-only links from the rendered output.
                return ""

        target = (source_dir / url).resolve()
        if target.exists():
            return f"{prefix}{target.as_posix()}{trailing}"
        return match.group(0)

    img_re = re.compile(
        r"(?P<prefix>!\[[^\]]*\]\()(?P<url>[^)\s]+)(?P<trailing>[^)]*\))"
    )
    content = img_re.sub(_rewrite, content)

    link_re = re.compile(
        r"(?P<prefix>(?<!!)\[[^\]]+\]\()(?P<url>[^)\s]+)(?P<trailing>[^)]*\))"
    )
    content = link_re.sub(_rewrite, content)
    return content


def shift_headings(content: str, shift: int) -> str:
    """Shift every markdown heading deeper by `shift` levels (max 6)."""
    if shift <= 0:
        return content

    def _shift(match: re.Match[str]) -> str:
        hashes = match.group(1)
        rest = match.group(2)
        new_level = min(6, len(hashes) + shift)
        return "#" * new_level + rest

    return re.sub(r"^(#{1,6})( .*)$", _shift, content, flags=re.MULTILINE)


def strip_specialist_comments(content: str) -> str:
    content = SPECIALIST_BLOCK_OPEN.sub("", content)
    content = SPECIALIST_BLOCK_CLOSE.sub("", content)
    return content


def strip_identifier_tokens(content: str) -> str:
    for pattern in BANNED_TOKEN_PATTERNS:
        content = pattern.sub("the project's 10,000-iteration Monte Carlo sensitivity analysis", content)
    return content


def prepare_section(section: Section) -> str:
    text = section.path.read_text(encoding="utf-8")
    text = strip_specialist_comments(text)
    text = rewrite_image_paths(text, section.path)
    text = shift_headings(text, section.heading_shift)
    text = strip_identifier_tokens(text)
    return text


def build_merged_markdown(
    sections: list[Section], merged_path: Path
) -> tuple[int, list[str]]:
    """Concatenate section markdown into `merged_path`. Returns counts."""
    missing_figures: list[str] = []

    merged_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    for section in sections:
        if not section.path.exists():
            continue
        parts.append(prepare_section(section))
        parts.append("\n\n")

    merged = "".join(parts).strip() + "\n"
    merged_path.write_text(merged, encoding="utf-8")

    image_refs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", merged)
    for ref in image_refs:
        if ref.startswith("http"):
            continue
        if not Path(ref).exists():
            missing_figures.append(ref)

    return len([s for s in sections if s.path.exists()]), missing_figures


def run_pandoc(merged_md: Path, output_docx: Path) -> None:
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
        f"--reference-doc={REFERENCE_DOCX}",
        "--metadata", f"title={REPORT_TITLE}",
        "--metadata", f"subtitle={REPORT_SUBTITLE}",
    ]
    subprocess.run(cmd, check=True)


def _set_cell_vertical_center(cell) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _set_cell_borders(cell) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:tcBorders"))
    if existing is not None:
        tcPr.remove(existing)
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")        # 0.5 pt
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    tcPr.append(borders)


def _set_table_borders(table) -> None:
    tblPr = table._tbl.tblPr
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    tblPr.append(borders)


def _set_table_full_width(table) -> None:
    tblPr = table._tbl.tblPr
    existing = tblPr.find(qn("w:tblW"))
    if existing is not None:
        tblPr.remove(existing)
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), "5000")   # 50 * 100 = pct * 50 when type = pct
    w.set(qn("w:type"), "pct")
    tblPr.append(w)


def _shade_cell(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:shd"))
    if existing is not None:
        tcPr.remove(existing)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_row_as_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    trPr.append(header)


_NUMERIC_PATTERN = re.compile(r"^\s*[+-]?\$?[0-9][0-9,]*(?:\.[0-9]+)?\s*%?\s*$")


def _cell_is_numeric(text: str) -> bool:
    if not text:
        return False
    return bool(_NUMERIC_PATTERN.match(text.strip()))


def _column_alignments(table) -> list[int]:
    """Return WD_ALIGN_PARAGRAPH for each column (CENTER if > 60% numeric, else LEFT)."""
    if len(table.rows) <= 1:
        return [WD_ALIGN_PARAGRAPH.LEFT for _ in range(len(table.columns))]

    num_cols = len(table.columns)
    alignments = [WD_ALIGN_PARAGRAPH.LEFT] * num_cols
    for ci in range(num_cols):
        numeric_cells = 0
        non_empty = 0
        for ri, row in enumerate(table.rows):
            if ri == 0:
                continue
            text = row.cells[ci].text.strip()
            if not text:
                continue
            non_empty += 1
            if _cell_is_numeric(text):
                numeric_cells += 1
        if non_empty and numeric_cells / non_empty >= 0.6:
            alignments[ci] = WD_ALIGN_PARAGRAPH.CENTER
    return alignments


def _apply_paragraph_defaults(paragraph) -> None:
    pf = paragraph.paragraph_format
    if pf.alignment is None:
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.line_spacing = 1.2
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE


def postprocess_docx(docx_path: Path) -> dict[str, int]:
    doc = Document(docx_path)

    body_paragraph_count = 0
    for paragraph in doc.paragraphs:
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name.startswith("Heading") or style_name in ("Title", "TOC Heading"):
            continue
        if style_name.startswith("TOC"):
            continue
        _apply_paragraph_defaults(paragraph)
        body_paragraph_count += 1

    table_count = 0
    for table in doc.tables:
        _set_table_borders(table)
        _set_table_full_width(table)
        alignments = _column_alignments(table)

        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                _set_cell_vertical_center(cell)
                _set_cell_borders(cell)

                alignment = alignments[ci] if ci < len(alignments) else WD_ALIGN_PARAGRAPH.LEFT
                for paragraph in cell.paragraphs:
                    pf = paragraph.paragraph_format
                    pf.alignment = alignment
                    pf.line_spacing = 1.15
                    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                    pf.space_before = Pt(0)
                    pf.space_after = Pt(0)

                if ri == 0:
                    _shade_cell(cell, "D9D9D9")
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True

        if table.rows:
            _set_row_as_header(table.rows[0])

        table_count += 1

    doc.save(docx_path)
    return {
        "body_paragraphs": body_paragraph_count,
        "tables": table_count,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path,
                        default=BUILD_DIR / "atoms_vs_ashes_report.docx")
    parser.add_argument("--merged-md", type=Path,
                        default=BUILD_DIR / "merged.md")
    parser.add_argument("--keep-merged", action="store_true",
                        help="Retain the intermediate merged.md for review.")
    parser.add_argument("--include-ukraine-caveat", dest="include_ukraine_caveat",
                        action="store_true", default=True)
    parser.add_argument("--no-include-ukraine-caveat",
                        dest="include_ukraine_caveat", action="store_false")
    parser.add_argument("--skip-postprocess", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if not REFERENCE_DOCX.exists():
        print("reference.docx missing; regenerating from scripts/make_reference_docx.py ...")
        subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "make_reference_docx.py")], check=True)

    sections = discover_sections(include_ukraine_caveat=args.include_ukraine_caveat)
    section_count, missing_figures = build_merged_markdown(sections, args.merged_md)

    print(f"Merged {section_count} markdown files -> {args.merged_md}")
    if missing_figures:
        print(f"WARNING: {len(missing_figures)} referenced figures not found on disk:")
        for ref in missing_figures[:10]:
            print(f"  - {ref}")
        if len(missing_figures) > 10:
            print(f"  ... and {len(missing_figures) - 10} more.")

    print(f"Running pandoc -> {args.out} ...")
    run_pandoc(args.merged_md, args.out)

    if not args.skip_postprocess:
        stats = postprocess_docx(args.out)
        print(f"Post-processed body paragraphs: {stats['body_paragraphs']} "
              f"| tables restyled: {stats['tables']}")

    if not args.keep_merged:
        try:
            args.merged_md.unlink()
        except FileNotFoundError:
            pass

    print(f"Wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
