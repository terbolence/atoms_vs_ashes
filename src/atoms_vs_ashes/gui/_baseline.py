# man_hours: 0.6
"""Baseline-view resolver for the Results page.

Sensitivity runs persist ``composite_rankings`` under a fresh
``run_id`` but do **not** copy ``screening_verdicts`` from the parent
scoring run. The Results page (Coverage / Sites / Regional / Stability
/ KPI tabs) needs the *parent* scoring ``run_id`` so the verdict join
finds rows; otherwise ``passed_exclusionary=False`` flags propagate
without their explanation and the UI shows ``status="hard-fail"`` with
``n_failed_criteria=0``.

The resolver returns the ``run_id`` + ``weight_profile`` pair that
holds the canonical ``baseline`` composite + the matching verdicts.
For a scoring run that's the run itself; for a sensitivity run with a
populated ``runs.parent_run_id`` we follow the FK; for an older
sensitivity run with ``parent_run_id=NULL`` we fall back to "the most
recent ``composite_rankings`` row whose ``weight_profile = baseline``"
which mirrors :func:`atoms_vs_ashes.scoring._suite_persist._resolve_baseline_run_id`.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import CompositeRanking
from atoms_vs_ashes.db.models_analytics import Run

DEFAULT_WEIGHT_PROFILE = "baseline"


@dataclass(frozen=True)
class BaselineView:
    """Resolved (run_id, weight_profile) for the canonical Results view."""

    run_id: str
    weight_profile: str
    source: str  # "self" | "parent_run_id" | "fallback_latest_baseline"
    sensitivity_run_id: str | None  # original run_id when source != "self"


def resolve_baseline_view(run_id: str) -> BaselineView:
    """Return the (run_id, weight_profile) carrying baseline + verdicts.

    Pure read; opens its own short-lived session.
    """
    with session_scope() as session:
        row = session.execute(
            select(Run.run_kind, Run.parent_run_id).where(Run.run_id == run_id)
        ).first()
        run_kind = str(row[0]) if row else "scoring"
        parent_run_id = str(row[1]) if row and row[1] else None

        if run_kind not in {"sensitivity", "national_sensitivity"}:
            return BaselineView(
                run_id=run_id, weight_profile=DEFAULT_WEIGHT_PROFILE,
                source="self", sensitivity_run_id=None,
            )

        if parent_run_id:
            return BaselineView(
                run_id=parent_run_id, weight_profile=DEFAULT_WEIGHT_PROFILE,
                source="parent_run_id", sensitivity_run_id=run_id,
            )

        fallback = session.execute(
            select(CompositeRanking.run_id)
            .where(CompositeRanking.weight_profile == DEFAULT_WEIGHT_PROFILE)
            .order_by(CompositeRanking.ranked_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if fallback:
            return BaselineView(
                run_id=str(fallback), weight_profile=DEFAULT_WEIGHT_PROFILE,
                source="fallback_latest_baseline", sensitivity_run_id=run_id,
            )

    # Last-ditch: nothing to resolve to — return the sensitivity run_id
    # itself so callers degrade to "no verdicts" rather than crash.
    return BaselineView(
        run_id=run_id, weight_profile=DEFAULT_WEIGHT_PROFILE,
        source="self", sensitivity_run_id=run_id,
    )


__all__ = ["BaselineView", "DEFAULT_WEIGHT_PROFILE", "resolve_baseline_view"]
