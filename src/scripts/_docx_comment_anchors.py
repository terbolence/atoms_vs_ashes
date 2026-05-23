"""Stream `word/document.xml` to resolve anchored context for each reviewer comment.

Used by `extract_docx_comments.py`. For every comment the extractor records the
heading path (chapter -> section -> ...) plus a rich paragraph context: the full
paragraph that hosts the highlighted span, the preceding text paragraph, the
following text paragraph, and the paragraph index inside the current subsection.

Kept as a private helper so the orchestrator stays under the project's
300-line file budget. Memory is bounded by clearing closed `<w:p>` elements
during `iterparse`.
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

SUBSECTION_RESET_LEVEL = 2


@dataclass
class Anchor:
    """Resolved anchor for a single Word comment."""

    comment_id: str
    anchor_text: str
    anchor_chars: int
    heading_path: list[str] = field(default_factory=list)
    chapter: str = ""
    section_heading: str = ""
    paragraph_index: int = 0
    subsection_paragraph_index: int = 0
    paragraph_text: str = ""
    prev_paragraph_text: str = ""
    next_paragraph_text: str = ""
    span_paragraphs: int = 1


def _localname(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _heading_path(stack: list[tuple[int, str]]) -> list[str]:
    """Return the heading path excluding Title (level 0)."""
    return [t for level, t in stack if level >= 1]


def _chapter(stack: list[tuple[int, str]]) -> str:
    for level, t in stack:
        if level == 1 and t:
            return t
    for level, t in stack:
        if level >= 1 and t:
            return t
    return stack[0][1] if stack else ""


def _section_heading(stack: list[tuple[int, str]]) -> str:
    """Deepest heading on the stack (the immediate parent section)."""
    for level, t in reversed(stack):
        if level >= 1 and t:
            return t
    return ""


def _new_pending(cid: str, ctx: dict) -> dict:
    return {
        "comment_id": cid,
        "heading_path": list(ctx["heading_path"]),
        "chapter": ctx["chapter"],
        "section_heading": ctx["section_heading"],
        "paragraph_index": ctx["paragraph_index"],
        "subsection_paragraph_index": ctx["subsection_paragraph_index"],
        "prev_paragraph_text": ctx["prev_paragraph_text"],
        "anchor_buf": [],
        "paragraph_text": "",
        "span_paragraphs": 0,
        "needs_next": True,
    }


def _finalize(p: dict, *, next_text: str = "", max_chars: int = 400) -> Anchor:
    body = "".join(p["anchor_buf"]).strip() or p["paragraph_text"]
    return Anchor(
        comment_id=p["comment_id"],
        anchor_text=body if len(body) <= max_chars else body[:max_chars].rstrip() + "…",
        anchor_chars=len(body),
        heading_path=list(p["heading_path"]),
        chapter=p["chapter"],
        section_heading=p["section_heading"],
        paragraph_index=p["paragraph_index"],
        subsection_paragraph_index=p["subsection_paragraph_index"],
        paragraph_text=p["paragraph_text"],
        prev_paragraph_text=p["prev_paragraph_text"],
        next_paragraph_text=next_text,
        span_paragraphs=max(p["span_paragraphs"], 1),
    )


def _push_heading(stack: list[tuple[int, str]], level: int, text: str) -> None:
    while stack and stack[-1][0] >= level:
        stack.pop()
    stack.append((level, text))


def extract_anchors(
    document_xml: bytes,
    valid_ids: set[str],
    max_anchor_chars: int = 400,
) -> dict[str, Anchor]:
    """Return `{comment_id: Anchor}` with rich paragraph context for each valid id.

    Comments inside footnotes, headers, or footers live in different XML parts and
    are silently skipped here. Their absence is handled at the call site.
    """
    finalized: dict[str, Anchor] = {}
    open_ranges: dict[str, dict] = {}
    awaiting_next: list[dict] = []
    pending_points: dict[str, dict] = {}

    heading_stack: list[tuple[int, str]] = []
    paragraph_index = 0
    subsection_paragraph_index = 0
    last_text_paragraph = ""

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
                    ctx = {
                        "heading_path": _heading_path(heading_stack),
                        "chapter": _chapter(heading_stack),
                        "section_heading": _section_heading(heading_stack),
                        "paragraph_index": paragraph_index,
                        "subsection_paragraph_index": subsection_paragraph_index,
                        "prev_paragraph_text": last_text_paragraph,
                    }
                    open_ranges[cid] = _new_pending(cid, ctx)
            elif tag == "commentRangeEnd":
                cid = elem.get(W_ID, "")
                pending = open_ranges.pop(cid, None)
                if pending is not None:
                    awaiting_next.append(pending)
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
                        "section_heading": _section_heading(heading_stack),
                        "paragraph_index": paragraph_index,
                        "subsection_paragraph_index": subsection_paragraph_index,
                        "prev_paragraph_text": last_text_paragraph,
                    }
        else:
            if tag in ("t", "tab", "br"):
                text = "\t" if tag == "tab" else ("\n" if tag == "br" else (elem.text or ""))
                if in_paragraph:
                    para_text_parts.append(text)
                if open_ranges:
                    for data in open_ranges.values():
                        data["anchor_buf"].append(text)
            elif tag == "p":
                para_text = "".join(para_text_parts).strip()
                is_heading = para_style in HEADING_LEVELS
                for data in open_ranges.values():
                    data["span_paragraphs"] += 1
                    if not data["paragraph_text"]:
                        data["paragraph_text"] = para_text
                for cid, ctx in list(pending_points.items()):
                    if ctx["paragraph_index"] == paragraph_index:
                        pending = _new_pending(cid, ctx)
                        pending["paragraph_text"] = para_text
                        pending["span_paragraphs"] = 1
                        finalized[cid] = _finalize(pending, max_chars=max_anchor_chars)
                        del pending_points[cid]
                if awaiting_next:
                    still_waiting: list[dict] = []
                    for pending in awaiting_next:
                        if not pending["paragraph_text"]:
                            pending["paragraph_text"] = para_text
                        if is_heading or not para_text:
                            still_waiting.append(pending)
                            continue
                        if pending["paragraph_index"] == paragraph_index:
                            still_waiting.append(pending)
                            continue
                        finalized[pending["comment_id"]] = _finalize(
                            pending, next_text=para_text, max_chars=max_anchor_chars
                        )
                    awaiting_next = still_waiting
                if is_heading and para_text:
                    level = HEADING_LEVELS[para_style]
                    _push_heading(heading_stack, level, para_text)
                    if level >= SUBSECTION_RESET_LEVEL:
                        subsection_paragraph_index = 0
                    else:
                        subsection_paragraph_index = 0
                elif para_text:
                    subsection_paragraph_index += 1
                    last_text_paragraph = para_text
                paragraph_index += 1
                in_paragraph = False
                elem.clear()

    for pending in awaiting_next:
        finalized[pending["comment_id"]] = _finalize(pending, max_chars=max_anchor_chars)
    return finalized
