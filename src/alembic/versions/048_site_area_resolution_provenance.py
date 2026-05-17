# man_hours: 1.5
"""Add site-area resolution provenance columns.

Revision ID: 048
Revises: 047
Create Date: 2026-05-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "048"
down_revision: Union[str, None] = "047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sites", sa.Column("site_area_source", sa.String(length=40), nullable=True))
    op.add_column("sites", sa.Column("site_area_confidence", sa.String(length=20), nullable=True))
    op.add_column("sites", sa.Column("site_area_review_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("sites", sa.Column("site_area_candidates_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("sites", sa.Column("expansion_potential_ha", sa.Numeric(10, 2), nullable=True))
    op.add_column("sites", sa.Column("site_area_resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sites", sa.Column("site_area_resolve_run_id", sa.String(length=60), nullable=True))


def downgrade() -> None:
    op.drop_column("sites", "site_area_resolve_run_id")
    op.drop_column("sites", "site_area_resolved_at")
    op.drop_column("sites", "expansion_potential_ha")
    op.drop_column("sites", "site_area_candidates_json")
    op.drop_column("sites", "site_area_review_flags")
    op.drop_column("sites", "site_area_confidence")
    op.drop_column("sites", "site_area_source")
