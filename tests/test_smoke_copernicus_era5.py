# man_hours: 0.5
"""Smoke tests for the S-04 Copernicus CDS / ERA5 connector.

These tests verify that:
  1. CDS API endpoint is reachable (HTTP connectivity check only — no auth)
  2. Local ERA5 data status can be checked without any API calls
  3. If local data is present, extraction returns plausible results
     for a known test site (Bucharest area, 44.43°N 26.10°E)

Marked @pytest.mark.smoke — excluded from default test runs.
Run with: pytest -m smoke tests/test_smoke_copernicus_era5.py

Note: The actual Tier 1 download (CDS API) is NOT tested here —
      that requires explicit user consent (live-api-safety rule).
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector


@pytest.fixture
def connector() -> CopernicusEra5Connector:
    """Create connector with default settings (reads from config/default.yml if available)."""
    try:
        from atoms_vs_ashes.config import Settings
        s = Settings()
        return CopernicusEra5Connector(s)
    except Exception:
        return CopernicusEra5Connector(None)


@pytest.mark.smoke
class TestSmokeLocalDataStatus:
    """Tests that check local ERA5 file status — no API calls."""

    def test_check_local_data_returns_dict(
        self, connector: CopernicusEra5Connector
    ) -> None:
        """check_local_data() should always succeed (no network required)."""
        status = connector.check_local_data()
        assert isinstance(status, dict)
        assert "monthly_means" in status
        assert "era5_land" in status
        assert "cmip6" in status

    def test_data_status_has_expected_keys(
        self, connector: CopernicusEra5Connector
    ) -> None:
        status = connector.check_local_data()
        for name, info in status.items():
            assert "present" in info
            assert "path" in info
            assert "stale" in info
            assert "ttl_days" in info

    def test_has_required_data_returns_bool(
        self, connector: CopernicusEra5Connector
    ) -> None:
        result = connector.has_required_data()
        assert isinstance(result, bool)


@pytest.mark.smoke
class TestSmokeCdsApiReachability:
    """Tests that verify CDS API endpoint reachability (no auth required)."""

    def test_cds_api_endpoint_responds(self) -> None:
        """CDS API base URL should return some HTTP response (even without auth)."""
        import httpx

        try:
            resp = httpx.get(
                "https://cds.climate.copernicus.eu/api",
                follow_redirects=True,
                timeout=10.0,
            )
            # CDS API may return 200, 301, 401, or 403 — all mean it's reachable
            assert resp.status_code < 500, (
                f"CDS API returned server error {resp.status_code}"
            )
        except httpx.ConnectError:
            pytest.skip("CDS API not reachable — check network connectivity")
        except httpx.TimeoutException:
            pytest.skip("CDS API timeout — likely network issue")


@pytest.mark.smoke
class TestSmokeLocalExtraction:
    """Tests that run extraction from local NetCDF files (if present)."""

    def test_extract_all_if_data_present(
        self, connector: CopernicusEra5Connector
    ) -> None:
        """If monthly means file exists locally, extract a sample site."""
        if not connector.has_required_data():
            pytest.skip(
                "ERA5 monthly means file not present locally. "
                "Run 'atoms-vs-ashes enrich ingest-era5' to download ERA5 data."
            )

        result = connector.extract_all(lat=44.43, lon=26.10)

        assert result is not None
        assert result.quality in ("high", "medium")
        assert -90.0 <= result.grid_lat <= 90.0
        assert -180.0 <= result.grid_lon <= 180.0
        assert result.grid_distance_km >= 0.0

        # Wind checks
        assert result.wind is not None
        total_freq = sum(result.wind.wind_rose_16sector.values())
        assert abs(total_freq - 1.0) < 0.02, f"Wind rose sums to {total_freq}, expected ~1.0"
        assert result.wind.mean_wind_speed_ms >= 0.0

        # Temperature checks
        assert result.temperature is not None
        assert result.temperature.max_temp_record_c > result.temperature.min_temp_record_c
        assert -60.0 < result.temperature.min_temp_record_c < 30.0
        assert 5.0 < result.temperature.max_temp_record_c < 55.0

        # Precipitation checks
        assert result.precipitation is not None
        assert result.precipitation.mean_annual_precip_mm > 0.0

        # Stability checks
        assert result.stability is not None
        stability_total = sum(result.stability.stability_class_freq.values())
        assert abs(stability_total - 1.0) < 0.02

    def test_extract_multiple_sites_if_data_present(
        self, connector: CopernicusEra5Connector
    ) -> None:
        """Extract multiple sites — verifies dataset reuse."""
        if not connector.has_required_data():
            pytest.skip("ERA5 data not present.")

        test_sites = [
            (44.43, 26.10, "Bucharest-area"),
            (52.23, 21.01, "Warsaw-area"),
            (50.08, 14.44, "Prague-area"),
        ]

        connector._open_datasets()
        try:
            for lat, lon, name in test_sites:
                result = connector.extract_all(lat=lat, lon=lon)
                assert result.quality in ("high", "medium"), (
                    f"Site {name}: unexpected quality {result.quality}"
                )
                assert result.wind is not None
                assert result.temperature is not None
        finally:
            connector._close_datasets()

    def test_to_dict_json_serializable_if_data_present(
        self, connector: CopernicusEra5Connector
    ) -> None:
        """Full result should be JSON-serializable."""
        if not connector.has_required_data():
            pytest.skip("ERA5 data not present.")

        import json

        result = connector.extract_all(lat=44.43, lon=26.10)
        serialized = json.dumps(result.to_dict(), default=str)
        parsed = json.loads(serialized)

        assert parsed["quality"] in ("high", "medium")
        assert "wind" in parsed
        assert "temperature" in parsed
        assert "precipitation" in parsed
        assert "stability" in parsed
