"""Phase 1.6 — persist analytics + run provenance to PostgreSQL.

Adds a regulator-grade audit trail by materialising every numeric
artefact the sensitivity / failure / swing / correlation pipelines
currently keep on disk only.

The 14 ``CREATE TABLE`` calls live in dedicated helper modules under
``atoms_vs_ashes.db.migrations`` so this file remains a thin
orchestrator and stays under the project's 300-line Python budget.

Forward-only: existing rows in ``composite_rankings`` /
``ranking_scores`` / ``screening_verdicts`` keep their string
``run_id`` values; the FKs added here are ``NOT VALID`` so historical
orphan references are not rejected.

Revision ID: 034
Revises: 033
Create Date: 2026-04-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from atoms_vs_ashes.db.migrations import (
    _034_failure as failure_tables,
    _034_provenance as provenance_tables,
    _034_rankings as ranking_tables,
)

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_RUN_KIND = sa.Enum(
    "scoring", "sensitivity", "failure_analysis", "correlation",
    "swing_audit", "extended_analysis",
    name="run_kind",
    create_constraint=True,
)
_THRESHOLD_DIRECTION = sa.Enum(
    "plus_25", "minus_25",
    name="threshold_direction",
    create_constraint=True,
)
_FAILURE_AXIS = sa.Enum(
    "criterion", "country", "smr", "multi_failure_histogram", "summary",
    name="failure_aggregate_axis",
    create_constraint=True,
)


_NEW_TABLES_DROP_ORDER = (
    "country_balance_check",
    "criterion_correlations",
    "swing_weights",
    "failure_aggregates",
    "failure_outcomes",
    "threshold_sensitivity",
    "weight_profile_stability",
    "oat_importance",
    "country_site_rankings",
    "country_rankings_summary",
    "site_bands",
    "composite_score_components",
    "dataset_snapshot",
    "runs",
)

_SOFT_FK_TARGETS = (
    ("composite_rankings", "fk_composite_rankings_run"),
    ("ranking_scores", "fk_ranking_scores_run"),
    ("screening_verdicts", "fk_screening_verdicts_run"),
)


def upgrade() -> None:
    bind = op.get_bind()
    _RUN_KIND.create(bind, checkfirst=True)
    _THRESHOLD_DIRECTION.create(bind, checkfirst=True)
    _FAILURE_AXIS.create(bind, checkfirst=True)

    provenance_tables.create_runs(_RUN_KIND)
    provenance_tables.create_dataset_snapshot()
    provenance_tables.create_composite_components()
    provenance_tables.create_site_bands()

    ranking_tables.create_country_rankings_summary()
    ranking_tables.create_country_site_rankings()
    ranking_tables.create_oat_importance()
    ranking_tables.create_weight_profile_stability()
    ranking_tables.create_threshold_sensitivity(_THRESHOLD_DIRECTION)

    failure_tables.create_failure_outcomes()
    failure_tables.create_failure_aggregates(_FAILURE_AXIS)
    failure_tables.create_swing_weights()
    failure_tables.create_criterion_correlations()
    failure_tables.create_country_balance_check()

    _add_soft_fks_to_existing_run_id_columns(bind)


def downgrade() -> None:
    bind = op.get_bind()
    for table, fk_name in reversed(_SOFT_FK_TARGETS):
        bind.execute(sa.text(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk_name}"
        ))
    for tbl in _NEW_TABLES_DROP_ORDER:
        op.drop_table(tbl)
    _FAILURE_AXIS.drop(bind, checkfirst=True)
    _THRESHOLD_DIRECTION.drop(bind, checkfirst=True)
    _RUN_KIND.drop(bind, checkfirst=True)


def _add_soft_fks_to_existing_run_id_columns(bind) -> None:
    """Wire ``run_id`` on existing tables to ``runs.run_id`` with NOT VALID.

    Historical rows (e.g. the 20260423 / 20260425 runs) predate the
    ``runs`` table; ``NOT VALID`` keeps them legal while making any new
    INSERT reference an existing ``runs`` row.
    """
    for table, fk_name in _SOFT_FK_TARGETS:
        bind.execute(sa.text(
            f"ALTER TABLE {table} "
            f"ADD CONSTRAINT {fk_name} "
            "FOREIGN KEY (run_id) REFERENCES runs(run_id) "
            "ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED NOT VALID"
        ))
