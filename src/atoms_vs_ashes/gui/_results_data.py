# man_hours: 1.0
"""DB-backed read helpers for the consolidated ``Results`` page.

Every helper opens a short-lived :func:`session_scope` and returns a
plain dataclass (no ORM rows leak past this module) so the renderers
can stay thin and Streamlit-friendly. The shape mirrors what the
legacy ``*_metrics.json`` bundle would have carried for the same run,
which lets the renderer fall back to JSON without changing its
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.db.models_analytics import Run

# Re-exported for callers that still import sensitivity helpers from
# this module; the implementation lives in ``_results_data_sens`` to
# keep this file under the 300-line cap.
from atoms_vs_ashes.gui._results_data_sens import (
    SensitivitySnapshot,
    sensitivity_snapshot,
)
from atoms_vs_ashes.runtime.scope import RunScope


def _scope_filter(stmt, scope: RunScope | None):
    return stmt if scope is None else scope.apply_to_composite_query(stmt)


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
    """Return runs ordered by ``started_at`` DESC.

    Filters to runs that *did* persist a ``runs`` row — cancelled /
    rolled-back runs do not appear here, which matches the user's
    expectation that this page only lists results worth analysing.
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
    return [
        RunSummary(
            run_id=run_id, run_kind=run_kind, status=status,
            started_at=started_at, completed_at=completed_at,
        )
        for run_id, run_kind, status, started_at, completed_at in rows
    ]


@dataclass
class CountryRow:
    country_code: str
    n_pairs: int = 0
    n_passed: int = 0
    n_passed_avoidance: int = 0
    n_passed_exclusionary: int = 0
    mean_composite: float | None = None
    min_composite: float | None = None
    max_composite: float | None = None


def list_weight_profiles(run_id: str) -> list[str]:
    """Distinct ``weight_profile`` labels persisted for ``run_id``.

    Scoring runs always produce ``baseline``; sensitivity runs add
    ``country_balanced``, ``threshold_minus_25``, ``threshold_plus_25``,
    ``w_<crit>_<dir>``, and ``mc_<iterations>`` but never ``baseline``.
    Returning the live set lets the renderer offer a sensible default
    + a picker when the user wants to inspect a specific perturbation.
    """
    with session_scope() as session:
        rows = session.execute(
            select(CompositeRanking.weight_profile)
            .where(CompositeRanking.run_id == run_id)
            .distinct()
            .order_by(CompositeRanking.weight_profile)
        ).all()
    return [str(r[0]) for r in rows]


def default_weight_profile(profiles: list[str]) -> str | None:
    """Pick the most "baseline-like" profile from ``profiles``.

    Preference order: ``baseline`` (scoring runs) → ``country_balanced``
    (sensitivity runs, post-country-balance) → first available.
    """
    if not profiles:
        return None
    for candidate in ("baseline", "country_balanced"):
        if candidate in profiles:
            return candidate
    return profiles[0]


def is_single_smr(run_id: str, *, scope: RunScope | None = None) -> bool:
    """True when ``run_id`` (intersected with ``scope``) has one SMR."""
    with session_scope() as session:
        stmt = (
            select(CompositeRanking.smr_key)
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(CompositeRanking.run_id == run_id)
            .distinct()
            .limit(2)
        )
        rows = session.execute(_scope_filter(stmt, scope)).all()
    return len(rows) == 1


