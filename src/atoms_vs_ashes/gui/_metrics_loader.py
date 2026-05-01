# man_hours: 0.5
"""Read :class:`MetricsBundle` JSON documents off disk for the dashboard pages.

We intentionally read the JSON file rather than rebuilding the bundle
in-process: the heavy work happens once when the failure-analysis
script writes ``<stamp>_metrics.json`` (plan §9), and every GUI page
just decodes it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def discover_metrics_files(audit_dir: str | Path) -> list[Path]:
    """Return ``audit_dir/*_metrics.json`` candidates, newest-first.

    Lives here (not in ``_data.py``) so the loader is importable
    without Streamlit — useful in unit tests and CLI consumers.
    """
    root = Path(audit_dir)
    if not root.is_dir():
        return []
    return sorted(
        root.glob("*_metrics.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


@dataclass
class LoadedMetrics:
    path: Path
    data: dict[str, Any]

    @property
    def summary(self) -> dict[str, Any]:
        return self.data.get("summary") or {}

    @property
    def per_country(self) -> list[dict[str, Any]]:
        return self.data.get("per_country") or []

    @property
    def per_criterion(self) -> list[dict[str, Any]]:
        return self.data.get("per_criterion") or []

    @property
    def per_smr(self) -> list[dict[str, Any]]:
        return self.data.get("per_smr") or []

    @property
    def top_n(self) -> list[dict[str, Any]]:
        return self.data.get("top_n_per_country") or []

    @property
    def per_country_margins(self) -> list[dict[str, Any]]:
        return self.data.get("per_country_margins") or []

    @property
    def near_miss(self) -> dict[str, Any]:
        return self.data.get("near_miss") or {}

    @property
    def sensitivity(self) -> dict[str, Any]:
        return self.data.get("sensitivity") or {}

    @property
    def per_pair_failures(self) -> list[dict[str, Any]]:
        return self.data.get("per_pair_failures") or []

    @property
    def provenance(self) -> dict[str, Any]:
        return self.data.get("provenance") or {}

    @property
    def multi_failure_histogram(self) -> dict[str, int]:
        return self.data.get("multi_failure_histogram") or {}


def load_metrics_file(path: str | Path) -> LoadedMetrics:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return LoadedMetrics(path=path, data=data)


def pick_metrics_file(audit_dir: str | Path) -> Path | None:
    """Return the most recent ``*_metrics.json`` under ``audit_dir`` or None."""
    files = discover_metrics_files(audit_dir)
    return files[0] if files else None


def pick_metrics_file_for_run(
    audit_dir: str | Path,
    run_id: str,
    *,
    max_candidates: int = 30,
) -> Path | None:
    """Return newest ``*_metrics.json`` whose payload ``run_id`` matches.

    Scans ``discover_metrics_files`` (newest first), parses each candidate
    until a match is found or ``max_candidates`` is exhausted.
    """
    files = discover_metrics_files(audit_dir)
    for path in files[:max_candidates]:
        loaded = load_metrics_file(path)
        if str(loaded.data.get("run_id", "")) == str(run_id):
            return path
    return None


def metrics_picker_widget(audit_dir: str | Path, *, key: str) -> Path | None:
    """Streamlit-friendly file picker for metrics JSONs.

    Imported lazily so this module stays importable without Streamlit
    (e.g. in unit tests).
    """
    import streamlit as st  # noqa: WPS433 — intentional local import

    files = discover_metrics_files(audit_dir)
    if not files:
        st.info(
            f"No `*_metrics.json` under `{audit_dir}`. "
            "Run the scoring pipeline (or `generate_failure_analysis.py`) first."
        )
        return None
    options = [str(p) for p in files]
    chosen = st.selectbox(
        "Metrics file",
        options=options,
        index=0,
        key=key,
        format_func=lambda p: Path(p).name,
    )
    return Path(chosen)


__all__ = [
    "LoadedMetrics",
    "load_metrics_file",
    "metrics_picker_widget",
    "pick_metrics_file",
    "pick_metrics_file_for_run",
]
