# man_hours: 0.1
"""Helpers for hand-written Alembic migrations that exceed 300 lines.

Each module in this package is dedicated to a single migration revision
(`_034_*` for revision 034, etc.) and only exposes ``op.create_table``
calls. The migration script in ``src/alembic/versions/`` stays a thin
orchestrator + downgrade so each file fits the 300-line budget.
"""
