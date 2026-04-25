# man_hours: 0.5
"""Run-provenance + composite-component tables for Alembic revision 034.

Every table here has a CASCADE FK back to ``runs.run_id``. The
``run_kind`` enum is created by the orchestrator before this module
executes.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def _run_fk() -> sa.ForeignKey:
    return sa.ForeignKey("runs.run_id", ondelete="CASCADE")


def create_runs(run_kind_enum: sa.Enum) -> None:
    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(60), primary_key=True),
        sa.Column("run_kind", run_kind_enum, nullable=False),
        sa.Column("parent_run_id", sa.String(60), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="running"
        ),
        sa.Column("cli_command", sa.Text(), nullable=True),
        sa.Column("git_sha", sa.String(40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_run_id"], ["runs.run_id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_runs_kind", "runs", ["run_kind"])


def create_dataset_snapshot() -> None:
    op.create_table(
        "dataset_snapshot",
        sa.Column(
            "run_id", sa.String(60),
            sa.ForeignKey("runs.run_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("rubric_file_path", sa.Text(), nullable=True),
        sa.Column("rubric_sha256", sa.String(64), nullable=True),
        sa.Column("n_sites_total", sa.Integer(), nullable=True),
        sa.Column("n_sites_screened_in", sa.Integer(), nullable=True),
        sa.Column("n_smrs", sa.Integer(), nullable=True),
        sa.Column("n_criteria_exclusionary", sa.Integer(), nullable=True),
        sa.Column("n_criteria_avoidance", sa.Integer(), nullable=True),
        sa.Column("n_criteria_ranking", sa.Integer(), nullable=True),
        sa.Column(
            "weight_normalisation_profile", sa.String(30), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
    )


def create_composite_components() -> None:
    op.create_table(
        "composite_score_components",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "smr_key", sa.String(30),
            sa.ForeignKey("smr_designs.smr_key"), nullable=False
        ),
        sa.Column("weight_profile", sa.String(30), nullable=False),
        sa.Column(
            "criterion_id", sa.String(10),
            sa.ForeignKey("criteria.criterion_id"), nullable=False
        ),
        sa.Column("score_0_10", sa.Numeric(3, 1), nullable=False),
        sa.Column("weight_normalised", sa.Numeric(5, 4), nullable=True),
        sa.Column("weighted_contribution", sa.Numeric(7, 4), nullable=True),
        sa.Column("category", sa.String(10), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "run_id", "site_id", "smr_key", "weight_profile", "criterion_id",
            name="pk_composite_components",
        ),
    )
    op.create_index(
        "ix_csc_pair", "composite_score_components",
        ["site_id", "smr_key", "weight_profile"],
    )


def create_site_bands() -> None:
    op.create_table(
        "site_bands",
        sa.Column("run_id", sa.String(60), _run_fk(), nullable=False),
        sa.Column(
            "site_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("smr_key", sa.String(30), nullable=True),
        sa.Column("scope_country_code", sa.String(2), nullable=True),
        sa.Column("band", sa.String(1), nullable=False),
        sa.Column("top5pct_hit_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("top10pct_hit_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("top30pct_hit_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("scenarios_total", sa.Integer(), nullable=False),
        sa.Column("scenarios_scored", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "run_id", "site_id", "smr_key", "scope_country_code",
            name="uq_site_bands_scope",
        ),
    )
    op.create_index("ix_site_bands_run", "site_bands", ["run_id"])
