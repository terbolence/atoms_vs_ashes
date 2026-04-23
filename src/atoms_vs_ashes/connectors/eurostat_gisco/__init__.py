# man_hours: 0.25
"""S-16 Eurostat GISCO connector package.

Provides Urban Audit city proximity data for RI-05 (nearest city >50k,
settlement hierarchy) using Eurostat GISCO distribution API and
Eurostat statistics API (urb_cpop1 city populations).

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.eurostat_gisco.client import EurostatGiscoConnector
from atoms_vs_ashes.connectors.eurostat_gisco.models import (
    CRITERION_IDS,
    BatchResult,
    CityProximityResult,
    CityRecord,
    EurostatGiscoResult,
    NearbyCityRecord,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "CityProximityResult",
    "CityRecord",
    "EurostatGiscoConnector",
    "EurostatGiscoResult",
    "NearbyCityRecord",
    "SiteEnrichmentSummary",
]
