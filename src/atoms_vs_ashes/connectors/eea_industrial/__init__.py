# man_hours: 0.25
"""S-37 EEA Industrial Emissions Portal connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.eea_industrial.client import EeaIndustrialConnector
from atoms_vs_ashes.connectors.eea_industrial.models import (
    CRITERION_IDS,
    BatchResult,
    IndustrialProximityResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "EeaIndustrialConnector",
    "IndustrialProximityResult",
    "SiteEnrichmentSummary",
]
