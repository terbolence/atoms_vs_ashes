# man_hours: 0.25
"""Run-picker queries for the Results page (keeps ``_results_data`` lean)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking
from atoms_vs_ashes.db.models_analytics import Run

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


@dataclass
class RunSummary:
    """One row of the run-picker dropdown."""

    run_id: str
    run_kind: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None

    @property
    def duration_s(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def label(self) -> str:
        ts = self.completed_at or self.started_at
        when = ts.strftime("%Y-%m-%d %H:%M") if ts else "—"
        return f"{self.run_kind} • {self.run_id} • {self.status} • {when}"


def list_recent_runs(limit: int = 30) -> list[RunSummary]:
    """Return runs ordered newest-first.

    Some validation/replay jobs persist ``composite_rankings`` without a
    canonical ``runs`` row. Include those composite-backed runs so the Results
    page can still inspect them.
    """
    with session_scope() as session:
        rows = session.execute(
            select(
                Run.run_id, Run.run_kind, Run.status,
                Run.started_at, Run.completed_at,
            )
            .order_by(Run.started_at.desc())
            .limit(limit)
        ).all()
        canonical = [
            RunSummary(
                run_id=run_id, run_kind=run_kind, status=status,
                started_at=started_at, completed_at=completed_at,
            )
            for run_id, run_kind, status, started_at, completed_at in rows
        ]
        return _merge_with_composite_runs(session, canonical, None, limit)


def _canonical_runs_for_kind(session, run_kind: str, limit: int) -> list[RunSummary]:
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


def _composite_backed_runs(session, run_kind: str | None) -> list[RunSummary]:
    rows = session.execute(
        select(
            CompositeRanking.run_id,
            func.min(CompositeRanking.ranked_at),
            func.max(CompositeRanking.ranked_at),
            func.count(func.distinct(CompositeRanking.weight_profile)),
        )
        .group_by(CompositeRanking.run_id)
    ).all()
    out: list[RunSummary] = []
    for run_id, first_ranked, last_ranked, n_profiles in rows:
        inferred_kind = "sensitivity" if int(n_profiles or 0) > 1 else "scoring"
        if run_kind is not None and inferred_kind != run_kind:
            continue
        out.append(
            RunSummary(
                run_id=str(run_id),
                run_kind=inferred_kind,
                status="completed",
                started_at=first_ranked,
                completed_at=last_ranked,
            )
        )
    return out


def _merge_with_composite_runs(
    session, canonical: list[RunSummary], run_kind: str | None, limit: int,
) -> list[RunSummary]:
    by_id = {r.run_id: r for r in canonical}
    for inferred in _composite_backed_runs(session, run_kind):
        by_id.setdefault(inferred.run_id, inferred)
    return sorted(
        by_id.values(),
        key=lambda r: r.completed_at or r.started_at or _EPOCH,
        reverse=True,
    )[:limit]


def list_recent_runs_for_kind(
    run_kind: str, *, limit: int = 30,
) -> list[RunSummary]:
    """Return runs of one ``run_kind``, newest-first."""
    with session_scope() as session:
        canonical = _canonical_runs_for_kind(session, run_kind, limit)
        return _merge_with_composite_runs(session, canonical, run_kind, limit)


__all__ = ["RunSummary", "list_recent_runs", "list_recent_runs_for_kind"]
