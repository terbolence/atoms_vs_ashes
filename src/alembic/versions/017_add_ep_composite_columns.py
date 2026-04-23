"""Add DRV-02 EP composite derived-layer columns to site_emergency_planning.

New columns:
  ep01_evacuation_feasible (Boolean) — derived from composite score vs threshold.
  ep01_terrain_score (Numeric(5,1)) — terrain difficulty sub-score from DEM data.

Revision ID: 016
Revises: 015
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_emergency_planning",
        sa.Column("ep01_evacuation_feasible", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "site_emergency_planning",
        sa.Column("ep01_terrain_score", sa.Numeric(5, 1), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_emergency_planning", "ep01_terrain_score")
    op.drop_column("site_emergency_planning", "ep01_evacuation_feasible")
