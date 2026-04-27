# man_hours: 1.5
"""Subprocess driver for the GUI's start/stop scoring + sensitivity buttons.

We deliberately spawn the existing ``score`` CLI in a child process
(rather than calling :func:`run_scoring` in-thread) so cancellation is
trivial: the GUI writes the sentinel file via the
``FileWatchedCancellationToken`` protocol the engine already polls
(plan §7). The Streamlit page only consumes the heartbeat JSONL the
child appends to disk, leaving the engine code untouched.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class RunHandle:
    """One running CLI invocation tracked by the GUI."""

    run_id: str
    cmd: list[str]
    pid: int | None
    heartbeat_path: Path
    cancel_flag_path: Path
    log_path: Path
    started_at: float = field(default_factory=time.time)
    returncode: int | None = None

    def is_running(self) -> bool:
        if self.pid is None or self.returncode is not None:
            return False
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True


def _runs_root() -> Path:
    root = Path(".cursor/.atoms_runs")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _new_run_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def start_score_run(profile_path: Path, *, weight_profile: str) -> RunHandle:
    """Launch ``score run`` as a detached child process."""
    run_id = _new_run_id("score")
    return _start_command(
        run_id,
        [
            sys.executable,
            "-m",
            "atoms_vs_ashes",
            "--run-id",
            run_id,
            "score",
            "run",
            "--weight-profile",
            weight_profile,
            "--profile",
            str(profile_path.resolve()),
        ],
    )


def start_sensitivity_run(
    profile_path: Path,
    *,
    weight_profile: str,
    iterations: int | None = None,
    include: Iterable[str] = ("weights", "mc", "country"),
    seed: int = 42,
    audit_dir: str = "audit/post_processing/06_scoring",
    no_progress: bool = True,
) -> RunHandle:
    """Launch ``score sensitivity`` as a detached child process."""
    run_id = _new_run_id("sens")
    cmd = [
        sys.executable,
        "-m",
        "atoms_vs_ashes",
        "--run-id",
        run_id,
        "score",
        "sensitivity",
        "--weight-profile-base",
        weight_profile,
        "--rubric-dir",
        str(_resolve_spec_dir(profile_path)),
        "--audit-dir",
        audit_dir,
        "--seed",
        str(seed),
    ]
    if iterations is not None:
        cmd += ["--mc-draws", str(iterations)]
    for stage in include:
        cmd += ["--include", stage]
    if no_progress:
        cmd += ["--no-progress"]
    return _start_command(run_id, cmd)


def _resolve_spec_dir(profile_path: Path) -> Path:
    """Best-effort spec/rubric dir lookup (falls back to legacy rubric dir)."""
    try:
        from atoms_vs_ashes.runprofile import parse_run_profile

        profile, _ = parse_run_profile(profile_path)
        return Path(profile.spec_dir)
    except Exception:
        return Path("config/scoring_rubrics")


def _start_command(run_id: str, cmd: list[str]) -> RunHandle:
    root = _runs_root()
    hb = root / f"{run_id}.heartbeat.jsonl"
    cancel = root / f"{run_id}.cancel"
    log = root / f"{run_id}.log"
    cmd = cmd + ["--heartbeat-path", str(hb), "--cancel-flag", str(cancel)]
    log_fh = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    return RunHandle(
        run_id=run_id,
        cmd=cmd,
        pid=proc.pid,
        heartbeat_path=hb,
        cancel_flag_path=cancel,
        log_path=log,
    )


def cancel_run(handle: RunHandle) -> None:
    """Touch the sentinel file so the engine cancels at its next safe point."""
    handle.cancel_flag_path.parent.mkdir(parents=True, exist_ok=True)
    handle.cancel_flag_path.write_text("cancel", encoding="utf-8")


def kill_run(handle: RunHandle) -> None:
    """Send SIGTERM as a hard fallback when the cooperative cancel times out."""
    if handle.pid is None:
        return
    try:
        os.killpg(os.getpgid(handle.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass


def read_heartbeat(handle: RunHandle, *, tail: int = 200) -> list[dict[str, Any]]:
    """Read the last ``tail`` heartbeat ticks emitted by the child process."""
    if not handle.heartbeat_path.is_file():
        return []
    out: list[dict[str, Any]] = []
    with open(handle.heartbeat_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out[-tail:]


def read_log_tail(handle: RunHandle, *, max_bytes: int = 4096) -> str:
    """Tail the child's stdout/stderr for inline error display."""
    if not handle.log_path.is_file():
        return ""
    size = handle.log_path.stat().st_size
    with open(handle.log_path, "rb") as fh:
        if size > max_bytes:
            fh.seek(size - max_bytes)
        return fh.read().decode("utf-8", errors="replace")


__all__ = [
    "RunHandle",
    "cancel_run",
    "kill_run",
    "read_heartbeat",
    "read_log_tail",
    "start_score_run",
    "start_sensitivity_run",
]
