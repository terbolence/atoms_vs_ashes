"""Backfill enrichment_runs from existing run_id values.

Scans all tables that carry a run_id column and inserts distinct values
into enrichment_runs with best-effort metadata inferred from the run_id
format and table of origin.

Revision ID: 019
Revises: 018
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES_WITH_RUN_ID = [
    ("site_natural_hazards", "enrich"),
    ("site_human_hazards", "enrich"),
    ("site_radiological", "enrich"),
    ("site_emergency_planning", "enrich"),
    ("site_infrastructure_v2", "enrich"),
    ("screening_verdicts", "screen"),
    ("site_observations", "enrich"),
    ("audit_log", "ingest"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for table, run_type in _TABLES_WITH_RUN_ID:
        conn.execute(
            sa.text(f"""
                INSERT INTO enrichment_runs (run_id, run_type, status)
                SELECT DISTINCT run_id,
                       CASE WHEN run_id LIKE 'llm-%%' THEN 'llm'
                            ELSE :run_type
                       END,
                       'completed'
                FROM {table}
                WHERE run_id IS NOT NULL
                ON CONFLICT (run_id) DO NOTHING
            """),
            {"run_type": run_type},
        )


def downgrade() -> None:
    op.execute("DELETE FROM enrichment_runs")


import sqlalchemy as sa  # noqa: E402 – needed for sa.text in upgrade
