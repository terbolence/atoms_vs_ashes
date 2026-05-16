# man_hours: 4.4
"""Pure parsing and classification logic for OSM transport access (P11).

No I/O, no HTTP, no database imports. Fully unit-testable.
Serves criteria NS-03 / A14 (transport access for heavy modules).
"""

from __future__ import annotations

from atoms_vs_ashes.connectors.osm.heavy_haul import (
    _HEAVY_HAUL_HIGHWAY_TYPES,
    _is_barge_capable,
    _parse_gauge,
    assess_heavy_haul,
    infer_gauge_by_country,
)
from atoms_vs_ashes.connectors.osm.models import (
    BROAD_GAUGE_MM,
    HighwayResult,
    OsmElement,
    RailwayResult,
    STANDARD_GAUGE_MM,
    TransportResult,
    WaterwayResult,
)
from atoms_vs_ashes.geo import haversine_km

# Appended by ``build_ns03_comment``; batch cache uses this to detect P11-persisted rows.
TRANSPORT_NS03_COMMENT_MARKER = "Source: OSM Overpass API"

def classify_highways(
    site_lat: float,
    site_lon: float,
    elements: list[OsmElement],
) -> HighwayResult:
    """Classify highway elements by proximity and heavy-haul capability.

    Parameters
    ----------
    site_lat, site_lon
        Site coordinates (WGS84).
    elements
        OSM way elements with ``highway`` tag and center coordinates.
    """
    if not elements:
        return HighwayResult(error="No highways found within search radius")

    nearest_km: float | None = None
    nearest_type: str | None = None

    valid_count = 0
    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        valid_count += 1
        dist = haversine_km(site_lat, site_lon, el.lat, el.lon)
        hw_type = el.tags.get("highway", "unknown")
        if nearest_km is None or dist < nearest_km:
            nearest_km = dist
            nearest_type = hw_type

    if nearest_km is None:
        return HighwayResult(
            element_count=len(elements),
            error="All highway elements lacked coordinates",
        )

    heavy_haul = (
        nearest_km < 5.0
        and nearest_type in _HEAVY_HAUL_HIGHWAY_TYPES
    )

    return HighwayResult(
        nearest_highway_km=nearest_km,
        nearest_highway_type=nearest_type,
        highway_heavy_haul=heavy_haul,
        element_count=valid_count,
    )


def classify_railways(
    site_lat: float,
    site_lon: float,
    elements: list[OsmElement],
    country_code: str = "",
) -> RailwayResult:
    """Classify railway elements by proximity, usage, and gauge.

    Parameters
    ----------
    site_lat, site_lon
        Site coordinates (WGS84).
    elements
        OSM way elements with ``railway`` tag and center coordinates.
    country_code
        ISO 3166-1 alpha-2 code for gauge inference when OSM tag is absent.
    """
    if not elements:
        return RailwayResult(error="No railways found within search radius")

    nearest_km: float | None = None
    nearest_mainline_km: float | None = None
    siding_present = False
    nearest_gauge: int | None = None
    valid_count = 0

    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        valid_count += 1
        dist = haversine_km(site_lat, site_lon, el.lat, el.lon)
        tags = el.tags

        railway_type = tags.get("railway", "")
        usage = tags.get("usage", "")
        service = tags.get("service", "")

        if nearest_km is None or dist < nearest_km:
            nearest_km = dist
            gauge_str = tags.get("gauge", "")
            nearest_gauge = _parse_gauge(gauge_str)

        is_mainline = (
            railway_type == "rail"
            and usage in ("main", "branch", "")
            and service not in ("siding", "spur", "yard")
        )
        if is_mainline and (nearest_mainline_km is None or dist < nearest_mainline_km):
            nearest_mainline_km = dist

        if service in ("siding", "spur") and dist < 1.0:
            siding_present = True

    if nearest_km is None:
        return RailwayResult(
            element_count=len(elements),
            error="All railway elements lacked coordinates",
        )

    if nearest_gauge is None:
        nearest_gauge = infer_gauge_by_country(country_code)

    is_standard_or_broad = nearest_gauge in (STANDARD_GAUGE_MM, BROAD_GAUGE_MM)
    heavy_haul = nearest_km < 5.0 and is_standard_or_broad

    return RailwayResult(
        nearest_rail_km=nearest_km,
        nearest_mainline_rail_km=nearest_mainline_km,
        rail_siding_present=siding_present,
        rail_gauge_mm=nearest_gauge,
        rail_heavy_haul=heavy_haul,
        element_count=valid_count,
    )


