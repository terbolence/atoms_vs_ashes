# man_hours: 0.5
"""Tests for :mod:`atoms_vs_ashes.db.threshold_overrides` merge behaviour."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from atoms_vs_ashes.db import threshold_overrides as tro


def test_merge_db_replaces_scalar(monkeypatch: pytest.MonkeyPatch) -> None:
    row = SimpleNamespace(
        criterion_id="NH-02", code="E1", smr_key="", value=8.0
    )
    monkeypatch.setattr(tro, "fetch_all_rows", lambda _s: [row])
    out = tro.merge_db_over_yaml({"NH-02": {"E1": 5.0}}, object())
    assert out["NH-02"]["E1"] == 8.0


def test_merge_db_per_smr_merges_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    row = SimpleNamespace(
        criterion_id="BF-01",
        code="B1",
        smr_key="nuscale_voygr6",
        value=500.0,
    )
    monkeypatch.setattr(tro, "fetch_all_rows", lambda _s: [row])
    base: dict = {"BF-01": {"B1": 462.0}}
    out = tro.merge_db_over_yaml(base, object())
    assert out["BF-01"]["B1"] == {"": 462.0, "nuscale_voygr6": 500.0}
