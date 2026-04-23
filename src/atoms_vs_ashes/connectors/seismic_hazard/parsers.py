# man_hours: 6.0
"""Pure parsing and validation functions for EFEHR API responses.

No I/O, no HTTP, no database — fully unit-testable in isolation.

API Validation (2026-04-13) revealed:
  - Model discovery XML uses nested <id>/<name> elements, not attributes.
  - ESHM20 curve returns NRML 0.3 (ns2: prefixed) with a different
    structure than the NRML 0.4 assumed in the spec.
  - ESHM20 map endpoint is non-functional; ESHM13 map works.
  - Spectra endpoint non-functional for both models.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from atoms_vs_ashes.connectors.seismic_hazard.models import (
    GML_NS,
    INSCOPE_LAT_MAX,
    INSCOPE_LAT_MIN,
    INSCOPE_LON_MAX,
    INSCOPE_LON_MIN,
    NRML_NS,
    NRML_NS_03,
    HazardCurve,
    UniformHazardSpectrum,
)
from atoms_vs_ashes.geo import haversine_km


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
    """Parse NRML XML hazard curve response into a HazardCurve dataclass.

    Handles both NRML 0.4 (spec-documented) and NRML 0.3 (actual EFEHR
    response for ESHM20 as of 2026-04-13).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    curve = _try_parse_nrml04_curve(root)
    if curve is not None:
        return curve

    return _try_parse_nrml03_curve(root)


def _try_parse_nrml04_curve(root: ET.Element) -> HazardCurve | None:
    """NRML 0.4: <hazardCurves><hazardCurve><IMLs/><poEs/></hazardCurve>"""
    for ns in [f"{{{NRML_NS}}}", ""]:
        hc_elem = root.find(f".//{ns}hazardCurves")
        if hc_elem is None:
            continue

        imt = hc_elem.get("IMT", "PGA")
        inv_time = float(hc_elem.get("investigationTime", "50.0"))

        curve_elem = hc_elem.find(f"{ns}hazardCurve")
        if curve_elem is None:
            continue

        imls_elem = curve_elem.find(f"{ns}IMLs")
        poes_elem = curve_elem.find(f"{ns}poEs")
        if imls_elem is None or imls_elem.text is None:
            continue
        if poes_elem is None or poes_elem.text is None:
            continue

        imls = [float(x) for x in imls_elem.text.strip().split()]
        poes = [float(x) for x in poes_elem.text.strip().split()]
        if len(imls) < 2 or len(imls) != len(poes):
            continue

        return HazardCurve(imt=imt, imls=imls, poes=poes, investigation_time=inv_time)
    return None


def _try_parse_nrml03_curve(root: ET.Element) -> HazardCurve | None:
    """NRML 0.3: <hazardResult><hazardCurveField><IML/><HCNode><hazardCurve><poE/>>"""
    ns = f"{{{NRML_NS_03}}}"

    hr = root.find(f".//{ns}hazardResult")
    if hr is None:
        return None

    config = hr.find(f".//{ns}hazardProcessing")
    inv_time = 50.0
    if config is not None:
        inv_time = float(config.get("investigationTimeSpan", "50.0"))

    hcf = hr.find(f".//{ns}hazardCurveField")
    if hcf is None:
        return None

    iml_elem = hcf.find(f"{ns}IML")
    if iml_elem is None or iml_elem.text is None:
        return None
    imt = iml_elem.get("IMT", "PGA")
    imls = [float(x) for x in iml_elem.text.strip().split()]

    poe_elem = hcf.find(f".//{ns}poE")
    if poe_elem is None or poe_elem.text is None:
        return None
    poes = [float(x) for x in poe_elem.text.strip().split()]

    if len(imls) < 2 or len(imls) != len(poes):
        return None

    return HazardCurve(imt=imt, imls=imls, poes=poes, investigation_time=inv_time)


