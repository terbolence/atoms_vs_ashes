# man_hours: 3.0
"""Stream `word/document.xml` to find the anchored text + heading path for each comment id.

Used by `extract_docx_comments.py`. Kept as a private helper so the orchestrator
stays under the project's 300-line file budget.

Key idea: `iterparse` with `start`/`end` events, an in-memory heading stack, and
per-comment buffers. Paragraph elements are `clear()`-ed on close to keep memory
bounded for very large reports.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_VAL = f"{{{W_NS}}}val"
W_ID = f"{{{W_NS}}}id"

HEADING_LEVELS: dict[str, int] = {
    "Title": 0,
    "Heading1": 1,
    "Heading2": 2,
    "Heading3": 3,
    "Heading4": 4,
    "Heading5": 5,
    "Heading6": 6,
    "Heading7": 7,
    "Heading8": 8,
    "Heading9": 9,
}


@dataclass
class Anchor:
    """Resolved anchor for a single Word comment."""

    comment_id: str
    anchor_text: str
    anchor_chars: int
    heading_path: list[str] = field(default_factory=list)
    chapter: str = ""
    paragraph_index: int = 0


def _localname(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit].rstrip() + "…"


def _heading_path(stack: list[tuple[int, str]]) -> list[str]:
    """Return the path excluding Title (level 0) — chapter-down only."""
    return [t for level, t in stack if level >= 1]


def _chapter(stack: list[tuple[int, str]]) -> str:
    """Top-level Heading1 if present; otherwise the first non-empty entry."""
    for level, t in stack:
        if level == 1 and t:
            return t
    for level, t in stack:
        if level >= 1 and t:
            return t
    return stack[0][1] if stack else ""


def _make_anchor(cid: str, body: str, ctx: dict, max_chars: int) -> Anchor:
    return Anchor(
        comment_id=cid,
        anchor_text=_truncate(body, max_chars),
        anchor_chars=len(body),
        heading_path=list(ctx["heading_path"]),
        chapter=ctx["chapter"],
        paragraph_index=ctx["paragraph_index"],
    )


def extract_anchors(
    document_xml: bytes,
    valid_ids: set[str],
    max_anchor_chars: int = 400,
) -> dict[str, Anchor]:
    """Return `{comment_id: Anchor}` for every id in `valid_ids` found in the body.

    Comments inside footnotes/headers/footers are ignored (they live in other
    XML parts) and silently end up without anchors — handled at the call site.
    """
    finalized: dict[str, Anchor] = {}
    open_ranges: dict[str, dict] = {}
    pending_points: dict[str, dict] = {}

    heading_stack: list[tuple[int, str]] = []
    paragraph_index = 0

    in_paragraph = False
    para_text_parts: list[str] = []
    para_style: str | None = None

    context = ET.iterparse(io.BytesIO(document_xml), events=("start", "end"))
    _, _root = next(context)
    for event, elem in context:
        tag = _localname(elem.tag)
        if event == "start":
            if tag == "p":
                in_paragraph = True
                para_text_parts = []
                para_style = None
            elif tag == "pStyle" and in_paragraph:
                para_style = elem.get(W_VAL)
            elif tag == "commentRangeStart":
                cid = elem.get(W_ID, "")
                if cid and cid in valid_ids and cid not in open_ranges and cid not in finalized:
                    open_ranges[cid] = {
                        "heading_path": _heading_path(heading_stack),
                        "chapter": _chapter(heading_stack),
                        "paragraph_index": paragraph_index,
                        "buf": [],
                    }
            elif tag == "commentRangeEnd":
                cid = elem.get(W_ID, "")
                data = open_ranges.pop(cid, None)
                if data is not None:
                    body = "".join(data["buf"]).strip()
                    if body:
                        finalized[cid] = _make_anchor(cid, body, data, max_anchor_chars)
                    else:
                        pending_points[cid] = {
                            "heading_path": data["heading_path"],
                            "chapter": data["chapter"],
                            "paragraph_index": data["paragraph_index"],
                        }
            elif tag == "commentReference":
                cid = elem.get(W_ID, "")
                if (
                    cid
                    and cid in valid_ids
                    and cid not in open_ranges
                    and cid not in finalized
                    and cid not in pending_points
                ):
                    pending_points[cid] = {
                        "heading_path": _heading_path(heading_stack),
                        "chapter": _chapter(heading_stack),
                        "paragraph_index": paragraph_index,
                    }
        else:  # end
            if tag == "t":
                text = elem.text or ""
                if in_paragraph:
                    para_text_parts.append(text)
                if open_ranges:
                    for data in open_ranges.values():
                        data["buf"].append(text)
            elif tag == "tab":
                if in_paragraph:
                    para_text_parts.append("\t")
                if open_ranges:
                    for data in open_ranges.values():
                        data["buf"].append("\t")
            elif tag == "br":
                if in_paragraph:
                    para_text_parts.append("\n")
                if open_ranges:
                    for data in open_ranges.values():
                        data["buf"].append("\n")
            elif tag == "p":
                para_text = "".join(para_text_parts).strip()
                for cid, data in list(pending_points.items()):
                    if data["paragraph_index"] == paragraph_index:
                        finalized[cid] = _make_anchor(cid, para_text, data, max_anchor_chars)
                        del pending_points[cid]
                if para_style in HEADING_LEVELS and para_text:
                    level = HEADING_LEVELS[para_style]
                    while heading_stack and heading_stack[-1][0] >= level:
                        heading_stack.pop()
                    heading_stack.append((level, para_text))
                paragraph_index += 1
                in_paragraph = False
                elem.clear()

    return finalized
