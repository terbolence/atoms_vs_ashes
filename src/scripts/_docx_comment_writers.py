# man_hours: 1.5
"""JSON + Markdown writers for `extract_docx_comments.py`.

Kept as a private helper so the orchestrator stays under the 300-line file budget.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid an import cycle at runtime
    from extract_docx_comments import Comment

COMMENTS_PART = "word/comments.xml"
COMMENTS_EXT_PART = "word/commentsExtended.xml"
DOCUMENT_PART = "word/document.xml"

ANCHOR_FIELDS_OPTIONAL = ("anchor_text", "anchor_chars", "chapter", "paragraph_index")


def comment_to_dict(c: "Comment") -> dict[str, object]:
    d = asdict(c)
    if c.done is None:
        d.pop("done", None)
    if c.parent_para_id is None:
        d.pop("parent_para_id", None)
    if c.anchor_text is None:
        for key in ANCHOR_FIELDS_OPTIONAL:
            d.pop(key, None)
    if not c.heading_path:
        d.pop("heading_path", None)
    return d


def write_json(comments: list["Comment"], path: Path, indent: int) -> None:
    payload = {
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(comments),
        "anchors_attached": sum(1 for c in comments if c.anchor_text is not None),
        "comments": [comment_to_dict(c) for c in comments],
    }
    path.write_text(json.dumps(payload, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def _where_line(c: "Comment") -> str | None:
    if c.heading_path:
        return " > ".join(c.heading_path)
    if c.chapter:
        return c.chapter
    return None


def _anchor_excerpt(text: str, limit: int = 200) -> str:
    excerpt = text.replace("\n", " ").strip()
    return excerpt if len(excerpt) <= limit else excerpt[:limit].rstrip() + "…"


def write_markdown(
    comments: list["Comment"],
    path: Path,
    source: Path,
    parent_lookup: dict[str, str],
) -> None:
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
            lines.append(f"_Anchor:_ \"{_anchor_excerpt(c.anchor_text)}\"")
            lines.append("")
        if c.text:
            for body_line in c.text.splitlines():
                lines.append("> " + body_line if body_line else ">")
        else:
            lines.append("> _(empty)_")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
