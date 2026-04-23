# man_hours: 0.25
"""S-29 HydroRIVERS (Global River Network) connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.hydrorivers.client import HydroRiversConnector
from atoms_vs_ashes.connectors.hydrorivers.models import (
    CRITERION_ID,
    BatchResult,
    RiverResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_ID",
    "HydroRiversConnector",
    "RiverResult",
    "SiteEnrichmentSummary",
]
