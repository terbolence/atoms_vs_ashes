# man_hours: 0.5
"""Unit tests for the streamlit-free metrics loader helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path

from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    discover_metrics_files,
    load_metrics_file,
    pick_metrics_file,
)


def _write_metrics(path: Path, *, run_id: str = "r1") -> None:
    payload = {
        "run_id": run_id,
        "summary": {"total_pairs": 12, "survived": 7},
        "per_country": [{"country_code": "RO", "n_pairs": 4, "survived": 3}],
        "per_criterion": [{"criterion_id": "NH-02"}],
        "per_smr": [{"smr_key": "nuscale_voygr6"}],
        "top_n_per_country": [{"country_code": "RO", "rank": 1}],
        "per_country_margins": [],
        "near_miss": {"gap_threshold_pct": 10.0, "rows": []},
        "sensitivity": {"mc": None},
        "per_pair_failures": [],
        "provenance": {"profile_path": "config/run_profiles/baseline.yaml"},
        "multi_failure_histogram": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_discover_metrics_files_returns_newest_first(tmp_path: Path) -> None:
    older = tmp_path / "20260101_metrics.json"
    newer = tmp_path / "20260201_metrics.json"
    _write_metrics(older)
    time.sleep(0.01)
    _write_metrics(newer)
    files = discover_metrics_files(tmp_path)
    assert [p.name for p in files] == [newer.name, older.name]


def test_discover_metrics_files_handles_missing_dir(tmp_path: Path) -> None:
    assert discover_metrics_files(tmp_path / "nope") == []


def test_load_metrics_file_returns_typed_panels(tmp_path: Path) -> None:
    p = tmp_path / "x_metrics.json"
    _write_metrics(p, run_id="abc")
    loaded = load_metrics_file(p)
    assert isinstance(loaded, LoadedMetrics)
    assert loaded.summary["total_pairs"] == 12
    assert loaded.per_country[0]["country_code"] == "RO"
    assert loaded.per_criterion[0]["criterion_id"] == "NH-02"
    assert loaded.top_n[0]["rank"] == 1
    assert loaded.near_miss["gap_threshold_pct"] == 10.0
    assert loaded.sensitivity == {"mc": None}
    assert loaded.provenance["profile_path"].endswith(".yaml")


def test_pick_metrics_file_returns_none_when_empty(tmp_path: Path) -> None:
    assert pick_metrics_file(tmp_path) is None


def test_pick_metrics_file_returns_newest(tmp_path: Path) -> None:
    a = tmp_path / "20260101_metrics.json"
    b = tmp_path / "20260202_metrics.json"
    _write_metrics(a)
    time.sleep(0.01)
    _write_metrics(b)
    assert pick_metrics_file(tmp_path) == b
