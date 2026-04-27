# man_hours: 0.5
"""DB-backed sensitivity snapshot for the consolidated ``Results`` page.

Reads everything the engine persisted directly for a sensitivity run
(``composite_rankings`` grouped by ``weight_profile``,
``country_balance_check``, ``threshold_sensitivity``) so the
**Sensitivity** tab has live content without needing the offline
metrics bundle.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.db.models_analytics import SiteBand
from atoms_vs_ashes.db.models_analytics_part2 import (
    CountryBalanceCheck,
    ThresholdSensitivity,
)


@dataclass
class SensitivitySnapshot:
    composite_by_profile: dict[str, int] = field(default_factory=dict)
    country_balance: list[dict] = field(default_factory=list)
    threshold_sweep: list[dict] = field(default_factory=list)

    @property
    def mc_iterations(self) -> int | None:
        candidates: list[int] = []
        for label in self.composite_by_profile:
            if label.startswith("mc_"):
                try:
                    candidates.append(int(label.split("_", 1)[1]))
                except ValueError:
                    continue
        return max(candidates) if candidates else None


def sensitivity_snapshot(run_id: str) -> SensitivitySnapshot:
    """All sensitivity rows persisted for ``run_id`` (no JSON bundle needed)."""
    with session_scope() as session:
        return SensitivitySnapshot(
            composite_by_profile=_composite_breakdown(session, run_id),
            country_balance=_country_balance_rows(session, run_id),
            threshold_sweep=_threshold_sensitivity_rows(session, run_id),
        )


def _composite_breakdown(session: Session, run_id: str) -> dict[str, int]:
    rows = session.execute(
        select(CompositeRanking.weight_profile, func.count())
        .where(CompositeRanking.run_id == run_id)
        .group_by(CompositeRanking.weight_profile)
    ).all()
    return {str(profile): int(n) for profile, n in rows}


def _country_balance_rows(session: Session, run_id: str) -> list[dict]:
    rows = session.execute(
        select(
            CountryBalanceCheck.country_code,
            CountryBalanceCheck.baseline_count,
            CountryBalanceCheck.balanced_count,
            CountryBalanceCheck.delta,
            CountryBalanceCheck.triggered_floor_swap,
        )
        .where(CountryBalanceCheck.run_id == run_id)
        .order_by(CountryBalanceCheck.country_code)
    ).all()
    return [
        {
            "country_code": cc,
            "baseline_count": int(bc),
            "balanced_count": int(balc),
            "delta": int(d),
            "triggered_floor_swap": bool(swap),
        }
        for cc, bc, balc, d, swap in rows
    ]


def _threshold_sensitivity_rows(session: Session, run_id: str) -> list[dict]:
    rows = session.execute(
        select(
            ThresholdSensitivity.criterion_id,
            ThresholdSensitivity.direction,
            ThresholdSensitivity.n_pairs_affected,
            ThresholdSensitivity.mean_abs_score_delta,
            ThresholdSensitivity.mean_abs_rank_change,
            ThresholdSensitivity.survivors_added,
            ThresholdSensitivity.survivors_removed,
        )
        .where(ThresholdSensitivity.run_id == run_id)
        .order_by(
            ThresholdSensitivity.criterion_id, ThresholdSensitivity.direction,
        )
    ).all()
    return [
        {
            "criterion_id": cid,
            "direction": direction,
            "n_pairs_affected": int(n) if n is not None else None,
            "mean_abs_score_delta": (
                float(d) if d is not None else None
            ),
            "mean_abs_rank_change": (
                float(r) if r is not None else None
            ),
            "survivors_added": int(sa) if sa is not None else None,
            "survivors_removed": int(sr) if sr is not None else None,
        }
        for cid, direction, n, d, r, sa, sr in rows
    ]


@dataclass
class StabilityRow:
    """One row of the stability ledger (Tool 6)."""

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


def site_stability_ledger(run_id: str) -> list[StabilityRow]:
    """Per-site stability bands joined with the MC composite stats.

    Pulls every ``site_bands`` row for ``run_id`` and joins to the
    matching ``composite_rankings`` row produced by the Monte-Carlo
    weight profile (``mc_<N>``). The MC stats are taken from the
    largest ``mc_<N>`` profile available, which is the canonical
    Monte-Carlo summary surface for the run.

    Returns an empty list for non-sensitivity runs (``site_bands``
    is sensitivity-only).
    """
    with session_scope() as session:
        mc_profile = _largest_mc_profile(session, run_id)
        return _stability_rows(session, run_id, mc_profile)


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
    session: Session, run_id: str, mc_profile: str | None,
) -> list[StabilityRow]:
    stmt = (
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
        .where(SiteBand.run_id == run_id)
        .order_by(
            SiteBand.band, Site.country_code, Site.name,
        )
    )
    rows = session.execute(stmt).all()
    mc_lookup = _mc_lookup(session, run_id, mc_profile)
    out: list[StabilityRow] = []
    for r in rows:
        key = (r[0], r[3])
        mc = mc_lookup.get(key, (None, None, None))
        out.append(
            StabilityRow(
                site_id=r[0], site_name=str(r[1]),
                country_code=str(r[2]),
                smr_key=str(r[3]) if r[3] is not None else None,
                scope_country_code=(
                    str(r[4]) if r[4] is not None else None
                ),
                band=str(r[5]),
                top5pct_hit_rate=(
                    float(r[6]) if r[6] is not None else None
                ),
                top10pct_hit_rate=(
                    float(r[7]) if r[7] is not None else None
                ),
                top30pct_hit_rate=(
                    float(r[8]) if r[8] is not None else None
                ),
                scenarios_total=int(r[9]),
                scenarios_scored=int(r[10]),
                mc_mean=mc[0], mc_low=mc[1], mc_high=mc[2],
            )
        )
    return out


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
    "SensitivitySnapshot",
    "StabilityRow",
    "sensitivity_snapshot",
    "site_stability_ledger",
]
