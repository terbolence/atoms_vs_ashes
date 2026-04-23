"""Add hydrology / water stress columns to site_infrastructure_v2.

New columns for S-29/S-30/S-33 hydrology stack (NS-01):
  water_stress_score, water_stress_label, ns01_source.

Revision ID: 016
Revises: 015
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("water_stress_score", sa.Numeric(5, 3), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("water_stress_label", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("ns01_source", sa.String(60), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_infrastructure_v2", "ns01_source")
    op.drop_column("site_infrastructure_v2", "water_stress_label")
    op.drop_column("site_infrastructure_v2", "water_stress_score")
