# man_hours: 0.5
"""Pure diff/render helpers for ``preview_fix04_osm_vs_db.py``.

Extracted from the CLI orchestrator to keep both files under the
300-line file-size limit and to make the diff matrix unit-testable
without DB or Overpass dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class DomainSpec:
    """Static description of one FIX-04 domain (military / transmitter / power)."""

    label: str          # "military" / "transmitter" / "power"
    criterion: str      # "HI-06" / "HI-07" / "NS-02"
    db_table: str       # "site_human_hazards" or "site_infrastructure_v2"
    columns: tuple[tuple[str, str], ...]
    """Pairs of (parser_dict_key, db_column) in display order."""


_MILITARY = DomainSpec(
    label="military", criterion="HI-06", db_table="site_human_hazards",
    columns=(
        ("nearest_military_km", "nearest_military_km"),
        ("nearest_military_name", "nearest_military_name"),
        ("military_count", "military_count"),
        ("quality", "hi06_quality"),
        # hi06_comment is verbose + deterministic; included in JSONL but
        # excluded from diff matrix to keep the report focused.
    ),
)
_TRANSMITTER = DomainSpec(
    label="transmitter", criterion="HI-07", db_table="site_human_hazards",
    columns=(
        ("nearest_transmitter_km", "nearest_transmitter_km"),
        ("transmitter_type", "transmitter_type"),
        ("transmitter_count", "transmitter_count"),
        ("quality", "hi07_quality"),
    ),
)
_POWER = DomainSpec(
    label="power", criterion="NS-02", db_table="site_infrastructure_v2",
    columns=(
        ("nearest_hv_line_km", "nearest_hv_line_km"),
        ("nearest_substation_km", "nearest_substation_km"),
        ("hv_line_count", "hv_line_count"),
        ("substation_count", "substation_count"),
        ("hv_line_voltage_kv", "hv_line_voltage_kv"),
        ("quality", "ns02_quality"),
    ),
)
DOMAINS: tuple[DomainSpec, ...] = (_MILITARY, _TRANSMITTER, _POWER)

NUMERIC_TOLERANCES: dict[str, float] = {
    "nearest_military_km": 0.01,
    "nearest_transmitter_km": 0.01,
    "nearest_hv_line_km": 0.01,
    "nearest_substation_km": 0.01,
}


@dataclass(frozen=True)
class ColumnDiff:
    domain: str
    column: str
    current: Any
    proposed: Any


def coerce(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def values_equal(column: str, current: Any, proposed: Any) -> bool:
    a = coerce(current)
    b = coerce(proposed)
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    tol = NUMERIC_TOLERANCES.get(column)
    if tol is not None:
        try:
            return abs(float(a) - float(b)) <= tol
        except (TypeError, ValueError):
            return a == b
    return a == b


def diff_domain(
    *,
    spec: DomainSpec,
    parsed: dict[str, Any] | None,
    db_row: dict[str, Any],
) -> list[ColumnDiff]:
    """Return per-column diffs for one domain on one site.

    `parsed` is the dict returned by the FIX-04 parser for the domain
    (`_parse_military` / `_parse_transmitters` / `_parse_power`); use
    ``None`` to indicate a fetch error (no diff produced).
    """
    if parsed is None:
        return []
    diffs: list[ColumnDiff] = []
    for parsed_key, db_col in spec.columns:
        cur = coerce(db_row.get(db_col))
        prop = parsed.get(parsed_key)
        if not values_equal(db_col, cur, prop):
            diffs.append(ColumnDiff(spec.label, db_col, cur, prop))
    return diffs


def serialise(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    return v


def serialise_diff(d: ColumnDiff) -> dict[str, Any]:
    return {
        "domain": d.domain, "column": d.column,
        "current": serialise(d.current), "proposed": serialise(d.proposed),
    }


def render_report_md(
    *,
    total_sites: int,
    sites_with_changes: list[dict[str, Any]],
    sites_unchanged: int,
    fetch_errors: dict[str, list[dict[str, Any]]],
    column_change_counts: dict[str, dict[str, int]],
    run_id: str,
    head_limit: int = 50,
) -> str:
    parts: list[str] = []
    parts.append("<!-- man_hours: 0.3 -->")
    parts.append("# FIX-04 OSM avoidance — preview report (no DB writes)")
    parts.append("")
    parts.append(f"- Run ID: `{run_id}`")
    parts.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    parts.append(f"- Total sites considered: **{total_sites}**")
    parts.append(
        f"- Sites with at least one proposed change (any domain): "
        f"**{len(sites_with_changes)}**"
    )
    parts.append(f"- Sites already in sync: **{sites_unchanged}**")
    for d in DOMAINS:
        n_err = len(fetch_errors.get(d.label, []))
        parts.append(f"- Fetch errors ({d.label} / {d.criterion}): **{n_err}**")
    parts.append("")
    for d in DOMAINS:
        parts.append(f"## {d.criterion} ({d.label}) — proposed changes per column")
        parts.append("")
        parts.append("| Column | Sites that would change |")
        parts.append("|--------|------------------------:|")
        counts = column_change_counts.get(d.label, {})
        for _, col in d.columns:
            parts.append(f"| `{col}` | {counts.get(col, 0)} |")
        parts.append("")

    if not sites_with_changes:
        parts.append("_No sites would change in any domain. Apply step is a no-op._")
        return "\n".join(parts) + "\n"

    parts.append(f"## Sites with proposed changes (showing first {head_limit})")
    parts.append("")
    for entry in sites_with_changes[:head_limit]:
        parts.append(
            f"### {entry['country_code']} — {entry['name']}  (`{entry['site_id']}`)"
        )
        parts.append("")
        parts.append("| domain | column | current_db | proposed |")
        parts.append("|--------|--------|------------|----------|")
        for d in entry["diffs"]:
            parts.append(
                f"| {d['domain']} | `{d['column']}` | `{d['current']}` | `{d['proposed']}` |"
            )
        parts.append("")
    if len(sites_with_changes) > head_limit:
        parts.append(
            f"_+ {len(sites_with_changes) - head_limit} more sites; see JSONL "
            "for the full list._"
        )
        parts.append("")
    for d in DOMAINS:
        errs = fetch_errors.get(d.label, [])
        if not errs:
            continue
        parts.append(f"## Fetch errors ({d.criterion} / {d.label})")
        parts.append("")
        parts.append("| site | country | error |")
        parts.append("|------|---------|-------|")
        for e in errs[:head_limit]:
            parts.append(f"| {e['name']} | {e['country_code']} | `{e['error']}` |")
        parts.append("")
    return "\n".join(parts) + "\n"
