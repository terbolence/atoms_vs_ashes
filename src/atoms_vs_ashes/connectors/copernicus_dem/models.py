# man_hours: 2.0
"""Result dataclasses and domain constants for S-19 Copernicus DEM GLO-30.

Pure data definitions — no I/O, no HTTP, no database imports.
Serves criteria NH-04a (slope gradient), NH-08d (tsunami elevation proxy),
RI-01d (terrain channeling), EP-03a (topographic barriers),
NS-04a (earthworks proxy), NS-04b (drainage micro-topography).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NH-04", "NH-08", "RI-01", "EP-03", "NS-04")
PRIMARY_CRITERION = "NH-04"
SOURCE_NAME = "copernicus_dem_glo30"
SOURCE_URL = "https://registry.opendata.aws/copernicus-dem/"
SOURCE_DESCRIPTION = (
    "Copernicus DEM GLO-30 — Global 30-metre Digital Elevation Model. "
    "Based on TanDEM-X SAR data (2011–2015), edited with ICESat-2. "
    "Cloud-Optimized GeoTIFF tiles on AWS Open Data (public S3 bucket). "
    "ESA / Copernicus Programme. Free and open access."
)

S3_BUCKET = "copernicus-dem-30m"
S3_REGION = "eu-central-1"

HTTPS_BASE_URL = (
    "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
)

RASTER_CRS = "EPSG:4326"
RESOLUTION_M = 30
VERTICAL_DATUM = "EGM2008"

DEFAULT_BUFFER_M = 5_000
SLOPE_BUFFER_M = 1_000
CACHE_TTL_DAYS = 365

# E-rule E3 thresholds (from spec §3)
SLOPE_CAUTION_DEG = 15.0
SLOPE_FAIL_DEG = 30.0

# Tsunami elevation proxy threshold (coastal sites)
COASTAL_ELEVATION_CAUTION_M = 10.0

# Slope stability classification
SLOPE_CLASS_MAP: dict[str, tuple[float, float]] = {
    "flat": (0.0, 2.0),
    "gentle": (2.0, 5.0),
    "moderate": (5.0, 10.0),
    "steep": (10.0, 15.0),
    "very_steep": (15.0, 30.0),
    "extreme": (30.0, 90.0),
}

# Study area bounding box (WGS84) — all 23 in-scope countries
INSCOPE_LAT_MIN, INSCOPE_LAT_MAX = 35.0, 60.0
INSCOPE_LON_MIN, INSCOPE_LON_MAX = 12.0, 46.0


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ElevationStats:
    """Elevation statistics within a buffer zone."""

    site_elevation_m: float | None = None
    min_m: float | None = None
    max_m: float | None = None
    mean_m: float | None = None
    std_m: float | None = None
    relief_m: float | None = None  # max - min

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_elevation_m": _round_or_none(self.site_elevation_m, 1),
            "min_m": _round_or_none(self.min_m, 1),
            "max_m": _round_or_none(self.max_m, 1),
            "mean_m": _round_or_none(self.mean_m, 1),
            "std_m": _round_or_none(self.std_m, 2),
            "relief_m": _round_or_none(self.relief_m, 1),
        }


@dataclass
class SlopeStats:
    """Slope statistics within a buffer zone."""

    max_deg: float | None = None
    mean_deg: float | None = None
    p90_deg: float | None = None
    p95_deg: float | None = None
    pct_above_15: float | None = None  # % of cells > 15°
    pct_above_30: float | None = None  # % of cells > 30°

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_deg": _round_or_none(self.max_deg, 2),
            "mean_deg": _round_or_none(self.mean_deg, 2),
            "p90_deg": _round_or_none(self.p90_deg, 2),
            "p95_deg": _round_or_none(self.p95_deg, 2),
            "pct_above_15": _round_or_none(self.pct_above_15, 1),
            "pct_above_30": _round_or_none(self.pct_above_30, 1),
        }


@dataclass
class TerrainRuggedness:
    """Terrain Ruggedness Index (TRI) within a buffer zone."""

    mean_tri: float | None = None
    max_tri: float | None = None
    tri_class: str | None = None  # "level" / "nearly_level" / ... / "extremely_rugged"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_tri": _round_or_none(self.mean_tri, 2),
            "max_tri": _round_or_none(self.max_tri, 2),
            "tri_class": self.tri_class,
        }


# Riley et al. (1999) TRI classification
TRI_CLASS_MAP: dict[str, tuple[float, float]] = {
    "level": (0.0, 80.0),
    "nearly_level": (80.0, 116.0),
    "slightly_rugged": (116.0, 161.0),
    "intermediately_rugged": (161.0, 239.0),
    "moderately_rugged": (239.0, 497.0),
    "highly_rugged": (497.0, 958.0),
    "extremely_rugged": (958.0, float("inf")),
}


@dataclass
class DemResult:
    """Complete DEM analysis for a single site."""

    lat: float
    lon: float
    elevation: ElevationStats = field(default_factory=ElevationStats)
    slope: SlopeStats = field(default_factory=SlopeStats)
    tri: TerrainRuggedness = field(default_factory=TerrainRuggedness)
    slope_stability_class: str | None = None
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "elevation": self.elevation.to_dict(),
            "slope": self.slope.to_dict(),
            "tri": self.tri.to_dict(),
            "slope_stability_class": self.slope_stability_class,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached"
    elevation_m: float | None = None
    max_slope_deg: float | None = None
    slope_class: str | None = None
    source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "elevation_m": s.elevation_m,
                    "max_slope_deg": s.max_slope_deg,
                    "slope_class": s.slope_class,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        if mins >= 1:
            elapsed = f"{mins:.1f} min"
        else:
            elapsed = f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _round_or_none(val: float | None, ndigits: int) -> float | None:
    if val is None:
        return None
    return round(val, ndigits)


def classify_slope(slope_deg: float) -> str:
    """Map a representative slope angle to a stability class."""
    for cls, (lo, hi) in SLOPE_CLASS_MAP.items():
        if lo <= slope_deg < hi:
            return cls
    return "extreme"


def classify_tri(mean_tri: float) -> str:
    """Map mean TRI value to Riley et al. (1999) class."""
    for cls, (lo, hi) in TRI_CLASS_MAP.items():
        if lo <= mean_tri < hi:
            return cls
    return "extremely_rugged"


def tile_id_for_point(lat: float, lon: float) -> str:
    """Compute the S3 tile directory name for a given WGS84 coordinate.

    Copernicus DEM tiles are named by the SW corner of each 1°×1° cell.
    For lat >= 0, the tile label is N{floor(lat)}, for lat < 0 it is S{ceil(|lat|)}.
    For lon >= 0, the tile label is E{floor(lon)}, for lon < 0 it is W{ceil(|lon|)}.
    """
    import math as _math

    if lat >= 0:
        lat_label = f"N{int(_math.floor(lat)):02d}"
    else:
        lat_label = f"S{int(_math.ceil(abs(lat))):02d}"

    if lon >= 0:
        lon_label = f"E{int(_math.floor(lon)):03d}"
    else:
        lon_label = f"W{int(_math.ceil(abs(lon))):03d}"

    return f"Copernicus_DSM_COG_10_{lat_label}_00_{lon_label}_00_DEM"


def s3_key_for_tile(tile_id: str) -> str:
    """Return the full S3 object key for a tile."""
    return f"{tile_id}/{tile_id}.tif"


def https_url_for_tile(tile_id: str) -> str:
    """Return the HTTPS URL for direct COG access."""
    return f"{HTTPS_BASE_URL}/{s3_key_for_tile(tile_id)}"


def tiles_for_bbox(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float,
) -> list[str]:
    """Return all tile IDs covering a bounding box."""
    import math as _math

    lat_start = int(_math.floor(min_lat))
    lat_end = int(_math.floor(max_lat))
    lon_start = int(_math.floor(min_lon))
    lon_end = int(_math.floor(max_lon))

    tiles: list[str] = []
    for lat_i in range(lat_start, lat_end + 1):
        for lon_i in range(lon_start, lon_end + 1):
            tiles.append(tile_id_for_point(float(lat_i) + 0.5, float(lon_i) + 0.5))
    return tiles
