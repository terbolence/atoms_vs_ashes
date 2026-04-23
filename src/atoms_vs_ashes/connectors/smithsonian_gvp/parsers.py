# man_hours: 3.0
"""Pure parsing, spatial query, and hazard classification for S-07 GVP volcanism.

No I/O, no HTTP, no database imports.  All functions operate on in-memory
data structures (lists of VolcanoRecord / EruptionRecord dataclasses).

Criterion: NH-07 (Holocene volcano proximity and volcanic product hazards).
"""

from __future__ import annotations

import datetime
from typing import Any

from atoms_vs_ashes.connectors.smithsonian_gvp.models import (
    AVOIDANCE_RECENT_DISTANCE_KM,
    AVOIDANCE_RECENT_YEARS,
    AVOIDANCE_VEI4_DISTANCE_KM,
    DEFAULT_SEARCH_RADIUS_KM,
    EXCLUSION_DISTANCE_KM,
    EXTENDED_RADIUS_KM,
    HIGH_EXPLOSIVITY_TYPES,
    MAX_NEARBY_VOLCANOES,
    MIN_ERUPTION_COUNT,
    MIN_VOLCANO_COUNT,
    PRODUCT_MAP,
    EruptionRecord,
    EruptionStatistics,
    NearbyVolcano,
    SmithsonianGvpResult,
    VolcanoRecord,
)
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_CURRENT_YEAR = datetime.date.today().year
_HOLOCENE_START_YEAR = -10000  # ~12 kya


# ---------------------------------------------------------------------------
# GeoJSON parsing
# ---------------------------------------------------------------------------

def parse_volcanoes_geojson(geojson: dict[str, Any]) -> list[VolcanoRecord]:
    """Parse a WFS GeoJSON FeatureCollection into VolcanoRecord objects.

    Skips features with missing required fields or invalid coordinates.
    """
    features = geojson.get("features", [])
    volcanoes: list[VolcanoRecord] = []

    for feat in features:
        props = feat.get("properties") or {}
        try:
            number = int(props.get("Volcano_Number", 0))
            name = str(props.get("Volcano_Name", "Unknown"))
            lat = _safe_float(props.get("Latitude"))
            lon = _safe_float(props.get("Longitude"))

            if lat is None or lon is None:
                geom = feat.get("geometry") or {}
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                else:
                    log.warning("gvp_invalid_coords", volcano_number=number, name=name)
                    continue

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                log.warning("gvp_invalid_coords", lat=lat, lon=lon, name=name)
                continue

            elevation = _safe_int(props.get("Elevation")) or 0
            primary_type = str(props.get("Primary_Volcano_Type", "Unknown"))
            last_eruption_year = _safe_int(props.get("Last_Eruption_Year"))

            if last_eruption_year is not None and last_eruption_year > _CURRENT_YEAR:
                log.warning(
                    "gvp_future_eruption_year",
                    name=name, year=last_eruption_year,
                )

            volcanoes.append(VolcanoRecord(
                number=number,
                name=name,
                latitude=lat,
                longitude=lon,
                elevation=elevation,
                primary_type=primary_type,
                last_eruption_year=last_eruption_year,
                country=str(props.get("Country", "")),
                region=str(props.get("Region", "")),
                subregion=str(props.get("Subregion", "")),
                tectonic_setting=props.get("Tectonic_Setting"),
                evidence_category=str(props.get("Evidence_Category", "")),
                major_rock_type=props.get("Major_Rock_Type"),
                geological_summary=props.get("Geological_Summary"),
            ))
        except (ValueError, TypeError, KeyError) as exc:
            log.warning("gvp_parse_volcano_error", error=str(exc))
            continue

    if len(volcanoes) < MIN_VOLCANO_COUNT:
        log.warning(
            "gvp_low_count",
            entity="volcanoes",
            count=len(volcanoes),
            expected=MIN_VOLCANO_COUNT,
        )

    return volcanoes


