# man_hours: 0.25
"""S-08 EU Flood Risk Maps connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.eu_flood_risk.client import EuFloodRiskConnector
from atoms_vs_ashes.connectors.eu_flood_risk.models import (
    ApsfrDesignation,
    BatchResult,
    EuFloodRiskResult,
    FloodDepthProfile,
    SiteEnrichmentSummary,
    TileExtent,
)
from atoms_vs_ashes.connectors.eu_flood_risk.parsers import (
    build_flood_depth_profile,
    classify_flood_hazard,
    compute_flood_exposure_class,
    compute_flood_return_period_threshold,
    determine_quality,
    determine_screening_flags,
    filter_tiles_for_bbox,
    find_covering_tile,
    parse_tile_extents,
    validate_depth_profile,
)

__all__ = [
    "ApsfrDesignation",
    "BatchResult",
    "EuFloodRiskConnector",
    "EuFloodRiskResult",
    "FloodDepthProfile",
    "SiteEnrichmentSummary",
    "TileExtent",
    "build_flood_depth_profile",
    "classify_flood_hazard",
    "compute_flood_exposure_class",
    "compute_flood_return_period_threshold",
    "determine_quality",
    "determine_screening_flags",
    "filter_tiles_for_bbox",
    "find_covering_tile",
    "parse_tile_extents",
    "validate_depth_profile",
]
