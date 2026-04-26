# man_hours: 0.5
"""Lightweight statistics helpers for the metrics builder.

Kept separate so the builder stays under the 300-line limit and so the
percentile / sorting logic can be unit-tested without setting up a
full breakdown.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import mean


def percentile(values: Sequence[float], q: float) -> float | None:
    """Return the ``q``-th percentile (0..100) using nearest-rank.

    Returns ``None`` for an empty list. Nearest-rank is preferred over
    linear interpolation here because composite scores are
    discrete-feeling (they live on a 0–10 scale) and reviewers expect
    the p10 / p90 to map to an actual site, not an interpolated value.
    """
    if not values:
        return None
    pct = max(0.0, min(100.0, q))
    sorted_vals = sorted(values)
    rank = max(1, int(round(pct / 100.0 * len(sorted_vals))))
    rank = min(rank, len(sorted_vals))
    return float(sorted_vals[rank - 1])


def composite_distribution(scores: Sequence[float]) -> dict[str, float | None]:
    """Return ``{mean, p10, p90}`` for a list of composites."""
    if not scores:
        return {"mean": None, "p10": None, "p90": None}
    return {
        "mean": float(mean(scores)),
        "p10": percentile(scores, 10),
        "p90": percentile(scores, 90),
    }


def severity_bucket_counts(margins_norm: Sequence[float]) -> dict[str, int]:
    """Bucket normalised margin magnitudes into severity bands.

    Severity is on ``|gap_norm|`` — the sign of the margin only tells
    the GUI which side of the threshold the site is on (handled
    upstream). The buckets follow plan §9: ``critical >= 0.50``,
    ``severe >= 0.20``, ``minor >= 0.05``, ``trivial < 0.05``.
    """
    buckets = {"critical": 0, "severe": 0, "minor": 0, "trivial": 0}
    for m in margins_norm:
        if m is None:
            continue
        magnitude = abs(m)
        if magnitude >= 0.50:
            buckets["critical"] += 1
        elif magnitude >= 0.20:
            buckets["severe"] += 1
        elif magnitude >= 0.05:
            buckets["minor"] += 1
        else:
            buckets["trivial"] += 1
    return buckets


def sort_top_n(items: Sequence, n: int) -> list:
    """Sort by ``composite_score`` descending, keeping ``None`` last."""
    def _key(c) -> tuple[int, float]:
        score = getattr(c, "composite_score", None)
        return (0 if score is None else 1, float(score) if score is not None else 0.0)

    return sorted(items, key=_key, reverse=True)[:n]


__all__ = [
    "composite_distribution",
    "percentile",
    "severity_bucket_counts",
    "sort_top_n",
]
