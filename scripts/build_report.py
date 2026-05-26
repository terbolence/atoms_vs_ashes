# man_hours: 9.0
"""Assemble the report and export a formatted `.docx`."""

from __future__ import annotations

import argparse
import re
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
from report_section_discovery import Section, discover_sections
from report_side_deliverables import build_side_deliverables

REPORT_TITLE = "Atoms vs Ashes: Coal-to-Nuclear Siting Assessment"
REPORT_SUBTITLE = "Stage 1 and Stage 2 Siting Study for Central, Eastern and Southern Europe"

# Tokens whose mere presence on a line means the entire line must be deleted
# from the merged report source. The user instructed: "The report should not
# contain any run ids of any kind." The previous substitution-with-placeholder
# strategy produced ungrammatical sentences (e.g. dangling "nat-" prefixes),
# so we now remove the whole line outright.
RUNID_LINE_PATTERNS = [
    re.compile(r"score-[0-9a-f]{8}"),
    re.compile(r"sens-[0-9a-f]{8}"),
    re.compile(r"nat-sens-[0-9a-f]{8}"),
    re.compile(r"swing_20[0-9]{6}_[0-9a-f]{8}"),
    re.compile(r"corr_20[0-9]{6}_[0-9a-f]{8}"),
    re.compile(r"fail_20[0-9]{6}_[0-9a-f]{8}"),
    re.compile(r"p16ext_20[0-9]{8}T[0-9]+_[0-9a-f]{8}"),
    re.compile(r"\bp16_20260425T[0-9a-zA-Z_]+"),
    re.compile(r"\b20260425T[0-9a-zA-Z_]+"),
    re.compile(r"7b609bd0"),
    re.compile(r"214bab4e"),
    re.compile(r"20260502_sensitivity_mc_10000"),
    re.compile(r"/sensitivity/20260425b?/"),
]

# Tokens we want to strip in-place (without deleting the whole line), because
# the surrounding sentence is still useful prose. Currently used only for
# explicit non-NuScale SMR names — the report is restricted to NuScale VOYGR-6
# by user instruction. If any non-NuScale SMR name slips through into the
# published source, the build scrubs it inline.
NONNUSCALE_SMR_PATTERNS = [
    re.compile(r"\bBWRX[-_ ]?300\b", re.IGNORECASE),
    re.compile(r"\bHoltec(?:[-_ ]?SMR)?[-_ ]?300\b", re.IGNORECASE),
    re.compile(r"\bNatrium\b", re.IGNORECASE),
    re.compile(r"\bOklo(?:[-_ ]?Aurora)?\b", re.IGNORECASE),
    re.compile(r"\bRolls[-_ ]?Royce(?:[-_ ]?SMR)?\b", re.IGNORECASE),
    re.compile(r"\bX[-_ ]?energy\b", re.IGNORECASE),
    re.compile(r"\bXe[-_ ]?100\b", re.IGNORECASE),
]

SPECIALIST_BLOCK_OPEN = re.compile(r"<!--\s*specialist\s+[^>]*-->")
SPECIALIST_BLOCK_CLOSE = re.compile(r"<!--\s*/specialist\s+[^>]*-->")

# Blockquote-italic "Specialist interpretation pending: ..." placeholder
# lines emitted by the country / site profile generators when the specialist
# LLM pass has not yet been run. They are drafting notes and must not appear
# in the published DOCX (format JSON `publication_rules`).
SPECIALIST_PENDING_LINE = re.compile(
    r"^\s*>\s*_Specialist interpretation pending:.*$",
    re.MULTILINE,
)

