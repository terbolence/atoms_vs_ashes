# man_hours: 1.5
"""Build the near-miss panel of the :class:`MetricsBundle`.

A pair is *near-miss* (plan §9.1) when:

1. it failed on **exactly one** exclusionary criterion (no compound
   knockouts — those are not actionable for threshold tuning), and
2. ``|gap_norm|`` is at or below ``near_miss_gap_pct / 100``.

The panel surfaces the candidates that flip into Set B with the
smallest threshold change, plus a per-country and per-criterion
breakdown so the GUI can answer "*which criterion would unlock the
most sites if we relaxed it by 5%?*" without recomputing scoring.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from atoms_vs_ashes.metrics.bundle import (
    NearMissPanel,
    NearMissRow,
    PerPairFailure,
)


def _would_pass_threshold(
    *, value: float | None, margin: float | None
) -> float | None:
    """Return the numeric threshold at which the site would just pass.

    ``would_pass = value`` is a useful approximation: if the rubric is
    ``metric < threshold`` and the site sits on the failing side, then
    setting the threshold to its measured value flips the predicate
    open by one ulp; the GUI displays this as "set the threshold to X
    and this site qualifies".
    """
    if value is None or margin is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _single_criterion_pairs(
    failures: Sequence[PerPairFailure],
) -> dict[tuple[str, str], list[PerPairFailure]]:
    """Return ``{(site_id, smr_key): [row]}`` for pairs with one failure."""
    by_pair: dict[tuple[str, str], list[PerPairFailure]] = defaultdict(list)
    for f in failures:
        by_pair[(f.site_id, f.smr_key)].append(f)
    return {pair: rows for pair, rows in by_pair.items() if len(rows) == 1}


def _within_gap(row: PerPairFailure, gap_threshold: float) -> bool:
    """True if ``|margin_norm| <= gap_threshold`` (excludes floor rows)."""
    if row.margin_norm is None:
        return False
    return abs(row.margin_norm) <= gap_threshold


def _to_near_miss_row(row: PerPairFailure) -> NearMissRow:
    value_num = None
    try:
        value_num = float(row.value) if row.value is not None else None
    except (TypeError, ValueError):
        value_num = None
    return NearMissRow(
        site_id=row.site_id,
        site_name=row.site_name,
        country_code=row.country_code,
        smr_key=row.smr_key,
        criterion_id=row.criterion_id,
        code=row.code,
        metric=row.metric,
        value=row.value,
        threshold=row.threshold,
        gap=row.margin,
        gap_norm=row.margin_norm,
        would_pass_at_threshold=_would_pass_threshold(
            value=value_num, margin=row.margin,
        ),
    )


def _by_country(rows: Iterable[NearMissRow]) -> list[dict]:
    counter: Counter[str] = Counter()
    for r in rows:
        counter[r.country_code] += 1
    return [
        {"country_code": cc, "n_near_miss": n}
        for cc, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def _by_criterion(rows: Iterable[NearMissRow]) -> list[dict]:
    counter: Counter[tuple[str, str | None]] = Counter()
    for r in rows:
        counter[(r.criterion_id, r.code)] += 1
    return [
        {"criterion_id": cid, "code": code, "n_near_miss": n}
        for (cid, code), n in sorted(
            counter.items(), key=lambda kv: (-kv[1], kv[0])
        )
    ]


def build_near_miss_panel(
    failures: Sequence[PerPairFailure],
    *,
    gap_threshold_pct: float = 10.0,
    max_rows: int | None = None,
) -> NearMissPanel:
    """Filter ``failures`` down to the near-miss panel.

    ``gap_threshold_pct`` is in percent (e.g. ``10.0`` → ``0.10``); a
    pair qualifies when ``|margin_norm|`` is at or below this value.
    The output is sorted ascending by ``|gap_norm|`` so the closest
    misses lead the GUI's table.
    """
    threshold = max(0.0, gap_threshold_pct) / 100.0
    candidates = _single_criterion_pairs(failures)
    selected = [
        _to_near_miss_row(rows[0])
        for rows in candidates.values()
        if _within_gap(rows[0], threshold)
    ]
    selected.sort(
        key=lambda r: abs(r.gap_norm or 0.0)
    )
    if max_rows is not None:
        selected = selected[:max_rows]
    return NearMissPanel(
        gap_threshold_pct=float(gap_threshold_pct),
        rows=selected,
        by_country=_by_country(selected),
        by_criterion=_by_criterion(selected),
    )


__all__ = ["build_near_miss_panel"]
