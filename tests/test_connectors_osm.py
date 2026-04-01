# man_hours: 6.0
"""Tests for the OSM Overpass API connector — geometry parsing and area computation."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import MultiPolygon, Polygon

from atoms_vs_ashes.connectors.osm import (
    PlantBoundary,
    _parse_relation_geometry,
    _parse_way_geometry,
    compute_geodesic_area_ha,
    find_best_plant_boundary,
)


# ---------------------------------------------------------------------------
# Geometry parsing — ways
# ---------------------------------------------------------------------------


class TestParseWayGeometry:
    def test_valid_closed_polygon(self):
        elem = {
            "geometry": [
                {"lat": 50.0, "lon": 19.0},
                {"lat": 50.0, "lon": 19.01},
                {"lat": 50.01, "lon": 19.01},
                {"lat": 50.01, "lon": 19.0},
                {"lat": 50.0, "lon": 19.0},
            ]
        }
        poly = _parse_way_geometry(elem)
        assert poly is not None
        assert isinstance(poly, Polygon)
        assert poly.is_valid
        assert not poly.is_empty

    def test_auto_closes_ring(self):
        elem = {
            "geometry": [
                {"lat": 50.0, "lon": 19.0},
                {"lat": 50.0, "lon": 19.01},
                {"lat": 50.01, "lon": 19.01},
                {"lat": 50.01, "lon": 19.0},
            ]
        }
        poly = _parse_way_geometry(elem)
        assert poly is not None
        assert poly.is_valid

    def test_too_few_points_returns_none(self):
        elem = {
            "geometry": [
                {"lat": 50.0, "lon": 19.0},
                {"lat": 50.01, "lon": 19.01},
                {"lat": 50.0, "lon": 19.0},
            ]
        }
        assert _parse_way_geometry(elem) is None

    def test_empty_geometry_returns_none(self):
        assert _parse_way_geometry({"geometry": []}) is None
        assert _parse_way_geometry({}) is None


# ---------------------------------------------------------------------------
# Geometry parsing — relations
# ---------------------------------------------------------------------------


class TestParseRelationGeometry:
    def test_single_outer_ring(self):
        elem = {
            "members": [
                {
                    "type": "way",
                    "role": "outer",
                    "geometry": [
                        {"lat": 50.0, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.01},
                        {"lat": 50.01, "lon": 19.01},
                        {"lat": 50.01, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.0},
                    ],
                }
            ]
        }
        geom = _parse_relation_geometry(elem)
        assert geom is not None
        assert geom.is_valid

    def test_outer_with_inner_hole(self):
        elem = {
            "members": [
                {
                    "type": "way",
                    "role": "outer",
                    "geometry": [
                        {"lat": 50.0, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.02},
                        {"lat": 50.02, "lon": 19.02},
                        {"lat": 50.02, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.0},
                    ],
                },
                {
                    "type": "way",
                    "role": "inner",
                    "geometry": [
                        {"lat": 50.005, "lon": 19.005},
                        {"lat": 50.005, "lon": 19.015},
                        {"lat": 50.015, "lon": 19.015},
                        {"lat": 50.015, "lon": 19.005},
                        {"lat": 50.005, "lon": 19.005},
                    ],
                },
            ]
        }
        geom = _parse_relation_geometry(elem)
        assert geom is not None
        outer_only = Polygon(
            [(19.0, 50.0), (19.02, 50.0), (19.02, 50.02), (19.0, 50.02), (19.0, 50.0)]
        )
        assert geom.area < outer_only.area

    def test_no_outer_returns_none(self):
        elem = {
            "members": [
                {
                    "type": "way",
                    "role": "inner",
                    "geometry": [
                        {"lat": 50.0, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.01},
                        {"lat": 50.01, "lon": 19.01},
                        {"lat": 50.01, "lon": 19.0},
                        {"lat": 50.0, "lon": 19.0},
                    ],
                }
            ]
        }
        assert _parse_relation_geometry(elem) is None

    def test_empty_members_returns_none(self):
        assert _parse_relation_geometry({"members": []}) is None
        assert _parse_relation_geometry({}) is None


# ---------------------------------------------------------------------------
# Geodesic area computation
# ---------------------------------------------------------------------------


class TestGeodesicArea:
    def test_known_approximate_area(self):
        """A ~1 km × ~1 km square near Kraków should be roughly 100 ha."""
        # 0.01° lat ≈ 1.11 km, 0.01° lon ≈ 0.71 km at 50°N → ~79 ha
        poly = Polygon([
            (19.0, 50.0),
            (19.01, 50.0),
            (19.01, 50.01),
            (19.0, 50.01),
            (19.0, 50.0),
        ])
        area = compute_geodesic_area_ha(poly)
        assert 70 < area < 90, f"Expected ~79 ha, got {area:.1f}"

    def test_area_is_positive(self):
        poly = Polygon([
            (19.0, 50.0),
            (19.0, 50.01),
            (19.01, 50.01),
            (19.01, 50.0),
            (19.0, 50.0),
        ])
        area = compute_geodesic_area_ha(poly)
        assert area > 0

    def test_multipolygon(self):
        p1 = Polygon([(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01), (0, 0)])
        p2 = Polygon([(1, 1), (1.01, 1), (1.01, 1.01), (1, 1.01), (1, 1)])
        mp = MultiPolygon([p1, p2])
        area = compute_geodesic_area_ha(mp)
        single_area = compute_geodesic_area_ha(p1)
        assert area > single_area


# ---------------------------------------------------------------------------
# Best-boundary selection
# ---------------------------------------------------------------------------


class TestFindBestPlantBoundary:
    def _make_boundary(
        self, osm_id: int, clat: float, clon: float, area_ha: float,
    ) -> PlantBoundary:
        poly = Polygon([
            (clon - 0.001, clat - 0.001),
            (clon + 0.001, clat - 0.001),
            (clon + 0.001, clat + 0.001),
            (clon - 0.001, clat + 0.001),
            (clon - 0.001, clat - 0.001),
        ])
        return PlantBoundary(
            osm_id=osm_id,
            osm_type="way",
            name=f"Plant {osm_id}",
            geometry=poly,
            area_ha=area_ha,
            centroid_lat=clat,
            centroid_lon=clon,
        )

    def test_empty_returns_none(self):
        assert find_best_plant_boundary(50.0, 19.0, []) is None

    def test_single_boundary_returned(self):
        b = self._make_boundary(1, 50.0, 19.0, 30.0)
        assert find_best_plant_boundary(50.0, 19.0, [b]) is b

    def test_closest_centroid_preferred(self):
        close = self._make_boundary(1, 50.001, 19.001, 20.0)
        far = self._make_boundary(2, 50.1, 19.1, 100.0)
        result = find_best_plant_boundary(50.0, 19.0, [far, close])
        assert result is close

    def test_larger_preferred_when_equidistant(self):
        small = self._make_boundary(1, 50.0, 19.0, 20.0)
        big = self._make_boundary(2, 50.0, 19.0, 80.0)
        result = find_best_plant_boundary(50.0, 19.0, [small, big])
        assert result is big
