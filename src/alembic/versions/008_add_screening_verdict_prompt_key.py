"""Add prompt_key to screening_verdicts for sub-criterion differentiation.

Criteria like HI-01 are assessed by multiple prompts (A1–A4). Without
a prompt_key column the unique constraint causes overwrites or failures.

Revision ID: 008
Revises: 007
Create Date: 2026-04-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "screening_verdicts",
        sa.Column("prompt_key", sa.String(10), nullable=True),
    )
    op.drop_constraint(
        "uq_verdict_site_smr_criterion_run",
        "screening_verdicts",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_verdict_site_smr_criterion_prompt_run",
        "screening_verdicts",
        ["site_id", "smr_key", "criterion_id", "prompt_key", "run_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_verdict_site_smr_criterion_prompt_run",
        "screening_verdicts",
        type_="unique",
    )
    op.drop_column("screening_verdicts", "prompt_key")
    op.create_unique_constraint(
        "uq_verdict_site_smr_criterion_run",
        "screening_verdicts",
        ["site_id", "smr_key", "criterion_id", "run_id"],
    )
