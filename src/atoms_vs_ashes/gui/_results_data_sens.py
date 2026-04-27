# man_hours: 0.5
"""DB-backed sensitivity snapshot for the consolidated ``Results`` page.

Reads everything the engine persisted directly for a sensitivity run
(``composite_rankings`` grouped by ``weight_profile``,
``country_balance_check``, ``threshold_sensitivity``) so the
**Sensitivity** tab has live content without needing the offline
metrics bundle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking
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


__all__ = ["SensitivitySnapshot", "sensitivity_snapshot"]
