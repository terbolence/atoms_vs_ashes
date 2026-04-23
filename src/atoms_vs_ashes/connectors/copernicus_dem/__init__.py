# man_hours: 0.25
"""S-19 Copernicus DEM GLO-30 connector package.

Reads Cloud-Optimized GeoTIFF tiles from AWS Open Data to compute
slope gradient, elevation statistics, and terrain ruggedness.
Serves criteria NH-04a, NH-08d, RI-01d, EP-03a, NS-04a/b.

Public API — import from this package, not from internal submodules.
"""

from atoms_vs_ashes.connectors.copernicus_dem.client import CopernicusDemConnector
from atoms_vs_ashes.connectors.copernicus_dem.models import (
    CRITERION_IDS,
    PRIMARY_CRITERION,
    BatchResult,
    DemResult,
    ElevationStats,
    SiteEnrichmentSummary,
    SlopeStats,
    TerrainRuggedness,
)

__all__ = [
    "BatchResult",
    "CRITERION_IDS",
    "CopernicusDemConnector",
    "DemResult",
    "ElevationStats",
    "PRIMARY_CRITERION",
    "SiteEnrichmentSummary",
    "SlopeStats",
    "TerrainRuggedness",
]
