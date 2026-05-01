# man_hours: 0.25
"""Run-picker queries for the Results page (keeps ``_results_data`` lean)."""

from __future__ import annotations

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.gui._results_data import RunSummary


def list_recent_runs(limit: int = 30) -> list[RunSummary]:
    """Return runs ordered by ``started_at`` DESC."""
    with session_scope() as session:
        rows = session.execute(
            select(
                Run.run_id, Run.run_kind, Run.status,
                Run.started_at, Run.completed_at,
            )
            .order_by(Run.started_at.desc())
            .limit(limit)
        ).all()
    return [
        RunSummary(
            run_id=run_id, run_kind=run_kind, status=status,
            started_at=started_at, completed_at=completed_at,
        )
        for run_id, run_kind, status, started_at, completed_at in rows
    ]


def list_recent_runs_for_kind(
    run_kind: str, *, limit: int = 30,
) -> list[RunSummary]:
    """Return runs of one ``run_kind``, ``started_at`` DESC."""
    with session_scope() as session:
        rows = session.execute(
            select(
                Run.run_id, Run.run_kind, Run.status,
                Run.started_at, Run.completed_at,
            )
            .where(Run.run_kind == run_kind)
            .order_by(Run.started_at.desc())
            .limit(limit)
        ).all()
    return [
        RunSummary(
            run_id=run_id, run_kind=run_kind, status=status,
            started_at=started_at, completed_at=completed_at,
        )
        for run_id, run_kind, status, started_at, completed_at in rows
    ]


__all__ = ["list_recent_runs", "list_recent_runs_for_kind"]
