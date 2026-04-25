# man_hours: 0.5
"""Failure / swing / correlation / country-balance tables for revision 034."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def _run_fk() -> sa.ForeignKey:
    return sa.ForeignKey("runs.run_id", ondelete="CASCADE")


def create_failure_outcomes() -> None:
    op.create_table(
        "failure_outcomes",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("smr_key", sa.String(30), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("bucket", sa.String(12), nullable=False),
        sa.Column("n_hard", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_floor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "n_distinct_failures", sa.Integer(),
            nullable=False, server_default="0"
        ),
        sa.Column(
            "hard_criteria", postgresql.ARRAY(sa.String()), nullable=True
        ),
        sa.Column(
            "floor_criteria", postgresql.ARRAY(sa.String()), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "site_id", "smr_key", name="pk_failure_outcomes",
        ),
        sa.CheckConstraint(
            "bucket IN ('survived', 'hard_only', 'floor_only', 'both')",
            name="ck_failure_outcomes_bucket",
        ),
    )
    op.create_index(
        "ix_failure_outcomes_country", "failure_outcomes",
        ["run_id", "country_code"],
    )


def create_failure_aggregates(axis_enum: sa.Enum) -> None:
    op.create_table(
        "failure_aggregates",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("axis", axis_enum, nullable=False),
        sa.Column("scope_smr_key", sa.String(30), nullable=True),
        sa.Column("key", sa.String(60), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "axis", "scope_smr_key", "key", "metric",
            name="pk_failure_aggregates",
        ),
    )


def create_swing_weights() -> None:
    op.create_table(
        "swing_weights",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "criterion_id", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column("family", sa.String(10), nullable=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("declared_weight", sa.Numeric(7, 6), nullable=True),
        sa.Column("observed_min", sa.Numeric(4, 1), nullable=True),
        sa.Column("observed_max", sa.Numeric(4, 1), nullable=True),
        sa.Column("observed_range", sa.Numeric(4, 1), nullable=True),
        sa.Column("swing_weight", sa.Numeric(7, 6), nullable=True),
        sa.Column("delta", sa.Numeric(7, 6), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "criterion_id", name="pk_swing_weights",
        ),
    )


def create_criterion_correlations() -> None:
    op.create_table(
        "criterion_correlations",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "criterion_a", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column(
            "criterion_b", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column("pearson", sa.Numeric(6, 4), nullable=True),
        sa.Column("spearman", sa.Numeric(6, 4), nullable=True),
        sa.Column("max_abs", sa.Numeric(6, 4), nullable=True),
        sa.Column("n_pairs", sa.Integer(), nullable=True),
        sa.Column(
            "flagged", sa.Boolean(),
            nullable=False, server_default=sa.text("false")
        ),
        sa.Column("threshold", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "criterion_a", "criterion_b",
            name="pk_criterion_correlations",
        ),
        sa.CheckConstraint(
            "criterion_a < criterion_b",
            name="ck_criterion_correlations_pair_order",
        ),
    )


def create_country_balance_check() -> None:
    op.create_table(
        "country_balance_check",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column(
            "baseline_count", sa.Integer(),
            nullable=False, server_default="0"
        ),
        sa.Column(
            "balanced_count", sa.Integer(),
            nullable=False, server_default="0"
        ),
        sa.Column("delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "triggered_floor_swap", sa.Boolean(),
            nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", name="pk_country_balance_check",
        ),
    )
