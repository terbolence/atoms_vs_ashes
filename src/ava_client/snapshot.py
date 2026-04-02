"""Markdown integration-snapshot writer.

Produces snapshot files that are backward-compatible with the format
established by ``scripts/live_integration_snapshots.py``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ava_client.resolver import ResolvedSite


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def truncate_json(obj: Any, max_items: int = 50) -> Any:
    """Recursively truncate large lists for readable snapshots."""
    if isinstance(obj, list) and len(obj) > max_items:
        return obj[:max_items] + [f"... ({len(obj) - max_items} more items)"]
    if isinstance(obj, dict):
        return {k: truncate_json(v, max_items) for k, v in obj.items()}
    return obj


def pretty_json(obj: Any, max_items: int = 50) -> str:
    return json.dumps(truncate_json(obj, max_items), indent=2, default=str, ensure_ascii=False)


def build_header(title: str, description: str, run_id: str, site_count: int,
                 success: int = 0, failed: int = 0) -> str:
    return (
        f"<!-- man_hours: 0.0 -->\n"
        f"# {title}\n\n"
        f"**Generated:** {timestamp_utc()}\n"
        f"**Run ID:** {run_id}\n"
        f"**Description:** {description}\n"
        f"**Sites:** {site_count} processed, {success} successful, {failed} failed\n\n"
        f"---\n\n"
    )


def build_site_section(site: ResolvedSite, status: str, elapsed_ms: int,
                       summary: str, detail_json: str) -> str:
    icon = "PASS" if status == "ok" else "FAIL" if status == "error" else "SKIP"
    return (
        f"## {site.country} - {site.name}\n\n"
        f"- **Coordinates:** {site.lat}, {site.lon}\n"
        f"- **Status:** {icon} ({elapsed_ms} ms)\n"
        f"- **Summary:** {summary}\n\n"
        f"<details>\n<summary>Full response</summary>\n\n"
        f"```json\n{detail_json}\n```\n\n"
        f"</details>\n\n"
        f"---\n\n"
    )


def write_snapshot(output_dir: Path, filename: str, content: str) -> Path:
    """Write *content* to ``output_dir / filename``, creating dirs as needed."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path
