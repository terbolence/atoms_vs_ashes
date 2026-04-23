# man_hours: 0.25
"""S-15 WDPA Protected Planet REST API v4 connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.wdpa.client import WdpaConnector
from atoms_vs_ashes.connectors.wdpa.models import (
    ALL_INSCOPE,
    CRITERION_IDS,
    EU_MEMBER_STATES_INSCOPE,
    ISO2_TO_ISO3,
    NON_EU_INSCOPE,
    SOURCE_NAME,
    AreaProximity,
    BatchResult,
    CountryIngestionSummary,
    IngestionResult,
    ProtectedArea,
    SiteEnrichmentSummary,
    SpatialIndex,
    WdpaResult,
)
from atoms_vs_ashes.connectors.wdpa.parsers import (
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_by_iucn,
    count_by_radius,
    count_international_designations,
    filter_country_areas,
    nearest_ramsar_km,
    parse_api_page,
    parse_protected_area,
    parse_shapefile_feature,
    should_exclude_natura2000,
    strictest_iucn_category,
    validate_result,
)

__all__ = [
    "ALL_INSCOPE",
    "AreaProximity",
    "BatchResult",
    "CRITERION_IDS",
    "CountryIngestionSummary",
    "EU_MEMBER_STATES_INSCOPE",
    "ISO2_TO_ISO3",
    "IngestionResult",
    "NON_EU_INSCOPE",
    "ProtectedArea",
    "SOURCE_NAME",
    "SiteEnrichmentSummary",
    "SpatialIndex",
    "WdpaConnector",
    "WdpaResult",
    "classify_sensitivity",
    "compute_area_fractions",
    "compute_distances",
    "count_by_iucn",
    "count_by_radius",
    "count_international_designations",
    "filter_country_areas",
    "nearest_ramsar_km",
    "parse_api_page",
    "parse_protected_area",
    "parse_shapefile_feature",
    "should_exclude_natura2000",
    "strictest_iucn_category",
    "validate_result",
]
