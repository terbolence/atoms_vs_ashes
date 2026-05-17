# man_hours: 0.8
"""DB-backed Stability ledger for the Results page."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import ALL_COUNTRIES_SENTINEL
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.db.models_analytics import SiteBand


@dataclass
class StabilityRow:
    """One row of the stability ledger."""

    site_id: uuid.UUID
    site_name: str
    country_code: str
    smr_key: str | None
    scope_country_code: str | None
    band: str
    top5pct_hit_rate: float | None
    top10pct_hit_rate: float | None
    top30pct_hit_rate: float | None
    scenarios_total: int
    scenarios_scored: int
    mc_mean: float | None
    mc_low: float | None
    mc_high: float | None


def site_stability_ledger(
    run_id: str, *, country_code: str | None = None,
) -> list[StabilityRow]:
    """Per-site stability bands joined with the MC composite stats."""
    with session_scope() as session:
        mc_profile = _largest_mc_profile(session, run_id)
        return _stability_rows(session, run_id, mc_profile, country_code)


def regional_stability_ledger(run_id: str) -> list[StabilityRow]:
    """Regional stability bands only (all-country sentinel scope)."""
    return site_stability_ledger(run_id, country_code=None)


def national_stability_ledger(run_id: str, *, country_code: str) -> list[StabilityRow]:
    """Country-scoped stability bands for a national sensitivity run."""
    return site_stability_ledger(run_id, country_code=country_code)


def _largest_mc_profile(session: Session, run_id: str) -> str | None:
    """Pick the ``mc_<N>`` weight profile with the highest N."""
    rows = session.execute(
        select(CompositeRanking.weight_profile)
        .where(CompositeRanking.run_id == run_id)
        .distinct()
    ).all()
    candidates: list[tuple[int, str]] = []
    for (label,) in rows:
        if not isinstance(label, str) or not label.startswith("mc_"):
            continue
        try:
            candidates.append((int(label.split("_", 1)[1]), label))
        except ValueError:
            continue
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][1]


def _stability_rows(
    session: Session,
    run_id: str,
    mc_profile: str | None,
    country_code: str | None,
) -> list[StabilityRow]:
    scope_code = country_code or ALL_COUNTRIES_SENTINEL
    rows = session.execute(
        select(
            SiteBand.site_id,
            Site.name,
            Site.country_code,
            SiteBand.smr_key,
            SiteBand.scope_country_code,
            SiteBand.band,
            SiteBand.top5pct_hit_rate,
            SiteBand.top10pct_hit_rate,
            SiteBand.top30pct_hit_rate,
            SiteBand.scenarios_total,
            SiteBand.scenarios_scored,
        )
        .join(Site, Site.site_id == SiteBand.site_id)
        .where(
            (SiteBand.run_id == run_id)
            & (SiteBand.scope_country_code == scope_code)
        )
        .order_by(SiteBand.band, Site.country_code, Site.name)
    ).all()
    mc_lookup = _mc_lookup(session, run_id, mc_profile)
    return [
        _to_stability_row(
            r, mc_lookup.get((r[0], r[3]), (None, None, None)),
        )
        for r in rows
    ]


def _to_stability_row(row, mc: tuple[float | None, ...]) -> StabilityRow:
    return StabilityRow(
        site_id=row[0], site_name=str(row[1]),
        country_code=str(row[2]),
        smr_key=str(row[3]) if row[3] is not None else None,
        scope_country_code=str(row[4]) if row[4] is not None else None,
        band=str(row[5]),
        top5pct_hit_rate=float(row[6]) if row[6] is not None else None,
        top10pct_hit_rate=float(row[7]) if row[7] is not None else None,
        top30pct_hit_rate=float(row[8]) if row[8] is not None else None,
        scenarios_total=int(row[9]),
        scenarios_scored=int(row[10]),
        mc_mean=mc[0], mc_low=mc[1], mc_high=mc[2],
    )


def _mc_lookup(
    session: Session, run_id: str, mc_profile: str | None,
) -> dict[tuple[uuid.UUID, str | None], tuple[float | None, ...]]:
    """Pre-fetch MC composite stats for the (site, smr) pairs."""
    if mc_profile is None:
        return {}
    rows = session.execute(
        select(
            CompositeRanking.site_id,
            CompositeRanking.smr_key,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
        )
        .where(
            (CompositeRanking.run_id == run_id)
            & (CompositeRanking.weight_profile == mc_profile)
        )
    ).all()
    return {
        (sid, str(smr) if smr is not None else None): (
            float(mean) if mean is not None else None,
            float(low) if low is not None else None,
            float(high) if high is not None else None,
        )
        for sid, smr, mean, low, high in rows
    }


__all__ = [
    "StabilityRow",
    "national_stability_ledger",
    "regional_stability_ledger",
    "site_stability_ledger",
]
