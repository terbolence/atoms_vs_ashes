# man_hours: 2.0
"""Pure transformation logic for CORINE Land Cover batch enrichment.

Computes buildable area metrics, dominant land class, and land suitability
breakdowns from a SiteClassification result.  All functions are pure —
no I/O, no DB, no HTTP — and fully unit-testable.
"""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.connectors.corine.models import (
    CLC_LABELS,
    CORINE_COVERED_COUNTRIES,
    FAVOURABLE_FOOTPRINT_CLC,
    MODERATE_FOOTPRINT_CLC,
    NATURAL_SEMINATURAL_CLC,
    UNFAVOURABLE_FOOTPRINT_CLC,
    SiteClassification,
)

BUILDABLE_RADIUS_M = 1_000
NUCLEAR_ISLAND_HA = 14.0
VOYGR6_FOOTPRINT_HA = 72.8


def compute_buildable_metrics(
    classification: SiteClassification,
    *,
    buildable_radius_m: float = BUILDABLE_RADIUS_M,
) -> dict[str, Any]:
    """Derive buildable area metrics from a CORINE ring classification.

    Parameters
    ----------
    classification
        Result from ``CorineConnector.classify()``.
    buildable_radius_m
        Rings with ``outer_m <= buildable_radius_m`` contribute to
        ``buildable_area_ha``.

    Returns
    -------
    dict
        Keys: ``buildable_area_ha``, ``dominant_land_class``,
        ``dominant_land_label``, ``dominant_class_pct``,
        ``favourable_land_pct``, ``moderate_land_pct``,
        ``unfavourable_land_pct``, ``natural_seminatural_ha``.
    """
    total_area_ha = 0.0
    favourable_ha = 0.0
    moderate_ha = 0.0
    unfavourable_ha = 0.0
    class_areas: dict[str, float] = {}

    for ring in classification.rings:
        for clc_code, area_ha in ring.by_class.items():
            class_areas[clc_code] = class_areas.get(clc_code, 0.0) + area_ha
            total_area_ha += area_ha
            if clc_code in FAVOURABLE_FOOTPRINT_CLC:
                favourable_ha += area_ha
            elif clc_code in MODERATE_FOOTPRINT_CLC:
                moderate_ha += area_ha
            elif clc_code in UNFAVOURABLE_FOOTPRINT_CLC:
                unfavourable_ha += area_ha

    dominant_class = max(class_areas, key=class_areas.get) if class_areas else None
    dominant_label = CLC_LABELS.get(dominant_class, "Unknown") if dominant_class else None

    buildable_ha = 0.0
    for ring in classification.rings:
        if ring.outer_m <= buildable_radius_m:
            buildable_ha += ring.developable_ha

    dominant_class_pct = 0.0
    if dominant_class and total_area_ha > 0:
        dominant_class_pct = (class_areas[dominant_class] / total_area_ha) * 100

    if total_area_ha > 0:
        favourable_pct = (favourable_ha / total_area_ha) * 100
        moderate_pct = (moderate_ha / total_area_ha) * 100
        unfavourable_pct = (unfavourable_ha / total_area_ha) * 100
    else:
        favourable_pct = moderate_pct = unfavourable_pct = 0.0

    natural_seminatural_ha = sum(
        v for k, v in class_areas.items() if k in NATURAL_SEMINATURAL_CLC
    )

    return {
        "buildable_area_ha": round(buildable_ha, 2),
        "dominant_land_class": dominant_class,
        "dominant_land_label": dominant_label,
        "dominant_class_pct": round(dominant_class_pct, 1),
        "favourable_land_pct": round(favourable_pct, 1),
        "moderate_land_pct": round(moderate_pct, 1),
        "unfavourable_land_pct": round(unfavourable_pct, 1),
        "natural_seminatural_ha": round(natural_seminatural_ha, 2),
        "patch_count": classification.patch_count,
        "largest_contiguous_ha": classification.largest_contiguous_ha,
    }


def build_ns04_comment(metrics: dict[str, Any]) -> str:
    """Build a human-readable NS-04 comment from computed metrics."""
    label = metrics.get("dominant_land_label") or "Unknown"
    pct = metrics.get("dominant_class_pct", 0.0)
    buildable = metrics.get("buildable_area_ha", 0.0)

    parts = [f"Dominant: {label} ({pct:.0f}%)"]
    parts.append(f"Buildable (CORINE, 0\u20131 km): {buildable:.1f} ha")

    fav = metrics.get("favourable_land_pct", 0.0)
    mod = metrics.get("moderate_land_pct", 0.0)
    unfav = metrics.get("unfavourable_land_pct", 0.0)
    parts.append(f"Suitability: {fav:.0f}% fav / {mod:.0f}% mod / {unfav:.0f}% unfav")

    return "; ".join(parts)


def is_corine_covered(country_code: str) -> bool:
    """Return True if the country is within CORINE coverage."""
    return country_code.upper() in CORINE_COVERED_COUNTRIES


def assess_buildable_adequacy(buildable_ha: float) -> str:
    """Classify buildable area adequacy for A15 screening.

    Returns
    -------
    str
        ``"adequate"`` if >= VOYGR-6 footprint,
        ``"marginal"`` if >= nuclear island minimum,
        ``"insufficient"`` otherwise.
    """
    if buildable_ha >= VOYGR6_FOOTPRINT_HA:
        return "adequate"
    if buildable_ha >= NUCLEAR_ISLAND_HA:
        return "marginal"
    return "insufficient"
