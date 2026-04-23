# man_hours: 0.25
"""S-17 Eurostat Demographic Projections connector package.

Provides population projection and socioeconomic data for:
  - RI-06 (projected population density / receptor growth factor)
  - NS-09 (socioeconomic impact — GDP, employment, fiscal capacity)
  - NS-10 (workforce availability — working-age population, retraining index)
  - NS-12 (public opinion proxy — nuclear policy stance)

Data sources: EUROPOP2023/2019 (Eurostat), regional statistics (Eurostat),
curated NSO supplements + UN WPP 2024 for non-EU countries.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.eurostat_projections.client import (
    EurostatProjectionsConnector,
)
from atoms_vs_ashes.connectors.eurostat_projections.models import (
    CRITERION_IDS,
    BatchResult,
    EurostatProjectionsResult,
    IngestionResult,
    NsoProjection,
    PolicyProxyResult,
    PopulationProjectionResult,
    SiteEnrichmentSummary,
    SocioeconomicResult,
    WorkforceResult,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "EurostatProjectionsConnector",
    "EurostatProjectionsResult",
    "IngestionResult",
    "NsoProjection",
    "PolicyProxyResult",
    "PopulationProjectionResult",
    "SiteEnrichmentSummary",
    "SocioeconomicResult",
    "WorkforceResult",
]
