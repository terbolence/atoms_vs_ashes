# man_hours: 0.5
"""Heartbeat writer behaviour: throttling, ETA, JSONL format."""

from __future__ import annotations

import json
from pathlib import Path

from atoms_vs_ashes.runtime.heartbeat import HeartbeatRecord, HeartbeatWriter


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_record_serialises_fields() -> None:
    rec = HeartbeatRecord(stage="scoring", processed=10, total=100, eta_s=5.5)
    payload = json.loads(rec.to_json())
    assert payload["stage"] == "scoring"
    assert payload["processed"] == 10
    assert payload["total"] == 100
    assert payload["eta_s"] == 5.5
    assert payload["ts"].endswith("Z")


def test_no_path_writer_is_no_op(tmp_path: Path) -> None:
    with HeartbeatWriter(None) as hb:
        hb.start_stage("scoring", total=1)
        hb.tick("scoring", processed=1, total=1, force=True)
    assert list(tmp_path.iterdir()) == []


def test_throttle_respects_min_interval(tmp_path: Path) -> None:
    clock = _FakeClock()
    path = tmp_path / "hb.jsonl"
    with HeartbeatWriter(path, min_interval_s=1.0, clock=clock) as hb:
        hb.start_stage("scoring", total=10)
        hb.tick("scoring", processed=1, total=10)
        clock.advance(0.5)
        hb.tick("scoring", processed=2, total=10)
        clock.advance(0.6)
        hb.tick("scoring", processed=3, total=10)
        hb.end_stage("scoring", processed=10, total=10)
    rows = _read(path)
    processed = [r["processed"] for r in rows]
    assert processed[0] == 0
    assert 3 in processed
    assert 2 not in processed
    assert processed[-1] == 10


def test_eta_increases_then_collapses(tmp_path: Path) -> None:
    clock = _FakeClock()
    path = tmp_path / "hb.jsonl"
    with HeartbeatWriter(path, min_interval_s=0.0, clock=clock) as hb:
        hb.start_stage("scoring", total=10)
        clock.advance(2.0)
        hb.tick("scoring", processed=2, total=10)
        clock.advance(2.0)
        hb.tick("scoring", processed=10, total=10, force=True)
    rows = _read(path)
    eta_values = [r["eta_s"] for r in rows if r["processed"] in (2, 10)]
    assert eta_values[0] is not None and eta_values[0] > 0
    assert eta_values[-1] == 0


def test_force_bypasses_throttle(tmp_path: Path) -> None:
    clock = _FakeClock()
    path = tmp_path / "hb.jsonl"
    with HeartbeatWriter(path, min_interval_s=10.0, clock=clock) as hb:
        hb.start_stage("scoring", total=10)
        hb.tick("scoring", processed=1, total=10)
        hb.tick("scoring", processed=2, total=10, force=True)
    processed = [r["processed"] for r in _read(path)]
    assert 2 in processed
