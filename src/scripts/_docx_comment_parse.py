"""Parse `word/comments.xml` and `word/commentsExtended.xml` into ``Comment`` objects.

Used by `extract_docx_comments.py`. Holds the small ``Comment`` dataclass plus
the XML helpers so the orchestrator stays under the 300-line file budget.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

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
    section_heading: str | None = None
    paragraph_index: int | None = None
    subsection_paragraph_index: int | None = None
    span_paragraphs: int | None = None
    paragraph_text: str | None = None
    prev_paragraph_text: str | None = None
    next_paragraph_text: str | None = None
    report_path: str | None = None
    language: str | None = None


def read_part(zf: zipfile.ZipFile, member: str) -> bytes | None:
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


def ext_paraid_to_comment_id(comments: list[Comment]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for c in comments:
        for pid in c.para_ids:
            mapping[pid] = c.id
    return mapping
