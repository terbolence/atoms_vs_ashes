# man_hours: 1.0
"""Add site_units table and plant-level aggregate columns to sites.

Stores per-unit detail from the GEM tracker while the parent ``sites``
row carries aggregated totals (``unit_count``, ``operating_capacity_mw``).

Revision ID: 007
Revises: 006
Create Date: 2026-04-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sites", sa.Column("unit_count", sa.Integer()))
    op.add_column("sites", sa.Column("operating_capacity_mw", sa.Numeric(10, 2)))

    site_status_enum = postgresql.ENUM(
        "operating", "retired", "mothballed", "announced",
        "pre_permit", "permitted", "construction", "shelved",
        "cancelled", "planned_closure", "other",
        name="site_status", create_type=False,
    )

    op.create_table(
        "site_units",
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("gem_unit_phase_id", sa.String(30)),
        sa.Column("unit_name", sa.String(200)),
        sa.Column("capacity_mw", sa.Numeric(10, 2)),
        sa.Column("status", site_status_enum),
        sa.Column("start_year", sa.Integer()),
        sa.Column("retired_year", sa.Integer()),
        sa.Column("planned_retirement", sa.Date()),
        sa.Column("combustion_technology", sa.String(100)),
        sa.Column("coal_type", sa.String(100)),
        sa.Column("extended_data", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Index("ix_unit_site_id", "site_id"),
        sa.Index("ix_unit_gem_unit_phase_id", "gem_unit_phase_id"),
    )


def downgrade() -> None:
    op.drop_table("site_units")
    op.drop_column("sites", "operating_capacity_mw")
    op.drop_column("sites", "unit_count")
