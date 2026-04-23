# man_hours: 2.0
"""ESA WorldCover data models, class crosswalk, and constants.

ESA WorldCover v200 (2021) provides 11 land cover classes at 10 m
resolution globally.  This module maps those classes to CORINE-equivalent
favourability categories so the same buildable-area metrics can be
computed for non-EU sites.

Pure data definitions — no I/O, no HTTP, no database imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


CRITERION_NS04 = "NS-04"
CRITERION_NS05 = "NS-05"
SOURCE_NAME = "esa_worldcover_2021_v200"
SOURCE_URL = "https://esa-worldcover.org/en/data-access"
RASTER_DIR_DEFAULT = "sources/worldcover"

S3_BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    "/v200/2021/map"
)
TILE_PATTERN = "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"

# ESA WorldCover v200 class values and labels
ESA_CLASS_LABELS: dict[int, str] = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}

# Crosswalk: ESA WorldCover class → CORINE-equivalent favourability
# for buildable area assessment (A15 / NS-05)
FAVOURABLE_ESA: frozenset[int] = frozenset({
    40,  # Cropland — equivalent to CORINE 211/231 (arable/pasture)
    50,  # Built-up — equivalent to CORINE 111-142 (artificial surfaces)
    60,  # Bare / sparse — equivalent to CORINE 331/333
})

MODERATE_ESA: frozenset[int] = frozenset({
    20,  # Shrubland — equivalent to CORINE 322/323/324
    30,  # Grassland — equivalent to CORINE 321
    100, # Moss and lichen — marginal but developable
})

UNFAVOURABLE_ESA: frozenset[int] = frozenset({
    10,  # Tree cover — equivalent to CORINE 311-313 (forest)
    70,  # Snow and ice — equivalent to CORINE 335
    80,  # Permanent water — equivalent to CORINE 511-523
    90,  # Herbaceous wetland — equivalent to CORINE 411-412
    95,  # Mangroves — equivalent to CORINE 421-423
})

# ESA classes considered "developable" (parallel to CORINE DEVELOPABLE_CODES)
DEVELOPABLE_ESA: frozenset[int] = frozenset({
    40,  # Cropland
    50,  # Built-up
    60,  # Bare / sparse
    30,  # Grassland
})

# Natural/semi-natural classes (ecological sensitivity indicator)
NATURAL_SEMINATURAL_ESA: frozenset[int] = frozenset({
    10, 20, 30, 70, 80, 90, 95, 100,
})

# ESA class → approximate CORINE code for dominant_land_class column
ESA_TO_CLC_APPROX: dict[int, str] = {
    10: "311",   # Tree cover → Broad-leaved forest
    20: "322",   # Shrubland → Moors and heathland
    30: "321",   # Grassland → Natural grasslands
    40: "211",   # Cropland → Non-irrigated arable land
    50: "112",   # Built-up → Discontinuous urban fabric
    60: "333",   # Bare/sparse → Sparsely vegetated areas
    70: "335",   # Snow/ice → Glaciers and perpetual snow
    80: "512",   # Water → Water bodies
    90: "411",   # Wetland → Inland marshes
    95: "421",   # Mangroves → Salt marshes
    100: "333",  # Moss/lichen → Sparsely vegetated areas
}

# Non-EU countries where WorldCover is the primary land cover source
NON_EU_COUNTRIES: frozenset[str] = frozenset({
    "BA", "RS", "ME", "XK", "AL", "MK", "MD", "UA", "BY", "AM", "TR",
})


@dataclass
class RingLandCover:
    """Land cover area breakdown for a single ring from WorldCover raster."""

    label: str
    inner_m: float
    outer_m: float
    total_area_ha: float
    by_class: dict[int, float] = field(default_factory=dict)
    developable_ha: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "inner_m": self.inner_m,
            "outer_m": self.outer_m,
            "total_area_ha": round(self.total_area_ha, 2),
            "by_class": {str(k): round(v, 3) for k, v in self.by_class.items()},
            "developable_ha": round(self.developable_ha, 3),
        }


@dataclass
class WorldCoverResult:
    """Full WorldCover classification result for a site."""

    lat: float
    lon: float
    rings: list[RingLandCover] = field(default_factory=list)
    total_developable_ha: float = 0.0
    patch_count: int = 0
    largest_contiguous_ha: float = 0.0
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "rings": [r.to_dict() for r in self.rings],
            "total_developable_ha": round(self.total_developable_ha, 3),
            "patch_count": self.patch_count,
            "largest_contiguous_ha": round(self.largest_contiguous_ha, 2),
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site result summary for batch logging."""

    site_id: uuid.UUID
    site_name: str
    status: str  # ok | cached | error | skipped
    buildable_area_ha: float | None = None
    dominant_land_class: str | None = None
    quality: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate result for a WorldCover batch run."""

    run_id: str = ""
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    skipped_eu: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)
