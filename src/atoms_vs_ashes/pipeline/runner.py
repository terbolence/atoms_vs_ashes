"""Pipeline orchestration — ties ingestion stages together."""

from __future__ import annotations

from pathlib import Path

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.ingest.ownership import load_ownership, validate_ownership
from atoms_vs_ashes.ingest.sites import load_coal_tracker, load_supplementary_sites
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.pipeline.quality_report import generate_quality_report

log = get_logger(__name__)


def run_ingest(
    settings: Settings,
    *,
    run_id: str,
    project_root: Path | None = None,
) -> dict:
    """Execute the full ingestion pipeline (sites + ownership)."""
    summary: dict = {"run_id": run_id, "stages": {}}

    with session_scope() as session:
        sites_count = load_coal_tracker(
            session, settings, run_id=run_id, project_root=project_root
        )
        suppl_count = load_supplementary_sites(
            session, settings, run_id=run_id
        )
        summary["stages"]["sites"] = {
            "tracker_sites": sites_count,
            "supplementary_sites": suppl_count,
        }

    with session_scope() as session:
        ownership_result = load_ownership(
            session, settings, run_id=run_id, project_root=project_root
        )
        summary["stages"]["ownership"] = ownership_result

    with session_scope() as session:
        ownership_warnings = validate_ownership(session)
        summary["stages"]["ownership_warnings"] = ownership_warnings

    log.info("ingest_complete", summary=summary)
    return summary


def run_validate(settings: Settings, *, run_id: str) -> dict:
    """Run data-quality validation checks against the current DB state."""
    with session_scope() as session:
        report = generate_quality_report(session, run_id=run_id)
    log.info("validation_complete", report=report)
    return report
