# man_hours: 0.9
"""National sensitivity analytics tables for Alembic revision 046."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def _run_fk() -> sa.ForeignKey:
    return sa.ForeignKey("runs.run_id", ondelete="CASCADE")


def create_national_rank_sensitivity() -> None:
    op.create_table(
        "national_rank_sensitivity",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("smr_key", sa.String(30), nullable=False),
        sa.Column("weight_profile", sa.String(30), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("baseline_national_rank", sa.Integer(), nullable=True),
        sa.Column("scenario_national_rank", sa.Integer(), nullable=True),
        sa.Column("rank_delta", sa.Integer(), nullable=True),
        sa.Column("baseline_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("scenario_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("score_delta", sa.Numeric(7, 4), nullable=True),
        sa.Column("scenario_family", sa.String(30), nullable=True),
        sa.Column("eligible_pair_count", sa.Integer(), nullable=False),
        sa.Column("small_n_flag", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "weight_profile", "site_id",
            name="pk_national_rank_sensitivity",
        ),
    )
    op.create_index(
        "ix_national_rank_sensitivity_slice",
        "national_rank_sensitivity",
        ["run_id", "country_code", "smr_key", "weight_profile"],
    )


def create_national_sensitivity_summary() -> None:
    op.create_table(
        "national_sensitivity_summary",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("smr_key", sa.String(30), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("weight_profile", sa.String(30), nullable=False),
        sa.Column("criterion_id", sa.String(10), nullable=False),
        sa.Column("family", sa.String(30), nullable=False),
        sa.Column("n_pairs", sa.Integer(), nullable=False),
        sa.Column("mean_abs_rank_delta", sa.Numeric(8, 4), nullable=True),
        sa.Column("max_abs_rank_delta", sa.Numeric(8, 4), nullable=True),
        sa.Column("spearman_rho", sa.Numeric(6, 4), nullable=True),
        sa.Column("top1_changed", sa.Boolean(), nullable=True),
        sa.Column("top3_jaccard", sa.Numeric(6, 4), nullable=True),
        sa.Column("top5_jaccard", sa.Numeric(6, 4), nullable=True),
        sa.Column("small_n_flag", sa.Boolean(), nullable=False),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "metric",
            "weight_profile", "criterion_id", "family",
            name="pk_national_sensitivity_summary",
        ),
    )
    op.create_index(
        "ix_national_sensitivity_summary_slice",
        "national_sensitivity_summary",
        ["run_id", "country_code", "smr_key", "metric"],
    )


def create_national_mc_rank_distribution() -> None:
    op.create_table(
        "national_mc_rank_distribution",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("smr_key", sa.String(30), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("iterations", sa.Integer(), nullable=False),
        sa.Column("p_rank_1", sa.Numeric(6, 4), nullable=True),
        sa.Column("p_rank_le_3", sa.Numeric(6, 4), nullable=True),
        sa.Column("p_rank_le_5", sa.Numeric(6, 4), nullable=True),
        sa.Column("median_rank", sa.Numeric(8, 3), nullable=True),
        sa.Column("p05_rank", sa.Numeric(8, 3), nullable=True),
        sa.Column("p95_rank", sa.Numeric(8, 3), nullable=True),
        sa.Column("rank_iqr", sa.Numeric(8, 3), nullable=True),
        sa.Column("eligible_pair_count", sa.Integer(), nullable=False),
        sa.Column("small_n_flag", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "site_id",
            name="pk_national_mc_rank_distribution",
        ),
    )
    op.create_index(
        "ix_national_mc_rank_distribution_slice",
        "national_mc_rank_distribution",
        ["run_id", "country_code", "smr_key"],
    )
