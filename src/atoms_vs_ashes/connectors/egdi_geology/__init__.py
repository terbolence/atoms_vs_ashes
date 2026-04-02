# man_hours: 0.25
"""S-02 EGDI Geology connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.egdi_geology.client import EgdiGeologyConnector
from atoms_vs_ashes.connectors.egdi_geology.models import (
    BatchResult,
    BoreholeAssessment,
    EgdiGeologyResult,
    FaultAssessment,
    HydrogeologyAssessment,
    KarstAssessment,
    LithologyAssessment,
    MiningAssessment,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.egdi_geology.parsers import (
    build_borehole_assessment,
    build_fault_assessment,
    build_karst_assessment,
    build_mining_assessment,
    build_wfs_bbox,
    classify_aquifer,
    classify_fault_activity,
    classify_lithology,
    compute_quality,
    nearest_feature_distance,
    parse_geojson_features,
    validate_coordinates_in_egdi_domain,
)

__all__ = [
    "BatchResult",
    "BoreholeAssessment",
    "EgdiGeologyConnector",
    "EgdiGeologyResult",
    "FaultAssessment",
    "HydrogeologyAssessment",
    "KarstAssessment",
    "LithologyAssessment",
    "MiningAssessment",
    "SiteEnrichmentSummary",
    "build_borehole_assessment",
    "build_fault_assessment",
    "build_karst_assessment",
    "build_mining_assessment",
    "build_wfs_bbox",
    "classify_aquifer",
    "classify_fault_activity",
    "classify_lithology",
    "compute_quality",
    "nearest_feature_distance",
    "parse_geojson_features",
    "validate_coordinates_in_egdi_domain",
]
