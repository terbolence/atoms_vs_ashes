# man_hours: 2.0
"""Pure computation functions for the S-09 GFMS connector.

No I/O, no HTTP, no database. All functions are deterministic and fully
testable without network access. Consumed by client.py.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from atoms_vs_ashes.connectors.gfms.models import (
    BINARY_DTYPE,
    COASTAL_DISTANCE_THRESHOLD_KM,
    DAM_BREAK_ANOMALY_RATIO,
    EXPECTED_FILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    HIGH_ANNUAL_PROB,
    LAT_MAX,
    LOW_ANNUAL_PROB,
    MAX_PLAUSIBLE_INTENSITY_MM,
    MODERATE_ANNUAL_PROB,
    NODATA,
    PROJ_LAT_MAX,
    PROJ_LAT_MIN,
    PROJ_LON_MAX,
    PROJ_LON_MIN,
    RESOLUTION_DEG,
    SOURCE_NAME,
    SUBGRID_COL_END,
    SUBGRID_COL_START,
    SUBGRID_COLS,
    SUBGRID_ROW_END,
    SUBGRID_ROW_START,
    SUBGRID_ROWS,
    XLLCORNER,
    YLLCORNER,
    CoastalFloodProxy,
    DamBreakProxy,
    FloodStatisticsRaster,
    GfmsResult,
)

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Coordinate mapping (pure math)
# ---------------------------------------------------------------------------

def grid_coords_to_pixel(lat: float, lon: float) -> tuple[int, int]:
    """Convert WGS84 lat/lon to global grid pixel index (row, col).

    Bottom-up orientation: row 0 = lat -50 (YLLCORNER), row 799 = lat +50.
    Col 0 = lon -127.25 (XLLCORNER).
    """
    row = int((lat - YLLCORNER) / RESOLUTION_DEG)
    col = int((lon - XLLCORNER) / RESOLUTION_DEG)
    row = max(0, min(row, GRID_ROWS - 1))
    col = max(0, min(col, GRID_COLS - 1))
    return row, col


def pixel_to_subgrid(global_row: int, global_col: int) -> tuple[int, int]:
    """Convert global grid pixel to project sub-grid pixel.

    Project sub-grid: rows 680–799, cols 1114–1377 in the global grid.
    Returns (sub_row, sub_col). Values may be negative or ≥ sub-grid size
    if the pixel is outside the project bbox.
    """
    sub_row = global_row - SUBGRID_ROW_START
    sub_col = global_col - SUBGRID_COL_START
    return sub_row, sub_col


def pixel_centre_coords(global_row: int, global_col: int) -> tuple[float, float]:
    """Return the lat/lon of the centre of a global grid pixel.

    Bottom-up: lat = YLLCORNER + (row + 0.5) * cellsize.
    """
    lat = YLLCORNER + (global_row + 0.5) * RESOLUTION_DEG
    lon = XLLCORNER + (global_col + 0.5) * RESOLUTION_DEG
    return lat, lon


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two WGS84 points in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_within_subgrid(sub_row: int, sub_col: int) -> bool:
    """Return True if sub-grid indices are within bounds."""
    return 0 <= sub_row < SUBGRID_ROWS and 0 <= sub_col < SUBGRID_COLS


def is_within_project_bbox(lat: float, lon: float) -> bool:
    """Return True if coordinates are within the project bounding box."""
    return PROJ_LAT_MIN <= lat <= PROJ_LAT_MAX and PROJ_LON_MIN <= lon <= PROJ_LON_MAX


def is_within_coverage(lat: float) -> bool:
    """Return True if latitude is within GFMS coverage (50°S–50°N)."""
    return -50.0 <= lat <= 50.0


# ---------------------------------------------------------------------------
# Binary grid parsing
# ---------------------------------------------------------------------------

# The project sub-grid occupies the TOP 120 rows (680-799) of the 800-row grid.
# For a full-file download we read the whole 7,865,600-byte file and slice.
# We do NOT use HTTP Range requests because the sub-grid is at the END of the file,
# not the beginning (bottom-up row order means high latitudes = high row indices).
# Instead we download the full file into memory and extract.
SUBGRID_RANGE_BYTES = EXPECTED_FILE_SIZE  # full file: 7,865,600 bytes


def parse_subgrid_from_bytes(data: bytes) -> np.ndarray | None:
    """Parse the project sub-grid from a complete GFMS binary file in memory.

    ``data`` must be exactly ``EXPECTED_FILE_SIZE`` (7,865,600 bytes) — the
    full 800×2458 float32 grid. The project sub-grid (rows 680-799, cols
    1114-1377) is extracted and returned as a (120, 264) float32 array.

    Returns None if the buffer is malformed.
    """
    if len(data) != EXPECTED_FILE_SIZE:
        return None

    raw = np.frombuffer(data, dtype=BINARY_DTYPE)

    if raw.size != GRID_ROWS * GRID_COLS:
        return None

    grid = raw.reshape(GRID_ROWS, GRID_COLS)

    subgrid = grid[SUBGRID_ROW_START:SUBGRID_ROW_END,
                   SUBGRID_COL_START:SUBGRID_COL_END].copy().astype(np.float32)

    # Replace nodata (-9999) and any other negatives with 0 (no-flood)
    subgrid = np.where(np.isfinite(subgrid), subgrid, 0.0)
    subgrid = np.where(subgrid < 0, 0.0, subgrid)

    return subgrid


def parse_binary_grid(file_path: Path) -> np.ndarray | None:
    """Read a GFMS binary grid file and return the project sub-grid.

    Returns a (120, 264) float32 array or None if the file is malformed.
    The nodata sentinel (-9999) and any negative values are replaced with 0.
    """
    size = file_path.stat().st_size
    if size != EXPECTED_FILE_SIZE:
        return None

    raw = np.fromfile(str(file_path), dtype=BINARY_DTYPE)

    if raw.size != GRID_ROWS * GRID_COLS:
        return None

    grid = raw.reshape(GRID_ROWS, GRID_COLS)

    subgrid = grid[SUBGRID_ROW_START:SUBGRID_ROW_END, SUBGRID_COL_START:SUBGRID_COL_END]
    subgrid = subgrid.copy().astype(np.float32)

    subgrid = np.where(np.isfinite(subgrid), subgrid, 0.0)
    subgrid = np.where(subgrid < 0, 0.0, subgrid)

    return subgrid


# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------

def compute_flood_statistics(
    subgrids: list[np.ndarray],
    n_years: float,
    temporal_sampling: str,
    start_year: int,
    end_year: int,
) -> FloodStatisticsRaster:
    """Compute per-pixel flood frequency statistics from a list of sub-grids.

    Parameters
    ----------
    subgrids
        List of (120, 264) float32 arrays. Values > 0 indicate flooding.
    n_years
        Total years spanned by the snapshot collection.
    temporal_sampling
        Sampling strategy label.
    start_year, end_year
        Analysis period.
    """
    n = len(subgrids)
    if n == 0:
        empty = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)
        return FloodStatisticsRaster(
            event_count=np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.int32),
            max_intensity=empty.copy(),
            annual_probability=empty.copy(),
            p95_intensity=empty.copy(),
            mean_nonzero_intensity=empty.copy(),
            n_snapshots=0,
            n_years=n_years,
            start_year=start_year,
            end_year=end_year,
            temporal_sampling=temporal_sampling,
            bbox=(PROJ_LON_MIN, PROJ_LAT_MIN, PROJ_LON_MAX, PROJ_LAT_MAX),
        )

    stack = np.stack(subgrids, axis=0)  # (n, 120, 264)

    event_count = np.sum(stack > 0, axis=0).astype(np.int32)

    max_intensity = np.max(stack, axis=0).astype(np.float32)

    annual_probability = np.where(
        n_years > 0,
        event_count.astype(np.float32) / n,
        0.0,
    ).astype(np.float32)

    # P95 of non-zero values per pixel (set to 0 if no flood events)
    # Use numpy percentile with a masked approach
    p95_intensity = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)
    mean_nonzero = np.zeros((SUBGRID_ROWS, SUBGRID_COLS), dtype=np.float32)

    # Vectorised approach: compute percentile along axis 0 on the full stack,
    # then zero out pixels where event_count == 0 (no floods → p95 irrelevant)
    nonzero_stack = np.where(stack > 0, stack, np.nan)
    with np.errstate(all="ignore"):
        p95_intensity = np.nanpercentile(nonzero_stack, 95, axis=0).astype(np.float32)
        mean_nonzero = np.nanmean(nonzero_stack, axis=0).astype(np.float32)
    p95_intensity = np.nan_to_num(p95_intensity, nan=0.0)
    mean_nonzero = np.nan_to_num(mean_nonzero, nan=0.0)

    return FloodStatisticsRaster(
        event_count=event_count,
        max_intensity=max_intensity,
        annual_probability=annual_probability,
        p95_intensity=p95_intensity,
        mean_nonzero_intensity=mean_nonzero,
        n_snapshots=n,
        n_years=n_years,
        start_year=start_year,
        end_year=end_year,
        temporal_sampling=temporal_sampling,
        bbox=(PROJ_LON_MIN, PROJ_LAT_MIN, PROJ_LON_MAX, PROJ_LAT_MAX),
    )


# ---------------------------------------------------------------------------
# Classification and proxy logic (pure)
# ---------------------------------------------------------------------------

def classify_flood_susceptibility(
    event_count: int,
    annual_probability: float,
    max_intensity_mm: float,  # noqa: ARG001 — reserved for future intensity-based override
    *,
    high_prob: float = HIGH_ANNUAL_PROB,
    moderate_prob: float = MODERATE_ANNUAL_PROB,
    low_prob: float = LOW_ANNUAL_PROB,
) -> str:
    """Return flood susceptibility class based on annual probability."""
    if annual_probability >= high_prob:
        return "high"
    if annual_probability >= moderate_prob:
        return "moderate"
    if annual_probability >= low_prob:
        return "low"
    return "negligible"


def compute_coastal_proxy(
    lat: float,
    lon: float,
    event_count: int,
    *,
    coastal_threshold_km: float = COASTAL_DISTANCE_THRESHOLD_KM,
) -> CoastalFloodProxy | None:
    """Compute NH-08 coastal flood proxy for sites near the coast.

    Uses a lightweight bounding-box approach to identify coastal sites
    (within ~20 km of sea-facing boundaries). Quality is always "low"
    since GFMS models fluvial flooding only.

    Coastal regions covered by in-scope countries:
      - Adriatic: lon 13–21, lat 38–46
      - Black Sea west: lon 27–33, lat 41–47
      - Baltic south: lon 17–25, lat 53–57 (actually > 50°N, outside GFMS)
      - Aegean / Marmara (Turkey): lon 26–30, lat 38–42
      - Caspian (not in scope)
    """
    # Distance from nearest coastline is approximated via distance to
    # closest sea boundary. For a full implementation, use a coastline
    # dataset; for this initial implementation, use simple region checks.
    coastal_dist_km: float | None = None

    # Adriatic Sea coast (~eastern Adriatic: HR, ME, AL, BA coastline)
    adriatic_coast_points = [
        (45.3, 13.7),  # Rijeka
        (43.5, 16.4),  # Split
        (42.7, 18.1),  # Dubrovnik area
        (42.3, 19.2),  # Bar, ME
        (41.3, 19.5),  # Durrës, AL
    ]
    # Black Sea coast (RO, BG, TR, UA)
    black_sea_coast_points = [
        (44.2, 28.6),  # Constanța, RO
        (43.2, 27.9),  # Varna, BG
        (41.0, 28.9),  # Istanbul area, TR
        (46.5, 30.7),  # Odessa, UA
    ]
    # Baltic coast (EE, LV, LT — mostly > 50°N, outside GFMS)
    baltic_coast_points = [
        (54.7, 20.5),  # Kaliningrad area
        (55.7, 21.1),  # Klaipėda, LT
    ]

    all_coast_points = adriatic_coast_points + black_sea_coast_points + baltic_coast_points
    min_dist = min(haversine_km(lat, lon, clat, clon) for clat, clon in all_coast_points)
    coastal_dist_km = round(min_dist, 1)

    if min_dist > coastal_threshold_km:
        return None

    return CoastalFloodProxy(
        is_coastal=True,
        coastal_flood_events=event_count,
        coastal_distance_km=coastal_dist_km,
    )


def compute_dam_break_proxy(
    max_intensity: float,
    p95_intensity: float | None,
) -> DamBreakProxy:
    """Return dam-break proxy based on flood intensity anomaly."""
    if p95_intensity is None or p95_intensity == 0.0:
        return DamBreakProxy(
            max_anomaly_ratio=None,
            anomalous_event_flag=False,
            note="Insufficient data for anomaly detection",
        )
    ratio = max_intensity / p95_intensity
    return DamBreakProxy(
        max_anomaly_ratio=ratio,
        anomalous_event_flag=ratio > DAM_BREAK_ANOMALY_RATIO,
    )


def determine_quality(
    n_snapshots: int,
    lat: float,
    stale_cache: bool = False,
) -> str:
    """Return quality grade for NH-09 major river flood frequency."""
    if lat > LAT_MAX or lat < -50.0:
        return "insufficient"
    if stale_cache:
        return "medium"
    if n_snapshots >= 500:
        return "high"
    if n_snapshots >= 100:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------

def assemble_result(
    lat: float,
    lon: float,
    stats: FloodStatisticsRaster,
    *,
    coastal_threshold_km: float = COASTAL_DISTANCE_THRESHOLD_KM,
    high_prob: float = HIGH_ANNUAL_PROB,
    moderate_prob: float = MODERATE_ANNUAL_PROB,
    low_prob: float = LOW_ANNUAL_PROB,
    stale_cache: bool = False,
) -> GfmsResult:
    """Assemble a GfmsResult by sampling the pre-computed statistics raster.

    Returns a GfmsResult with quality "insufficient" if the site is outside
    GFMS coverage (|lat| > 50°N) or outside the project sub-grid.
    """
    if not is_within_coverage(lat):
        return GfmsResult(
            lat=lat, lon=lon,
            pixel_lat=lat, pixel_lon=lon, pixel_distance_km=0.0,
            flood_event_count=0,
            annual_flood_probability=0.0,
            flood_frequency_per_year=0.0,
            max_intensity_mm=0.0,
            p95_intensity_mm=None,
            mean_event_intensity_mm=None,
            flood_susceptibility="negligible",
            coastal_flood_proxy=None,
            dam_break_proxy=None,
            analysis_period=(stats.start_year, stats.end_year),
            n_snapshots_analysed=stats.n_snapshots,
            temporal_sampling=stats.temporal_sampling,
            source=SOURCE_NAME,
            quality="insufficient",
            error=(
                f"Site at lat {lat:.4f} is outside GFMS coverage "
                f"(|lat| > 50°N limit). No flood statistics available."
            ),
        )

    # Map lat/lon to global pixel
    global_row, global_col = grid_coords_to_pixel(lat, lon)
    sub_row, sub_col = pixel_to_subgrid(global_row, global_col)
    pixel_lat, pixel_lon = pixel_centre_coords(global_row, global_col)
    pixel_dist_km = haversine_km(lat, lon, pixel_lat, pixel_lon)

    # Handle coordinates near the sub-grid edge with grace
    sub_row_clamped = max(0, min(sub_row, SUBGRID_ROWS - 1))
    sub_col_clamped = max(0, min(sub_col, SUBGRID_COLS - 1))
    outside_subgrid = not is_within_subgrid(sub_row, sub_col)

    event_count = int(stats.event_count[sub_row_clamped, sub_col_clamped])
    max_intensity = float(stats.max_intensity[sub_row_clamped, sub_col_clamped])
    annual_prob = float(stats.annual_probability[sub_row_clamped, sub_col_clamped])
    p95_intensity = float(stats.p95_intensity[sub_row_clamped, sub_col_clamped])
    mean_intensity = float(stats.mean_nonzero_intensity[sub_row_clamped, sub_col_clamped])

    p95_val = p95_intensity if p95_intensity > 0 else None
    mean_val = mean_intensity if mean_intensity > 0 else None

    flood_freq_per_year = event_count / stats.n_years if stats.n_years > 0 else 0.0

    susceptibility = classify_flood_susceptibility(
        event_count, annual_prob, max_intensity,
        high_prob=high_prob, moderate_prob=moderate_prob, low_prob=low_prob,
    )

    coastal_proxy = compute_coastal_proxy(
        lat, lon, event_count, coastal_threshold_km=coastal_threshold_km,
    )
    dam_proxy = compute_dam_break_proxy(max_intensity, p95_val)

    quality = determine_quality(stats.n_snapshots, lat, stale_cache=stale_cache)
    if outside_subgrid:
        quality = "low"

    # Clamp implausible values
    if max_intensity > MAX_PLAUSIBLE_INTENSITY_MM:
        quality = min_quality(quality, "low")

    return GfmsResult(
        lat=lat,
        lon=lon,
        pixel_lat=pixel_lat,
        pixel_lon=pixel_lon,
        pixel_distance_km=pixel_dist_km,
        flood_event_count=event_count,
        annual_flood_probability=min(annual_prob, 1.0),
        flood_frequency_per_year=flood_freq_per_year,
        max_intensity_mm=max_intensity,
        p95_intensity_mm=p95_val,
        mean_event_intensity_mm=mean_val,
        flood_susceptibility=susceptibility,
        coastal_flood_proxy=coastal_proxy,
        dam_break_proxy=dam_proxy,
        analysis_period=(stats.start_year, stats.end_year),
        n_snapshots_analysed=stats.n_snapshots,
        temporal_sampling=stats.temporal_sampling,
        source=SOURCE_NAME,
        quality=quality,
    )


def min_quality(q1: str, q2: str) -> str:
    """Return the lower of two quality grades."""
    order = {"high": 3, "medium": 2, "low": 1, "insufficient": 0}
    return q1 if order.get(q1, 0) <= order.get(q2, 0) else q2
