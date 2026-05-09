# man_hours: 2.5
"""Triage scaffold writer for `extract_docx_comments.py`.

Emits one machine- and human-editable file (`<stem>_triage.yaml` when PyYAML is
available, else `<stem>_triage.json`) with one entry per comment id. The
extractor refreshes the `auto.*` block on every run and preserves user-edited
fields (`category`, `subsystem`, `action`, `depends_on`, `notes`). Missing ids
are kept and tagged with `auto.removed: true` for review history.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:  # PyYAML is the preferred carrier; JSON is a graceful fallback.
    import yaml  # type: ignore[import-untyped]

    _HAS_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    _HAS_YAML = False


USER_FIELDS: tuple[str, ...] = ("category", "subsystem", "action", "depends_on", "notes")


CATEGORIES: tuple[str, ...] = (
    "ack",
    "wording",
    "scoring",
    "weights",
    "exclusionary",
    "sensitivity",
    "data",
    "connector",
    "methodology",
    "clarification",
)
SUBSYSTEMS: tuple[str, ...] = (
    "report-text",
    "scoring-engine",
    "swing-weights",
    "sensitivity",
    "data-connector",
    "methodology-doc",
    "qa-cross-check",
)


@dataclass
class TriageInputComment:
    """Subset of comment fields the triage layer needs."""

    id: str
    author: str
    date: str
    text: str
    chapter: str
    heading_path: list[str]
    anchor_excerpt: str
    done: bool | None
    parent_id: str | None


_ACK_RE = re.compile(r"^(ok|ok\.|da|da\.|noted|nota)\.?$", re.IGNORECASE)
_RE_SCORING = re.compile(r"\b(scor|scoring|weight|swing|pondere|ranking)\w*", re.IGNORECASE)
_RE_EXCLUSIONARY = re.compile(r"\b(exclus|exclusionary|safety)\w*", re.IGNORECASE)
_RE_WORDING = re.compile(r"\b(tabel|titlu|heading|wording|clarif|table|title|heading)\w*", re.IGNORECASE)
_RE_SENS = re.compile(r"\b(sensitivity|sensibilitate)\w*", re.IGNORECASE)
_RE_DATA = re.compile(r"\b(connector|api|enrich|sursa|sursă|date)\w*", re.IGNORECASE)


def heuristic_classification(text: str) -> dict[str, str]:
    """Return `{heuristic_category, heuristic_subsystem}` from the comment body.

    The rules are deliberately cheap and do not call any LLM. They populate
    `auto.heuristic_*` fields only — the user-editable `category` / `subsystem`
    stay blank for the next plan to confirm.
    """
    norm = (text or "").strip()
    if _ACK_RE.fullmatch(norm):
        return {"heuristic_category": "ack", "heuristic_subsystem": "report-text"}
    cat = ""
    sub = ""
    if _RE_SCORING.search(norm):
        sub = sub or "scoring-engine"
    if _RE_EXCLUSIONARY.search(norm):
        cat = cat or "exclusionary"
        sub = sub or "methodology-doc"
    if _RE_WORDING.search(norm):
        cat = cat or "wording"
        sub = sub or "report-text"
    if _RE_SENS.search(norm):
        sub = sub or "sensitivity"
    if _RE_DATA.search(norm):
        sub = sub or "data-connector"
    return {"heuristic_category": cat, "heuristic_subsystem": sub}


def _excerpt(text: str, limit: int = 160) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _build_auto_block(c: TriageInputComment) -> dict[str, object]:
    block: dict[str, object] = {
        "author": c.author,
        "date": c.date,
        "chapter": c.chapter,
        "heading_path": list(c.heading_path),
        "anchor_excerpt": _excerpt(c.anchor_excerpt),
        "text_excerpt": _excerpt(c.text),
        "reply_to": c.parent_id,
        "done": bool(c.done) if c.done is not None else False,
    }
    block.update(heuristic_classification(c.text))
    return block


def _empty_user_fields() -> dict[str, object]:
    return {
        "category": "",
        "subsystem": "",
        "action": "",
        "depends_on": [],
        "notes": "",
    }


def _merge_item(existing: dict | None, new_id: str, new_auto: dict[str, object]) -> dict[str, object]:
    out: dict[str, object] = {"id": new_id, "auto": new_auto}
    if existing:
        for key in USER_FIELDS:
            if key in existing:
                out[key] = existing[key]
        for key, value in existing.items():
            if key in ("id", "auto") or key in USER_FIELDS:
                continue
            out[key] = value
    for key, default in _empty_user_fields().items():
        out.setdefault(key, default)
    return out


def _load_existing(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        if path.suffix == ".yaml" and _HAS_YAML:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        else:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception as exc:  # noqa: BLE001 — surface the issue and keep going.
        print(f"warn: could not parse existing triage file {path.name}: {exc}; ignoring")
        return {}
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return {}
    return {str(item.get("id", "")): item for item in items if isinstance(item, dict)}


def _ordered_dump(data: dict, path: Path) -> None:
    if path.suffix == ".yaml" and _HAS_YAML:
        path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False),
            encoding="utf-8",
        )
    else:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _path_for_dir(out_dir: Path, stem: str) -> Path:
    suffix = ".yaml" if _HAS_YAML else ".json"
    return out_dir / f"{stem}_triage{suffix}"


def write_triage(
    comments: list[TriageInputComment],
    out_dir: Path,
    stem: str,
    source_name: str,
) -> Path:
    """Write/refresh the triage file. Idempotent w.r.t. user-edited fields."""

    out_path = _path_for_dir(out_dir, stem)
    legacy_path = out_dir / f"{stem}_triage.yaml" if not _HAS_YAML else out_dir / f"{stem}_triage.json"
    existing_items: dict[str, dict] = {}
    existing_items.update(_load_existing(out_path))
    if legacy_path.exists() and legacy_path != out_path:
        for cid, item in _load_existing(legacy_path).items():
            existing_items.setdefault(cid, item)

    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for c in comments:
        seen.add(c.id)
        new_auto = _build_auto_block(c)
        items.append(_merge_item(existing_items.get(c.id), c.id, new_auto))

    for cid, existing in existing_items.items():
        if cid in seen:
            continue
        auto = dict(existing.get("auto", {}))
        auto["removed"] = True
        items.append(_merge_item(existing, cid, auto))

    payload: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source_name,
        "categories": list(CATEGORIES),
        "subsystems": list(SUBSYSTEMS),
        "items": items,
    }
    _ordered_dump(payload, out_path)
    return out_path
