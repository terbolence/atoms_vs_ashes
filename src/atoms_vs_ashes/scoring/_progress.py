# man_hours: 2.0
"""Progress reporter for long-running scoring loops.

Design goals (see plan §2.1 and §4 of
``.cursor/plans/phase_1.6_sensitivity_cli_71ef0042.plan.md``):

- Show **percent + M/N + ETA** in a TTY (rich-based), without adding a
  new dependency (``rich`` is already in ``pyproject.toml``).
- Degrade gracefully when stdout is **not** a TTY (CI, piped logs):
  emit a structured log line at every 5 % boundary and at completion.
- Keep the API tiny: ``with ProgressReporter(total=N, description='...') as p:``
  and ``p.advance(n)`` — ``n`` can be greater than 1 so a vectorised
  chunk still advances the bar accurately.
"""

from __future__ import annotations

import sys
from typing import Iterable, Iterator, TypeVar

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

T = TypeVar("T")

_LOG_BOUNDARY_PCT = 5  # emit fallback log every 5 %


class ProgressReporter:
    """Context-manager progress reporter with TTY + non-TTY modes.

    Typical usage::

        with ProgressReporter(total=len(pairs), description="Monte Carlo") as p:
            for pair in pairs:
                do_work(pair)
                p.advance(1)

    ``advance(n)`` tolerates ``n > 1`` — used when a vectorised chunk
    processes many units in one call.
    """

    def __init__(
        self,
        *,
        total: int,
        description: str,
        enabled: bool = True,
        console: Console | None = None,
    ) -> None:
        self.total = max(0, int(total))
        self.description = description
        self.console = console or Console(file=sys.stderr)
        self._use_rich = bool(enabled) and self.console.is_terminal
        self._progress: Progress | None = None
        self._task_id: int | None = None
        self._done = 0
        self._last_logged_pct = -1

    # --- context manager -------------------------------------------------

    def __enter__(self) -> "ProgressReporter":
        if self._use_rich:
            self._progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=self.console,
                transient=False,
            )
            self._progress.__enter__()
            self._task_id = self._progress.add_task(
                self.description, total=self.total if self.total > 0 else None
            )
        else:
            log.info(
                "progress_start",
                description=self.description,
                total=self.total,
                mode="log_fallback",
            )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._progress is not None:
            self._progress.__exit__(exc_type, exc, tb)
            self._progress = None
            self._task_id = None
            return
        if exc_type is None:
            log.info(
                "progress_done",
                description=self.description,
                done=self._done,
                total=self.total,
                percent=100,
            )

    # --- api -------------------------------------------------------------

    def advance(self, n: int = 1) -> None:
        """Advance by ``n`` units (``n`` may be > 1 for vectorised steps)."""
        if n <= 0 or self.total <= 0:
            return
        self._done = min(self.total, self._done + n)
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, advance=n)
            return
        pct = int(100 * self._done / self.total)
        boundary = (pct // _LOG_BOUNDARY_PCT) * _LOG_BOUNDARY_PCT
        if boundary > self._last_logged_pct:
            self._last_logged_pct = boundary
            log.info(
                "progress_tick",
                description=self.description,
                done=self._done,
                total=self.total,
                percent=boundary,
            )

    def track(self, iterable: Iterable[T]) -> Iterator[T]:
        """Convenience: iterate while advancing once per element."""
        for item in iterable:
            yield item
            self.advance(1)
