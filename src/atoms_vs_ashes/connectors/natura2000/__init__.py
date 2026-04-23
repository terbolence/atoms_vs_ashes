# man_hours: 0.25
"""S-14 Natura 2000 WFS connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.natura2000.client import Natura2000Connector
from atoms_vs_ashes.connectors.natura2000.models import (
    CRITERION_IDS,
    EU_MEMBER_STATES_INSCOPE,
    NON_EU_INSCOPE,
    SOURCE_NAME,
    BatchResult,
    Natura2000Result,
    Natura2000Site,
    SiteEnrichmentSummary,
    SiteProximity,
)
from atoms_vs_ashes.connectors.natura2000.parsers import (
    classify_designation_types,
    classify_sensitivity,
    compute_area_fractions,
    compute_distances,
    count_sites_by_radius,
    parse_features,
    validate_result,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "EU_MEMBER_STATES_INSCOPE",
    "NON_EU_INSCOPE",
    "Natura2000Connector",
    "Natura2000Result",
    "Natura2000Site",
    "SOURCE_NAME",
    "SiteEnrichmentSummary",
    "SiteProximity",
    "classify_designation_types",
    "classify_sensitivity",
    "compute_area_fractions",
    "compute_distances",
    "count_sites_by_radius",
    "parse_features",
    "validate_result",
]
