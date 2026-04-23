# man_hours: 16.0
"""SQLAlchemy ORM models — mirrors architecture/specs/02_data_model_postgres.md."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
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

VerdictEnum = Enum(
    "pass", "fail", "inconclusive", "caution", "not_assessed", "deferred",
    name="screening_verdict",
    create_constraint=True,
)


# ---------------------------------------------------------------------------
# Operational tables
# ---------------------------------------------------------------------------

class EnrichmentRun(Base):
    """Run-level metadata for enrichment, screening, scoring, and LLM batches."""

    __tablename__ = "enrichment_runs"

    run_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    run_type: Mapped[str] = mapped_column(String(30), nullable=False)
    connector_slug: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )
    site_count: Mapped[int | None] = mapped_column(Integer)
    success_count: Mapped[int | None] = mapped_column(Integer)
    error_count: Mapped[int | None] = mapped_column(Integer)
    config_hash: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_enrichment_runs_type", "run_type"),
        Index("ix_enrichment_runs_connector", "connector_slug"),
    )


class ConnectorError(Base):
    """Structured error log for connector / API / LLM failures."""

    __tablename__ = "connector_errors"

    error_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    run_id: Mapped[str | None] = mapped_column(
        String(60), ForeignKey("enrichment_runs.run_id")
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id")
    )
    connector_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    criterion_id: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id")
    )
    error_type: Mapped[str | None] = mapped_column(String(50))
    http_status: Mapped[int | None] = mapped_column(SmallInteger)
    message: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    retryable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_connector_errors_run_id", "run_id"),
        Index("ix_connector_errors_site_id", "site_id"),
        Index("ix_connector_errors_connector", "connector_slug"),
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
    criterion_class: Mapped[str | None] = mapped_column(String(30))
    threshold_expression: Mapped[str | None] = mapped_column(Text)
    units: Mapped[str | None] = mapped_column(String(30))
    value_type: Mapped[str | None] = mapped_column(String(20))
    domain_table: Mapped[str | None] = mapped_column(String(50))
    domain_column_prefix: Mapped[str | None] = mapped_column(String(20))
    source_priority: Mapped[dict | None] = mapped_column(JSONB)


class SmrDesign(Base):
    __tablename__ = "smr_designs"

    smr_key: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    capacity_mwe: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    thermal_output_mwt: Mapped[float | None] = mapped_column(Numeric(10, 2))
    land_requirement_ha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    epz_radius_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    module_weight_t: Mapped[float | None] = mapped_column(Numeric(10, 2))
    cooling_type: Mapped[str | None] = mapped_column(String(60))
    design_life_yr: Mapped[int | None] = mapped_column(Integer)
    regulatory_status: Mapped[str | None] = mapped_column(String(200))


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

    unit_count: Mapped[int | None] = mapped_column(Integer)
    operating_capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))

    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    ownership_records = relationship("SiteOwnership", back_populates="site")
    units = relationship("SiteUnit", back_populates="site", order_by="SiteUnit.unit_name")
    natural_hazards = relationship("SiteNaturalHazards", back_populates="site", uselist=False)
    human_hazards = relationship("SiteHumanHazards", back_populates="site", uselist=False)
    radiological = relationship("SiteRadiological", back_populates="site", uselist=False)
    emergency_planning = relationship("SiteEmergencyPlanning", back_populates="site", uselist=False)
    infrastructure = relationship("SiteInfrastructureV2", back_populates="site", uselist=False)
    screening_verdicts = relationship("ScreeningVerdict", back_populates="site")
    ranking_scores = relationship("RankingScore", back_populates="site")
    composite_rankings = relationship("CompositeRanking", back_populates="site")
    observations = relationship("SiteObservation", back_populates="site")

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


class SiteUnit(Base):
    """Individual generating unit within a plant site.

    One ``Site`` (keyed by ``gem_location_id``) may have many units.
    The parent ``Site`` carries aggregated totals; this table preserves
    per-unit detail from the GEM Coal Plant Tracker.
    """

    __tablename__ = "site_units"

    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    gem_unit_phase_id: Mapped[str | None] = mapped_column(String(30))
    unit_name: Mapped[str | None] = mapped_column(String(200))
    capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str | None] = mapped_column(SiteStatus)
    start_year: Mapped[int | None] = mapped_column(Integer)
    retired_year: Mapped[int | None] = mapped_column(Integer)
    planned_retirement: Mapped[date | None] = mapped_column(Date)
    combustion_technology: Mapped[str | None] = mapped_column(String(100))
    coal_type: Mapped[str | None] = mapped_column(String(100))
    extended_data: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="units")

    __table_args__ = (
        Index("ix_unit_site_id", "site_id"),
        Index("ix_unit_gem_unit_phase_id", "gem_unit_phase_id"),
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


# ---------------------------------------------------------------------------
# Domain measurement tables (one row per site, explicit typed columns)
# ---------------------------------------------------------------------------

class SiteNaturalHazards(Base):
    """NH-01 through NH-14: all natural hazard metrics for a site."""

    __tablename__ = "site_natural_hazards"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), primary_key=True
    )
    # NH-01: Seismic ground motion
    pga_475yr_g: Mapped[float | None] = mapped_column(Numeric(8, 5))
    pga_2475yr_g: Mapped[float | None] = mapped_column(Numeric(8, 5))
    spectral_accel_json: Mapped[dict | None] = mapped_column(JSONB)
    nh01_source: Mapped[str | None] = mapped_column(String(200))
    nh01_quality: Mapped[str | None] = mapped_column(String(20))
    nh01_comment: Mapped[str | None] = mapped_column(Text)
    # NH-02: Surface rupture
    nearest_fault_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    fault_name: Mapped[str | None] = mapped_column(String(200))
    fault_slip_rate_mm_yr: Mapped[float | None] = mapped_column(Numeric(8, 3))
    nh02_source: Mapped[str | None] = mapped_column(String(200))
    nh02_quality: Mapped[str | None] = mapped_column(String(20))
    nh02_comment: Mapped[str | None] = mapped_column(Text)
    # NH-03: Liquefaction
    liquefaction_suscept: Mapped[str | None] = mapped_column(String(30))
    soil_type: Mapped[str | None] = mapped_column(String(100))
    groundwater_depth_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    # nh03_source: provenance tag (zhu_global_1km / egdi_lithology / soilgrids).
    # nh03_quality: evidence-confidence enum (high|medium|low|no_data).
    nh03_source: Mapped[str | None] = mapped_column(String(40))
    nh03_quality: Mapped[str | None] = mapped_column(String(20))
    nh03_comment: Mapped[str | None] = mapped_column(Text)
    # NH-04: Slope stability
    # slope_angle_deg: fused/primary value from CopernicusDemConnector
    slope_angle_deg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    slope_stability_class: Mapped[str | None] = mapped_column(String(30))
    landslide_inventory_notes: Mapped[str | None] = mapped_column(Text)
    nh04_quality: Mapped[str | None] = mapped_column(String(20))
    nh04_comment: Mapped[str | None] = mapped_column(Text)
    # nh04_dem_cog_*: from CopernicusDemConnector (Cloud-Optimized GeoTIFF)
    nh04_dem_cog_slope_max_deg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    # nh04_gee_*: from EarthEngineConnector (Google Earth Engine SRTM/ALOS)
    nh04_gee_slope_max_deg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    nh04_gee_slope_mean_deg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    nh04_gee_terrain_class: Mapped[str | None] = mapped_column(String(30))
    # Discrepancy between CopDEM and GEE slope values
    nh04_slope_discrepancy: Mapped[str | None] = mapped_column(String(20))
    nh04_slope_fusion_method: Mapped[str | None] = mapped_column(String(120))
    nh04_cross_source_summary: Mapped[str | None] = mapped_column(Text)
    # NH-05: Karst
    karst_present: Mapped[bool | None] = mapped_column(Boolean)
    karst_severity: Mapped[str | None] = mapped_column(String(30))
    karst_formation_type: Mapped[str | None] = mapped_column(String(200))
    nh05_quality: Mapped[str | None] = mapped_column(String(20))
    nh05_comment: Mapped[str | None] = mapped_column(Text)
    # NH-05b: Subsidence & Collapse (split from NH-05 karst)
    mining_void_present: Mapped[bool | None] = mapped_column(Boolean)
    subsidence_risk_class: Mapped[str | None] = mapped_column(String(30))
    collapse_mechanism: Mapped[str | None] = mapped_column(String(500))
    nh05b_quality: Mapped[str | None] = mapped_column(String(20))
    nh05b_comment: Mapped[str | None] = mapped_column(Text)
    # NH-06: Foundation (ranking)
    bearing_capacity_kpa: Mapped[float | None] = mapped_column(Numeric(10, 2))
    depth_to_bedrock_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nh06_quality: Mapped[str | None] = mapped_column(String(20))
    nh06_comment: Mapped[str | None] = mapped_column(Text)
    # NH-07: Volcanism
    nearest_holocene_volcano_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    volcano_name: Mapped[str | None] = mapped_column(String(200))
    nh07_hazard_class: Mapped[str | None] = mapped_column(String(30))
    nh07_quality: Mapped[str | None] = mapped_column(String(20))
    nh07_comment: Mapped[str | None] = mapped_column(Text)
    # NH-08: Coastal flooding
    distance_to_coast_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    storm_surge_risk: Mapped[str | None] = mapped_column(String(30))
    tsunami_risk: Mapped[str | None] = mapped_column(String(30))
    nh08_quality: Mapped[str | None] = mapped_column(String(20))
    nh08_comment: Mapped[str | None] = mapped_column(Text)
    # NH-09: River flooding
    flood_zone_class: Mapped[str | None] = mapped_column(String(30))
    nearest_river_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    dam_break_exposure: Mapped[bool | None] = mapped_column(Boolean)
    nh09_quality: Mapped[str | None] = mapped_column(String(20))
    nh09_comment: Mapped[str | None] = mapped_column(Text)
    # NH-10: Extreme winds (ranking)
    max_wind_speed_ms: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nh10_quality: Mapped[str | None] = mapped_column(String(20))
    nh10_comment: Mapped[str | None] = mapped_column(Text)
    # NH-11: Extreme precipitation (ranking)
    # extreme_precip_mm = max DAILY precipitation (mm).
    # mean_annual_precip_mm = climatological mean annual total (mm/year),
    # populated from ERA5 (see copernicus_era5 connector).
    extreme_precip_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    mean_annual_precip_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nh11_quality: Mapped[str | None] = mapped_column(String(20))
    nh11_comment: Mapped[str | None] = mapped_column(Text)
    # NH-12: Extreme temperatures (ranking)
    extreme_temp_max_c: Mapped[float | None] = mapped_column(Numeric(6, 2))
    extreme_temp_min_c: Mapped[float | None] = mapped_column(Numeric(6, 2))
    nh12_quality: Mapped[str | None] = mapped_column(String(20))
    nh12_comment: Mapped[str | None] = mapped_column(Text)
    # NH-13: Forest/wildfire (ranking)
    # wildfire_*: from CorineConnector (fragmentation proxy)
    wildfire_combustible_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    wildfire_wui_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    nh13_quality: Mapped[str | None] = mapped_column(String(20))
    nh13_comment: Mapped[str | None] = mapped_column(Text)
    # nh13_gee_*: from EarthEngineConnector (MODIS burn-area product)
    nh13_gee_modis_burn_months: Mapped[int | None] = mapped_column(Integer)
    nh13_gee_fire_recurrence_class: Mapped[str | None] = mapped_column(String(20))
    nh13_gee_burn_fraction_mean: Mapped[float | None] = mapped_column(Numeric(8, 4))
    nh13_cross_source_summary: Mapped[str | None] = mapped_column(Text)
    # NH-14: Combined hazards (ranking)
    combined_hazard_notes: Mapped[str | None] = mapped_column(Text)
    nh14_quality: Mapped[str | None] = mapped_column(String(20))
    nh14_comment: Mapped[str | None] = mapped_column(Text)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    site = relationship("Site", back_populates="natural_hazards")


class SiteHumanHazards(Base):
    """HI-01 through HI-08: human-induced hazard metrics for a site."""

    __tablename__ = "site_human_hazards"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), primary_key=True
    )
    # HI-01: Aviation (OurAirportsConnector; search radius: 50 km)
    nearest_airport_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_airport_name: Mapped[str | None] = mapped_column(String(200))
    nearest_airport_type: Mapped[str | None] = mapped_column(String(30))
    flight_path_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    airport_count: Mapped[int | None] = mapped_column(Integer)
    hi01_quality: Mapped[str | None] = mapped_column(String(20))
    hi01_comment: Mapped[str | None] = mapped_column(Text)
    # HI-02: Industrial explosions
    nearest_seveso_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_industrial_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    hi02_quality: Mapped[str | None] = mapped_column(String(20))
    hi02_comment: Mapped[str | None] = mapped_column(Text)
    # HI-03: Toxic releases
    nearest_toxic_source_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    hi03_quality: Mapped[str | None] = mapped_column(String(20))
    hi03_comment: Mapped[str | None] = mapped_column(Text)
    # HI-04: External fires
    nearest_flammable_storage_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_pipeline_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    hi04_quality: Mapped[str | None] = mapped_column(String(20))
    hi04_comment: Mapped[str | None] = mapped_column(Text)
    # HI-05: Transport hazards (ranking)
    hazmat_route_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    hi05_quality: Mapped[str | None] = mapped_column(String(20))
    hi05_comment: Mapped[str | None] = mapped_column(Text)
    # HI-06: Military installations (OSM military=*; search radius: 30 km)
    nearest_military_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_military_name: Mapped[str | None] = mapped_column(String(200))
    military_count: Mapped[int | None] = mapped_column(Integer)
    hi06_quality: Mapped[str | None] = mapped_column(String(20))
    hi06_comment: Mapped[str | None] = mapped_column(Text)
    # HI-07: Electromagnetic interference (search radius: 20 km)
    nearest_transmitter_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    transmitter_type: Mapped[str | None] = mapped_column(String(60))
    transmitter_count: Mapped[int | None] = mapped_column(Integer)
    hi07_quality: Mapped[str | None] = mapped_column(String(20))
    hi07_comment: Mapped[str | None] = mapped_column(Text)
    # HI-08: Other nuclear installations
    nearest_nuclear_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_nuclear_name: Mapped[str | None] = mapped_column(String(200))
    hi08_quality: Mapped[str | None] = mapped_column(String(20))
    hi08_comment: Mapped[str | None] = mapped_column(Text)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    site = relationship("Site", back_populates="human_hazards")


class SiteRadiological(Base):
    """RI-01 through RI-06: radiological impact metrics for a site."""

    __tablename__ = "site_radiological"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), primary_key=True
    )
    # RI-04: Population density at EPZ radii (screening)
    pop_density_5km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pop_density_16km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pop_density_25km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pop_density_80km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pop_total_5km: Mapped[int | None] = mapped_column(Integer)
    pop_total_16km: Mapped[int | None] = mapped_column(Integer)
    pop_total_25km: Mapped[int | None] = mapped_column(Integer)
    pop_total_80km: Mapped[int | None] = mapped_column(Integer)
    ri04_quality: Mapped[str | None] = mapped_column(String(20))
    ri04_comment: Mapped[str | None] = mapped_column(Text)
    # RI-05: Distance to population centres (ranking)
    nearest_city_50k_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_city_name: Mapped[str | None] = mapped_column(String(200))
    nearest_city_pop: Mapped[int | None] = mapped_column(Integer)
    ri05_quality: Mapped[str | None] = mapped_column(String(20))
    ri05_comment: Mapped[str | None] = mapped_column(Text)
    # RI-06: Population projections (ranking)
    pop_growth_rate_pct: Mapped[float | None] = mapped_column(Numeric(6, 3))
    projected_pop_25km_60yr: Mapped[int | None] = mapped_column(Integer)
    ri06_quality: Mapped[str | None] = mapped_column(String(20))
    ri06_comment: Mapped[str | None] = mapped_column(Text)
    # RI-01: Atmospheric dispersion (ranking)
    prevailing_wind_dir: Mapped[str | None] = mapped_column(String(10))
    avg_wind_speed_ms: Mapped[float | None] = mapped_column(Numeric(6, 2))
    mixing_height_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    ri01_quality: Mapped[str | None] = mapped_column(String(20))
    ri01_comment: Mapped[str | None] = mapped_column(Text)
    # RI-02: Surface water dispersion (ranking)
    nearest_river_flow_m3s: Mapped[float | None] = mapped_column(Numeric(12, 2))
    ri02_quality: Mapped[str | None] = mapped_column(String(20))
    ri02_comment: Mapped[str | None] = mapped_column(Text)
    # RI-03: Groundwater dispersion (ranking)
    aquifer_type: Mapped[str | None] = mapped_column(String(60))
    groundwater_flow_dir: Mapped[str | None] = mapped_column(String(30))
    ri03_quality: Mapped[str | None] = mapped_column(String(20))
    ri03_comment: Mapped[str | None] = mapped_column(Text)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    site = relationship("Site", back_populates="radiological")


class SiteEmergencyPlanning(Base):
    """EP-01 through EP-05: emergency planning metrics for a site."""

    __tablename__ = "site_emergency_planning"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), primary_key=True
    )
    # EP-01: Emergency plan feasibility (composite)
    ep01_composite_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_road_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_special_pop_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_geography_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_population_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_terrain_score: Mapped[float | None] = mapped_column(Numeric(5, 1))
    ep01_evacuation_feasible: Mapped[bool | None] = mapped_column(Boolean)
    ep01_quality: Mapped[str | None] = mapped_column(String(20))
    ep01_comment: Mapped[str | None] = mapped_column(Text)
    # EP-02: Evacuation routes (ranking)
    road_density_km_per_km2: Mapped[float | None] = mapped_column(Numeric(8, 3))
    total_road_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    has_motorway_access: Mapped[bool | None] = mapped_column(Boolean)
    ep02_quality: Mapped[str | None] = mapped_column(String(20))
    ep02_comment: Mapped[str | None] = mapped_column(Text)
    # EP-03: Physical geography constraints (ranking)
    # major_river_barrier, waterway_count_epz: from OverpassClient (OSM waterways)
    major_river_barrier: Mapped[bool | None] = mapped_column(Boolean)
    waterway_count_epz: Mapped[int | None] = mapped_column(Integer)
    ep03_quality: Mapped[str | None] = mapped_column(String(20))
    ep03_comment: Mapped[str | None] = mapped_column(Text)
    # ep03_gee_*: from EarthEngineConnector; relief = elevation range within 16 km
    ep03_gee_relief_16km_m: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ep03_gee_mountain_barrier_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    ep03_cross_source_summary: Mapped[str | None] = mapped_column(Text)
    # EP-04: Special populations (ranking)
    hospital_count_epz: Mapped[int | None] = mapped_column(Integer)
    prison_count_epz: Mapped[int | None] = mapped_column(Integer)
    care_home_count_epz: Mapped[int | None] = mapped_column(Integer)
    ep04_quality: Mapped[str | None] = mapped_column(String(20))
    ep04_comment: Mapped[str | None] = mapped_column(Text)
    # EP-05: Concurrent hazard impact (ranking)
    concurrent_hazard_notes: Mapped[str | None] = mapped_column(Text)
    ep05_quality: Mapped[str | None] = mapped_column(String(20))
    ep05_comment: Mapped[str | None] = mapped_column(Text)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    site = relationship("Site", back_populates="emergency_planning")


class SiteInfrastructureV2(Base):
    """NS-01 through NS-13: non-safety / infrastructure metrics for a site."""

    __tablename__ = "site_infrastructure_v2"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), primary_key=True
    )
    # NS-01: Cooling water
    cooling_source_type: Mapped[str | None] = mapped_column(String(60))
    cooling_source_name: Mapped[str | None] = mapped_column(String(200))
    # cooling_source_hyriv_id: HydroRIVERS reach id retained even when the
    # human-readable river name has been resolved into cooling_source_name.
    cooling_source_hyriv_id: Mapped[int | None] = mapped_column(BigInteger)
    cooling_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    cooling_flow_m3s: Mapped[float | None] = mapped_column(Numeric(12, 2))
    water_stress_score: Mapped[float | None] = mapped_column(Numeric(5, 3))
    water_stress_label: Mapped[str | None] = mapped_column(String(30))
    ns01_source: Mapped[str | None] = mapped_column(String(60))
    ns01_quality: Mapped[str | None] = mapped_column(String(20))
    ns01_comment: Mapped[str | None] = mapped_column(Text)
    # NS-02: Grid connection (EntsoEConnector + OverpassClient; search radius: 50 km)
    nearest_substation_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    substation_name: Mapped[str | None] = mapped_column(String(200))
    nearest_hv_line_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    hv_line_voltage_kv: Mapped[int | None] = mapped_column(Integer)
    hv_line_count: Mapped[int | None] = mapped_column(Integer)
    substation_count: Mapped[int | None] = mapped_column(Integer)
    grid_export_capacity_mw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ns02_quality: Mapped[str | None] = mapped_column(String(20))
    ns02_comment: Mapped[str | None] = mapped_column(Text)
    # NS-03: Transport access
    nearest_highway_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_rail_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    nearest_waterway_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    heavy_haul_capable: Mapped[bool | None] = mapped_column(Boolean)
    ns03_quality: Mapped[str | None] = mapped_column(String(20))
    ns03_comment: Mapped[str | None] = mapped_column(Text)
    # NS-04: Site topography
    # dominant_*/favourable_*/moderate_*/unfavourable_*: from CorineConnector + WorldCoverConnector
    dominant_land_class: Mapped[str | None] = mapped_column(String(30))
    dominant_class_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    favourable_land_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    moderate_land_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    unfavourable_land_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # favourable_area_ha: derived hectare value. See
    # docs/post_processing/data_curation_methodology.md for the algorithm.
    favourable_area_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    favourable_area_method: Mapped[str | None] = mapped_column(String(40))
    ns04_quality: Mapped[str | None] = mapped_column(String(20))
    ns04_comment: Mapped[str | None] = mapped_column(Text)
    # ns04_gee_*: from EarthEngineConnector; grading_class = terrain grading difficulty
    ns04_gee_terrain_class: Mapped[str | None] = mapped_column(String(30))
    ns04_gee_relief_range_m: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ns04_gee_grading_class: Mapped[str | None] = mapped_column(String(30))
    ns04_cross_source_summary: Mapped[str | None] = mapped_column(Text)
    # NS-05: Land availability / site footprint
    buildable_area_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    largest_contiguous_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    patch_count: Mapped[int | None] = mapped_column(Integer)
    ns05_quality: Mapped[str | None] = mapped_column(String(20))
    ns05_comment: Mapped[str | None] = mapped_column(Text)
    # NS-06: Existing infrastructure (ranking)
    reusable_infra_score: Mapped[int | None] = mapped_column(SmallInteger)
    ns06_quality: Mapped[str | None] = mapped_column(String(20))
    ns06_comment: Mapped[str | None] = mapped_column(Text)
    # ns06_gee_*: from EarthEngineConnector; demolition_class = whether existing
    # structures need demolition for site reuse (none/partial/full)
    ns06_gee_built_fraction: Mapped[float | None] = mapped_column(Numeric(5, 4))
    ns06_gee_demolition_class: Mapped[str | None] = mapped_column(String(20))
    ns06_cross_source_summary: Mapped[str | None] = mapped_column(Text)
    # NS-07: Environmental impact non-rad (screening)
    env_impact_notes: Mapped[str | None] = mapped_column(Text)
    ns07_quality: Mapped[str | None] = mapped_column(String(20))
    ns07_comment: Mapped[str | None] = mapped_column(Text)
    # NS-08: Ecological sensitivity (CORINE fragmentation)
    ecological_natural_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ecological_patch_count: Mapped[int | None] = mapped_column(Integer)
    ecological_largest_patch_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    # NS-08: Natura 2000 proximity (Natura2000Connector; "n2k" = Natura 2000 network)
    n2k_nearest_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 3))
    n2k_overlap: Mapped[bool | None] = mapped_column(Boolean)
    n2k_sensitivity_class: Mapped[str | None] = mapped_column(String(20))
    n2k_result_json: Mapped[dict | None] = mapped_column(JSONB)
    ns08_source: Mapped[str | None] = mapped_column(String(60))
    ns08_quality: Mapped[str | None] = mapped_column(String(20))
    ns08_comment: Mapped[str | None] = mapped_column(Text)
    # NS-08: WDPA protected areas (WdpaConnector; "wdpa" = World Database on Protected Areas)
    wdpa_nearest_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 3))
    wdpa_overlap: Mapped[bool | None] = mapped_column(Boolean)
    wdpa_sensitivity_class: Mapped[str | None] = mapped_column(String(20))
    wdpa_result_json: Mapped[dict | None] = mapped_column(JSONB)
    wdpa_source: Mapped[str | None] = mapped_column(String(60))
    wdpa_quality: Mapped[str | None] = mapped_column(String(20))
    wdpa_comment: Mapped[str | None] = mapped_column(Text)
    # NS-09: Socioeconomic impact (ranking)
    ns09_quality: Mapped[str | None] = mapped_column(String(20))
    ns09_comment: Mapped[str | None] = mapped_column(Text)
    # NS-10: Workforce availability (ranking)
    ns10_quality: Mapped[str | None] = mapped_column(String(20))
    ns10_comment: Mapped[str | None] = mapped_column(Text)
    # NS-11: Coal-to-nuclear synergies (ranking)
    ns11_quality: Mapped[str | None] = mapped_column(String(20))
    ns11_comment: Mapped[str | None] = mapped_column(Text)
    # NS-12: Regulatory/political environment (ranking)
    ns12_quality: Mapped[str | None] = mapped_column(String(20))
    ns12_comment: Mapped[str | None] = mapped_column(Text)
    # NS-13: Construction logistics (ranking)
    laydown_suitable_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    laydown_largest_patch_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ns13_quality: Mapped[str | None] = mapped_column(String(20))
    ns13_comment: Mapped[str | None] = mapped_column(Text)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_id: Mapped[str | None] = mapped_column(String(40))
    # Provenance for the merged DB (Step 2.4 / Phase 2). Default 'api'.
    source_db: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="api"
    )
    merge_run_id: Mapped[str | None] = mapped_column(String(60))

    site = relationship("Site", back_populates="infrastructure")


# ---------------------------------------------------------------------------
# Decision tables (per-site, per-SMR-design)
# ---------------------------------------------------------------------------

class ScreeningVerdict(Base):
    """Pass/fail verdicts from screening phases, per site per SMR design."""

    __tablename__ = "screening_verdicts"

    verdict_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    smr_key: Mapped[str] = mapped_column(
        String(30), ForeignKey("smr_designs.smr_key"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt_key: Mapped[str | None] = mapped_column(String(10))
    verdict: Mapped[str] = mapped_column(VerdictEnum, nullable=False)
    measured_value: Mapped[str | None] = mapped_column(Text)
    threshold: Mapped[str | None] = mapped_column(Text)
    measured_value_numeric: Mapped[float | None] = mapped_column(Numeric)
    threshold_numeric: Mapped[float | None] = mapped_column(Numeric)
    measured_units: Mapped[str | None] = mapped_column(String(20))
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    data_sources: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    sources_needed: Mapped[str | None] = mapped_column(Text)
    run_id: Mapped[str | None] = mapped_column(String(40))
    screened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="screening_verdicts")

    __table_args__ = (
        UniqueConstraint(
            "site_id", "smr_key", "criterion_id", "prompt_key", "run_id",
            name="uq_verdict_site_smr_criterion_prompt_run",
        ),
        Index("ix_verdict_site_id", "site_id"),
    )


class RankingScore(Base):
    """0–10 native ranking scores per site per SMR design per criterion.

    Migrated from the legacy 1–5 SMALLINT columns in Alembic revision
    ``033_scoring_0_10``.  ``score_0_10`` is the canonical score;
    ``score_low_0_10`` / ``score_high_0_10`` bracket the Monte-Carlo
    uncertainty band.  ``weight_factor`` and ``weight_normalised``
    snapshot the master weight table at scoring time so downstream
    exports do not have to re-join.
    """

    __tablename__ = "ranking_scores"

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    smr_key: Mapped[str] = mapped_column(
        String(30), ForeignKey("smr_designs.smr_key"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    score_0_10: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    score_low_0_10: Mapped[float | None] = mapped_column(Numeric(3, 1))
    score_high_0_10: Mapped[float | None] = mapped_column(Numeric(3, 1))
    weight_factor: Mapped[int | None] = mapped_column(SmallInteger)
    weight_normalised: Mapped[float | None] = mapped_column(Numeric(5, 4))
    quality_flag: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    data_sources: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    run_id: Mapped[str | None] = mapped_column(String(40))
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="ranking_scores")

    __table_args__ = (
        CheckConstraint(
            "score_0_10 BETWEEN 0 AND 10",
            name="ck_ranking_score_0_10_range",
        ),
        CheckConstraint(
            "score_low_0_10 IS NULL OR score_low_0_10 BETWEEN 0 AND 10",
            name="ck_ranking_score_low_0_10_range",
        ),
        CheckConstraint(
            "score_high_0_10 IS NULL OR score_high_0_10 BETWEEN 0 AND 10",
            name="ck_ranking_score_high_0_10_range",
        ),
        CheckConstraint(
            "weight_factor IS NULL OR weight_factor BETWEEN 1 AND 10",
            name="ck_ranking_weight_factor_range",
        ),
        CheckConstraint(
            "weight_normalised IS NULL OR (weight_normalised >= 0 AND weight_normalised <= 1)",
            name="ck_ranking_weight_normalised_range",
        ),
        UniqueConstraint(
            "site_id", "smr_key", "criterion_id", "run_id",
            name="uq_ranking_site_smr_criterion_run",
        ),
    )


class CompositeRanking(Base):
    """Final weighted composite score and rank per site per SMR design.

    Scores are on the 0–10 scale.  ``composite_score_low`` /
    ``composite_score_high`` carry Monte-Carlo bounds when produced by
    the sensitivity suite; ``weight_profile`` labels baseline vs.
    sensitivity rows (``baseline``, ``w_plus_20``, ``w_minus_20``,
    ``mc_1000`` …).  See Alembic revision ``033_scoring_0_10``.
    """

    __tablename__ = "composite_rankings"

    ranking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    smr_key: Mapped[str] = mapped_column(
        String(30), ForeignKey("smr_designs.smr_key"), nullable=False
    )
    composite_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    composite_score_low: Mapped[float | None] = mapped_column(Numeric(6, 3))
    composite_score_high: Mapped[float | None] = mapped_column(Numeric(6, 3))
    weight_profile: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="baseline"
    )
    rank_position: Mapped[int | None] = mapped_column(Integer)
    passed_exclusionary: Mapped[bool] = mapped_column(Boolean, nullable=False)
    passed_avoidance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    criteria_coverage: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_confidence: Mapped[str | None] = mapped_column(String(20))
    sensitivity_stable: Mapped[bool | None] = mapped_column(Boolean)
    per_category_scores: Mapped[dict | None] = mapped_column(JSONB)
    run_id: Mapped[str | None] = mapped_column(String(40))
    ranked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="composite_rankings")

    __table_args__ = (
        UniqueConstraint(
            "site_id", "smr_key", "run_id", "weight_profile",
            name="uq_composite_site_smr_run_profile",
        ),
        Index("ix_composite_weight_profile", "weight_profile"),
    )


# ---------------------------------------------------------------------------
# Observations / comments
# ---------------------------------------------------------------------------

class SiteObservation(Base):
    """Structured comments and annotations per site per criterion."""

    __tablename__ = "site_observations"

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    smr_key: Mapped[str | None] = mapped_column(
        String(30), ForeignKey("smr_designs.smr_key")
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    observation_class: Mapped[str | None] = mapped_column(String(30))
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[str | None] = mapped_column(String(20))
    author: Mapped[str | None] = mapped_column(String(100))
    run_id: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    site = relationship("Site", back_populates="observations")

    __table_args__ = (
        Index("ix_obs_site_id", "site_id"),
        Index("ix_obs_criterion_id", "criterion_id"),
    )


# ---------------------------------------------------------------------------
# Raw API response archive (for external audit & data repair)
# ---------------------------------------------------------------------------

class SiteRawResponse(Base):
    """Per-site, per-connector raw API response for audit and data repair.

    For JSON APIs the body goes into ``response_body`` (JSONB).
    For non-JSON responses (XML, binary raster metadata) use ``response_text``.
    """

    __tablename__ = "site_raw_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    connector_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(60))
    request_url: Mapped[str | None] = mapped_column(Text)
    request_params: Mapped[dict | None] = mapped_column(JSONB)
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    response_text: Mapped[str | None] = mapped_column(Text)
    response_headers: Mapped[dict | None] = mapped_column(JSONB)
    http_status: Mapped[int | None] = mapped_column(SmallInteger)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "site_id", "connector_slug", "run_id",
            name="uq_site_raw_responses_site_connector_run",
        ),
        Index("ix_site_raw_responses_site_id", "site_id"),
        Index("ix_site_raw_responses_connector", "connector_slug"),
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Merge provenance (Step 2.4 / Phase 2 — atoms_vs_ashes_merged)
# ---------------------------------------------------------------------------

class MergeAudit(Base):
    """One row per scalar value that the merger / LLM-enrichment pipeline
    chose for the merged DB.  See ``audit/post_processing/02_data_verification``.
    """

    __tablename__ = "merge_audit"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    merge_run_id: Mapped[str] = mapped_column(String(60), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str | None] = mapped_column(String(10))
    table_name: Mapped[str] = mapped_column(String(60), nullable=False)
    column_name: Mapped[str] = mapped_column(String(60), nullable=False)
    source_chosen: Mapped[str] = mapped_column(String(20), nullable=False)
    api_value: Mapped[dict | None] = mapped_column(JSONB)
    llm_value: Mapped[dict | None] = mapped_column(JSONB)
    final_value: Mapped[dict | None] = mapped_column(JSONB)
    rule_id: Mapped[str | None] = mapped_column(String(60))
    rule_explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "source_chosen IN ('api', 'llm', 'merged', 'rejected')",
            name="ck_merge_audit_source_chosen",
        ),
        Index("ix_merge_audit_site_id", "site_id"),
        Index("ix_merge_audit_run_id", "merge_run_id"),
        Index("ix_merge_audit_criterion", "criterion_id"),
    )


class SiteLlmVerdict(Base):
    """Phase-5 promotion of LLM ``screening_verdicts`` into the merged DB.

    One row per ``(site_id, criterion_id, prompt_key)`` carrying the
    consensus verdict across the 8 SMR designs (worst-case-with-fail
    override -- see ``20260421_llm_field_promotion_proposal.md`` § 2.1).
    """

    __tablename__ = "site_llm_verdicts"

    llm_verdict_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    prompt_key: Mapped[str] = mapped_column(String(10), nullable=False)
    llm_verdict: Mapped[str] = mapped_column(VerdictEnum, nullable=False)
    llm_verdict_confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    llm_verdict_run_id: Mapped[str | None] = mapped_column(String(40))
    llm_verdict_smr_key: Mapped[str | None] = mapped_column(String(30))
    smr_consensus_count: Mapped[int | None] = mapped_column(SmallInteger)
    smr_disagreement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_justification: Mapped[str | None] = mapped_column(Text)
    llm_sources_needed: Mapped[str | None] = mapped_column(Text)
    source_db: Mapped[str] = mapped_column(String(20), nullable=False, default="llm")
    merge_run_id: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "source_db IN ('api', 'llm', 'merged')",
            name="ck_site_llm_verdicts_source_db",
        ),
        UniqueConstraint(
            "site_id", "criterion_id", "prompt_key",
            name="uq_llm_verdict_site_criterion_prompt",
        ),
        Index("ix_llm_verdicts_site", "site_id"),
        Index("ix_llm_verdicts_criterion", "criterion_id"),
        Index("ix_llm_verdicts_run_id", "merge_run_id"),
    )


class SiteLlmObservation(Base):
    """Phase-5 promotion of LLM-authored ``site_observations`` into the merged DB.

    Excludes ``llm_error_migrated`` rows (those are already mirrored
    into the API DB by migration 020).
    """

    __tablename__ = "site_llm_observations"

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False
    )
    criterion_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("criteria.criterion_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[str | None] = mapped_column(String(20))
    llm_run_id: Mapped[str | None] = mapped_column(String(40))
    source_db: Mapped[str] = mapped_column(String(20), nullable=False, default="llm")
    merge_run_id: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('llm', 'web_search')",
            name="ck_site_llm_observations_source_type",
        ),
        CheckConstraint(
            "source_db IN ('api', 'llm', 'merged')",
            name="ck_site_llm_observations_source_db",
        ),
        Index("ix_llm_observations_site", "site_id"),
        Index("ix_llm_observations_criterion", "criterion_id"),
        Index("ix_llm_observations_run_id", "merge_run_id"),
    )


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
