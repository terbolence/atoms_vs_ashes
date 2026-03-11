"""Data quality report generation per spec §2.7.2 step 7 and §2.8."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    AuditLog,
    Country,
    DataQualityFlag,
    Site,
    SiteOwnership,
    StagingUnmatchedOwnership,
)


def generate_quality_report(session: Session, *, run_id: str) -> dict:
    """Produce a reproducible data-quality report from the current DB state."""
    report: dict = {}

    # 1. Total site count
    total_sites = session.scalar(select(func.count(Site.site_id)))
    report["total_sites"] = total_sites

    # 2. Country coverage
    country_counts = session.execute(
        select(Site.country_code, func.count(Site.site_id))
        .group_by(Site.country_code)
        .order_by(func.count(Site.site_id).desc())
    ).all()
    report["sites_per_country"] = {row[0]: row[1] for row in country_counts}

    all_countries = session.execute(select(Country.country_code)).scalars().all()
    countries_with_sites = {row[0] for row in country_counts}
    countries_without = set(all_countries) - countries_with_sites
    report["countries_without_sites"] = sorted(countries_without)

    # 3. Coordinate completeness (should be 100% post-ingestion)
    missing_coords = session.scalar(
        select(func.count(Site.site_id)).where(
            (Site.latitude.is_(None)) | (Site.longitude.is_(None))
        )
    )
    report["sites_missing_coordinates"] = missing_coords

    # 4. Ownership linkage
    sites_with_ownership = session.scalar(
        select(func.count(func.distinct(SiteOwnership.site_id)))
    )
    report["sites_with_ownership"] = sites_with_ownership
    report["sites_without_ownership"] = total_sites - (sites_with_ownership or 0)

    unmatched = session.scalar(
        select(func.count(StagingUnmatchedOwnership.row_id))
    )
    report["unmatched_ownership_rows"] = unmatched

    # 5. Status breakdown
    status_counts = session.execute(
        select(Site.status, func.count(Site.site_id))
        .group_by(Site.status)
        .order_by(func.count(Site.site_id).desc())
    ).all()
    report["status_breakdown"] = {row[0]: row[1] for row in status_counts}

    # 6. Audit log count for this run
    audit_count = session.scalar(
        select(func.count(AuditLog.log_id)).where(AuditLog.run_id == run_id)
    )
    report["audit_entries_this_run"] = audit_count

    # Persist summary-level flags
    if missing_coords and missing_coords > 0:
        session.add(DataQualityFlag(
            dataset="sites",
            dimension="completeness",
            level="low",
            detail=f"{missing_coords} site(s) missing coordinates",
            run_id=run_id,
        ))
    if countries_without:
        session.add(DataQualityFlag(
            dataset="sites",
            dimension="completeness",
            level="medium",
            detail=f"Countries with no sites: {', '.join(sorted(countries_without))}",
            run_id=run_id,
        ))

    return report
