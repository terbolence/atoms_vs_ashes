"""Add JSONB columns for multi-connector evidence (S-06 GEE + others).

Stores parallel measurements and fusion metadata for NH-04, NH-13,
NS-04, NS-06, EP-03 without replacing the wide-column primary fields.

Revision ID: 026
Revises: 025
Create Date: 2026-04-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_column("site_emergency_planning", "ep03_multi_source_json")
    op.drop_column("site_infrastructure_v2", "ns06_multi_source_json")
    op.drop_column("site_infrastructure_v2", "ns04_multi_source_json")
    op.drop_column("site_natural_hazards", "nh13_multi_source_json")
    op.drop_column("site_natural_hazards", "nh04_multi_source_json")
