# man_hours: 2.0
"""Result dataclasses and domain constants for S-20 GHSL GHS-POP.

Pure data definitions — no I/O, no HTTP, no database imports.
Serves criteria RI-04 (population density), RI-05 (nearest city),
RI-06 (population projection), and EP-01 (EPZ feasibility population).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CRITERION_IDS = ("RI-04", "RI-05", "RI-06", "EP-01")
SOURCE_NAME = "ghsl_pop_100m_r2023a"
SOURCE_URL = (
    "https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php"
)
SOURCE_DESCRIPTION = (
    "GHS-POP R2023A — Global Human Settlement Population Grid. "
    "100 m resolution, Mollweide projection (ESRI:54009). "
    "European Commission JRC. CC BY 4.0."
)

DOWNLOAD_BASE_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"
    "GHS_POP_GLOBE_R2023A/"
)

# Mollweide equal-area projection used by GHS-POP
MOLLWEIDE_CRS = "ESRI:54009"

# EPZ ring radii in metres (matching IAEA SSG-35 zones)
EPZ_RADII_M: tuple[int, ...] = (5_000, 16_000, 25_000, 80_000)
EPZ_RADII_KM: tuple[int, ...] = (5, 16, 25, 80)

# Avoidance / exclusionary thresholds (from spec §3)
CAUTION_POP_DENSITY_5KM = 1_000  # persons/km² → CAUTION
FAIL_POP_DENSITY_5KM = 5_000     # persons/km² → FAIL if road density < 2

# City detection threshold
CITY_POP_THRESHOLD = 50_000

# Study area bounding box (WGS84) — all 23 in-scope countries
INSCOPE_LAT_MIN, INSCOPE_LAT_MAX = 35.0, 60.0
INSCOPE_LON_MIN, INSCOPE_LON_MAX = 12.0, 46.0

# Epochs available in GHS-POP R2023A
AVAILABLE_EPOCHS = (
    1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030,
)
PRIMARY_EPOCH = 2020
PROJECTION_EPOCH = 2030


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RingPopulation:
    """Population statistics for a single EPZ ring buffer."""

    radius_km: int
    pop_total: int
    area_km2: float
    pop_density: float  # persons/km²

    def to_dict(self) -> dict[str, Any]:
        return {
            "radius_km": self.radius_km,
            "pop_total": self.pop_total,
            "area_km2": round(self.area_km2, 2),
            "pop_density": round(self.pop_density, 2),
        }


@dataclass
class NearestCity:
    """Nearest settlement exceeding the population threshold."""

    name: str | None
    population: int | None
    distance_km: float | None
    lat: float | None = None
    lon: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "population": self.population,
            "distance_km": round(self.distance_km, 2) if self.distance_km is not None else None,
            "lat": self.lat,
            "lon": self.lon,
        }


@dataclass
class GhslPopResult:
    """Population assessment for a single site from GHS-POP raster."""

    lat: float
    lon: float
    rings: list[RingPopulation] = field(default_factory=list)
    nearest_city: NearestCity | None = None
    pop_growth_rate_pct: float | None = None
    source: str = SOURCE_NAME
    quality: str = "medium"
    error: str | None = None

    @property
    def pop_density_5km(self) -> float | None:
        return self._ring_density(5)

    @property
    def pop_density_16km(self) -> float | None:
        return self._ring_density(16)

    @property
    def pop_density_25km(self) -> float | None:
        return self._ring_density(25)

    @property
    def pop_density_80km(self) -> float | None:
        return self._ring_density(80)

    @property
    def pop_total_5km(self) -> int | None:
        return self._ring_total(5)

    @property
    def pop_total_16km(self) -> int | None:
        return self._ring_total(16)

    @property
    def pop_total_25km(self) -> int | None:
        return self._ring_total(25)

    @property
    def pop_total_80km(self) -> int | None:
        return self._ring_total(80)

    def _ring_density(self, radius_km: int) -> float | None:
        for r in self.rings:
            if r.radius_km == radius_km:
                return r.pop_density
        return None

    def _ring_total(self, radius_km: int) -> int | None:
        for r in self.rings:
            if r.radius_km == radius_km:
                return r.pop_total
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "rings": [r.to_dict() for r in self.rings],
            "nearest_city": self.nearest_city.to_dict() if self.nearest_city else None,
            "pop_growth_rate_pct": self.pop_growth_rate_pct,
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
    pop_density_5km: float | None = None
    nearest_city_name: str | None = None
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
                    "pop_density_5km": s.pop_density_5km,
                    "nearest_city_name": s.nearest_city_name,
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
