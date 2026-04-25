# man_hours: 0.5
"""Country / OAT / weight-stability / threshold tables for revision 034."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def _run_fk() -> sa.ForeignKey:
    return sa.ForeignKey("runs.run_id", ondelete="CASCADE")


def create_country_rankings_summary() -> None:
    op.create_table(
        "country_rankings_summary",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("smr_key", sa.String(30), nullable=True),
        sa.Column("n_sites", sa.Integer(), nullable=False),
        sa.Column("k_value", sa.Integer(), nullable=False),
        sa.Column("scenarios_compared", sa.Integer(), nullable=False),
        sa.Column(
            "mean_jaccard_vs_baseline_topk", sa.Numeric(5, 4), nullable=True
        ),
        sa.Column(
            "min_jaccard_vs_baseline_topk", sa.Numeric(5, 4), nullable=True
        ),
        sa.Column("band_a_count", sa.Integer(), nullable=True),
        sa.Column("band_b_count", sa.Integer(), nullable=True),
        sa.Column("band_c_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key",
            name="pk_country_rankings_summary",
        ),
    )


def create_country_site_rankings() -> None:
    op.create_table(
        "country_site_rankings",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("smr_key", sa.String(30), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("national_rank", sa.Integer(), nullable=True),
        sa.Column("regional_rank", sa.Integer(), nullable=True),
        sa.Column("composite_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("composite_score_low", sa.Numeric(6, 3), nullable=True),
        sa.Column("composite_score_high", sa.Numeric(6, 3), nullable=True),
        sa.Column("band", sa.String(1), nullable=True),
        sa.Column("pairwise_winrate_top5", sa.Numeric(4, 3), nullable=True),
        sa.Column("p_rank_le_k", sa.Numeric(4, 3), nullable=True),
        sa.Column("acceptability_flag", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "country_code", "smr_key", "site_id",
            name="pk_country_site_rankings",
        ),
    )


def create_oat_importance() -> None:
    op.create_table(
        "oat_importance",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "criterion_id", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column("family", sa.String(10), nullable=True),
        sa.Column("criterion_name", sa.String(200), nullable=True),
        sa.Column("mean_abs_rank_change", sa.Numeric(8, 4), nullable=True),
        sa.Column("importance_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("pairs_compared", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "criterion_id", name="pk_oat_importance",
        ),
    )


def create_weight_profile_stability() -> None:
    op.create_table(
        "weight_profile_stability",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column("weight_profile", sa.String(30), nullable=False),
        sa.Column("scored_pairs", sa.Integer(), nullable=False),
        sa.Column("top5_overlap_jaccard", sa.Numeric(5, 4), nullable=True),
        sa.Column("top10_overlap_jaccard", sa.Numeric(5, 4), nullable=True),
        sa.Column("top5_overlap_count", sa.Integer(), nullable=True),
        sa.Column("top10_overlap_count", sa.Integer(), nullable=True),
        sa.Column("mean_abs_score_delta", sa.Numeric(7, 4), nullable=True),
        sa.Column("max_abs_score_delta", sa.Numeric(7, 4), nullable=True),
        sa.Column("pairs_drift_compared", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "weight_profile", name="pk_weight_profile_stability",
        ),
    )


def create_threshold_sensitivity(direction_enum: sa.Enum) -> None:
    op.create_table(
        "threshold_sensitivity",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "criterion_id", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column("direction", direction_enum, nullable=False),
        sa.Column("n_pairs_affected", sa.Integer(), nullable=True),
        sa.Column("mean_abs_score_delta", sa.Numeric(7, 4), nullable=True),
        sa.Column("mean_abs_rank_change", sa.Numeric(8, 4), nullable=True),
        sa.Column("survivors_added", sa.Integer(), nullable=True),
        sa.Column("survivors_removed", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "criterion_id", "direction",
            name="pk_threshold_sensitivity",
        ),
    )
