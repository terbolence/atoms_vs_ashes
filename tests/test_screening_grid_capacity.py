# man_hours: 5.0
"""Tests for BF-01 Grid Capacity screening check."""

from __future__ import annotations

import json

import pytest

from atoms_vs_ashes.screening.grid_capacity import evaluate_site

# Sorted ascending by MWe — mirrors config/default.yml
SMR_THRESHOLDS: list[tuple[str, str, float]] = [
    ("oklo_aurora", "Oklo Aurora", 75),
    ("xe_100", "X-energy Xe-100", 80),
    ("bwrx_300", "GE Hitachi BWRX-300", 300),
    ("holtec_smr300", "Holtec SMR-300", 300),
    ("natrium_nominal", "TerraPower Natrium (nominal)", 345),
    ("nuscale_voygr6", "NuScale VOYGR-6", 462),
    ("rolls_royce_smr", "Rolls-Royce SMR", 470),
    ("natrium_peak", "TerraPower Natrium (peak)", 500),
]

ALL_KEYS = [s[0] for s in SMR_THRESHOLDS]


# ---------------------------------------------------------------------------
# Boundary tests — every MWe threshold edge
# ---------------------------------------------------------------------------


class TestEvaluateSiteBoundaries:
    """Verify pass/fail at every capacity boundary."""

    def test_none_is_inconclusive(self):
        verdict, val, _ = evaluate_site(None, SMR_THRESHOLDS)
        assert verdict == "inconclusive"
        assert val["site_capacity_mw"] is None

    def test_zero_mw_fails(self):
        verdict, val, _ = evaluate_site(0, SMR_THRESHOLDS)
        assert verdict == "fail"
        assert val["compatible"] == []
        assert set(val["incompatible"]) == set(ALL_KEYS)

    def test_below_smallest_smr(self):
        verdict, val, _ = evaluate_site(74, SMR_THRESHOLDS)
        assert verdict == "fail"

    def test_exactly_smallest_smr(self):
        verdict, val, _ = evaluate_site(75, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "oklo_aurora" in val["compatible"]
        assert "xe_100" in val["incompatible"]

    def test_at_80_mwe(self):
        verdict, val, _ = evaluate_site(80, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == {"oklo_aurora", "xe_100"}

    def test_at_299_mwe(self):
        verdict, val, _ = evaluate_site(299, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == {"oklo_aurora", "xe_100"}

    def test_at_300_mwe(self):
        verdict, val, _ = evaluate_site(300, SMR_THRESHOLDS)
        assert verdict == "pass"
        compat = set(val["compatible"])
        assert {"oklo_aurora", "xe_100", "bwrx_300", "holtec_smr300"} == compat

    def test_at_344_mwe(self):
        verdict, val, _ = evaluate_site(344, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "natrium_nominal" not in val["compatible"]

    def test_at_345_mwe(self):
        verdict, val, _ = evaluate_site(345, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "natrium_nominal" in val["compatible"]
        assert "nuscale_voygr6" not in val["compatible"]

    def test_at_461_mwe(self):
        verdict, val, _ = evaluate_site(461, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "nuscale_voygr6" not in val["compatible"]

    def test_at_462_mwe(self):
        """Reference SMR threshold."""
        verdict, val, _ = evaluate_site(462, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "nuscale_voygr6" in val["compatible"]
        assert "rolls_royce_smr" not in val["compatible"]

    def test_at_470_mwe(self):
        verdict, val, _ = evaluate_site(470, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "rolls_royce_smr" in val["compatible"]
        assert "natrium_peak" not in val["compatible"]

    def test_at_499_mwe(self):
        verdict, val, _ = evaluate_site(499, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert "natrium_peak" not in val["compatible"]

    def test_at_500_mwe(self):
        verdict, val, _ = evaluate_site(500, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == set(ALL_KEYS)

    def test_large_capacity(self):
        verdict, val, _ = evaluate_site(1000, SMR_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == set(ALL_KEYS)
        assert val["incompatible"] == []


# ---------------------------------------------------------------------------
# Justification text quality
# ---------------------------------------------------------------------------


class TestJustificationText:
    def test_fail_mentions_minimum(self):
        _, _, just = evaluate_site(50, SMR_THRESHOLDS)
        assert "below" in just.lower()
        assert "Oklo Aurora" in just

    def test_all_pass_mentions_all(self):
        _, _, just = evaluate_site(600, SMR_THRESHOLDS)
        assert "all" in just.lower()

    def test_partial_lists_compatible(self):
        _, _, just = evaluate_site(350, SMR_THRESHOLDS)
        assert "5 of 8" in just
        assert "NuScale" in just

    def test_inconclusive_mentions_no_data(self):
        _, _, just = evaluate_site(None, SMR_THRESHOLDS)
        assert "no" in just.lower() or "No" in just


# ---------------------------------------------------------------------------
# Kairos / Hermes must never appear
# ---------------------------------------------------------------------------


class TestKairosExclusion:
    """Verify that the Hermes test reactor is not in the SMR list."""

    def test_no_kairos_in_thresholds(self):
        keys = [k for k, _, _ in SMR_THRESHOLDS]
        assert "kairos" not in " ".join(keys).lower()
        assert "hermes" not in " ".join(keys).lower()

    def test_no_kairos_in_results(self):
        _, val, just = evaluate_site(1000, SMR_THRESHOLDS)
        combined = json.dumps(val) + just
        assert "kairos" not in combined.lower()
        assert "hermes" not in combined.lower()


# ---------------------------------------------------------------------------
# Value dict structure
# ---------------------------------------------------------------------------


class TestValueStructure:
    def test_value_dict_keys(self):
        _, val, _ = evaluate_site(400, SMR_THRESHOLDS)
        assert "site_capacity_mw" in val
        assert "compatible" in val
        assert "incompatible" in val
        assert isinstance(val["compatible"], list)
        assert isinstance(val["incompatible"], list)

    def test_compatible_incompatible_partition(self):
        """Every SMR key must appear in exactly one list."""
        _, val, _ = evaluate_site(350, SMR_THRESHOLDS)
        all_returned = set(val["compatible"]) | set(val["incompatible"])
        assert all_returned == set(ALL_KEYS)
        assert not set(val["compatible"]) & set(val["incompatible"])
