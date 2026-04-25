# man_hours: 0.75
"""Per-direction roll-up for the ±25 % threshold sensitivity sweep.

The current ``run_threshold_sensitivity`` perturbs every numeric
threshold at once, so the per-criterion roll-up replicates the same
global stats across every ranking criterion present in the survivor
pool. Querying a single criterion's row therefore reads "if all numeric
thresholds shift in this direction, here is the global impact". A
future per-criterion threshold pass can replace these rows in-place
without schema change.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import persist_threshold_sensitivity
from atoms_vs_ashes.db.models import CompositeRanking, RankingScore
from atoms_vs_ashes.scoring._suite_threshold import ThresholdSensitivityResult

DIRECTION_TO_ENUM = {
    "threshold_minus_25": "minus_25",
    "threshold_plus_25": "plus_25",
}


def _direction_stats(
    composites,
    baseline_rows: dict[tuple, CompositeRanking],
) -> tuple[list[float], int, int]:
    deltas: list[float] = []
    added = 0
    removed = 0
    for composite in composites:
        base = baseline_rows.get((composite.site_id, composite.smr_key))
        if base is None:
            continue
        if composite.passed_exclusionary and not base.passed_exclusionary:
            added += 1
        elif base.passed_exclusionary and not composite.passed_exclusionary:
            removed += 1
        if (
            base.composite_score is not None
            and composite.composite_score is not None
        ):
            deltas.append(
                abs(float(base.composite_score) - float(composite.composite_score))
            )
    return deltas, added, removed


def persist_threshold_rollup(
    session: Session,
    results_by_direction: dict[str, ThresholdSensitivityResult],
    baseline_rows: dict[tuple, CompositeRanking],
    *,
    run_id: str,
) -> int:
    """Persist one ``threshold_sensitivity`` row per (direction, criterion)."""
    criterion_ids = sorted(
        {
            cid
            for cid in session.execute(
                select(RankingScore.criterion_id).distinct()
            )
            .scalars()
            .all()
        }
    )
    if not criterion_ids:
        return 0
    rows: list[dict[str, object]] = []
    for direction, result in results_by_direction.items():
        enum_value = DIRECTION_TO_ENUM.get(direction)
        if enum_value is None:
            continue
        deltas, added, removed = _direction_stats(result.composites, baseline_rows)
        mean_delta = (sum(deltas) / len(deltas)) if deltas else None
        for cid in criterion_ids:
            rows.append({
                "criterion_id": cid,
                "direction": enum_value,
                "n_pairs_affected": len(deltas),
                "mean_abs_score_delta": mean_delta,
                "mean_abs_rank_change": None,
                "survivors_added": added,
                "survivors_removed": removed,
            })
    return persist_threshold_sensitivity(session, run_id=run_id, rows=rows)


__all__ = ["persist_threshold_rollup", "DIRECTION_TO_ENUM"]
