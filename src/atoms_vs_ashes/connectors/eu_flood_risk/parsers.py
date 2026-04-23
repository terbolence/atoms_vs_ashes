# man_hours: 3.0
"""Pure parsing and classification logic for S-08 EU Flood Risk Maps.

No I/O, no HTTP, no database imports. Fully unit-testable.
"""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.connectors.eu_flood_risk.models import (
    ApsfrDesignation,
    DEFAULT_AVOIDANCE_DEPTH_RP500_M,
    DEFAULT_EXCLUSION_DEPTH_RP100_M,
    FloodDepthProfile,
    MAX_PLAUSIBLE_DEPTH_M,
    RETURN_PERIODS,
    TileExtent,
)


def parse_tile_extents(geojson: dict[str, Any]) -> list[TileExtent]:
    """Parse tile_extents.geojson into a list of TileExtent objects.

    JRC GeoJSON has ``{"id": 122, "name": "N50_E10"}`` per feature.
    The download filename pattern is ``ID{id}_{name}_RP{rp}_depth.tif``.
    """
    tiles: list[TileExtent] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        tile_id = props.get("id")
        tile_name = props.get("name")
        if tile_id is None or not tile_name:
            continue

        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        if not coords:
            continue

        ring = coords[0] if geom.get("type") == "Polygon" else coords
        if not ring or len(ring) < 3:
            continue

        lons = [c[0] for c in ring]
        lats = [c[1] for c in ring]
        bbox = (min(lons), min(lats), max(lons), max(lats))
        tiles.append(TileExtent(
            tile_id=str(tile_id), tile_name=str(tile_name), bbox=bbox,
        ))

    return tiles


