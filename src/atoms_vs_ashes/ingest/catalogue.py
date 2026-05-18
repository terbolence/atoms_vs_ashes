# man_hours: 0.8
"""Scoring-catalogue helpers — keep supplementary config sites in the DB."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.ingest.sites import load_supplementary_sites
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CATALOGUE_SYNC_RUN_ID = "catalogue-sync"

ENRICHMENT_TABLES = (
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
    "site_ownership",
    "site_units",
    "site_observations",
    "site_raw_responses",
)


def ensure_scoring_catalogue(
    session: Session,
    settings: Settings,
    *,
    run_id: str = CATALOGUE_SYNC_RUN_ID,
) -> int:
    """Ensure config-defined supplementary sites exist before scoring runs."""
    inserted = load_supplementary_sites(session, settings, run_id=run_id)
    if inserted:
        log.info("scoring_catalogue_supplementary_inserted", count=inserted)
    return inserted


def enrichment_row_counts(
    session: Session,
    site_id: uuid.UUID,
) -> dict[str, int]:
    """Return per-table row counts for one site (0 when the table is missing)."""
    sid = str(site_id)
    out: dict[str, int] = {}
    for table in ENRICHMENT_TABLES:
        try:
            out[table] = int(
                session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE site_id = :sid"),
                    {"sid": sid},
                ).scalar()
                or 0
            )
        except Exception:
            session.rollback()
            out[table] = 0
    return out


def assess_site_scoring_readiness(
    session: Session,
    site_id: uuid.UUID,
) -> dict[str, Any]:
    """True when the five criterion-family enrichment tables each have a row."""
    counts = enrichment_row_counts(session, site_id)
    required = (
        "site_natural_hazards",
        "site_human_hazards",
        "site_radiological",
        "site_emergency_planning",
        "site_infrastructure_v2",
    )
    missing = [t for t in required if counts.get(t, 0) < 1]
    site = session.get(Site, site_id)
    return {
        "site_id": str(site_id),
        "site_name": site.name if site else None,
        "ready": not missing,
        "missing_tables": missing,
        "row_counts": counts,
    }


def sites_missing_enrichment_in_scope(
    session: Session,
    *,
    site_ids: list[uuid.UUID],
) -> list[dict[str, Any]]:
    """Readiness report for each site id (used before scoring)."""
    return [
        assess_site_scoring_readiness(session, sid) for sid in site_ids
    ]


def warn_unready_sites_in_scope(
    session: Session,
    *,
    site_ids: list[uuid.UUID],
) -> list[str]:
    """Human-readable warnings for sites with no enrichment family rows."""
    warnings: list[str] = []
    for report in sites_missing_enrichment_in_scope(session, site_ids=site_ids):
        if report["ready"]:
            continue
        name = report.get("site_name") or report["site_id"]
        missing = ", ".join(report["missing_tables"])
        warnings.append(
            f"{name} ({report['site_id']}) has no enrichment in: {missing}; "
            "composite will be NULL until connectors are run on this DB profile."
        )
        log.warning(
            "site_not_enrichment_ready",
            site_id=report["site_id"],
            site_name=name,
            missing_tables=report["missing_tables"],
        )
    return warnings


__all__ = [
    "CATALOGUE_SYNC_RUN_ID",
    "ENRICHMENT_TABLES",
    "assess_site_scoring_readiness",
    "enrichment_row_counts",
    "ensure_scoring_catalogue",
    "sites_missing_enrichment_in_scope",
    "warn_unready_sites_in_scope",
]