def country_breakdown(
    run_id: str, *, weight_profile: str = "baseline",
) -> list[CountryRow]:
    """Per-country aggregate over ``composite_rankings`` for ``run_id``.

    Filters to ``weight_profile`` (default ``baseline``) and joins
    ``sites`` to attribute each (site × SMR) pair to a country, then
    groups + aggregates. Returns an empty list when the requested
    profile has no rows.
    """
    with session_scope() as session:
        passed_both = case(
            (
                (CompositeRanking.passed_exclusionary == True)  # noqa: E712
                & (CompositeRanking.passed_avoidance == True),  # noqa: E712
                1,
            ),
            else_=0,
        )
        rows = session.execute(
            select(
                Site.country_code,
                func.count().label("n_pairs"),
                func.sum(passed_both).label("n_passed"),
                func.sum(
                    case(
                        (CompositeRanking.passed_avoidance == True, 1),  # noqa: E712
                        else_=0,
                    )
                ).label("n_passed_avoidance"),
                func.sum(
                    case(
                        (CompositeRanking.passed_exclusionary == True, 1),  # noqa: E712
                        else_=0,
                    )
                ).label("n_passed_exclusionary"),
                func.avg(CompositeRanking.composite_score).label("mean_c"),
                func.min(CompositeRanking.composite_score).label("min_c"),
                func.max(CompositeRanking.composite_score).label("max_c"),
            )
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
            )
            .group_by(Site.country_code)
            .order_by(Site.country_code)
        ).all()
    return [
        CountryRow(
            country_code=str(cc),
            n_pairs=int(n_pairs or 0),
            n_passed=int(n_passed or 0),
            n_passed_avoidance=int(n_pa or 0),
            n_passed_exclusionary=int(n_pe or 0),
            mean_composite=float(mean_c) if mean_c is not None else None,
            min_composite=float(min_c) if min_c is not None else None,
            max_composite=float(max_c) if max_c is not None else None,
        )
        for cc, n_pairs, n_passed, n_pa, n_pe, mean_c, min_c, max_c in rows
    ]


@dataclass
class TopSiteRow:
    rank_position: int | None
    smr_key: str
    site_name: str
    country_code: str
    composite_score: float | None
    composite_score_low: float | None
    composite_score_high: float | None
    passed_exclusionary: bool
    passed_avoidance: bool
    latitude: float | None = None
    longitude: float | None = None


def top_sites(
    run_id: str,
    *,
    limit: int = 50,
    only_passed: bool = True,
    weight_profile: str = "baseline",
    scope: RunScope | None = None,
) -> list[TopSiteRow]:
    """Top-ranked composite rows for ``run_id`` under ``weight_profile``.

    ``only_passed`` filters to rows that cleared both floors;
    ``scope`` narrows to the active project setup.
    """
    with session_scope() as session:
        stmt = (
            select(
                CompositeRanking.rank_position,
                CompositeRanking.smr_key,
                Site.name,
                Site.country_code,
                CompositeRanking.composite_score,
                CompositeRanking.composite_score_low,
                CompositeRanking.composite_score_high,
                CompositeRanking.passed_exclusionary,
                CompositeRanking.passed_avoidance,
                Site.latitude,
                Site.longitude,
            )
            .join(Site, Site.site_id == CompositeRanking.site_id)
            .where(
                (CompositeRanking.run_id == run_id)
                & (CompositeRanking.weight_profile == weight_profile)
            )
            .order_by(
                CompositeRanking.composite_score.desc().nulls_last(),
            )
            .limit(limit)
        )
        stmt = _scope_filter(stmt, scope)
        if only_passed:
            stmt = stmt.where(
                (CompositeRanking.passed_exclusionary == True)  # noqa: E712
                & (CompositeRanking.passed_avoidance == True)  # noqa: E712
            )
        rows = session.execute(stmt).all()
    return [
        TopSiteRow(
            rank_position=rk,
            smr_key=str(smr),
            site_name=str(name),
            country_code=str(cc),
            composite_score=float(cs) if cs is not None else None,
            composite_score_low=float(lo) if lo is not None else None,
            composite_score_high=float(hi) if hi is not None else None,
            passed_exclusionary=bool(pe),
            passed_avoidance=bool(pa),
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
        )
        for rk, smr, name, cc, cs, lo, hi, pe, pa, lat, lon in rows
    ]


__all__ = [
    "CountryRow",
    "RunSummary",
    "SensitivitySnapshot",
    "TopSiteRow",
    "country_breakdown",
    "default_weight_profile",
    "is_single_smr",
    "list_recent_runs",
    "list_weight_profiles",
    "sensitivity_snapshot",
    "top_sites",
]
