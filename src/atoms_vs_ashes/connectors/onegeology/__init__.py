# man_hours: 0.25
"""S-03 OneGeology connector package.

Supplements S-02 EGDI data for NH-02 (faults) and NH-05 (karst)
by querying national geological survey WFS endpoints.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.onegeology.client import OneGeologyConnector
from atoms_vs_ashes.connectors.onegeology.models import (
    BatchResult,
    OneGeologyFaultResult,
    OneGeologyKarstResult,
    OneGeologyResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.onegeology.parsers import (
    build_fault_result,
    build_karst_result,
    build_wfs_bbox,
    nearest_feature_distance,
    parse_geojson_features,
)

__all__ = [
    "BatchResult",
    "OneGeologyConnector",
    "OneGeologyFaultResult",
    "OneGeologyKarstResult",
    "OneGeologyResult",
    "SiteEnrichmentSummary",
    "build_fault_result",
    "build_karst_result",
    "build_wfs_bbox",
    "nearest_feature_distance",
    "parse_geojson_features",
]
