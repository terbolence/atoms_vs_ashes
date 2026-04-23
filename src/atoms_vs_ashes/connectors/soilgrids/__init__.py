# man_hours: 0.25
"""S-21 SoilGrids connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.soilgrids.client import SoilGridsConnector
from atoms_vs_ashes.connectors.soilgrids.models import (
    CRITERION_IDS,
    BatchResult,
    SiteEnrichmentSummary,
    SoilGridsResult,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "SiteEnrichmentSummary",
    "SoilGridsConnector",
    "SoilGridsResult",
]
