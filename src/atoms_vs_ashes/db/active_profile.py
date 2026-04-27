# man_hours: 1.0
"""Read/write the singleton ``active_run_profile`` row as a :class:`RunProfile`.

The DB JSONB column is the source of truth for the GUI's current run
profile. These helpers handle the Pydantic <-> JSONB round-trip so the
rest of the codebase keeps speaking :class:`RunProfile`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import ActiveRunProfile
from atoms_vs_ashes.runprofile.schema import RunProfile

ACTIVE_PROFILE_ID = "active"


def load_active_profile(session: Session) -> RunProfile:
    """Return the live :class:`RunProfile` from the DB singleton row.

    Raises :class:`RuntimeError` if the row is missing — alembic 039
    seeds it on every fresh DB so callers should never see this in
    practice; treat it as a corrupted-install signal.
    """
    row = session.get(ActiveRunProfile, ACTIVE_PROFILE_ID)
    if row is None:
        raise RuntimeError(
            "active_run_profile row is missing — run `alembic upgrade head` "
            "to seed it from the migration default."
        )
    return RunProfile.model_validate(row.profile or {})


def save_active_profile(
    session: Session,
    profile: RunProfile,
    *,
    updated_by: str | None = None,
) -> None:
    """Upsert the singleton row with ``profile.model_dump(mode='json')``.

    Caller is responsible for the surrounding transaction (a
    ``session_scope`` block flushes/commits on exit).
    """
    payload = profile.model_dump(mode="json")
    row = session.get(ActiveRunProfile, ACTIVE_PROFILE_ID)
    if row is None:
        row = ActiveRunProfile(id=ACTIVE_PROFILE_ID, profile=payload)
        if updated_by is not None:
            row.updated_by = updated_by
        session.add(row)
    else:
        row.profile = payload
        if updated_by is not None:
            row.updated_by = updated_by
    session.flush()


__all__ = [
    "ACTIVE_PROFILE_ID",
    "load_active_profile",
    "save_active_profile",
]
