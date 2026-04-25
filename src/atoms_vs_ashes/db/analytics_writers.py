# man_hours: 1.5
"""DB-side writers for the Phase 1.6 banding / country / OAT / correlation tables.

Producers (CSV writers) call these helpers to fan out their dataclass
rows into the corresponding ORM tables. All writers are idempotent at
the (run_id, scope) level: re-running deletes the prior rows for that
exact slice and re-inserts the fresh values, so a partial run can be
re-driven without manual cleanup.

When ``session`` is ``None`` every writer becomes a no-op so the CSV
side of the pipeline keeps working in unit tests / dry-runs.

Failure / swing / weight-stability writers live in
``analytics_writers_failure.py`` to respect the 300-line file budget.
The package's ``__init__`` re-exports both.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers_failure import (
    persist_country_balance_check,
    persist_failure_aggregates,
    persist_failure_outcomes,
    persist_swing_weights,
    persist_threshold_sensitivity,
    persist_weight_profile_stability,
)
from atoms_vs_ashes.db.models_analytics import SiteBand as SiteBandORM
from atoms_vs_ashes.db.models_analytics import (
    CountryRankingsSummary,
    CountrySiteRanking,
)
from atoms_vs_ashes.db.models_analytics_part2 import (
    CriterionCorrelation,
    OatImportance,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def _wipe(session: Session, model, **filters) -> None:
    """Remove prior rows matching ``filters`` so the writer is idempotent."""
    stmt = delete(model)
    for col, value in filters.items():
        stmt = stmt.where(getattr(model, col) == value)
    session.execute(stmt)


def persist_site_bands(
    session: Session | None,
    *,
    run_id: str,
    bands: Iterable[Any],
    smr_filter: str | None = None,
    country_filter: str | None = None,
) -> int:
    """Insert one ``site_bands`` row per band record."""
    if session is None or run_id is None:
        return 0
    _wipe(
        session, SiteBandORM,
        run_id=run_id,
        smr_key=smr_filter,
        scope_country_code=country_filter,
    )
    rows = [
        SiteBandORM(
            run_id=run_id,
            site_id=b.site_id,
            smr_key=smr_filter,
            scope_country_code=country_filter,
            band=b.band,
            top5pct_hit_rate=b.top5pct_hit_rate,
            top10pct_hit_rate=b.top10pct_hit_rate,
            top30pct_hit_rate=b.top30pct_hit_rate,
            scenarios_total=b.scenarios_total,
            scenarios_scored=b.scenarios_scored,
        )
        for b in bands
    ]
    session.bulk_save_objects(rows)
    return len(rows)


def persist_country_summary(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Any],
    smr_filter: str | None = None,
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(
        session, CountryRankingsSummary,
        run_id=run_id, smr_key=smr_filter,
    )
    objs = [
        CountryRankingsSummary(
            run_id=run_id,
            country_code=r.country_code,
            smr_key=smr_filter,
            n_sites=r.n_sites,
            k_value=r.K,
            scenarios_compared=r.scenarios_compared,
            mean_jaccard_vs_baseline_topk=r.mean_jaccard,
            min_jaccard_vs_baseline_topk=r.min_jaccard,
            band_a_count=getattr(r, "band_a_count", None),
            band_b_count=getattr(r, "band_b_count", None),
            band_c_count=getattr(r, "band_c_count", None),
        )
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_country_site_rankings(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Mapping[str, Any]],
) -> int:
    if session is None or run_id is None:
        return 0
    objs = [CountrySiteRanking(run_id=run_id, **r) for r in rows]
    if not objs:
        return 0
    keys = {(o.country_code, o.smr_key) for o in objs}
    for code, smr in keys:
        _wipe(
            session, CountrySiteRanking,
            run_id=run_id, country_code=code, smr_key=smr,
        )
    session.bulk_save_objects(objs)
    return len(objs)


def persist_oat_importance(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Any],
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, OatImportance, run_id=run_id)
    objs = [
        OatImportance(
            run_id=run_id,
            criterion_id=r.criterion_id,
            family=getattr(r, "family", None),
            criterion_name=getattr(r, "criterion_name", None),
            mean_abs_rank_change=getattr(r, "mean_abs_rank_change", None),
            importance_score=getattr(r, "importance_score", None),
            pairs_compared=getattr(r, "pairs_compared", None),
        )
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_criterion_correlations(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Mapping[str, Any]],
    threshold: float | None = 0.7,
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, CriterionCorrelation, run_id=run_id)
    objs: list[CriterionCorrelation] = []
    for r in rows:
        a, b = sorted([r["criterion_a"], r["criterion_b"]])
        objs.append(CriterionCorrelation(
            run_id=run_id, criterion_a=a, criterion_b=b,
            pearson=r.get("pearson"),
            spearman=r.get("spearman"),
            max_abs=r.get("max_abs"),
            n_pairs=r.get("n_pairs"),
            flagged=bool(r.get("flagged", False)),
            threshold=threshold,
        ))
    session.bulk_save_objects(objs)
    return len(objs)


__all__ = [
    "persist_site_bands",
    "persist_country_summary",
    "persist_country_site_rankings",
    "persist_oat_importance",
    "persist_criterion_correlations",
    "persist_swing_weights",
    "persist_threshold_sensitivity",
    "persist_weight_profile_stability",
    "persist_country_balance_check",
    "persist_failure_outcomes",
    "persist_failure_aggregates",
]
