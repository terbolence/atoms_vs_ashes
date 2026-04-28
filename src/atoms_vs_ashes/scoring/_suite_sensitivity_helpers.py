# man_hours: 0.05
"""Small helpers for :mod:`atoms_vs_ashes.scoring.suite`."""

from __future__ import annotations


def build_ranked_country_list(
    country_by_pair: dict[tuple, str],
    baseline_rows,
) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for pair, base in baseline_rows.items():
        if base.composite_score is None:
            continue
        country = country_by_pair.get(pair, "??")
        ranked.append((country, float(base.composite_score)))
    ranked.sort(key=lambda kv: kv[1], reverse=True)
    return ranked


__all__ = ["build_ranked_country_list"]
