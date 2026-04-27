# man_hours: 1.0
"""Remove the manually-ingested Brăila–Chișcani supplementary site row.

The GEM-sourced **Brăila** coal/thermal plant stays. The duplicate came from
``ingestion.supplementary_sites`` in ``config/default.yml`` (coordinates
``45.2744 / 27.9291`` with fewer significant digits than typical GEM rows).

Deletes dependent rows first (legacy FKs are ``NO ACTION``), then the
``sites`` row. Tables whose FKs use ``ON DELETE CASCADE`` toward
``sites`` are cleaned automatically when the parent row disappears.

Revision ID: 036
Revises: 035
Create Date: 2026-04-26
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "036"
down_revision: Union[str, None] = "035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Rows inserted by ``load_supplementary_sites`` (no GEM location id,
# name contains Chișcani / ASCII variant, or exact YAML coordinates).
_DOOMED = """
SELECT site_id FROM sites
WHERE country_code = 'RO'
  AND (
    lower(name) LIKE '%chiscani%'
    OR lower(name) LIKE '%chișcani%'
    OR (
      round(latitude::numeric, 4) = 45.2744
      AND round(longitude::numeric, 4) = 27.9291
    )
  )
"""

# Child tables first (no ON DELETE CASCADE from ``sites`` in core schema).
_PRE_DELETE = (
    "site_llm_observations",
    "site_llm_verdicts",
    "merge_audit",
    "site_raw_responses",
    "site_observations",
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


def upgrade() -> None:
    bind = op.get_bind()
    n = bind.execute(sa.text(f"SELECT count(*) FROM ({_DOOMED}) t")).scalar()
    if not n:
        return
    for table in _PRE_DELETE:
        bind.execute(
            sa.text(f'DELETE FROM "{table}" WHERE site_id IN ({_DOOMED})')
        )
    bind.execute(sa.text(f"DELETE FROM audit_log WHERE site_id IN ({_DOOMED})"))
    bind.execute(sa.text(f"DELETE FROM sites WHERE site_id IN ({_DOOMED})"))


def downgrade() -> None:
    """Irreversible data migration — supplementary row not recreated."""
