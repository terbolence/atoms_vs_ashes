# man_hours: 1.0
"""DB persistence helpers for the EGDI geology connector."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.egdi_geology.models import EgdiGeologyResult
from atoms_vs_ashes.db.models import (
    DataSource,
    SiteNaturalHazards,
    SiteObservation,
    SiteRadiological,
)

_SOURCE_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "egdi_hike_faults": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI HIKE pan-European fault database — fault proximity and activity",
    ),
    "egdi_lithology": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI surface lithology — soil/rock classification",
    ),
    "egdi_mines": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI mineral occurrences and coal heritage — mining proximity",
    ),
    "egdi_karst": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI karstified zones (CZ, IE) — subsidence hazard",
    ),
    "egdi_bgr_hydrogeology": (
        "https://maps.europe-geology.eu/wfs/",
        "BGR 1:1.5M hydrogeological map — aquifer type and groundwater bodies",
    ),
    "egdi_boreholes": (
        "https://maps.europe-geology.eu/wfs/",
        "EGDI geotechnical boreholes — foundation characterization",
    ),
}


def check_cache(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    ttl_days: int,
) -> SiteNaturalHazards | None:
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.nh02_quality is not None and row.fetched_at:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            return row
    return None


def ensure_data_sources(session: Session) -> dict[str, uuid.UUID]:
    ids: dict[str, uuid.UUID] = {}
    for name, (url, description) in _SOURCE_DESCRIPTIONS.items():
        existing = session.query(DataSource).filter_by(name=name).first()
        if existing:
            ids[name] = existing.source_id
        else:
            ds = DataSource(
                name=name, url=url, description=description,
                last_fetched=datetime.now(timezone.utc),
            )
            session.add(ds)
            session.flush()
            ids[name] = ds.source_id
    return ids


def persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
) -> list[str]:
    """Write geology data to SiteNaturalHazards + SiteRadiological columns."""
    now = datetime.now(timezone.utc)
    written: list[str] = []

    nh_row = session.get(SiteNaturalHazards, site_id)
    if nh_row is None:
        nh_row = SiteNaturalHazards(site_id=site_id)
        session.add(nh_row)

    _persist_natural_hazards(session, nh_row, site_id, result, run_id, written)
    nh_row.fetched_at = now
    nh_row.run_id = run_id

    _persist_radiological(session, site_id, result, run_id, now, written)
    if result.quality not in ("high", "medium"):
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-02", source_type="api",
            observation=(
                result.error or f"Quality: {result.quality} — "
                f"{len(result.layers_with_data)}/{len(result.layers_queried)} "
                "layers returned data"
            ),
            impact="negative", confidence=result.quality, run_id=run_id,
        ))
    return written


def _persist_natural_hazards(
    session: Session,
    nh_row: SiteNaturalHazards,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
    written: list[str],
) -> None:
    _persist_faults(session, nh_row, site_id, result, run_id, written)
    _persist_lithology(nh_row, result, written)
    _persist_mining_and_karst(session, nh_row, site_id, result, run_id, written)
    _persist_boreholes(session, nh_row, site_id, result, run_id, written)


def _persist_faults(
    session: Session,
    nh_row: SiteNaturalHazards,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
    written: list[str],
) -> None:
    if result.faults:
        nh_row.nearest_fault_km = result.faults.nearest_fault_distance_km
        if result.faults.nearest_fault_slip_rate_mm_yr is not None:
            nh_row.fault_slip_rate_mm_yr = result.faults.nearest_fault_slip_rate_mm_yr
    no_faults = result.faults is None or result.faults.fault_count_within_buffer == 0
    nh_row.nh02_quality = "low" if no_faults else "medium"
    nh_row.nh02_source = "egdi_hike_faults"
    written.append("NH-02")
    if no_faults:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-02", source_type="api",
            observation="No faults found within buffer — site may be outside HIKE coverage",
            impact="neutral", confidence=nh_row.nh02_quality or "low", run_id=run_id,
        ))


def _persist_lithology(
    nh_row: SiteNaturalHazards,
    result: EgdiGeologyResult,
    written: list[str],
) -> None:
    if result.lithology and result.lithology.lithology_class:
        nh_row.soil_type = result.lithology.lithology_class
        if nh_row.liquefaction_suscept is None:
            nh_row.liquefaction_suscept = result.lithology.liquefaction_susceptibility
    egdi_quality = (
        "low"
        if result.lithology is None or result.lithology.lithology_class is None
        else "medium"
    )
    if nh_row.nh03_source is None:
        nh_row.nh03_source = "egdi_lithology"
    if nh_row.nh03_quality is None or nh_row.nh03_quality == "low":
        nh_row.nh03_quality = egdi_quality
    written.append("NH-03")
    if result.lithology and result.lithology.rock_type:
        nh_row.slope_stability_class = result.lithology.rock_type
    nh_row.nh04_quality = egdi_quality
    written.append("NH-04")


def _persist_mining_and_karst(
    session: Session,
    nh_row: SiteNaturalHazards,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
    written: list[str],
) -> None:
    if result.mines:
        distance = result.mines.nearest_mine_distance_km
        nh_row.mining_void_present = distance is not None
        nh_row.mining_void_distance_km = distance
        nh_row.nh05b_quality = "medium"
        if distance is not None:
            nh_row.nh05b_comment = (
                "Nearest mapped EGDI mine/mining-heritage feature: "
                f"{distance:.3f} km; features within buffer: "
                f"{result.mines.mine_count_within_buffer}."
            )
    if result.karst:
        nh_row.karst_present = (
            result.karst.coverage_available and result.karst.in_karst_zone
        )
    nh_row.nh05_quality = "medium"
    written.append("NH-05")
    if result.karst and not result.karst.coverage_available:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-05", source_type="api",
            observation=(
                "No EGDI karst data available for this country — "
                "S-03 OneGeology or national survey required"
            ),
            impact="negative", confidence="low", run_id=run_id,
        ))


def _persist_boreholes(
    session: Session,
    nh_row: SiteNaturalHazards,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
    written: list[str],
) -> None:
    if result.boreholes and result.boreholes.nearest_borehole_depth_m is not None:
        nh_row.depth_to_bedrock_m = result.boreholes.nearest_borehole_depth_m
    no_boreholes = bool(result.boreholes and result.boreholes.borehole_count_within_buffer == 0)
    nh_row.nh06_quality = "low" if no_boreholes else "medium"
    written.append("NH-06")
    if no_boreholes:
        session.add(SiteObservation(
            site_id=site_id, criterion_id="NH-06", source_type="api",
            observation="No EGDI geotechnical boreholes within buffer — limited pilot coverage",
            impact="negative", confidence="low", run_id=run_id,
        ))


def _persist_radiological(
    session: Session,
    site_id: uuid.UUID,
    result: EgdiGeologyResult,
    run_id: str,
    now: datetime,
    written: list[str],
) -> None:
    ri_row = session.get(SiteRadiological, site_id)
    if ri_row is None:
        ri_row = SiteRadiological(site_id=site_id)
        session.add(ri_row)
    if result.hydrogeology:
        ri_row.aquifer_type = result.hydrogeology.aquifer_type
    ri_row.ri03_quality = (
        "low"
        if result.hydrogeology is None or result.hydrogeology.aquifer_type is None
        else "medium"
    )
    ri_row.fetched_at = now
    ri_row.run_id = run_id
    written.append("RI-03")


def persist_error_observation(
    session: Session, site_id: uuid.UUID, run_id: str, error: str,
) -> None:
    session.add(SiteObservation(
        site_id=site_id, criterion_id="NH-02", source_type="api",
        observation=f"Enrichment failed: {error}",
        impact="blocking", confidence="low", run_id=run_id,
    ))
