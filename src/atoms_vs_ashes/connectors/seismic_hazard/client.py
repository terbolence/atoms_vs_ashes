# man_hours: 8.0
"""EFEHR REST API client and single-site fetch orchestration.

Handles HTTP communication, model discovery, retry logic, and the
``fetch_all`` orchestrator that assembles a complete SeismicHazardResult.
Batch enrichment and DB persistence live in ``batch.py``.

API Validation (2026-04-13) revealed:
  - ESHM20 map endpoint returns empty data; ESHM13 map works.
  - ESHM20 curve works (NRML 0.3 format).
  - Spectra endpoint non-functional for both models.
  - Model discovery XML uses nested <id>/<name> elements.
  - No rate limits detected; avg response time ~2s per map request.
  - Grid resolution ~0.1° → bbox must be at least ±0.15°.
"""

from __future__ import annotations

import random
import time
import uuid
from typing import Any

import httpx

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.http_audit import ConnectorHttpAuditLogger
from atoms_vs_ashes.connectors.seismic_hazard.fallback import GemRasterFallback
from atoms_vs_ashes.connectors.seismic_hazard.models import (
    DEFAULT_BBOX_MARGIN,
    DEFAULT_ESHM13_MODEL_ID,
    SOURCE_EFEHR_CURVE,
    SOURCE_EFEHR_ESHM13,
    SOURCE_EFEHR_ESHM20,
    SOURCE_GEM_GLOBAL,
    SeismicHazardResult,
)
from atoms_vs_ashes.connectors.seismic_hazard.parsers import (
    interpolate_curve_at_poe,
    nearest_value,
    parse_map_csv,
    parse_model_discovery,
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
    hazard spectra from the EFEHR REST API with automatic model-level and
    GEM GeoTIFF fallback.

    API behaviour (validated 2026-04-13):
      Map: ESHM13 (model 68) → works.  ESHM20 (model 81) → empty.
      Curve: ESHM20 → works (NRML 0.3).  ESHM13 → error.
      Spectra: non-functional for both models.
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
        self._bbox_margin: float = cfg.get("bbox_margin", DEFAULT_BBOX_MARGIN)

        self._return_periods: list[dict[str, Any]] = cfg.get("return_periods", [
            {"poe": 0.1, "label": "475yr"},
            {"poe": 0.02, "label": "2475yr"},
        ])
        self._spectral_periods: list[str] = cfg.get("spectral_periods", [
            "0.10s", "0.20s", "0.30s", "0.50s", "1.00s", "2.00s",
        ])
        self._fetch_spectral_periods: bool = cfg.get(
            "fetch_spectral_periods", False,
        )

        retry_cfg: dict[str, Any] = {}
        if settings is not None:
            retry_cfg = settings.retry
        self._max_retries: int = retry_cfg.get("max_retries", 3)
        self._base_delay: float = retry_cfg.get("base_delay_s", 2)
        self._max_delay: float = retry_cfg.get("max_delay_s", 60)

        gem_dir = cfg.get("gem_raster_dir", "sources/seismic/gem_global")
        self._gem_fallback = GemRasterFallback(gem_dir)

        self._client = httpx.Client(timeout=self._timeout)

        # Model ID caches: ESHM20 for curves, ESHM13 for maps
        self._eshm20_id: int | None = self._model_id
        self._eshm13_id: int | None = None
        self._models_discovered: bool = False

        self._audit: ConnectorHttpAuditLogger | None = None

        # Per-site raw response accumulator consumed by batch.py for
        # log_raw_response().  Each entry: dict(url, params, http_status,
        # elapsed_ms, body_text, error).  See reset_raw_call_log() /
        # consume_raw_call_log().
        self._raw_call_log: list[dict[str, Any]] = []

    def enable_audit_log(self, run_id: str) -> None:
        """Enable file-based HTTP audit logging for this connector session."""
        self._audit = ConnectorHttpAuditLogger("seismic", run_id)
        log.info("seismic_audit_enabled", log_dir=str(self._audit.base_dir))

    # ------------------------------------------------------------------
    # Raw-response accumulator (consumed by batch.log_raw_response)
    # ------------------------------------------------------------------

    def reset_raw_call_log(self) -> None:
        """Clear the per-site raw-response accumulator before a new site."""
        self._raw_call_log = []

    def consume_raw_call_log(self) -> list[dict[str, Any]]:
        """Return the accumulated raw calls and clear the buffer."""
        out = self._raw_call_log
        self._raw_call_log = []
        return out

    def _record_call(
        self,
        url: str,
        params: dict[str, Any],
        *,
        http_status: int | None,
        elapsed_ms: int,
        body_text: str | None = None,
        error: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "url": url,
            "params": dict(params),
            "http_status": http_status,
            "elapsed_ms": elapsed_ms,
        }
        if body_text is not None:
            # Cap stored body to keep DB rows manageable; full body is on disk
            # via ConnectorHttpAuditLogger when enable_audit_log() is on.
            entry["body_text"] = body_text[:200_000]
        if error is not None:
            entry["error"] = error
        self._raw_call_log.append(entry)

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

    def discover_models(self, lat: float, lon: float) -> None:
        """Discover ESHM20 and ESHM13 model IDs via the EFEHR API.

        Caches results in memory for the lifetime of the connector.
        """
        if self._models_discovered:
            return

        resp = self._request_with_retry(
            f"{self._base_url}/map", params={"lat": str(lat), "lon": str(lon)}
        )
        if resp is None:
            return

        models = parse_model_discovery(resp.text)
        for mid, name in models:
            name_lower = name.lower()
            if "eshm20" in name_lower or "2020" in name_lower:
                self._eshm20_id = mid
                log.info(
                    "seismic_model_discovered",
                    model_id=mid, model_name=name, role="eshm20",
                )
            elif "eshm13" in name_lower or "2013" in name_lower:
                self._eshm13_id = mid
                log.info(
                    "seismic_model_discovered",
                    model_id=mid, model_name=name, role="eshm13",
                )

        if self._eshm13_id is None and self._eshm20_id is None and models:
            self._eshm13_id = models[0][0]
            log.info(
                "seismic_model_discovered",
                model_id=models[0][0], model_name=models[0][1],
                note="fallback_to_first_model",
            )

        self._models_discovered = True

    # Keep backward-compat alias used by tests
    def discover_model(self, lat: float, lon: float) -> int | None:
        """Discover model IDs and return the preferred map model."""
        self.discover_models(lat, lon)
        return self._eshm13_id or self._eshm20_id

    # ------------------------------------------------------------------
    # Single-site fetch methods
    # ------------------------------------------------------------------

    def fetch_pga(
        self, lat: float, lon: float
    ) -> tuple[float | None, float | None, float, str]:
        """Fetch PGA at 475yr and 2475yr return periods.

        Returns (pga_475yr, pga_2475yr, grid_distance_km, source_name).
        Tries ESHM20 first for maps, falls back to ESHM13.
        """
        self.discover_models(lat, lon)

        # ESHM20 map is non-functional (API validated 2026-04-13).
        # Try ESHM13 directly; if ESHM13 unavailable, try ESHM20 anyway.
        model_ids_to_try = []
        if self._eshm13_id is not None:
            model_ids_to_try.append((self._eshm13_id, SOURCE_EFEHR_ESHM13))
        if self._eshm20_id is not None:
            model_ids_to_try.append((self._eshm20_id, SOURCE_EFEHR_ESHM20))

        if not model_ids_to_try:
            return None, None, 0.0, ""

        for model_id, source_name in model_ids_to_try:
            pga_475yr, pga_2475yr, dist_km = self._fetch_pga_for_model(
                lat, lon, model_id
            )
            if pga_475yr is not None:
                return pga_475yr, pga_2475yr, dist_km, source_name

        return None, None, 0.0, ""

    def _fetch_pga_for_model(
        self, lat: float, lon: float, model_id: int,
    ) -> tuple[float | None, float | None, float]:
        pga_475yr: float | None = None
        pga_2475yr: float | None = None
        dist_km = 0.0

        for rp in self._return_periods:
            poe = rp["poe"]
            label = rp["label"]

            value, dist = self._fetch_map_value(
                lat, lon, model_id, self._default_imt, poe, self._bbox_margin
            )
            if value is None:
                value, dist = self._fetch_map_value(
                    lat, lon, model_id, self._default_imt, poe,
                    self._bbox_margin * 2,
                )

            if value is not None:
                dist_km = max(dist_km, dist)
                if label == "475yr":
                    pga_475yr = value
                elif label == "2475yr":
                    pga_2475yr = value

            time.sleep(self._inter_request_delay)

        return pga_475yr, pga_2475yr, dist_km

    def fetch_hazard_curve(
        self, lat: float, lon: float, imt: str = "PGA"
    ) -> Any:
        """Fetch a full hazard curve at a point.

        Prefers ESHM20 for curves (validated working 2026-04-13).
        """
        self.discover_models(lat, lon)

        model_ids_to_try = []
        if self._eshm20_id is not None:
            model_ids_to_try.append(self._eshm20_id)
        if self._eshm13_id is not None:
            model_ids_to_try.append(self._eshm13_id)

        for model_id in model_ids_to_try:
            params = {
                "lat": str(lat), "lon": str(lon), "id": str(model_id),
                "imt": imt, "soiltype": self._default_soil,
                "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
            }
            resp = self._request_with_retry(
                f"{self._base_url}/curve", params=params
            )
            if resp is None:
                continue

            if "<errors>" in resp.text or "<soiltypes>" in resp.text:
                log.info(
                    "seismic_curve_skip_model",
                    model_id=model_id, reason="error_or_discovery_response",
                )
                continue

            curve = parse_nrml_curve(resp.text)
            if curve is not None:
                return curve

            log.warning(
                "seismic_parse_error", endpoint="curve",
                model_id=model_id, lat=lat, lon=lon,
            )

        return None

    def fetch_uhs(
        self, lat: float, lon: float, poe: float = 0.1
    ) -> Any:
        """Fetch a uniform hazard spectrum at a point.

        Non-functional for both models as of 2026-04-13 API validation.
        Kept for forward-compatibility.
        """
        self.discover_models(lat, lon)

        model_ids_to_try = []
        if self._eshm20_id is not None:
            model_ids_to_try.append(self._eshm20_id)
        if self._eshm13_id is not None:
            model_ids_to_try.append(self._eshm13_id)

        for model_id in model_ids_to_try:
            params = {
                "lat": str(lat), "lon": str(lon), "modelid": str(model_id),
                "imt": "SA", "poe": str(poe), "timespanpoe": "50",
                "soilType": self._default_soil,
                "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
            }
            resp = self._request_with_retry(
                f"{self._base_url}/spectra", params=params
            )
            if resp is None:
                continue

            if "<errors>" in resp.text:
                continue

            uhs = parse_nrml_spectra(resp.text)
            if uhs is not None:
                return uhs

        return None

    def fetch_pga_from_curve(
        self, lat: float, lon: float,
    ) -> tuple[float | None, float | None]:
        """Extract PGA at 475yr and 2475yr from a hazard curve via log-log interpolation.

        Used as a fallback when the map endpoint returns empty for a site
        (e.g. Ukrainian sites outside the ESHM13 grid).
        The curve PoEs are expressed as investigation-time PoE (50 years):
          475yr  → 50-year PoE ≈ 0.1
          2475yr → 50-year PoE ≈ 0.02
        """
        curve = self.fetch_hazard_curve(lat, lon, imt="PGA")
        if curve is None:
            return None, None

        pga_475 = interpolate_curve_at_poe(curve, 0.1)
        pga_2475 = interpolate_curve_at_poe(curve, 0.02)
        return pga_475, pga_2475

    def fetch_sa_from_curves(
        self, lat: float, lon: float, poe: float = 0.1,
    ) -> dict[str, float]:
        """Fetch SA(T) values by querying /curve with imt=SA(period) for each spectral period.

        Workaround for the broken /spectra (UHS) endpoint: we query the
        /curve endpoint once per spectral period and interpolate the curve
        at the target PoE to extract SA(T).
        """
        sa_values: dict[str, float] = {}

        for period_str in self._spectral_periods:
            imt = f"SA[{period_str}]"

            time.sleep(self._inter_request_delay)
            curve = self.fetch_hazard_curve(lat, lon, imt=imt)
            if curve is None:
                log.warning(
                    "seismic_sa_curve_missing",
                    lat=lat, lon=lon, period=period_str,
                )
                continue

            sa_val = interpolate_curve_at_poe(curve, poe)
            if sa_val is not None:
                sa_values[period_str] = round(sa_val, 6)
            else:
                log.warning(
                    "seismic_sa_interpolation_failed",
                    lat=lat, lon=lon, period=period_str,
                )

        return sa_values

    def fetch_all(self, lat: float, lon: float) -> SeismicHazardResult:
        """Orchestrate all fetches for a single site.

        Falls back through ESHM13 → GEM GeoTIFF for PGA map values.
        Uses ESHM20 for hazard curves when available.
        """
        result = SeismicHazardResult(lat=lat, lon=lon)

        if not validate_coordinates_in_scope(lat, lon):
            log.warning("seismic_out_of_scope", lat=lat, lon=lon)

        pga_475yr, pga_2475yr, dist_km, source = self.fetch_pga(lat, lon)
        result.pga_475yr = pga_475yr
        result.pga_2475yr = pga_2475yr
        result.grid_distance_km = dist_km
        result.source = source or SOURCE_EFEHR_ESHM20

        if result.pga_475yr is None:
            time.sleep(self._inter_request_delay)
            curve_pga_475, curve_pga_2475 = self.fetch_pga_from_curve(lat, lon)
            if curve_pga_475 is not None:
                result.pga_475yr = curve_pga_475
                result.pga_2475yr = curve_pga_2475
                result.source = SOURCE_EFEHR_CURVE
                result.quality = "medium"
                log.info(
                    "seismic_fallback_curve_pga",
                    lat=lat, lon=lon,
                    pga_475yr=curve_pga_475, pga_2475yr=curve_pga_2475,
                )

        if result.pga_475yr is None:
            result = self._try_gem_fallback(result)

        if result.source == SOURCE_EFEHR_ESHM13:
            result.model_id = self._eshm13_id
            result.model_name = "ESHM13"
        elif result.source in (SOURCE_EFEHR_ESHM20, SOURCE_EFEHR_CURVE):
            result.model_id = self._eshm20_id
            result.model_name = "ESHM20"

        time.sleep(self._inter_request_delay)

        if result.source != SOURCE_EFEHR_CURVE:
            curve = self.fetch_hazard_curve(lat, lon, self._default_imt)
        else:
            curve = self.fetch_hazard_curve(lat, lon, self._default_imt)
        result.hazard_curve = curve
        if curve and not validate_curve_monotonicity(curve):
            log.warning("seismic_curve_non_monotonic", lat=lat, lon=lon)
            if result.quality == "high":
                result.quality = "low"

        time.sleep(self._inter_request_delay)

        uhs = self.fetch_uhs(lat, lon, poe=0.1)
        result.uhs = uhs
        if uhs:
            result.sa_values = {
                f"{p:.2f}s": sa for p, sa in zip(uhs.periods, uhs.sa_values)
            }

        if not result.sa_values and self._fetch_spectral_periods:
            sa_from_curves = self.fetch_sa_from_curves(lat, lon, poe=0.1)
            if sa_from_curves:
                result.sa_values = sa_from_curves
                log.info(
                    "seismic_sa_from_curves",
                    lat=lat, lon=lon, n_periods=len(sa_from_curves),
                )

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
            pga_475yr=result.pga_475yr, source=result.source,
            quality=result.quality,
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

        if "<errors>" in resp.text:
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
                result.source = SOURCE_GEM_GLOBAL
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
            t0 = time.monotonic()
            try:
                resp = self._client.get(url, params=params)
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                if self._audit:
                    self._audit.log(
                        url=url, params=params, response=resp,
                        attempt=attempt + 1, elapsed_ms=elapsed_ms,
                    )

                if resp.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    self._record_call(
                        url, params,
                        http_status=resp.status_code,
                        elapsed_ms=elapsed_ms,
                        error=f"HTTP {resp.status_code}",
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
                    log.warning(
                        "seismic_client_error", url=url,
                        status=resp.status_code,
                    )
                    self._record_call(
                        url, params,
                        http_status=resp.status_code,
                        elapsed_ms=elapsed_ms,
                        error=f"HTTP {resp.status_code}",
                    )
                    return None
                self._record_call(
                    url, params,
                    http_status=resp.status_code,
                    elapsed_ms=elapsed_ms,
                    body_text=resp.text,
                )
                return resp
            except httpx.RemoteProtocolError as exc:
                # LL-017: server disconnected mid-response — always retry
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                last_exc = exc

                if self._audit:
                    self._audit.log(
                        url=url, params=params, response=None,
                        error=f"LL-017 disconnect: {exc}",
                        attempt=attempt + 1, elapsed_ms=elapsed_ms,
                    )
                self._record_call(
                    url, params,
                    http_status=None,
                    elapsed_ms=elapsed_ms,
                    error=f"LL-017 disconnect: {exc}",
                )

                delay = min(
                    self._base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self._max_delay,
                )
                log.warning(
                    "seismic_retry_disconnect", url=url,
                    error=str(exc), attempt=attempt + 1,
                    delay_s=round(delay, 1),
                )
                time.sleep(delay)
            except httpx.HTTPError as exc:
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                last_exc = exc

                if self._audit:
                    self._audit.log(
                        url=url, params=params, response=None,
                        error=str(exc), attempt=attempt + 1,
                        elapsed_ms=elapsed_ms,
                    )
                self._record_call(
                    url, params,
                    http_status=None,
                    elapsed_ms=elapsed_ms,
                    error=str(exc),
                )

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
