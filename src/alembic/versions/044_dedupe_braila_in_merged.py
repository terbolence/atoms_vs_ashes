# man_hours: 0.8
"""Remove the duplicate ``Braila power station`` row from the merged DB.

Background
----------

`atoms_vs_ashes_merged` carries two `Braila power station` rows at the
same coordinates ``(45.165033, 27.923383)``:

* `29836b52-…` — status `retired` — the canonical row, present in
  both `atoms_vs_ashes` and `atoms_vs_ashes_merged`.
* `323cdbf0-…` — status `cancelled` — present **only** in the merged
  DB. Every scoring/sensitivity run that referenced this UUID also
  referenced the canonical UUID with the same number of verdicts (see
  the audit notes for the merged-DB-canonical-cutover plan), so the
  row is a true duplicate, not a unique site.

This migration cascades the deletion through all child tables (FKs are
``NO ACTION`` for most of them, so order matters), then drops the row
from `sites`. It is **idempotent**: if the duplicate is already absent
the upgrade is a no-op.

Applying this migration to `atoms_vs_ashes` is harmless because the
duplicate UUID never existed there; the SELECT count returns 0 and the
upgrade short-circuits.

Revision ID: 044
Revises: 043
Create Date: 2026-05-15
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "044"
down_revision: Union[str, None] = "043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DUPLICATE_SITE_ID = "323cdbf0-c4a8-467a-af76-e2e3df0b537f"


# Order matters: child tables that hold rows pinned to ``site_id`` must
# be cleared before the parent ``sites`` row can be dropped. The order
# mirrors `036_remove_supplementary_braila_chiscani_site.py`, extended
# with the merged-only tables introduced after migration 036
# (`country_site_rankings`, `failure_outcomes`, `merge_audit`,
# `site_llm_observations`, `site_llm_verdicts`).
_PRE_DELETE: tuple[str, ...] = (
    "site_llm_observations",
    "site_llm_verdicts",
    "merge_audit",
    "country_site_rankings",
    "failure_outcomes",
    "site_raw_responses",
    "site_observations",
    "site_bands",
    "composite_score_components",
    "composite_rankings",
    "ranking_scores",
    "screening_verdicts",
    "site_infrastructure_v2",
    "site_emergency_planning",
    "site_radiological",
    "site_human_hazards",
    "site_natural_hazards",
    "site_units",
    "site_ownership",
    "connector_errors",
)


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    bind = op.get_bind()
    present = bind.execute(
        sa.text("SELECT 1 FROM sites WHERE site_id = :sid"),
        {"sid": _DUPLICATE_SITE_ID},
    ).first()
    if not present:
        return
    for table in _PRE_DELETE:
        if not _table_exists(table):
            continue
        bind.execute(
            sa.text(f'DELETE FROM "{table}" WHERE site_id = :sid'),
            {"sid": _DUPLICATE_SITE_ID},
        )
    if _table_exists("audit_log"):
        bind.execute(
            sa.text("DELETE FROM audit_log WHERE site_id = :sid"),
            {"sid": _DUPLICATE_SITE_ID},
        )
    bind.execute(
        sa.text("DELETE FROM sites WHERE site_id = :sid"),
        {"sid": _DUPLICATE_SITE_ID},
    )


def downgrade() -> None:
    """Irreversible: the duplicate row is not recreated."""
