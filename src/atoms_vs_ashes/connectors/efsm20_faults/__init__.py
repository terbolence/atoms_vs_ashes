# man_hours: 0.25
"""S-18 EFSM20 (European Fault-Source Model 2020) connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.efsm20_faults.client import Efsm20FaultsConnector
from atoms_vs_ashes.connectors.efsm20_faults.models import (
    CRITERION_ID,
    BatchResult,
    FaultResult,
    FaultTrace,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_ID",
    "Efsm20FaultsConnector",
    "FaultResult",
    "FaultTrace",
    "SiteEnrichmentSummary",
]
