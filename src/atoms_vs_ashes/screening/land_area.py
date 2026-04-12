# man_hours: 6.0
"""BF-02 Land Area Basic Filter.

For each site × SMR design, determine whether the site's available land
area (hectares) can accommodate the SMR and record a pass/fail/inconclusive
verdict in ``screening_verdicts``.

Site area is expected to have been populated by the OSM area ingestion
pipeline (``ingest.osm_area``) before this check runs.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import ScreeningVerdict, Site, SiteObservation
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


def evaluate_site_for_smr(
    site_area_ha: float | None,
    smr_key: str,
    smr_name: str,
    smr_land_ha: float,
) -> tuple[str, str, str]:
    """Pure-logic evaluation returning ``(verdict, measured_value, justification)``."""
    if site_area_ha is None:
        return (
            "inconclusive",
            json.dumps({"site_area_ha": None}),
            "No site area data available; OSM boundary not found or not yet queried",
        )

    if site_area_ha >= smr_land_ha:
        return (
            "pass",
            json.dumps({"site_area_ha": site_area_ha}),
            f"Site area {site_area_ha:.1f} ha >= "
            f"{smr_name} requirement ({smr_land_ha:.1f} ha)",
        )

    return (
        "fail",
        json.dumps({"site_area_ha": site_area_ha}),
        f"Site area {site_area_ha:.1f} ha < "
        f"{smr_name} requirement ({smr_land_ha:.1f} ha)",
    )


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
    ) -> list[ScreeningVerdict]:
        smrs = _smr_land_thresholds(settings)
        if not smrs:
            log.warning("no_smr_types_configured")
            return []

        sites = session.execute(select(Site)).scalars().all()
        verdicts: list[ScreeningVerdict] = []
        inconclusive_logged: set = set()

        for site in sites:
            area = float(site.site_area_ha) if site.site_area_ha is not None else None

            for smr_key, smr_name, smr_land_ha in smrs:
                verdict, measured_value, justification = evaluate_site_for_smr(
                    area, smr_key, smr_name, smr_land_ha,
                )

                confidence = "high" if area is not None else "low"

                verdicts.append(
                    ScreeningVerdict(
                        site_id=site.site_id,
                        smr_key=smr_key,
                        criterion_id=self.criterion_id,
                        phase=self.phase,
                        verdict=verdict,
                        measured_value=measured_value,
                        threshold=f"{smr_land_ha:.1f} ha",
                        justification=justification,
                        confidence=confidence,
                        data_sources=["sites.site_area_ha (from OSM Overpass)"],
                        run_id=run_id,
                    )
                )

                if verdict == "inconclusive" and site.site_id not in inconclusive_logged:
                    inconclusive_logged.add(site.site_id)
                    session.add(
                        SiteObservation(
                            site_id=site.site_id,
                            criterion_id=self.criterion_id,
                            smr_key=smr_key,
                            source_type="api",
                            observation=(
                                "site_area_ha is not set; "
                                "BF-02 land area screening inconclusive"
                            ),
                            impact="blocking",
                            confidence="low",
                            run_id=run_id,
                        )
                    )

        return verdicts
