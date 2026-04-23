# man_hours: 0.25
"""S-39 OurAirports connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.ourairports.client import OurAirportsConnector
from atoms_vs_ashes.connectors.ourairports.models import (
    CRITERION_ID,
    AirportProximityResult,
    BatchResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "AirportProximityResult",
    "BatchResult",
    "CRITERION_ID",
    "OurAirportsConnector",
    "SiteEnrichmentSummary",
]
