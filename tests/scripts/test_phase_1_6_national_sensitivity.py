# man_hours: 0.8
"""Smoke tests for Phase 1.6 national sensitivity script wiring."""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

import pytest

from scripts import run_phase_1_6_sensitivity as phase16
from scripts._phase_1_6_driver_stages import run_national_from_args


def test_parse_args_exposes_national_flags(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_phase_1_6_sensitivity.py",
            "--skip-national",
            "--national-mc-rank-draws",
            "25",
            "--min-national-pairs",
            "4",
        ],
    )
    args = phase16._parse_args()
    assert args.skip_national is True
    assert args.national_mc_rank_draws == 25
    assert args.min_national_pairs == 4


def test_run_national_rejects_invalid_draws(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sys, "argv", ["run_phase_1_6_sensitivity.py"])
    args = phase16._parse_args()
    args.skip_national = False
    args.national_mc_rank_draws = 0
    args.mc_stages = [10]
    args.min_national_pairs = 3
    with pytest.raises(ValueError, match="national-mc-rank-draws"):
        run_national_from_args(args, tmp_path, "20260516", "sens-test")


def test_migration_revision_order() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "src/alembic/versions/046_national_sensitivity_rankings.py"
    )
    spec = importlib.util.spec_from_file_location("rev046", path)
    assert spec is not None and spec.loader is not None
    rev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rev)
    assert rev.revision == "046"
    assert rev.down_revision == "045"
