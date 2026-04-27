# man_hours: 1.0
"""DB-side verification helpers for finished scoring/sensitivity runs.

A sensitivity run completes in seconds even with thousands of MC draws
(each draw is ``len(rows_by_pair)`` cell evaluations), which can feel
suspicious to a user expecting a long-running job. This module lets the
GUI confirm the actual workload by reading row counts straight from the
database after the child process exits — no heartbeats, no logs, just
the persisted facts:

- ``runs.status`` / ``started_at`` / ``completed_at``
- ``composite_rankings`` rows grouped by ``weight_profile`` (so the
  caller can show ``mc_<iterations>``, ``w_plus_20``, ``w_minus_20`` and
  baseline counts side-by-side)
- ``ranking_scores`` row count (per-criterion scores)
- ``country_balance_check`` row count
- ``threshold_sensitivity`` row count

Read-only and short-lived: every call opens a fresh ``session_scope``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st
from sqlalchemy import func, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking, RankingScore
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.db.models_analytics_part2 import (
    CountryBalanceCheck,
    ThresholdSensitivity,
)


@dataclass
class RunVerification:
    """Snapshot of what a single ``run_id`` actually wrote to the DB."""

    found: bool = False
    run_kind: str | None = None
    status: str | None = None
    started_at_iso: str | None = None
    completed_at_iso: str | None = None
    duration_s: float | None = None
    composite_by_profile: dict[str, int] = field(default_factory=dict)
    ranking_score_rows: int = 0
    country_balance_rows: int = 0
    threshold_sensitivity_rows: int = 0

    @property
    def baseline_rows(self) -> int:
        return int(self.composite_by_profile.get("baseline", 0))

    @property
    def mc_iterations(self) -> int | None:
        """Largest ``mc_<n>`` profile label among composite rows.

        The sensitivity suite labels MC composite rows ``mc_<iterations>``
        (see ``run_sensitivity_suite``); reading the integer suffix back
        confirms the user's requested iteration count actually ran.
        """
        candidates: list[int] = []
        for label in self.composite_by_profile:
            if label.startswith("mc_"):
                try:
                    candidates.append(int(label.split("_", 1)[1]))
                except ValueError:
                    continue
        return max(candidates) if candidates else None

    @property
    def mc_rows(self) -> int:
        return sum(
            n for label, n in self.composite_by_profile.items()
            if label.startswith("mc_")
        )

    @property
    def weight_perturbation_rows(self) -> int:
        return sum(
            n for label, n in self.composite_by_profile.items()
            if label != "baseline" and not label.startswith("mc_")
        )


def read_run_verification(run_id: str) -> RunVerification:
    """Return persisted-row counts + run status for ``run_id``.

    ``RunVerification.found`` is ``False`` when no ``runs`` row exists
    (e.g. a sensitivity run that crashed before ``start_run`` flushed,
    or whose transaction was rolled back). All counts default to zero
    in that case so callers can render a uniform "no rows persisted"
    message.
    """
    with session_scope() as session:
        run = session.get(Run, run_id)
        if run is None:
            return RunVerification(found=False)
        composite_rows = session.execute(
            select(
                CompositeRanking.weight_profile, func.count()
            )
            .where(CompositeRanking.run_id == run_id)
            .group_by(CompositeRanking.weight_profile)
        ).all()
        composite_by_profile = {
            str(profile): int(count) for profile, count in composite_rows
        }
        ranking_score_rows = int(
            session.execute(
                select(func.count())
                .select_from(RankingScore)
                .where(RankingScore.run_id == run_id)
            ).scalar()
            or 0
        )
        country_balance_rows = int(
            session.execute(
                select(func.count())
                .select_from(CountryBalanceCheck)
                .where(CountryBalanceCheck.run_id == run_id)
            ).scalar()
            or 0
        )
        threshold_sensitivity_rows = int(
            session.execute(
                select(func.count())
                .select_from(ThresholdSensitivity)
                .where(ThresholdSensitivity.run_id == run_id)
            ).scalar()
            or 0
        )
        duration: float | None = None
        if run.completed_at is not None and run.started_at is not None:
            duration = (run.completed_at - run.started_at).total_seconds()
        return RunVerification(
            found=True,
            run_kind=run.run_kind,
            status=run.status,
            started_at_iso=(
                run.started_at.isoformat() if run.started_at else None
            ),
            completed_at_iso=(
                run.completed_at.isoformat() if run.completed_at else None
            ),
            duration_s=duration,
            composite_by_profile=composite_by_profile,
            ranking_score_rows=ranking_score_rows,
            country_balance_rows=country_balance_rows,
            threshold_sensitivity_rows=threshold_sensitivity_rows,
        )


def render_verification_panel(run_id: str) -> None:
    """Compact DB-row confirmation card for a finished run.

    Shown by the run-status panel after the child process exits 0;
    surfaces what actually got persisted so the user can sanity-check
    iteration counts (e.g. ``mc_5000`` rows really do exist) without
    leaving the GUI.
    """
    try:
        verif = read_run_verification(run_id)
    except Exception as exc:
        st.caption(f"Could not query run verification: {exc!s}")
        return
    if not verif.found:
        st.caption(
            "No `runs` row was persisted for this run id — the "
            "transaction was rolled back."
        )
        return
    with st.expander("Run verification (DB rows persisted)", expanded=True):
        head_cols = st.columns(3)
        head_cols[0].metric("DB status", verif.status or "—")
        head_cols[1].metric(
            "DB duration",
            f"{verif.duration_s:.1f} s" if verif.duration_s else "—",
        )
        head_cols[2].metric("Run kind", verif.run_kind or "—")
        if verif.run_kind == "sensitivity":
            _render_sensitivity_metrics(verif)
        else:
            _render_scoring_metrics(verif)


def _render_sensitivity_metrics(verif: RunVerification) -> None:
    cols = st.columns(4)
    cols[0].metric(
        "MC iterations (DB)",
        f"{verif.mc_iterations:,}" if verif.mc_iterations else "—",
        help=(
            "Read from the highest ``mc_<N>`` ``weight_profile`` label "
            "found on this run's ``composite_rankings`` rows. Confirms "
            "the requested iteration count actually ran."
        ),
    )
    cols[1].metric(
        "MC ranking rows",
        f"{verif.mc_rows:,}",
        help=(
            "Number of ``composite_rankings`` rows tagged "
            "``mc_<iterations>`` — one per (site × SMR) pair the "
            "Monte-Carlo summary wrote."
        ),
    )
    cols[2].metric(
        "Weight-perturbation rows",
        f"{verif.weight_perturbation_rows:,}",
        help=(
            "``composite_rankings`` rows for sensitivity weight profiles "
            "(``w_plus_20``, ``w_minus_20``, …). One row per profile × "
            "(site × SMR)."
        ),
    )
    cols[3].metric(
        "Baseline rows",
        f"{verif.baseline_rows:,}",
        help=(
            "``composite_rankings`` rows tagged ``baseline`` — written "
            "by the country-balance stage so downstream queries have a "
            "stable reference set."
        ),
    )
    cols2 = st.columns(2)
    cols2[0].metric(
        "Country-balance rows",
        f"{verif.country_balance_rows:,}",
        help="``country_balance_check`` rows — one per country in scope.",
    )
    cols2[1].metric(
        "Threshold-sweep rows",
        f"{verif.threshold_sensitivity_rows:,}",
        help=(
            "``threshold_sensitivity`` rows — one per (site × SMR × "
            "direction) entry in the ±25 % threshold sweep."
        ),
    )
    if verif.composite_by_profile:
        st.caption(
            "weight_profile breakdown: "
            + ", ".join(
                f"`{label}`={count:,}"
                for label, count in sorted(verif.composite_by_profile.items())
            )
        )


def _render_scoring_metrics(verif: RunVerification) -> None:
    cols = st.columns(2)
    cols[0].metric(
        "Composite rows",
        f"{verif.baseline_rows:,}",
        help="``composite_rankings`` rows tagged ``baseline``.",
    )
    cols[1].metric(
        "Per-criterion ranking rows",
        f"{verif.ranking_score_rows:,}",
        help=(
            "``ranking_scores`` rows — one per (site × SMR × "
            "criterion) the engine evaluated."
        ),
    )


__all__ = [
    "RunVerification",
    "read_run_verification",
    "render_verification_panel",
]
