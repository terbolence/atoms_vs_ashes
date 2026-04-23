# man_hours: 4.0
"""Pure XML parsing and computation for ENTSO-E CIM documents.

No I/O, no HTTP — fully unit-testable against fixture XML strings.
Uses lxml for XPath-based parsing of IEC 62325 CIM documents.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from atoms_vs_ashes.connectors.entso_e.models import (
    BIDDING_ZONES,
    COAL_PSR_TYPES,
    EIC_TO_COUNTRY,
    HYDRO_PSR_TYPES,
    LARGE_UNIT_THRESHOLD_MW,
    NUCLEAR_PSR_TYPE,
    NS_ACK,
    NS_GL,
    NS_PUB,
    NS_TRANS,
    PSR_TYPE_NAMES,
    READINESS_EXCELLENT_MW,
    READINESS_GOOD_MW,
    READINESS_LIMITED_MW,
    READINESS_MODERATE_MW,
    SMR_CAPACITY_MWE,
    THERMAL_PSR_TYPES,
    WIND_SOLAR_PSR_TYPES,
    ZONE_DISPLAY_NAMES,
    CapacityEntry,
    CapacityMetrics,
    FlowEntry,
    FlowTimeSeries,
    GenerationUnit,
    InstalledCapacityAggregated,
    InterconnectionMetrics,
    InterconnectorSummary,
    NtcEntry,
    NtcTimeSeries,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# Namespace maps for ElementTree XPath
_NS_GL_MAP = {"ns": NS_GL}
_NS_PUB_MAP = {"ns": NS_PUB}
_NS_ACK_MAP = {"ns": NS_ACK}
_NS_TRANS_MAP = {"ns": NS_TRANS}


# ---------------------------------------------------------------------------
# Acknowledgement detection
# ---------------------------------------------------------------------------

def is_acknowledgement(xml_text: str) -> tuple[bool, str | None]:
    """Check if XML is an ENTSO-E acknowledgement (no data) document.

    Returns (is_ack, reason_text).
    """
    if "Acknowledgement_MarketDocument" not in xml_text:
        return False, None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return False, None

    if "acknowledgementdocument" in root.tag.lower() or "Acknowledgement" in root.tag:
        reason_el = root.find(f".//{{{NS_ACK}}}Reason/{{{NS_ACK}}}text")
        if reason_el is None:
            reason_el = root.find(".//{http://www.w3.org/1999/xhtml}text")
        reason = reason_el.text if reason_el is not None else "No matching data found"
        return True, reason
    return False, None


# ---------------------------------------------------------------------------
# A68: Installed Generation Capacity Aggregated
# ---------------------------------------------------------------------------

def parse_installed_capacity_xml(
    xml_text: str, zone_eic: str, year: int,
) -> InstalledCapacityAggregated:
    """Parse A68 installed capacity aggregated XML into structured data."""
    root = ET.fromstring(xml_text)
    ns = _detect_namespace(root)
    ns_map = {"ns": ns} if ns else {}

    entries: list[CapacityEntry] = []

    ts_path = f".//{{{ns}}}TimeSeries" if ns else ".//TimeSeries"
    for ts in root.findall(ts_path):
        psr_el = _find(ts, "MktPSRType/psrType", ns)
        psr_type = psr_el.text.strip() if psr_el is not None and psr_el.text else "B20"

        points = _findall(ts, "Period/Point", ns)
        for pt in points:
            qty_el = _find(pt, "quantity", ns)
            if qty_el is not None and qty_el.text:
                try:
                    mw = float(qty_el.text.strip())
                except ValueError:
                    continue
                entries.append(CapacityEntry(
                    psr_type=psr_type,
                    psr_name=PSR_TYPE_NAMES.get(psr_type, psr_type),
                    installed_mw=mw,
                ))

    return InstalledCapacityAggregated(
        zone_eic=zone_eic, year=year, entries=entries,
    )


# ---------------------------------------------------------------------------
# A71: Installed Generation Capacity per Unit
# ---------------------------------------------------------------------------

def parse_generation_units_xml(
    xml_text: str, zone_eic: str,
) -> list[GenerationUnit]:
    """Parse A71 per-unit capacity XML into a list of GenerationUnit."""
    root = ET.fromstring(xml_text)
    ns = _detect_namespace(root)

    units: list[GenerationUnit] = []

    for ts in _findall(root, "TimeSeries", ns):
        psr_el = _find(ts, "MktPSRType/psrType", ns)
        psr_type = psr_el.text.strip() if psr_el is not None and psr_el.text else "B20"

        reg_resource = _find(ts, "MktPSRType/PowerSystemResources", ns)
        if reg_resource is None:
            points = _findall(ts, "Period/Point", ns)
            for pt in points:
                qty_el = _find(pt, "quantity", ns)
                if qty_el is not None and qty_el.text:
                    try:
                        mw = float(qty_el.text.strip())
                    except ValueError:
                        continue
                    units.append(GenerationUnit(
                        unit_name="Unknown",
                        unit_eic=None,
                        psr_type=psr_type,
                        psr_name=PSR_TYPE_NAMES.get(psr_type, psr_type),
                        installed_mw=mw,
                        zone_eic=zone_eic,
                    ))
            continue

        name_el = _find(reg_resource, "name", ns)
        unit_name = name_el.text.strip() if name_el is not None and name_el.text else "Unknown"

        eic_el = _find(reg_resource, "mRID", ns)
        unit_eic = eic_el.text.strip() if eic_el is not None and eic_el.text else None

        voltage_el = _find(reg_resource, "nominalP", ns)
        voltage_kv: float | None = None
        if voltage_el is not None and voltage_el.text:
            try:
                voltage_kv = float(voltage_el.text.strip())
            except ValueError:
                pass

        points = _findall(ts, "Period/Point", ns)
        for pt in points:
            qty_el = _find(pt, "quantity", ns)
            if qty_el is not None and qty_el.text:
                try:
                    mw = float(qty_el.text.strip())
                except ValueError:
                    continue
                units.append(GenerationUnit(
                    unit_name=unit_name,
                    unit_eic=unit_eic,
                    psr_type=psr_type,
                    psr_name=PSR_TYPE_NAMES.get(psr_type, psr_type),
                    installed_mw=mw,
                    voltage_kv=voltage_kv,
                    zone_eic=zone_eic,
                ))

    return units


# ---------------------------------------------------------------------------
# A61: Year-Ahead NTC
# ---------------------------------------------------------------------------

def parse_ntc_xml(
    xml_text: str, from_eic: str, to_eic: str,
) -> NtcTimeSeries:
    """Parse A61 year-ahead NTC XML."""
    root = ET.fromstring(xml_text)
    ns = _detect_namespace(root)

    entries: list[NtcEntry] = []

    for ts in _findall(root, "TimeSeries", ns):
        period = _find(ts, "Period", ns)
        if period is None:
            continue

        interval = _find(period, "timeInterval", ns)
        start = ""
        end = ""
        if interval is not None:
            start_el = _find(interval, "start", ns)
            end_el = _find(interval, "end", ns)
            start = start_el.text.strip() if start_el is not None and start_el.text else ""
            end = end_el.text.strip() if end_el is not None and end_el.text else ""

        for pt in _findall(period, "Point", ns):
            qty_el = _find(pt, "quantity", ns)
            if qty_el is not None and qty_el.text:
                try:
                    mw = float(qty_el.text.strip())
                except ValueError:
                    continue
                entries.append(NtcEntry(start=start, end=end, mw=mw))

    return NtcTimeSeries(from_eic=from_eic, to_eic=to_eic, entries=entries)


# ---------------------------------------------------------------------------
# A11: Cross-Border Physical Flows
# ---------------------------------------------------------------------------

def parse_flows_xml(
    xml_text: str, from_eic: str, to_eic: str,
) -> FlowTimeSeries:
    """Parse A11 cross-border physical flow XML."""
    root = ET.fromstring(xml_text)
    ns = _detect_namespace(root)

    entries: list[FlowEntry] = []

    for ts in _findall(root, "TimeSeries", ns):
        for pt in _findall(ts, "Period/Point", ns):
            pos_el = _find(pt, "position", ns)
            qty_el = _find(pt, "quantity", ns)
            if pos_el is not None and qty_el is not None:
                try:
                    position = int(pos_el.text.strip())
                    mw = float(qty_el.text.strip())
                except (ValueError, AttributeError):
                    continue
                entries.append(FlowEntry(position=position, mw=mw))

    return FlowTimeSeries(from_eic=from_eic, to_eic=to_eic, entries=entries)


# ---------------------------------------------------------------------------
# Pure computation — capacity metrics
# ---------------------------------------------------------------------------

def compute_capacity_metrics(
    capacity: InstalledCapacityAggregated,
    units: list[GenerationUnit] | None = None,
) -> CapacityMetrics:
    """Compute structured capacity metrics from parsed data."""
    by_type: dict[str, float] = {}
    for entry in capacity.entries:
        by_type[entry.psr_type] = by_type.get(entry.psr_type, 0.0) + entry.installed_mw

    total = sum(by_type.values())
    thermal = sum(by_type.get(t, 0.0) for t in THERMAL_PSR_TYPES)
    nuclear = by_type.get(NUCLEAR_PSR_TYPE, 0.0)
    hydro = sum(by_type.get(t, 0.0) for t in HYDRO_PSR_TYPES)
    wind_solar = sum(by_type.get(t, 0.0) for t in WIND_SOLAR_PSR_TYPES)
    other = total - thermal - nuclear - hydro - wind_solar

    metrics = CapacityMetrics(
        total_installed_mw=total,
        thermal_installed_mw=thermal,
        nuclear_installed_mw=nuclear,
        hydro_installed_mw=hydro,
        wind_solar_installed_mw=wind_solar,
        other_installed_mw=max(0.0, other),
        capacity_by_type=by_type,
        has_nuclear_precedent=nuclear > 0,
        smr_capacity_ratio=SMR_CAPACITY_MWE / total if total > 0 else 0.0,
    )

    if units:
        largest = max(units, key=lambda u: u.installed_mw)
        metrics.largest_unit_mw = largest.installed_mw
        metrics.largest_unit_name = largest.unit_name
        metrics.largest_unit_type = largest.psr_type
        metrics.units_above_400mw = sum(
            1 for u in units if u.installed_mw >= LARGE_UNIT_THRESHOLD_MW
        )
        metrics.units_above_200mw = sum(
            1 for u in units if u.installed_mw >= 200
        )
        metrics.nuclear_units = sum(
            1 for u in units if u.psr_type == NUCLEAR_PSR_TYPE
        )
        metrics.coal_units_above_200mw = sum(
            1 for u in units
            if u.psr_type in COAL_PSR_TYPES and u.installed_mw >= 200
        )

    return metrics


# ---------------------------------------------------------------------------
# Pure computation — interconnection metrics
# ---------------------------------------------------------------------------

def compute_interconnection_metrics(
    ntc_list: list[NtcTimeSeries],
    flow_list: list[FlowTimeSeries] | None = None,
    total_installed_mw: float = 0.0,
) -> InterconnectionMetrics:
    """Compute interconnection metrics from NTC and flow data."""
    neighbours_map: dict[str, InterconnectorSummary] = {}

    for ntc in ntc_list:
        neighbour_eic = ntc.to_eic
        country = EIC_TO_COUNTRY.get(neighbour_eic, "")
        name = ZONE_DISPLAY_NAMES.get(country, neighbour_eic)

        if neighbour_eic not in neighbours_map:
            neighbours_map[neighbour_eic] = InterconnectorSummary(
                neighbour_eic=neighbour_eic, neighbour_name=name,
            )
        summary = neighbours_map[neighbour_eic]
        summary.ntc_export_mw = ntc.mean_mw

    total_export = sum(
        s.ntc_export_mw for s in neighbours_map.values()
        if s.ntc_export_mw is not None
    )
    total_import = sum(
        s.ntc_import_mw for s in neighbours_map.values()
        if s.ntc_import_mw is not None
    )
    max_single = max(
        (s.ntc_export_mw or 0.0 for s in neighbours_map.values()),
        default=0.0,
    )

    ratio = (total_export + total_import) / total_installed_mw if total_installed_mw > 0 else 0.0

    return InterconnectionMetrics(
        n_interconnectors=len(neighbours_map),
        total_ntc_export_mw=total_export,
        total_ntc_import_mw=total_import,
        max_single_interconnector_mw=max_single,
        interconnection_ratio=ratio,
        neighbours=list(neighbours_map.values()),
    )


# ---------------------------------------------------------------------------
# Nuclear readiness classification
# ---------------------------------------------------------------------------

def assess_nuclear_readiness(
    capacity: CapacityMetrics | None,
    interconnection: InterconnectionMetrics | None = None,
) -> str:
    """Classify zone nuclear readiness based on capacity and interconnection.

    Returns one of: "excellent", "good", "moderate", "limited", "insufficient".
    """
    if capacity is None:
        return "insufficient"

    total = capacity.total_installed_mw

    if total < READINESS_LIMITED_MW:
        return "insufficient"

    if total < READINESS_MODERATE_MW:
        return "limited"

    if total < READINESS_GOOD_MW:
        if capacity.has_nuclear_precedent:
            return "good"
        return "moderate"

    if total < READINESS_EXCELLENT_MW:
        if capacity.has_nuclear_precedent:
            return "excellent"
        if capacity.units_above_400mw >= 2:
            return "good"
        return "good"

    # total >= 10,000 MW
    if capacity.has_nuclear_precedent:
        return "excellent"
    if capacity.units_above_400mw >= 3:
        return "excellent"
    return "good"


# ---------------------------------------------------------------------------
# Quality determination
# ---------------------------------------------------------------------------

def determine_quality(
    has_a68: bool,
    has_a71: bool,
    has_ntc: bool,
    has_flows: bool,
) -> str:
    """Determine data quality level based on available data products."""
    if has_a68 and has_a71 and has_ntc and has_flows:
        return "high"
    if has_a68 and (has_a71 or has_ntc):
        return "medium"
    if has_a68:
        return "low"
    return "insufficient"


# ---------------------------------------------------------------------------
# Bidding zone identification
# ---------------------------------------------------------------------------

def identify_bidding_zone(
    country_code: str,
    bidding_zones: dict[str, str] | None = None,
) -> str | None:
    """Map country code to bidding zone EIC code."""
    zones = bidding_zones or BIDDING_ZONES
    return zones.get(country_code.upper())


# ---------------------------------------------------------------------------
# XML helpers (stdlib ElementTree)
# ---------------------------------------------------------------------------

def _detect_namespace(root: ET.Element) -> str:
    """Extract the namespace URI from the root element tag."""
    tag = root.tag
    if tag.startswith("{"):
        return tag[1:tag.index("}")]
    return ""


def _find(parent: ET.Element, path: str, ns: str) -> ET.Element | None:
    """Find a child element using a simple dotted path with namespace."""
    parts = path.split("/")
    current = parent
    for part in parts:
        if ns:
            current = current.find(f"{{{ns}}}{part}")
        else:
            current = current.find(part)
        if current is None:
            return None
    return current


def _findall(parent: ET.Element, path: str, ns: str) -> list[ET.Element]:
    """Find all matching elements using a simple dotted path with namespace."""
    parts = path.split("/")
    if len(parts) == 1:
        tag = f"{{{ns}}}{parts[0]}" if ns else parts[0]
        return parent.findall(f".//{tag}")

    current_list = [parent]
    for i, part in enumerate(parts):
        tag = f"{{{ns}}}{part}" if ns else part
        next_list: list[ET.Element] = []
        for el in current_list:
            if i == len(parts) - 1:
                next_list.extend(el.findall(f".//{tag}"))
            else:
                found = el.findall(f".//{tag}")
                next_list.extend(found)
        current_list = next_list
    return current_list
