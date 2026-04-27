# man_hours: 1.0
"""Create singleton active_run_profile table; seed from former baseline.yaml.

The GUI now stores the user's RunProfile in this row instead of
``config/run_profiles/baseline.yaml``. The CLI engine continues to
consume YAML; the GUI exports this row to a transient YAML at
run-launch (see ``atoms_vs_ashes.gui._runner``).

Revision ID: 039
Revises: 038
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "039"
down_revision: Union[str, None] = "038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_BASELINE_PROFILE: dict = {
    "run_label": "baseline",
    "db_profile": "merged",
    "spec_dir": "config/scoring_specs",
    "weight_profile": "baseline",
    "scope": {
        "countries": [],
        "smr_keys": ["nuscale_voygr6"],
        "site_status_in": ["operating", "retired", "mothballed"],
        "site_ids": [],
    },
    "fail_thresholds": {},
    "expert_override": False,
    "scoring": {
        "unscored_fallback_score": 5.0,
        "unscored_fraction_warn": 0.05,
        "unscored_fraction_hard": 0.20,
        "weight_overrides": {},
        "qualification_mode": "normal",
        "top_n_per_country": 10,
        "near_miss_gap_pct": 10.0,
    },
    "sensitivity": {
        "enabled": ["weights", "mc", "threshold", "oat", "country"],
        "mc_iterations": 5000,
        "mc_seed": 42,
        "weight_perturbation_pct": 20.0,
        "threshold_targeted_pct": [10.0, 25.0],
        "threshold_global_stress": True,
        "top_n_country": 20,
        "country_balance_max_share": 0.40,
        "mc_stability_band_width": 1.0,
    },
    "output": {
        "stamp": "",
        "audit_dir": "audit/post_processing/06_scoring",
        "report_dir": "report/output/sensitivity",
    },
    "notes": "Seeded from former config/run_profiles/baseline.yaml (alembic 039).",
}


def upgrade() -> None:
    op.create_table(
        "active_run_profile",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column(
            "profile", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 'active'", name="ck_active_run_profile_singleton"),
    )
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO active_run_profile (id, profile, updated_by) "
            "VALUES ('active', CAST(:payload AS JSONB), 'alembic_039') "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"payload": __import__("json").dumps(_BASELINE_PROFILE)},
    )


def downgrade() -> None:
    op.drop_table("active_run_profile")
