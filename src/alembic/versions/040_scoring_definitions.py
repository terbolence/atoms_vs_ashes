# man_hours: 1.0
"""Create DB-backed scoring definition tables.

Revision ID: 040
Revises: 039
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "040"
down_revision: Union[str, None] = "039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "scoring_definition_state",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scoring_criteria",
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("family", sa.String(10), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phases", jsonb, nullable=False),
        sa.Column("weight_factor", sa.Integer(), nullable=False),
        sa.Column("normalised_weight_pct", sa.Numeric(6, 3), nullable=False),
        sa.Column("primary_metric", sa.String(120), nullable=True),
        sa.Column("band_kind", sa.String(40), nullable=True),
        sa.Column("db_fields", jsonb, nullable=True),
        sa.Column("aggregation", jsonb, nullable=True),
        sa.Column("quality_floor", jsonb, nullable=True),
        sa.Column("template_json", jsonb, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("criterion_id"),
    )
    op.create_index("ix_scoring_criteria_family", "scoring_criteria", ["family"])
    op.create_table(
        "scoring_fail_conditions",
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("condition_expr", sa.Text(), nullable=False),
        sa.Column("descriptor", sa.Text(), nullable=True),
        sa.Column("pass_mark", sa.Numeric(4, 2), nullable=True),
        sa.Column("threshold", jsonb, nullable=True),
        sa.Column("threshold_affects_expr", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["scoring_criteria.criterion_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("criterion_id", "code"),
    )
    op.create_table(
        "scoring_bands",
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("score_low", sa.Numeric(4, 2), nullable=False),
        sa.Column("score_high", sa.Numeric(4, 2), nullable=False),
        sa.Column("condition_expr", sa.Text(), nullable=False),
        sa.Column("descriptor", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["criterion_id"], ["scoring_criteria.criterion_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("criterion_id", "ordinal"),
    )
    op.create_table(
        "scoring_sub_scores",
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("weight", sa.Numeric(6, 4), nullable=True),
        sa.Column("primary_metric", sa.String(120), nullable=True),
        sa.Column("bands_json", jsonb, nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["scoring_criteria.criterion_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("criterion_id", "key"),
    )
    op.create_table(
        "scoring_band_recipes",
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("fail_code", sa.String(40), nullable=False),
        sa.Column("metric", sa.String(120), nullable=True),
        sa.Column("elevation_pass_m", sa.Numeric(8, 3), nullable=True),
        sa.ForeignKeyConstraint(["criterion_id"], ["scoring_criteria.criterion_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("criterion_id"),
    )
    op.create_table(
        "compiled_scoring_snapshots",
        sa.Column("snapshot_id", sa.String(80), nullable=False),
        sa.Column("compiled_sha256", sa.String(64), nullable=False),
        sa.Column("definition_revision", sa.Integer(), nullable=False),
        sa.Column("threshold_overrides", jsonb, nullable=False),
        sa.Column("bundles_by_smr", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_table(
        "scoring_run_snapshots",
        sa.Column("run_id", sa.String(60), nullable=False),
        sa.Column("snapshot_id", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["compiled_scoring_snapshots.snapshot_id"]),
        sa.PrimaryKeyConstraint("run_id"),
    )


def downgrade() -> None:
    op.drop_table("scoring_run_snapshots")
    op.drop_table("compiled_scoring_snapshots")
    op.drop_table("scoring_band_recipes")
    op.drop_table("scoring_sub_scores")
    op.drop_table("scoring_bands")
    op.drop_table("scoring_fail_conditions")
    op.drop_index("ix_scoring_criteria_family", table_name="scoring_criteria")
    op.drop_table("scoring_criteria")
    op.drop_table("scoring_definition_state")
