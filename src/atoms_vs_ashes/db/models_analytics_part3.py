# man_hours: 1.6
"""ORM models for national sensitivity analytics.

Kept separate from ``models_analytics.py`` and ``models_analytics_part2.py``
to preserve the repository's small-file discipline. These tables extend
Phase 1.6 sensitivity with national-rank outputs keyed by
``(country_code, smr_key)``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from atoms_vs_ashes.db.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NationalRankSensitivity(Base):
    """Per-pair national rank delta under one sensitivity profile."""

    __tablename__ = "national_rank_sensitivity"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    smr_key: Mapped[str] = mapped_column(String(30), nullable=False)
    weight_profile: Mapped[str] = mapped_column(String(30), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    baseline_national_rank: Mapped[int | None] = mapped_column(Integer)
    scenario_national_rank: Mapped[int | None] = mapped_column(Integer)
    rank_delta: Mapped[int | None] = mapped_column(Integer)
    baseline_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    scenario_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    score_delta: Mapped[float | None] = mapped_column(Numeric(7, 4))
    scenario_family: Mapped[str | None] = mapped_column(String(30))
    eligible_pair_count: Mapped[int] = mapped_column(Integer, nullable=False)
    small_n_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "weight_profile", "site_id",
            name="pk_national_rank_sensitivity",
        ),
        Index(
            "ix_national_rank_sensitivity_slice",
            "run_id", "country_code", "smr_key", "weight_profile",
        ),
    )


class NationalSensitivitySummary(Base):
    """Per-country/SMR national sensitivity metric summary."""

    __tablename__ = "national_sensitivity_summary"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    smr_key: Mapped[str] = mapped_column(String(30), nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    weight_profile: Mapped[str] = mapped_column(String(30), nullable=False)
    criterion_id: Mapped[str] = mapped_column(String(10), nullable=False)
    family: Mapped[str] = mapped_column(String(30), nullable=False)
    n_pairs: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_abs_rank_delta: Mapped[float | None] = mapped_column(Numeric(8, 4))
    max_abs_rank_delta: Mapped[float | None] = mapped_column(Numeric(8, 4))
    spearman_rho: Mapped[float | None] = mapped_column(Numeric(6, 4))
    top1_changed: Mapped[bool | None] = mapped_column(Boolean)
    top3_jaccard: Mapped[float | None] = mapped_column(Numeric(6, 4))
    top5_jaccard: Mapped[float | None] = mapped_column(Numeric(6, 4))
    small_n_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "metric",
            "weight_profile", "criterion_id", "family",
            name="pk_national_sensitivity_summary",
        ),
        Index(
            "ix_national_sensitivity_summary_slice",
            "run_id", "country_code", "smr_key", "metric",
        ),
    )


class NationalMcRankDistribution(Base):
    """Monte Carlo national-rank probability distribution per pair."""

    __tablename__ = "national_mc_rank_distribution"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    smr_key: Mapped[str] = mapped_column(String(30), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    p_rank_1: Mapped[float | None] = mapped_column(Numeric(6, 4))
    p_rank_le_3: Mapped[float | None] = mapped_column(Numeric(6, 4))
    p_rank_le_5: Mapped[float | None] = mapped_column(Numeric(6, 4))
    median_rank: Mapped[float | None] = mapped_column(Numeric(8, 3))
    p05_rank: Mapped[float | None] = mapped_column(Numeric(8, 3))
    p95_rank: Mapped[float | None] = mapped_column(Numeric(8, 3))
    rank_iqr: Mapped[float | None] = mapped_column(Numeric(8, 3))
    eligible_pair_count: Mapped[int] = mapped_column(Integer, nullable=False)
    small_n_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "site_id",
            name="pk_national_mc_rank_distribution",
        ),
        Index(
            "ix_national_mc_rank_distribution_slice",
            "run_id", "country_code", "smr_key",
        ),
    )
