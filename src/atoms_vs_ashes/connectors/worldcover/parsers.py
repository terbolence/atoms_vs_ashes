# man_hours: 3.0
"""Pure transformation logic for ESA WorldCover land cover analysis.

Computes buildable area metrics, dominant land class, and land suitability
breakdowns from raster-sampled ring data.  All functions are pure —
no I/O, no DB, no HTTP — and fully unit-testable.
"""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.connectors.corine.models import CLC_LABELS
from atoms_vs_ashes.connectors.worldcover.models import (
    DEVELOPABLE_ESA,
    ESA_CLASS_LABELS,
    ESA_TO_CLC_APPROX,
    FAVOURABLE_ESA,
    MODERATE_ESA,
    NATURAL_SEMINATURAL_ESA,
    NON_EU_COUNTRIES,
    UNFAVOURABLE_ESA,
    WorldCoverResult,
)

BUILDABLE_RADIUS_M = 1_000
NUCLEAR_ISLAND_HA = 14.0
VOYGR6_FOOTPRINT_HA = 72.8


def compute_buildable_metrics(
    result: WorldCoverResult,
    *,
    buildable_radius_m: float = BUILDABLE_RADIUS_M,
) -> dict[str, Any]:
    """Derive buildable area metrics from WorldCover ring analysis.

    Returns the same dict shape as the CORINE parsers module so both
    can write to the same SiteInfrastructureV2 columns.
    """
    total_area_ha = 0.0
    favourable_ha = 0.0
    moderate_ha = 0.0
    unfavourable_ha = 0.0
    class_areas: dict[int, float] = {}

    for ring in result.rings:
        for esa_class, area_ha in ring.by_class.items():
            class_areas[esa_class] = class_areas.get(esa_class, 0.0) + area_ha
            total_area_ha += area_ha
            if esa_class in FAVOURABLE_ESA:
                favourable_ha += area_ha
            elif esa_class in MODERATE_ESA:
                moderate_ha += area_ha
            elif esa_class in UNFAVOURABLE_ESA:
                unfavourable_ha += area_ha

    dominant_esa = max(class_areas, key=class_areas.get) if class_areas else None
    dominant_clc = ESA_TO_CLC_APPROX.get(dominant_esa) if dominant_esa else None
    dominant_label = ESA_CLASS_LABELS.get(dominant_esa, "Unknown") if dominant_esa else None

    buildable_ha = 0.0
    for ring in result.rings:
        if ring.outer_m <= buildable_radius_m:
            buildable_ha += ring.developable_ha

    dominant_class_pct = 0.0
    if dominant_esa and total_area_ha > 0:
        dominant_class_pct = (class_areas[dominant_esa] / total_area_ha) * 100

    if total_area_ha > 0:
        favourable_pct = (favourable_ha / total_area_ha) * 100
        moderate_pct = (moderate_ha / total_area_ha) * 100
        unfavourable_pct = (unfavourable_ha / total_area_ha) * 100
    else:
        favourable_pct = moderate_pct = unfavourable_pct = 0.0

    natural_seminatural_ha = sum(
        v for k, v in class_areas.items() if k in NATURAL_SEMINATURAL_ESA
    )

    return {
        "buildable_area_ha": float(round(buildable_ha, 2)),
        "dominant_land_class": dominant_clc,
        "dominant_land_label": dominant_label,
        "dominant_class_pct": float(round(dominant_class_pct, 1)),
        "favourable_land_pct": float(round(favourable_pct, 1)),
        "moderate_land_pct": float(round(moderate_pct, 1)),
        "unfavourable_land_pct": float(round(unfavourable_pct, 1)),
        "natural_seminatural_ha": float(round(natural_seminatural_ha, 2)),
        "patch_count": result.patch_count,
        "largest_contiguous_ha": result.largest_contiguous_ha,
    }


def build_ns04_comment(metrics: dict[str, Any]) -> str:
    """Build a human-readable NS-04 comment from computed metrics."""
    label = metrics.get("dominant_land_label") or "Unknown"
    pct = metrics.get("dominant_class_pct", 0.0)
    buildable = metrics.get("buildable_area_ha", 0.0)

    parts = [f"Dominant: {label} ({pct:.0f}%)"]
    parts.append(f"Buildable (WorldCover, 0\u20131 km): {buildable:.1f} ha")

    fav = metrics.get("favourable_land_pct", 0.0)
    mod = metrics.get("moderate_land_pct", 0.0)
    unfav = metrics.get("unfavourable_land_pct", 0.0)
    parts.append(f"Suitability: {fav:.0f}% fav / {mod:.0f}% mod / {unfav:.0f}% unfav")

    return "; ".join(parts)


def is_non_eu(country_code: str) -> bool:
    """Return True if the country is in the non-EU set (WorldCover target)."""
    return country_code.upper() in NON_EU_COUNTRIES


def assess_buildable_adequacy(buildable_ha: float) -> str:
    """Classify buildable area adequacy for A15 screening."""
    if buildable_ha >= VOYGR6_FOOTPRINT_HA:
        return "adequate"
    if buildable_ha >= NUCLEAR_ISLAND_HA:
        return "marginal"
    return "insufficient"
