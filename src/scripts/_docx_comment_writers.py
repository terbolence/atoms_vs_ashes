"""JSON + Markdown writers for `extract_docx_comments.py`.

Renders a reviewer-comment digest that is rich enough to drive surgical edits:
chapter -> section -> paragraph location, the **full** anchor paragraph plus the
**preceding** and **following** paragraph as surrounding context, a language tag
on the reviewer note (Romanian / English / mixed), and a pointer to the v1.03
report Markdown file that contains the targeted section.

Kept as a private helper so the orchestrator stays under the 300-line budget.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid an import cycle at runtime
    from _docx_comment_parse import Comment

COMMENTS_PART = "word/comments.xml"
COMMENTS_EXT_PART = "word/commentsExtended.xml"
DOCUMENT_PART = "word/document.xml"

ANCHOR_FIELDS_OPTIONAL = (
    "anchor_text",
    "anchor_chars",
    "chapter",
    "section_heading",
    "paragraph_index",
    "subsection_paragraph_index",
    "span_paragraphs",
    "paragraph_text",
    "prev_paragraph_text",
    "next_paragraph_text",
)

LANGUAGE_LABEL = {
    "ro": "Romanian",
    "en": "English",
    "mixed": "Romanian and English",
}


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
    for key in ("report_path", "language", "paragraph_text", "prev_paragraph_text", "next_paragraph_text", "section_heading"):
        if d.get(key) in (None, ""):
            d.pop(key, None)
    return d


def write_json(comments: list["Comment"], path: Path, indent: int) -> None:
    payload = {
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(comments),
        "anchors_attached": sum(1 for c in comments if c.anchor_text is not None),
        "comments": [comment_to_dict(c) for c in comments],
    }
    path.write_text(json.dumps(payload, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def _anchor_excerpt(text: str, limit: int = 240) -> str:
    excerpt = text.replace("\n", " ").strip()
    return excerpt if len(excerpt) <= limit else excerpt[:limit].rstrip() + "…"


def _location_line(c: "Comment") -> str | None:
    bits: list[str] = []
    if c.section_heading:
        bits.append(f"Section: **{c.section_heading}**")
    if c.subsection_paragraph_index is not None and c.subsection_paragraph_index > 0:
        bits.append(f"paragraph {c.subsection_paragraph_index} of the section")
    if c.span_paragraphs and c.span_paragraphs > 1:
        bits.append(f"spans {c.span_paragraphs} paragraphs")
    return " — ".join(bits) if bits else None


def _report_pointer(c: "Comment", report_root: str | None) -> str | None:
    if not c.report_path:
        return None
    if report_root:
        return f"`{report_root.rstrip('/')}/{c.report_path}`"
    return f"`{c.report_path}`"


def _language_note(c: "Comment") -> str | None:
    if not c.language:
        return None
    label = LANGUAGE_LABEL.get(c.language, c.language)
    if c.language == "ro":
        return f"_Reviewer note language: {label} (translate before acting)._"
    if c.language == "mixed":
        return f"_Reviewer note language: {label} (Romanian parts need translation)._"
    return f"_Reviewer note language: {label}._"


def _blockquote(text: str) -> list[str]:
    if not text:
        return []
    return ["> " + line if line else ">" for line in text.splitlines()]


def _render_comment(
    idx: int,
    c: "Comment",
    parent_lookup: dict[str, str],
    report_root: str | None,
) -> list[str]:
    lines: list[str] = []
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

    if c.heading_path:
        lines.append(f"**Where:** {' > '.join(c.heading_path)}")
    elif c.chapter:
        lines.append(f"**Where:** {c.chapter}")
    location = _location_line(c)
    if location:
        lines.append(location)
    pointer = _report_pointer(c, report_root)
    if pointer:
        lines.append(f"**Report file:** {pointer}")
    lines.append("")

    if c.anchor_text:
        lines.append(f"_Highlighted span:_ \"{_anchor_excerpt(c.anchor_text, limit=240)}\"")
        lines.append("")
    if c.paragraph_text:
        lines.append("**Anchor paragraph:**")
        lines.append("")
        lines.extend(_blockquote(c.paragraph_text))
        lines.append("")
    if c.prev_paragraph_text:
        lines.append(f"_Preceding paragraph:_ {_anchor_excerpt(c.prev_paragraph_text, limit=360)}")
        lines.append("")
    if c.next_paragraph_text:
        lines.append(f"_Following paragraph:_ {_anchor_excerpt(c.next_paragraph_text, limit=360)}")
        lines.append("")

    lines.append("**Reviewer note:**")
    lines.append("")
    if c.text:
        lines.extend(_blockquote(c.text))
    else:
        lines.append("> _(empty)_")
    lang_note = _language_note(c)
    if lang_note:
        lines.append("")
        lines.append(lang_note)
    lines.append("")
    return lines


def write_markdown(
    comments: list["Comment"],
    path: Path,
    source: Path,
    parent_lookup: dict[str, str],
    *,
    report_root: str | None = None,
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
    with_paragraph = sum(1 for c in comments if c.paragraph_text)
    if with_paragraph:
        lines.append(f"With full-paragraph context: **{with_paragraph} / {len(comments)}**.")
    with_pointer = sum(1 for c in comments if c.report_path)
    if with_pointer:
        lines.append(f"With resolved v1.03 file pointer: **{with_pointer} / {len(comments)}**.")
    if report_root:
        lines.append(f"Report root: `{report_root}`.")
    lines.append("")
    if not comments:
        lines.append("_No comments found._")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    authors = sorted({c.author for c in comments if c.author})
    if authors:
        lines.append("Authors: " + ", ".join(f"`{a}`" for a in authors))
        lines.append("")
    languages = sorted({c.language for c in comments if c.language})
    if languages:
        lines.append("Reviewer-note languages: " + ", ".join(f"`{lang}`" for lang in languages))
        lines.append("")
    lines.append("---")
    lines.append("")

    for idx, c in enumerate(comments, start=1):
        lines.extend(_render_comment(idx, c, parent_lookup, report_root))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
