"""Add WDPA protected area columns to site_infrastructure_v2.

New columns for S-15 WDPA connector (NS-08):
  wdpa_nearest_distance_km, wdpa_overlap, wdpa_sensitivity_class,
  wdpa_result_json, wdpa_source, wdpa_quality, wdpa_comment.

Revision ID: 015
Revises: 014
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_nearest_distance_km", sa.Numeric(8, 3), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_overlap", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_sensitivity_class", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_result_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_source", sa.String(60), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_quality", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("wdpa_comment", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_infrastructure_v2", "wdpa_comment")
    op.drop_column("site_infrastructure_v2", "wdpa_quality")
    op.drop_column("site_infrastructure_v2", "wdpa_source")
    op.drop_column("site_infrastructure_v2", "wdpa_result_json")
    op.drop_column("site_infrastructure_v2", "wdpa_sensitivity_class")
    op.drop_column("site_infrastructure_v2", "wdpa_overlap")
    op.drop_column("site_infrastructure_v2", "wdpa_nearest_distance_km")
