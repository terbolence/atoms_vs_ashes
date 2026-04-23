# man_hours: 4.0
"""Google Earth Engine connector — ``earthengine-api`` only in this module."""

from __future__ import annotations

import os
import random
import time
from datetime import datetime, timezone
from typing import Any

from atoms_vs_ashes.connectors.earth_engine.models import (
    SOURCE_NAME,
    EarthEngineResult,
    GeeBuiltUpResult,
    GeeFireResult,
    GeeTerrainResult,
)
from atoms_vs_ashes.connectors.earth_engine import parsers
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

GEE_DISABLED_MSG = (
    "Google Earth Engine is disabled (connectors.earth_engine.enabled: false). "
    "Terrain and related criteria use Copernicus DEM and other non-GEE sources. "
    "To opt in after Google approval: set enabled: true, install pip extra "
    "'[earth-engine]', and configure service account credentials."
)


def _cfg(settings: Any | None) -> dict[str, Any]:
    if settings and hasattr(settings, "_yaml"):
        return settings._yaml.get("connectors", {}).get("earth_engine", {})
    return {}


class EarthEngineConnector:
    """S-06: server-side reductions on GEE for NH-04, NH-13, NS-04, NS-06, EP-03."""

    def __init__(self, settings: Any | None = None, *, mode_override: str | None = None) -> None:
        cfg = _cfg(settings)
        self._enabled: bool = bool(cfg.get("enabled", False))
        self._project_id: str | None = (
            cfg.get("project_id")
            or os.environ.get("GEE_PROJECT_ID")
        )
        key = cfg.get("service_account_key") or os.environ.get("GEE_SERVICE_ACCOUNT_KEY")
        self._service_account_key: str | None = key
        self._service_account_email: str | None = (
            cfg.get("service_account_email") or os.environ.get("GEE_SERVICE_ACCOUNT_EMAIL")
        )
        self._high_volume: bool = bool(cfg.get("high_volume_endpoint", True))
        self._timeout_s: int = int(cfg.get("timeout_s", 120))
        self._mode: str = str(mode_override or cfg.get("mode", "fallback"))
        self._dem_asset: str = str(cfg.get("dem_asset", "COPERNICUS/DEM/GLO30"))
        self._dem_band: str = str(cfg.get("dem_band", "DEM"))
        self._mods = cfg.get("modules") or {}
        self._terrain_cfg = self._mods.get("terrain") or {}
        self._fire_cfg = self._mods.get("fire") or {}
        self._built_cfg = self._mods.get("built_up") or {}
        self._ee_initialized = False

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def enabled(self) -> bool:
        """True only when YAML ``connectors.earth_engine.enabled`` is true."""
        return self._enabled

    def _init_ee(self) -> None:
        if not self._enabled:
            raise RuntimeError(GEE_DISABLED_MSG)
        if self._ee_initialized:
            return
        try:
            import ee
        except ImportError as exc:
            raise RuntimeError(
                "earthengine-api is not installed. Install with: "
                "pip install 'atoms-vs-ashes[earth-engine]'",
            ) from exc

        if not self._project_id:
            raise RuntimeError(
                "Earth Engine project_id missing — set connectors.earth_engine.project_id "
                "or GEE_PROJECT_ID.",
            )
        if not self._service_account_key:
            raise RuntimeError(
                "Service account key path missing — set connectors.earth_engine.service_account_key "
                "or GEE_SERVICE_ACCOUNT_KEY.",
            )
        if not self._service_account_email:
            raise RuntimeError(
                "Service account email missing — set connectors.earth_engine.service_account_email "
                "or GEE_SERVICE_ACCOUNT_EMAIL (client_email in the JSON key).",
            )

        credentials = ee.ServiceAccountCredentials(
            self._service_account_email,
            self._service_account_key,
        )
        opt_url = None
        if self._high_volume:
            opt_url = "https://earthengine-highvolume.googleapis.com"
        ee.Initialize(credentials, project=self._project_id, opt_url=opt_url)
        self._ee_initialized = True
        log.info("gee_init_ok", project=self._project_id, high_volume=self._high_volume)

    def _retry_get_info(self, ee_obj: Any) -> Any:
        import ee
        from ee import EEException

        delays = [2.0, 8.0, 24.0]
        last_exc: Exception | None = None
        for attempt, base in enumerate(delays):
            try:
                return ee_obj.getInfo()
            except EEException as exc:
                last_exc = exc
                msg = str(exc).lower()
                if "quota" in msg or "eecu" in msg:
                    log.warning("gee_quota_exceeded", attempt=attempt, error=str(exc))
                    time.sleep(60)
                    continue
                if attempt < len(delays) - 1:
                    jitter = 0.5 + random.random() * 0.5
                    time.sleep(base * jitter)
            except Exception as exc:
                last_exc = exc
                if attempt < len(delays) - 1:
                    time.sleep(base)
        if last_exc:
            raise last_exc
        raise RuntimeError("getInfo failed without exception")

    def health_check(self) -> bool:
        if not self._enabled:
            log.info("gee_disabled_config")
            return False
        try:
            self._init_ee()
            import ee

            return self._retry_get_info(ee.Number(1)) == 1
        except Exception as exc:
            log.error("gee_init_error", error=str(exc))
            return False

    def fetch_terrain(self, lat: float, lon: float) -> GeeTerrainResult:
        self._init_ee()
        import ee

        point = ee.Geometry.Point([float(lon), float(lat)])
        radius = float(self._terrain_cfg.get("radius_m", 2000))
        epz_r = float(self._terrain_cfg.get("epz_radius_m", 16000))
        aoi = point.buffer(radius)
        epz_aoi = point.buffer(epz_r)

        dem = ee.Image(self._dem_asset).select(self._dem_band)
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)
        comb = (
            ee.Reducer.mean()
            .combine(ee.Reducer.max(), sharedInputs=True)
            .combine(ee.Reducer.percentile([95]), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
        )
        slope_raw = self._retry_get_info(
            slope.reduceRegion(
                reducer=comb,
                geometry=aoi,
                scale=30,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        aspect_raw = self._retry_get_info(
            aspect.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=30,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        if isinstance(slope_raw, dict) and isinstance(aspect_raw, dict):
            amean = aspect_raw.get("aspect") or aspect_raw.get("mean")
            if amean is not None:
                slope_raw["aspect_mean"] = amean
        elev_raw = self._retry_get_info(
            dem.reduceRegion(
                reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True),
                geometry=aoi,
                scale=30,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        epz_raw = self._retry_get_info(
            dem.reduceRegion(
                reducer=ee.Reducer.minMax(),
                geometry=epz_aoi,
                scale=30,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        relief_16 = None
        if isinstance(epz_raw, dict):
            emin16 = epz_raw.get("DEM_min")
            emax16 = epz_raw.get("DEM_max")
            if emin16 is not None and emax16 is not None:
                relief_16 = float(emax16) - float(emin16)

        sr = slope_raw if isinstance(slope_raw, dict) else {}
        er = elev_raw if isinstance(elev_raw, dict) else {}
        tr = parsers.parse_slope_elevation_dicts(
            sr,
            er,
            dem_dataset=self._dem_asset,
            aoi_radius_m=radius,
            relief_16km_m=relief_16,
        )
        return tr

    def fetch_fire_history(self, lat: float, lon: float) -> GeeFireResult:
        self._init_ee()
        import ee

        point = ee.Geometry.Point([float(lon), float(lat)])
        radius = float(self._fire_cfg.get("radius_m", 5000))
        aoi = point.buffer(radius)
        start = str(self._fire_cfg.get("start_date", "2000-11-01"))
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mcd64 = (
            ee.ImageCollection("MODIS/061/MCD64A1")
            .filterDate(start, end)
            .select("BurnDate")
        )
        burn_sum = mcd64.map(lambda im: im.gt(0)).sum()
        raw = self._retry_get_info(
            burn_sum.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
                geometry=aoi,
                scale=500,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        if not isinstance(raw, dict):
            raw = {}
        return parsers.parse_fire_dict(
            raw,
            aoi_radius_m=radius,
            analysis_period=f"{start} to {end}",
            burn_year_list=[],
        )

    def fetch_built_up(self, lat: float, lon: float) -> GeeBuiltUpResult:
        self._init_ee()
        import ee

        point = ee.Geometry.Point([float(lon), float(lat)])
        radius = float(self._built_cfg.get("radius_m", 500))
        months = int(self._built_cfg.get("lookback_months", 12))
        aoi = point.buffer(radius)
        end = ee.Date.utc()
        start = end.advance(-months, "month")
        dw = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterDate(start, end)
            .select("built")
        )
        mean_img = dw.mean()
        raw = self._retry_get_info(
            mean_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=10,
                maxPixels=10_000_000,
                bestEffort=True,
            ),
        )
        if not isinstance(raw, dict):
            raw = {}
        period = f"{months}m lookback to UTC now"
        return parsers.parse_built_dict(raw, aoi_radius_m=radius, analysis_period=period)

    def fetch_all(
        self,
        lat: float,
        lon: float,
        *,
        run_terrain: bool = True,
        run_fire: bool = True,
        run_built: bool = True,
    ) -> EarthEngineResult:
        res = EarthEngineResult(lat=lat, lon=lon, mode=self._mode)
        if not self._enabled:
            res.error = GEE_DISABLED_MSG
            log.info("gee_fetch_skipped_disabled", lat=lat, lon=lon)
            return res
        try:
            if run_terrain:
                res.terrain = self.fetch_terrain(lat, lon)
                res.modules_succeeded.append("terrain")
            if run_fire:
                res.fire = self.fetch_fire_history(lat, lon)
                res.modules_succeeded.append("fire")
            if run_built:
                res.built_up = self.fetch_built_up(lat, lon)
                res.modules_succeeded.append("built_up")
        except Exception as exc:
            res.error = str(exc)
            log.warning("gee_fetch_error", lat=lat, lon=lon, error=str(exc))
        return res

    def close(self) -> None:
        return

    def __enter__(self) -> EarthEngineConnector:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = ["EarthEngineConnector", "GEE_DISABLED_MSG", "SOURCE_NAME"]
