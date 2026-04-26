# man_hours: 1.0
"""Run-profile + compiled-spec provenance columns on dataset_snapshot.

Adds the six fields required by the user-controlled scoring plan
(§5 of ``scoring_control_gui_872d4eb7``):

- ``run_profile_path`` / ``run_profile_sha256`` — anchors the
  configuration the run was kicked off with so two runs with the
  same profile produce identical hashes.
- ``spec_bundle_path`` / ``spec_bundle_sha256`` — anchors the
  compiled :class:`Criterion` bundle (template + user fail-thresholds
  → canonical JSON) which the engine actually consumed.
- ``n_countries_in_scope`` / ``n_smrs_in_scope`` — light scope
  cardinalities used in audit MD headers without re-loading the
  profile.
- ``scope_summary`` — full :class:`RunScope` plus
  ``fail_thresholds`` and any ``expert_overrides`` (criterion → code
  → ``{value, recommended_value, deviation_pct}``). JSONB so the GUI
  can read it back without a re-compile.

All columns are nullable so historical ``dataset_snapshot`` rows
remain valid; new rows from :func:`atoms_vs_ashes.db.runs.start_run`
populate them.

Revision ID: 035
Revises: 034
Create Date: 2026-04-26
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = (
    sa.Column("run_profile_path", sa.Text(), nullable=True),
    sa.Column("run_profile_sha256", sa.String(64), nullable=True),
    sa.Column("spec_bundle_path", sa.Text(), nullable=True),
    sa.Column("spec_bundle_sha256", sa.String(64), nullable=True),
    sa.Column("n_countries_in_scope", sa.Integer(), nullable=True),
    sa.Column("n_smrs_in_scope", sa.Integer(), nullable=True),
    sa.Column("scope_summary", JSONB(), nullable=True),
)


def upgrade() -> None:
    for col in _NEW_COLUMNS:
        op.add_column("dataset_snapshot", col.copy())


def downgrade() -> None:
    for col in reversed(_NEW_COLUMNS):
        op.drop_column("dataset_snapshot", col.name)
