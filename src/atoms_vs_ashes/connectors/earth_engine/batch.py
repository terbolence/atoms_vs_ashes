# man_hours: 3.5
"""Batch enrichment and persistence for S-06 Google Earth Engine."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.earth_engine.fusion import FusionConfig, fuse_slope_degrees
from atoms_vs_ashes.connectors.earth_engine.models import (
    SOURCE_DESCRIPTION,
    SOURCE_NAME,
    SOURCE_URL,
    BatchResult,
    EarthEngineResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.earth_engine.client import GEE_DISABLED_MSG
from atoms_vs_ashes.connectors.earth_engine.parsers import terrain_slope_stability_class
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteEmergencyPlanning,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteObservation,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.earth_engine.client import EarthEngineConnector

log = get_logger(__name__)


def _fusion_cfg(settings: Any | None) -> FusionConfig:
    if settings and hasattr(settings, "_yaml"):
        raw = settings._yaml.get("connectors", {}).get("earth_engine", {}).get("fusion") or {}
        return FusionConfig(
            small_rel_tolerance=float(raw.get("small_rel_tolerance", 0.12)),
            small_abs_slope_deg=float(raw.get("small_abs_slope_deg", 2.0)),
            small_abs_built=float(raw.get("small_abs_built", 0.08)),
            trusted_priority=tuple(
                raw.get(
                    "trusted_priority",
                    ["google_earth_engine", "sentinel_hub_cdse", "copernicus_dem_glo30"],
                ),
            ),
        )
    return FusionConfig()


def _demolition_score(demolition_class: str | None) -> int | None:
    if demolition_class == "minimal":
        return 88
    if demolition_class == "moderate":
        return 55
    if demolition_class == "extensive":
        return 22
    return None


def _should_skip_terrain(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    mode: str,
) -> bool:
    if mode != "fallback":
        return False
    nh = session.get(SiteNaturalHazards, site_id)
    if nh is None or nh.slope_angle_deg is None:
        return False
    if nh.run_id != run_id:
        return False
    return True


def _append_summary(existing: str | None, fragment: str) -> str:
    """Append a short human-readable note for Excel-friendly ``*_cross_source_summary``."""
    frag = fragment.strip()
    if not frag:
        return existing or ""
    if not existing:
        return frag
    return f"{existing} | {frag}"


def _ensure_data_source(session: Session) -> uuid.UUID:
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing:
        existing.last_fetched = datetime.now(timezone.utc)
        return existing.source_id
    ds = DataSource(
        name=SOURCE_NAME,
        url=SOURCE_URL,
        description=SOURCE_DESCRIPTION,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: EarthEngineResult,
    run_id: str,
    *,
    fusion_cfg: FusionConfig,
    terrain_skipped: bool,
) -> None:
    now = datetime.now(timezone.utc)
    nh = session.get(SiteNaturalHazards, site_id)
    if nh is None:
        nh = SiteNaturalHazards(site_id=site_id)
        session.add(nh)

    prior_slope = float(nh.slope_angle_deg) if nh.slope_angle_deg is not None else None

    if terrain_skipped:
        nh.nh04_cross_source_summary = _append_summary(
            nh.nh04_cross_source_summary,
            "GEE terrain not run (fallback: prior DEM slope already present for this run_id).",
        )
    elif result.terrain is not None:
        t = result.terrain
        nh.nh04_gee_slope_max_deg = t.slope_max_deg
        nh.nh04_gee_slope_mean_deg = t.slope_mean_deg
        nh.nh04_gee_terrain_class = t.terrain_class
        if prior_slope is not None:
            nh.nh04_dem_cog_slope_max_deg = prior_slope
        fusion = fuse_slope_degrees(
            copernicus_max_slope=prior_slope,
            gee_max_slope=t.slope_max_deg,
            cfg=fusion_cfg,
        )
        disc = fusion.get("discrepancy")
        nh.nh04_slope_discrepancy = disc if isinstance(disc, str) else str(disc)
        nh.nh04_slope_fusion_method = str(fusion.get("method", ""))
        fused = fusion.get("fused_slope_max_deg")
        if fused is not None:
            nh.slope_angle_deg = float(fused)
        nh.slope_stability_class = terrain_slope_stability_class(
            t.terrain_class,
            t.slope_max_deg,
        )
        nh.nh04_quality = "high" if t.quality == "high" else t.quality
        parts: list[str] = []
        if prior_slope is not None:
            parts.append(f"Prior DEM pipeline max slope {prior_slope}° (before GEE pass).")
        parts.append(
            f"GEE Copernicus DEM max {t.slope_max_deg}° mean {t.slope_mean_deg}° "
            f"terrain_class={t.terrain_class}.",
        )
        parts.append(
            f"Fusion method={fusion.get('method')}; discrepancy={fusion.get('discrepancy')}; "
            f"fused_max_deg={fused}.",
        )
        nh.nh04_cross_source_summary = _append_summary(nh.nh04_cross_source_summary, " ".join(parts))
        note = (
            f"NH-04 fused ({fusion.get('method')}); GEE max slope "
            f"{t.slope_max_deg}°, mean {t.slope_mean_deg}°. "
            f"Discrepancy vs prior DEM: {fusion.get('discrepancy')}."
        )
        prev = nh.nh04_comment or ""
        nh.nh04_comment = f"{prev}; {note}" if prev else note
    elif result.error:
        nh.nh04_cross_source_summary = _append_summary(
            nh.nh04_cross_source_summary,
            result.error[:2000] if result.error else "",
        )

    nh.fetched_at = now
    nh.run_id = run_id

    if result.fire is not None:
        f = result.fire
        nh.nh13_gee_modis_burn_months = f.modis_burn_count_25yr
        nh.nh13_gee_fire_recurrence_class = f.fire_recurrence_class
        nh.nh13_gee_burn_fraction_mean = f.modis_burn_fraction_mean
        nh.nh13_cross_source_summary = _append_summary(
            nh.nh13_cross_source_summary,
            f"GEE MODIS MCD64A1 burn-month signal≈{f.modis_burn_count_25yr}, "
            f"recurrence={f.fire_recurrence_class}, mean_burn_fraction={f.modis_burn_fraction_mean}.",
        )
        if f.modis_burn_fraction_mean is not None:
            nh.wildfire_combustible_pct = min(
                100.0,
                max(0.0, float(f.modis_burn_fraction_mean) * 100.0),
            )
        nh.nh13_quality = f.quality
        nh.nh13_comment = (
            f"MODIS MCD64A1 long-horizon fire proxy (GEE): "
            f"class={f.fire_recurrence_class}, "
            f"months_with_burn_signal≈{f.modis_burn_count_25yr}."
        )

    infra = session.get(SiteInfrastructureV2, site_id)
    if infra is None:
        infra = SiteInfrastructureV2(site_id=site_id)
        session.add(infra)

    if result.terrain is not None and not terrain_skipped:
        t = result.terrain
        infra.ns04_gee_terrain_class = t.terrain_class
        infra.ns04_gee_relief_range_m = t.relief_range_m
        infra.ns04_gee_grading_class = t.grading_class
        infra.ns04_cross_source_summary = _append_summary(
            infra.ns04_cross_source_summary,
            f"GEE DEM terrain_class={t.terrain_class}, relief_range_m={t.relief_range_m}, "
            f"grading_class={t.grading_class}.",
        )
        infra.fetched_at = now
        infra.run_id = run_id

    if result.built_up is not None:
        b = result.built_up
        infra.ns06_gee_built_fraction = b.built_fraction_dw
        infra.ns06_gee_demolition_class = b.demolition_class
        infra.ns06_cross_source_summary = _append_summary(
            infra.ns06_cross_source_summary,
            f"GEE Dynamic World built_fraction={b.built_fraction_dw}, "
            f"demolition_class={b.demolition_class}.",
        )
        score = _demolition_score(b.demolition_class)
        if infra.reusable_infra_score is None and score is not None:
            infra.reusable_infra_score = score
        infra.ns06_quality = b.quality
        infra.ns06_comment = (
            f"Dynamic World built mean={b.built_fraction_dw}; "
            f"class={b.demolition_class}."
        )
        infra.fetched_at = now
        infra.run_id = run_id

    ep = session.get(SiteEmergencyPlanning, site_id)
    if ep is None:
        ep = SiteEmergencyPlanning(site_id=site_id)
        session.add(ep)

    if result.terrain is not None and not terrain_skipped:
        t = result.terrain
        ep.ep03_gee_relief_16km_m = t.relief_16km_m
        ep.ep03_gee_mountain_barrier_score = t.mountain_barrier_score
        ep.ep03_cross_source_summary = _append_summary(
            ep.ep03_cross_source_summary,
            f"GEE relief within 16 km radius: {t.relief_16km_m} m vertical; "
            f"mountain_barrier_score={t.mountain_barrier_score}.",
        )
        extra = (
            f"GEE mountain relief@16km: {t.relief_16km_m} m, "
            f"barrier_score={t.mountain_barrier_score}."
        )
        ep.ep03_comment = f"{ep.ep03_comment}; {extra}" if ep.ep03_comment else extra
        ep.fetched_at = now
        ep.run_id = run_id

    if result.error:
        session.add(
            SiteObservation(
                site_id=site_id,
                criterion_id="NH-04",
                source_type="api",
                observation=f"Google Earth Engine partial failure: {result.error}",
                impact="negative",
                confidence="low",
                run_id=run_id,
            ),
        )


def enrich_site(
    connector: EarthEngineConnector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
    *,
    settings: Any | None = None,
    modules: dict[str, bool] | None = None,
) -> SiteEnrichmentSummary:
    if not connector.enabled:
        site = session.get(Site, site_id)
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name if site else "<unknown>",
            status="skipped",
            error=GEE_DISABLED_MSG,
        )
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name="<unknown>",
            status="error",
            error=f"Site {site_id} not found",
        )
    t0 = time.monotonic()
    _ensure_data_source(session)
    fusion_cfg = _fusion_cfg(settings)
    mods = modules or {"terrain": True, "fire": True, "built_up": True}
    skip_terrain = not mods.get("terrain", True) or _should_skip_terrain(
        session, site_id, run_id, connector.mode,
    )
    try:
        res = connector.fetch_all(
            float(site.latitude),
            float(site.longitude),
            run_terrain=not skip_terrain,
            run_fire=mods.get("fire", True),
            run_built=mods.get("built_up", True),
        )
        if skip_terrain:
            res.modules_skipped.append("terrain_prior_dem")
        _persist_result(
            session, site_id, res, run_id,
            fusion_cfg=fusion_cfg, terrain_skipped=skip_terrain,
        )
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="ok",
            slope_mean_deg=res.terrain.slope_mean_deg if res.terrain else None,
            terrain_class=res.terrain.terrain_class if res.terrain else None,
            fire_recurrence_class=res.fire.fire_recurrence_class if res.fire else None,
            modules_run=list(res.modules_succeeded),
            elapsed_ms=elapsed,
        )
    except Exception as exc:
        session.rollback()
        log.error("gee_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="error",
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def enrich_batch(
    connector: EarthEngineConnector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
    settings: Any | None = None,
    modules: dict[str, bool] | None = None,
    inter_request_delay_s: float = 1.0,
) -> BatchResult:
    batch = BatchResult(run_id=run_id)
    if not connector.enabled:
        log.warning("gee_batch_skip_disabled", run_id=run_id)
        return batch
    t_batch = time.monotonic()
    q = session.query(Site)
    if site_ids is not None:
        if not site_ids:
            return batch
        q = q.filter(Site.site_id.in_(site_ids))
    elif country_codes is not None:
        q = q.filter(Site.country_code.in_(country_codes))
    sites = q.order_by(Site.country_code, Site.name).all()
    batch.total_sites = len(sites)
    if not sites:
        return batch

    _ensure_data_source(session)
    fusion_cfg = _fusion_cfg(settings)
    mods = modules or {"terrain": True, "fire": True, "built_up": True}

    for i, site in enumerate(sites):
        t0 = time.monotonic()
        skip_terrain = not mods.get("terrain", True) or _should_skip_terrain(
            session, site.site_id, run_id, connector.mode,
        )
        try:
            res = connector.fetch_all(
                float(site.latitude),
                float(site.longitude),
                run_terrain=not skip_terrain,
                run_fire=mods.get("fire", True),
                run_built=mods.get("built_up", True),
            )
            if skip_terrain:
                res.modules_skipped.append("terrain_prior_dem")
                batch.skipped_s05_sufficient += 1
            _persist_result(
                session, site.site_id, res, run_id,
                fusion_cfg=fusion_cfg, terrain_skipped=skip_terrain,
            )
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            log.info(
                "gee_site_complete",
                site_id=str(site.site_id),
                index=i + 1,
                total=len(sites),
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(
                SiteEnrichmentSummary(
                    site_id=site.site_id,
                    site_name=site.name,
                    status="ok",
                    slope_mean_deg=res.terrain.slope_mean_deg if res.terrain else None,
                    terrain_class=res.terrain.terrain_class if res.terrain else None,
                    fire_recurrence_class=res.fire.fire_recurrence_class if res.fire else None,
                    modules_run=list(res.modules_succeeded),
                    elapsed_ms=elapsed_ms,
                ),
            )
        except Exception as exc:
            session.rollback()
            log.error("gee_site_error", site_id=str(site.site_id), error=str(exc))
            batch.failed += 1
            batch.per_site.append(
                SiteEnrichmentSummary(
                    site_id=site.site_id,
                    site_name=site.name,
                    status="error",
                    error=str(exc),
                    elapsed_ms=int((time.monotonic() - t0) * 1000),
                ),
            )
        if inter_request_delay_s > 0:
            time.sleep(inter_request_delay_s)
        if (i + 1) % 25 == 0:
            log.info(
                "gee_batch_progress",
                completed=i + 1,
                total=len(sites),
                succeeded=batch.succeeded,
                failed=batch.failed,
            )

    batch.elapsed_s = time.monotonic() - t_batch
    log.info(
        "gee_batch_done",
        run_id=run_id,
        total=batch.total_sites,
        succeeded=batch.succeeded,
        failed=batch.failed,
        skipped_s05_sufficient=batch.skipped_s05_sufficient,
    )
    return batch
