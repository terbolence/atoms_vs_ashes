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
from atoms_vs_ashes.db.models import ScreeningVerdict, Site, SiteObservation, SmrDesign
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


def _smr_rows_from_db(session: Session) -> list[tuple[str, str, float, float | None]]:
    """``(key, name, capacity_mwe, land_ha)`` from :class:`SmrDesign`, sorted by MWe."""
    rows = session.execute(
        select(
            SmrDesign.smr_key,
            SmrDesign.name,
            SmrDesign.capacity_mwe,
            SmrDesign.land_requirement_ha,
        ).order_by(SmrDesign.capacity_mwe, SmrDesign.smr_key)
    ).all()
    out: list[tuple[str, str, float, float | None]] = []
    for k, n, c, h in rows:
        out.append(
            (
                k,
                n,
                float(c),
                float(h) if h is not None else None,
            )
        )
    return out


def evaluate_site(
    site_value: float | None,
    smrs: list[tuple[str, str, float]],
) -> tuple[str, dict, str]:
    """Partition *site_value* (MW) against a sorted SMR ``(key, name, mwe)`` list."""
    from atoms_vs_ashes.screening import _site_smr_batch

    return _site_smr_batch.evaluate_site(
        site_value,
        smrs,
        site_key="site_capacity_mw",
        unit_singular="capacity (MW)",
        value_fmt="%.0f",
    )


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
        smrs = _smr_rows_from_db(session)
        if not smrs and settings.smr_types:
            log.warning(
                "no_smr_in_db_falling_back_to_config",
                n_legacy=len(settings.smr_types),
            )
            smrs = [
                (k, s["name"], float(s["capacity_mwe"]), None)
                for k, s in settings.smr_types.items()
            ]
            smrs.sort(key=lambda t: t[2])
        if not smrs:
            log.warning("no_smr_types_configured")
            return []

        sites = session.execute(select(Site)).scalars().all()
        verdicts: list[ScreeningVerdict] = []
        inconclusive_logged: set = set()

        for site in sites:
            capacity = _resolve_capacity(site)

            for smr_key, smr_name, smr_mwe, _land in smrs:
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
