# man_hours: 1.0
"""Smoke tests for the S-03 OneGeology connector (live network required).

Run with: pytest tests/test_smoke_onegeology.py -m smoke -v
Skipped automatically when network is unavailable.

These tests make real HTTP requests to national geological survey endpoints.
They verify endpoint reachability and basic response parsing — not data correctness.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.onegeology import OneGeologyConnector

pytestmark = pytest.mark.smoke

# ---------------------------------------------------------------------------
# Registry with verified endpoints from API exploration
# ---------------------------------------------------------------------------

SMOKE_REGISTRY = {
    "RO": {
        "wfs_url": "https://inspire.igr.ro/geoserver/wfs",
        "wfs_version": "2.0.0",
        "fault_layer": None,  # updated after GetCapabilities probe
        "karst_layer": None,
    },
    "BG": {
        "wfs_url": "https://inspire.geology.bg/geoserver/wfs",
        "wfs_version": "2.0.0",
        "fault_layer": None,
        "karst_layer": None,
    },
    "AT": {
        "wfs_url": "https://gisgba.geologie.ac.at/geoserver/wfs",
        "wfs_version": "2.0.0",
        "fault_layer": None,
        "karst_layer": None,
    },
}


def _make_smoke_connector() -> OneGeologyConnector:
    """Build a connector with the smoke test registry (no settings object)."""
    connector = OneGeologyConnector.__new__(OneGeologyConnector)
    import httpx
    connector._timeout = 30
    connector._inter_request_delay = 1.0
    connector._cache_ttl_days = 180
    connector._max_features = 100
    connector._fault_buffer_km = 8.0
    connector._karst_buffer_km = 5.0
    connector._endpoint_registry = SMOKE_REGISTRY
    connector._client = httpx.Client(
        timeout=30, follow_redirects=True,
        headers={"User-Agent": "atoms_vs_ashes/onegeology-connector/smoke-test"},
    )
    return connector


@pytest.fixture()
def connector():
    c = _make_smoke_connector()
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Endpoint health checks
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_health_check_returns_dict(connector: OneGeologyConnector) -> None:
    """health_check() returns a dict with results for each registered country."""
    health = connector.health_check()
    assert isinstance(health, dict)
    # Health check is informational — don't fail if endpoints are down
    for cc, reachable in health.items():
        assert isinstance(reachable, bool)
        print(f"  {cc}: {'OK' if reachable else 'UNREACHABLE'}")


@pytest.mark.smoke
@pytest.mark.parametrize("country_code,wfs_url", [
    ("RO", "https://inspire.igr.ro/geoserver/wfs"),
    ("BG", "https://inspire.geology.bg/geoserver/wfs"),
    ("AT", "https://gisgba.geologie.ac.at/geoserver/wfs"),
])
def test_endpoint_getcapabilities(
    connector: OneGeologyConnector,
    country_code: str,
    wfs_url: str,
) -> None:
    """GetCapabilities request returns a response (even if not 200)."""
    import httpx
    try:
        resp = connector._client.get(wfs_url, params={
            "service": "WFS", "version": "2.0.0", "request": "GetCapabilities",
        })
        # Any response (even 4xx/5xx) means the endpoint exists and is talking
        print(f"  {country_code} {wfs_url}: HTTP {resp.status_code}, "
              f"content-type={resp.headers.get('content-type', 'unknown')}, "
              f"len={len(resp.content)} bytes")
        # Just log — don't assert on status code (endpoints may require auth etc.)
    except httpx.TimeoutException:
        pytest.skip(f"{country_code} endpoint timed out — network unreachable")
    except httpx.HTTPError as exc:
        pytest.skip(f"{country_code} endpoint unreachable: {exc}")


# ---------------------------------------------------------------------------
# Fetch-all (no actual layer queries since layers are null in smoke registry)
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_fetch_all_no_endpoint_graceful(connector: OneGeologyConnector) -> None:
    """fetch_all() for an unregistered country returns quality=insufficient."""
    result = connector.fetch_all(
        lat=48.0, lon=23.0, country_code="UA",
        s02_nh02_quality=None,
        s02_nh05_quality=None,
    )
    assert result.quality == "insufficient"
    assert result.faults is None
    assert result.karst is None
    assert result.supplements_s02 is False


@pytest.mark.smoke
def test_fetch_all_s02_adequate_skips_network(connector: OneGeologyConnector) -> None:
    """fetch_all() when S-02 data is adequate returns without querying."""
    result = connector.fetch_all(
        lat=44.43, lon=26.10, country_code="RO",
        s02_nh02_quality="high",
        s02_nh05_quality="medium",
    )
    assert result.quality == "high"
    assert result.endpoints_queried == []


@pytest.mark.smoke
def test_fetch_all_null_layer_graceful(connector: OneGeologyConnector) -> None:
    """fetch_all() with registered endpoint but null layers returns gracefully."""
    result = connector.fetch_all(
        lat=44.43, lon=26.10, country_code="RO",
        s02_nh02_quality=None,
        s02_nh05_quality=None,
    )
    # Endpoint is registered but layers are null — should return incomplete result
    # without error
    assert result.country_code == "RO"
    assert isinstance(result.quality, str)
    print(f"  RO fetch_all result: quality={result.quality}, "
          f"faults={result.faults}, karst={result.karst}")
