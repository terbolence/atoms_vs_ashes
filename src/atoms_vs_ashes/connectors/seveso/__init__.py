# man_hours: 0.25
"""S-12 SEVESO III connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.seveso.client import SevesoConnector
from atoms_vs_ashes.connectors.seveso.models import (
    CRITERION_IDS,
    BatchResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "SevesoConnector",
    "SiteEnrichmentSummary",
]
