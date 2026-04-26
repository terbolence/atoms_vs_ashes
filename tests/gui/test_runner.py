# man_hours: 0.5
"""Unit tests for the GUI subprocess runner contract."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from atoms_vs_ashes.gui import _runner
from atoms_vs_ashes.gui._runner import (
    RunHandle,
    cancel_run,
    read_heartbeat,
    read_log_tail,
)


def _make_handle(tmp_path: Path) -> RunHandle:
    hb = tmp_path / "hb.jsonl"
    cancel = tmp_path / "cancel"
    log = tmp_path / "log.txt"
    return RunHandle(
        run_id="run-x", cmd=["echo"], pid=os.getpid(),
        heartbeat_path=hb, cancel_flag_path=cancel, log_path=log,
    )


def test_read_heartbeat_handles_missing_file(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    assert read_heartbeat(handle) == []


def test_read_heartbeat_parses_jsonl_and_skips_garbage(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    handle.heartbeat_path.write_text(
        json.dumps({"phase": "score", "done": 1, "total": 10, "progress": 0.1}) + "\n"
        "not json\n"
        + json.dumps({"phase": "score", "done": 5, "total": 10, "progress": 0.5}) + "\n"
    )
    ticks = read_heartbeat(handle)
    assert [t["done"] for t in ticks] == [1, 5]


def test_read_heartbeat_tail_limits_rows(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    lines = [json.dumps({"i": i}) for i in range(50)]
    handle.heartbeat_path.write_text("\n".join(lines) + "\n")
    ticks = read_heartbeat(handle, tail=5)
    assert [t["i"] for t in ticks] == [45, 46, 47, 48, 49]


def test_read_log_tail_returns_last_bytes(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    handle.log_path.write_text("a" * 100 + "TAIL")
    out = read_log_tail(handle, max_bytes=4)
    assert out == "TAIL"


def test_cancel_run_writes_sentinel(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    cancel_run(handle)
    assert handle.cancel_flag_path.is_file()
    assert handle.cancel_flag_path.read_text() == "cancel"


def test_handle_running_check_uses_pid(tmp_path: Path) -> None:
    handle = _make_handle(tmp_path)
    assert handle.is_running() is True
    handle.pid = None
    assert handle.is_running() is False


def test_resolve_spec_dir_falls_back_for_invalid_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "broken.yaml"
    bad.write_text("not: a profile\n")
    assert _runner._resolve_spec_dir(bad) == Path("config/scoring_rubrics")


def test_resolve_spec_dir_uses_profile_field(tmp_path: Path) -> None:
    yaml_path = tmp_path / "p.yaml"
    yaml_path.write_text("run_label: t\nspec_dir: config/scoring_specs\n")
    assert _runner._resolve_spec_dir(yaml_path) == Path("config/scoring_specs")


def test_new_run_id_is_unique() -> None:
    a = _runner._new_run_id("score")
    b = _runner._new_run_id("score")
    assert a != b
    assert a.startswith("score-")


def test_runs_root_creates_directory(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = _runner._runs_root()
    assert root.is_dir()
    assert root == Path(".cursor/.atoms_runs")
