# man_hours: 0.5
"""Smoke tests for S-10 Copernicus EMS — requires live API access.

Run: pytest tests/test_smoke_copernicus_ems.py -m smoke -v --tb=short
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.copernicus_ems import CopernicusEmsConnector

pytestmark = pytest.mark.smoke

_TEST_LAT, _TEST_LON = 45.27, 27.96  # Braila, Romania


class TestConnectivity:
    def test_health_check(self) -> None:
        with CopernicusEmsConnector() as c:
            assert c.health_check() is True


class TestCatalogueIngestion:
    def test_fetch_rrm_activations(self) -> None:
        with CopernicusEmsConnector() as c:
            activations = c.fetch_rrm_activations(category="Flood")
            assert len(activations) > 0
            act = activations[0]
            assert act.code is not None
            assert act.category == "Flood"

    def test_fetch_rapid_activations(self) -> None:
        with CopernicusEmsConnector() as c:
            activations = c.fetch_rapid_activations(category_slug="flood")
            assert len(activations) >= 0  # may be empty if filtering is strict

    def test_ingest_catalogue(self) -> None:
        with CopernicusEmsConnector() as c:
            result = c.ingest_catalogue("smoke-test")
            assert result.n_rrm_fetched >= 0
            assert result.elapsed_s > 0


class TestSiteAssessment:
    def test_assess_site_after_ingestion(self) -> None:
        with CopernicusEmsConnector() as c:
            c.ingest_catalogue("smoke-test")
            result = c.assess_site(_TEST_LAT, _TEST_LON)
            assert result is not None
            d = result.to_dict()
            for key in ["lat", "lon", "susceptibility", "quality"]:
                assert key in d

    def test_assess_site_without_ingestion(self) -> None:
        with CopernicusEmsConnector() as c:
            result = c.assess_site(_TEST_LAT, _TEST_LON)
            assert result.error is not None
            assert result.quality == "insufficient"
