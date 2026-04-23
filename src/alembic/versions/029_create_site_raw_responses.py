"""Create site_raw_responses table for raw API response audit logging.

Stores the full raw HTTP response body (or raster extraction metadata) for
every per-site API call, keyed by (site_id, connector_slug, run_id).
Enables external audit and rapid repair of any DB column derivation errors.

Revision ID: 029
Revises: 028
Create Date: 2026-04-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_raw_responses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "site_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id"),
            nullable=False,
        ),
        sa.Column("connector_slug", sa.String(100), nullable=False),
        sa.Column("run_id", sa.String(60), nullable=True),
        sa.Column("request_url", sa.Text, nullable=True),
        sa.Column("request_params", JSONB, nullable=True),
        sa.Column("response_body", JSONB, nullable=True),
        sa.Column("response_text", sa.Text, nullable=True),
        sa.Column("response_headers", JSONB, nullable=True),
        sa.Column("http_status", sa.SmallInteger, nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_site_raw_responses_site_id",
        "site_raw_responses",
        ["site_id"],
    )
    op.create_index(
        "ix_site_raw_responses_connector",
        "site_raw_responses",
        ["connector_slug"],
    )
    op.create_unique_constraint(
        "uq_site_raw_responses_site_connector_run",
        "site_raw_responses",
        ["site_id", "connector_slug", "run_id"],
    )


def downgrade() -> None:
    op.drop_table("site_raw_responses")
