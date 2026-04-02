# man_hours: 6.0
"""EFEHR REST API client and single-site fetch orchestration.

Handles HTTP communication, model discovery, retry logic, and the
``fetch_all`` orchestrator that assembles a complete SeismicHazardResult.
Batch enrichment and DB persistence live in ``batch.py``.
"""

from __future__ import annotations

import random
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.seismic_hazard.fallback import GemRasterFallback
from atoms_vs_ashes.connectors.seismic_hazard.models import SeismicHazardResult
from atoms_vs_ashes.connectors.seismic_hazard.parsers import (
    nearest_value,
    parse_map_csv,
    parse_nrml_curve,
    parse_nrml_spectra,
    validate_coordinates_in_scope,
    validate_curve_monotonicity,
    validate_pga,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class SeismicHazardConnector:
    """EFEHR/GEM seismic hazard data connector.

    Fetches PGA at multiple return periods, full hazard curves, and uniform
    hazard spectra from the EFEHR ESHM20 REST API with automatic GEM
    GeoTIFF fallback.  Batch enrichment is delegated to ``batch.py``.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings is not None:
            cfg = settings.connector_config("seismic_hazard")

        self._base_url: str = cfg.get(
            "efehr_base_url", "http://appsrvr.share-eu.org:8080/share"
        ).rstrip("/")
        self._model_name: str = cfg.get("efehr_model_name", "ESHM20")
        self._model_id: int | None = cfg.get("efehr_model_id")
        self._timeout: int = cfg.get("timeout_s", 30)
        self._inter_request_delay: float = cfg.get("inter_request_delay_s", 0.5)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 365)
        self._default_imt: str = cfg.get("default_imt", "PGA")
        self._default_soil: str = cfg.get("default_soil", "rock_vs30_800ms-1")

        self._return_periods: list[dict[str, Any]] = cfg.get("return_periods", [
            {"poe": 0.1, "label": "475yr"},
            {"poe": 0.02, "label": "2475yr"},
        ])
        self._spectral_periods: list[str] = cfg.get("spectral_periods", [
            "0.10s", "0.20s", "0.30s", "0.50s", "1.00s", "2.00s",
        ])

        retry_cfg: dict[str, Any] = {}
        if settings is not None:
            retry_cfg = settings.retry
        self._max_retries: int = retry_cfg.get("max_retries", 3)
        self._base_delay: float = retry_cfg.get("base_delay_s", 2)
        self._max_delay: float = retry_cfg.get("max_delay_s", 60)

        gem_dir = cfg.get("gem_raster_dir", "sources/seismic/gem_global")
        self._gem_fallback = GemRasterFallback(gem_dir)

        self._client = httpx.Client(timeout=self._timeout)
        self._model_id_cache: int | None = self._model_id

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()
        self._gem_fallback.close()

    def __enter__(self) -> SeismicHazardConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the EFEHR API is reachable."""
        try:
            resp = self._client.get(
                f"{self._base_url}/map", params={"lat": "47", "lon": "15"}
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    # ------------------------------------------------------------------
    # Model discovery
    # ------------------------------------------------------------------

    def discover_model(self, lat: float, lon: float) -> int | None:
        """Find the ESHM20 model ID via EFEHR model discovery endpoint.

        Caches the result in memory for subsequent calls.
        """
        if self._model_id_cache is not None:
            return self._model_id_cache

        resp = self._request_with_retry(
            f"{self._base_url}/map", params={"lat": str(lat), "lon": str(lon)}
        )
        if resp is None:
            return None

        try:
            root = ET.fromstring(resp.text)
            for model_elem in root.iter("model"):
                name = model_elem.get("name", "")
                if self._model_name.lower() in name.lower():
                    mid = int(model_elem.get("id", "0"))
                    self._model_id_cache = mid
                    log.info(
                        "seismic_model_discovered",
                        model_id=mid, model_name=name, lat=lat, lon=lon,
                    )
                    return mid
            models = list(root.iter("model"))
            if models:
                mid = int(models[0].get("id", "0"))
                name = models[0].get("name", "unknown")
                self._model_id_cache = mid
                log.info(
                    "seismic_model_discovered",
                    model_id=mid, model_name=name, lat=lat, lon=lon,
                    note="fallback_to_first_model",
                )
                return mid
        except (ET.ParseError, ValueError, AttributeError) as exc:
            log.warning("seismic_model_discovery_error", error=str(exc))

        return None

    # ------------------------------------------------------------------
    # Single-site fetch methods
    # ------------------------------------------------------------------

    def fetch_pga(
        self, lat: float, lon: float
    ) -> tuple[float | None, float | None, float]:
        """Fetch PGA at 475yr and 2475yr return periods.

        Returns (pga_475yr, pga_2475yr, grid_distance_km).
        """
        model_id = self._ensure_model(lat, lon)
        if model_id is None:
            return None, None, 0.0

        pga_475yr: float | None = None
        pga_2475yr: float | None = None
        dist_km = 0.0
        bbox_margin = 0.01

        for rp in self._return_periods:
            poe = rp["poe"]
            label = rp["label"]

            value, dist = self._fetch_map_value(
                lat, lon, model_id, self._default_imt, poe, bbox_margin
            )
            if value is None:
                value, dist = self._fetch_map_value(
                    lat, lon, model_id, self._default_imt, poe, bbox_margin * 2
                )

            if value is not None:
                dist_km = max(dist_km, dist)
                if label == "475yr":
                    pga_475yr = value
                elif label == "2475yr":
                    pga_2475yr = value

        return pga_475yr, pga_2475yr, dist_km

    def fetch_hazard_curve(
        self, lat: float, lon: float, imt: str = "PGA"
    ) -> Any:
        """Fetch a full hazard curve at a point."""
        model_id = self._ensure_model(lat, lon)
        if model_id is None:
            return None

        params = {
            "lat": str(lat), "lon": str(lon), "id": str(model_id),
            "imt": imt, "soilType": self._default_soil,
            "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
        }
        resp = self._request_with_retry(f"{self._base_url}/curve", params=params)
        if resp is None:
            return None

        curve = parse_nrml_curve(resp.text)
        if curve is None:
            log.warning("seismic_parse_error", endpoint="curve", lat=lat, lon=lon)
        return curve

    def fetch_uhs(
        self, lat: float, lon: float, poe: float = 0.1
    ) -> Any:
        """Fetch a uniform hazard spectrum at a point."""
        model_id = self._ensure_model(lat, lon)
        if model_id is None:
            return None

        params = {
            "lat": str(lat), "lon": str(lon), "modelid": str(model_id),
            "imt": "SA", "poe": str(poe), "timespanpoe": "50",
            "soilType": self._default_soil,
            "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
        }
        resp = self._request_with_retry(f"{self._base_url}/spectra", params=params)
        if resp is None:
            return None

        uhs = parse_nrml_spectra(resp.text)
        if uhs is None:
            log.warning("seismic_parse_error", endpoint="spectra", lat=lat, lon=lon)
        return uhs

    def fetch_all(self, lat: float, lon: float) -> SeismicHazardResult:
        """Orchestrate all three fetches for a single site.

        Falls back to GEM GeoTIFF if EFEHR is unreachable or returns no data.
        """
        result = SeismicHazardResult(lat=lat, lon=lon)

        if not validate_coordinates_in_scope(lat, lon):
            log.warning("seismic_out_of_scope", lat=lat, lon=lon)

        pga_475yr, pga_2475yr, dist_km = self.fetch_pga(lat, lon)
        result.pga_475yr = pga_475yr
        result.pga_2475yr = pga_2475yr
        result.grid_distance_km = dist_km
        result.model_id = self._model_id_cache
        result.model_name = self._model_name

        if result.pga_475yr is None:
            result = self._try_gem_fallback(result)

        if result.source == "efehr_eshm20":
            curve = self.fetch_hazard_curve(lat, lon, self._default_imt)
            result.hazard_curve = curve
            if curve and not validate_curve_monotonicity(curve):
                log.warning("seismic_curve_non_monotonic", lat=lat, lon=lon)
                result.quality = "low"

            uhs = self.fetch_uhs(lat, lon, poe=0.1)
            result.uhs = uhs
            if uhs:
                result.sa_values = {
                    f"{p:.2f}s": sa for p, sa in zip(uhs.periods, uhs.sa_values)
                }

        pga_quality, pga_detail = validate_pga(result.pga_475yr)
        if pga_quality != "high":
            result.quality = pga_quality
            if result.error is None:
                result.error = pga_detail

        if dist_km > 15.0 and result.quality == "high":
            result.quality = "low"
            result.error = (
                f"Nearest grid node is {dist_km:.1f} km from site "
                f"(threshold: 15 km)"
            )

        log.info(
            "seismic_fetch_ok", lat=lat, lon=lon,
            pga_475yr=result.pga_475yr, source=result.source, quality=result.quality,
        )
        return result

    # ------------------------------------------------------------------
    # Batch enrichment (delegated to batch module)
    # ------------------------------------------------------------------

    def enrich_site(self, site_id: Any, session: Any, run_id: str) -> Any:
        """Fetch and persist seismic hazard data for a single DB site."""
        from atoms_vs_ashes.connectors.seismic_hazard.batch import enrich_site
        return enrich_site(self, site_id, session, run_id)

    def enrich_batch(
        self, session: Any, run_id: str, **kwargs: Any
    ) -> Any:
        """Enrich multiple sites with seismic hazard data."""
        from atoms_vs_ashes.connectors.seismic_hazard.batch import enrich_batch
        return enrich_batch(self, session, run_id, **kwargs)

    def enrich_all(self, session: Any, run_id: str) -> Any:
        """Convenience: enrich every site in the database."""
        from atoms_vs_ashes.connectors.seismic_hazard.batch import enrich_batch
        return enrich_batch(self, session, run_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_model(self, lat: float, lon: float) -> int | None:
        if self._model_id_cache is not None:
            return self._model_id_cache
        return self.discover_model(lat, lon)

    def _fetch_map_value(
        self, lat: float, lon: float, model_id: int,
        imt: str, poe: float, margin: float,
    ) -> tuple[float | None, float]:
        params = {
            "id": str(model_id),
            "lon1": str(round(lon - margin, 6)),
            "lat1": str(round(lat - margin, 6)),
            "lon2": str(round(lon + margin, 6)),
            "lat2": str(round(lat + margin, 6)),
            "imt": imt, "hmapexceedprob": str(poe), "hmapexceedyears": "50",
            "soiltype": self._default_soil,
            "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
        }
        resp = self._request_with_retry(f"{self._base_url}/map", params=params)
        if resp is None:
            return None, 0.0

        grid = parse_map_csv(resp.text)
        if not grid:
            return None, 0.0

        try:
            value, dist = nearest_value(grid, lat, lon)
            return value, dist
        except ValueError:
            return None, 0.0

    def _try_gem_fallback(self, result: SeismicHazardResult) -> SeismicHazardResult:
        try:
            pga = self._gem_fallback.sample(result.lat, result.lon)
            if pga is not None:
                result.pga_475yr = pga
                result.source = "gem_global_v2023"
                result.model_name = "GEM Global v2023.1"
                result.quality = "medium"
                log.info(
                    "seismic_fallback_gem",
                    lat=result.lat, lon=result.lon, pga_475yr=pga,
                )
                return result
        except (FileNotFoundError, ImportError) as exc:
            log.warning(
                "gem_raster_unavailable",
                error=str(exc), lat=result.lat, lon=result.lon,
            )

        result.quality = "insufficient"
        result.error = "EFEHR returned no data and GEM raster fallback unavailable"
        log.error(
            "seismic_fetch_error",
            lat=result.lat, lon=result.lon, error=result.error,
        )
        return result

    def _request_with_retry(
        self, url: str, params: dict[str, str]
    ) -> httpx.Response | None:
        """HTTP GET with exponential backoff and jitter."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.get(url, params=params)
                if resp.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    delay = min(
                        self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                        self._max_delay,
                    )
                    log.warning(
                        "seismic_retry", url=url, status=resp.status_code,
                        attempt=attempt + 1, delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    log.warning("seismic_client_error", url=url, status=resp.status_code)
                    return None
                return resp
            except httpx.HTTPError as exc:
                last_exc = exc
                delay = min(
                    self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self._max_delay,
                )
                log.warning(
                    "seismic_retry", url=url, error=str(exc),
                    attempt=attempt + 1, delay_s=round(delay, 1),
                )
                time.sleep(delay)

        log.error(
            "seismic_fetch_error", url=url,
            error=str(last_exc), attempts=self._max_retries,
        )
        return None
