# man_hours: 0.25
"""S-20 GHSL GHS-POP population grid connector package.

Computes population density within EPZ ring buffers (5/16/25/80 km)
from the GHS-POP R2023A 100 m raster (Mollweide projection).
Serves criteria RI-04, RI-05, RI-06, and EP-01.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.ghsl_pop.client import GhslPopConnector
from atoms_vs_ashes.connectors.ghsl_pop.models import (
    CRITERION_IDS,
    EPZ_RADII_KM,
    EPZ_RADII_M,
    BatchResult,
    GhslPopResult,
    NearestCity,
    RingPopulation,
    SiteEnrichmentSummary,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "EPZ_RADII_KM",
    "EPZ_RADII_M",
    "GhslPopConnector",
    "GhslPopResult",
    "NearestCity",
    "RingPopulation",
    "SiteEnrichmentSummary",
]
