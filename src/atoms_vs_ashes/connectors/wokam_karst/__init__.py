# man_hours: 0.25
"""S-25 WOKAM (World Karst Aquifer Map) connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.wokam_karst.client import WokamKarstConnector
from atoms_vs_ashes.connectors.wokam_karst.models import (
    CRITERION_ID,
    BatchResult,
    KarstResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_ID",
    "KarstResult",
    "SiteEnrichmentSummary",
    "WokamKarstConnector",
]
