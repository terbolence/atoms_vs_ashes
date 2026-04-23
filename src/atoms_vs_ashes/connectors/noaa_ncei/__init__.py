# man_hours: 0.25
"""S-11 NOAA NCEI connector package — meteorological hazard data.

Public API — import from this package, not from internal submodules.
Criteria served: NH-10 (extreme winds, tornadoes, tropical storms),
                 NH-11 (intense precipitation, hail),
                 NH-12 (air temperature extremes).
"""

from atoms_vs_ashes.connectors.noaa_ncei.client import NoaaNceiConnector
from atoms_vs_ashes.connectors.noaa_ncei.models import (
    BatchResult,
    CONNECTOR_SLUG,
    CRITERION_IDS,
    NoaaNceiResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CONNECTOR_SLUG",
    "CRITERION_IDS",
    "NoaaNceiConnector",
    "NoaaNceiResult",
    "SiteEnrichmentSummary",
]
