# man_hours: 0.25
"""Persist a :class:`MetricsBundle` as a single JSON document."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from atoms_vs_ashes.metrics.bundle import MetricsBundle


def _default(obj: Any) -> Any:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


def write_metrics_json(
    bundle: MetricsBundle, path: Path, *, indent: int = 2
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bundle.to_dict()
    text = json.dumps(payload, indent=indent, default=_default, sort_keys=False)
    path.write_text(text, encoding="utf-8")
    return path


__all__ = ["write_metrics_json"]
