# man_hours: 0.5
"""Pure diff/render helpers for ``preview_ourairports_vs_db.py``.

Extracted to keep the CLI orchestrator under the 300-line file-size
limit and to make the diff matrix unit-testable without DB or HTTP
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


# Columns the apply batch (`_persist_result`) would touch on
# `site_human_hazards` for HI-01. Keep this list aligned with
# `src/atoms_vs_ashes/connectors/ourairports/batch.py::_persist_result`.
HI01_COLUMNS: tuple[str, ...] = (
    "nearest_airport_km",
    "nearest_airport_name",
    "nearest_airport_type",
    "nearest_airport_class",
    "nearest_airport_runway_length_m",
    "nearest_airport_scheduled_service",
    "flight_path_distance_km",
    "airport_count",
    "hi01_quality",
)

# Mapping from DB column → key on `AirportProximityResult.to_dict()`.
# (Most are 1:1; flight_path is renamed.)
RESULT_KEY_FOR_COLUMN: dict[str, str] = {
    "nearest_airport_km": "nearest_airport_km",
    "nearest_airport_name": "nearest_airport_name",
    "nearest_airport_type": "nearest_airport_type",
    "nearest_airport_class": "nearest_airport_class",
    "nearest_airport_runway_length_m": "nearest_airport_runway_length_m",
    "nearest_airport_scheduled_service": "nearest_airport_scheduled_service",
    "flight_path_distance_km": "nearest_flight_path_km",
    "airport_count": "airport_count",
    "hi01_quality": "quality",
}

# Per-column equality tolerance (numeric). Strings / bools fall through
# to straight equality. Tolerances mirror DB column precision:
# Numeric(8,2) for distances → 0.01 km drift is noise; Numeric(8,1) for
# runway length → 1 m drift is noise.
NUMERIC_TOLERANCES: dict[str, float] = {
    "nearest_airport_km": 0.01,
    "flight_path_distance_km": 0.01,
    "nearest_airport_runway_length_m": 1.0,
}


@dataclass(frozen=True)
class ColumnDiff:
    column: str
    current: Any
    proposed: Any


def coerce(value: Any) -> Any:
    """Normalise DB-returned types so equality tests are meaningful."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def values_equal(column: str, current: Any, proposed: Any) -> bool:
    """Tolerant equality used by the diff matrix."""
    a = coerce(current)
    b = coerce(proposed)
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # Booleans never coerce to float (False==0.0 would wrongly match
    # other zero-ish numerics).
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    tol = NUMERIC_TOLERANCES.get(column)
    if tol is not None:
        try:
            return abs(float(a) - float(b)) <= tol
        except (TypeError, ValueError):
            return a == b
    return a == b


def diff_site(
    *,
    db_row: dict[str, Any],
    proposed: dict[str, Any],
    columns: tuple[str, ...] = HI01_COLUMNS,
) -> list[ColumnDiff]:
    """Return the per-column diffs for one site.

    `db_row` is a mapping of HI-01 column → current DB value (use
    ``None`` when the row is absent). `proposed` is the dict produced by
    `AirportProximityResult.to_dict()` (or compatible).
    """
    diffs: list[ColumnDiff] = []
    for col in columns:
        current = coerce(db_row.get(col))
        proposed_val = proposed.get(RESULT_KEY_FOR_COLUMN.get(col, col))
        if not values_equal(col, current, proposed_val):
            diffs.append(ColumnDiff(col, current, proposed_val))
    return diffs


def render_report_md(
    *,
    total_sites: int,
    sites_with_changes: list[dict[str, Any]],
    sites_unchanged: int,
    fetch_errors: list[dict[str, Any]],
    column_change_counts: dict[str, int],
    run_id: str,
    head_limit: int = 50,
) -> str:
    """Render the human-readable correction proposal report."""
    parts: list[str] = []
    parts.append("<!-- man_hours: 0.3 -->")
    parts.append("# HI-01 OurAirports — preview report (no DB writes)")
    parts.append("")
    parts.append(f"- Run ID: `{run_id}`")
    parts.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    parts.append(f"- Total sites considered: **{total_sites}**")
    parts.append(f"- Sites with at least one proposed change: **{len(sites_with_changes)}**")
    parts.append(f"- Sites already in sync: **{sites_unchanged}**")
    parts.append(f"- Fetch errors: **{len(fetch_errors)}**")
    parts.append("")
    parts.append("## Proposed changes per column")
    parts.append("")
    parts.append("| Column | Sites that would change |")
    parts.append("|--------|------------------------:|")
    for col in HI01_COLUMNS:
        parts.append(f"| `{col}` | {column_change_counts.get(col, 0)} |")
    parts.append("")
    if not sites_with_changes:
        parts.append("_No sites would change. Apply step is a no-op._")
        return "\n".join(parts) + "\n"

    parts.append(f"## Sites with proposed changes (showing first {head_limit})")
    parts.append("")
    for entry in sites_with_changes[:head_limit]:
        parts.append(
            f"### {entry['country_code']} — {entry['name']}  (`{entry['site_id']}`)"
        )
        parts.append("")
        parts.append("| column | current_db | proposed |")
        parts.append("|--------|------------|----------|")
        for d in entry["diffs"]:
            parts.append(
                f"| `{d['column']}` | `{d['current']}` | `{d['proposed']}` |"
            )
        parts.append("")
    if len(sites_with_changes) > head_limit:
        parts.append(
            f"_+ {len(sites_with_changes) - head_limit} more sites; see JSONL "
            "for the full list._"
        )
        parts.append("")
    if fetch_errors:
        parts.append("## Fetch errors")
        parts.append("")
        parts.append("| site | country | error |")
        parts.append("|------|---------|-------|")
        for e in fetch_errors[:head_limit]:
            parts.append(
                f"| {e['name']} | {e['country_code']} | `{e['error']}` |"
            )
        parts.append("")
    return "\n".join(parts) + "\n"
