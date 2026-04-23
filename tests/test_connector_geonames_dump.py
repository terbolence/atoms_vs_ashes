# man_hours: 2.0
"""Unit tests for GeoNames cities5000 dump connector."""

from __future__ import annotations

import numpy as np
import pytest

from atoms_vs_ashes.connectors.geonames_dump.models import GeonamesCityRow
from atoms_vs_ashes.connectors.geonames_dump.parsers import (
    argmin_nearest,
    haversine_km_vec,
    parse_geonames_line,
    row_matches_ri05_filter,
)


def test_parse_geonames_line_valid() -> None:
    line = (
        "123\tParis\tParis\t\t48.85\t2.35\tP\tPPLC\tFR\t\t11\t"
        "\t\t\t2148000\t\t35\tEurope/Paris\t2024-01-01\n"
    )
    row = parse_geonames_line(line)
    assert row is not None
    assert row.geoname_id == 123
    assert row.name == "Paris"
    assert row.lat == pytest.approx(48.85)
    assert row.lon == pytest.approx(2.35)
    assert row.feature_class == "P"
    assert row.feature_code == "PPLC"
    assert row.country_code == "FR"
    assert row.population == 2_148_000


def test_parse_geonames_line_short() -> None:
    assert parse_geonames_line("a\tb\n") is None


def test_row_matches_filter() -> None:
    row = GeonamesCityRow(
        geoname_id=1,
        name="X",
        lat=0.0,
        lon=0.0,
        country_code="ZZ",
        population=60_000,
        feature_class="P",
        feature_code="PPL",
    )
    assert row_matches_ri05_filter(row, min_population=50_000, feature_class="P")
    assert not row_matches_ri05_filter(
        row, min_population=100_000, feature_class="P",
    )
    row2 = GeonamesCityRow(
        geoname_id=2,
        name="R",
        lat=1.0,
        lon=1.0,
        country_code="ZZ",
        population=60_000,
        feature_class="A",
        feature_code="ADM1",
    )
    assert not row_matches_ri05_filter(
        row2, min_population=50_000, feature_class="P",
    )


def test_haversine_vec_and_argmin() -> None:
    lats = np.array([0.0, 0.1, 10.0], dtype=np.float64)
    lons = np.array([0.0, 0.0, 10.0], dtype=np.float64)
    d = haversine_km_vec(0.0, 0.0, lats, lons)
    assert d.shape == (3,)
    assert d[0] == pytest.approx(0.0, abs=1e-6)
    idx = argmin_nearest(0.0, 0.0, lats, lons)
    assert idx == 0


def test_haversine_known_paris_lyon() -> None:
    """Rough check ~390 km."""
    lat1, lon1 = 48.8566, 2.3522
    lat2, lon2 = 45.7640, 4.8357
    d = haversine_km_vec(lat1, lon1, np.array([lat2]), np.array([lon2]))
    assert 350 < float(d[0]) < 450
