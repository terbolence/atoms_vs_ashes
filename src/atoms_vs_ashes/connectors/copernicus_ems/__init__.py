# man_hours: 0.25
"""S-10 Copernicus EMS connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.copernicus_ems.client import CopernicusEmsConnector
from atoms_vs_ashes.connectors.copernicus_ems.models import (
    BatchResult,
    CatalogueIngestionResult,
    FlashFloodAssessment,
    FloodFootprint,
    FootprintSummary,
    RapidActivation,
    RrmActivation,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.copernicus_ems.parsers import (
    classify_susceptibility,
    determine_quality,
    parse_rapid_activation,
    parse_rrm_activation,
)

__all__ = [
    "BatchResult",
    "CatalogueIngestionResult",
    "CopernicusEmsConnector",
    "FlashFloodAssessment",
    "FloodFootprint",
    "FootprintSummary",
    "RapidActivation",
    "RrmActivation",
    "SiteEnrichmentSummary",
    "classify_susceptibility",
    "determine_quality",
    "parse_rapid_activation",
    "parse_rrm_activation",
]
