# man_hours: 4.0
"""Extract reviewer comments from a `.docx`, with anchored context and a triage scaffold.

A `.docx` is a ZIP archive. Reviewer comments live in `word/comments.xml`
(typically a few KB even for very large reports), with optional threading and
resolution metadata in `word/commentsExtended.xml`. By default this script also
streams `word/document.xml` to attach, per comment, the **anchor text** (what
the reviewer highlighted) and the **heading path** (chapter -> section -> ...)
so downstream routing into subsystems is data-driven rather than manual.

Outputs (next to the input by default):

  - `<stem>_comments.json`  — machine-readable list of comments + anchors
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
import json
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from _docx_comment_anchors import Anchor, extract_anchors
from _docx_comment_triage import TriageInputComment, write_triage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    PROJECT_ROOT / "report" / "output" / "feedback" / "atoms_vs_ashes_report_feedback.docx"
)

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
}

COMMENTS_PART = "word/comments.xml"
COMMENTS_EXT_PART = "word/commentsExtended.xml"
DOCUMENT_PART = "word/document.xml"


@dataclass
class Comment:
    id: str
    author: str
    initials: str
    date: str
    text: str
    para_ids: list[str] = field(default_factory=list)
    done: bool | None = None
    parent_para_id: str | None = None
    anchor_text: str | None = None
    anchor_chars: int | None = None
    heading_path: list[str] = field(default_factory=list)
    chapter: str | None = None
    paragraph_index: int | None = None


def _read_part(zf: zipfile.ZipFile, member: str) -> bytes | None:
    try:
        return zf.read(member)
    except KeyError:
        return None


def _paragraph_text(p: ET.Element) -> str:
    pieces: list[str] = []
    for node in p.iter():
        tag = node.tag.split("}", 1)[-1]
        if tag == "t":
            pieces.append(node.text or "")
        elif tag == "tab":
            pieces.append("\t")
        elif tag == "br":
            pieces.append("\n")
    return "".join(pieces).strip()


def _comment_text(comment: ET.Element) -> tuple[str, list[str]]:
    bodies: list[str] = []
    para_ids: list[str] = []
    for p in comment.findall("w:p", NS):
        para_id = p.get(f"{{{NS['w14']}}}paraId")
        if para_id:
            para_ids.append(para_id)
        text = _paragraph_text(p)
        if text:
            bodies.append(text)
    return "\n\n".join(bodies), para_ids


def parse_comments(xml_bytes: bytes) -> list[Comment]:
    root = ET.fromstring(xml_bytes)
    comments: list[Comment] = []
    for c in root.findall("w:comment", NS):
        text, para_ids = _comment_text(c)
        comments.append(
            Comment(
                id=c.get(f"{{{NS['w']}}}id", ""),
                author=c.get(f"{{{NS['w']}}}author", ""),
                initials=c.get(f"{{{NS['w']}}}initials", ""),
                date=c.get(f"{{{NS['w']}}}date", ""),
                text=text,
                para_ids=para_ids,
            )
        )
    comments.sort(key=lambda x: int(x.id) if x.id.isdigit() else x.id)
    return comments


def parse_extended(xml_bytes: bytes) -> dict[str, dict[str, str | bool]]:
    root = ET.fromstring(xml_bytes)
    by_para: dict[str, dict[str, str | bool]] = {}
    for ex in root.findall("w15:commentEx", NS):
        para_id = ex.get(f"{{{NS['w15']}}}paraId")
        if not para_id:
            continue
        done_attr = ex.get(f"{{{NS['w15']}}}done", "0")
        parent = ex.get(f"{{{NS['w15']}}}parentParaId")
        by_para[para_id] = {
            "done": done_attr in ("1", "true", "True"),
            "parent_para_id": parent,
        }
    return by_para


def merge_extended(comments: list[Comment], extended: dict[str, dict[str, str | bool]]) -> None:
    if not extended:
        return
    for c in comments:
        for pid in c.para_ids:
            meta = extended.get(pid)
            if not meta:
                continue
            if c.done is None:
                c.done = bool(meta.get("done"))
            if c.parent_para_id is None and meta.get("parent_para_id"):
                c.parent_para_id = str(meta["parent_para_id"])


def _ext_paraid_to_comment_id(comments: list[Comment]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for c in comments:
        for pid in c.para_ids:
            mapping[pid] = c.id
    return mapping


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
        c.paragraph_index = a.paragraph_index
        matched += 1
    return matched


def _comment_to_dict(c: Comment) -> dict[str, object]:
    d = asdict(c)
    if c.done is None:
        d.pop("done", None)
    if c.parent_para_id is None:
        d.pop("parent_para_id", None)
    if c.anchor_text is None:
        for key in ("anchor_text", "anchor_chars", "chapter", "paragraph_index"):
            d.pop(key, None)
    if not c.heading_path:
        d.pop("heading_path", None)
    return d


def write_json(comments: list[Comment], path: Path, indent: int) -> None:
    payload = {
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(comments),
        "anchors_attached": sum(1 for c in comments if c.anchor_text is not None),
        "comments": [_comment_to_dict(c) for c in comments],
    }
    path.write_text(json.dumps(payload, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def _where_line(c: Comment) -> str | None:
    if c.heading_path:
        return " > ".join(c.heading_path)
    if c.chapter:
        return c.chapter
    return None


def write_markdown(comments: list[Comment], path: Path, source: Path, parent_lookup: dict[str, str]) -> None:
    lines: list[str] = []
    lines.append(f"# Reviewer comments — `{source.name}`")
    lines.append("")
    lines.append(
        f"Extracted {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
        f"from `{COMMENTS_PART}` (and `{COMMENTS_EXT_PART}` / `{DOCUMENT_PART}` when present)."
    )
    lines.append(f"Total comments: **{len(comments)}**.")
    anchored = sum(1 for c in comments if c.anchor_text is not None)
    lines.append(f"Anchored to body text: **{anchored} / {len(comments)}**.")
    lines.append("")
    if not comments:
        lines.append("_No comments found._")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    authors = sorted({c.author for c in comments if c.author})
    if authors:
        lines.append("Authors: " + ", ".join(f"`{a}`" for a in authors))
        lines.append("")

    for idx, c in enumerate(comments, start=1):
        header_bits = [f"#{c.id}"]
        if c.author:
            header_bits.append(c.author)
        if c.date:
            header_bits.append(c.date)
        if c.done:
            header_bits.append("done")
        if c.parent_para_id:
            parent_cid = parent_lookup.get(c.parent_para_id)
            header_bits.append(f"reply-to #{parent_cid}" if parent_cid else "reply")
        lines.append(f"## {idx}. " + " — ".join(header_bits))
        lines.append("")
        where = _where_line(c)
        if where:
            lines.append(f"**Where:** {where}")
            lines.append("")
        if c.anchor_text:
            excerpt = c.anchor_text.replace("\n", " ").strip()
            if len(excerpt) > 200:
                excerpt = excerpt[:200].rstrip() + "…"
            lines.append(f"_Anchor:_ \"{excerpt}\"")
            lines.append("")
        if c.text:
            for body_line in c.text.splitlines():
                lines.append("> " + body_line if body_line else ">")
        else:
            lines.append("> _(empty)_")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract(docx_path: Path, *, with_anchors: bool = True, max_anchor_chars: int = 400) -> list[Comment]:
    if not docx_path.exists():
        raise SystemExit(f"Input not found: {docx_path}")
    with zipfile.ZipFile(docx_path) as zf:
        comments_xml = _read_part(zf, COMMENTS_PART)
        if comments_xml is None:
            members = [n for n in zf.namelist() if "comment" in n.lower()]
            raise SystemExit(
                f"`{COMMENTS_PART}` not found in {docx_path.name}. "
                f"Comment-related entries: {members or 'none'}"
            )
        ext_xml = _read_part(zf, COMMENTS_EXT_PART)
        document_xml = _read_part(zf, DOCUMENT_PART) if with_anchors else None

    comments = parse_comments(comments_xml)
    if ext_xml is not None:
        merge_extended(comments, parse_extended(ext_xml))
    if document_xml is not None:
        valid_ids = {c.id for c in comments}
        anchors = extract_anchors(document_xml, valid_ids, max_anchor_chars=max_anchor_chars)
        merge_anchors(comments, anchors)
    return comments


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
    parent_lookup = _ext_paraid_to_comment_id(comments)

    json_path = out_dir / f"{docx_path.stem}_comments.json"
    md_path = out_dir / f"{docx_path.stem}_comments.md"

    if not args.no_json:
        write_json(comments, json_path, indent=args.indent)
        print(f"wrote {json_path.relative_to(PROJECT_ROOT)} ({len(comments)} comments)")
    if not args.no_markdown:
        write_markdown(comments, md_path, docx_path, parent_lookup)
        print(f"wrote {md_path.relative_to(PROJECT_ROOT)}")
    if not args.no_triage:
        triage_inputs = _to_triage_inputs(comments, parent_lookup)
        triage_path = write_triage(triage_inputs, out_dir, docx_path.stem, docx_path.name)
        print(f"wrote {triage_path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
