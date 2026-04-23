# man_hours: 2.0
"""Tests for ESA WorldCover connector — parsing, metrics, and crosswalk logic.

Covers:
- Buildable area computation from fixture ring data
- ESA → CORINE class crosswalk
- Dominant class extraction
- Favourable/moderate/unfavourable percentage calculation
- Non-EU country detection
- Tile name computation
- Edge cases and boundary conditions
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.worldcover.client import WorldCoverConnector
from atoms_vs_ashes.connectors.worldcover.models import (
    DEVELOPABLE_ESA,
    ESA_CLASS_LABELS,
    ESA_TO_CLC_APPROX,
    FAVOURABLE_ESA,
    MODERATE_ESA,
    NON_EU_COUNTRIES,
    UNFAVOURABLE_ESA,
    RingLandCover,
    WorldCoverResult,
)
from atoms_vs_ashes.connectors.worldcover.parsers import (
    NUCLEAR_ISLAND_HA,
    VOYGR6_FOOTPRINT_HA,
    assess_buildable_adequacy,
    build_ns04_comment,
    compute_buildable_metrics,
    is_non_eu,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_result(
    rings: list[RingLandCover] | None = None,
    error: str | None = None,
) -> WorldCoverResult:
    r = WorldCoverResult(lat=41.37, lon=19.43, error=error)
    if rings:
        r.rings = rings
        r.total_developable_ha = sum(ring.developable_ha for ring in rings)
    return r


def _make_ring(
    label: str,
    inner_m: float,
    outer_m: float,
    by_class: dict[int, float],
    developable_ha: float = 0.0,
) -> RingLandCover:
    return RingLandCover(
        label=label,
        inner_m=inner_m,
        outer_m=outer_m,
        total_area_ha=sum(by_class.values()),
        by_class=by_class,
        developable_ha=developable_ha,
    )


# Typical Turkish site: cropland + built-up + some forest
RING_0_500 = _make_ring(
    "0-500m", 0, 500,
    by_class={40: 25.0, 50: 20.0, 10: 15.0, 30: 10.0},
    developable_ha=55.0,
)
RING_500_1K = _make_ring(
    "500m-1km", 500, 1000,
    by_class={40: 80.0, 30: 30.0, 10: 20.0, 50: 10.0},
    developable_ha=120.0,
)
RING_1K_2K = _make_ring(
    "1-2km", 1000, 2000,
    by_class={40: 200.0, 10: 100.0, 30: 50.0, 80: 20.0},
    developable_ha=250.0,
)

TYPICAL_RESULT = _make_result(rings=[RING_0_500, RING_500_1K, RING_1K_2K])


# ===================================================================
# Test classes
# ===================================================================


class TestComputeBuildableMetrics:
    """Test buildable area computation from WorldCover ring data."""

    def test_buildable_area_from_inner_rings(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        expected = RING_0_500.developable_ha + RING_500_1K.developable_ha
        assert metrics["buildable_area_ha"] == pytest.approx(expected, abs=0.01)

    def test_outer_ring_excluded(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        total_all = sum(r.developable_ha for r in TYPICAL_RESULT.rings)
        assert metrics["buildable_area_ha"] < total_all

    def test_custom_buildable_radius(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT, buildable_radius_m=500)
        assert metrics["buildable_area_ha"] == pytest.approx(
            RING_0_500.developable_ha, abs=0.01,
        )

    def test_dominant_class_is_most_prevalent(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        # 40 (Cropland): 25+80+200 = 305 ha — largest
        assert metrics["dominant_land_class"] == "211"  # CLC approx for cropland
        assert metrics["dominant_land_label"] == "Cropland"

    def test_dominant_class_pct(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        total = sum(sum(r.by_class.values()) for r in TYPICAL_RESULT.rings)
        expected_pct = (305.0 / total) * 100
        assert metrics["dominant_class_pct"] == pytest.approx(expected_pct, abs=0.5)

    def test_percentages_sum_reasonable(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        total_pct = (
            metrics["favourable_land_pct"]
            + metrics["moderate_land_pct"]
            + metrics["unfavourable_land_pct"]
        )
        assert total_pct <= 100.1

    def test_natural_seminatural_ha(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        # 10 (tree): 15+20+100=135, 30 (grass): 10+30+50=90, 80 (water): 20
        expected = 135.0 + 90.0 + 20.0
        assert metrics["natural_seminatural_ha"] == pytest.approx(expected, abs=0.01)


class TestComputeBuildableMetricsEdgeCases:
    """Edge cases for WorldCover metrics computation."""

    def test_empty_result_no_rings(self):
        r = _make_result(rings=[])
        metrics = compute_buildable_metrics(r)
        assert metrics["buildable_area_ha"] == 0.0
        assert metrics["dominant_land_class"] is None
        assert metrics["dominant_land_label"] is None

    def test_result_with_error(self):
        r = _make_result(error="Tile not found")
        metrics = compute_buildable_metrics(r)
        assert metrics["buildable_area_ha"] == 0.0

    def test_single_class_100_percent(self):
        ring = _make_ring("0-500m", 0, 500, by_class={40: 50.0}, developable_ha=50.0)
        r = _make_result(rings=[ring])
        metrics = compute_buildable_metrics(r)
        assert metrics["dominant_land_class"] == "211"
        assert metrics["dominant_class_pct"] == pytest.approx(100.0, abs=0.1)
        assert metrics["favourable_land_pct"] == pytest.approx(100.0, abs=0.1)

    def test_all_unfavourable(self):
        ring = _make_ring("0-500m", 0, 500, by_class={10: 40.0, 80: 10.0}, developable_ha=0.0)
        r = _make_result(rings=[ring])
        metrics = compute_buildable_metrics(r)
        assert metrics["unfavourable_land_pct"] == pytest.approx(100.0, abs=0.1)
        assert metrics["buildable_area_ha"] == 0.0


class TestEsaCrosswalk:
    """Test ESA → CORINE class crosswalk consistency."""

    def test_all_esa_classes_have_labels(self):
        for cls in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]:
            assert cls in ESA_CLASS_LABELS

    def test_all_esa_classes_have_clc_mapping(self):
        for cls in ESA_CLASS_LABELS:
            assert cls in ESA_TO_CLC_APPROX, f"ESA class {cls} has no CLC mapping"

    def test_favourability_sets_are_disjoint(self):
        assert FAVOURABLE_ESA & MODERATE_ESA == frozenset()
        assert FAVOURABLE_ESA & UNFAVOURABLE_ESA == frozenset()
        assert MODERATE_ESA & UNFAVOURABLE_ESA == frozenset()

    def test_all_classes_classified(self):
        all_classes = FAVOURABLE_ESA | MODERATE_ESA | UNFAVOURABLE_ESA
        for cls in ESA_CLASS_LABELS:
            assert cls in all_classes, f"ESA class {cls} not in any favourability set"


class TestTileNameComputation:
    """Test tile name computation from coordinates."""

    def test_bucharest_area(self):
        assert WorldCoverConnector.tile_name_for(44.43, 26.10) == "N42E024"

    def test_istanbul(self):
        assert WorldCoverConnector.tile_name_for(41.01, 28.97) == "N39E027"

    def test_yerevan(self):
        assert WorldCoverConnector.tile_name_for(40.18, 44.51) == "N39E042"

    def test_minsk(self):
        assert WorldCoverConnector.tile_name_for(53.15, 27.50) == "N51E027"

    def test_tile_boundary(self):
        assert WorldCoverConnector.tile_name_for(39.0, 21.0) == "N39E021"

    def test_negative_lon(self):
        assert WorldCoverConnector.tile_name_for(45.0, -3.0) == "N45W003"


class TestIsNonEu:
    """Test non-EU country detection."""

    @pytest.mark.parametrize("cc", sorted(NON_EU_COUNTRIES))
    def test_non_eu_countries(self, cc: str):
        assert is_non_eu(cc) is True

    def test_eu_countries_not_matched(self):
        for cc in ["RO", "PL", "CZ", "HU", "AT"]:
            assert is_non_eu(cc) is False

    def test_lowercase(self):
        assert is_non_eu("tr") is True
        assert is_non_eu("ro") is False


class TestAssessBuildableAdequacy:
    """Test A15 buildable area adequacy classification."""

    def test_adequate(self):
        assert assess_buildable_adequacy(100.0) == "adequate"
        assert assess_buildable_adequacy(VOYGR6_FOOTPRINT_HA) == "adequate"

    def test_marginal(self):
        assert assess_buildable_adequacy(50.0) == "marginal"
        assert assess_buildable_adequacy(NUCLEAR_ISLAND_HA) == "marginal"

    def test_insufficient(self):
        assert assess_buildable_adequacy(10.0) == "insufficient"
        assert assess_buildable_adequacy(0.0) == "insufficient"


class TestBuildNs04Comment:
    """Test human-readable comment generation."""

    def test_contains_dominant_label(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        comment = build_ns04_comment(metrics)
        assert "Cropland" in comment

    def test_contains_worldcover_source(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        comment = build_ns04_comment(metrics)
        assert "WorldCover" in comment

    def test_contains_suitability(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        comment = build_ns04_comment(metrics)
        assert "fav" in comment


class TestResultDataclassStructure:
    """Verify output dictionary shape and types."""

    def test_all_expected_keys_present(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        expected_keys = {
            "buildable_area_ha", "dominant_land_class", "dominant_land_label",
            "dominant_class_pct", "favourable_land_pct", "moderate_land_pct",
            "unfavourable_land_pct", "natural_seminatural_ha",
            "patch_count", "largest_contiguous_ha",
        }
        assert set(metrics.keys()) == expected_keys

    def test_numeric_types(self):
        metrics = compute_buildable_metrics(TYPICAL_RESULT)
        for key in ["buildable_area_ha", "dominant_class_pct",
                     "favourable_land_pct", "moderate_land_pct",
                     "unfavourable_land_pct", "natural_seminatural_ha"]:
            assert isinstance(metrics[key], float)

    def test_matches_corine_output_shape(self):
        """WorldCover metrics dict must have the same keys as CORINE metrics."""
        from atoms_vs_ashes.connectors.corine.parsers import compute_buildable_metrics as corine_compute
        from atoms_vs_ashes.connectors.corine.models import RingClassification, SiteClassification

        corine_sc = SiteClassification(lat=44.0, lon=26.0)
        corine_metrics = corine_compute(corine_sc)
        wc_metrics = compute_buildable_metrics(_make_result(rings=[]))

        assert set(corine_metrics.keys()) == set(wc_metrics.keys())