def parse_nrml_spectra(xml_text: str) -> UniformHazardSpectrum | None:
    """Parse NRML XML uniform hazard spectrum response."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    for ns in [f"{{{NRML_NS}}}", f"{{{NRML_NS_03}}}", ""]:
        uhs_elem = root.find(f".//{ns}uniformHazardSpectra")
        if uhs_elem is None:
            continue

        inv_time = float(uhs_elem.get("investigationTime", "50.0"))

        uhs_node = uhs_elem.find(f".//{ns}uhs")
        if uhs_node is None:
            continue

        poe = float(uhs_node.get("poe", "0.1"))

        periods_elem = uhs_elem.find(f".//{ns}periods")
        if periods_elem is None or periods_elem.text is None:
            continue

        periods = [float(x) for x in periods_elem.text.strip().split()]

        vals_elem = uhs_node.find(f"{ns}IMLs")
        if vals_elem is None or vals_elem.text is None:
            continue

        sa_values = [float(x) for x in vals_elem.text.strip().split()]

        if not periods or len(periods) != len(sa_values):
            continue

        return UniformHazardSpectrum(
            poe=poe,
            investigation_time=inv_time,
            periods=periods,
            sa_values=sa_values,
        )
    return None


def parse_model_discovery(xml_text: str) -> list[tuple[int, str]]:
    """Parse model discovery XML into (model_id, model_name) pairs.

    The EFEHR API returns nested elements, not attributes::

        <models>
          <model><id>81</id><name>ESHM20</name></model>
        </models>
    """
    results: list[tuple[int, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results

    for model_elem in root.iter("model"):
        mid: int | None = None
        name: str = ""

        id_el = model_elem.find("id")
        if id_el is not None and id_el.text:
            try:
                mid = int(id_el.text.strip())
            except ValueError:
                pass

        # Also try attribute-style (defensive)
        if mid is None:
            id_attr = model_elem.get("id")
            if id_attr is not None:
                try:
                    mid = int(id_attr)
                except ValueError:
                    pass

        name_el = model_elem.find("name")
        if name_el is not None and name_el.text:
            name = name_el.text.strip()
        elif model_elem.get("name"):
            name = model_elem.get("name", "")

        if mid is not None:
            results.append((mid, name))

    return results


def nearest_value(
    grid: list[tuple[float, float, float]], lat: float, lon: float
) -> tuple[float, float]:
    """Find the closest grid point and return (value, distance_km)."""
    if not grid:
        raise ValueError("Empty grid — no data points returned")

    best_val = grid[0][2]
    best_dist = float("inf")

    for g_lon, g_lat, g_val in grid:
        dist = haversine_km(lat, lon, g_lat, g_lon)
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


def interpolate_curve_at_poe(
    curve: HazardCurve, target_poe: float,
) -> float | None:
    """Log-log interpolation of IML at a target probability of exceedance.

    The hazard curve provides (IML, PoE) pairs where PoE decreases as IML
    increases.  ``target_poe`` must be in the same units as the curve's PoE
    values — typically the investigation-time PoE (e.g. 0.1 for 475-year
    return period over a 50-year investigation window).

    Returns None if the target PoE is outside the curve range or the curve
    has fewer than 2 points.
    """
    if len(curve.imls) < 2 or len(curve.imls) != len(curve.poes):
        return None

    poes = curve.poes
    imls = curve.imls

    if target_poe >= poes[0] or target_poe <= 0:
        return None
    if target_poe <= poes[-1]:
        return imls[-1]

    for i in range(len(poes) - 1):
        if poes[i] >= target_poe >= poes[i + 1]:
            if poes[i] <= 0 or poes[i + 1] <= 0 or imls[i] <= 0 or imls[i + 1] <= 0:
                return None
            log_poe_lo = math.log(poes[i])
            log_poe_hi = math.log(poes[i + 1])
            log_iml_lo = math.log(imls[i])
            log_iml_hi = math.log(imls[i + 1])
            frac = (math.log(target_poe) - log_poe_lo) / (log_poe_hi - log_poe_lo)
            log_iml = log_iml_lo + frac * (log_iml_hi - log_iml_lo)
            return math.exp(log_iml)

    return None
