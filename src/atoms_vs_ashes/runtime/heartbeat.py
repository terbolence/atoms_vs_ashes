# man_hours: 1.0
"""Heartbeat writer for long-running runs (plan §6 + §10).

Emits one JSON object per line to ``runs/<run_id>/heartbeat.jsonl`` so
the GUI's WebSocket can ``tail -f`` the file (or, equivalently, the
FastAPI handler can ``aiofiles``-stream it).

Each tick carries::

    {"ts": "2026-04-26T18:30:00Z",
     "stage": "scoring|sensitivity:mc|sensitivity:threshold|...",
     "processed": 142,
     "total": 1900,
     "eta_s": 540.0,
     "message": "site=RO-12 smr=nuscale_voygr6"}

Throttling: at most one tick every ``min_interval_s`` seconds (default
1.0 s) plus a guaranteed final tick on close. This keeps the file
small even for 10k-iteration MC runs while still feeling live in the
GUI.
"""

from __future__ import annotations

import datetime as _dt
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def _now_iso() -> str:
    return (
        _dt.datetime.now(tz=_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class HeartbeatRecord:
    """One JSONL row written by :class:`HeartbeatWriter`."""

    stage: str
    processed: int
    total: int
    message: str = ""
    ts: str = field(default_factory=_now_iso)
    eta_s: float | None = None
    unit: str = "items"

    def to_json(self) -> str:
        return json.dumps(
            {
                "ts": self.ts,
                "stage": self.stage,
                "processed": self.processed,
                "total": self.total,
                "eta_s": self.eta_s,
                "message": self.message,
                "unit": self.unit,
            },
            separators=(",", ":"),
        )


class HeartbeatWriter:
    """Append-only JSONL heartbeat writer with per-stage throttling.

    Use as a context manager; the writer flushes on every emitted
    tick so the GUI sees fresh bytes immediately. Falls back to a
    no-op when ``path`` is ``None`` so library code can stay simple.
    """

    def __init__(
        self,
        path: Path | None,
        *,
        min_interval_s: float = 1.0,
        clock=time.monotonic,
    ) -> None:
        self.path = Path(path) if path is not None else None
        self.min_interval_s = float(min_interval_s)
        self._clock = clock
        self._fh: IO[str] | None = None
        self._stage_started: dict[str, float] = {}
        self._stage_last_emit: dict[str, float] = {}

    def __enter__(self) -> "HeartbeatWriter":
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fh is not None:
            self._fh.flush()
            self._fh.close()
            self._fh = None

    def start_stage(
        self,
        stage: str,
        *,
        total: int,
        message: str = "",
        unit: str = "items",
    ) -> None:
        """Mark a stage as started and emit a 0/total tick.

        Resets the throttle so the next ``tick`` for this stage is
        guaranteed to fire. Safe to call repeatedly when an
        orchestrator re-enters a stage (the GUI will see two start
        ticks but no double-counting downstream).
        """
        self._stage_started[stage] = self._clock()
        self._stage_last_emit[stage] = -float("inf")
        self.emit(
            HeartbeatRecord(
                stage=stage, processed=0, total=int(total),
                message=message, unit=unit,
            )
        )

    def tick(
        self,
        stage: str,
        *,
        processed: int,
        total: int,
        message: str = "",
        unit: str = "items",
        force: bool = False,
    ) -> None:
        """Emit a tick subject to ``min_interval_s`` throttling.

        ``force=True`` bypasses the throttle (use sparingly — e.g.
        when a substantial milestone like "all sites scored" is
        reached and the GUI should refresh even if the previous
        tick was very recent).
        """
        now = self._clock()
        last = self._stage_last_emit.get(stage, -float("inf"))
        if not force and (now - last) < self.min_interval_s:
            return
        self._stage_last_emit[stage] = now
        eta = self._eta_seconds(stage, processed=processed, total=total, now=now)
        self.emit(
            HeartbeatRecord(
                stage=stage,
                processed=int(processed),
                total=int(total),
                eta_s=eta,
                message=message,
                unit=unit,
            )
        )

    def end_stage(
        self,
        stage: str,
        *,
        processed: int,
        total: int,
        message: str = "",
        unit: str = "items",
    ) -> None:
        """Force a final tick so the GUI bar reaches 100 %."""
        self.tick(
            stage,
            processed=processed,
            total=total,
            message=message or "stage_complete",
            unit=unit,
            force=True,
        )

    def emit(self, record: HeartbeatRecord) -> None:
        """Write one record now (no throttling). Public for unit tests."""
        line = record.to_json()
        if self._fh is not None:
            self._fh.write(line + "\n")
            self._fh.flush()
        log.debug("heartbeat", **json.loads(line))

    def _eta_seconds(
        self, stage: str, *, processed: int, total: int, now: float
    ) -> float | None:
        started = self._stage_started.get(stage)
        if started is None or processed <= 0 or total <= 0:
            return None
        elapsed = max(0.0, now - started)
        rate = processed / elapsed if elapsed > 0 else 0.0
        if rate <= 0:
            return None
        remaining = max(0, total - processed)
        return round(remaining / rate, 2)


__all__ = ["HeartbeatRecord", "HeartbeatWriter"]
