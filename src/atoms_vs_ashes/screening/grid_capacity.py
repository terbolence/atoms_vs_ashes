# man_hours: 8.0
"""BF-01 Grid Capacity Basic Filter.

For each site × SMR design, determine whether the site's grid / installed
capacity can accommodate the SMR and record a pass/fail/inconclusive
verdict in ``screening_verdicts``.
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

CRITERION_ID = "BF-01"
PHASE = "basic_filter"


def _resolve_capacity(site: Site) -> float | None:
    """Return the best available capacity figure for *site*.

    Preference order:
    1. ``grid_capacity_mw`` (explicit grid connection data)
    2. ``installed_capacity_mw`` (coal plant nameplate as proxy)
    """
    for attr in ("grid_capacity_mw", "installed_capacity_mw"):
        val = getattr(site, attr, None)
        if val is not None:
            return float(val)
    return None


def _smr_thresholds(settings: Settings) -> list[tuple[str, str, float]]:
    """Return ``(key, display_name, capacity_mwe)`` sorted ascending by MWe."""
    entries: list[tuple[str, str, float]] = []
    for key, spec in settings.smr_types.items():
        entries.append((key, spec["name"], float(spec["capacity_mwe"])))
    entries.sort(key=lambda t: t[2])
    return entries


def evaluate_site_for_smr(
    site_capacity_mw: float | None,
    smr_key: str,
    smr_name: str,
    smr_capacity_mwe: float,
) -> tuple[str, str, str]:
    """Pure-logic evaluation returning ``(verdict, measured_value, justification)``."""
    if site_capacity_mw is None:
        return (
            "inconclusive",
            json.dumps({"site_capacity_mw": None}),
            "No grid or installed capacity data available for this site",
        )

    if site_capacity_mw >= smr_capacity_mwe:
        return (
            "pass",
            json.dumps({"site_capacity_mw": site_capacity_mw}),
            f"Site capacity {site_capacity_mw:.0f} MW >= "
            f"{smr_name} requirement ({smr_capacity_mwe:.0f} MWe)",
        )

    return (
        "fail",
        json.dumps({"site_capacity_mw": site_capacity_mw}),
        f"Site capacity {site_capacity_mw:.0f} MW < "
        f"{smr_name} requirement ({smr_capacity_mwe:.0f} MWe)",
    )


@register_check
class GridCapacityCheck(ScreeningCheck):
    """BF-01: Grid Capacity Basic Filter."""

    criterion_id = CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningVerdict]:
        smrs = _smr_thresholds(settings)
        if not smrs:
            log.warning("no_smr_types_configured")
            return []

        sites = session.execute(select(Site)).scalars().all()
        verdicts: list[ScreeningVerdict] = []
        inconclusive_logged: set = set()

        for site in sites:
            capacity = _resolve_capacity(site)

            for smr_key, smr_name, smr_mwe in smrs:
                verdict, measured_value, justification = evaluate_site_for_smr(
                    capacity, smr_key, smr_name, smr_mwe,
                )

                confidence = "high" if capacity is not None else "low"

                verdicts.append(
                    ScreeningVerdict(
                        site_id=site.site_id,
                        smr_key=smr_key,
                        criterion_id=self.criterion_id,
                        phase=self.phase,
                        verdict=verdict,
                        measured_value=measured_value,
                        threshold=f"{smr_mwe:.0f} MWe",
                        justification=justification,
                        confidence=confidence,
                        data_sources=["sites.grid_capacity_mw", "sites.installed_capacity_mw"],
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
                                "Neither grid_capacity_mw nor installed_capacity_mw "
                                "is set; BF-01 screening inconclusive"
                            ),
                            impact="blocking",
                            confidence="low",
                            run_id=run_id,
                        )
                    )

        return verdicts
