# man_hours: 0.4
"""Canonical map from logical DB profile name to PostgreSQL database.

Imported by both the CLI (`cli.py`) and the engine bootstrap
(`engine.init_engine_for_active_profile`) so the two never drift apart.
Per the merged-DB-canonical-cutover plan, ``merged`` is the canonical
read/write target.
"""

from __future__ import annotations

DB_PROFILES: dict[str, str] = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

DEFAULT_PROFILE: str = "merged"


def resolve_db_name(profile: str) -> str:
    """Return the PostgreSQL database name for ``profile``.

    Raises :class:`ValueError` (not :class:`KeyError`) so callers get a
    crisp message at startup if the active profile carries an unknown
    ``db_profile`` string.
    """
    try:
        return DB_PROFILES[profile]
    except KeyError as exc:
        raise ValueError(
            f"Unknown db_profile {profile!r}; "
            f"expected one of {sorted(DB_PROFILES)}"
        ) from exc


__all__ = ["DB_PROFILES", "DEFAULT_PROFILE", "resolve_db_name"]