def parse_eruptions_geojson(geojson: dict[str, Any]) -> list[EruptionRecord]:
    """Parse a WFS GeoJSON FeatureCollection into EruptionRecord objects.

    Skips records with invalid VEI values or missing required fields.
    """
    features = geojson.get("features", [])
    eruptions: list[EruptionRecord] = []

    for feat in features:
        props = feat.get("properties") or {}
        try:
            volcano_number = int(props.get("Volcano_Number", 0))
            eruption_number = int(props.get("Eruption_Number", 0))
            if volcano_number == 0:
                continue

            vei = _safe_int(props.get("ExplosivityIndexMax"))
            if vei is not None and not (0 <= vei <= 8):
                log.warning(
                    "gvp_invalid_vei",
                    eruption_number=eruption_number, vei=vei,
                )
                vei = None

            start_year = _safe_int(props.get("StartDateYear"))
            end_year = _safe_int(props.get("EndDateYear"))
            if start_year is not None and end_year is not None and start_year > end_year:
                log.warning(
                    "gvp_inconsistent_dates",
                    eruption_number=eruption_number,
                    start=start_year, end=end_year,
                )

            eruptions.append(EruptionRecord(
                eruption_number=eruption_number,
                volcano_number=volcano_number,
                volcano_name=str(props.get("Volcano_Name", "")),
                activity_type=str(props.get("Activity_Type", "")),
                vei_max=vei,
                start_year=start_year,
                start_year_uncertainty=_safe_int(props.get("StartDateYearUncertainty")),
                end_year=end_year,
                activity_area=props.get("ActivityArea"),
            ))
        except (ValueError, TypeError, KeyError) as exc:
            log.warning("gvp_parse_eruption_error", error=str(exc))
            continue

    if len(eruptions) < MIN_ERUPTION_COUNT:
        log.warning(
            "gvp_low_count",
            entity="eruptions",
            count=len(eruptions),
            expected=MIN_ERUPTION_COUNT,
        )

    return eruptions


def build_eruption_index(
    eruptions: list[EruptionRecord],
) -> dict[int, list[EruptionRecord]]:
    """Index eruption records by Volcano_Number for fast lookup."""
    index: dict[int, list[EruptionRecord]] = {}
    for e in eruptions:
        index.setdefault(e.volcano_number, []).append(e)
    return index


# ---------------------------------------------------------------------------
# Spatial queries
# ---------------------------------------------------------------------------

def find_nearby_volcanoes(
    lat: float,
    lon: float,
    volcanoes: list[VolcanoRecord],
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
) -> list[tuple[VolcanoRecord, float]]:
    """Find all volcanoes within radius_km of (lat, lon).

    Returns a list of (VolcanoRecord, distance_km) sorted by distance ascending.
    """
    nearby: list[tuple[VolcanoRecord, float]] = []
    for v in volcanoes:
        dist = haversine_km(lat, lon, v.latitude, v.longitude)
        if dist <= radius_km:
            nearby.append((v, dist))
    nearby.sort(key=lambda x: x[1])
    return nearby


# ---------------------------------------------------------------------------
# Eruption statistics
# ---------------------------------------------------------------------------

def compute_eruption_statistics(
    eruptions: list[EruptionRecord],
) -> EruptionStatistics:
    """Compute aggregate eruption statistics for a single volcano's eruption list."""
    stats = EruptionStatistics()
    if not eruptions:
        return stats

    stats.total_eruptions = len(eruptions)
    vei_values: list[int] = []
    cutoff_2ka = _CURRENT_YEAR - AVOIDANCE_RECENT_YEARS
    cutoff_10ka = _HOLOCENE_START_YEAR

    for e in eruptions:
        if e.activity_type == "Confirmed Eruption":
            stats.confirmed_eruptions += 1
        else:
            stats.uncertain_eruptions += 1

        if e.vei_max is not None:
            vei_values.append(e.vei_max)
            stats.eruptions_with_vei += 1
        else:
            stats.eruptions_without_vei += 1

        if e.start_year is not None:
            if e.start_year >= cutoff_2ka:
                stats.eruptions_last_2ka += 1
            if e.start_year >= cutoff_10ka:
                stats.eruptions_last_10ka += 1

    if vei_values:
        stats.max_vei = max(vei_values)
        stats.mean_vei = sum(vei_values) / len(vei_values)
        for v in vei_values:
            stats.vei_distribution[v] = stats.vei_distribution.get(v, 0) + 1

    # Eruption frequency: eruptions per 1,000 years over the Holocene
    holocene_span_ka = (_CURRENT_YEAR - _HOLOCENE_START_YEAR) / 1000.0
    if holocene_span_ka > 0 and stats.total_eruptions > 0:
        stats.eruption_frequency_per_ka = stats.total_eruptions / holocene_span_ka

    return stats


