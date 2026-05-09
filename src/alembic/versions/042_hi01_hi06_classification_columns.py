# man_hours: 0.4
"""Add HI-01 airport class / runway / scheduled-service columns and HI-06
4-class military taxonomy + high-consequence distance columns.

These columns are populated by the SP-F connector refinements (OurAirports
runway-length parsing, OSM military classification). The migration is
purely additive (all columns nullable) so a delayed Alembic upgrade does
not break existing scoring runs — the connector code uses ``hasattr``
guards to gracefully degrade when the columns are absent.

Revision ID: 042
Revises: 041
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "042"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_airport_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_airport_runway_length_m", sa.Numeric(8, 1), nullable=True),
    )
    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_airport_scheduled_service", sa.Boolean, nullable=True),
    )

    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_military_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_high_consequence_military_km", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "site_human_hazards",
        sa.Column("nearest_high_consequence_military_class", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_human_hazards", "nearest_high_consequence_military_class")
    op.drop_column("site_human_hazards", "nearest_high_consequence_military_km")
    op.drop_column("site_human_hazards", "nearest_military_class")
    op.drop_column("site_human_hazards", "nearest_airport_scheduled_service")
    op.drop_column("site_human_hazards", "nearest_airport_runway_length_m")
    op.drop_column("site_human_hazards", "nearest_airport_class")
