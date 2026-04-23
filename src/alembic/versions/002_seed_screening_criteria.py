# man_hours: 1.5
"""Seed screening criteria — BF-01 Grid Capacity Basic Filter.

Revision ID: 002
Revises: 001
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CRITERIA = [
    {
        "criterion_id": "BF-01",
        "name": "Grid Capacity Basic Filter",
        "category": "basic_filter",
        "phase": "screening",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Checks whether site grid capacity (installed or grid-connected MW) "
            "can accommodate one or more reference SMR designs. Sites that cannot "
            "host any deployable SMR type (minimum 75 MWe for Oklo Aurora) are "
            "marked as fail."
        ),
    },
]


def upgrade() -> None:
    criteria = sa.table(
        "criteria",
        sa.column("criterion_id", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("phase", sa.String),
        sa.column("weight", sa.Numeric),
        sa.column("iaea_reference", sa.String),
        sa.column("epri_reference", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(criteria, CRITERIA)


def downgrade() -> None:
    op.execute("DELETE FROM criteria WHERE criterion_id = 'BF-01'")