# ---------------------------------------------------------------------------
# Hazard classification
# ---------------------------------------------------------------------------

def classify_hazard(
    nearby: list[tuple[VolcanoRecord, float]],
    eruption_index: dict[int, list[EruptionRecord]],
    *,
    exclusion_km: float = EXCLUSION_DISTANCE_KM,
    avoidance_vei4_km: float = AVOIDANCE_VEI4_DISTANCE_KM,
    avoidance_recent_km: float = AVOIDANCE_RECENT_DISTANCE_KM,
    avoidance_recent_years: int = AVOIDANCE_RECENT_YEARS,
) -> tuple[str, list[str]]:
    """Determine hazard class and screening flags from nearby volcanoes.

    Returns (hazard_class, screening_flags).
    """
    if not nearby:
        return "negligible", []

    flags: list[str] = []

    # E7: Exclusionary — volcano within exclusion distance
    nearest_volcano, nearest_dist = nearby[0]
    if nearest_dist < exclusion_km:
        flags.append("E7")
        return "exclusionary", flags

    # A12: Avoidance — VEI >= 4 (or assumed capable) within avoidance distance
    cutoff_2ka = _CURRENT_YEAR - avoidance_recent_years
    for v, dist in nearby:
        if dist > avoidance_vei4_km:
            break
        eruptions = eruption_index.get(v.number, [])
        stats = compute_eruption_statistics(eruptions)
        if stats.max_vei is not None and stats.max_vei >= 4:
            flags.append("A12")
            return "avoidance", flags
        # Proxy: high-explosivity type with no VEI data → assume VEI 4+
        if stats.max_vei is None and v.primary_type in HIGH_EXPLOSIVITY_TYPES:
            flags.append("A12")
            return "avoidance", flags

    # A13: Avoidance — recently active volcano within 100 km
    for v, dist in nearby:
        if dist > avoidance_recent_km:
            break
        eruptions = eruption_index.get(v.number, [])
        stats = compute_eruption_statistics(eruptions)
        if stats.eruptions_last_2ka > 0:
            flags.append("A13")
            return "avoidance", flags

    return "low", flags


# ---------------------------------------------------------------------------
# Volcanic product determination
# ---------------------------------------------------------------------------

def determine_volcanic_products(
    primary_type: str,
    rock_type: str | None,
    max_vei: int | None,
) -> list[str]:
    """Determine expected volcanic products based on volcano type and rock type.

    Uses the mapping from spec §16.2.
    """
    type_lower = primary_type.lower()

    for prefix, products in PRODUCT_MAP.items():
        if type_lower.startswith(prefix):
            return list(products)

    # Fallback: if high VEI, assume full product set
    if max_vei is not None and max_vei >= 4:
        return [
            "lava_flow", "pyroclastic_flow", "lahar",
            "tephra_fall", "volcanic_gas",
        ]

    return ["lava_flow", "tephra_fall", "volcanic_gas"]


# ---------------------------------------------------------------------------
# Quality determination
# ---------------------------------------------------------------------------

