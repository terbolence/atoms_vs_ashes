# man_hours: 0.5
"""Country-scoped threshold summaries for the Sensitivity tab."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.db.models_analytics_part2 import ThresholdSensitivity

_PROFILE_TO_DIRECTION = {
    "threshold_minus_25": "minus_25",
    "threshold_plus_25": "plus_25",
}
_DIRECTION_TO_PROFILE = {v: k for k, v in _PROFILE_TO_DIRECTION.items()}


def _baseline_run_id(session: Session, run_id: str) -> str:
    run = session.get(Run, run_id)
    return str(run.parent_run_id) if run and run.parent_run_id else run_id


def _criterion_ids(session: Session, run_id: str) -> list[str]:
    return [
        str(cid)
        for (cid,) in session.execute(
            select(ThresholdSensitivity.criterion_id)
            .where(ThresholdSensitivity.run_id == run_id)
            .distinct()
            .order_by(ThresholdSensitivity.criterion_id)
        ).all()
    ]


def _rows_by_pair(
    session: Session,
    *,
    run_id: str,
    weight_profile: str,
    country_code: str,
) -> dict[tuple[uuid.UUID, str], CompositeRanking]:
    rows = session.execute(
        select(CompositeRanking)
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(
            (CompositeRanking.run_id == run_id)
            & (CompositeRanking.weight_profile == weight_profile)
            & (Site.country_code == country_code)
        )
    ).scalars().all()
    return {(r.site_id, str(r.smr_key)): r for r in rows}


def country_threshold_sensitivity_rows(
    session: Session,
    *,
    run_id: str,
    country_code: str,
    baseline_weight_profile: str,
) -> list[dict]:
    """Derive threshold sweep rows for one country from profile composites."""
    criterion_ids = _criterion_ids(session, run_id)
    if not criterion_ids:
        return []
    baseline = _rows_by_pair(
        session,
        run_id=_baseline_run_id(session, run_id),
        weight_profile=baseline_weight_profile,
        country_code=country_code,
    )
    out: list[dict] = []
    for direction, profile in _DIRECTION_TO_PROFILE.items():
        perturbed = _rows_by_pair(
            session,
            run_id=run_id,
            weight_profile=profile,
            country_code=country_code,
        )
        deltas: list[float] = []
        added = 0
        removed = 0
        for pair, row in perturbed.items():
            base = baseline.get(pair)
            if base is None:
                continue
            if row.passed_exclusionary and not base.passed_exclusionary:
                added += 1
            elif base.passed_exclusionary and not row.passed_exclusionary:
                removed += 1
            if base.composite_score is not None and row.composite_score is not None:
                deltas.append(abs(float(base.composite_score) - float(row.composite_score)))
        mean_delta = sum(deltas) / len(deltas) if deltas else None
        for cid in criterion_ids:
            out.append({
                "criterion_id": cid,
                "direction": direction,
                "n_pairs_affected": len(deltas),
                "mean_abs_score_delta": mean_delta,
                "mean_abs_rank_change": None,
                "survivors_added": added,
                "survivors_removed": removed,
            })
    return out


__all__ = ["country_threshold_sensitivity_rows"]
