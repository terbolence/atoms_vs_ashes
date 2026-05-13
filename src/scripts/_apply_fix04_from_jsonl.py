# man_hours: 0.6
"""Pure helpers for ``apply_fix04_from_preview_jsonl.py``.

Extracted from the CLI orchestrator so the orchestrator stays under
the 300-line file-size limit and so the per-record decision logic is
unit-testable without DB or filesystem dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

DOMAIN_LABELS: tuple[str, ...] = ("military", "power", "transmitter")


def iter_records(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield ``(line_no, record)`` for every non-blank JSONL line.

    Raises ``ValueError`` with the offending line number on a parse
    failure.
    """
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield line_no, json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_no} of {path}: {exc}"
                ) from exc


def select_record(
    rec: dict[str, Any],
    *,
    countries: set[str] | None,
    site_ids: set[str] | None,
) -> bool:
    """Return True if the record passes the CLI country / site-id filters."""
    if countries:
        if (rec.get("country_code") or "").upper() not in countries:
            return False
    if site_ids:
        if rec.get("site_id") not in site_ids:
            return False
    return True


def classify_payload(
    rec: dict[str, Any], label: str,
) -> tuple[str, dict[str, Any] | None]:
    """Decide what to do for one ``(record, domain)`` pair.

    Returns ``(action, payload)`` where ``action`` is one of:

    - ``"apply"`` — payload is a dict ready for the persist function.
    - ``"skip-error"`` — the preview captured a fetch error for this
      domain on this site.
    - ``"skip-no-payload"`` — payload is missing or not a dict.
    """
    fetch_errors = rec.get("fetch_errors") or {}
    if isinstance(fetch_errors, dict) and label in fetch_errors:
        return "skip-error", None
    fetch = rec.get("fetch") or {}
    payload = fetch.get(label) if isinstance(fetch, dict) else None
    if not isinstance(payload, dict):
        return "skip-no-payload", None
    return "apply", payload


def empty_counts() -> dict[str, Any]:
    """Initial counter dict for the replay summary."""
    return {
        "considered": 0,
        "filtered_out": 0,
        "applied": {label: 0 for label in DOMAIN_LABELS},
        "skip_error": {label: 0 for label in DOMAIN_LABELS},
        "skip_no_payload": {label: 0 for label in DOMAIN_LABELS},
        "commit_errors": 0,
    }
