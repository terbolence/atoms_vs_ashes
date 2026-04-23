# man_hours: 2.5
"""Pure dataclasses for S-06 Google Earth Engine — no ``ee`` imports."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

CRITERION_IDS = ("NH-04", "NH-13", "NS-04", "NS-06", "EP-03")

SOURCE_SLUG = "google_earth_engine"
SOURCE_NAME = "google_earth_engine"
SOURCE_URL = "https://earthengine.google.com/"
SOURCE_DESCRIPTION = (
    "Google Earth Engine — Copernicus DEM GLO-30, MODIS MCD64A1 burned area, "
    "Dynamic World built-up probability."
)


@dataclass
class GeeTerrainResult:
    """Terrain statistics from Copernicus DEM in GEE."""

    dem_dataset: str = "COPERNICUS/DEM/GLO30"
    dem_resolution_m: float = 30.0
    aoi_radius_m: float = 2000.0
    slope_max_deg: float | None = None
    slope_mean_deg: float | None = None
    slope_p95_deg: float | None = None
    slope_std_deg: float | None = None
    elevation_min_m: float | None = None
    elevation_max_m: float | None = None
    elevation_mean_m: float | None = None
    relief_range_m: float | None = None
    aspect_mean_deg: float | None = None
    relief_16km_m: float | None = None
    mountain_barrier_score: float | None = None
    terrain_class: str | None = None
    grading_class: str | None = None
    drainage_class: str | None = None
    roughness_class: str | None = None
    quality: str = "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dem_dataset": self.dem_dataset,
            "dem_resolution_m": self.dem_resolution_m,
            "aoi_radius_m": self.aoi_radius_m,
            "slope_max_deg": self.slope_max_deg,
            "slope_mean_deg": self.slope_mean_deg,
            "slope_p95_deg": self.slope_p95_deg,
            "slope_std_deg": self.slope_std_deg,
            "elevation_min_m": self.elevation_min_m,
            "elevation_max_m": self.elevation_max_m,
            "elevation_mean_m": self.elevation_mean_m,
            "relief_range_m": self.relief_range_m,
            "aspect_mean_deg": self.aspect_mean_deg,
            "relief_16km_m": self.relief_16km_m,
            "mountain_barrier_score": self.mountain_barrier_score,
            "terrain_class": self.terrain_class,
            "grading_class": self.grading_class,
            "drainage_class": self.drainage_class,
            "roughness_class": self.roughness_class,
            "quality": self.quality,
        }


@dataclass
class GeeFireResult:
    """Long-horizon fire metrics from MODIS MCD64A1 in GEE."""

    dataset: str = "MODIS/061/MCD64A1"
    resolution_m: float = 500.0
    aoi_radius_m: float = 5000.0
    analysis_period: str = ""
    modis_burn_count_25yr: int = 0
    modis_burn_fraction_mean: float | None = None
    burn_year_list: list[int] = field(default_factory=list)
    fire_recurrence_class: str = "none"
    firms_active_fire_count: int = 0
    quality: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "resolution_m": self.resolution_m,
            "aoi_radius_m": self.aoi_radius_m,
            "analysis_period": self.analysis_period,
            "modis_burn_count_25yr": self.modis_burn_count_25yr,
            "modis_burn_fraction_mean": self.modis_burn_fraction_mean,
            "burn_year_list": list(self.burn_year_list),
            "fire_recurrence_class": self.fire_recurrence_class,
            "firms_active_fire_count": self.firms_active_fire_count,
            "quality": self.quality,
        }


@dataclass
class GeeBuiltUpResult:
    """Dynamic World built probability mean."""

    dataset: str = "GOOGLE/DYNAMICWORLD/V1"
    resolution_m: float = 10.0
    aoi_radius_m: float = 500.0
    analysis_period: str = ""
    built_fraction_dw: float | None = None
    demolition_class: str | None = None
    quality: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "resolution_m": self.resolution_m,
            "aoi_radius_m": self.aoi_radius_m,
            "analysis_period": self.analysis_period,
            "built_fraction_dw": self.built_fraction_dw,
            "demolition_class": self.demolition_class,
            "quality": self.quality,
        }


@dataclass
class EarthEngineResult:
    """Assembled per-site GEE enrichment."""

    lat: float
    lon: float
    terrain: GeeTerrainResult | None = None
    fire: GeeFireResult | None = None
    built_up: GeeBuiltUpResult | None = None
    source: str = SOURCE_NAME
    mode: str = "fallback"
    quality: str = "high"
    modules_succeeded: list[str] = field(default_factory=list)
    modules_skipped: list[str] = field(default_factory=list)
    modules_failed: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "terrain": self.terrain.to_dict() if self.terrain else None,
            "fire": self.fire.to_dict() if self.fire else None,
            "built_up": self.built_up.to_dict() if self.built_up else None,
            "source": self.source,
            "mode": self.mode,
            "quality": self.quality,
            "modules_succeeded": list(self.modules_succeeded),
            "modules_skipped": list(self.modules_skipped),
            "modules_failed": list(self.modules_failed),
            "error": self.error,
        }


@dataclass
class SiteEnrichmentSummary:
    site_id: uuid.UUID
    site_name: str
    status: str
    slope_mean_deg: float | None = None
    terrain_class: str | None = None
    fire_recurrence_class: str | None = None
    modules_run: list[str] = field(default_factory=list)
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_cached: int = 0
    skipped_s05_sufficient: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped_cached": self.skipped_cached,
            "skipped_s05_sufficient": self.skipped_s05_sufficient,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "slope_mean_deg": s.slope_mean_deg,
                    "terrain_class": s.terrain_class,
                    "fire_recurrence_class": s.fire_recurrence_class,
                    "modules_run": s.modules_run,
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
            f"{self.total_sites} sites: {self.succeeded} ok, {self.failed} failed, "
            f"{self.skipped_cached} cached, {self.skipped_s05_sufficient} skipped_prior_dem ({elapsed})"
        )
