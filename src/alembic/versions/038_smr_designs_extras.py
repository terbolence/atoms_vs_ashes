# man_hours: 1.0
"""Add optional SMR design columns; correct NuScale VOYGR-6 land / export figures.

Revision ID: 038
Revises: 037
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "038"
down_revision: Union[str, None] = "037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "smr_designs",
        sa.Column("exclusion_zone_radius_m", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "smr_designs",
        sa.Column("cooling_water_demand_m3_per_h", sa.Numeric(14, 3), nullable=True),
    )
    op.add_column("smr_designs", sa.Column("notes", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE smr_designs SET capacity_mwe = 462, land_requirement_ha = 50 "
            "WHERE smr_key = 'nuscale_voygr6'"
        )
    )


def downgrade() -> None:
    op.drop_column("smr_designs", "notes")
    op.drop_column("smr_designs", "cooling_water_demand_m3_per_h")
    op.drop_column("smr_designs", "exclusion_zone_radius_m")
