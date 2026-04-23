# man_hours: 1.5
"""Result dataclasses and domain constants for S-09 GFMS flood connector.

Pure data definitions — no I/O, no HTTP, no database imports.
Criteria served: NH-08 (coastal flooding, weak fluvial proxy),
                 NH-09 (river flooding, flash flood, dam-break proxy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("NH-08", "NH-09")
SOURCE_NAME = "gfms_flood_detection"
SOURCE_URL = "http://flood.umd.edu/"
BASE_DOWNLOAD_URL = "http://eagle2.umd.edu/flood/download"

# Grid specification (from GFMS_readme.pdf):
#   row=800, col=2458, xllcorner=-127.25, yllcorner=-50, cellsize=0.125
#   Row 0 = BOTTOM of grid (lat -50), row 799 = TOP (lat +50).
#   NoData = -9999.
GRID_ROWS = 800
GRID_COLS = 2458
RESOLUTION_DEG = 0.125
YLLCORNER = -50.0     # latitude of bottom edge of row-0
XLLCORNER = -127.25   # longitude of left edge of col-0
LAT_MAX = 50.0        # top latitude of grid
LON_MAX = XLLCORNER + GRID_COLS * RESOLUTION_DEG  # 180.0

EXPECTED_FILE_SIZE = GRID_ROWS * GRID_COLS * 4  # 7,865,600 bytes (float32)
NODATA = -9999.0

# Project sub-grid (lat 35–50°N, lon 12–45°E)
PROJ_LAT_MAX = 50.0
PROJ_LAT_MIN = 35.0
PROJ_LON_MIN = 12.0
PROJ_LON_MAX = 45.0

# Sub-grid row/col bounds in global grid (bottom-up orientation).
# Row = int((lat - YLLCORNER) / cellsize)
SUBGRID_ROW_START = 680   # row for 35°N = (35 - (-50)) / 0.125 = 680
SUBGRID_ROW_END = 800     # row for 50°N = (50 - (-50)) / 0.125 = 800 (top of grid)
SUBGRID_COL_START = 1114  # col for 12°E = (12 - (-127.25)) / 0.125 = 1114
SUBGRID_COL_END = 1378    # col for 45°E = (45 - (-127.25)) / 0.125 = 1378

SUBGRID_ROWS = SUBGRID_ROW_END - SUBGRID_ROW_START   # 120
SUBGRID_COLS = SUBGRID_COL_END - SUBGRID_COL_START   # 264

# Flood susceptibility thresholds (defaults; overridable via config)
HIGH_ANNUAL_PROB = 0.10
MODERATE_ANNUAL_PROB = 0.03
LOW_ANNUAL_PROB = 0.005

# Validation thresholds
MAX_PLAUSIBLE_INTENSITY_MM = 5000.0
MIN_SNAPSHOTS_FOR_STATISTICS = 100
COASTAL_DISTANCE_THRESHOLD_KM = 20.0

# Dam-break proxy: max_intensity > ratio × p95 → anomalous flag
DAM_BREAK_ANOMALY_RATIO = 3.0

# Courtesy delay between file downloads (seconds)
INTER_REQUEST_DELAY_S = 0.5

# Binary file endianness — spec says little-endian; verified empirically
BINARY_DTYPE = "<f4"  # IEEE 754 float32, little-endian


# ---------------------------------------------------------------------------
# Internal statistics raster (computed once, cached on disk)
# ---------------------------------------------------------------------------

@dataclass
class FloodStatisticsRaster:
    """Per-pixel flood frequency statistics over the project sub-grid (120×264)."""

    event_count: np.ndarray       # shape (120, 264), int32
    max_intensity: np.ndarray     # shape (120, 264), float32
    annual_probability: np.ndarray  # shape (120, 264), float32
    p95_intensity: np.ndarray     # shape (120, 264), float32
    mean_nonzero_intensity: np.ndarray  # shape (120, 264), float32
    n_snapshots: int
    n_years: float
    start_year: int
    end_year: int
    temporal_sampling: str        # "weekly" | "daily_recent" | "full"
    bbox: tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    resolution: float = RESOLUTION_DEG

    def to_npz_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "max_intensity": self.max_intensity,
            "annual_probability": self.annual_probability,
            "p95_intensity": self.p95_intensity,
            "mean_nonzero_intensity": self.mean_nonzero_intensity,
            "n_snapshots": np.int32(self.n_snapshots),
            "n_years": np.float64(self.n_years),
            "start_year": np.int32(self.start_year),
            "end_year": np.int32(self.end_year),
            "temporal_sampling_bytes": self.temporal_sampling.encode(),
            "resolution": np.float64(self.resolution),
        }

    @classmethod
    def from_npz(cls, data: Any) -> FloodStatisticsRaster:
        return cls(
            event_count=data["event_count"],
            max_intensity=data["max_intensity"],
            annual_probability=data["annual_probability"],
            p95_intensity=data["p95_intensity"],
            mean_nonzero_intensity=data["mean_nonzero_intensity"],
            n_snapshots=int(data["n_snapshots"]),
            n_years=float(data["n_years"]),
            start_year=int(data["start_year"]),
            end_year=int(data["end_year"]),
            temporal_sampling=data["temporal_sampling_bytes"].tobytes().decode(),
            bbox=(PROJ_LON_MIN, PROJ_LAT_MIN, PROJ_LON_MAX, PROJ_LAT_MAX),
            resolution=float(data["resolution"]),
        )


# ---------------------------------------------------------------------------
# NH-08 coastal proxy
# ---------------------------------------------------------------------------

@dataclass
class CoastalFloodProxy:
    """Weak NH-08 coastal flood proxy derived from GFMS fluvial signal."""

    is_coastal: bool
    coastal_flood_events: int
    note: str = (
        "GFMS models fluvial flooding only; "
        "coastal storm surge not captured"
    )
    coastal_distance_km: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_coastal": self.is_coastal,
            "coastal_flood_events": self.coastal_flood_events,
            "coastal_distance_km": self.coastal_distance_km,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# NH-09 dam-break proxy
# ---------------------------------------------------------------------------

@dataclass
class DamBreakProxy:
    """Weak NH-09 dam-break proxy from flood intensity anomaly detection."""

    max_anomaly_ratio: float | None
    anomalous_event_flag: bool
    note: str = "GFMS does not model dams; anomaly proxy only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_anomaly_ratio": (
                round(self.max_anomaly_ratio, 2)
                if self.max_anomaly_ratio is not None else None
            ),
            "anomalous_event_flag": self.anomalous_event_flag,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Top-level result for a single site
# ---------------------------------------------------------------------------

@dataclass
class GfmsResult:
    """Complete GFMS flood assessment for a single site."""

    lat: float
    lon: float
    pixel_lat: float
    pixel_lon: float
    pixel_distance_km: float
    flood_event_count: int
    annual_flood_probability: float
    flood_frequency_per_year: float
    max_intensity_mm: float
    p95_intensity_mm: float | None
    mean_event_intensity_mm: float | None
    flood_susceptibility: str                # "high" | "moderate" | "low" | "negligible"
    coastal_flood_proxy: CoastalFloodProxy | None
    dam_break_proxy: DamBreakProxy | None
    analysis_period: tuple[int, int]         # (start_year, end_year)
    n_snapshots_analysed: int
    temporal_sampling: str
    resolution_degrees: float = RESOLUTION_DEG
    model_description: str = "GFMS DRIVE (VIC+DRTR), GPM IMERG input"
    source: str = SOURCE_NAME
    quality: str = "high"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "pixel_lat": self.pixel_lat,
            "pixel_lon": self.pixel_lon,
            "pixel_distance_km": round(self.pixel_distance_km, 2),
            "flood_event_count": self.flood_event_count,
            "annual_flood_probability": round(self.annual_flood_probability, 6),
            "flood_frequency_per_year": round(self.flood_frequency_per_year, 4),
            "max_intensity_mm": round(self.max_intensity_mm, 2),
            "p95_intensity_mm": (
                round(self.p95_intensity_mm, 2)
                if self.p95_intensity_mm is not None else None
            ),
            "mean_event_intensity_mm": (
                round(self.mean_event_intensity_mm, 2)
                if self.mean_event_intensity_mm is not None else None
            ),
            "flood_susceptibility": self.flood_susceptibility,
            "coastal_flood_proxy": (
                self.coastal_flood_proxy.to_dict()
                if self.coastal_flood_proxy else None
            ),
            "dam_break_proxy": (
                self.dam_break_proxy.to_dict()
                if self.dam_break_proxy else None
            ),
            "analysis_period": list(self.analysis_period),
            "n_snapshots_analysed": self.n_snapshots_analysed,
            "temporal_sampling": self.temporal_sampling,
            "resolution_degrees": self.resolution_degrees,
            "model_description": self.model_description,
            "source": self.source,
            "quality": self.quality,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Batch result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str                              # "ok" | "error" | "cached"
    flood_susceptibility: str | None = None
    annual_flood_probability: float | None = None
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
                    "flood_susceptibility": s.flood_susceptibility,
                    "annual_flood_probability": s.annual_flood_probability,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.failed} failed, {self.skipped_cached} cached ({elapsed})"
        )
