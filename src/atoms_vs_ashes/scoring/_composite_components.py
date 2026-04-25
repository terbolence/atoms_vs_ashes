# man_hours: 0.5
"""Persist per-criterion contributions for a batch of composites.

Split out from ``composite.py`` so each file stays under the 300-line
budget enforced by ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

from sqlalchemy import delete
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models_analytics import CompositeScoreComponent

if TYPE_CHECKING:
    from atoms_vs_ashes.scoring.composite import CompositeResult


def persist_composite_components(
    session: Session,
    results: Iterable["CompositeResult"],
    *,
    run_id: str,
    weight_profile: str,
) -> int:
    """Wipe + insert per-criterion contributions for ``(run_id, profile)``."""
    session.execute(
        delete(CompositeScoreComponent).where(
            CompositeScoreComponent.run_id == run_id,
            CompositeScoreComponent.weight_profile == weight_profile,
        )
    )
    rows: list[CompositeScoreComponent] = []
    for r in results:
        if not r.passed_exclusionary:
            continue
        for c in r.components:
            rows.append(CompositeScoreComponent(
                run_id=run_id,
                site_id=r.site_id,
                smr_key=r.smr_key,
                weight_profile=weight_profile,
                criterion_id=c.criterion_id,
                score_0_10=c.score_0_10,
                weight_normalised=c.weight_normalised,
                weighted_contribution=c.weighted_contribution,
                category=c.category,
            ))
    if rows:
        session.bulk_save_objects(rows)
    return len(rows)


__all__ = ["persist_composite_components"]
