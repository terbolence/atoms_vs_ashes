# man_hours: 0.25
"""S-23 BDTICM Depth-to-Bedrock connector package.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.bdticm_bedrock.client import BdticmBedrockConnector
from atoms_vs_ashes.connectors.bdticm_bedrock.models import (
    CRITERION_ID,
    BatchResult,
    BedrockResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "BedrockResult",
    "BdticmBedrockConnector",
    "CRITERION_ID",
    "SiteEnrichmentSummary",
]
