# man_hours: 4.2
"""Persistence layer — writes LLM assessment results to the LLM database.

Maps each criterion's structured output to the appropriate domain table,
screening_verdicts, ranking_scores, and site_observations rows with full
LLM provenance tags.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.db.models import (
    AuditLog,
    RankingScore,
    ScreeningVerdict,
    Site,
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteRadiological,
)
from atoms_vs_ashes.llm.prompts import get_prompt_version
from atoms_vs_ashes.llm.schemas import (
    AVOIDANCE_KEYS,
    EXCLUSIONARY_KEYS,
    PROMPT_REGISTRY,
)
from sqlalchemy import inspect as sa_inspect

from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def _safe_truncate(row: Any, col_name: str, value: Any) -> Any:
    """Clip string values to column max length to prevent StringDataRightTruncation."""
    if not isinstance(value, str):
        return value
    mapper = sa_inspect(type(row))
    col = mapper.columns.get(col_name)
    if col is not None and hasattr(col.type, "length") and col.type.length:
        max_len = col.type.length
        if len(value) > max_len:
            log.warning(
                "persist_truncated_value",
                column=col_name,
                original_len=len(value),
                max_len=max_len,
            )
            return value[: max_len - 3] + "..."
    return value

_DOMAIN_TABLE_MAP: dict[str, type] = {
    "NH-01": SiteNaturalHazards,
    "NH-02": SiteNaturalHazards,
    "NH-03": SiteNaturalHazards,
    "NH-04": SiteNaturalHazards,
    "NH-05": SiteNaturalHazards,
    "NH-05b": SiteNaturalHazards,
    "NH-06": SiteNaturalHazards,
    "NH-07": SiteNaturalHazards,
    "NH-08": SiteNaturalHazards,
    "NH-09": SiteNaturalHazards,
    "NH-10": SiteNaturalHazards,
    "NH-11": SiteNaturalHazards,
    "NH-12": SiteNaturalHazards,
    "NH-13": SiteNaturalHazards,
    "NH-14": SiteNaturalHazards,
    "HI-01": SiteHumanHazards,
    "HI-02": SiteHumanHazards,
    "HI-03": SiteHumanHazards,
    "HI-04": SiteHumanHazards,
    "HI-05": SiteHumanHazards,
    "HI-06": SiteHumanHazards,
    "HI-07": SiteHumanHazards,
    "HI-08": SiteHumanHazards,
    "RI-01": SiteRadiological,
    "RI-02": SiteRadiological,
    "RI-03": SiteRadiological,
    "RI-04": SiteRadiological,
    "RI-05": SiteRadiological,
    "RI-06": SiteRadiological,
    "EP-01": SiteEmergencyPlanning,
    "EP-02": SiteEmergencyPlanning,
    "EP-03": SiteEmergencyPlanning,
    "EP-04": SiteEmergencyPlanning,
    "EP-05": SiteEmergencyPlanning,
    "NS-01": SiteInfrastructureV2,
    "NS-02": SiteInfrastructureV2,
    "NS-03": SiteInfrastructureV2,
    "NS-04": SiteInfrastructureV2,
    "NS-05": SiteInfrastructureV2,
    "NS-06": SiteInfrastructureV2,
    "NS-07": SiteInfrastructureV2,
    "NS-08": SiteInfrastructureV2,
    "NS-09": SiteInfrastructureV2,
    "NS-10": SiteInfrastructureV2,
    "NS-11": SiteInfrastructureV2,
    "NS-12": SiteInfrastructureV2,
    "NS-13": SiteInfrastructureV2,
}

# Maps LLM response fields → domain table column names per criterion_id.
# Only criterion-specific fields are listed; common fields (quality, comment,
# fetched_at, run_id) are handled generically.
_FIELD_MAP: dict[str, dict[str, str]] = {
    "NH-02": {"nearest_fault_km": "nearest_fault_km", "nearest_fault_name": "fault_name", "fault_slip_rate_mm_yr": "fault_slip_rate_mm_yr"},
    "NH-03": {"liquefaction_suscept": "liquefaction_suscept", "soil_type": "soil_type", "groundwater_depth_m": "groundwater_depth_m"},
    "NH-04": {"slope_angle_deg": "slope_angle_deg", "slope_stability_class": "slope_stability_class", "landslide_inventory_notes": "landslide_inventory_notes"},
    "NH-07": {"nearest_holocene_volcano_km": "nearest_holocene_volcano_km", "volcano_name": "volcano_name"},
    "NH-05": {"karst_present": "karst_present", "karst_severity": "karst_severity", "karst_formation_type": "karst_formation_type"},
    "NH-05b": {"mining_void_present": "mining_void_present", "subsidence_risk_class": "subsidence_risk_class", "collapse_mechanism": "collapse_mechanism"},
    "NS-08": {"ecological_natural_pct": "ecological_natural_pct", "ecological_patch_count": "ecological_patch_count"},
    "EP-01": {},
    "NS-01": {"cooling_source_type": "cooling_source_type", "cooling_source_name": "cooling_source_name", "cooling_distance_km": "cooling_distance_km", "estimated_flow_m3s": "cooling_flow_m3s"},
    "HI-01": {"nearest_airport_km": "nearest_airport_km", "nearest_airport_name": "nearest_airport_name", "airport_count": "airport_count"},
    "HI-06": {"nearest_military_km": "nearest_military_km", "nearest_military_name": "nearest_military_name", "military_count": "military_count"},
    "HI-02": {"nearest_seveso_km": "nearest_seveso_km", "nearest_industrial_km": "nearest_industrial_km"},
    "HI-03": {"nearest_toxic_source_km": "nearest_toxic_source_km"},
    "HI-04": {"nearest_flammable_storage_km": "nearest_flammable_storage_km", "nearest_pipeline_km": "nearest_pipeline_km"},
    "HI-05": {"hazmat_route_distance_km": "hazmat_route_distance_km"},
    "HI-07": {"nearest_transmitter_km": "nearest_transmitter_km", "transmitter_type": "transmitter_type", "transmitter_count": "transmitter_count"},
    "HI-08": {"nearest_nuclear_km": "nearest_nuclear_km", "nearest_nuclear_name": "nearest_nuclear_name"},
    "NH-01": {"pga_475yr_g": "pga_475yr_g", "pga_2475yr_g": "pga_2475yr_g"},
    "NH-06": {"bearing_capacity_kpa": "bearing_capacity_kpa", "depth_to_bedrock_m": "depth_to_bedrock_m"},
    "NH-08": {"distance_to_coast_km": "distance_to_coast_km", "storm_surge_risk": "storm_surge_risk", "tsunami_risk": "tsunami_risk"},
    "NH-09": {"flood_zone_class": "flood_zone_class", "nearest_river_km": "nearest_river_km", "dam_break_exposure": "dam_break_exposure"},
    "NH-10": {"max_wind_speed_ms": "max_wind_speed_ms"},
    "NH-11": {"extreme_precip_mm": "extreme_precip_mm"},
    "NH-12": {"extreme_temp_max_c": "extreme_temp_max_c", "extreme_temp_min_c": "extreme_temp_min_c"},
    "NH-13": {"wildfire_combustible_pct": "wildfire_combustible_pct"},
    "RI-01": {"prevailing_wind_dir": "prevailing_wind_dir", "avg_wind_speed_ms": "avg_wind_speed_ms", "mixing_height_m": "mixing_height_m"},
    "RI-02": {"nearest_river_flow_m3s": "nearest_river_flow_m3s"},
    "RI-03": {"aquifer_type": "aquifer_type", "groundwater_flow_dir": "groundwater_flow_dir"},
    "RI-04": {"pop_density_5km": "pop_density_5km", "pop_density_25km": "pop_density_25km", "pop_total_80km": "pop_total_80km"},
    "RI-05": {"nearest_city_50k_km": "nearest_city_50k_km", "nearest_city_name": "nearest_city_name", "nearest_city_pop": "nearest_city_pop"},
    "RI-06": {"pop_growth_rate_pct": "pop_growth_rate_pct", "projected_pop_25km_60yr": "projected_pop_25km_60yr"},
    "EP-02": {"road_density_km_per_km2": "road_density_km_per_km2", "has_motorway_access": "has_motorway_access"},
    "EP-03": {"major_river_barrier": "major_river_barrier", "waterway_count_epz": "waterway_count_epz"},
    "EP-04": {"hospital_count_epz": "hospital_count_epz", "prison_count_epz": "prison_count_epz", "care_home_count_epz": "care_home_count_epz"},
    "NS-02": {"nearest_substation_km": "nearest_substation_km", "nearest_hv_line_km": "nearest_hv_line_km", "grid_export_capacity_mw": "grid_export_capacity_mw"},
    "NS-03": {"nearest_highway_km": "nearest_highway_km", "nearest_rail_km": "nearest_rail_km", "nearest_waterway_km": "nearest_waterway_km", "heavy_haul_capable": "heavy_haul_capable"},
    "NS-04": {"dominant_land_class": "dominant_land_class", "favourable_land_pct": "favourable_land_pct"},
    "NS-05": {"buildable_area_ha": "buildable_area_ha", "largest_contiguous_ha": "largest_contiguous_ha"},
    "NS-06": {"reusable_infra_score": "reusable_infra_score"},
    "NS-07": {"env_impact_tier": "env_impact_tier", "env_impact_notes": "env_impact_notes"},
    "NS-13": {"laydown_suitable_ha": "laydown_suitable_ha", "laydown_largest_patch_ha": "laydown_largest_patch_ha"},
    "NH-14": {"combined_hazard_notes": "combined_hazard_notes"},
    "EP-05": {"concurrent_hazard_notes": "concurrent_hazard_notes"},
}

_QUALITY_COL: dict[str, str] = {
    "NH-01": "nh01_quality", "NH-02": "nh02_quality", "NH-03": "nh03_quality",
    "NH-04": "nh04_quality", "NH-05": "nh05_quality", "NH-05b": "nh05b_quality", "NH-06": "nh06_quality",
    "NH-07": "nh07_quality", "NH-08": "nh08_quality", "NH-09": "nh09_quality",
    "NH-10": "nh10_quality", "NH-11": "nh11_quality", "NH-12": "nh12_quality",
    "NH-13": "nh13_quality", "NH-14": "nh14_quality",
    "HI-01": "hi01_quality", "HI-02": "hi02_quality", "HI-03": "hi03_quality",
    "HI-04": "hi04_quality", "HI-05": "hi05_quality", "HI-06": "hi06_quality",
    "HI-07": "hi07_quality", "HI-08": "hi08_quality",
    "RI-01": "ri01_quality", "RI-02": "ri02_quality", "RI-03": "ri03_quality",
    "RI-04": "ri04_quality", "RI-05": "ri05_quality", "RI-06": "ri06_quality",
    "EP-01": "ep01_quality", "EP-02": "ep02_quality", "EP-03": "ep03_quality",
    "EP-04": "ep04_quality", "EP-05": "ep05_quality",
    "NS-01": "ns01_quality", "NS-02": "ns02_quality", "NS-03": "ns03_quality",
    "NS-04": "ns04_quality", "NS-05": "ns05_quality", "NS-06": "ns06_quality",
    "NS-07": "ns07_quality", "NS-08": "ns08_quality", "NS-09": "ns09_quality",
    "NS-10": "ns10_quality", "NS-11": "ns11_quality", "NS-12": "ns12_quality",
    "NS-13": "ns13_quality",
}

_COMMENT_COL: dict[str, str] = {k: k.replace("_quality", "_comment") for k in _QUALITY_COL.values()}
# Invert so criterion_id → column name
_COMMENT_COL_BY_CRITERION: dict[str, str] = {}
for cid, qcol in _QUALITY_COL.items():
    _COMMENT_COL_BY_CRITERION[cid] = qcol.replace("_quality", "_comment")


def _get_or_create_domain_row(session: Session, site_id: uuid.UUID, criterion_id: str) -> Any:
    """Return the domain table row for a site, creating one if needed."""
    table_cls = _DOMAIN_TABLE_MAP.get(criterion_id)
    if table_cls is None:
        return None
    row = session.get(table_cls, site_id)
    if row is None:
        row = table_cls(site_id=site_id)
        session.add(row)
    return row


def persist_exclusionary(
    session: Session,
    *,
    site_id: uuid.UUID,
    prompt_key: str,
    result: dict[str, Any],
    run_id: str,
    smr_keys: list[str],
) -> None:
    """Persist an exclusionary (E1-E9) LLM assessment."""
    schema_cls = PROMPT_REGISTRY[prompt_key]
    criterion_id = schema_cls.model_fields["criterion_id"].default
    model_name = result.get("_model", "unknown")
    thinking = result.get("_thinking", "")
    now = datetime.now(timezone.utc)

    prompt_ver = get_prompt_version(prompt_key)
    ensure_data_source(
        session,
        name=f"llm:{model_name}",
        url="https://api.anthropic.com",
        description=f"Anthropic {model_name} — LLM siting assessment (prompt {prompt_ver})",
    )

    domain_row = _get_or_create_domain_row(session, site_id, criterion_id)
    if domain_row is not None:
        field_map = _FIELD_MAP.get(criterion_id, {})
        for src_field, db_col in field_map.items():
            val = result.get(src_field)
            if val is not None and hasattr(domain_row, db_col):
                val = _safe_truncate(domain_row, db_col, val)
                setattr(domain_row, db_col, val)
        q_col = _QUALITY_COL.get(criterion_id)
        if q_col and hasattr(domain_row, q_col):
            setattr(domain_row, q_col, "llm")
        c_col = _COMMENT_COL_BY_CRITERION.get(criterion_id)
        if c_col and hasattr(domain_row, c_col):
            comment = _safe_truncate(domain_row, c_col, result.get("justification", "")[:500])
            setattr(domain_row, c_col, comment)
        domain_row.fetched_at = now
        domain_row.run_id = run_id

    phase = "exclusionary" if prompt_key in EXCLUSIONARY_KEYS else "avoidance"
    sn_raw = result.get("sources_needed")
    sources_needed_text = "; ".join(sn_raw) if isinstance(sn_raw, list) else (sn_raw or None)
    for smr_key in smr_keys:
        existing = session.query(ScreeningVerdict).filter_by(
            site_id=site_id, smr_key=smr_key, criterion_id=criterion_id,
            prompt_key=prompt_key, run_id=run_id,
        ).first()
        if existing:
            existing.verdict = result.get("verdict", "inconclusive")
            existing.justification = result.get("justification", "No justification provided")
            existing.confidence = result.get("confidence", "low")
            existing.data_sources = [f"llm:{model_name}"]
            existing.sources_needed = sources_needed_text
            existing.phase = phase
            existing.screened_at = now
        else:
            session.add(ScreeningVerdict(
                site_id=site_id,
                smr_key=smr_key,
                criterion_id=criterion_id,
                prompt_key=prompt_key,
                phase=phase,
                verdict=result.get("verdict", "inconclusive"),
                justification=result.get("justification", "No justification provided"),
                confidence=result.get("confidence", "low"),
                data_sources=[f"llm:{model_name}"],
                sources_needed=sources_needed_text,
                run_id=run_id,
            ))

    author_tag = f"{model_name}|{prompt_ver}"
    if thinking:
        write_observation(
            session,
            site_id=site_id,
            criterion_id=criterion_id,
            observation=f"[LLM thinking trace]\n{thinking[:4000]}",
            run_id=run_id,
            source_type="llm",
            impact="neutral",
            confidence=result.get("confidence", "low"),
            author=author_tag,
        )

    write_observation(
        session,
        site_id=site_id,
        criterion_id=criterion_id,
        observation=result.get("justification", ""),
        run_id=run_id,
        source_type="llm",
        impact="neutral" if result.get("verdict") == "pass" else "negative",
        confidence=result.get("confidence", "low"),
        author=author_tag,
    )


def persist_avoidance(
    session: Session,
    *,
    site_id: uuid.UUID,
    prompt_key: str,
    result: dict[str, Any],
    run_id: str,
    smr_keys: list[str],
) -> None:
    """Persist an avoidance (A1-A15) LLM assessment — same structure as exclusionary."""
    persist_exclusionary(
        session,
        site_id=site_id,
        prompt_key=prompt_key,
        result=result,
        run_id=run_id,
        smr_keys=smr_keys,
    )


def persist_ranking(
    session: Session,
    *,
    site_id: uuid.UUID,
    prompt_key: str,
    result: dict[str, Any],
    run_id: str,
    smr_keys: list[str],
) -> None:
    """Persist a ranking criterion LLM assessment."""
    schema_cls = PROMPT_REGISTRY[prompt_key]
    criterion_id = schema_cls.model_fields["criterion_id"].default
    model_name = result.get("_model", "unknown")
    prompt_ver = get_prompt_version(prompt_key)
    now = datetime.now(timezone.utc)

    ensure_data_source(
        session,
        name=f"llm:{model_name}",
        url="https://api.anthropic.com",
        description=f"Anthropic {model_name} — LLM siting assessment (prompt {prompt_ver})",
    )

    domain_row = _get_or_create_domain_row(session, site_id, criterion_id)
    if domain_row is not None:
        field_map = _FIELD_MAP.get(criterion_id, {})
        for src_field, db_col in field_map.items():
            val = result.get(src_field)
            if val is not None and hasattr(domain_row, db_col):
                val = _safe_truncate(domain_row, db_col, val)
                setattr(domain_row, db_col, val)
        q_col = _QUALITY_COL.get(criterion_id)
        if q_col and hasattr(domain_row, q_col):
            setattr(domain_row, q_col, "llm")
        c_col = _COMMENT_COL_BY_CRITERION.get(criterion_id)
        if c_col and hasattr(domain_row, c_col):
            comment = _safe_truncate(domain_row, c_col, result.get("justification", "")[:500])
            setattr(domain_row, c_col, comment)
        domain_row.fetched_at = now
        domain_row.run_id = run_id

    author_tag = f"{model_name}|{prompt_ver}"
    score_val = result.get("score")
    if score_val is not None:
        # LLM prompts still emit scores on the legacy 1–5 scale; the DB
        # now stores native 0–10 (Alembic 033).  Scale by 2 so existing
        # prompts remain usable until the rubric-driven scoring engine
        # lands in phase 1.3.
        def _scale(val: Any) -> float | None:
            return float(val) * 2 if val is not None else None

        scaled_score = _scale(score_val)
        scaled_low = _scale(result.get("score_low"))
        scaled_high = _scale(result.get("score_high"))
        for smr_key in smr_keys:
            existing_rs = session.query(RankingScore).filter_by(
                site_id=site_id, smr_key=smr_key,
                criterion_id=criterion_id, run_id=run_id,
            ).first()
            if existing_rs:
                existing_rs.score_0_10 = scaled_score
                existing_rs.score_low_0_10 = scaled_low
                existing_rs.score_high_0_10 = scaled_high
                existing_rs.confidence = result.get("confidence", "low")
                existing_rs.justification = result.get("justification", "")
                existing_rs.data_sources = [f"llm:{model_name}"]
                existing_rs.scored_at = now
            else:
                session.add(RankingScore(
                    site_id=site_id,
                    smr_key=smr_key,
                    criterion_id=criterion_id,
                    score_0_10=scaled_score,
                    score_low_0_10=scaled_low,
                    score_high_0_10=scaled_high,
                    confidence=result.get("confidence", "low"),
                    justification=result.get("justification", ""),
                    data_sources=[f"llm:{model_name}"],
                    run_id=run_id,
                ))

    write_observation(
        session,
        site_id=site_id,
        criterion_id=criterion_id,
        observation=result.get("justification", ""),
        run_id=run_id,
        source_type="llm",
        impact="neutral",
        confidence=result.get("confidence", "low"),
        author=author_tag,
    )


def persist_result(
    session: Session,
    *,
    site_id: uuid.UUID,
    prompt_key: str,
    result: dict[str, Any],
    run_id: str,
    smr_keys: list[str],
) -> None:
    """Route a result to the correct persistence function based on prompt key."""
    if prompt_key in EXCLUSIONARY_KEYS:
        persist_exclusionary(session, site_id=site_id, prompt_key=prompt_key,
                             result=result, run_id=run_id, smr_keys=smr_keys)
    elif prompt_key in AVOIDANCE_KEYS:
        persist_avoidance(session, site_id=site_id, prompt_key=prompt_key,
                          result=result, run_id=run_id, smr_keys=smr_keys)
    else:
        persist_ranking(session, site_id=site_id, prompt_key=prompt_key,
                        result=result, run_id=run_id, smr_keys=smr_keys)

    prompt_ver = get_prompt_version(prompt_key)
    session.add(AuditLog(
        operation="llm_assess",
        table_name="multi",
        site_id=site_id,
        run_id=run_id,
        message=f"LLM {prompt_key} assessment persisted (prompt {prompt_ver})",
    ))
