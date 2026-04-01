# man_hours: 5.0
"""Tests for BF-02 Land Area screening check."""

from __future__ import annotations

import json

import pytest

from atoms_vs_ashes.screening.land_area import evaluate_site

# Sorted ascending by land_ha — mirrors config/default.yml
SMR_LAND_THRESHOLDS: list[tuple[str, str, float]] = [
    ("oklo_aurora", "Oklo Aurora", 22),
    ("bwrx_300", "GE Hitachi BWRX-300", 25.3),
    ("xe_100", "X-energy Xe-100", 31),
    ("holtec_smr300", "Holtec SMR-300", 38),
    ("rolls_royce_smr", "Rolls-Royce SMR", 44.5),
    ("natrium_nominal", "TerraPower Natrium (nominal)", 51),
    ("natrium_peak", "TerraPower Natrium (peak)", 51),
    ("nuscale_voygr6", "NuScale VOYGR-6", 72.8),
]

ALL_KEYS = [s[0] for s in SMR_LAND_THRESHOLDS]


# ---------------------------------------------------------------------------
# Boundary tests — every land threshold edge
# ---------------------------------------------------------------------------


class TestEvaluateSiteBoundaries:
    """Verify pass/fail at every land-area boundary."""

    def test_none_is_inconclusive(self):
        verdict, val, _ = evaluate_site(None, SMR_LAND_THRESHOLDS)
        assert verdict == "inconclusive"
        assert val["site_area_ha"] is None

    def test_zero_ha_fails(self):
        verdict, val, _ = evaluate_site(0, SMR_LAND_THRESHOLDS)
        assert verdict == "fail"
        assert val["compatible"] == []
        assert set(val["incompatible"]) == set(ALL_KEYS)

    def test_below_smallest_smr(self):
        verdict, _, _ = evaluate_site(21.9, SMR_LAND_THRESHOLDS)
        assert verdict == "fail"

    def test_exactly_smallest_smr(self):
        verdict, val, _ = evaluate_site(22, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "oklo_aurora" in val["compatible"]
        assert "bwrx_300" in val["incompatible"]

    def test_at_25_3_ha(self):
        verdict, val, _ = evaluate_site(25.3, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == {"oklo_aurora", "bwrx_300"}

    def test_at_31_ha(self):
        verdict, val, _ = evaluate_site(31, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == {"oklo_aurora", "bwrx_300", "xe_100"}

    def test_at_37_9_ha(self):
        verdict, val, _ = evaluate_site(37.9, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "holtec_smr300" not in val["compatible"]

    def test_at_38_ha(self):
        verdict, val, _ = evaluate_site(38, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "holtec_smr300" in val["compatible"]
        assert "rolls_royce_smr" not in val["compatible"]

    def test_at_44_5_ha(self):
        verdict, val, _ = evaluate_site(44.5, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "rolls_royce_smr" in val["compatible"]
        assert "natrium_nominal" not in val["compatible"]

    def test_at_50_9_ha(self):
        verdict, val, _ = evaluate_site(50.9, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "natrium_nominal" not in val["compatible"]

    def test_at_51_ha(self):
        """Both Natrium configurations share the same 51 ha footprint."""
        verdict, val, _ = evaluate_site(51, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "natrium_nominal" in val["compatible"]
        assert "natrium_peak" in val["compatible"]
        assert "nuscale_voygr6" not in val["compatible"]

    def test_at_72_7_ha(self):
        verdict, val, _ = evaluate_site(72.7, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert "nuscale_voygr6" not in val["compatible"]

    def test_at_72_8_ha(self):
        """Reference SMR threshold."""
        verdict, val, _ = evaluate_site(72.8, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == set(ALL_KEYS)

    def test_large_area(self):
        verdict, val, _ = evaluate_site(200, SMR_LAND_THRESHOLDS)
        assert verdict == "pass"
        assert set(val["compatible"]) == set(ALL_KEYS)
        assert val["incompatible"] == []


# ---------------------------------------------------------------------------
# Justification text quality
# ---------------------------------------------------------------------------


class TestJustificationText:
    def test_fail_mentions_minimum(self):
        _, _, just = evaluate_site(10, SMR_LAND_THRESHOLDS)
        assert "below" in just.lower()
        assert "Oklo Aurora" in just

    def test_all_pass_mentions_all(self):
        _, _, just = evaluate_site(100, SMR_LAND_THRESHOLDS)
        assert "all" in just.lower()

    def test_partial_lists_compatible(self):
        _, _, just = evaluate_site(40, SMR_LAND_THRESHOLDS)
        assert "4 of 8" in just
        assert "Holtec" in just

    def test_inconclusive_mentions_no_data(self):
        _, _, just = evaluate_site(None, SMR_LAND_THRESHOLDS)
        assert "no" in just.lower() or "No" in just


# ---------------------------------------------------------------------------
# Value dict structure
# ---------------------------------------------------------------------------


class TestValueStructure:
    def test_value_dict_keys(self):
        _, val, _ = evaluate_site(40, SMR_LAND_THRESHOLDS)
        assert "site_area_ha" in val
        assert "compatible" in val
        assert "incompatible" in val
        assert isinstance(val["compatible"], list)
        assert isinstance(val["incompatible"], list)

    def test_compatible_incompatible_partition(self):
        """Every SMR key must appear in exactly one list."""
        _, val, _ = evaluate_site(40, SMR_LAND_THRESHOLDS)
        all_returned = set(val["compatible"]) | set(val["incompatible"])
        assert all_returned == set(ALL_KEYS)
        assert not set(val["compatible"]) & set(val["incompatible"])

    def test_area_preserved_in_value(self):
        _, val, _ = evaluate_site(55.5, SMR_LAND_THRESHOLDS)
        assert val["site_area_ha"] == 55.5
