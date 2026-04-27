# man_hours: 1.5
"""Subprocess driver for the GUI's start/stop scoring + sensitivity buttons.

We deliberately spawn the existing ``score`` CLI in a child process
(rather than calling :func:`run_scoring` in-thread) so cancellation is
trivial: the GUI writes the sentinel file via the
``FileWatchedCancellationToken`` protocol the engine already polls
(plan §7). The Streamlit page only consumes the heartbeat JSONL the
child appends to disk, leaving the engine code untouched.

Profile transport
=================
The engine still consumes a YAML run profile. The GUI keeps the live
profile in the ``active_run_profile`` DB row (alembic 039); on each
run-launch we serialise that row to
``audit/.runtime/active_profile.<run_id>.yaml`` and pass the path to
``score run --profile``. Stale transients (older than 24h) are pruned
on every launch so the directory stays tidy.
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

import yaml

from atoms_vs_ashes.db.active_profile import load_active_profile
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.runprofile.schema import RunProfile

_RUNTIME_DIR = Path("audit/.runtime")
_RUNTIME_PROFILE_PREFIX = "active_profile."
_RUNTIME_PROFILE_SUFFIX = ".yaml"
_RUNTIME_TTL_SECONDS = 24 * 60 * 60


@dataclass
class RunHandle:
    """One running CLI invocation tracked by the GUI."""

    run_id: str
    cmd: list[str]
    pid: int | None
    heartbeat_path: Path
    cancel_flag_path: Path
    log_path: Path
    profile_path: Path | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    returncode: int | None = None
    proc: subprocess.Popen | None = field(default=None, repr=False, compare=False)

    def _mark_finished(self, rc: int | None = None) -> None:
        if rc is not None:
            self.returncode = rc
        if self.finished_at is None:
            self.finished_at = time.time()

    def is_running(self) -> bool:
        if self.pid is None or self.returncode is not None:
            return False
        if self.proc is not None:
            rc = self.proc.poll()
            if rc is not None:
                self._mark_finished(rc)
                return False
            return True
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            self._mark_finished()
            return False
        except PermissionError:
            return True
        return True


def _runs_root() -> Path:
    root = Path(".cursor/.atoms_runs")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _runtime_root() -> Path:
    _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return _RUNTIME_DIR


def _new_run_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _load_active_profile() -> RunProfile:
    """Pull the live :class:`RunProfile` from the DB singleton row."""
    with session_scope() as session:
        return load_active_profile(session)


def export_active_profile_to_yaml(
    run_id: str,
    *,
    profile: RunProfile | None = None,
    runtime_dir: Path | None = None,
) -> Path:
    """Serialise the active DB profile to a per-run YAML the engine can read.

    ``profile`` may be passed in for tests; in normal use the runner
    pulls the row from the DB itself. Returns the path to the written
    YAML — caller is responsible for treating it as transient.
    """
    p = profile if profile is not None else _load_active_profile()
    target_dir = runtime_dir if runtime_dir is not None else _runtime_root()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{_RUNTIME_PROFILE_PREFIX}{run_id}{_RUNTIME_PROFILE_SUFFIX}"
    payload = p.model_dump(mode="json")
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def cleanup_stale_runtime_profiles(
    *,
    runtime_dir: Path | None = None,
    ttl_seconds: float = _RUNTIME_TTL_SECONDS,
    keep_run_ids: Iterable[str] = (),
) -> list[Path]:
    """Delete transient ``active_profile.*.yaml`` files older than ``ttl_seconds``.

    Returns the list of removed paths. ``keep_run_ids`` always survives
    regardless of age (so an in-flight run keeps its YAML).
    """
    target_dir = runtime_dir if runtime_dir is not None else _RUNTIME_DIR
    if not target_dir.is_dir():
        return []
    keep = {str(rid) for rid in keep_run_ids}
    now = time.time()
    removed: list[Path] = []
    for entry in target_dir.glob(f"{_RUNTIME_PROFILE_PREFIX}*{_RUNTIME_PROFILE_SUFFIX}"):
        rid = entry.name[
            len(_RUNTIME_PROFILE_PREFIX) : -len(_RUNTIME_PROFILE_SUFFIX)
        ]
        if rid in keep:
            continue
        try:
            age = now - entry.stat().st_mtime
        except OSError:
            continue
        if age >= ttl_seconds:
            try:
                entry.unlink()
                removed.append(entry)
            except OSError:
                continue
    return removed


def start_score_run(
    *,
    weight_profile: str | None = None,
    profile: RunProfile | None = None,
    keep_run_ids: Iterable[str] = (),
) -> RunHandle:
    """Launch ``score run`` against the active DB profile."""
    run_id = _new_run_id("score")
    yaml_path = export_active_profile_to_yaml(run_id, profile=profile)
    cleanup_stale_runtime_profiles(keep_run_ids={run_id, *keep_run_ids})
    weight = weight_profile or (profile or _load_active_profile()).weight_profile
    cmd = [
        sys.executable, "-m", "atoms_vs_ashes",
        "--run-id", run_id, "score", "run",
        "--weight-profile", weight,
        "--profile", str(yaml_path.resolve()),
    ]
    return _start_command(run_id, cmd, profile_path=yaml_path)


def start_sensitivity_run(
    *,
    weight_profile: str | None = None,
    profile: RunProfile | None = None,
    iterations: int | None = None,
    include: Iterable[str] = ("weights", "mc", "country"),
    seed: int | None = None,
    audit_dir: str | None = None,
    no_progress: bool = True,
    keep_run_ids: Iterable[str] = (),
) -> RunHandle:
    """Launch ``score sensitivity`` against the active DB profile."""
    run_id = _new_run_id("sens")
    active = profile if profile is not None else _load_active_profile()
    yaml_path = export_active_profile_to_yaml(run_id, profile=active)
    cleanup_stale_runtime_profiles(keep_run_ids={run_id, *keep_run_ids})
    weight = weight_profile or active.weight_profile
    seed_val = seed if seed is not None else int(active.sensitivity.mc_seed)
    audit = audit_dir or active.output.audit_dir
    cmd = [
        sys.executable, "-m", "atoms_vs_ashes",
        "--run-id", run_id, "score", "sensitivity",
        "--weight-profile-base", weight,
        "--rubric-dir", str(Path(active.spec_dir)),
        "--audit-dir", audit, "--seed", str(seed_val),
        "--profile", str(yaml_path.resolve()),
    ]
    if iterations is not None:
        cmd += ["--mc-draws", str(iterations)]
    for stage in include:
        cmd += ["--include", stage]
    if no_progress:
        cmd += ["--no-progress"]
    return _start_command(run_id, cmd, profile_path=yaml_path)


def _start_command(
    run_id: str,
    cmd: list[str],
    *,
    profile_path: Path | None = None,
) -> RunHandle:
    root = _runs_root()
    hb = root / f"{run_id}.heartbeat.jsonl"
    cancel = root / f"{run_id}.cancel"
    log = root / f"{run_id}.log"
    cmd = cmd + ["--heartbeat-path", str(hb), "--cancel-flag", str(cancel)]
    log_fh = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd, stdout=log_fh, stderr=subprocess.STDOUT, start_new_session=True,
    )
    return RunHandle(
        run_id=run_id, cmd=cmd, pid=proc.pid, heartbeat_path=hb,
        cancel_flag_path=cancel, log_path=log,
        profile_path=profile_path, proc=proc,
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
    "RunHandle", "cancel_run", "cleanup_stale_runtime_profiles",
    "export_active_profile_to_yaml", "kill_run", "read_heartbeat",
    "read_log_tail", "start_score_run", "start_sensitivity_run",
]
