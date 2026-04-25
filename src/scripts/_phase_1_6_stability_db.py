# man_hours: 0.4
"""Persist Phase 1.6 cross-profile analytics into ``weight_profile_stability``.

Split out from ``_phase_1_6_audit.py`` to respect the 300-line file
budget enforced by ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers_failure import (
    persist_weight_profile_stability,
)
from scripts._phase_1_6_analytics import PhaseAnalytics


def persist_stability(
    db_session: Session | None,
    run_id: str,
    analytics: PhaseAnalytics,
) -> int:
    """Forward analytics roll-up into ``weight_profile_stability``."""
    if db_session is None:
        return 0
    rows = [
        {
            "weight_profile": p.label,
            "n_pairs": p.pairs_drift_compared,
            "top5_overlap_jaccard": p.top5pct_jaccard,
            "top10_overlap_jaccard": p.top10pct_jaccard,
            "mean_abs_score_delta": p.mean_abs_drift,
            "max_abs_rank_change": None,
            "country_count_changed": None,
        }
        for p in analytics.profiles
    ]
    if not rows:
        return 0
    return persist_weight_profile_stability(db_session, run_id=run_id, rows=rows)


__all__ = ["persist_stability"]
