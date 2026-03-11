"""Ingest ownership data from the GEM Global Energy Ownership Tracker XLSX."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import (
    AuditLog,
    Site,
    SiteOwnership,
    StagingUnmatchedOwnership,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_COLUMN_MAP: dict[str, str] = {
    "Parent GEM Entity ID": "parent_gem_entity_id",
    "Parent": "parent_name",
    "Parent Registration Country": "parent_reg_country",
    "Parent Headquarters Country": "parent_hq_country",
    "Project": "project",
    "Share": "share_pct",
    "Ownership Path": "ownership_path",
    "Immediate Project Owner": "immediate_owner",
    "Immediate Project Owner GEM Entity ID": "immediate_owner_gem_id",
    "Tracker": "tracker",
    "Status": "status",
    "Capacity (MW)": "capacity_mw",
    "GEM location ID": "gem_location_id",
    "GEM unit ID": "gem_unit_id",
}


def _safe_float(val: Any) -> float | None:
    if val is None or str(val).strip() in ("", "--"):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _str_or_none(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("--", "nan", "NaN", "None"):
        return None
    return s


def _build_location_id_index(session: Session) -> dict[str, Any]:
    """Build lookup: gem_location_id → site_id."""
    rows = session.execute(
        select(Site.gem_location_id, Site.site_id).where(
            Site.gem_location_id.is_not(None)
        )
    ).all()
    return {r[0]: r[1] for r in rows}


def _build_unit_id_index(session: Session) -> dict[str, Any]:
    """Build lookup: gem_unit_phase_id → site_id."""
    rows = session.execute(
        select(Site.gem_unit_phase_id, Site.site_id).where(
            Site.gem_unit_phase_id.is_not(None)
        )
    ).all()
    return {r[0]: r[1] for r in rows}


def load_ownership(
    session: Session,
    settings: Settings,
    *,
    run_id: str,
    project_root: Path | None = None,
) -> dict[str, int]:
    """Parse, filter, link and insert ownership records.

    Returns a dict with keys: matched, unmatched, total.
    """
    root = project_root or Path(settings.source_files.get("ownership_tracker", "")).parent.parent
    tracker_path = root / settings.source_files["ownership_tracker"]
    sheet = settings.source_files.get("ownership_tracker_sheet", "Coal Plant Ownership")

    log.info("reading_ownership_tracker", path=str(tracker_path), sheet=sheet)
    df = pd.read_excel(tracker_path, sheet_name=sheet, dtype=str)
    df.columns = df.columns.str.strip()

    loc_index = _build_location_id_index(session)
    unit_index = _build_unit_id_index(session)

    in_scope_loc_ids = set(loc_index.keys())

    df = df[df["GEM location ID"].isin(in_scope_loc_ids)].copy()
    log.info("filtered_ownership_in_scope", rows=len(df))

    matched = 0
    unmatched = 0

    for idx, raw_row in df.iterrows():
        mapped = {target: raw_row.get(src) for src, target in _COLUMN_MAP.items()}

        gem_loc = _str_or_none(mapped.get("gem_location_id"))
        gem_unit = _str_or_none(mapped.get("gem_unit_id"))

        site_id = None
        if gem_loc and gem_loc in loc_index:
            site_id = loc_index[gem_loc]
        elif gem_unit and gem_unit in unit_index:
            site_id = unit_index[gem_unit]

        if site_id is None:
            raw_dict = {k: _str_or_none(v) for k, v in raw_row.items()}
            session.add(StagingUnmatchedOwnership(
                raw_data=raw_dict,
                reason=f"No site match for gem_location_id={gem_loc}, gem_unit_id={gem_unit}",
            ))
            session.add(AuditLog(
                operation="stage_unmatched",
                table_name="_staging_unmatched_ownership",
                source_file=str(tracker_path),
                source_row=int(idx) if isinstance(idx, (int, float)) else None,
                run_id=run_id,
                message=f"Unmatched ownership row: loc={gem_loc} unit={gem_unit}",
            ))
            unmatched += 1
            continue

        record = SiteOwnership(
            site_id=site_id,
            parent_gem_entity_id=_str_or_none(mapped.get("parent_gem_entity_id")),
            parent_name=_str_or_none(mapped.get("parent_name")),
            parent_reg_country=_str_or_none(mapped.get("parent_reg_country")),
            parent_hq_country=_str_or_none(mapped.get("parent_hq_country")),
            project=_str_or_none(mapped.get("project")),
            share_pct=_safe_float(mapped.get("share_pct")),
            ownership_path=_str_or_none(mapped.get("ownership_path")),
            immediate_owner=_str_or_none(mapped.get("immediate_owner")),
            immediate_owner_gem_id=_str_or_none(mapped.get("immediate_owner_gem_id")),
            tracker=_str_or_none(mapped.get("tracker")),
            status=_str_or_none(mapped.get("status")),
            capacity_mw=_safe_float(mapped.get("capacity_mw")),
            gem_location_id=gem_loc,
            gem_unit_id=gem_unit,
        )
        session.add(record)

        session.add(AuditLog(
            operation="insert",
            table_name="site_ownership",
            site_id=site_id,
            after_value={"parent_name": record.parent_name, "share_pct": str(record.share_pct)},
            source_file=str(tracker_path),
            source_row=int(idx) if isinstance(idx, (int, float)) else None,
            run_id=run_id,
            message="Ownership record ingested",
        ))
        matched += 1

    totals = {"matched": matched, "unmatched": unmatched, "total": matched + unmatched}
    log.info("ownership_ingestion_complete", **totals)
    return totals


def validate_ownership(session: Session) -> list[str]:
    """Run post-ingestion checks and return a list of warnings."""
    warnings: list[str] = []

    sites_with_ownership = session.execute(
        select(SiteOwnership.site_id).distinct()
    ).scalars().all()

    total_sites = session.execute(select(Site.site_id)).scalars().all()
    sites_without = set(total_sites) - set(sites_with_ownership)
    if sites_without:
        warnings.append(
            f"{len(sites_without)} site(s) have no ownership records."
        )

    from sqlalchemy import func
    share_sums = session.execute(
        select(
            SiteOwnership.site_id,
            func.sum(SiteOwnership.share_pct).label("total_share"),
        ).group_by(SiteOwnership.site_id)
    ).all()

    for site_id, total_share in share_sums:
        if total_share is None:
            continue
        try:
            ts = float(total_share)
        except (ValueError, TypeError):
            continue
        if ts < 80 or ts > 120:
            warnings.append(
                f"Site {site_id}: ownership share sum = {ts:.1f}% "
                f"(expected ~100%)"
            )

    return warnings
