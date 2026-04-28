# man_hours: 0.25
"""Add NH-05 nearest mine distance.

Revision ID: 041
Revises: 040
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041"
down_revision: Union[str, None] = "040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_natural_hazards",
        sa.Column("mining_void_distance_km", sa.Numeric(8, 3), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_natural_hazards", "mining_void_distance_km")