def classify_waterways(
    site_lat: float,
    site_lon: float,
    elements: list[OsmElement],
) -> WaterwayResult:
    """Classify navigable waterway elements by proximity and CEMT class.

    Parameters
    ----------
    site_lat, site_lon
        Site coordinates (WGS84).
    elements
        OSM way elements with navigability tags and center coordinates.
    """
    if not elements:
        return WaterwayResult(error="No navigable waterways found within search radius")

    nearest_km: float | None = None
    nearest_name: str | None = None
    nearest_cemt: str | None = None
    nearest_barge: bool | None = None
    valid_count = 0

    for el in elements:
        if el.lat is None or el.lon is None:
            continue
        valid_count += 1
        dist = haversine_km(site_lat, site_lon, el.lat, el.lon)
        tags = el.tags

        if nearest_km is None or dist < nearest_km:
            nearest_km = dist
            nearest_name = tags.get("name")
            cemt = tags.get("CEMT", "")
            nearest_cemt = cemt if cemt else None
            nearest_barge = _is_barge_capable(cemt, tags)

    if nearest_km is None:
        return WaterwayResult(
            element_count=len(elements),
            error="All waterway elements lacked coordinates",
        )

    return WaterwayResult(
        nearest_waterway_km=nearest_km,
        nearest_waterway_name=nearest_name,
        waterway_cemt_class=nearest_cemt,
        waterway_barge_capable=nearest_barge,
        element_count=valid_count,
    )


def build_ns03_comment(result: TransportResult) -> str:
    """Build a human-readable summary for the ns03_comment DB column."""
    parts: list[str] = []

    hw = result.highway
    if hw.nearest_highway_km is not None:
        parts.append(
            f"Highway: {hw.nearest_highway_km:.1f} km "
            f"({hw.nearest_highway_type or 'unknown'})"
        )
    elif hw.error:
        parts.append(f"Highway: {hw.error}")

    rw = result.railway
    if rw.nearest_rail_km is not None:
        gauge_str = f", gauge {rw.rail_gauge_mm} mm" if rw.rail_gauge_mm else ""
        siding_str = ", rail siding <1 km" if rw.rail_siding_present else ""
        parts.append(f"Rail: {rw.nearest_rail_km:.1f} km{gauge_str}{siding_str}")
    elif rw.error:
        parts.append(f"Rail: {rw.error}")

    ww = result.waterway
    if ww.nearest_waterway_km is not None:
        name_str = f" ({ww.nearest_waterway_name})" if ww.nearest_waterway_name else ""
        cemt_str = f", CEMT {ww.waterway_cemt_class}" if ww.waterway_cemt_class else ""
        barge_str = ", barge-capable" if ww.waterway_barge_capable else ""
        parts.append(
            f"Waterway: {ww.nearest_waterway_km:.1f} km{name_str}{cemt_str}{barge_str}"
        )
    elif ww.error:
        parts.append(f"Waterway: {ww.error}")

    hh = result.heavy_haul_capable
    if hh is True:
        parts.append(f"Heavy-haul: YES (confidence: {result.heavy_haul_confidence})")
    elif hh is False:
        parts.append(f"Heavy-haul: NO (confidence: {result.heavy_haul_confidence})")
    else:
        parts.append(f"Heavy-haul: UNDETERMINED (confidence: {result.heavy_haul_confidence})")

    parts.append(TRANSPORT_NS03_COMMENT_MARKER)
    return "; ".join(parts)


def determine_quality(
    result: TransportResult,
    country_code: str = "",
) -> str:
    """Determine overall data quality based on element counts and coverage."""
    total_elements = (
        result.highway.element_count
        + result.railway.element_count
        + result.waterway.element_count
    )
    if total_elements < 2 or country_code.upper() in {
        "BA", "RS", "ME", "AL", "MK", "XK", "BY", "AM",
    }:
        return "low"
    if result.highway.error and result.railway.error:
        return "low"
    if result.highway.element_count > 0 and result.railway.element_count > 0:
        return "high"
    return "medium"


