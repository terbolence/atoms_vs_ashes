# man_hours: 3.0
"""S-07 Smithsonian GVP (Global Volcanism Program) connector.

Downloads the full Holocene Volcanoes and Holocene Eruptions datasets from
the GVP GeoServer WFS, caches them locally as JSON, and performs in-memory
proximity queries for each candidate site.

Source CRS: EPSG:4326 (WGS84).
Criterion served: NH-07 (volcanic hazard proximity and characterisation).
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.smithsonian_gvp.models import (
    AVOIDANCE_RECENT_DISTANCE_KM,
    AVOIDANCE_RECENT_YEARS,
    AVOIDANCE_VEI4_DISTANCE_KM,
    DEFAULT_SEARCH_RADIUS_KM,
    ERUPTIONS_LAYER,
    EXCLUSION_DISTANCE_KM,
    EXTENDED_RADIUS_KM,
    MAX_NEARBY_VOLCANOES,
    SOURCE_NAME,
    VOLCANOES_LAYER,
    WFS_URL,
    EruptionRecord,
    SmithsonianGvpResult,
    VolcanoRecord,
)
from atoms_vs_ashes.connectors.smithsonian_gvp.parsers import (
    assemble_result,
    build_eruption_index,
    parse_eruptions_geojson,
    parse_volcanoes_geojson,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/gvp"
_TIMEOUT_S = 60
_RETRY_MAX = 3
_RETRY_BASE_S = 2.0
_RETRY_MAX_DELAY_S = 60.0


class SmithsonianGvpConnector:
    """Holocene volcano proximity and eruption hazard assessment from GVP VOTW.

    Downloads the full GVP Holocene Volcanoes and Eruptions datasets once
    per run via WFS, caches locally, and queries in-memory for each site.
    Only 2 HTTP requests per run (not per site).
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("smithsonian_gvp")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("smithsonian_gvp", {})

        self._wfs_url: str = cfg.get("wfs_url", WFS_URL)
        self._volcanoes_layer: str = cfg.get("volcanoes_layer", VOLCANOES_LAYER)
        self._eruptions_layer: str = cfg.get("eruptions_layer", ERUPTIONS_LAYER)
        self._timeout: int = cfg.get("timeout_s", _TIMEOUT_S)
        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._volcanoes_cache_file: str = cfg.get(
            "volcanoes_cache_file", "holocene_volcanoes.json",
        )
        self._eruptions_cache_file: str = cfg.get(
            "eruptions_cache_file", "holocene_eruptions.json",
        )
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 365)
        self._eruptions_cache_ttl_days: int = cfg.get("eruptions_cache_ttl_days", 180)
        self._search_radius_km: float = cfg.get("search_radius_km", DEFAULT_SEARCH_RADIUS_KM)
        self._extended_radius_km: float = cfg.get("extended_radius_km", EXTENDED_RADIUS_KM)
        self._max_nearby: int = cfg.get("max_nearby_volcanoes", MAX_NEARBY_VOLCANOES)
        self._exclusion_km: float = cfg.get("exclusion_distance_km", EXCLUSION_DISTANCE_KM)
        self._avoidance_vei4_km: float = cfg.get(
            "avoidance_vei4_distance_km", AVOIDANCE_VEI4_DISTANCE_KM,
        )
        self._avoidance_recent_km: float = cfg.get(
            "avoidance_recent_distance_km", AVOIDANCE_RECENT_DISTANCE_KM,
        )
        self._avoidance_recent_years: int = cfg.get(
            "avoidance_recent_years", AVOIDANCE_RECENT_YEARS,
        )

        self._client = httpx.Client(timeout=self._timeout)

        # Loaded data (lazily initialised)
        self._volcanoes: list[VolcanoRecord] | None = None
        self._eruption_index: dict[int, list[EruptionRecord]] | None = None
        self._database_version: str = ""
        self._using_stale_cache: bool = False

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _ensure_data_loaded(self) -> None:
        """Load volcano and eruption data, from cache or WFS."""
        if self._volcanoes is not None and self._eruption_index is not None:
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)

        volcanoes_path = self._cache_dir / self._volcanoes_cache_file
        eruptions_path = self._cache_dir / self._eruptions_cache_file

        self._volcanoes = self._load_volcanoes(volcanoes_path)
        eruptions = self._load_eruptions(eruptions_path)
        self._eruption_index = build_eruption_index(eruptions)

        log.info(
            "gvp_data_loaded",
            volcanoes=len(self._volcanoes),
            eruptions=len(eruptions),
            database_version=self._database_version,
            stale_cache=self._using_stale_cache,
        )

    def _load_volcanoes(self, cache_path: Path) -> list[VolcanoRecord]:
        """Load volcanoes from cache or fetch from WFS."""
        cached = self._read_cache(cache_path, self._cache_ttl_days)
        if cached is not None:
            volcanoes = parse_volcanoes_geojson(cached)
            self._database_version = _extract_version(cached)
            log.info("gvp_data_cached", entity="volcanoes", count=len(volcanoes))
            return volcanoes

        geojson = self._fetch_wfs_layer(self._volcanoes_layer, "volcanoes")
        if geojson is None:
            stale = self._read_cache(cache_path, ttl_days=None)
            if stale is not None:
                self._using_stale_cache = True
                volcanoes = parse_volcanoes_geojson(stale)
                self._database_version = _extract_version(stale)
                log.warning("gvp_stale_cache", entity="volcanoes", count=len(volcanoes))
                return volcanoes
            raise RuntimeError(
                "GVP WFS unreachable and no local cache available. "
                "Cannot load Holocene volcano data."
            )

        self._write_cache(cache_path, geojson)
        self._database_version = _extract_version(geojson)
        return parse_volcanoes_geojson(geojson)

    def _load_eruptions(self, cache_path: Path) -> list[EruptionRecord]:
        """Load eruptions from cache or fetch from WFS."""
        cached = self._read_cache(cache_path, self._eruptions_cache_ttl_days)
        if cached is not None:
            eruptions = parse_eruptions_geojson(cached)
            log.info("gvp_data_cached", entity="eruptions", count=len(eruptions))
            return eruptions

        geojson = self._fetch_wfs_layer(self._eruptions_layer, "eruptions")
        if geojson is None:
            stale = self._read_cache(cache_path, ttl_days=None)
            if stale is not None:
                self._using_stale_cache = True
                eruptions = parse_eruptions_geojson(stale)
                log.warning("gvp_stale_cache", entity="eruptions", count=len(eruptions))
                return eruptions
            raise RuntimeError(
                "GVP WFS unreachable and no local cache available. "
                "Cannot load Holocene eruption data."
            )

        self._write_cache(cache_path, geojson)
        return parse_eruptions_geojson(geojson)

    # ------------------------------------------------------------------
    # WFS HTTP
    # ------------------------------------------------------------------

    def _fetch_wfs_layer(
        self, layer_name: str, entity_label: str,
    ) -> dict[str, Any] | None:
        """Fetch a full WFS layer as GeoJSON with retry logic."""
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": layer_name,
            "outputFormat": "application/json",
        }

        for attempt in range(1, _RETRY_MAX + 1):
            try:
                t0 = time.monotonic()
                resp = self._client.get(self._wfs_url, params=params)
                elapsed_ms = int((time.monotonic() - t0) * 1000)

                resp.raise_for_status()
                data = resp.json()

                feature_count = len(data.get("features", []))
                log.info(
                    "gvp_wfs_ok",
                    layer=layer_name,
                    features=feature_count,
                    elapsed_ms=elapsed_ms,
                    attempt=attempt,
                )

                if feature_count == 0:
                    log.error(
                        "gvp_empty_response",
                        layer=layer_name,
                        entity=entity_label,
                    )
                    if attempt < _RETRY_MAX:
                        self._sleep_backoff(attempt)
                        continue
                    return None

                return data

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (401, 403):
                    log.error("gvp_auth_error", status=status, layer=layer_name)
                    raise
                log.warning(
                    "gvp_http_error",
                    status=status, layer=layer_name,
                    attempt=attempt,
                )
            except httpx.TimeoutException as exc:
                log.warning(
                    "gvp_timeout",
                    layer=layer_name, attempt=attempt,
                    error=str(exc),
                )
            except httpx.HTTPError as exc:
                log.warning(
                    "gvp_network_error",
                    layer=layer_name, attempt=attempt,
                    error=str(exc),
                )
            except json.JSONDecodeError as exc:
                log.warning(
                    "gvp_parse_error",
                    layer=layer_name, attempt=attempt,
                    error=str(exc),
                )

            if attempt < _RETRY_MAX:
                self._sleep_backoff(attempt)

        log.error("gvp_fetch_failed", layer=layer_name, attempts=_RETRY_MAX)
        return None

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        delay = min(_RETRY_BASE_S * (2 ** attempt), _RETRY_MAX_DELAY_S)
        delay *= 0.5 + random.random() * 0.5
        time.sleep(delay)

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _read_cache(
        self, path: Path, ttl_days: int | None,
    ) -> dict[str, Any] | None:
        """Read a cached GeoJSON file if it exists and is within TTL."""
        if not path.is_file():
            return None

        if ttl_days is not None:
            age_days = (time.time() - path.stat().st_mtime) / 86400
            if age_days > ttl_days:
                log.info(
                    "gvp_cache_expired",
                    path=str(path), age_days=round(age_days, 1),
                )
                return None

        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("gvp_cache_read_error", path=str(path), error=str(exc))
            return None

    @staticmethod
    def _write_cache(path: Path, data: dict[str, Any]) -> None:
        """Write GeoJSON data to a cache file atomically."""
        tmp = path.with_suffix(".json.tmp")
        try:
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(str(tmp), str(path))
            log.info("gvp_cache_written", path=str(path))
        except OSError as exc:
            log.warning("gvp_cache_write_error", path=str(path), error=str(exc))

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify GVP WFS is reachable and returns the expected layers."""
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetCapabilities",
        }
        try:
            resp = self._client.get(self._wfs_url, params=params)
            resp.raise_for_status()
            text = resp.text
            has_volcanoes = "Holocene_Volcanoes" in text
            has_eruptions = "Holocene_Eruptions" in text
            ok = has_volcanoes and has_eruptions
            log.info(
                "gvp_health_check",
                status=resp.status_code,
                has_volcanoes=has_volcanoes,
                has_eruptions=has_eruptions,
                ok=ok,
            )
            return ok
        except Exception as exc:
            log.warning("gvp_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Single-site fetch
    # ------------------------------------------------------------------

    def fetch(self, lat: float, lon: float) -> SmithsonianGvpResult:
        """Assess volcanic hazard for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        """
        try:
            self._ensure_data_loaded()
        except RuntimeError as exc:
            return SmithsonianGvpResult(
                lat=lat, lon=lon,
                error=str(exc), quality="insufficient",
            )

        assert self._volcanoes is not None
        assert self._eruption_index is not None

        return assemble_result(
            lat, lon,
            self._volcanoes,
            self._eruption_index,
            search_radius_km=self._search_radius_km,
            max_nearby=self._max_nearby,
            exclusion_km=self._exclusion_km,
            avoidance_vei4_km=self._avoidance_vei4_km,
            avoidance_recent_km=self._avoidance_recent_km,
            avoidance_recent_years=self._avoidance_recent_years,
            database_version=self._database_version,
            using_stale_cache=self._using_stale_cache,
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()
        self._volcanoes = None
        self._eruption_index = None

    def __enter__(self) -> SmithsonianGvpConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _extract_version(geojson: dict[str, Any]) -> str:
    """Try to extract database version from GeoJSON metadata."""
    total = geojson.get("totalFeatures") or geojson.get("numberMatched") or "?"
    return f"VOTW ({total} features)"
