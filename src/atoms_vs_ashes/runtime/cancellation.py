# man_hours: 0.5
"""Minimal cooperative cancellation token (plan §6 + §10).

Long-running scoring and sensitivity stages periodically call
:meth:`CancellationToken.raise_if_cancelled` (or check
:attr:`is_cancelled`) so the GUI/CLI can request a graceful stop
between site iterations or perturbation steps. The token is
thread-safe so a FastAPI cancel handler can flip it from another
worker.

Design notes:
- This is intentionally not a ``threading.Event`` directly so callers
  can attach a ``reason`` (logged + persisted).
- :class:`CancellationRequested` is what callers should ``except`` —
  it is *not* a runtime error, so the suite cleans up partial state
  and marks ``runs.status = cancelled`` rather than ``failed``.
"""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class CancellationRequested(Exception):
    """Raised from ``raise_if_cancelled`` when the token has been tripped.

    Caught by the orchestrator (engine, sensitivity suite, CLI driver)
    to mark the run as ``cancelled`` and persist whatever progress has
    been committed so partial results are still inspectable from the
    GUI (plan §10).
    """

    def __init__(self, reason: str | None = None) -> None:
        super().__init__(reason or "cancelled")
        self.reason = reason


@dataclass
class CancellationToken:
    """Thread-safe cooperative cancellation flag with a reason.

    A token defaults to "armed but not tripped" — call :meth:`cancel`
    to trip it. Pass the *same* instance into every nested call
    (engine -> sensitivity suite -> threshold driver) so a single
    user-initiated cancel halts the whole pipeline.
    """

    reason: str | None = None

    def __post_init__(self) -> None:
        self._event = threading.Event()
        if self.reason is not None:
            self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self, reason: str | None = None) -> None:
        """Trip the token. Idempotent — repeat calls keep the first reason."""
        if self._event.is_set():
            return
        if reason is not None:
            self.reason = reason
        self._event.set()

    def raise_if_cancelled(self) -> None:
        """Raise :class:`CancellationRequested` if the token has been tripped.

        Called from inside long loops at safe points (after a site is
        committed, between perturbation steps, etc.) so cleanup can
        run before the orchestrator catches and marks the run as
        cancelled.
        """
        if self._event.is_set():
            raise CancellationRequested(self.reason)


@dataclass
class FileWatchedCancellationToken(CancellationToken):
    """Cancellation token that also trips when a sentinel file appears.

    Cross-process cancellation: ``score cancel --run-id`` writes
    ``runs/<run_id>/cancel.flag`` (an empty file) and the running
    scoring/sensitivity process checks for it on every safe-point
    poll. Cheaper than IPC and survives TTY disconnects.
    """

    sentinel_path: Path | None = None

    @property
    def is_cancelled(self) -> bool:  # type: ignore[override]
        if self._event.is_set():
            return True
        if self.sentinel_path is not None and self.sentinel_path.exists():
            self.cancel(reason=f"sentinel:{self.sentinel_path}")
            return True
        return False

    def raise_if_cancelled(self) -> None:  # type: ignore[override]
        if self.is_cancelled:
            raise CancellationRequested(self.reason)


@contextmanager
def install_sigint_handler(token: CancellationToken) -> Iterator[None]:
    """Trip ``token`` on Ctrl-C while preserving the prior handler.

    Use sparingly — the CLI binds this around long ``score run`` /
    ``score sensitivity`` calls so a single Ctrl-C records the
    cancellation reason and lets the orchestrator finalise before
    the process exits.
    """

    def _handler(signum, frame):  # noqa: ARG001
        token.cancel(reason="sigint")

    previous = signal.signal(signal.SIGINT, _handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


__all__ = [
    "CancellationRequested",
    "CancellationToken",
    "FileWatchedCancellationToken",
    "install_sigint_handler",
]
