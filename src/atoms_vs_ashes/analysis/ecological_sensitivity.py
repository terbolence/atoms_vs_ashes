# man_hours: 4.0
"""NS-08 Ecological sensitivity assessment using CORINE land cover.

Priority 2 — S-14 Natura 2000 (P1) and S-15 WDPA (P1) not yet implemented.
CORINE provides a land-cover-based fragmentation proxy (NS-08d).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.connectors.corine import (
    CorineConnector,
    NATURAL_SEMINATURAL_CLC,
    NON_EU_COUNTRIES,
    parse_clc_features,
)
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.geo import buffer_circle_wgs84, geodesic_area_ha
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-08"


@dataclass
class FragmentationResult:
    """Landscape fragmentation metrics for ecological sensitivity."""
    lat: float
    lon: float
    patch_count: int = 0
    patch_density_per_km2: float = 0.0
    largest_patch_ha: float = 0.0
    largest_patch_index: float = 0.0
    total_natural_ha: float = 0.0
    buffer_area_ha: float = 0.0
    natural_pct: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "patch_count": self.patch_count,
            "patch_density_per_km2": round(self.patch_density_per_km2, 3),
            "largest_patch_ha": round(self.largest_patch_ha, 2),
            "largest_patch_index": round(self.largest_patch_index, 4),
            "total_natural_ha": round(self.total_natural_ha, 2),
            "buffer_area_ha": round(self.buffer_area_ha, 2),
            "natural_pct": round(self.natural_pct, 1),
            "error": self.error,
        }


def assess_ecological_sensitivity(
    lat: float,
    lon: float,
    corine: CorineConnector | None = None,
    buffer_radius_m: float = 25_000,
    *,
    features: list[dict[str, Any]] | None = None,
) -> FragmentationResult:
    """Compute landscape fragmentation metrics from CORINE.

    Pass *corine* to fetch data on demand, or *features* to use
    pre-fetched GeoJSON features.
    """
    if features is None:
        if corine is None:
            return FragmentationResult(lat=lat, lon=lon, error="No CORINE connector or pre-fetched features provided")
        features = corine.fetch(lat, lon, radius_m=buffer_radius_m + 500)

    if not features:
        return FragmentationResult(lat=lat, lon=lon, error="No CLC features returned")

    parsed = parse_clc_features(features)
    if not parsed:
        return FragmentationResult(lat=lat, lon=lon, error="No valid CLC polygons parsed")

    buffer_geom = buffer_circle_wgs84(lat, lon, buffer_radius_m)
    buffer_area_ha = geodesic_area_ha(buffer_geom)
    buffer_area_km2 = buffer_area_ha / 100.0

    natural_patches: list[Any] = []
    for geom, clc_code in parsed:
        if clc_code not in NATURAL_SEMINATURAL_CLC:
            continue
        try:
            intersection = buffer_geom.intersection(geom)
            if not intersection.is_empty:
                natural_patches.append(intersection)
        except Exception:
            continue

    result = FragmentationResult(lat=lat, lon=lon, buffer_area_ha=buffer_area_ha)

    if not natural_patches:
        return result

    patch_areas = [geodesic_area_ha(p) for p in natural_patches]
    result.patch_count = len(natural_patches)
    result.total_natural_ha = sum(patch_areas)
    result.largest_patch_ha = max(patch_areas)
    result.natural_pct = (result.total_natural_ha / buffer_area_ha * 100) if buffer_area_ha > 0 else 0
    result.largest_patch_index = (result.largest_patch_ha / buffer_area_ha) if buffer_area_ha > 0 else 0
    result.patch_density_per_km2 = (result.patch_count / buffer_area_km2) if buffer_area_km2 > 0 else 0

    return result


def assess_and_persist(
    lat: float,
    lon: float,
    site_id: Any,
    country_code: str,
    session: Session,
    run_id: str,
    corine: CorineConnector,
) -> FragmentationResult:
    """Assess ecological sensitivity and persist as SiteAttribute NS-08."""
    t0 = time.monotonic()

    if country_code in NON_EU_COUNTRIES:
        write_quality_flag(
            session,
            site_id=site_id,
            dataset="corine",
            dimension="ecological_sensitivity",
            level="insufficient",
            detail=f"CORINE does not cover {country_code}; NS-08 requires S-14/S-15",
            run_id=run_id,
        )
        result = FragmentationResult(lat=lat, lon=lon, error=f"No CORINE coverage for {country_code}")
    else:
        result = assess_ecological_sensitivity(lat, lon, corine)

    source_id = ensure_data_source(
        session,
        name="corine_clc2018_wfs",
        url=corine._wfs_url,
        description="CORINE Land Cover 2018 WFS for ecological sensitivity",
    )

    session.merge(
        SiteAttribute(
            site_id=site_id,
            criterion_id=CRITERION_ID,
            value_numeric=result.natural_pct,
            value_json=result.to_dict(),
            source_id=source_id,
            run_id=run_id,
            cache_status="fresh",
        )
    )

    if result.error:
        write_quality_flag(
            session,
            site_id=site_id,
            dataset="corine",
            dimension="ecological_sensitivity",
            level="low",
            detail=result.error,
            run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info(
        "ecological_sensitivity_assess_ok",
        site_id=str(site_id),
        criterion_id=CRITERION_ID,
        run_id=run_id,
        natural_pct=round(result.natural_pct, 1),
        elapsed_ms=elapsed_ms,
    )
    return result
