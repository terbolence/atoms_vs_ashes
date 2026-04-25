# man_hours: 1.5
"""ORM models for sensitivity / failure / swing / correlation tables.

Continuation of ``models_analytics.py`` — kept in a sibling file to
respect the 300-line per-file budget. All classes register on the same
``Base`` declarative registry.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from atoms_vs_ashes.db.models import Base
from atoms_vs_ashes.db.models_analytics import (
    FailureAggregateAxis,
    ThresholdDirection,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OatImportance(Base):
    __tablename__ = "oat_importance"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    family: Mapped[str | None] = mapped_column(String(10))
    criterion_name: Mapped[str | None] = mapped_column(String(200))
    mean_abs_rank_change: Mapped[float | None] = mapped_column(Numeric(8, 4))
    importance_score: Mapped[float | None] = mapped_column(Numeric(8, 4))
    pairs_compared: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "criterion_id", name="pk_oat_importance",
        ),
    )


class WeightProfileStability(Base):
    __tablename__ = "weight_profile_stability"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    weight_profile: Mapped[str] = mapped_column(String(30), nullable=False)
    scored_pairs: Mapped[int] = mapped_column(Integer, nullable=False)
    top5_overlap_jaccard: Mapped[float | None] = mapped_column(Numeric(5, 4))
    top10_overlap_jaccard: Mapped[float | None] = mapped_column(Numeric(5, 4))
    top5_overlap_count: Mapped[int | None] = mapped_column(Integer)
    top10_overlap_count: Mapped[int | None] = mapped_column(Integer)
    mean_abs_score_delta: Mapped[float | None] = mapped_column(Numeric(7, 4))
    max_abs_score_delta: Mapped[float | None] = mapped_column(Numeric(7, 4))
    pairs_drift_compared: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "weight_profile", name="pk_weight_profile_stability",
        ),
    )


class ThresholdSensitivity(Base):
    __tablename__ = "threshold_sensitivity"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    direction: Mapped[str] = mapped_column(ThresholdDirection, nullable=False)
    n_pairs_affected: Mapped[int | None] = mapped_column(Integer)
    mean_abs_score_delta: Mapped[float | None] = mapped_column(Numeric(7, 4))
    mean_abs_rank_change: Mapped[float | None] = mapped_column(Numeric(8, 4))
    survivors_added: Mapped[int | None] = mapped_column(Integer)
    survivors_removed: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "criterion_id", "direction",
            name="pk_threshold_sensitivity",
        ),
    )


class FailureOutcome(Base):
    """One row per (run, site, SMR) classifying the failure mode."""

    __tablename__ = "failure_outcomes"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    smr_key: Mapped[str] = mapped_column(String(30), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    bucket: Mapped[str] = mapped_column(String(12), nullable=False)
    n_hard: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_floor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_distinct_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hard_criteria: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    floor_criteria: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "site_id", "smr_key", name="pk_failure_outcomes",
        ),
        CheckConstraint(
            "bucket IN ('survived', 'hard_only', 'floor_only', 'both')",
            name="ck_failure_outcomes_bucket",
        ),
        Index("ix_failure_outcomes_country", "run_id", "country_code"),
    )


class FailureAggregate(Base):
    """Roll-up of failure outcomes along a single axis (country / criterion / SMR / ...)."""

    __tablename__ = "failure_aggregates"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    axis: Mapped[str] = mapped_column(FailureAggregateAxis, nullable=False)
    scope_smr_key: Mapped[str | None] = mapped_column(String(30))
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(14, 4))
    extra: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "axis", "scope_smr_key", "key", "metric",
            name="pk_failure_aggregates",
        ),
    )


class SwingWeight(Base):
    __tablename__ = "swing_weights"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    family: Mapped[str | None] = mapped_column(String(10))
    name: Mapped[str | None] = mapped_column(String(200))
    declared_weight: Mapped[float | None] = mapped_column(Numeric(7, 6))
    observed_min: Mapped[float | None] = mapped_column(Numeric(4, 1))
    observed_max: Mapped[float | None] = mapped_column(Numeric(4, 1))
    observed_range: Mapped[float | None] = mapped_column(Numeric(4, 1))
    swing_weight: Mapped[float | None] = mapped_column(Numeric(7, 6))
    delta: Mapped[float | None] = mapped_column(Numeric(7, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "criterion_id", name="pk_swing_weights",
        ),
    )


class CriterionCorrelation(Base):
    __tablename__ = "criterion_correlations"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    criterion_a: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    criterion_b: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    pearson: Mapped[float | None] = mapped_column(Numeric(6, 4))
    spearman: Mapped[float | None] = mapped_column(Numeric(6, 4))
    max_abs: Mapped[float | None] = mapped_column(Numeric(6, 4))
    n_pairs: Mapped[int | None] = mapped_column(Integer)
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threshold: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "criterion_a", "criterion_b",
            name="pk_criterion_correlations",
        ),
        CheckConstraint(
            "criterion_a < criterion_b",
            name="ck_criterion_correlations_pair_order",
        ),
    )


class CountryBalanceCheck(Base):
    __tablename__ = "country_balance_check"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    baseline_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balanced_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    triggered_floor_swap: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", name="pk_country_balance_check",
        ),
    )
