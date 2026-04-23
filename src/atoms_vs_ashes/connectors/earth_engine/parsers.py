# man_hours: 2.0
"""Pure parsing and classification for GEE reduceRegion outputs — no ``ee``."""

from __future__ import annotations

import math
from typing import Any

from atoms_vs_ashes.connectors.earth_engine.models import (
    GeeBuiltUpResult,
    GeeFireResult,
    GeeTerrainResult,
)


def _f(d: dict[str, Any], *keys: str) -> float | None:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                v = float(d[k])
                if math.isnan(v) or math.isinf(v):
                    return None
                return v
            except (TypeError, ValueError):
                continue
    return None


def classify_terrain_from_slope_and_relief(
    slope_mean_deg: float | None,
    relief_range_m: float | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """S-06 / S-05 aligned terrain buckets (spec §3 classification thresholds)."""
    tc: str | None = None
    if slope_mean_deg is not None:
        if slope_mean_deg < 3:
            tc = "flat"
        elif slope_mean_deg < 8:
            tc = "moderate"
        elif slope_mean_deg < 20:
            tc = "steep"
        else:
            tc = "mountainous"

    gc: str | None = None
    if relief_range_m is not None:
        if relief_range_m < 50:
            gc = "minimal"
        elif relief_range_m < 200:
            gc = "moderate"
        elif relief_range_m < 500:
            gc = "major"
        else:
            gc = "major"

    dc: str | None = None
    if slope_mean_deg is not None and relief_range_m is not None:
        if slope_mean_deg < 5 and relief_range_m < 100:
            dc = "good"
        elif slope_mean_deg < 12 and relief_range_m < 300:
            dc = "moderate"
        else:
            dc = "poor"

    rc: str | None = None
    if slope_mean_deg is not None:
        if slope_mean_deg < 3:
            rc = "smooth"
        elif slope_mean_deg < 8:
            rc = "moderate"
        elif slope_mean_deg < 15:
            rc = "rough"
        else:
            rc = "very_rough"

    return tc, gc, dc, rc


def terrain_slope_stability_class(terrain_class: str | None, slope_max_deg: float | None) -> str | None:
    """Map S-06 terrain bucket to ``SiteNaturalHazards.slope_stability_class`` vocabulary."""
    if slope_max_deg is None:
        return None
    if slope_max_deg >= 30:
        return "extreme"
    if terrain_class == "flat":
        return "flat"
    if terrain_class == "moderate":
        return "moderate"
    if terrain_class == "steep":
        return "steep"
    if terrain_class == "mountainous":
        return "very_steep"
    return "moderate"


def mountain_barrier_score(relief_16km_m: float | None) -> float | None:
    if relief_16km_m is None:
        return None
    return max(0.0, min(1.0, relief_16km_m / 1500.0))


def classify_fire_recurrence(burn_count: int) -> str:
    if burn_count <= 0:
        return "none"
    if burn_count <= 2:
        return "rare"
    if burn_count <= 5:
        return "moderate"
    return "frequent"


def classify_demolition(built_fraction: float | None) -> str | None:
    if built_fraction is None:
        return None
    if built_fraction < 0.1:
        return "minimal"
    if built_fraction < 0.5:
        return "moderate"
    return "extensive"


def parse_slope_elevation_dicts(
    slope_raw: dict[str, Any],
    elev_raw: dict[str, Any],
    *,
    dem_dataset: str,
    aoi_radius_m: float,
    relief_16km_m: float | None,
) -> GeeTerrainResult:
    slope_mean = _f(slope_raw, "slope_mean", "mean")
    slope_max = _f(slope_raw, "slope_max", "max")
    slope_p95 = _f(slope_raw, "slope_p95", "p95")
    slope_std = _f(slope_raw, "slope_stdDev", "stdDev", "std")
    emin = _f(elev_raw, "DEM_min", "min", "elevation_min")
    emax = _f(elev_raw, "DEM_max", "max", "elevation_max")
    emean = _f(elev_raw, "DEM_mean", "mean", "elevation_mean")
    aspect = _f(slope_raw, "aspect_mean", "aspect")
    relief = None
    if emax is not None and emin is not None:
        relief = emax - emin

    tc, gc, dc, rc = classify_terrain_from_slope_and_relief(slope_mean, relief)
    mbs = mountain_barrier_score(relief_16km_m)

    qual = "high"
    for v in (slope_mean, slope_max, emin, emax):
        if v is None:
            qual = "insufficient"
            break
    if slope_max is not None and slope_max > 60:
        qual = "low"

    return GeeTerrainResult(
        dem_dataset=dem_dataset,
        aoi_radius_m=aoi_radius_m,
        slope_max_deg=slope_max,
        slope_mean_deg=slope_mean,
        slope_p95_deg=slope_p95,
        slope_std_deg=slope_std,
        elevation_min_m=emin,
        elevation_max_m=emax,
        elevation_mean_m=emean,
        relief_range_m=relief,
        aspect_mean_deg=aspect,
        relief_16km_m=relief_16km_m,
        mountain_barrier_score=mbs,
        terrain_class=tc,
        grading_class=gc,
        drainage_class=dc,
        roughness_class=rc,
        quality=qual,
    )


def parse_fire_dict(
    raw: dict[str, Any],
    *,
    aoi_radius_m: float,
    analysis_period: str,
    burn_year_list: list[int],
) -> GeeFireResult:
    frac = _f(raw, "BurnDate_mean", "burned_mean", "mean")
    mx = _f(raw, "BurnDate_max", "max")
    count_proxy = 0
    if mx is not None:
        count_proxy = int(round(mx))
    elif frac is not None:
        count_proxy = min(300, int(round(frac * 300)))

    qual = "medium"
    if count_proxy > 100:
        qual = "low"

    return GeeFireResult(
        aoi_radius_m=aoi_radius_m,
        analysis_period=analysis_period,
        modis_burn_count_25yr=count_proxy,
        modis_burn_fraction_mean=frac,
        burn_year_list=list(burn_year_list),
        fire_recurrence_class=classify_fire_recurrence(count_proxy),
        quality=qual,
    )


def parse_built_dict(
    raw: dict[str, Any],
    *,
    aoi_radius_m: float,
    analysis_period: str,
) -> GeeBuiltUpResult:
    mean_built = _f(raw, "built_mean", "built", "mean")
    dclass = classify_demolition(mean_built)
    qual = "high" if mean_built is not None else "insufficient"
    if mean_built is not None and (mean_built < 0 or mean_built > 1):
        qual = "insufficient"
    return GeeBuiltUpResult(
        aoi_radius_m=aoi_radius_m,
        analysis_period=analysis_period,
        built_fraction_dw=mean_built,
        demolition_class=dclass,
        quality=qual,
    )
