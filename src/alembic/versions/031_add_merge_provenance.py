"""Phase 2: add per-row merge provenance + merge_audit table.

Used only by the ``atoms_vs_ashes_merged`` database (Step 2.4 / Phase 2).
Applying the migration to ``atoms_vs_ashes`` is harmless — every column
defaults to ``api`` and the ``merge_audit`` table simply stays empty.

Provenance design
-----------------

Each domain row gets two new columns:

* ``source_db`` (``api`` | ``llm`` | ``merged``) — the database the
  current scalar values came from.  Phase 2 stamps every row with
  ``api``; Phase 5 promotes a subset to ``llm`` or ``merged`` per
  ``business_logic.md``.
* ``merge_run_id`` — the run id that last touched the row (parallels
  ``run_id`` on the same tables).

A separate ``merge_audit`` table records every change applied during
merging / LLM enrichment, keyed by site + criterion + column.

Revision ID: 031
Revises: 030
Create Date: 2026-04-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROVENANCE_TABLES = (
    "sites",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
)


def upgrade() -> None:
    for tbl in PROVENANCE_TABLES:
        op.add_column(
            tbl,
            sa.Column(
                "source_db",
                sa.String(20),
                nullable=False,
                server_default="api",
            ),
        )
        op.add_column(
            tbl,
            sa.Column("merge_run_id", sa.String(60), nullable=True),
        )
        op.create_check_constraint(
            f"ck_{tbl}_source_db",
            tbl,
            "source_db IN ('api', 'llm', 'merged')",
        )
        op.create_index(
            f"ix_{tbl}_source_db",
            tbl,
            ["source_db"],
        )

    op.create_table(
        "merge_audit",
        sa.Column(
            "audit_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "merge_run_id",
            sa.String(60),
            nullable=False,
        ),
        sa.Column(
            "site_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id"),
            nullable=False,
        ),
        sa.Column("criterion_id", sa.String(10), nullable=True),
        sa.Column("table_name", sa.String(60), nullable=False),
        sa.Column("column_name", sa.String(60), nullable=False),
        sa.Column("source_chosen", sa.String(20), nullable=False),
        sa.Column("api_value", JSONB(), nullable=True),
        sa.Column("llm_value", JSONB(), nullable=True),
        sa.Column("final_value", JSONB(), nullable=True),
        sa.Column("rule_id", sa.String(60), nullable=True),
        sa.Column("rule_explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "source_chosen IN ('api', 'llm', 'merged', 'rejected')",
            name="ck_merge_audit_source_chosen",
        ),
    )
    op.create_index("ix_merge_audit_site_id", "merge_audit", ["site_id"])
    op.create_index("ix_merge_audit_run_id", "merge_audit", ["merge_run_id"])
    op.create_index(
        "ix_merge_audit_criterion", "merge_audit", ["criterion_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_merge_audit_criterion", table_name="merge_audit")
    op.drop_index("ix_merge_audit_run_id", table_name="merge_audit")
    op.drop_index("ix_merge_audit_site_id", table_name="merge_audit")
    op.drop_table("merge_audit")

    for tbl in PROVENANCE_TABLES:
        op.drop_index(f"ix_{tbl}_source_db", table_name=tbl)
        op.drop_constraint(f"ck_{tbl}_source_db", tbl, type_="check")
        op.drop_column(tbl, "merge_run_id")
        op.drop_column(tbl, "source_db")