def determine_quality(
    nearby: list[tuple[VolcanoRecord, float]],
    eruption_index: dict[int, list[EruptionRecord]],
    extended_radius_km: float = EXTENDED_RADIUS_KM,
    using_stale_cache: bool = False,
) -> str:
    """Determine data quality level for the assessment.

    See spec §16.3 for the full quality matrix.
    """
    if using_stale_cache:
        return "medium"

    if not nearby:
        return "high"  # confident negative — no volcano within search radius

    nearest_v, nearest_dist = nearby[0]

    if nearest_dist > extended_radius_km:
        return "high"

    eruptions = eruption_index.get(nearest_v.number, [])
    stats = compute_eruption_statistics(eruptions)

    if stats.total_eruptions == 0:
        return "medium"  # only geological evidence, no eruption records

    if stats.eruptions_with_vei > 0:
        vei_ratio = stats.eruptions_with_vei / max(stats.total_eruptions, 1)
        if vei_ratio >= 0.5:
            return "high"
        return "medium"

    return "medium"


# ---------------------------------------------------------------------------
# Assemble full result
# ---------------------------------------------------------------------------

def assemble_result(
    lat: float,
    lon: float,
    volcanoes: list[VolcanoRecord],
    eruption_index: dict[int, list[EruptionRecord]],
    *,
    search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    max_nearby: int = MAX_NEARBY_VOLCANOES,
    exclusion_km: float = EXCLUSION_DISTANCE_KM,
    avoidance_vei4_km: float = AVOIDANCE_VEI4_DISTANCE_KM,
    avoidance_recent_km: float = AVOIDANCE_RECENT_DISTANCE_KM,
    avoidance_recent_years: int = AVOIDANCE_RECENT_YEARS,
    database_version: str = "",
    using_stale_cache: bool = False,
) -> SmithsonianGvpResult:
    """Build the complete SmithsonianGvpResult for a single site.

    Pure computation — no I/O.
    """
    nearby_raw = find_nearby_volcanoes(lat, lon, volcanoes, search_radius_km)

    if not nearby_raw:
        quality = determine_quality([], eruption_index, using_stale_cache=using_stale_cache)
        return SmithsonianGvpResult(
            lat=lat, lon=lon,
            hazard_class="negligible",
            search_radius_km=search_radius_km,
            database_version=database_version,
            quality=quality,
        )

    hazard_class, screening_flags = classify_hazard(
        nearby_raw, eruption_index,
        exclusion_km=exclusion_km,
        avoidance_vei4_km=avoidance_vei4_km,
        avoidance_recent_km=avoidance_recent_km,
        avoidance_recent_years=avoidance_recent_years,
    )

    nearby_volcanoes: list[NearbyVolcano] = []
    for v, dist in nearby_raw[:max_nearby]:
        eruptions = eruption_index.get(v.number, [])
        stats = compute_eruption_statistics(eruptions)
        products = determine_volcanic_products(
            v.primary_type, v.major_rock_type, stats.max_vei,
        )
        years_since = None
        if v.last_eruption_year is not None:
            years_since = _CURRENT_YEAR - v.last_eruption_year

        nearby_volcanoes.append(NearbyVolcano(
            volcano_number=v.number,
            volcano_name=v.name,
            distance_km=dist,
            latitude=v.latitude,
            longitude=v.longitude,
            elevation_m=v.elevation,
            primary_type=v.primary_type,
            tectonic_setting=v.tectonic_setting,
            country=v.country,
            major_rock_type=v.major_rock_type,
            evidence_category=v.evidence_category,
            last_eruption_year=v.last_eruption_year,
            years_since_last_eruption=years_since,
            eruption_stats=stats,
            expected_products=products,
        ))

    within_100 = sum(1 for _, d in nearby_raw if d <= 100)
    within_300 = sum(1 for _, d in nearby_raw if d <= 300)

    nearest = nearby_volcanoes[0] if nearby_volcanoes else None
    products = nearest.expected_products if nearest else []

    quality = determine_quality(
        nearby_raw, eruption_index, using_stale_cache=using_stale_cache,
    )

    return SmithsonianGvpResult(
        lat=lat,
        lon=lon,
        nearest_volcano=nearest,
        nearby_volcanoes=nearby_volcanoes,
        volcanoes_within_100km=within_100,
        volcanoes_within_300km=within_300,
        hazard_class=hazard_class,
        screening_flags=screening_flags,
        volcanic_products=products,
        search_radius_km=search_radius_km,
        database_version=database_version,
        quality=quality,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
