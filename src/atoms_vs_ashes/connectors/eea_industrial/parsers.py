# man_hours: 3.0
"""Pure parsing and spatial query logic for S-37 EEA Industrial Emissions.

No I/O, no HTTP, no database imports.  All functions operate on
in-memory data structures and IndustrialFacility dataclasses.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections import Counter
from typing import Any

from shapely import STRtree
from shapely.geometry import Point

from atoms_vs_ashes.connectors.eea_industrial.models import (
    EPRTR_ACTIVITY_HAZARD_MAP,
    EU_MEMBER_COUNTRIES,
    EUROPE_LAT_MAX,
    EUROPE_LAT_MIN,
    EUROPE_LON_MAX,
    EUROPE_LON_MIN,
    NACE_HAZARD_MAP,
    NO_COVERAGE_COUNTRIES,
    PARTIAL_COVERAGE_COUNTRIES,
    EpzIndustrialAssessment,
    FacilityIndex,
    HazardProximity,
    IndustrialFacility,
    IndustrialProximityResult,
    NearbyFacility,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

# Common column name aliases across different EEA CSV export formats
_COL_ALIASES: dict[str, list[str]] = {
    "facility_id": [
        "OBJECTID", "FacilityID", "facilityId", "facility_id", "FacilityReportID",
    ],
    "name": [
        "siteName", "facilityNames",
        "FacilityName", "facilityName", "facility_name", "name",
    ],
    "latitude": [
        "y_4258", "Latitude", "latitude", "lat", "Lat",
    ],
    "longitude": [
        "x_4258", "Longitude", "longitude", "lon", "Lon", "Long",
    ],
    "country_code": [
        "countryCode", "CountryCode", "country_code", "Country",
    ],
    "nace_code": [
        "NACEMainEconomicActivityCode", "naceMainEconomicActivityCode",
        "nace_code", "NACECode", "NACE",
    ],
    "nace_description": [
        "NACEMainEconomicActivityName", "naceMainEconomicActivityName",
        "nace_description", "NACEName",
    ],
    "eprtr_activity_code": [
        "eprtr_AnnexIActivity",
        "EPRTRAnnexIMainActivityCode", "eprtrAnnexIMainActivityCode",
        "eprtr_activity_code", "MainActivityCode",
    ],
    "eprtr_activity_description": [
        "eea_activities", "eprtr_sectors",
        "EPRTRAnnexIMainActivityName", "eprtrAnnexIMainActivityName",
        "eprtr_activity_description", "MainActivityName",
    ],
    "seveso_status": [
        "has_seveso",
        "SevesoPart", "sevesoPart", "seveso_status", "SevesoStatus",
        "Seveso", "seveso",
    ],
    "parent_company": [
        "ParentCompanyName", "parentCompanyName", "parent_company",
    ],
    "city": ["City", "city"],
}

_NACE_PATTERN = re.compile(r"^\d{2}\.\d{1,2}$")


def _resolve_column(headers: list[str], field_name: str) -> str | None:
    """Find the actual CSV column name for a logical field."""
    aliases = _COL_ALIASES.get(field_name, [field_name])
    header_lower = {h.lower().strip(): h for h in headers}
    for alias in aliases:
        if alias in headers:
            return alias
        lower = alias.lower()
        if lower in header_lower:
            return header_lower[lower]
    return None


def parse_eprtr_csv(
    text: str,
    *,
    country_filter: set[str] | None = None,
) -> list[IndustrialFacility]:
    """Parse an E-PRTR facility CSV export into IndustrialFacility objects.

    Parameters
    ----------
    text
        Raw CSV text content.
    country_filter
        If provided, only include facilities in these countries.
    """
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        log.warning("eea_csv_empty_headers")
        return []

    headers = list(reader.fieldnames)
    col_map = {
        field: _resolve_column(headers, field)
        for field in _COL_ALIASES
    }

    facilities: list[IndustrialFacility] = []
    skipped_coords = 0
    skipped_country = 0

    for row_idx, row in enumerate(reader):
        lat_raw = row.get(col_map.get("latitude") or "", "")
        lon_raw = row.get(col_map.get("longitude") or "", "")

        lat = _safe_float(lat_raw)
        lon = _safe_float(lon_raw)
        if lat is None or lon is None:
            skipped_coords += 1
            continue

        if not _coords_in_europe(lat, lon):
            skipped_coords += 1
            continue

        cc = (row.get(col_map.get("country_code") or "", "") or "").strip().upper()
        if country_filter and cc not in country_filter:
            skipped_country += 1
            continue

        fid = (row.get(col_map.get("facility_id") or "", "") or "").strip()
        if not fid:
            fid = f"eprtr-{row_idx}"

        name = (row.get(col_map.get("name") or "", "") or "").strip()
        if not name:
            name = "Unknown facility"

        nace = _normalise_nace(row.get(col_map.get("nace_code") or "", ""))
        eprtr_code = (row.get(col_map.get("eprtr_activity_code") or "", "") or "").strip()
        eprtr_desc = (row.get(col_map.get("eprtr_activity_description") or "", "") or "").strip()
        seveso_raw = (row.get(col_map.get("seveso_status") or "", "") or "").strip()

        hazard_cats = classify_hazard(
            nace_code=nace,
            eprtr_activity_code=eprtr_code,
            seveso_status=seveso_raw,
            eprtr_description=eprtr_desc,
        )

        facility = IndustrialFacility(
            facility_id=fid,
            name=name,
            latitude=lat,
            longitude=lon,
            country_code=cc,
            nace_code=nace,
            nace_description=(row.get(col_map.get("nace_description") or "", "") or "").strip() or None,
            eprtr_activity_code=eprtr_code or None,
            eprtr_activity_description=(
                row.get(col_map.get("eprtr_activity_description") or "", "") or ""
            ).strip() or None,
            seveso_status=_normalise_seveso(seveso_raw),
            parent_company=(row.get(col_map.get("parent_company") or "", "") or "").strip() or None,
            city=(row.get(col_map.get("city") or "", "") or "").strip() or None,
            hazard_categories=hazard_cats,
            source="eprtr",
        )
        facilities.append(facility)

    if skipped_coords:
        log.info("eea_csv_skipped_coords", count=skipped_coords)
    if skipped_country:
        log.info("eea_csv_skipped_country", count=skipped_country)

    log.info("eea_csv_parsed", facility_count=len(facilities))
    return facilities


# ---------------------------------------------------------------------------
# Hazard classification
# ---------------------------------------------------------------------------

def classify_hazard(
    *,
    nace_code: str | None = None,
    eprtr_activity_code: str | None = None,
    seveso_status: str | None = None,
    substances: str | None = None,
    eprtr_description: str | None = None,
) -> set[str]:
    """Classify a facility's hazard categories from available metadata.

    Returns a subset of {"chemical", "toxic", "fire"}.

    The ESRI REST API returns ``eprtr_AnnexIActivity`` in a descriptive
    format like ``"5(a) - Installations for the disposal …"`` rather
    than the numeric ``"5.1"`` code.  We match against both formats.
    """
    cats: set[str] = set()

    if nace_code:
        cats.update(NACE_HAZARD_MAP.get(nace_code, set()))
        prefix = nace_code.split(".")[0] if "." in nace_code else nace_code
        if prefix in ("19", "20"):
            cats.add("chemical")
        if prefix == "20":
            cats.add("toxic")

    if eprtr_activity_code:
        for prefix, hazards in EPRTR_ACTIVITY_HAZARD_MAP.items():
            if eprtr_activity_code.startswith(prefix):
                cats.update(hazards)
                break

    # Fallback: classify from the descriptive text when the numeric
    # code doesn't match (ESRI format: "5(a) - Installations for …")
    desc = (eprtr_description or eprtr_activity_code or "").lower()
    if not cats and desc:
        cats.update(_classify_from_description(desc))

    if seveso_status and seveso_status.lower() in ("upper", "lower"):
        if not cats:
            cats.update({"chemical", "toxic", "fire"})

    return cats


# Keyword → hazard mapping for descriptive E-PRTR activity strings
_DESCRIPTION_HAZARD_KEYWORDS: dict[str, set[str]] = {
    "refiner": {"fire", "chemical"},
    "coke oven": {"fire"},
    "organic chemical": {"chemical", "toxic"},
    "inorganic chemical": {"chemical", "toxic"},
    "fertiliser": {"chemical"},
    "fertilizer": {"chemical"},
    "pharmaceutical": {"chemical"},
    "explosive": {"chemical", "fire"},
    "pyrotechnic": {"chemical", "fire"},
    "hazardous waste": {"toxic"},
    "waste incineration": {"toxic"},
    "non-hazardous waste": {"toxic"},
    "landfill": {"toxic"},
    "gasification": {"fire", "chemical"},
    "liquefaction": {"fire", "chemical"},
    "petroleum": {"fire", "chemical"},
    "iron and steel": {"chemical", "fire"},
    "basic metals": {"chemical", "fire"},
}


def _classify_from_description(desc: str) -> set[str]:
    """Extract hazard categories from a descriptive activity string."""
    cats: set[str] = set()
    for keyword, hazards in _DESCRIPTION_HAZARD_KEYWORDS.items():
        if keyword in desc:
            cats.update(hazards)
    return cats


def _normalise_seveso(raw: str) -> str | None:
    """Normalise SEVESO status to 'upper', 'lower', or None.

    The ESRI REST API returns ``has_seveso`` as an integer (0/1)
    rather than a textual tier.  We treat ``1`` as ``"upper"``
    (conservative — the API doesn't distinguish tiers).
    """
    if not raw:
        return None
    lower = raw.strip().lower()
    if "upper" in lower:
        return "upper"
    if "lower" in lower:
        return "lower"
    if lower in ("yes", "true", "1"):
        return "upper"
    if lower == "0":
        return None
    return None


def _normalise_nace(raw: str | None) -> str | None:
    """Clean and validate a NACE code."""
    if not raw:
        return None
    code = raw.strip()
    if _NACE_PATTERN.match(code):
        return code
    digits = re.sub(r"[^0-9.]", "", code)
    if _NACE_PATTERN.match(digits):
        return digits
    return None


# ---------------------------------------------------------------------------
# Spatial index
# ---------------------------------------------------------------------------

def build_facility_index(facilities: list[IndustrialFacility]) -> FacilityIndex:
    """Build a Shapely STRtree spatial index from facility points."""
    if not facilities:
        return FacilityIndex(facility_count=0)

    points = [Point(f.longitude, f.latitude) for f in facilities]
    tree = STRtree(points)

    countries = sorted({f.country_code for f in facilities})
    sources = sorted({f.source for f in facilities})

    log.info(
        "eea_index_built",
        facility_count=len(facilities),
        countries=len(countries),
    )

    return FacilityIndex(
        facilities=facilities,
        tree=tree,
        facility_count=len(facilities),
        countries_loaded=countries,
        data_sources=sources,
    )


# ---------------------------------------------------------------------------
# Proximity queries (pure — no I/O)
# ---------------------------------------------------------------------------

def query_facilities_in_radius(
    lat: float,
    lon: float,
    index: FacilityIndex,
    radius_km: float = 30.0,
) -> list[tuple[IndustrialFacility, float]]:
    """Find all facilities within radius_km of a point.

    Returns list of (facility, distance_km) tuples sorted by distance.
    """
    from atoms_vs_ashes.geo import haversine_km

    if not index.facilities or index.tree is None:
        return []

    # Rough bounding box filter via STRtree
    deg_margin = radius_km / 111.0 * 1.5
    minx = lon - deg_margin
    maxx = lon + deg_margin
    miny = lat - deg_margin
    maxy = lat + deg_margin

    from shapely.geometry import box
    search_box = box(minx, miny, maxx, maxy)
    candidate_idxs = index.tree.query(search_box)

    results: list[tuple[IndustrialFacility, float]] = []
    for idx in candidate_idxs:
        fac = index.facilities[idx]
        dist = haversine_km(lat, lon, fac.latitude, fac.longitude)
        if dist <= radius_km:
            results.append((fac, dist))

    results.sort(key=lambda x: x[1])
    return results


def compute_proximity_metrics(
    lat: float,
    lon: float,
    facilities_with_distances: list[tuple[IndustrialFacility, float]],
) -> IndustrialProximityResult:
    """Compute per-hazard-category proximity metrics from nearby facilities.

    Pure computation — no I/O.
    """
    chemical_facs: list[tuple[IndustrialFacility, float]] = []
    toxic_facs: list[tuple[IndustrialFacility, float]] = []
    fire_facs: list[tuple[IndustrialFacility, float]] = []

    for fac, dist in facilities_with_distances:
        if "chemical" in fac.hazard_categories:
            chemical_facs.append((fac, dist))
        if "toxic" in fac.hazard_categories:
            toxic_facs.append((fac, dist))
        if "fire" in fac.hazard_categories:
            fire_facs.append((fac, dist))

    chemical_prox = _build_hazard_proximity("chemical", chemical_facs)
    toxic_prox = _build_hazard_proximity("toxic", toxic_facs)
    fire_prox = _build_hazard_proximity("fire", fire_facs)

    epz = _compute_epz_assessment(facilities_with_distances)

    nearby = [
        NearbyFacility(
            name=fac.name,
            latitude=fac.latitude,
            longitude=fac.longitude,
            distance_km=dist,
            seveso_tier=fac.seveso_status,
            hazard_categories=fac.hazard_categories,
            nace_code=fac.nace_code,
            country_code=fac.country_code,
            source=fac.source,
            facility_id=fac.facility_id,
        )
        for fac, dist in facilities_with_distances
    ]

    return IndustrialProximityResult(
        lat=lat,
        lon=lon,
        chemical=chemical_prox,
        toxic=toxic_prox,
        fire=fire_prox,
        all_facilities=nearby,
        epz_assessment=epz,
        facility_count_total=len(facilities_with_distances),
    )


def assess_data_quality(
    country_code: str,
    n_facilities_found: int,
    data_sources_used: list[str],
) -> str:
    """Determine quality level based on data availability."""
    cc = country_code.upper()
    if cc in NO_COVERAGE_COUNTRIES:
        return "insufficient"
    if cc in PARTIAL_COVERAGE_COUNTRIES:
        return "low" if n_facilities_found == 0 else "medium"
    if cc in EU_MEMBER_COUNTRIES:
        if n_facilities_found == 0 and "eprtr" in data_sources_used:
            return "medium"
        return "high"
    return "insufficient"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_hazard_proximity(
    hazard_type: str,
    facs_with_dist: list[tuple[IndustrialFacility, float]],
) -> HazardProximity:
    """Build HazardProximity from a list of (facility, distance_km)."""
    prox = HazardProximity(hazard_type=hazard_type)

    if not facs_with_dist:
        return prox

    nearest_fac, nearest_dist = facs_with_dist[0]
    prox.nearest_facility_km = nearest_dist
    prox.nearest_facility_name = nearest_fac.name
    prox.nearest_facility_tier = nearest_fac.seveso_status
    prox.nearest_facility_nace = nearest_fac.nace_code

    for fac, dist in facs_with_dist:
        if dist <= 2.0:
            prox.count_within_2km += 1
        if dist <= 5.0:
            prox.count_within_5km += 1
            if fac.seveso_status == "upper":
                prox.upper_tier_within_5km += 1
        if dist <= 10.0:
            prox.count_within_10km += 1
            if fac.seveso_status == "upper":
                prox.upper_tier_within_10km += 1
        if dist <= 25.0:
            prox.count_within_25km += 1

    return prox


def _compute_epz_assessment(
    facs_with_dist: list[tuple[IndustrialFacility, float]],
) -> EpzIndustrialAssessment:
    """Compute EPZ-ring industrial hazard assessment."""
    epz = EpzIndustrialAssessment()
    hazard_counter: Counter[str] = Counter()

    for fac, dist in facs_with_dist:
        is_seveso = fac.seveso_status in ("upper", "lower")
        is_upper = fac.seveso_status == "upper"

        if dist <= 5.0:
            if is_seveso:
                epz.seveso_all_within_5km += 1
            if is_upper:
                epz.seveso_upper_within_5km += 1
        if dist <= 16.0:
            if is_seveso:
                epz.seveso_all_within_16km += 1
            if is_upper:
                epz.seveso_upper_within_16km += 1
        if dist <= 25.0:
            if is_seveso:
                epz.seveso_all_within_25km += 1
            if is_upper:
                epz.seveso_upper_within_25km += 1
            for cat in fac.hazard_categories:
                hazard_counter[cat] += 1

    # Area of 25 km circle ≈ π × 25² ≈ 1963.5 km²
    area_1000km2 = math.pi * 25.0 ** 2 / 1000.0
    total_in_25 = sum(
        1 for _, d in facs_with_dist
        if d <= 25.0 and any(
            cat in facs_with_dist[0][0].hazard_categories
            for cat in ("chemical", "toxic", "fire")
        )
    )
    hazardous_in_25 = sum(1 for _, d in facs_with_dist if d <= 25.0)
    epz.industrial_hazard_density_25km = hazardous_in_25 / area_1000km2 if area_1000km2 > 0 else 0.0

    if hazard_counter:
        epz.dominant_hazard_type = hazard_counter.most_common(1)[0][0]

    return epz


def _safe_float(val: Any) -> float | None:
    """Safely parse a value to float."""
    if val is None:
        return None
    try:
        f = float(str(val).strip())
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _coords_in_europe(lat: float, lon: float) -> bool:
    """Check if coordinates fall within the European bounding box."""
    return (
        EUROPE_LAT_MIN <= lat <= EUROPE_LAT_MAX
        and EUROPE_LON_MIN <= lon <= EUROPE_LON_MAX
    )
