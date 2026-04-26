# man_hours: 1.5
"""ORM models for analytics + provenance tables (Alembic revision 034).

These materialise the artefacts the Phase 1.6 sensitivity / failure /
swing-weight / correlation pipelines used to keep on disk only. They
share the ``Base`` declarative registry with ``models.py`` so Alembic
auto-discovery keeps working without touching the (already-large)
``models.py``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from atoms_vs_ashes.db.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


RunKind = Enum(
    "scoring", "sensitivity", "failure_analysis", "correlation",
    "swing_audit", "extended_analysis",
    name="run_kind",
    create_constraint=True,
)
ThresholdDirection = Enum(
    "plus_25", "minus_25",
    name="threshold_direction",
    create_constraint=True,
)
FailureAggregateAxis = Enum(
    "criterion", "country", "smr", "multi_failure_histogram", "summary",
    name="failure_aggregate_axis",
    create_constraint=True,
)


class Run(Base):
    """Single canonical row per analytics run (scoring, sensitivity, ...)."""

    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    run_kind: Mapped[str] = mapped_column(RunKind, nullable=False)
    parent_run_id: Mapped[str | None] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    cli_command: Mapped[str | None] = mapped_column(Text)
    git_sha: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_runs_kind", "run_kind"),)


class DatasetSnapshot(Base):
    __tablename__ = "dataset_snapshot"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"),
        primary_key=True,
    )
    rubric_file_path: Mapped[str | None] = mapped_column(Text)
    rubric_sha256: Mapped[str | None] = mapped_column(String(64))
    n_sites_total: Mapped[int | None] = mapped_column(Integer)
    n_sites_screened_in: Mapped[int | None] = mapped_column(Integer)
    n_smrs: Mapped[int | None] = mapped_column(Integer)
    n_criteria_exclusionary: Mapped[int | None] = mapped_column(Integer)
    n_criteria_avoidance: Mapped[int | None] = mapped_column(Integer)
    n_criteria_ranking: Mapped[int | None] = mapped_column(Integer)
    weight_normalisation_profile: Mapped[str | None] = mapped_column(String(30))
    run_profile_path: Mapped[str | None] = mapped_column(Text)
    run_profile_sha256: Mapped[str | None] = mapped_column(String(64))
    spec_bundle_path: Mapped[str | None] = mapped_column(Text)
    spec_bundle_sha256: Mapped[str | None] = mapped_column(String(64))
    n_countries_in_scope: Mapped[int | None] = mapped_column(Integer)
    n_smrs_in_scope: Mapped[int | None] = mapped_column(Integer)
    scope_summary: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class CompositeScoreComponent(Base):
    """Per-criterion contribution to a composite ranking row.

    Materialises what ``CompositeRanking.per_category_scores`` carried as
    a JSON blob, so analytics queries can join on ``criterion_id``.
    """

    __tablename__ = "composite_score_components"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    smr_key: Mapped[str] = mapped_column(
        String(30), ForeignKey("smr_designs.smr_key"), nullable=False
    )
    weight_profile: Mapped[str] = mapped_column(String(30), nullable=False)
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    score_0_10: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    weight_normalised: Mapped[float | None] = mapped_column(Numeric(5, 4))
    weighted_contribution: Mapped[float | None] = mapped_column(Numeric(7, 4))
    category: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "site_id", "smr_key", "weight_profile", "criterion_id",
            name="pk_composite_components",
        ),
        Index(
            "ix_csc_pair", "site_id", "smr_key", "weight_profile",
        ),
    )


class SiteBand(Base):
    """A–H stability band for a (site, SMR) under regional or national pool."""

    __tablename__ = "site_bands"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    smr_key: Mapped[str | None] = mapped_column(String(30))
    scope_country_code: Mapped[str | None] = mapped_column(String(2))
    band: Mapped[str] = mapped_column(String(1), nullable=False)
    top5pct_hit_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    top10pct_hit_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    top30pct_hit_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    scenarios_total: Mapped[int] = mapped_column(Integer, nullable=False)
    scenarios_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "site_id", "smr_key", "scope_country_code",
            name="pk_site_bands",
        ),
        UniqueConstraint(
            "run_id", "site_id", "smr_key", "scope_country_code",
            name="uq_site_bands_scope",
        ),
        Index("ix_site_bands_run", "run_id"),
    )


class CountryRankingsSummary(Base):
    __tablename__ = "country_rankings_summary"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    smr_key: Mapped[str | None] = mapped_column(String(30))
    n_sites: Mapped[int] = mapped_column(Integer, nullable=False)
    k_value: Mapped[int] = mapped_column(Integer, nullable=False)
    scenarios_compared: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_jaccard_vs_baseline_topk: Mapped[float | None] = mapped_column(Numeric(5, 4))
    min_jaccard_vs_baseline_topk: Mapped[float | None] = mapped_column(Numeric(5, 4))
    band_a_count: Mapped[int | None] = mapped_column(Integer)
    band_b_count: Mapped[int | None] = mapped_column(Integer)
    band_c_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key",
            name="pk_country_rankings_summary",
        ),
    )


class CountrySiteRanking(Base):
    """Per-site national rank + regional cross-reference.

    The ``acceptability_flag`` mirrors the IAEA-acceptability gate:
    True iff the site survived all hard E-codes and the safety-floor.
    """

    __tablename__ = "country_site_rankings"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    smr_key: Mapped[str] = mapped_column(String(30), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id", ondelete="CASCADE"),
        nullable=False,
    )
    national_rank: Mapped[int | None] = mapped_column(Integer)
    regional_rank: Mapped[int | None] = mapped_column(Integer)
    composite_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    composite_score_low: Mapped[float | None] = mapped_column(Numeric(6, 3))
    composite_score_high: Mapped[float | None] = mapped_column(Numeric(6, 3))
    band: Mapped[str | None] = mapped_column(String(1))
    pairwise_winrate_top5: Mapped[float | None] = mapped_column(Numeric(4, 3))
    p_rank_le_k: Mapped[float | None] = mapped_column(Numeric(4, 3))
    acceptability_flag: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "site_id",
            name="pk_country_site_rankings",
        ),
    )
