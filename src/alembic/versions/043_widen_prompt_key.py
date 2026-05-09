# man_hours: 0.2
"""Widen ``prompt_key`` columns from varchar(10) to varchar(40).

The legacy 10-char ceiling rejected post-feedback compound keys such as
``E_RI04:floor`` (12 chars). All scoring engine writes use the longer
form; the column is widened in two tables that carry it.

Revision ID: 043
Revises: 042
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "043"
down_revision: Union[str, None] = "042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(name)


def upgrade() -> None:
    if _table_exists("screening_verdicts"):
        op.alter_column(
            "screening_verdicts", "prompt_key",
            existing_type=sa.String(10),
            type_=sa.String(40),
            existing_nullable=True,
        )
    if _table_exists("llm_verdicts"):
        op.alter_column(
            "llm_verdicts", "prompt_key",
            existing_type=sa.String(10),
            type_=sa.String(40),
            existing_nullable=False,
        )


def downgrade() -> None:
    if _table_exists("llm_verdicts"):
        op.alter_column(
            "llm_verdicts", "prompt_key",
            existing_type=sa.String(40),
            type_=sa.String(10),
            existing_nullable=False,
        )
    if _table_exists("screening_verdicts"):
        op.alter_column(
            "screening_verdicts", "prompt_key",
            existing_type=sa.String(40),
            type_=sa.String(10),
            existing_nullable=True,
        )
