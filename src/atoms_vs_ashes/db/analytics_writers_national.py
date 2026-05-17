# man_hours: 1.5
"""DB writers for national sensitivity analytics.

The writers are idempotent by run/scope/profile, following the existing
``analytics_writers`` convention. They accept dataclasses or mappings so
pure scoring modules do not need to import ORM classes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models_analytics_part3 import (
    NationalMcRankDistribution,
    NationalRankSensitivity,
    NationalSensitivitySummary,
)

ALL_VALUE = "_all_"


def _get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _wipe(session: Session, model, **filters) -> None:
    stmt = delete(model)
    for col, value in filters.items():
        stmt = stmt.where(getattr(model, col) == value)
    session.execute(stmt)


def _text(value: Any, default: str = ALL_VALUE) -> str:
    if value is None or value == "":
        return default
    return str(value)


def persist_national_rank_sensitivity(
    session: Session | None,
    *,
    run_id: str | None,
    weight_profile: str,
    rows: Iterable[Any],
    scenario_family: str | None = None,
) -> int:
    """Persist per-pair national rank deltas for one profile."""
    if session is None or run_id is None:
        return 0
    rows_list = list(rows)
    if not rows_list:
        return 0
    _wipe(
        session, NationalRankSensitivity,
        run_id=run_id, weight_profile=weight_profile,
    )
    objs = [
        NationalRankSensitivity(
            run_id=run_id,
            country_code=_text(_get(r, "country_code"), "??"),
            smr_key=_text(_get(r, "smr_key")),
            weight_profile=weight_profile,
            site_id=_get(r, "site_id"),
            baseline_national_rank=_get(r, "baseline_rank"),
            scenario_national_rank=_get(r, "scenario_rank"),
            rank_delta=_get(r, "rank_delta"),
            baseline_score=_get(r, "baseline_score"),
            scenario_score=_get(r, "scenario_score"),
            score_delta=_get(r, "score_delta"),
            scenario_family=scenario_family,
            eligible_pair_count=int(_get(r, "eligible_pair_count", 0) or 0),
            small_n_flag=bool(_get(r, "small_n", False)),
        )
        for r in rows_list
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_national_sensitivity_summary(
    session: Session | None,
    *,
    run_id: str | None,
    rows: Iterable[Any],
) -> int:
    """Persist per-slice national sensitivity summary rows."""
    if session is None or run_id is None:
        return 0
    rows_list = list(rows)
    if not rows_list:
        return 0
    metrics = {_text(_get(r, "metric")) for r in rows_list}
    profiles = {_text(_get(r, "weight_profile")) for r in rows_list}
    for metric in metrics:
        for profile in profiles:
            _wipe(
                session, NationalSensitivitySummary,
                run_id=run_id, metric=metric, weight_profile=profile,
            )
    objs = [
        NationalSensitivitySummary(
            run_id=run_id,
            country_code=_text(_get(r, "country_code"), "??"),
            smr_key=_text(_get(r, "smr_key")),
            metric=_text(_get(r, "metric")),
            weight_profile=_text(_get(r, "weight_profile")),
            criterion_id=_text(_get(r, "criterion_id")),
            family=_text(_get(r, "family")),
            n_pairs=int(_get(r, "n_pairs", _get(r, "eligible_pair_count", 0)) or 0),
            mean_abs_rank_delta=_get(r, "mean_abs_rank_delta"),
            max_abs_rank_delta=_get(r, "max_abs_rank_delta"),
            spearman_rho=_get(r, "spearman_rho"),
            top1_changed=_get(r, "top1_changed"),
            top3_jaccard=_get(r, "top3_jaccard"),
            top5_jaccard=_get(r, "top5_jaccard"),
            small_n_flag=bool(_get(r, "small_n", _get(r, "small_n_flag", False))),
            extra=_get(r, "extra"),
        )
        for r in rows_list
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_national_oat_importance(
    session: Session | None,
    run_id: str | None,
    rows: Iterable[Any],
) -> int:
    """Persist national OAT rows into ``national_sensitivity_summary``."""
    summary_rows = [
        {
            "country_code": _get(r, "country_code"),
            "smr_key": _get(r, "smr_key"),
            "metric": "oat_importance",
            "weight_profile": ALL_VALUE,
            "criterion_id": _get(r, "criterion_id"),
            "family": _get(r, "family"),
            "n_pairs": _get(r, "eligible_pair_count"),
            "mean_abs_rank_delta": _get(r, "mean_abs_rank_change"),
            "max_abs_rank_delta": None,
            "spearman_rho": None,
            "top1_changed": None,
            "top3_jaccard": None,
            "top5_jaccard": None,
            "small_n": _get(r, "small_n"),
            "extra": {
                "pairs_compared": _get(r, "pairs_compared"),
                "importance_score": _get(r, "importance_score"),
            },
        }
        for r in rows
    ]
    return persist_national_sensitivity_summary(
        session, run_id=run_id, rows=summary_rows,
    )


def persist_national_mc_rank_distribution(
    session: Session | None,
    *,
    run_id: str | None,
    rows: Iterable[Any],
) -> int:
    """Persist MC national-rank probability rows."""
    if session is None or run_id is None:
        return 0
    rows_list = list(rows)
    if not rows_list:
        return 0
    _wipe(session, NationalMcRankDistribution, run_id=run_id)
    objs = [
        NationalMcRankDistribution(
            run_id=run_id,
            country_code=_text(_get(r, "country_code"), "??"),
            smr_key=_text(_get(r, "smr_key")),
            site_id=_get(r, "site_id"),
            iterations=int(_get(r, "iterations", 0) or 0),
            p_rank_1=_get(r, "p_rank_1"),
            p_rank_le_3=_get(r, "p_rank_le_3"),
            p_rank_le_5=_get(r, "p_rank_le_5"),
            median_rank=_get(r, "median_rank"),
            p05_rank=_get(r, "p05_rank"),
            p95_rank=_get(r, "p95_rank"),
            rank_iqr=_get(r, "rank_iqr"),
            eligible_pair_count=int(_get(r, "eligible_pair_count", 0) or 0),
            small_n_flag=bool(_get(r, "small_n", _get(r, "small_n_flag", False))),
        )
        for r in rows_list
    ]
    session.bulk_save_objects(objs)
    return len(objs)


__all__ = [
    "ALL_VALUE",
    "persist_national_mc_rank_distribution",
    "persist_national_oat_importance",
    "persist_national_rank_sensitivity",
    "persist_national_sensitivity_summary",
]
