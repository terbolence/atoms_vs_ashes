# man_hours: 6.0
"""BF-02 Land Area Basic Filter.

For each site, determine which of the deployable SMR designs can be
accommodated based on the site's available land area (hectares), and record
a pass / fail / inconclusive verdict in ``screening_results``.

Site area is expected to have been populated by the OSM area ingestion
pipeline (``ingest.osm_area``) before this check runs.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import DataQualityFlag, ScreeningResult, Site
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.screening.base import ScreeningCheck, register_check

log = get_logger(__name__)

CRITERION_ID = "BF-02"
PHASE = "basic_filter"


def _smr_land_thresholds(settings: Settings) -> list[tuple[str, str, float]]:
    """Return ``(key, display_name, land_ha)`` sorted ascending by hectares."""
    entries: list[tuple[str, str, float]] = []
    for key, spec in settings.smr_types.items():
        entries.append((key, spec["name"], float(spec["land_ha"])))
    entries.sort(key=lambda t: t[2])
    return entries


def _build_threshold_text(smrs: list[tuple[str, str, float]]) -> str:
    """Compact human-readable threshold summary."""
    if not smrs:
        return ""
    parts = [f"{smrs[0][2]:.1f} ha (min: {smrs[0][1]})"]
    ref = [s for s in smrs if s[0] == "nuscale_voygr6"]
    if ref:
        parts.append(f"{ref[0][2]:.1f} ha (ref: {ref[0][1]})")
    parts.append(f"{smrs[-1][2]:.1f} ha (max: {smrs[-1][1]})")
    return " / ".join(parts)


def evaluate_site(
    site_area_ha: float | None,
    smrs: list[tuple[str, str, float]],
) -> tuple[str, dict[str, Any], str]:
    """Pure-logic evaluation returning ``(verdict, value_dict, justification)``.

    Separated from DB concerns for easy unit testing.
    """
    if site_area_ha is None:
        return (
            "inconclusive",
            {"site_area_ha": None, "compatible": [], "incompatible": []},
            "No site area data available; OSM boundary not found or not yet queried",
        )

    compatible: list[str] = []
    incompatible: list[str] = []
    compatible_names: list[str] = []
    incompatible_names: list[str] = []

    for key, name, land_ha in smrs:
        if site_area_ha >= land_ha:
            compatible.append(key)
            compatible_names.append(f"{name} ({land_ha:.1f} ha)")
        else:
            incompatible.append(key)
            incompatible_names.append(f"{name} ({land_ha:.1f} ha)")

    verdict = "pass" if compatible else "fail"

    value_dict: dict[str, Any] = {
        "site_area_ha": site_area_ha,
        "compatible": compatible,
        "incompatible": incompatible,
    }

    n_compat = len(compatible)
    n_total = len(smrs)

    if verdict == "fail":
        justification = (
            f"Site area {site_area_ha:.1f} ha is below the minimum "
            f"SMR land requirement ({smrs[0][2]:.1f} ha for {smrs[0][1]})"
        )
    elif n_compat == n_total:
        justification = (
            f"Site area {site_area_ha:.1f} ha accommodates all "
            f"{n_total} SMR configurations"
        )
    else:
        justification = (
            f"Site area {site_area_ha:.1f} ha accommodates "
            f"{n_compat} of {n_total} SMR configurations "
            f"({', '.join(compatible_names)})"
        )
        if incompatible_names:
            justification += f" but not {', '.join(incompatible_names)}"

    return verdict, value_dict, justification


@register_check
class LandAreaCheck(ScreeningCheck):
    """BF-02: Land Area Basic Filter."""

    criterion_id = CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningResult]:
        smrs = _smr_land_thresholds(settings)
        if not smrs:
            log.warning("no_smr_types_configured")
            return []

        threshold_text = _build_threshold_text(smrs)
        sites = session.execute(select(Site)).scalars().all()
        results: list[ScreeningResult] = []

        for site in sites:
            area = float(site.site_area_ha) if site.site_area_ha is not None else None
            verdict, value_dict, justification = evaluate_site(area, smrs)

            if verdict == "inconclusive":
                session.add(
                    DataQualityFlag(
                        site_id=site.site_id,
                        dataset="sites",
                        dimension="site_area",
                        level="low",
                        detail=(
                            "site_area_ha is not set; "
                            "BF-02 land area screening inconclusive"
                        ),
                        run_id=run_id,
                    )
                )

            results.append(
                ScreeningResult(
                    site_id=site.site_id,
                    criterion_id=self.criterion_id,
                    phase=self.phase,
                    verdict=verdict,
                    value=json.dumps(value_dict),
                    threshold=threshold_text,
                    justification=justification,
                    source_refs="sites.site_area_ha (from OSM Overpass)",
                    run_id=run_id,
                )
            )

        return results
