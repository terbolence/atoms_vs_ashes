"""Add Natura 2000 proximity columns to site_infrastructure_v2.

New columns for S-14 Natura 2000 WFS connector (NS-08):
  n2k_nearest_distance_km, n2k_overlap, n2k_sensitivity_class,
  n2k_result_json, ns08_source.

Revision ID: 014
Revises: 013
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("n2k_nearest_distance_km", sa.Numeric(8, 3), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("n2k_overlap", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("n2k_sensitivity_class", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("n2k_result_json", JSONB(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns08_source", sa.String(60), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_infrastructure_v2", "ns08_source")
    op.drop_column("site_infrastructure_v2", "n2k_result_json")
    op.drop_column("site_infrastructure_v2", "n2k_sensitivity_class")
    op.drop_column("site_infrastructure_v2", "n2k_overlap")
    op.drop_column("site_infrastructure_v2", "n2k_nearest_distance_km")
