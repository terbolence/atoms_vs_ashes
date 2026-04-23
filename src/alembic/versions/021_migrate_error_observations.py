"""Migrate error observations from site_observations to connector_errors.

Moves rows with source_type = 'llm_error' and rows containing stack
traces / error patterns from site_observations into the dedicated
connector_errors table.  Original rows are preserved (not deleted) to
allow rollback verification before manual cleanup.

Revision ID: 021
Revises: 020
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Migrate llm_error observations
    conn.execute(sa.text("""
        INSERT INTO connector_errors
            (site_id, run_id, connector_slug, criterion_id,
             error_type, message, created_at)
        SELECT
            site_id,
            run_id,
            'llm_pipeline',
            criterion_id,
            CASE
                WHEN observation LIKE '%%rate_limit%%' THEN 'rate_limit'
                WHEN observation LIKE '%%invalid_request%%' THEN 'validation'
                WHEN observation LIKE '%%overloaded%%' THEN 'overloaded'
                ELSE 'api_error'
            END,
            observation,
            created_at
        FROM site_observations
        WHERE source_type = 'llm_error'
    """))

    # 2. Migrate API-side stack-trace observations (DEM enrichment failures, etc.)
    conn.execute(sa.text("""
        INSERT INTO connector_errors
            (site_id, run_id, connector_slug, criterion_id,
             error_type, message, created_at)
        SELECT
            site_id,
            run_id,
            'api_pipeline',
            criterion_id,
            'runtime_error',
            observation,
            created_at
        FROM site_observations
        WHERE source_type NOT IN ('llm_error')
          AND (observation LIKE '%%enrichment failed%%'
               OR observation LIKE '%%Traceback%%'
               OR observation LIKE '%%Error%%')
          AND length(observation) > 500
    """))

    # 3. Mark migrated llm_error rows (add a prefix so they can be identified)
    conn.execute(sa.text("""
        UPDATE site_observations
        SET source_type = 'llm_error_migrated'
        WHERE source_type = 'llm_error'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE site_observations
        SET source_type = 'llm_error'
        WHERE source_type = 'llm_error_migrated'
    """))
    conn.execute(sa.text(
        "DELETE FROM connector_errors WHERE connector_slug IN ('llm_pipeline', 'api_pipeline')"
    ))
