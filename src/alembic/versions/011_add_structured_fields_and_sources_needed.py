"""Add missing structured fields and sources_needed column.

Adds karst_severity, karst_formation_type, collapse_mechanism,
landslide_inventory_notes to site_natural_hazards, and sources_needed
to screening_verdicts for tracking data gaps per assessment.

Revision ID: 011
Revises: 010
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_natural_hazards",
        sa.Column("karst_severity", sa.String(30), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("karst_formation_type", sa.String(100), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("collapse_mechanism", sa.String(100), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("landslide_inventory_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "screening_verdicts",
        sa.Column("sources_needed", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("screening_verdicts", "sources_needed")
    op.drop_column("site_natural_hazards", "landslide_inventory_notes")
    op.drop_column("site_natural_hazards", "collapse_mechanism")
    op.drop_column("site_natural_hazards", "karst_formation_type")
    op.drop_column("site_natural_hazards", "karst_severity")
