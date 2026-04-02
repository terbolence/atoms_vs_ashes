# man_hours: 3.0
"""NS-05 Coal site reuse analysis from GEM data.

Priority 2 supplement -- compares existing coal site footprint against
SMR land requirements.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
from atoms_vs_ashes.db.models import SiteAttribute
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-05"
SOURCE_NAME = "gem_coal_tracker_reuse"
DEFAULT_SMR_LAND_HA = 72.8
ELIGIBLE_STATUSES = {"retired", "mothballed", "planned_closure"}


@dataclass
class CoalSiteResult:
    site_area_ha: float | None = None
    smr_land_ha: float = DEFAULT_SMR_LAND_HA
    sufficiency_ratio: float = 0.0
    is_sufficient: bool = False
    status: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "site_area_ha": self.site_area_ha,
            "smr_land_ha": self.smr_land_ha,
            "sufficiency_ratio": round(self.sufficiency_ratio, 3),
            "is_sufficient": self.is_sufficient,
            "status": self.status,
            "source": SOURCE_NAME,
            "error": self.error,
        }


def evaluate_coal_site(
    site_area_ha: float | None,
    status: str | None,
    smr_land_ha: float = DEFAULT_SMR_LAND_HA,
) -> CoalSiteResult:
    result = CoalSiteResult(
        site_area_ha=site_area_ha,
        smr_land_ha=smr_land_ha,
        status=status,
    )

    if site_area_ha is None or site_area_ha <= 0:
        result.error = "No site area available"
        return result

    result.sufficiency_ratio = site_area_ha / smr_land_ha
    result.is_sufficient = result.sufficiency_ratio >= 1.0
    return result


def assess_and_persist(
    site_id: Any,
    site_area_ha: float | None,
    status: str | None,
    session: Session,
    run_id: str,
    smr_land_ha: float = DEFAULT_SMR_LAND_HA,
) -> CoalSiteResult:
    t0 = time.monotonic()
    result = evaluate_coal_site(site_area_ha, status, smr_land_ha)

    source_id = ensure_data_source(
        session, name=SOURCE_NAME,
        url="https://globalenergymonitor.org/projects/global-coal-plant-tracker/",
        description="GEM Coal Plant Tracker site footprint for NS-05 reuse assessment",
    )

    session.merge(SiteAttribute(
        site_id=site_id, criterion_id=CRITERION_ID,
        value_numeric=result.sufficiency_ratio,
        value_json=result.to_dict(), source_id=source_id,
        run_id=run_id, cache_status="fresh",
    ))

    if result.error:
        write_quality_flag(
            session, site_id=site_id, dataset="gem_coal_tracker",
            dimension="coal_site_reuse", level="low",
            detail=result.error, run_id=run_id,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    log.info("coal_site_analysis_assess_ok", site_id=str(site_id),
             criterion_id=CRITERION_ID, run_id=run_id, elapsed_ms=elapsed_ms)
    return result
