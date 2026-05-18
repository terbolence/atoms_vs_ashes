# man_hours: 0.35
"""Widen active_run_profile site_status_in for supplementary catalogue sites.

Revision ID: 050
Revises: 049
"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "050"
down_revision: Union[str, None] = "049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Statuses used by config/default.yml supplementary_sites (Iernut = construction).
_SUPPLEMENTARY_STATUSES = ("construction", "cancelled", "shelved")


def upgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            "SELECT profile FROM active_run_profile WHERE id = 'active'"
        )
    ).first()
    if row is None:
        return
    profile = dict(row[0] or {})
    scope = dict(profile.get("scope") or {})
    current = list(scope.get("site_status_in") or [])
    merged = sorted({*current, *_SUPPLEMENTARY_STATUSES})
    if merged == current:
        return
    scope["site_status_in"] = merged
    profile["scope"] = scope
    bind.execute(
        sa.text(
            "UPDATE active_run_profile "
            "SET profile = CAST(:payload AS JSONB), "
            "    updated_by = 'alembic_050', "
            "    updated_at = now() "
            "WHERE id = 'active'"
        ),
        {"payload": json.dumps(profile)},
    )


def downgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            "SELECT profile FROM active_run_profile WHERE id = 'active'"
        )
    ).first()
    if row is None:
        return
    profile = dict(row[0] or {})
    scope = dict(profile.get("scope") or {})
    current = list(scope.get("site_status_in") or [])
    scope["site_status_in"] = [
        s for s in current if s not in _SUPPLEMENTARY_STATUSES
    ]
    profile["scope"] = scope
    bind.execute(
        sa.text(
            "UPDATE active_run_profile "
            "SET profile = CAST(:payload AS JSONB), "
            "    updated_by = 'alembic_050_downgrade', "
            "    updated_at = now() "
            "WHERE id = 'active'"
        ),
        {"payload": json.dumps(profile)},
    )
