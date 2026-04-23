# man_hours: 0.25
"""S-09 GFMS (Global Flood Monitoring System) connector package.

Two-phase flood frequency connector:
  Phase A: Archive ingestion — download binary grids, compute statistics.
  Phase B: Site enrichment — sample pre-computed statistics raster.

Criteria: NH-08 (coastal flood, weak fluvial proxy), NH-09 (river flooding).
"""

from atoms_vs_ashes.connectors.gfms.client import GfmsConnector
from atoms_vs_ashes.connectors.gfms.models import (
    CRITERION_IDS,
    SOURCE_NAME,
    BatchResult,
    CoastalFloodProxy,
    DamBreakProxy,
    FloodStatisticsRaster,
    GfmsResult,
    SiteEnrichmentSummary,
)

__all__ = [
    "GfmsConnector",
    "GfmsResult",
    "FloodStatisticsRaster",
    "CoastalFloodProxy",
    "DamBreakProxy",
    "BatchResult",
    "SiteEnrichmentSummary",
    "CRITERION_IDS",
    "SOURCE_NAME",
]
