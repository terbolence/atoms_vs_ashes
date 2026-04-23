# man_hours: 0.25
"""S-30 GloFAS v4 (River Discharge Reanalysis) connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.glofas_discharge.client import GlofasDischargeConnector
from atoms_vs_ashes.connectors.glofas_discharge.models import (
    CRITERION_ID,
    BatchResult,
    DischargeResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_ID",
    "DischargeResult",
    "GlofasDischargeConnector",
    "SiteEnrichmentSummary",
]
