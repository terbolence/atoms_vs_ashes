"""Extract reviewer comments from a `.docx`, with rich anchored context.

A `.docx` is a ZIP archive. Reviewer comments live in `word/comments.xml`
(typically a few KB even for very large reports), with optional threading and
resolution metadata in `word/commentsExtended.xml`. By default this script
also streams `word/document.xml` to attach, per comment:

- the **heading path** (chapter -> section -> ...);
- the **anchor span** (what the reviewer highlighted);
- the **anchor paragraph** in full plus the **preceding** and **following**
  paragraph for surrounding context;
- a **subsection-relative paragraph index** so the comment can be pinpointed
  inside the section; and
- a resolved **report-file pointer** (``chapters/02_...md`` or a per-site
  Markdown file) when the heading path can be matched to a v1.03 source file.

Outputs (next to the input by default):

  - `<stem>_comments.json`  — machine-readable list of comments + context
  - `<stem>_comments.md`    — numbered, human-readable digest
  - `<stem>_triage.yaml`    — idempotent triage scaffold (or `.json` fallback)

Usage:
    python src/scripts/extract_docx_comments.py
    python src/scripts/extract_docx_comments.py --input path/to/file.docx
    python src/scripts/extract_docx_comments.py --no-anchors
    python src/scripts/extract_docx_comments.py --no-triage
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Iterable

from _docx_comment_anchors import Anchor, extract_anchors
from _docx_comment_parse import (
    COMMENTS_EXT_PART,
    COMMENTS_PART,
    DOCUMENT_PART,
    Comment,
    ext_paraid_to_comment_id,
    merge_extended,
    parse_comments,
    parse_extended,
    read_part,
)
from _docx_comment_report_paths import ReportPathIndex, detect_language
from _docx_comment_triage import TriageInputComment, write_triage
from _docx_comment_writers import write_json, write_markdown

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    PROJECT_ROOT / "report" / "output" / "feedback" / "atoms_vs_ashes_report_feedback.docx"
)


def merge_anchors(comments: list[Comment], anchors: dict[str, Anchor]) -> int:
    matched = 0
    for c in comments:
        a = anchors.get(c.id)
        if a is None:
            continue
        c.anchor_text = a.anchor_text
        c.anchor_chars = a.anchor_chars
        c.heading_path = list(a.heading_path)
        c.chapter = a.chapter
        c.section_heading = a.section_heading or None
        c.paragraph_index = a.paragraph_index
        c.subsection_paragraph_index = a.subsection_paragraph_index
        c.span_paragraphs = a.span_paragraphs
        c.paragraph_text = a.paragraph_text or None
        c.prev_paragraph_text = a.prev_paragraph_text or None
        c.next_paragraph_text = a.next_paragraph_text or None
        matched += 1
    return matched


def annotate_languages(comments: list[Comment]) -> None:
    for c in comments:
        lang = detect_language(c.text or "")
        c.language = lang or None


def attach_report_paths(comments: list[Comment], index: ReportPathIndex) -> None:
    for c in comments:
        if not c.heading_path:
            continue
        rel = index.resolve(c.heading_path)
        if rel:
            c.report_path = rel


def extract(docx_path: Path, *, with_anchors: bool = True, max_anchor_chars: int = 400) -> list[Comment]:
    if not docx_path.exists():
        raise SystemExit(f"Input not found: {docx_path}")
    with zipfile.ZipFile(docx_path) as zf:
        comments_xml = read_part(zf, COMMENTS_PART)
        if comments_xml is None:
            members = [n for n in zf.namelist() if "comment" in n.lower()]
            raise SystemExit(
                f"`{COMMENTS_PART}` not found in {docx_path.name}. "
                f"Comment-related entries: {members or 'none'}"
            )
        ext_xml = read_part(zf, COMMENTS_EXT_PART)
        document_xml = read_part(zf, DOCUMENT_PART) if with_anchors else None

    comments = parse_comments(comments_xml)
    if ext_xml is not None:
        merge_extended(comments, parse_extended(ext_xml))
    if document_xml is not None:
        valid_ids = {c.id for c in comments}
        anchors = extract_anchors(document_xml, valid_ids, max_anchor_chars=max_anchor_chars)
        merge_anchors(comments, anchors)
    annotate_languages(comments)
    return comments


def _infer_report_root(docx_path: Path) -> Path | None:
    """Walk upwards looking for an ``output/report/chapters`` sibling."""
    for parent in [docx_path.parent, *docx_path.parents]:
        candidate = parent / "output" / "report"
        if (candidate / "chapters").is_dir():
            return candidate
        if (parent / "chapters").is_dir() and parent.name == "report":
            return parent
    return None


def _to_triage_inputs(comments: list[Comment], parent_lookup: dict[str, str]) -> list[TriageInputComment]:
    items: list[TriageInputComment] = []
    for c in comments:
        parent_id = parent_lookup.get(c.parent_para_id) if c.parent_para_id else None
        items.append(
            TriageInputComment(
                id=c.id,
                author=c.author,
                date=c.date,
                text=c.text,
                chapter=c.chapter or "",
                heading_path=list(c.heading_path),
                anchor_excerpt=c.anchor_text or "",
                done=c.done,
                parent_id=parent_id,
                report_path=c.report_path,
                section_heading=c.section_heading,
                paragraph_text=c.paragraph_text,
                language=c.language,
            )
        )
    return items


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--input", "-i", type=Path, default=DEFAULT_INPUT,
        help=f"Path to the .docx (default: {DEFAULT_INPUT.relative_to(PROJECT_ROOT)})",
    )
    p.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Directory for outputs (default: same folder as the input .docx)",
    )
    p.add_argument("--no-markdown", action="store_true", help="Skip the Markdown digest")
    p.add_argument("--no-json", action="store_true", help="Skip the JSON output")
    p.add_argument("--no-anchors", action="store_true", help="Do not parse word/document.xml")
    p.add_argument("--no-triage", action="store_true", help="Skip the triage scaffold output")
    p.add_argument("--indent", type=int, default=2, help="JSON indent (default: 2)")
    p.add_argument(
        "--max-anchor-chars", type=int, default=400,
        help="Truncate stored anchor text to this many chars (default: 400)",
    )
    p.add_argument(
        "--report-root", type=Path, default=None,
        help=(
            "Override the v1.03 report root used to resolve heading paths to "
            "Markdown file pointers. Default: auto-detect from the DOCX location."
        ),
    )
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    docx_path: Path = args.input.resolve()
    out_dir: Path = (args.output_dir or docx_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    comments = extract(
        docx_path,
        with_anchors=not args.no_anchors,
        max_anchor_chars=args.max_anchor_chars,
    )
    report_root = args.report_root.resolve() if args.report_root else _infer_report_root(docx_path)
    report_index = ReportPathIndex(report_root)
    attach_report_paths(comments, report_index)
    parent_lookup = ext_paraid_to_comment_id(comments)
    anchored = sum(1 for c in comments if c.anchor_text is not None)

    json_path = out_dir / f"{docx_path.stem}_comments.json"
    md_path = out_dir / f"{docx_path.stem}_comments.md"

    if not args.no_json:
        write_json(comments, json_path, indent=args.indent)
        print(
            f"wrote {json_path.relative_to(PROJECT_ROOT)} "
            f"({len(comments)} comments, {anchored} anchored)"
        )
    if not args.no_markdown:
        if report_root and report_root.is_relative_to(PROJECT_ROOT):
            report_root_str = str(report_root.relative_to(PROJECT_ROOT))
        else:
            report_root_str = None
        write_markdown(
            comments,
            md_path,
            docx_path,
            parent_lookup,
            report_root=report_root_str,
        )
        print(f"wrote {md_path.relative_to(PROJECT_ROOT)}")
    if not args.no_triage:
        triage_inputs = _to_triage_inputs(comments, parent_lookup)
        triage_path = write_triage(triage_inputs, out_dir, docx_path.stem, docx_path.name)
        print(f"wrote {triage_path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
