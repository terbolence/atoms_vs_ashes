# man_hours: 2.0
"""Pure parsing and classification logic for S-10 Copernicus EMS.

No I/O, no HTTP, no database imports. Fully unit-testable.
"""

from __future__ import annotations

import re
from typing import Any

from atoms_vs_ashes.connectors.copernicus_ems.models import (
    COUNTRY_NAME_MAP,
    DEFAULT_SITE_BUFFER_KM,
    FlashFloodAssessment,
    FloodFootprint,
    FootprintSummary,
    RapidActivation,
    RrmActivation,
)


def parse_rrm_activation(data: dict[str, Any]) -> RrmActivation | None:
    """Parse a single RRM activation from the API JSON response."""
    code = data.get("code")
    if not code:
        return None

    name = data.get("name", "")
    category = data.get("category", "")
    sub_category = data.get("subCategory")
    drm_phase = data.get("actDrmPhase", "")
    countries_raw = data.get("countries", [])
    countries = _normalize_countries(countries_raw)
    activation_time = data.get("activationTime")
    closed = data.get("closed", False)

    centroid_lon, centroid_lat = _parse_wkt_point(data.get("centroid", ""))

    download_urls: list[str] = []
    for product in data.get("products", []):
        url = product.get("mapsDownload")
        if url:
            download_urls.append(url)

    return RrmActivation(
        code=str(code),
        name=str(name),
        category=str(category),
        sub_category=str(sub_category) if sub_category else None,
        drm_phase=str(drm_phase) if drm_phase else None,
        countries=countries,
        centroid_lon=centroid_lon,
        centroid_lat=centroid_lat,
        activation_time=str(activation_time) if activation_time else None,
        closed=bool(closed),
        download_urls=download_urls,
    )


def parse_rapid_activation(data: dict[str, Any]) -> RapidActivation | None:
    """Parse a single Rapid Mapping activation from the API JSON response."""
    code = data.get("code")
    if not code:
        return None

    name = data.get("name", "")
    category_obj = data.get("category", {})
    category = category_obj.get("slug", "") if isinstance(category_obj, dict) else str(category_obj)

    countries_raw = data.get("countries", [])
    countries: list[str] = []
    for c in countries_raw:
        if isinstance(c, dict):
            cname = c.get("short_name") or c.get("name", "")
        else:
            cname = str(c)
        iso = COUNTRY_NAME_MAP.get(cname, "")
        if iso:
            countries.append(iso)

    centroid_lon, centroid_lat = _parse_wkt_point(data.get("centroid", ""))

    return RapidActivation(
        code=str(code),
        name=str(name),
        category=str(category),
        countries=countries,
        centroid_lon=centroid_lon,
        centroid_lat=centroid_lat,
        activation_time=data.get("activationTime"),
        closed=data.get("closed", False),
        n_aois=int(data.get("n_aois", 0)),
        n_products=int(data.get("n_products", 0)),
    )


def classify_susceptibility(
    intersection_area_km2: float,
    distance_km: float | None,
    n_events: int,
    *,
    medium_distance_km: float = 10.0,
    low_distance_km: float = 50.0,
    negligible_distance_km: float = 100.0,
) -> str | None:
    """Classify flash flood susceptibility from proximity metrics.

    Returns 'high', 'medium', 'low', 'negligible', or None (no data).

    Tiers:
      - high: site polygon intersects a flood delineation polygon
      - medium: centroid within ``medium_distance_km`` (default 10 km)
      - low: centroid within ``low_distance_km`` (default 50 km)
      - negligible: centroid within ``negligible_distance_km`` (default 100 km)
    """
    if n_events == 0 or distance_km is None:
        return None

    if intersection_area_km2 > 0:
        return "high"

    if distance_km <= medium_distance_km:
        return "medium"

    if distance_km <= low_distance_km:
        return "low"

    if distance_km <= negligible_distance_km:
        return "negligible"

    return None


def determine_quality(
    n_events: int,
    susceptibility: str | None,
) -> str:
    """Determine assessment quality based on data availability."""
    if n_events == 0:
        return "insufficient"
    if n_events >= 3:
        return "high"
    if n_events >= 1:
        return "medium"
    return "insufficient"


def _parse_wkt_point(wkt: str | None) -> tuple[float | None, float | None]:
    """Extract (lon, lat) from a WKT POINT string."""
    if not wkt:
        return None, None
    match = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", wkt, re.IGNORECASE)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def _normalize_countries(raw: list[Any]) -> list[str]:
    """Normalize country names to ISO 3166-1 alpha-2 codes."""
    result: list[str] = []
    for item in raw:
        name = str(item) if not isinstance(item, dict) else item.get("name", "")
        iso = COUNTRY_NAME_MAP.get(name, "")
        if iso:
            result.append(iso)
    return result


def validate_footprint_area(area_km2: float) -> bool:
    """Return True if footprint area is plausible (< 50,000 km²)."""
    return 0 < area_km2 < 50_000


def validate_activation_date(date_str: str | None) -> bool:
    """Return True if activation date is within plausible range (2012–now+1day)."""
    if not date_str:
        return False
    try:
        from datetime import datetime, timedelta, timezone
        raw = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        min_date = datetime(2012, 1, 1, tzinfo=timezone.utc)
        max_date = datetime.now(timezone.utc) + timedelta(days=1)
        return min_date <= dt <= max_date
    except (ValueError, TypeError):
        return False
