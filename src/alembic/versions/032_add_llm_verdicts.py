"""Phase 5: add LLM-promoted verdicts and observations to the merged DB.

Used only by the ``atoms_vs_ashes_merged`` database (Step 2.4 / Phase 5
of the data-fusion plan).  Applying the migration to ``atoms_vs_ashes``
or ``atoms_vs_ashes_llm`` is harmless — both tables simply stay empty
on those databases.

Tables added
------------

* ``site_llm_verdicts`` — one row per ``(site_id, criterion_id,
  prompt_key)`` carrying the consensus LLM verdict promoted from
  ``atoms_vs_ashes_llm.screening_verdicts`` per the rule documented in
  ``audit/post_processing/02_data_verification/20260421_llm_field_promotion_proposal.md``
  § 2.1 (worst-case-with-fail-override across the 8 SMR designs).
* ``site_llm_observations`` — promoted rows from
  ``atoms_vs_ashes_llm.site_observations`` filtered to ``source_type
  IN ('llm', 'web_search')`` (the ``llm_error_migrated`` rows are
  already mirrored into the API DB by migration 020).

Both tables carry ``source_db`` / ``merge_run_id`` provenance columns
in line with migration 031.

Revision ID: 032
Revises: 031
Create Date: 2026-04-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM, UUID

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The ``screening_verdict`` ENUM type already exists in every DB
    # that has ``screening_verdicts`` (created by migration 003).  We
    # just *reference* it here rather than re-creating it.
    verdict_enum = ENUM(
        "pass", "fail", "inconclusive", "caution", "not_assessed", "deferred",
        name="screening_verdict",
        create_type=False,
    )

    op.create_table(
        "site_llm_verdicts",
        sa.Column(
            "llm_verdict_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "site_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            sa.String(10),
            sa.ForeignKey("criteria.criterion_id"),
            nullable=False,
        ),
        sa.Column("prompt_key", sa.String(10), nullable=False),
        sa.Column("llm_verdict", verdict_enum, nullable=False),
        sa.Column("llm_verdict_confidence", sa.String(20), nullable=False),
        sa.Column("llm_verdict_run_id", sa.String(40), nullable=True),
        sa.Column("llm_verdict_smr_key", sa.String(30), nullable=True),
        sa.Column("smr_consensus_count", sa.SmallInteger(), nullable=True),
        sa.Column("smr_disagreement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("llm_justification", sa.Text(), nullable=True),
        sa.Column("llm_sources_needed", sa.Text(), nullable=True),
        sa.Column(
            "source_db",
            sa.String(20),
            nullable=False,
            server_default="llm",
        ),
        sa.Column("merge_run_id", sa.String(60), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "source_db IN ('api', 'llm', 'merged')",
            name="ck_site_llm_verdicts_source_db",
        ),
        sa.UniqueConstraint(
            "site_id", "criterion_id", "prompt_key",
            name="uq_llm_verdict_site_criterion_prompt",
        ),
    )
    op.create_index(
        "ix_llm_verdicts_site", "site_llm_verdicts", ["site_id"]
    )
    op.create_index(
        "ix_llm_verdicts_criterion", "site_llm_verdicts", ["criterion_id"]
    )
    op.create_index(
        "ix_llm_verdicts_run_id", "site_llm_verdicts", ["merge_run_id"]
    )

    op.create_table(
        "site_llm_observations",
        sa.Column(
            "observation_id",
            UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "site_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            sa.String(10),
            sa.ForeignKey("criteria.criterion_id"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("impact", sa.String(20), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=True),
        sa.Column("llm_run_id", sa.String(40), nullable=True),
        sa.Column(
            "source_db",
            sa.String(20),
            nullable=False,
            server_default="llm",
        ),
        sa.Column("merge_run_id", sa.String(60), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "source_type IN ('llm', 'web_search')",
            name="ck_site_llm_observations_source_type",
        ),
        sa.CheckConstraint(
            "source_db IN ('api', 'llm', 'merged')",
            name="ck_site_llm_observations_source_db",
        ),
    )
    op.create_index(
        "ix_llm_observations_site", "site_llm_observations", ["site_id"]
    )
    op.create_index(
        "ix_llm_observations_criterion",
        "site_llm_observations",
        ["criterion_id"],
    )
    op.create_index(
        "ix_llm_observations_run_id",
        "site_llm_observations",
        ["merge_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_llm_observations_run_id", table_name="site_llm_observations"
    )
    op.drop_index(
        "ix_llm_observations_criterion", table_name="site_llm_observations"
    )
    op.drop_index(
        "ix_llm_observations_site", table_name="site_llm_observations"
    )
    op.drop_table("site_llm_observations")

    op.drop_index("ix_llm_verdicts_run_id", table_name="site_llm_verdicts")
    op.drop_index("ix_llm_verdicts_criterion", table_name="site_llm_verdicts")
    op.drop_index("ix_llm_verdicts_site", table_name="site_llm_verdicts")
    op.drop_table("site_llm_verdicts")
