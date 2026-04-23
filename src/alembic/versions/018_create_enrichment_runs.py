"""Create enrichment_runs table for run-level metadata.

Addresses audit finding W-01: run_id was an orphan string with no join
target. This table stores metadata for every enrichment, screening,
scoring, and LLM batch run.

Revision ID: 018
Revises: 017
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "enrichment_runs",
        sa.Column("run_id", sa.String(60), primary_key=True),
        sa.Column("run_type", sa.String(30), nullable=False),
        sa.Column("connector_slug", sa.String(100), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="completed",
        ),
        sa.Column("site_count", sa.Integer(), nullable=True),
        sa.Column("success_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_enrichment_runs_type", "enrichment_runs", ["run_type"])
    op.create_index(
        "ix_enrichment_runs_connector", "enrichment_runs", ["connector_slug"]
    )


def downgrade() -> None:
    op.drop_index("ix_enrichment_runs_connector", table_name="enrichment_runs")
    op.drop_index("ix_enrichment_runs_type", table_name="enrichment_runs")
    op.drop_table("enrichment_runs")
