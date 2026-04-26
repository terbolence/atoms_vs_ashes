# man_hours: 1.25
"""DB-side writers for the failure / swing / threshold tables.

Companion to ``analytics_writers.py`` — split out to respect the
300-line per-file budget. All writers share the same idempotency
pattern (``_wipe`` then ``bulk_save_objects``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models_analytics_part2 import (
    CountryBalanceCheck,
    FailureAggregate,
    FailureOutcome,
    SwingWeight,
    ThresholdSensitivity,
    WeightProfileStability,
)


def _wipe(session: Session, model, **filters) -> None:
    stmt = delete(model)
    for col, value in filters.items():
        stmt = stmt.where(getattr(model, col) == value)
    session.execute(stmt)


def persist_swing_weights(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Any],
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, SwingWeight, run_id=run_id)
    objs = [
        SwingWeight(
            run_id=run_id,
            criterion_id=r.criterion_id,
            family=getattr(r, "family", None),
            name=getattr(r, "name", None),
            declared_weight=getattr(r, "declared", None),
            observed_min=getattr(r, "observed_min", None),
            observed_max=getattr(r, "observed_max", None),
            observed_range=(
                (r.observed_max - r.observed_min)
                if (
                    getattr(r, "observed_min", None) is not None
                    and getattr(r, "observed_max", None) is not None
                )
                else None
            ),
            swing_weight=getattr(r, "swing", None),
            delta=getattr(r, "delta", None),
        )
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_threshold_sensitivity(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Mapping[str, Any]],
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, ThresholdSensitivity, run_id=run_id)
    objs = [
        ThresholdSensitivity(
            run_id=run_id,
            criterion_id=r["criterion_id"],
            direction=r["direction"],
            n_pairs_affected=r.get("n_pairs_affected"),
            mean_abs_score_delta=r.get("mean_abs_score_delta"),
            mean_abs_rank_change=r.get("mean_abs_rank_change"),
            survivors_added=r.get("survivors_added"),
            survivors_removed=r.get("survivors_removed"),
        )
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_weight_profile_stability(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Mapping[str, Any]],
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, WeightProfileStability, run_id=run_id)
    objs = [
        WeightProfileStability(run_id=run_id, **r)
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_country_balance_check(
    session: Session | None,
    *,
    run_id: str,
    rows: Iterable[Mapping[str, Any]],
) -> int:
    if session is None or run_id is None:
        return 0
    _wipe(session, CountryBalanceCheck, run_id=run_id)
    objs = [
        CountryBalanceCheck(run_id=run_id, **r)
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


def persist_failure_outcomes(
    session: Session | None,
    *,
    run_id: str,
    pairs: Iterable[Any],
    country_by_site: Mapping[Any, str] | None = None,
    smr_filter: str | None = None,
) -> int:
    if session is None or run_id is None:
        return 0
    if smr_filter is None:
        _wipe(session, FailureOutcome, run_id=run_id)
    else:
        _wipe(session, FailureOutcome, run_id=run_id, smr_key=smr_filter)
    objs: list[FailureOutcome] = []
    for p in pairs:
        union = set(p.hard_criteria) | set(p.floor_criteria)
        objs.append(FailureOutcome(
            run_id=run_id,
            site_id=p.site_id,
            smr_key=p.smr_key,
            country_code=(country_by_site or {}).get(p.site_id),
            bucket=p.bucket,
            n_hard=len(p.hard_criteria),
            n_floor=len(p.floor_criteria),
            n_distinct_failures=len(union),
            hard_criteria=list(p.hard_criteria) if p.hard_criteria else None,
            floor_criteria=list(p.floor_criteria) if p.floor_criteria else None,
        ))
    session.bulk_save_objects(objs)
    return len(objs)


def persist_failure_aggregates(
    session: Session | None,
    *,
    run_id: str,
    rows: Sequence[Mapping[str, Any]],
    scope_smr_key: str | None = None,
) -> int:
    if session is None or run_id is None:
        return 0
    from atoms_vs_ashes.db.analytics_writers import ALL_SMR_SENTINEL
    scope_value = scope_smr_key if scope_smr_key is not None else ALL_SMR_SENTINEL
    _wipe(
        session, FailureAggregate,
        run_id=run_id, scope_smr_key=scope_value,
    )
    objs = [
        FailureAggregate(
            run_id=run_id,
            axis=r["axis"],
            scope_smr_key=scope_value,
            key=r["key"],
            metric=r["metric"],
            value=r.get("value"),
            extra=r.get("extra"),
        )
        for r in rows
    ]
    session.bulk_save_objects(objs)
    return len(objs)


__all__ = [
    "persist_swing_weights",
    "persist_threshold_sensitivity",
    "persist_weight_profile_stability",
    "persist_country_balance_check",
    "persist_failure_outcomes",
    "persist_failure_aggregates",
]
