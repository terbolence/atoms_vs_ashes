# man_hours: 0.25
"""S-36 ESA WorldCover connector package."""

from atoms_vs_ashes.connectors.worldcover.client import WorldCoverConnector
from atoms_vs_ashes.connectors.worldcover.models import (
    BatchResult,
    CRITERION_NS04,
    CRITERION_NS05,
    DEVELOPABLE_ESA,
    ESA_CLASS_LABELS,
    ESA_TO_CLC_APPROX,
    FAVOURABLE_ESA,
    MODERATE_ESA,
    NATURAL_SEMINATURAL_ESA,
    NON_EU_COUNTRIES,
    SOURCE_NAME,
    UNFAVOURABLE_ESA,
    RingLandCover,
    SiteEnrichmentSummary,
    WorldCoverResult,
)
from atoms_vs_ashes.connectors.worldcover.parsers import (
    assess_buildable_adequacy,
    build_ns04_comment,
    compute_buildable_metrics,
    is_non_eu,
)

__all__ = [
    "BatchResult",
    "CRITERION_NS04",
    "CRITERION_NS05",
    "DEVELOPABLE_ESA",
    "ESA_CLASS_LABELS",
    "ESA_TO_CLC_APPROX",
    "FAVOURABLE_ESA",
    "MODERATE_ESA",
    "NATURAL_SEMINATURAL_ESA",
    "NON_EU_COUNTRIES",
    "RingLandCover",
    "SOURCE_NAME",
    "SiteEnrichmentSummary",
    "UNFAVOURABLE_ESA",
    "WorldCoverConnector",
    "WorldCoverResult",
    "assess_buildable_adequacy",
    "build_ns04_comment",
    "compute_buildable_metrics",
    "is_non_eu",
]
