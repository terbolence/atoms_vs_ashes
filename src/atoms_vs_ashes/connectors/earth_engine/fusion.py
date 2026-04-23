# man_hours: 1.5
"""Pure fusion logic for comparing independent connector values (S-06 vs others)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

DiscrepancySize = Literal["none", "small", "large"]


@dataclass(frozen=True)
class FusionConfig:
    """Thresholds and tie-break policy for cross-source numeric fusion."""

    small_rel_tolerance: float = 0.12
    small_abs_slope_deg: float = 2.0
    small_abs_built: float = 0.08
    trusted_priority: tuple[str, ...] = (
        "google_earth_engine",
        "sentinel_hub_cdse",
        "copernicus_dem_glo30",
    )


def _discrepancy_slope(a: float | None, b: float | None, cfg: FusionConfig) -> DiscrepancySize:
    if a is None or b is None:
        return "none"
    diff = abs(a - b)
    if diff <= cfg.small_abs_slope_deg:
        return "small"
    denom = max(abs(a), abs(b), 1e-6)
    if diff / denom <= cfg.small_rel_tolerance:
        return "small"
    return "large"


def _discrepancy_scalar(a: float | None, b: float | None, abs_tol: float, rel_tol: float) -> DiscrepancySize:
    if a is None or b is None:
        return "none"
    diff = abs(a - b)
    if diff <= abs_tol:
        return "small"
    denom = max(abs(a), abs(b), 1e-9)
    if diff / denom <= rel_tol:
        return "small"
    return "large"


def pick_trusted_value(
    values: dict[str, float | None],
    *,
    cfg: FusionConfig,
) -> tuple[str | None, float | None]:
    """Return (source_name, value) from the highest-priority source that has a value."""
    for name in cfg.trusted_priority:
        v = values.get(name)
        if v is not None:
            return name, float(v)
    return None, None


def fuse_slope_degrees(
    *,
    copernicus_max_slope: float | None,
    gee_max_slope: float | None,
    cfg: FusionConfig | None = None,
) -> dict[str, Any]:
    """Fuse NH-04 maximum slope from Copernicus local raster vs GEE server-side DEM.

    For the **same** Copernicus GLO-30 DEM, differences should usually be *small*
    (buffer and reducer choice). **Large** differences warrant engineering review;
    the default policy prefers ``google_earth_engine`` after ``sentinel_hub_cdse``,
    then ``copernicus_dem_glo30`` — this is a project default, not a universal
    truth (local COGs are auditable; GEE is reproducible server-side).
    """
    cfg = cfg or FusionConfig()
    values = {
        "copernicus_dem_glo30": copernicus_max_slope,
        "google_earth_engine": gee_max_slope,
    }
    disc = _discrepancy_slope(copernicus_max_slope, gee_max_slope, cfg)
    if disc == "none" or copernicus_max_slope is None or gee_max_slope is None:
        src, val = pick_trusted_value(
            {"google_earth_engine": gee_max_slope, "copernicus_dem_glo30": copernicus_max_slope},
            cfg=cfg,
        )
        return {
            "discrepancy": disc,
            "fused_slope_max_deg": val,
            "fused_source": src,
            "method": "single_source_or_priority",
            "inputs": dict(values),
        }
    if disc == "small":
        fused = (copernicus_max_slope + gee_max_slope) / 2.0
        return {
            "discrepancy": disc,
            "fused_slope_max_deg": round(fused, 3),
            "fused_source": "mean_small_discrepancy",
            "method": "arithmetic_mean",
            "inputs": dict(values),
        }
    src, val = pick_trusted_value(values, cfg=cfg)
    return {
        "discrepancy": disc,
        "fused_slope_max_deg": val,
        "fused_source": src,
        "method": "trusted_priority_large_discrepancy",
        "inputs": dict(values),
        "review": "Engineering judgement recommended — slope max differs materially between sources.",
    }


def fuse_built_fraction(
    *,
    sentinel_ndbi_proxy: float | None,
    gee_dw_built: float | None,
    cfg: FusionConfig | None = None,
) -> dict[str, Any]:
    """Fuse NS-06 proxies: Sentinel-2 NBR/NDBI style vs Dynamic World ``built`` mean."""
    cfg = cfg or FusionConfig()
    values = {"sentinel_hub_cdse": sentinel_ndbi_proxy, "google_earth_engine": gee_dw_built}
    disc = _discrepancy_scalar(
        sentinel_ndbi_proxy, gee_dw_built, cfg.small_abs_built, cfg.small_rel_tolerance,
    )
    if disc in ("none", "small") and sentinel_ndbi_proxy is not None and gee_dw_built is not None:
        fused = (sentinel_ndbi_proxy + gee_dw_built) / 2.0
        return {
            "discrepancy": disc,
            "fused_built_fraction": round(min(1.0, max(0.0, fused)), 4),
            "fused_source": "mean_small_discrepancy",
            "method": "arithmetic_mean",
            "inputs": dict(values),
        }
    src, val = pick_trusted_value(values, cfg=cfg)
    return {
        "discrepancy": disc if sentinel_ndbi_proxy is not None and gee_dw_built is not None else "none",
        "fused_built_fraction": val,
        "fused_source": src,
        "method": "trusted_priority",
        "inputs": dict(values),
    }
