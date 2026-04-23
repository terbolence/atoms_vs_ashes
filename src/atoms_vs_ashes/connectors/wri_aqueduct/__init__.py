# man_hours: 0.25
"""S-33 WRI Aqueduct 4.0 (Water Stress) connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.wri_aqueduct.client import WriAqueductConnector
from atoms_vs_ashes.connectors.wri_aqueduct.models import (
    CRITERION_ID,
    BatchResult,
    WaterStressResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_ID",
    "SiteEnrichmentSummary",
    "WaterStressResult",
    "WriAqueductConnector",
]
