"""Replace multi-source JSONB with Excel-friendly typed + Text columns.

Drops ``*_multi_source_json`` from revision 026 and adds flat columns for
S-06 GEE cross-checks so exports (e.g. XLSX) show human-readable values.

Revision ID: 027
Revises: 026
Create Date: 2026-04-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("site_emergency_planning", "ep03_multi_source_json")
    op.drop_column("site_infrastructure_v2", "ns06_multi_source_json")
    op.drop_column("site_infrastructure_v2", "ns04_multi_source_json")
    op.drop_column("site_natural_hazards", "nh13_multi_source_json")
    op.drop_column("site_natural_hazards", "nh04_multi_source_json")

    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_dem_cog_slope_max_deg", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_gee_slope_max_deg", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_gee_slope_mean_deg", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_gee_terrain_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_slope_discrepancy", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_slope_fusion_method", sa.String(120), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_cross_source_summary", sa.Text(), nullable=True),
    )

    op.add_column(
        "site_natural_hazards",
        sa.Column("nh13_gee_modis_burn_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh13_gee_fire_recurrence_class", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh13_gee_burn_fraction_mean", sa.Numeric(8, 4), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh13_cross_source_summary", sa.Text(), nullable=True),
    )

    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns04_gee_terrain_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns04_gee_relief_range_m", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns04_gee_grading_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns04_cross_source_summary", sa.Text(), nullable=True),
    )

    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns06_gee_built_fraction", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns06_gee_demolition_class", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns06_cross_source_summary", sa.Text(), nullable=True),
    )

    op.add_column(
        "site_emergency_planning",
        sa.Column("ep03_gee_relief_16km_m", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "site_emergency_planning",
        sa.Column("ep03_gee_mountain_barrier_score", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "site_emergency_planning",
        sa.Column("ep03_cross_source_summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_emergency_planning", "ep03_cross_source_summary")
    op.drop_column("site_emergency_planning", "ep03_gee_mountain_barrier_score")
    op.drop_column("site_emergency_planning", "ep03_gee_relief_16km_m")

    op.drop_column("site_infrastructure_v2", "ns06_cross_source_summary")
    op.drop_column("site_infrastructure_v2", "ns06_gee_demolition_class")
    op.drop_column("site_infrastructure_v2", "ns06_gee_built_fraction")

    op.drop_column("site_infrastructure_v2", "ns04_cross_source_summary")
    op.drop_column("site_infrastructure_v2", "ns04_gee_grading_class")
    op.drop_column("site_infrastructure_v2", "ns04_gee_relief_range_m")
    op.drop_column("site_infrastructure_v2", "ns04_gee_terrain_class")

    op.drop_column("site_natural_hazards", "nh13_cross_source_summary")
    op.drop_column("site_natural_hazards", "nh13_gee_burn_fraction_mean")
    op.drop_column("site_natural_hazards", "nh13_gee_fire_recurrence_class")
    op.drop_column("site_natural_hazards", "nh13_gee_modis_burn_months")

    op.drop_column("site_natural_hazards", "nh04_cross_source_summary")
    op.drop_column("site_natural_hazards", "nh04_slope_fusion_method")
    op.drop_column("site_natural_hazards", "nh04_slope_discrepancy")
    op.drop_column("site_natural_hazards", "nh04_gee_terrain_class")
    op.drop_column("site_natural_hazards", "nh04_gee_slope_mean_deg")
    op.drop_column("site_natural_hazards", "nh04_gee_slope_max_deg")
    op.drop_column("site_natural_hazards", "nh04_dem_cog_slope_max_deg")

    op.add_column(
        "site_natural_hazards",
        sa.Column("nh04_multi_source_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh13_multi_source_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns04_multi_source_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns06_multi_source_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_emergency_planning",
        sa.Column("ep03_multi_source_json", JSONB(), nullable=True),
    )
