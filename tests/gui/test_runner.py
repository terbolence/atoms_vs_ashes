# man_hours: 1.8
"""Unit tests for the GUI subprocess runner contract.

Covers the heartbeat/log helpers (unchanged) and the DB→YAML profile
export plus runtime cleanup added when the GUI moved to the
``active_run_profile`` DB row (alembic 039).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
import yaml

from atoms_vs_ashes.gui import _runner
from atoms_vs_ashes.gui._runner import (
    RunHandle,
    cancel_run,
    cleanup_stale_runtime_profiles,
    export_active_profile_to_yaml,
    read_heartbeat,
    read_log_tail,
    start_sensitivity_run,
)
from atoms_vs_ashes.gui._runner_national import start_national_sensitivity_run
from atoms_vs_ashes.gui import _runner_national
from atoms_vs_ashes.runprofile.schema import RunProfile, ScopeBlock


def _make_handle(tmp_path: Path) -> RunHandle:
    hb = tmp_path / "hb.jsonl"
    cancel = tmp_path / "cancel"
    log = tmp_path / "log.txt"
    return RunHandle(
        run_id="run-x",
        cmd=["echo"],
        pid=os.getpid(),
        heartbeat_path=hb,
        cancel_flag_path=cancel,
        log_path=log,
    )


def _profile_for_test(smr_keys: list[str] | None = None) -> RunProfile:
    return RunProfile(
        run_label="ro_focus_test",
        scope=ScopeBlock(
            countries=["RO"],
            smr_keys=["nuscale_voygr6"] if smr_keys is None else smr_keys,
        ),
        notes="from test_runner",
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


def test_new_run_id_is_unique() -> None:
    a = _runner._new_run_id("score")
    b = _runner._new_run_id("score")
    assert a != b
    assert a.startswith("score-")


def test_runs_root_creates_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = _runner._runs_root()
    assert root.is_dir()
    assert root == Path(".cursor/.atoms_runs")


def test_export_active_profile_writes_round_trippable_yaml(tmp_path: Path) -> None:
    profile = _profile_for_test()
    path = export_active_profile_to_yaml(
        "score-deadbeef", profile=profile, runtime_dir=tmp_path
    )
    assert path.is_file()
    assert path.name == "active_profile.score-deadbeef.yaml"
    payload = yaml.safe_load(path.read_text())
    reloaded = RunProfile.model_validate(payload)
    assert reloaded.run_label == "ro_focus_test"
    assert reloaded.scope.countries == ["RO"]
    assert reloaded.notes == "from test_runner"


def test_cleanup_removes_stale_files_but_keeps_active_runs(tmp_path: Path) -> None:
    fresh = export_active_profile_to_yaml(
        "score-fresh", profile=_profile_for_test(), runtime_dir=tmp_path
    )
    stale = tmp_path / "active_profile.score-stale.yaml"
    stale.write_text("placeholder")
    very_old = time.time() - 25 * 3600
    os.utime(stale, (very_old, very_old))
    in_flight = tmp_path / "active_profile.score-inflight.yaml"
    in_flight.write_text("placeholder")
    os.utime(in_flight, (very_old, very_old))

    removed = cleanup_stale_runtime_profiles(
        runtime_dir=tmp_path,
        keep_run_ids={"score-inflight"},
    )
    assert stale not in [p for p in tmp_path.iterdir()]
    assert in_flight in list(tmp_path.iterdir())
    assert fresh in list(tmp_path.iterdir())
    assert {p.name for p in removed} == {"active_profile.score-stale.yaml"}


def test_cleanup_skips_when_directory_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert cleanup_stale_runtime_profiles(runtime_dir=missing) == []


def test_national_sensitivity_runner_uses_separate_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, list[str]] = {}

    def fake_start(run_id, cmd, profile_path=None):
        captured["cmd"] = cmd
        return RunHandle(
            run_id=run_id,
            cmd=cmd,
            pid=None,
            heartbeat_path=tmp_path / "hb.jsonl",
            cancel_flag_path=tmp_path / "cancel",
            log_path=tmp_path / "log",
            profile_path=profile_path,
        )

    monkeypatch.setattr(_runner, "_start_command", fake_start)
    monkeypatch.setattr(_runner_national, "_start_command", fake_start)
    start_national_sensitivity_run(
        profile=_profile_for_test(),
        mc_rank_draws=1234,
        min_pairs=4,
        seed=99,
        audit_dir="audit/out",
    )

    cmd = captured["cmd"]
    assert cmd[cmd.index("score") + 1] == "national-sensitivity"
    assert "--mc-rank-draws" in cmd
    assert cmd[cmd.index("--mc-rank-draws") + 1] == "1234"
    assert "--min-pairs" in cmd
    assert cmd[cmd.index("--min-pairs") + 1] == "4"
    assert "--smr-key" in cmd
    assert cmd[cmd.index("--smr-key") + 1] == "nuscale_voygr6"


def test_national_sensitivity_runner_requires_one_profile_smr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="single-SMR"):
        start_national_sensitivity_run(profile=_profile_for_test(smr_keys=[]))

    with pytest.raises(ValueError, match="single-SMR"):
        start_national_sensitivity_run(
            profile=_profile_for_test(smr_keys=["a", "b"])
        )


def test_regional_sensitivity_runner_does_not_receive_national_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, list[str]] = {}

    def fake_start(run_id, cmd, profile_path=None):
        captured["cmd"] = cmd
        return RunHandle(
            run_id=run_id,
            cmd=cmd,
            pid=None,
            heartbeat_path=tmp_path / "hb.jsonl",
            cancel_flag_path=tmp_path / "cancel",
            log_path=tmp_path / "log",
            profile_path=profile_path,
        )

    monkeypatch.setattr(_runner, "_start_command", fake_start)
    start_sensitivity_run(profile=_profile_for_test(), iterations=1000)

    cmd = captured["cmd"]
    assert cmd[cmd.index("score") + 1] == "sensitivity"
    assert "--mc-rank-draws" not in cmd
    assert "--min-pairs" not in cmd
