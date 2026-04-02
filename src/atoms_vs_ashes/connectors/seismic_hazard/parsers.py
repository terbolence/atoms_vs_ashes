# man_hours: 4.0
"""Pure parsing and validation functions for EFEHR API responses.

No I/O, no HTTP, no database — fully unit-testable in isolation.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from atoms_vs_ashes.connectors.seismic_hazard.models import (
    INSCOPE_LAT_MAX,
    INSCOPE_LAT_MIN,
    INSCOPE_LON_MAX,
    INSCOPE_LON_MIN,
    NRML_NS,
    HazardCurve,
    UniformHazardSpectrum,
)


def parse_map_csv(text: str) -> list[tuple[float, float, float]]:
    """Parse EFEHR map CSV response into (lon, lat, value) tuples.

    Expected format::

        # longitude; latitude; PGA
        23.1234; 44.1456; 0.1523
    """
    rows: list[tuple[float, float, float]] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(";")
        if len(parts) < 3:
            continue
        try:
            lon = float(parts[0].strip())
            lat = float(parts[1].strip())
            val = float(parts[2].strip())
            rows.append((lon, lat, val))
        except (ValueError, IndexError):
            continue
    return rows


def parse_nrml_curve(xml_text: str) -> HazardCurve | None:
    """Parse NRML XML hazard curve response into a HazardCurve dataclass."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    hc_elem = root.find(f".//{{{NRML_NS}}}hazardCurves")
    if hc_elem is None:
        hc_elem = root.find(".//hazardCurves")
    if hc_elem is None:
        return None

    imt = hc_elem.get("IMT", "PGA")
    inv_time = float(hc_elem.get("investigationTime", "50.0"))

    curve_elem = hc_elem.find(f"{{{NRML_NS}}}hazardCurve")
    if curve_elem is None:
        curve_elem = hc_elem.find("hazardCurve")
    if curve_elem is None:
        return None

    imls_elem = curve_elem.find(f"{{{NRML_NS}}}IMLs")
    if imls_elem is None:
        imls_elem = curve_elem.find("IMLs")
    poes_elem = curve_elem.find(f"{{{NRML_NS}}}poEs")
    if poes_elem is None:
        poes_elem = curve_elem.find("poEs")

    if imls_elem is None or imls_elem.text is None:
        return None
    if poes_elem is None or poes_elem.text is None:
        return None

    imls = [float(x) for x in imls_elem.text.strip().split()]
    poes = [float(x) for x in poes_elem.text.strip().split()]

    if len(imls) < 2 or len(imls) != len(poes):
        return None

    return HazardCurve(imt=imt, imls=imls, poes=poes, investigation_time=inv_time)


def parse_nrml_spectra(xml_text: str) -> UniformHazardSpectrum | None:
    """Parse NRML XML uniform hazard spectrum response."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    uhs_elem = root.find(f".//{{{NRML_NS}}}uniformHazardSpectra")
    if uhs_elem is None:
        uhs_elem = root.find(".//uniformHazardSpectra")
    if uhs_elem is None:
        return None

    inv_time = float(uhs_elem.get("investigationTime", "50.0"))

    uhs_node = uhs_elem.find(f".//{{{NRML_NS}}}uhs")
    if uhs_node is None:
        uhs_node = uhs_elem.find(".//uhs")
    if uhs_node is None:
        return None

    poe = float(uhs_node.get("poe", "0.1"))

    periods_elem = uhs_elem.find(f".//{{{NRML_NS}}}periods")
    if periods_elem is None:
        periods_elem = uhs_elem.find(".//periods")
    if periods_elem is None or periods_elem.text is None:
        return None

    periods = [float(x) for x in periods_elem.text.strip().split()]

    vals_elem = uhs_node.find(f"{{{NRML_NS}}}IMLs")
    if vals_elem is None:
        vals_elem = uhs_node.find("IMLs")
    if vals_elem is None or vals_elem.text is None:
        return None

    sa_values = [float(x) for x in vals_elem.text.strip().split()]

    if not periods or len(periods) != len(sa_values):
        return None

    return UniformHazardSpectrum(
        poe=poe,
        investigation_time=inv_time,
        periods=periods,
        sa_values=sa_values,
    )


def nearest_value(
    grid: list[tuple[float, float, float]], lat: float, lon: float
) -> tuple[float, float]:
    """Find the closest grid point and return (value, distance_km)."""
    if not grid:
        raise ValueError("Empty grid — no data points returned")

    best_val = grid[0][2]
    best_dist = float("inf")

    for g_lon, g_lat, g_val in grid:
        dist = _haversine_km(lat, lon, g_lat, g_lon)
        if dist < best_dist:
            best_dist = dist
            best_val = g_val
    return best_val, best_dist


def validate_pga(value: float | None) -> tuple[str, str | None]:
    """Return (quality_level, detail) for a PGA value."""
    if value is None:
        return "insufficient", "PGA value is None"
    if value < 0:
        return "insufficient", f"Negative PGA value: {value}"
    if value > 5.0:
        return "insufficient", f"PGA value exceeds 5.0g: {value}"
    if value > 2.0:
        return "low", f"PGA value unusually high: {value}g"
    return "high", None


def validate_curve_monotonicity(curve: HazardCurve) -> bool:
    """PoE must decrease as IML increases."""
    for i in range(1, len(curve.poes)):
        if curve.poes[i] > curve.poes[i - 1]:
            return False
    return True


def validate_coordinates_in_scope(lat: float, lon: float) -> bool:
    return (
        INSCOPE_LAT_MIN <= lat <= INSCOPE_LAT_MAX
        and INSCOPE_LON_MIN <= lon <= INSCOPE_LON_MAX
    )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
