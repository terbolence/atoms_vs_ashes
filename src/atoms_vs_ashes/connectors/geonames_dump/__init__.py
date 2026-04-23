# man_hours: 0.25
"""GeoNames cities5000 dump — global RI-05 nearest city (≥50k) without web API."""

from atoms_vs_ashes.connectors.geonames_dump.client import GeonamesDumpConnector
from atoms_vs_ashes.connectors.geonames_dump.models import (
    EXTENDED_DATA_KEY,
    BatchResult,
    NearestGeonamesResult,
    RI05_QUALITY_TAG,
    SOURCE_NAME,
)

__all__ = [
    "BatchResult",
    "EXTENDED_DATA_KEY",
    "GeonamesDumpConnector",
    "NearestGeonamesResult",
    "RI05_QUALITY_TAG",
    "SOURCE_NAME",
]
