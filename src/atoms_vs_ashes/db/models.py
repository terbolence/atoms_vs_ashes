"""SQLAlchemy ORM models — mirrors architecture/specs/02_data_model_postgres.md."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

PlantType = Enum(
    "coal", "lignite", "gas", "thermal", "other",
    name="plant_type",
    create_constraint=True,
)

SiteStatus = Enum(
    "operating", "retired", "mothballed", "announced",
    "pre_permit", "permitted", "construction", "shelved",
    "cancelled", "planned_closure", "other",
    name="site_status",
    create_constraint=True,
)

ScreeningVerdict = Enum(
    "pass", "fail", "inconclusive",
    name="screening_verdict",
    create_constraint=True,
)

QualityLevel = Enum(
    "high", "medium", "low", "insufficient",
    name="quality_level",
    create_constraint=True,
)


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------

class Country(Base):
    __tablename__ = "countries"

    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str | None] = mapped_column(String(60))
    nuclear_policy_notes: Mapped[str | None] = mapped_column(Text)


class DataSource(Base):
    __tablename__ = "data_sources"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Criterion(Base):
    __tablename__ = "criteria"

    criterion_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    weight: Mapped[float | None] = mapped_column(Numeric(5, 4))
    iaea_reference: Mapped[str | None] = mapped_column(String(200))
    epri_reference: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)


# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------

class Site(Base):
    __tablename__ = "sites"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    alternative_names: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    country_code: Mapped[str] = mapped_column(
        String(2), ForeignKey("countries.country_code"), nullable=False
    )
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    location_accuracy: Mapped[str | None] = mapped_column(String(30))
    local_area: Mapped[str | None] = mapped_column(String(200))
    subnational_unit: Mapped[str | None] = mapped_column(String(200))
    region: Mapped[str | None] = mapped_column(String(60))

    plant_type: Mapped[str | None] = mapped_column(PlantType)
    installed_capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str | None] = mapped_column(SiteStatus)
    start_year: Mapped[int | None] = mapped_column(Integer)
    retired_year: Mapped[int | None] = mapped_column(Integer)
    planned_retirement: Mapped[date | None] = mapped_column(Date)
    coal_phaseout_year: Mapped[int | None] = mapped_column(Integer)

    grid_voltage_kv: Mapped[int | None] = mapped_column(Integer)
    grid_capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    cooling_water_source: Mapped[str | None] = mapped_column(String(200))
    site_area_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    elevation_m: Mapped[float | None] = mapped_column(Numeric(8, 2))

    owner_operator: Mapped[str | None] = mapped_column(Text)
    parent_company: Mapped[str | None] = mapped_column(Text)
    combustion_technology: Mapped[str | None] = mapped_column(String(100))
    coal_type: Mapped[str | None] = mapped_column(String(100))
    coal_source: Mapped[str | None] = mapped_column(Text)
    net_zero_year: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(Text)
    permits: Mapped[str | None] = mapped_column(Text)
    permit_date: Mapped[date | None] = mapped_column(Date)

    owner_gem_id: Mapped[str | None] = mapped_column(Text)
    parent_gem_id: Mapped[str | None] = mapped_column(Text)
    gem_unit_phase_id: Mapped[str | None] = mapped_column(String(30))
    gem_location_id: Mapped[str | None] = mapped_column(String(30))
    wiki_url: Mapped[str | None] = mapped_column(Text)

    extended_data: Mapped[dict | None] = mapped_column(JSONB)

    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    ownership_records = relationship("SiteOwnership", back_populates="site")
    attributes = relationship("SiteAttribute", back_populates="site")
    infrastructure = relationship("SiteInfrastructure", back_populates="site")
    scores = relationship("SiteScore", back_populates="site")
    screening_results = relationship("ScreeningResult", back_populates="site")
    quality_flags = relationship("DataQualityFlag", back_populates="site")

    __table_args__ = (
        Index("ix_sites_gem_location_id", "gem_location_id"),
        Index("ix_sites_gem_unit_phase_id", "gem_unit_phase_id"),
        Index("ix_sites_country_code", "country_code"),
        Index("ix_sites_geom", "geom", postgresql_using="gist"),
    )


class SiteOwnership(Base):
    __tablename__ = "site_ownership"

    ownership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    parent_gem_entity_id: Mapped[str | None] = mapped_column(String(30))
    parent_name: Mapped[str | None] = mapped_column(Text)
    parent_reg_country: Mapped[str | None] = mapped_column(String(120))
    parent_hq_country: Mapped[str | None] = mapped_column(String(120))
    project: Mapped[str | None] = mapped_column(Text)
    share_pct: Mapped[float | None] = mapped_column(Numeric(7, 4))
    ownership_path: Mapped[str | None] = mapped_column(Text)
    immediate_owner: Mapped[str | None] = mapped_column(Text)
    immediate_owner_gem_id: Mapped[str | None] = mapped_column(String(30))
    tracker: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(40))
    capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    gem_location_id: Mapped[str | None] = mapped_column(String(30))
    gem_unit_id: Mapped[str | None] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="ownership_records")

    __table_args__ = (
        Index("ix_ownership_site_id", "site_id"),
        Index("ix_ownership_gem_location_id", "gem_location_id"),
    )


class StagingUnmatchedOwnership(Base):
    """Ownership rows that could not be joined to any site."""

    __tablename__ = "_staging_unmatched_ownership"

    row_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


class SiteAttribute(Base):
    __tablename__ = "site_attributes"

    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    value_numeric: Mapped[float | None] = mapped_column(Numeric)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.source_id")
    )
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    cache_status: Mapped[str | None] = mapped_column(String(20))

    site = relationship("Site", back_populates="attributes")

    __table_args__ = (
        UniqueConstraint("site_id", "criterion_id", "run_id", name="uq_site_criterion_run"),
        Index("ix_attr_site_id", "site_id"),
    )


class SiteInfrastructure(Base):
    __tablename__ = "site_infrastructure"

    infra_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False, unique=True
    )
    grid_voltage_kv: Mapped[int | None] = mapped_column(Integer)
    grid_capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    substation_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    cooling_source_type: Mapped[str | None] = mapped_column(String(60))
    cooling_source_name: Mapped[str | None] = mapped_column(String(200))
    cooling_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    transport_road: Mapped[bool | None] = mapped_column(Boolean)
    transport_rail: Mapped[bool | None] = mapped_column(Boolean)
    transport_waterway: Mapped[bool | None] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)

    site = relationship("Site", back_populates="infrastructure")


class SiteScore(Base):
    __tablename__ = "site_scores"

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    justification: Mapped[str | None] = mapped_column(Text)
    source_refs: Mapped[str | None] = mapped_column(Text)
    run_id: Mapped[str | None] = mapped_column(String(40))
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("site_id", "criterion_id", "run_id", name="uq_score_site_criterion_run"),
    )


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    verdict: Mapped[str] = mapped_column(ScreeningVerdict, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    threshold: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(Text)
    source_refs: Mapped[str | None] = mapped_column(Text)
    run_id: Mapped[str | None] = mapped_column(String(40))
    screened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="screening_results")

    __table_args__ = (
        UniqueConstraint(
            "site_id", "criterion_id", "run_id",
            name="uq_screening_site_criterion_run",
        ),
    )


class RankingResult(Base):
    __tablename__ = "ranking_results"

    ranking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    composite_score: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    per_criterion_scores: Mapped[dict | None] = mapped_column(JSONB)
    run_id: Mapped[str | None] = mapped_column(String(40))
    ranked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("site_id", "run_id", name="uq_ranking_site_run"),
    )


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flags"

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id")
    )
    dataset: Mapped[str] = mapped_column(String(120), nullable=False)
    dimension: Mapped[str] = mapped_column(String(60), nullable=False)
    level: Mapped[str] = mapped_column(QualityLevel, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    run_id: Mapped[str | None] = mapped_column(String(40))
    flagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="quality_flags")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    operation: Mapped[str] = mapped_column(String(30), nullable=False)
    table_name: Mapped[str] = mapped_column(String(60), nullable=False)
    site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    before_value: Mapped[dict | None] = mapped_column(JSONB)
    after_value: Mapped[dict | None] = mapped_column(JSONB)
    source_file: Mapped[str | None] = mapped_column(Text)
    source_row: Mapped[int | None] = mapped_column(Integer)
    run_id: Mapped[str | None] = mapped_column(String(40))
    message: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_audit_site_id", "site_id"),
        Index("ix_audit_run_id", "run_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )
