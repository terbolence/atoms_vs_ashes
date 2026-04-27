# man_hours: 1.5
"""DB-backed scoring definition registry and compiled snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from atoms_vs_ashes.db.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScoringDefinitionState(Base):
    """Singleton revision row for editor cache invalidation."""

    __tablename__ = "scoring_definition_state"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default="active")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class ScoringCriterionDefinition(Base):
    """Authored criterion template, with normalized columns plus raw JSON."""

    __tablename__ = "scoring_criteria"

    criterion_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    family: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phases: Mapped[list] = mapped_column(JSONB, nullable=False)
    weight_factor: Mapped[int] = mapped_column(Integer, nullable=False)
    normalised_weight_pct: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    primary_metric: Mapped[str | None] = mapped_column(String(120))
    band_kind: Mapped[str | None] = mapped_column(String(40))
    db_fields: Mapped[dict | None] = mapped_column(JSONB)
    aggregation: Mapped[dict | None] = mapped_column(JSONB)
    quality_floor: Mapped[dict | None] = mapped_column(JSONB)
    template_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    __table_args__ = (Index("ix_scoring_criteria_family", "family"),)


class ScoringFailConditionDefinition(Base):
    __tablename__ = "scoring_fail_conditions"

    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("scoring_criteria.criterion_id", ondelete="CASCADE"),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_expr: Mapped[str] = mapped_column(Text, nullable=False)
    descriptor: Mapped[str | None] = mapped_column(Text)
    pass_mark: Mapped[float | None] = mapped_column(Numeric(4, 2))
    threshold: Mapped[dict | None] = mapped_column(JSONB)
    threshold_affects_expr: Mapped[bool] = mapped_column(default=True, nullable=False)


class ScoringBandDefinition(Base):
    __tablename__ = "scoring_bands"

    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("scoring_criteria.criterion_id", ondelete="CASCADE"),
        primary_key=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, primary_key=True)
    score_low: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    score_high: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    condition_expr: Mapped[str] = mapped_column(Text, nullable=False)
    descriptor: Mapped[str | None] = mapped_column(Text)


class ScoringSubScoreDefinition(Base):
    __tablename__ = "scoring_sub_scores"

    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("scoring_criteria.criterion_id", ondelete="CASCADE"),
        primary_key=True,
    )
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 4))
    primary_metric: Mapped[str | None] = mapped_column(String(120))
    bands_json: Mapped[list] = mapped_column(JSONB, nullable=False)


class ScoringBandRecipeDefinition(Base):
    __tablename__ = "scoring_band_recipes"

    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("scoring_criteria.criterion_id", ondelete="CASCADE"),
        primary_key=True,
    )
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    fail_code: Mapped[str] = mapped_column(String(40), nullable=False)
    metric: Mapped[str | None] = mapped_column(String(120))
    elevation_pass_m: Mapped[float | None] = mapped_column(Numeric(8, 3))


class CompiledScoringSnapshot(Base):
    __tablename__ = "compiled_scoring_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    compiled_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold_overrides: Mapped[dict] = mapped_column(JSONB, nullable=False)
    bundles_by_smr: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class ScoringRunSnapshot(Base):
    __tablename__ = "scoring_run_snapshots"

    run_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("runs.run_id", ondelete="CASCADE"), primary_key=True
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("compiled_scoring_snapshots.snapshot_id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
