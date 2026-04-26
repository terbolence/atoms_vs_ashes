# man_hours: 1.0
"""Pure helpers for failure-margin computation and aggregation.

Kept apart from :mod:`atoms_vs_ashes.metrics.margins` (which orchestrates
verdict iteration) so the gap arithmetic and severity bucketing can be
unit-tested with hand-built specs and dicts.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

EPS = 1e-9
SEVERITY_BUCKETS = (
    ("critical", 0.50),
    ("severe", 0.20),
    ("minor", 0.05),
)
FLOOR_SUFFIX = ":floor"


def is_floor_code(code: str | None) -> bool:
    return bool(code and code.endswith(FLOOR_SUFFIX))


def base_code(code: str | None) -> str | None:
    """Strip the ``:floor`` suffix (or return the code unchanged)."""
    if code is None:
        return None
    if code.endswith(FLOOR_SUFFIX):
        return code[: -len(FLOOR_SUFFIX)]
    return code


def severity_for(gap_norm: float | None) -> str | None:
    """Bucket a normalised gap *magnitude* into critical/severe/minor/trivial.

    Only ``|gap_norm|`` matters for severity — the sign of the gap is
    handled upstream (it indicates which side of the threshold the
    site sits on, see :func:`signed_gap`).
    """
    if gap_norm is None:
        return None
    magnitude = abs(gap_norm)
    for label, threshold in SEVERITY_BUCKETS:
        if magnitude >= threshold:
            return label
    return "trivial"


def signed_gap(*, value: float, threshold: float, op: str) -> float | None:
    """Return ``value - threshold`` (signed).

    The plan's reference example (``nearest_fault_km < 5`` with
    ``value = 3.6`` → ``gap = -1.4``) standardises on
    ``value - threshold`` regardless of the operator. The *sign* tells
    the GUI which side of the boundary the site sits on; severity is
    based on the magnitude only (see :func:`severity_for`). The ``op``
    argument is kept in the signature for forward-compat with future
    operator-specific maths (e.g. window-style criteria).
    """
    del op  # noqa: F841 - reserved for future window-criterion support
    return float(value) - float(threshold)


def normalise_gap(gap: float, threshold: float) -> float:
    """Divide the gap by ``|threshold|`` (clamped to ``EPS``)."""
    denom = max(abs(float(threshold)), EPS)
    return float(gap) / denom


def parse_measured_json(payload: str | None, metric: str | None) -> Any:
    """Pull ``metric`` out of the ``measured_value`` JSON string."""
    if not payload or not metric:
        return None
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, Mapping):
        return None
    return data.get(metric)


def coerce_numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile_of(values: list[float], q: float) -> float | None:
    """Nearest-rank percentile shared with ``_stats.percentile``.

    Re-defined here to avoid importing :mod:`atoms_vs_ashes.metrics._stats`
    (which has cross-package siblings) into the margin path.
    """
    if not values:
        return None
    pct = max(0.0, min(100.0, q))
    sorted_vals = sorted(values)
    rank = max(1, int(round(pct / 100.0 * len(sorted_vals))))
    rank = min(rank, len(sorted_vals))
    return float(sorted_vals[rank - 1])


def top_examples(
    rows: Iterable[Mapping[str, Any]],
    *,
    n: int,
    sort_key: str = "gap",
) -> list[dict[str, Any]]:
    """Return the ``n`` rows with the largest ``|sort_key|`` (NaN last).

    Picks the most-flagrant failures regardless of which side of the
    threshold the site sits on, so the ``examples`` list always shows
    the worst offenders.
    """
    def _key(r: Mapping[str, Any]) -> tuple[int, float]:
        v = r.get(sort_key)
        if v is None:
            return (0, 0.0)
        try:
            return (1, abs(float(v)))
        except (TypeError, ValueError):
            return (0, 0.0)

    sorted_rows = sorted(rows, key=_key, reverse=True)
    return [dict(r) for r in sorted_rows[:n]]


__all__ = [
    "FLOOR_SUFFIX",
    "base_code",
    "coerce_numeric",
    "is_floor_code",
    "normalise_gap",
    "parse_measured_json",
    "percentile_of",
    "severity_for",
    "signed_gap",
    "top_examples",
]
