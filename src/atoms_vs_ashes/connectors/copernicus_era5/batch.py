# man_hours: 2.5
"""Batch enrichment and DB persistence for the S-04 Copernicus ERA5 connector.

Writes to the following domain tables (wide-column design):
  - SiteNaturalHazards: NH-10 (wind), NH-11 (precipitation), NH-12 (temperature)
  - SiteRadiological:   RI-01 (atmospheric dispersion, wind rose, stability)
  - SiteInfrastructureV2: NS-01 (seasonality proxy — appends to existing data)
  - SiteEmergencyPlanning: EP-02 (seasonal constraints proxy)
  - SiteObservation: full JSON payload for downstream consumers

Per LL-009: NS-01 uses append semantics for the shared comment field
to avoid overwriting data from HydroRIVERS/GloFAS connectors.

Each site is committed independently for isolation.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.connectors.copernicus_era5.models import (
    CONNECTOR_SLUG,
    SOURCE_ERA5,
    SOURCE_URL,
    BatchResult,
    Era5ClimateResult,
    SiteEnrichmentSummary,
)
from atoms_vs_ashes.connectors.response_logger import log_raster_extraction
from atoms_vs_ashes.db.models import (
    DataSource,
    Site,
    SiteEmergencyPlanning,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteObservation,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

if TYPE_CHECKING:
    from atoms_vs_ashes.connectors.copernicus_era5.client import CopernicusEra5Connector

log = get_logger(__name__)

_SOURCE_TYPE = "raster"
_CRITERION_NH10 = "NH-10"
_CRITERION_NH11 = "NH-11"
_CRITERION_NH12 = "NH-12"
_CRITERION_RI01 = "RI-01"
_CRITERION_NS01 = "NS-01"
_CRITERION_EP02 = "EP-02"


def enrich_site(
    connector: CopernicusEra5Connector,
    site_id: uuid.UUID,
    session: Session,
    run_id: str,
) -> SiteEnrichmentSummary:
    """Fetch and persist ERA5 climate data for a single DB site."""
    site = session.get(Site, site_id)
    if site is None:
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name="<unknown>",
            status="error",
            error=f"Site {site_id} not found in database",
        )

    t0 = time.monotonic()
    _ensure_data_sources(session)

    cached = _check_cache(session, site_id, run_id, connector._cache_ttl_days)
    if cached:
        elapsed = int((time.monotonic() - t0) * 1000)
        log.info("era5_cache_hit", site_id=str(site_id))
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="cached",
            quality=cached.nh10_quality,
            max_wind_ms=(
                float(cached.max_wind_speed_ms)
                if cached.max_wind_speed_ms is not None else None
            ),
            max_temp_c=(
                float(cached.extreme_temp_max_c)
                if cached.extreme_temp_max_c is not None else None
            ),
            elapsed_ms=elapsed,
        )

    try:
        result = connector.extract_all(float(site.latitude), float(site.longitude))
        _persist_result(session, site_id, result, run_id)
        _log_era5_raw(session, connector, site_id, run_id, site, result)
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)

        log.info(
            "era5_site_complete",
            site_id=str(site_id),
            site_name=site.name,
            quality=result.quality,
            max_temp_c=round(result.temperature.max_temp_record_c, 1),
            max_wind_ms=(
                round(result.wind.wind_gust_50yr_ms, 1)
                if result.wind.wind_gust_50yr_ms else None
            ),
            grid_distance_km=round(result.grid_distance_km, 2),
            elapsed_ms=elapsed,
        )

        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="ok",
            quality=result.quality,
            max_wind_ms=result.wind.wind_gust_50yr_ms,
            max_temp_c=result.temperature.max_temp_record_c,
            grid_distance_km=result.grid_distance_km,
            elapsed_ms=elapsed,
        )

    except Exception as exc:
        session.rollback()
        _persist_error_observation(session, site_id, run_id, str(exc))
        try:
            _log_era5_raw(
                session, connector, site_id, run_id, site,
                None, error=str(exc),
            )
        except Exception as log_exc:
            log.warning("era5_raw_log_after_error_failed", error=str(log_exc))
        session.commit()
        elapsed = int((time.monotonic() - t0) * 1000)
        log.error("era5_site_error", site_id=str(site_id), error=str(exc))
        return SiteEnrichmentSummary(
            site_id=site_id,
            site_name=site.name,
            status="error",
            error=str(exc),
            elapsed_ms=elapsed,
        )


def enrich_batch(
    connector: CopernicusEra5Connector,
    session: Session,
    run_id: str,
    *,
    site_ids: list[uuid.UUID] | None = None,
    country_codes: list[str] | None = None,
) -> BatchResult:
    """Enrich multiple sites with per-site commit isolation and progress logging."""
    batch = BatchResult(run_id=run_id)
    batch_start = time.monotonic()

    query = session.query(Site)
    if site_ids is not None:
        if not site_ids:
            return batch
        query = query.filter(Site.site_id.in_(site_ids))
    elif country_codes is not None:
        query = query.filter(Site.country_code.in_(country_codes))

    sites = query.order_by(Site.country_code, Site.name).all()
    batch.total_sites = len(sites)

    if not sites:
        return batch

    _ensure_data_sources(session)

    log.info(
        "era5_batch_start",
        run_id=run_id,
        total_sites=len(sites),
    )

    # Open datasets once for the full batch (Tier 2 design — LL-011)
    connector._ensure_datasets_open()

    for i, site in enumerate(sites):
        site_start = time.monotonic()

        cached = _check_cache(session, site.site_id, run_id, connector._cache_ttl_days)
        if cached:
            log.info("era5_cache_hit", site_id=str(site.site_id))
            batch.skipped_cached += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="cached",
                quality=cached.nh10_quality,
                max_wind_ms=(
                    float(cached.max_wind_speed_ms)
                    if cached.max_wind_speed_ms is not None else None
                ),
                max_temp_c=(
                    float(cached.extreme_temp_max_c)
                    if cached.extreme_temp_max_c is not None else None
                ),
                elapsed_ms=elapsed_ms,
            ))
            continue

        try:
            result = connector.extract_all(float(site.latitude), float(site.longitude))
            _persist_result(session, site.site_id, result, run_id)
            _log_era5_raw(session, connector, site.site_id, run_id, site, result)
            session.commit()
            batch.succeeded += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)

            log.info(
                "era5_batch_site_done",
                site_id=str(site.site_id),
                site_name=site.name,
                index=i + 1,
                total=len(sites),
                quality=result.quality,
                elapsed_ms=elapsed_ms,
            )
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="ok",
                quality=result.quality,
                max_wind_ms=result.wind.wind_gust_50yr_ms,
                max_temp_c=result.temperature.max_temp_record_c,
                grid_distance_km=result.grid_distance_km,
                elapsed_ms=elapsed_ms,
            ))

        except Exception as exc:
            session.rollback()
            log.error("era5_site_error", site_id=str(site.site_id), error=str(exc))
            _persist_error_observation(session, site.site_id, run_id, str(exc))
            try:
                _log_era5_raw(
                    session, connector, site.site_id, run_id, site,
                    None, error=str(exc),
                )
            except Exception as log_exc:
                log.warning("era5_raw_log_after_error_failed", error=str(log_exc))
            session.commit()
            batch.failed += 1
            elapsed_ms = int((time.monotonic() - site_start) * 1000)
            batch.per_site.append(SiteEnrichmentSummary(
                site_id=site.site_id,
                site_name=site.name,
                status="error",
                error=str(exc),
                elapsed_ms=elapsed_ms,
            ))

        if (i + 1) % 25 == 0:
            log.info(
                "era5_batch_progress",
                completed=i + 1,
                total=len(sites),
                succeeded=batch.succeeded,
                failed=batch.failed,
                elapsed_s=round(time.monotonic() - batch_start, 1),
            )

    batch.elapsed_s = time.monotonic() - batch_start
    log.info(
        "era5_batch_done",
        run_id=run_id,
        total=batch.total_sites,
        succeeded=batch.succeeded,
        failed=batch.failed,
        cached=batch.skipped_cached,
        elapsed_s=round(batch.elapsed_s, 1),
    )
    return batch


# ---------------------------------------------------------------------------
# Cache check
# ---------------------------------------------------------------------------

def _check_cache(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    ttl_days: int,
) -> SiteNaturalHazards | None:
    """Return cached SiteNaturalHazards row if fresh for this run."""
    row = session.get(SiteNaturalHazards, site_id)
    if row and row.fetched_at and row.run_id == run_id:
        age = datetime.now(timezone.utc) - row.fetched_at
        if age < timedelta(days=ttl_days):
            if row.nh10_quality is not None or row.nh12_quality is not None:
                return row
    return None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _persist_result(
    session: Session,
    site_id: uuid.UUID,
    result: Era5ClimateResult,
    run_id: str,
) -> None:
    """Write ERA5 climate data to all relevant domain tables."""
    now = datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # SiteNaturalHazards — NH-10, NH-11, NH-12
    # -----------------------------------------------------------------------
    nh_row = session.get(SiteNaturalHazards, site_id)
    if nh_row is None:
        nh_row = SiteNaturalHazards(site_id=site_id)
        session.add(nh_row)

    # NH-10: Extreme winds
    wind = result.wind
    nh_row.max_wind_speed_ms = wind.wind_gust_50yr_ms or wind.max_wind_gust_ms
    nh_row.nh10_quality = result.quality
    nh10_parts = [
        f"ERA5 wind assessment (ref {result.reference_period})",
        f"50yr_gust={wind.wind_gust_50yr_ms:.1f}m/s" if wind.wind_gust_50yr_ms else "",
        f"max_gust={wind.max_wind_gust_ms:.1f}m/s" if wind.max_wind_gust_ms else "",
        f"99p={wind.wind_speed_99p_ms:.1f}m/s",
        f"prevailing={wind.prevailing_direction_deg:.0f}deg",
        f"tropical_idx={wind.tropical_storm_exposure_index:.1f}",
        f"gev={wind.gev_fit_quality}",
        f"grid_dist={result.grid_distance_km:.1f}km",
        f"source={CONNECTOR_SLUG}",
    ]
    nh_row.nh10_comment = " | ".join(p for p in nh10_parts if p)[:2000]

    # NH-11: Precipitation extremes, snow, drought
    precip = result.precipitation
    nh_row.extreme_precip_mm = precip.max_daily_precip_mm
    if precip.mean_annual_precip_mm is not None:
        nh_row.mean_annual_precip_mm = precip.mean_annual_precip_mm
    nh_row.nh11_quality = result.quality
    nh11_parts = [
        f"ERA5 precipitation (ref {result.reference_period})",
        f"annual={precip.mean_annual_precip_mm:.0f}mm",
        f"max_daily={precip.max_daily_precip_mm:.1f}mm" if precip.max_daily_precip_mm else "",
        f"snow_days={precip.annual_snow_days:.0f}/yr",
        f"snow_months={precip.snow_months}",
        f"SPI12_min={precip.spi_12_min:.2f}" if precip.spi_12_min is not None else "",
        f"DSI={precip.drought_severity_index:.3f}" if precip.drought_severity_index is not None else "",
        f"freezing_days={precip.freezing_rain_days_proxy:.1f}/yr",
        f"source={CONNECTOR_SLUG}",
    ]
    nh_row.nh11_comment = " | ".join(p for p in nh11_parts if p)[:2000]

    # NH-12: Temperature extremes and projections
    temp = result.temperature
    nh_row.extreme_temp_max_c = temp.max_temp_record_c
    nh_row.extreme_temp_min_c = temp.min_temp_record_c
    nh_row.nh12_quality = result.quality
    nh12_parts = [
        f"ERA5 temperature (ref {result.reference_period})",
        f"max={temp.max_temp_record_c:.1f}C",
        f"min={temp.min_temp_record_c:.1f}C",
        f"range={temp.temp_range_c:.1f}C",
        f"hot_days={temp.hot_days_above_35c:.0f}/yr",
        f"cold_days={temp.cold_days_below_minus20c:.0f}/yr",
        f"summer_mean={temp.mean_summer_temp_c:.1f}C",
        f"source={CONNECTOR_SLUG}",
    ]
    if result.climate_projections:
        proj = result.climate_projections
        if proj.warming_2050_ssp245_c is not None:
            nh12_parts.append(f"CMIP6_2050_ssp245=+{proj.warming_2050_ssp245_c:.1f}C")
        if proj.warming_2080_ssp585_c is not None:
            nh12_parts.append(f"CMIP6_2080_ssp585=+{proj.warming_2080_ssp585_c:.1f}C")
    nh_row.nh12_comment = " | ".join(p for p in nh12_parts if p)[:2000]

    nh_row.fetched_at = now
    nh_row.run_id = run_id

    # -----------------------------------------------------------------------
    # SiteRadiological — RI-01 (atmospheric dispersion)
    # -----------------------------------------------------------------------
    ri_row = session.get(SiteRadiological, site_id)
    if ri_row is None:
        ri_row = SiteRadiological(site_id=site_id)
        session.add(ri_row)

    stab = result.stability
    ri_row.prevailing_wind_dir = _deg_to_cardinal(wind.prevailing_direction_deg)
    ri_row.avg_wind_speed_ms = wind.mean_wind_speed_ms
    ri_row.mixing_height_m = stab.mean_mixing_height_m
    ri_row.ri01_quality = result.quality

    ri01_parts = [
        f"ERA5 atmospheric dispersion (ref {result.reference_period})",
        f"prevailing_wind={_deg_to_cardinal(wind.prevailing_direction_deg)}"
        f"({wind.prevailing_direction_deg:.0f}deg)",
        f"mean_speed={wind.mean_wind_speed_ms:.1f}m/s",
        f"mean_BLH={stab.mean_mixing_height_m:.0f}m",
        f"p5_BLH={stab.percentile_5_mixing_height_m:.0f}m",
        f"stable_frac={stab.stable_fraction:.3f}",
        _format_stability_classes(stab.stability_class_freq),
        f"wind_rose_dominant={_dominant_sector(wind.wind_rose_16sector)}",
        f"source={CONNECTOR_SLUG}",
    ]
    ri_row.ri01_comment = " | ".join(p for p in ri01_parts if p)[:2000]

    ri_row.fetched_at = now
    ri_row.run_id = run_id

    # -----------------------------------------------------------------------
    # SiteInfrastructureV2 — NS-01 (seasonality proxy)
    # Per LL-009: use append semantics; do not overwrite cooling water data
    # -----------------------------------------------------------------------
    ns_row = session.get(SiteInfrastructureV2, site_id)
    if ns_row is None:
        ns_row = SiteInfrastructureV2(site_id=site_id)
        session.add(ns_row)

    ns01_parts = [
        f"ERA5 seasonality proxy (ref {result.reference_period})",
        f"precip_cv={precip.precip_seasonality_index:.3f}",
        f"temp_cv={temp.temp_seasonality_index:.3f}",
        f"source={CONNECTOR_SLUG}",
    ]
    era5_ns01 = " | ".join(ns01_parts)

    if ns_row.ns01_comment:
        # Append rather than overwrite (LL-009)
        if CONNECTOR_SLUG not in ns_row.ns01_comment:
            ns_row.ns01_comment = (ns_row.ns01_comment + "; " + era5_ns01)[:2000]
    else:
        ns_row.ns01_comment = era5_ns01[:2000]

    if not ns_row.ns01_quality:
        ns_row.ns01_quality = result.quality

    # -----------------------------------------------------------------------
    # SiteEmergencyPlanning — EP-02 (seasonal constraints proxy)
    # -----------------------------------------------------------------------
    ep_row = session.get(SiteEmergencyPlanning, site_id)
    if ep_row is None:
        ep_row = SiteEmergencyPlanning(site_id=site_id)
        session.add(ep_row)

    ep02_parts = [
        f"ERA5 seasonal constraints proxy (ref {result.reference_period})",
        f"snow_months={precip.snow_months}",
        f"extreme_precip_months={precip.extreme_precip_months}",
        f"max_snowfall={precip.max_daily_snowfall_mm:.1f}mm/day"
        if precip.max_daily_snowfall_mm else "",
        f"source={CONNECTOR_SLUG}",
    ]
    ep_row.ep02_comment = " | ".join(p for p in ep02_parts if p)[:2000]
    ep_row.ep02_quality = result.quality

    ep_row.fetched_at = now
    ep_row.run_id = run_id

    # -----------------------------------------------------------------------
    # SiteObservation — full JSON payload for downstream consumers
    # -----------------------------------------------------------------------
    full_json = json.dumps(result.to_dict(), default=str)
    session.add(SiteObservation(
        site_id=site_id,
        criterion_id=_CRITERION_NH10,
        source_type=_SOURCE_TYPE,
        observation_class="data_json",
        observation=full_json,
        confidence=result.quality,
        run_id=run_id,
    ))

    # Quality-flag observation
    if result.quality_notes:
        session.add(SiteObservation(
            site_id=site_id,
            criterion_id=_CRITERION_NH10,
            source_type=_SOURCE_TYPE,
            observation_class="quality_flag",
            observation=(
                f"ERA5 data quality: {result.quality}. "
                + " | ".join(result.quality_notes)
            ),
            impact="neutral",
            confidence="high",
            run_id=run_id,
        ))

    # RI-01 observation (wind rose summary)
    wind_rose_json = json.dumps(wind.wind_rose_16sector, default=str)
    session.add(SiteObservation(
        site_id=site_id,
        criterion_id=_CRITERION_RI01,
        source_type=_SOURCE_TYPE,
        observation_class="data_json",
        observation=json.dumps({
            "wind_rose": wind.wind_rose_16sector,
            "stability_classes": stab.stability_class_freq,
            "mixing_height": {
                "mean_m": stab.mean_mixing_height_m,
                "p5_m": stab.percentile_5_mixing_height_m,
            },
        }, default=str),
        confidence=result.quality,
        run_id=run_id,
    ))


def _persist_error_observation(
    session: Session,
    site_id: uuid.UUID,
    run_id: str,
    error: str,
) -> None:
    """Write an error observation for a failed ERA5 enrichment."""
    session.add(SiteObservation(
        site_id=site_id,
        criterion_id=_CRITERION_NH10,
        source_type=_SOURCE_TYPE,
        observation=f"ERA5 enrichment failed: {error}",
        impact="blocking",
        confidence="low",
        run_id=run_id,
    ))


# ---------------------------------------------------------------------------
# DataSource provenance
# ---------------------------------------------------------------------------

def _ensure_data_sources(session: Session) -> None:
    """Get or create DataSource records for ERA5."""
    for name, desc in [
        (
            SOURCE_ERA5,
            "ERA5 reanalysis — ECMWF Copernicus Climate Data Store. "
            "Global atmospheric reanalysis at 0.25° (~31 km) resolution, "
            "hourly 1940–present. Variables: wind, temperature, precipitation, "
            "boundary layer height. Reference period 1991-2020 monthly means.",
        ),
    ]:
        existing = session.query(DataSource).filter_by(name=name).first()
        if existing is None:
            session.add(DataSource(
                name=name,
                url=SOURCE_URL,
                description=desc,
                last_fetched=datetime.now(timezone.utc),
            ))
            session.flush()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_CARDINALS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def _deg_to_cardinal(deg: float) -> str:
    """Convert wind direction degrees to 16-sector cardinal label."""
    idx = round(deg / 22.5) % 16
    return _CARDINALS[idx]


def _dominant_sector(wind_rose: dict[str, float]) -> str:
    """Return the sector with the highest frequency."""
    if not wind_rose:
        return "N"
    return max(wind_rose, key=lambda k: wind_rose[k])


def _format_stability_classes(class_freq: dict[str, float]) -> str:
    """Format stability class frequencies as compact string."""
    parts = [f"{k}={v * 100:.1f}%" for k, v in sorted(class_freq.items())]
    return "stability=[" + " ".join(parts) + "]"


# ---------------------------------------------------------------------------
# Raw response logging (per-site raster extraction)
# ---------------------------------------------------------------------------

def _log_era5_raw(
    session: Session,
    connector: CopernicusEra5Connector,
    site_id: uuid.UUID,
    run_id: str,
    site: Site,
    result: Era5ClimateResult | None,
    *,
    error: str | None = None,
) -> None:
    """Persist a per-site ERA5 raster extraction record.

    ERA5 is consumed locally as cached NetCDF files (Tier 2 design) — there
    is no per-site network call, but the connector samples values from the
    nearest 0.25° grid cell for each site.  We log the source NetCDF paths
    plus the extracted scalar values so downstream auditors can re-derive
    the assessment without re-running the connector.
    """
    monthly = getattr(connector, "monthly_means_path", None)
    land = getattr(connector, "era5_land_path", None)
    cmip6 = getattr(connector, "cmip6_path", None)

    extracted: dict[str, Any] = {}
    if result is not None:
        wind = result.wind
        temp = result.temperature
        precip = result.precipitation
        extracted = {
            "site_lat": float(site.latitude),
            "site_lon": float(site.longitude),
            "grid_distance_km": result.grid_distance_km,
            "reference_period": result.reference_period,
            "quality": result.quality,
            "wind": {
                "wind_gust_50yr_ms": wind.wind_gust_50yr_ms,
                "max_wind_gust_ms": wind.max_wind_gust_ms,
                "mean_wind_speed_ms": wind.mean_wind_speed_ms,
                "wind_speed_99p_ms": wind.wind_speed_99p_ms,
                "prevailing_direction_deg": wind.prevailing_direction_deg,
                "tropical_storm_exposure_index": wind.tropical_storm_exposure_index,
                "gev_fit_quality": wind.gev_fit_quality,
            },
            "temperature": {
                "max_temp_record_c": temp.max_temp_record_c,
                "min_temp_record_c": temp.min_temp_record_c,
                "mean_summer_temp_c": temp.mean_summer_temp_c,
                "hot_days_above_35c": temp.hot_days_above_35c,
                "cold_days_below_minus20c": temp.cold_days_below_minus20c,
            },
            "precipitation": {
                "mean_annual_precip_mm": precip.mean_annual_precip_mm,
                "max_daily_precip_mm": precip.max_daily_precip_mm,
                "annual_snow_days": precip.annual_snow_days,
                "spi_12_min": precip.spi_12_min,
                "drought_severity_index": precip.drought_severity_index,
            },
        }
        if result.climate_projections:
            extracted["climate_projections"] = {
                "warming_2050_ssp245_c": result.climate_projections.warming_2050_ssp245_c,
                "warming_2080_ssp585_c": result.climate_projections.warming_2080_ssp585_c,
            }
    if error is not None:
        extracted["error"] = error

    source_url = "|".join(
        str(p) for p in (monthly, land, cmip6) if p is not None
    ) or SOURCE_URL

    log_raster_extraction(
        session,
        site_id=site_id,
        connector_slug=CONNECTOR_SLUG,
        run_id=run_id,
        source_url=source_url,
        extracted_values=extracted,
        crs="EPSG:4326",
        resolution_m=27_750.0,
    )