# Inline backtick filename references like `sites_evaluation.md` are
# "internal project file references" which the format JSON `publication_rules`
# forbid in reader-facing text. The user reinforced this: "Never use any .md
# references in the report." We strip the backticked token to plain prose
# (without the `.md` suffix). For example, `sites_evaluation.md` -> sites
# evaluation. The replacement is conservative — it only affects backticked
# bare filenames, not Markdown link syntax (already handled by
# strip_local_markdown_links).
INLINE_MD_FILENAME = re.compile(r"`([A-Za-z0-9_./-]+)\.md`")

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
LOCAL_MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def rewrite_image_paths(content: str, source_path: Path, assets_dir: Path) -> str:
    source_dir = source_path.parent

    def _rewrite(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        url = match.group("url")

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
            assets_dir.mkdir(parents=True, exist_ok=True)
            asset_path = assets_dir / target.name
            if asset_path.resolve() != target:
                shutil.copy2(target, asset_path)
            asset_ref = f"{assets_dir.name}/{asset_path.name}"
            return f"{prefix}{asset_ref})"
        if prefix.startswith("!"):
            return ""
        return match.group(0)

    return re.sub(
        r"(?P<prefix>!\[[^\]]*\]\()(?P<url>[^)]+)\)",
        _rewrite,
        content,
    )


def strip_local_markdown_links(content: str) -> str:
    def _strip(match: re.Match[str]) -> str:
        label, url = match.groups()
        if url.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        return label

    return LOCAL_MARKDOWN_LINK.sub(_strip, content)


def strip_html_comments(content: str) -> str:
    return HTML_COMMENT.sub("", content)


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


def strip_runid_lines(content: str) -> str:
    """Drop every line that contains a project run-ID token."""
    kept: list[str] = []
    for line in content.splitlines(keepends=True):
        if any(pattern.search(line) for pattern in RUNID_LINE_PATTERNS):
            continue
        kept.append(line)
    return "".join(kept)


def strip_nonnuscale_smr_names(content: str) -> str:
    """Remove non-NuScale SMR names from prose (NuScale VOYGR-6 only)."""
    for pattern in NONNUSCALE_SMR_PATTERNS:
        content = pattern.sub("", content)
    return content


def strip_specialist_pending_blocks(content: str) -> str:
    """Drop blockquote-italic 'Specialist interpretation pending: ...' notes."""
    return SPECIALIST_PENDING_LINE.sub("", content)


def strip_inline_md_filenames(content: str) -> str:
    """Replace `<name>.md` backticked references with plain prose `<name>`."""
    def _replace(match: re.Match[str]) -> str:
        ref = match.group(1)
        leaf = ref.rsplit("/", 1)[-1].replace("_", " ")
        return leaf
    return INLINE_MD_FILENAME.sub(_replace, content)


def prepare_section(section: Section, assets_dir: Path) -> str:
    text = section.path.read_text(encoding="utf-8")
    text = strip_specialist_comments(text)
    text = strip_html_comments(text)
    text = strip_specialist_pending_blocks(text)
    text = rewrite_image_paths(text, section.path, assets_dir)
    text = strip_local_markdown_links(text)
    text = shift_headings(text, section.heading_shift)
    text = strip_runid_lines(text)
    text = strip_nonnuscale_smr_names(text)
    return strip_inline_md_filenames(text)


def build_merged_markdown(
    sections: list[Section],
    merged_path: Path,
    fmt: ReportFormatConfig,
) -> tuple[int, list[str]]:
    merged_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = merged_path.parent / "assets"
    parts: list[str] = [fmt.title_page_markdown()]
    for section in sections:
        if section.path.exists():
            parts.append(prepare_section(section, assets_dir))
            parts.append("\n\n")

    merged = "".join(parts).strip() + "\n"
    merged_path.write_text(merged, encoding="utf-8")

    missing_figures: list[str] = []
    for ref in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", merged):
        if ref.startswith("http"):
            continue
        ref_path = Path(ref)
        if not ref_path.is_absolute():
            ref_path = merged_path.parent / ref_path
        if not ref_path.exists():
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
    subprocess.run(cmd, check=True, cwd=merged_md.parent)


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
    parser.add_argument("--skip-postprocess", action="store_true")
    parser.add_argument(
        "--side-deliverables-only",
        action="store_true",
        help="Generate only the results table and work-audit synthesis deliverables.",
    )
    parser.add_argument(
        "--skip-side-deliverables",
        action="store_true",
        help="Build only the main report DOCX.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fmt = ReportFormatConfig.load(args.format)

    if args.side_deliverables_only:
        build_side_deliverables(fmt)
        return 0

    reference_docx = ensure_reference_docx(fmt)
    output_docx = args.out or fmt.build_path("output_docx")
    merged_md = args.merged_md or fmt.build_path("merged_markdown")

    sections = discover_sections(
        fmt.chapters_dir,
        fmt.annexes_dir,
    )
    section_count, missing_figures = build_merged_markdown(sections, merged_md, fmt)

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
    if not args.skip_side_deliverables:
        build_side_deliverables(fmt)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
