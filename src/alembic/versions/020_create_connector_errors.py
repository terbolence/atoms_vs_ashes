"""Create connector_errors table and migrate error observations.

Addresses audit findings W-06 and W-14: raw API error payloads and Python
stack traces were stored in site_observations alongside business data.
This migration creates a dedicated structured error table.

Revision ID: 020
Revises: 019
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "connector_errors",
        sa.Column(
            "error_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "run_id",
            sa.String(60),
            sa.ForeignKey("enrichment_runs.run_id"),
            nullable=True,
        ),
        sa.Column(
            "site_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id"),
            nullable=True,
        ),
        sa.Column("connector_slug", sa.String(100), nullable=False),
        sa.Column(
            "criterion_id",
            sa.String(10),
            sa.ForeignKey("criteria.criterion_id"),
            nullable=True,
        ),
        sa.Column("error_type", sa.String(50), nullable=True),
        sa.Column("http_status", sa.SmallInteger(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("raw_response", JSONB(), nullable=True),
        sa.Column("retryable", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_connector_errors_run_id", "connector_errors", ["run_id"])
    op.create_index("ix_connector_errors_site_id", "connector_errors", ["site_id"])
    op.create_index(
        "ix_connector_errors_connector", "connector_errors", ["connector_slug"]
    )


def downgrade() -> None:
    op.drop_index("ix_connector_errors_connector", table_name="connector_errors")
    op.drop_index("ix_connector_errors_site_id", table_name="connector_errors")
    op.drop_index("ix_connector_errors_run_id", table_name="connector_errors")
    op.drop_table("connector_errors")
