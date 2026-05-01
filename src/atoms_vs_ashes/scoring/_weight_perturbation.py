# man_hours: 1.0
"""Per-category weight-perturbation helpers for the sensitivity suite.

Extracted from :mod:`sensitivity` to keep each file ≤ 300 lines.
Uniform ±20 % scaling across every criterion is a renormalisation
no-op, so the suite perturbs one family at a time instead.
"""

from __future__ import annotations

from typing import Iterable

from atoms_vs_ashes.db.models import RankingScore, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._swing_weights import (
    observed_ranges,
    swing_normalised_weights,
)
from atoms_vs_ashes.scoring.composite import CompositeResult, compute_composite_for_site_smr
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)

WEIGHT_CATEGORIES: tuple[str, ...] = ("NH", "HI", "RI", "EP", "NS")
WEIGHT_DIRECTIONS: tuple[tuple[str, float, str], ...] = (
    ("plus", 1.2, "plus_20"),
    ("minus", 0.8, "minus_20"),
)
SWING_WEIGHT_PROFILE = "w_swing"


def _category_of(criterion_id: str) -> str:
    """Return the two-letter family prefix upper-cased (e.g. ``NH-02`` → ``NH``)."""
    return criterion_id.split("-", 1)[0].upper()


def perturb_weights_category(
    weights: dict[str, float],
    category: str,
    factor: float,
) -> dict[str, float]:
    """Scale only ``category``'s weights by ``factor`` then renormalise."""
    cat = category.upper()
    scaled = {
        cid: (w * factor if _category_of(cid) == cat else w)
        for cid, w in weights.items()
    }
    total = sum(scaled.values())
    if total <= 0:
        return dict(weights)
    return {cid: w / total for cid, w in scaled.items()}


def perturb_weights(
    weights: dict[str, float],
    direction: str,
) -> dict[str, float]:
    """Return a per-category bump of the ``NH`` family (legacy helper).

    Kept as a thin back-compat shim so any legacy import keeps working.
    """
    factor = 1.2 if direction == "plus" else 0.8 if direction == "minus" else 1.0
    return perturb_weights_category(weights, "NH", factor)


def _swing_weights_from_pool(
    sites_rows: dict[tuple, list[RankingScore]],
    weights: dict[str, float],
) -> dict[str, float]:
    """Return swing-weighted ``criterion_id -> weight`` for the pool.

    Builds the observed ranges from every baseline ranking row across
    the (site, SMR) pool, then delegates to
    :func:`atoms_vs_ashes.scoring._swing_weights.swing_normalised_weights`.
    """
    flat: list[RankingScore] = []
    for rows in sites_rows.values():
        flat.extend(r for r in rows if r.criterion_id in weights)
    return swing_normalised_weights(weights, observed_ranges(flat))


def _composites_for_profile(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
) -> list[CompositeResult]:
    bucket: list[CompositeResult] = []
    for pair, rows in sites_rows.items():
        verdicts = verdicts_by_pair.get(pair, [])
        bucket.append(
            compute_composite_for_site_smr(
                site_id=pair[0],
                smr_key=pair[1],
                ranking_rows=rows,
                verdicts=verdicts,
                weights=weights,
                criteria=criteria,
            )
        )
    return bucket


def run_weight_sensitivity(
    sites_rows: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    *,
    weights: dict[str, float],
    criteria: dict[str, Criterion],
    categories: Iterable[str] = WEIGHT_CATEGORIES,
    include_swing: bool = True,
) -> dict[str, list[CompositeResult]]:
    """Recompute composites for every (site, SMR) under per-category ±20 %.

    Produces profiles ``w_<CAT>_plus_20`` and ``w_<CAT>_minus_20`` for
    every family in ``categories``. When ``include_swing`` is true (the
    default) an extra ``w_swing`` profile is appended that re-weights
    each criterion by its observed 0-10 score range across the pool —
    the IAEA-style swing-weight check requested in the expert review.
    """
    out: dict[str, list[CompositeResult]] = {}
    for cat in categories:
        cat_upper = cat.upper()
        for _name, factor, suffix in WEIGHT_DIRECTIONS:
            label = f"w_{cat_upper}_{suffix}"
            perturbed = perturb_weights_category(weights, cat_upper, factor)
            out[label] = _composites_for_profile(
                sites_rows, verdicts_by_pair, weights=perturbed, criteria=criteria
            )
    if include_swing:
        swing = _swing_weights_from_pool(sites_rows, weights)
        out[SWING_WEIGHT_PROFILE] = _composites_for_profile(
            sites_rows, verdicts_by_pair, weights=swing, criteria=criteria
        )
    log.info(
        "weight_sensitivity_complete",
        pairs=len(sites_rows),
        profiles=list(out.keys()),
    )
    return out
