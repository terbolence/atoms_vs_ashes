# man_hours: 1.0
"""Swing-weight normalisation for the sensitivity audit.

A criterion that scores 5-7 across the entire pool of survivors is
already implicitly down-weighted by the data; pumping its weight up has
no real effect on rankings. The IAEA / multi-criteria-decision-analysis
literature handles this by **swing weighting**: scale each criterion's
declared weight by its observed 0-10 score *range* before normalising.

This module exposes two thin helpers that the swing-weight audit CLI
and the ``w_swing`` perturbation profile consume:

- :func:`observed_ranges` — ``criterion_id -> (min, max)`` from a pool
  of baseline ranking rows (typically restricted to surviving sites so
  excluded zeros don't inflate the range).
- :func:`swing_normalised_weights` — re-scale each criterion's weight
  by its observed range, then renormalise so the new weights sum to 1.
  Falls back to the declared weight when a criterion has zero observed
  range (constant score; swing has no information content).

Both helpers are pure functions with no DB or IO; orchestration lives
in :mod:`scripts.generate_swing_weight_audit` and the sensitivity
suite's per-profile rerun.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import NamedTuple

from atoms_vs_ashes.db.models import RankingScore
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class ObservedRange(NamedTuple):
    minimum: float
    maximum: float

    @property
    def width(self) -> float:
        return max(0.0, self.maximum - self.minimum)


def observed_ranges(
    ranking_rows: Iterable[RankingScore],
) -> dict[str, ObservedRange]:
    """Collapse a flat sequence of ranking rows to per-criterion (min, max).

    Empty input returns ``{}``. Rows with ``score_0_10 is None`` are
    skipped so an unscored row cannot pretend to lower the minimum.
    """
    seen: dict[str, ObservedRange] = {}
    for row in ranking_rows:
        score = getattr(row, "score_0_10", None)
        cid = getattr(row, "criterion_id", None)
        if score is None or cid is None:
            continue
        s = float(score)
        cur = seen.get(cid)
        if cur is None:
            seen[cid] = ObservedRange(minimum=s, maximum=s)
        else:
            seen[cid] = ObservedRange(
                minimum=min(cur.minimum, s),
                maximum=max(cur.maximum, s),
            )
    return seen


def swing_normalised_weights(
    base_weights: Mapping[str, float],
    ranges: Mapping[str, ObservedRange],
) -> dict[str, float]:
    """Return a swing-weighted, renormalised copy of ``base_weights``.

    Scaling rule (per criterion):

    .. code:: python

        scaled[cid] = base_weights[cid] * range_width

    Criteria absent from ``ranges`` (no observed rows) keep their
    declared weight so a missing observation cannot zero the criterion
    out unintentionally. Criteria with zero observed range (constant
    score across the pool) also fall back to the declared weight; they
    carry no swing information so the audit treats them as neutral.

    The returned dict is renormalised to sum to 1.0.
    """
    scaled: dict[str, float] = {}
    for cid, weight in base_weights.items():
        rng = ranges.get(cid)
        width = rng.width if rng is not None else 0.0
        if rng is None or width == 0.0:
            scaled[cid] = float(weight)
        else:
            scaled[cid] = float(weight) * width
    total = sum(scaled.values())
    if total <= 0:
        log.warning("swing_weights_zero_total", n=len(scaled))
        return {cid: float(w) for cid, w in base_weights.items()}
    return {cid: w / total for cid, w in scaled.items()}


def swing_weight_delta(
    base_weights: Mapping[str, float],
    swing_weights: Mapping[str, float],
) -> dict[str, float]:
    """Return per-criterion ``swing - base`` (signed; positive = up-weighted).

    Useful for the audit table so reviewers see at a glance which
    criteria the swing normalisation favours.
    """
    return {
        cid: float(swing_weights.get(cid, 0.0)) - float(base_weights.get(cid, 0.0))
        for cid in set(base_weights) | set(swing_weights)
    }