def filter_tiles_for_bbox(
    tiles: list[TileExtent],
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> list[TileExtent]:
    """Return tiles that overlap the given bounding box."""
    result: list[TileExtent] = []
    for tile in tiles:
        t_min_lon, t_min_lat, t_max_lon, t_max_lat = tile.bbox
        if (t_max_lon >= min_lon and t_min_lon <= max_lon
                and t_max_lat >= min_lat and t_min_lat <= max_lat):
            result.append(tile)
    return result


def find_covering_tile(
    tiles: list[TileExtent], lon: float, lat: float,
) -> TileExtent | None:
    """Find the tile that contains the given point."""
    for tile in tiles:
        if tile.contains(lon, lat):
            return tile
    return None


def build_flood_depth_profile(
    depths: dict[int, float | None],
    tile_id: str | None = None,
) -> FloodDepthProfile:
    """Construct a FloodDepthProfile from a {return_period: depth} mapping."""
    profile = FloodDepthProfile(
        depth_rp10_m=depths.get(10),
        depth_rp20_m=depths.get(20),
        depth_rp50_m=depths.get(50),
        depth_rp75_m=depths.get(75),
        depth_rp100_m=depths.get(100),
        depth_rp200_m=depths.get(200),
        depth_rp500_m=depths.get(500),
        tile_id=tile_id,
    )

    valid_depths = [d for d in depths.values() if d is not None and d > 0]
    profile.max_depth_m = max(valid_depths) if valid_depths else None

    d100 = depths.get(100)
    if d100 is not None and d100 > 0:
        if d100 < 1.0:
            profile.depth_class_rp100 = 1
        elif d100 < 3.0:
            profile.depth_class_rp100 = 2
        elif d100 < 10.0:
            profile.depth_class_rp100 = 3
        else:
            profile.depth_class_rp100 = 4

    return profile


def classify_flood_hazard(
    depth_profile: FloodDepthProfile,
    apsfr_designations: list[ApsfrDesignation],
    *,
    is_spurious: bool = False,
    is_permanent_water: bool = False,
    exclusion_depth_rp100_m: float = DEFAULT_EXCLUSION_DEPTH_RP100_M,
    avoidance_depth_rp500_m: float = DEFAULT_AVOIDANCE_DEPTH_RP500_M,
) -> str:
    """Classify flood hazard: 'exclusionary'|'avoidance'|'low'|'negligible'.

    Implements the decision logic from S-08 spec §16.1.
    """
    if is_spurious:
        if any(a.probability_scenario in ("high", "medium") for a in apsfr_designations):
            return "avoidance"
        return "low"

    if is_permanent_water:
        return "exclusionary"

    d100 = depth_profile.depth_rp100_m
    if d100 is not None and d100 > exclusion_depth_rp100_m:
        return "exclusionary"

    d500 = depth_profile.depth_rp500_m
    if d500 is not None and d500 > avoidance_depth_rp500_m:
        return "avoidance"

    if any(a.probability_scenario in ("high", "medium") for a in apsfr_designations):
        return "avoidance"

    for _rp, depth in depth_profile.depths_as_list():
        if depth is not None and depth > 0:
            return "low"

    if any(a.probability_scenario == "low" for a in apsfr_designations):
        return "low"

    return "negligible"


def compute_flood_return_period_threshold(
    depth_profile: FloodDepthProfile,
) -> int | None:
    """Return the lowest return period with depth > 0, or None."""
    for rp, depth in depth_profile.depths_as_list():
        if depth is not None and depth > 0:
            return rp
    return None


def compute_flood_exposure_class(
    depth_profile: FloodDepthProfile,
) -> str:
    """Classify flood exposure: 'high'|'moderate'|'low'|'negligible'."""
    d100 = depth_profile.depth_rp100_m
    if d100 is not None and d100 > 3.0:
        return "high"
    if d100 is not None and d100 > 0.5:
        return "moderate"
    if d100 is not None and d100 > 0:
        return "low"

    d500 = depth_profile.depth_rp500_m
    if d500 is not None and d500 > 0:
        return "low"

    return "negligible"


def determine_screening_flags(
    depth_profile: FloodDepthProfile,
    apsfr_designations: list[ApsfrDesignation],
    *,
    exclusion_depth_rp100_m: float = DEFAULT_EXCLUSION_DEPTH_RP100_M,
    avoidance_depth_rp500_m: float = DEFAULT_AVOIDANCE_DEPTH_RP500_M,
) -> list[str]:
    """Return list of triggered screening flags: 'E8', 'A14', 'A15', 'A11'.

    A11 (river/coastal flood risk avoidance) triggers when the site has
    any flood exposure: non-zero GloFAS depth at any return period, or
    falls within any APSFR designation regardless of probability.
    """
    flags: list[str] = []

    d100 = depth_profile.depth_rp100_m
    if d100 is not None and d100 > exclusion_depth_rp100_m:
        flags.append("E8")

    d500 = depth_profile.depth_rp500_m
    if d500 is not None and d500 > avoidance_depth_rp500_m:
        flags.append("A14")

    if any(a.probability_scenario in ("high", "medium") for a in apsfr_designations):
        flags.append("A15")

    # A11: flood risk avoidance — any flood exposure from raster or APSFR
    has_any_depth = any(
        d is not None and d > 0 for _rp, d in depth_profile.depths_as_list()
    )
    if has_any_depth or apsfr_designations:
        flags.append("A11")

    return flags


def validate_depth_profile(
    depth_profile: FloodDepthProfile,
) -> list[str]:
    """Validate a flood depth profile. Return list of issue descriptions."""
    issues: list[str] = []
    depths = depth_profile.depths_as_list()

    for rp, depth in depths:
        if depth is not None and depth < 0:
            issues.append(f"Negative depth at RP{rp}: {depth} m")

    prev_depth: float | None = None
    for rp, depth in depths:
        if depth is not None and prev_depth is not None and depth < prev_depth:
            issues.append(
                f"Non-monotonic depth: RP{rp}={depth} m < previous={prev_depth} m"
            )
        if depth is not None:
            prev_depth = depth

    for rp, depth in depths:
        if depth is not None and depth > MAX_PLAUSIBLE_DEPTH_M:
            issues.append(f"Implausible depth at RP{rp}: {depth} m (max {MAX_PLAUSIBLE_DEPTH_M} m)")

    return issues


def determine_quality(
    depth_profile: FloodDepthProfile,
    apsfr_designations: list[ApsfrDesignation],
    country_code: str | None = None,
    *,
    is_permanent_water: bool = False,
    is_spurious: bool = False,
    eu_member_states: frozenset[str] | None = None,
) -> str:
    """Determine quality level: 'high'|'medium'|'low'|'insufficient'."""
    from atoms_vs_ashes.connectors.eu_flood_risk.models import EU_MEMBER_STATES

    eu_states = eu_member_states or EU_MEMBER_STATES

    if is_permanent_water:
        return "insufficient"

    if is_spurious:
        return "low"

    sampled_count = sum(
        1 for _rp, d in depth_profile.depths_as_list() if d is not None
    )

    if sampled_count == 0:
        if not apsfr_designations:
            return "insufficient"
        return "medium"

    if sampled_count < 3:
        return "low"

    if sampled_count < 5:
        return "medium"

    is_eu = country_code in eu_states if country_code else bool(apsfr_designations)
    if is_eu and apsfr_designations:
        return "high"

    if not is_eu:
        return "high"

    return "high"


def count_sampled_return_periods(depth_profile: FloodDepthProfile) -> int:
    """Count how many return periods have non-None depth values."""
    return sum(1 for _rp, d in depth_profile.depths_as_list() if d is not None)
