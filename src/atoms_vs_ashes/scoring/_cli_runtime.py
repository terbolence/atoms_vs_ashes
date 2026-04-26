# man_hours: 0.5
"""Helpers shared by the ``score run`` / ``score sensitivity`` commands.

Keeps :mod:`atoms_vs_ashes.scoring._cli` ≤ 300 lines while
preserving a single source of truth for the cancellation-token +
heartbeat-writer wiring that GUI users depend on (plan §6 + §7 +
§10).
"""

from __future__ import annotations

from pathlib import Path

from atoms_vs_ashes.runtime import (
    FileWatchedCancellationToken,
    HeartbeatWriter,
)


def make_cancellation_token(cancel_flag: str | None) -> FileWatchedCancellationToken:
    """Return a token that trips when ``cancel_flag`` exists on disk."""
    return FileWatchedCancellationToken(
        sentinel_path=Path(cancel_flag) if cancel_flag else None,
    )


def make_heartbeat_writer(heartbeat_path: str | None) -> HeartbeatWriter:
    """Return a writer that appends ticks to ``heartbeat_path`` (or no-op)."""
    return HeartbeatWriter(Path(heartbeat_path) if heartbeat_path else None)


def arm_cancel_flag(cancel_flag: str) -> Path:
    """Touch ``cancel_flag`` so the watching process cancels."""
    path = Path(cancel_flag)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


__all__ = [
    "arm_cancel_flag",
    "make_cancellation_token",
    "make_heartbeat_writer",
]
