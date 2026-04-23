# man_hours: 10.0
"""Initial schema — all core, reference, and audit tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- Enums (create_type=False because we create them explicitly) ----------
    plant_type = postgresql.ENUM(
        "coal", "lignite", "gas", "thermal", "other",
        name="plant_type", create_type=False,
    )
    plant_type.create(op.get_bind(), checkfirst=True)

    site_status = postgresql.ENUM(
        "operating", "retired", "mothballed", "announced",
        "pre_permit", "permitted", "construction", "shelved",
        "cancelled", "planned_closure", "other",
        name="site_status", create_type=False,
    )
    site_status.create(op.get_bind(), checkfirst=True)

    screening_verdict = postgresql.ENUM(
        "pass", "fail", "inconclusive",
        name="screening_verdict", create_type=False,
    )
    screening_verdict.create(op.get_bind(), checkfirst=True)

    quality_level = postgresql.ENUM(
        "high", "medium", "low", "insufficient",
        name="quality_level", create_type=False,
    )
    quality_level.create(op.get_bind(), checkfirst=True)

    # --- Reference tables -----------------------------------------------------
    op.create_table(
        "countries",
        sa.Column("country_code", sa.String(2), primary_key=True),
        sa.Column("country_name", sa.String(120), nullable=False),
        sa.Column("region", sa.String(60)),
        sa.Column("nuclear_policy_notes", sa.Text()),
    )

    op.create_table(
        "data_sources",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("url", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("last_fetched", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "criteria",
        sa.Column("criterion_id", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("weight", sa.Numeric(5, 4)),
        sa.Column("iaea_reference", sa.String(200)),
        sa.Column("epri_reference", sa.String(200)),
        sa.Column("description", sa.Text()),
    )

    # --- Core tables ----------------------------------------------------------
    op.create_table(
        "sites",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("alternative_names", postgresql.ARRAY(sa.String())),
        sa.Column("country_code", sa.String(2),
                   sa.ForeignKey("countries.country_code"), nullable=False),
        sa.Column("country_name", sa.String(120), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("geom", geoalchemy2.Geometry("POINT", srid=4326)),
        sa.Column("location_accuracy", sa.String(30)),
        sa.Column("local_area", sa.String(200)),
        sa.Column("subnational_unit", sa.String(200)),
        sa.Column("region", sa.String(60)),
        sa.Column("plant_type", plant_type),
        sa.Column("installed_capacity_mw", sa.Numeric(10, 2)),
        sa.Column("status", site_status),
        sa.Column("start_year", sa.Integer()),
        sa.Column("retired_year", sa.Integer()),
        sa.Column("planned_retirement", sa.Date()),
        sa.Column("coal_phaseout_year", sa.Integer()),
        sa.Column("grid_voltage_kv", sa.Integer()),
        sa.Column("grid_capacity_mw", sa.Numeric(10, 2)),
        sa.Column("cooling_water_source", sa.String(200)),
        sa.Column("site_area_ha", sa.Numeric(10, 2)),
        sa.Column("elevation_m", sa.Numeric(8, 2)),
        sa.Column("owner_operator", sa.Text()),
        sa.Column("parent_company", sa.Text()),
        sa.Column("combustion_technology", sa.String(100)),
        sa.Column("coal_type", sa.String(100)),
        sa.Column("coal_source", sa.Text()),
        sa.Column("net_zero_year", sa.Integer()),
        sa.Column("location", sa.Text()),
        sa.Column("permits", sa.Text()),
        sa.Column("permit_date", sa.Date()),
        sa.Column("owner_gem_id", sa.Text()),
        sa.Column("parent_gem_id", sa.Text()),
        sa.Column("gem_unit_phase_id", sa.String(30)),
        sa.Column("gem_location_id", sa.String(30)),
        sa.Column("wiki_url", sa.Text()),
        sa.Column("extended_data", postgresql.JSONB()),
        sa.Column("last_verified", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
    )
    op.create_index("ix_sites_gem_location_id", "sites", ["gem_location_id"])
    op.create_index("ix_sites_gem_unit_phase_id", "sites", ["gem_unit_phase_id"])
    op.create_index("ix_sites_country_code", "sites", ["country_code"])
    op.create_index("ix_sites_geom", "sites", ["geom"], postgresql_using="gist")

    # --- Ownership ------------------------------------------------------------
    op.create_table(
        "site_ownership",
        sa.Column("ownership_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("parent_gem_entity_id", sa.String(30)),
        sa.Column("parent_name", sa.Text()),
        sa.Column("parent_reg_country", sa.String(120)),
        sa.Column("parent_hq_country", sa.String(120)),
        sa.Column("project", sa.Text()),
        sa.Column("share_pct", sa.Numeric(7, 4)),
        sa.Column("ownership_path", sa.Text()),
        sa.Column("immediate_owner", sa.Text()),
        sa.Column("immediate_owner_gem_id", sa.String(30)),
        sa.Column("tracker", sa.String(100)),
        sa.Column("status", sa.String(40)),
        sa.Column("capacity_mw", sa.Numeric(10, 2)),
        sa.Column("gem_location_id", sa.String(30)),
        sa.Column("gem_unit_id", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
    )
    op.create_index("ix_ownership_site_id", "site_ownership", ["site_id"])
    op.create_index("ix_ownership_gem_location_id", "site_ownership", ["gem_location_id"])

    op.create_table(
        "_staging_unmatched_ownership",
        sa.Column("row_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
    )

    # --- Attributes, Infrastructure, Scores -----------------------------------
    op.create_table(
        "site_attributes",
        sa.Column("attribute_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10),
                   sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("value_numeric", sa.Numeric()),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_json", postgresql.JSONB()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("data_sources.source_id")),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("run_id", sa.String(40)),
        sa.Column("cache_status", sa.String(20)),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id",
                            name="uq_site_criterion_run"),
    )
    op.create_index("ix_attr_site_id", "site_attributes", ["site_id"])

    op.create_table(
        "site_infrastructure",
        sa.Column("infra_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False, unique=True),
        sa.Column("grid_voltage_kv", sa.Integer()),
        sa.Column("grid_capacity_mw", sa.Numeric(10, 2)),
        sa.Column("substation_distance_km", sa.Numeric(8, 2)),
        sa.Column("cooling_source_type", sa.String(60)),
        sa.Column("cooling_source_name", sa.String(200)),
        sa.Column("cooling_distance_km", sa.Numeric(8, 2)),
        sa.Column("transport_road", sa.Boolean()),
        sa.Column("transport_rail", sa.Boolean()),
        sa.Column("transport_waterway", sa.Boolean()),
        sa.Column("notes", sa.Text()),
    )

    op.create_table(
        "site_scores",
        sa.Column("score_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10),
                   sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("justification", sa.Text()),
        sa.Column("source_refs", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("scored_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id",
                            name="uq_score_site_criterion_run"),
    )

    # --- Screening & Ranking --------------------------------------------------
    op.create_table(
        "screening_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10),
                   sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("verdict", screening_verdict, nullable=False),
        sa.Column("value", sa.Text()),
        sa.Column("threshold", sa.Text()),
        sa.Column("justification", sa.Text()),
        sa.Column("source_refs", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("screened_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id",
                            name="uq_screening_site_criterion_run"),
    )

    op.create_table(
        "ranking_results",
        sa.Column("ranking_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("composite_score", sa.Numeric(7, 4), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("per_criterion_scores", postgresql.JSONB()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("ranked_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "run_id", name="uq_ranking_site_run"),
    )

    # --- Quality & Audit ------------------------------------------------------
    op.create_table(
        "data_quality_flags",
        sa.Column("flag_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("sites.site_id")),
        sa.Column("dataset", sa.String(120), nullable=False),
        sa.Column("dimension", sa.String(60), nullable=False),
        sa.Column("level", quality_level, nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("flagged_at", sa.DateTime(timezone=True),
                   server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_log",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True),
                   server_default=sa.text("now()"), nullable=False),
        sa.Column("operation", sa.String(30), nullable=False),
        sa.Column("table_name", sa.String(60), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True)),
        sa.Column("before_value", postgresql.JSONB()),
        sa.Column("after_value", postgresql.JSONB()),
        sa.Column("source_file", sa.Text()),
        sa.Column("source_row", sa.Integer()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("message", sa.Text()),
    )
    op.create_index("ix_audit_site_id", "audit_log", ["site_id"])
    op.create_index("ix_audit_run_id", "audit_log", ["run_id"])
    op.create_index("ix_audit_timestamp", "audit_log", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("data_quality_flags")
    op.drop_table("ranking_results")
    op.drop_table("screening_results")
    op.drop_table("site_scores")
    op.drop_table("site_infrastructure")
    op.drop_table("site_attributes")
    op.drop_table("_staging_unmatched_ownership")
    op.drop_table("site_ownership")
    op.drop_table("sites")
    op.drop_table("criteria")
    op.drop_table("data_sources")
    op.drop_table("countries")

    op.execute("DROP TYPE IF EXISTS quality_level")
    op.execute("DROP TYPE IF EXISTS screening_verdict")
    op.execute("DROP TYPE IF EXISTS site_status")
    op.execute("DROP TYPE IF EXISTS plant_type")
