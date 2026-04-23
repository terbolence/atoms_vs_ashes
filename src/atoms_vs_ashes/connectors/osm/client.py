# man_hours: 22.0
"""OpenStreetMap Overpass API connector.

Provides a general-purpose Overpass client for querying:
- Populated places and their populations
- Amenities (hospitals, prisons, care homes)
- Road network density
- Waterways and physical features
- Airports and heliports (HI-01)
- Military installations (HI-06)
- Communication transmitters (HI-07)
- Power infrastructure (NS-02)
- Land use polygons (NS-05)
- Site area estimation (FIX-03: BF-02, A15, NS-05a)
- Transport access: highway, railway, navigable waterway proximity (P11: NS-03, A14)
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.osm.models import (
    OsmElement,
    PlantBoundary,
    SiteAreaCandidate,
    SiteAreaResult,
)
from atoms_vs_ashes.geo import haversine_km
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_RAW_RESPONSE_DIR: Path | None = None


def enable_raw_response_logging(directory: str | Path) -> None:
    """Enable raw Overpass response caching to *directory* for audit purposes.

    Every successful (HTTP 200) response body is dumped as a JSON file with
    metadata.  Call once at startup — affects all OverpassClient instances.
    """
    global _RAW_RESPONSE_DIR
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    _RAW_RESPONSE_DIR = d
    log.info("osm_raw_logging_enabled", directory=str(d))

DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_TIMEOUT_S = 240

# LL-017 / LL-018: statuses that indicate a transient failure, not "no data".
_RETRYABLE_STATUSES: frozenset[int] = frozenset({406, 408, 429, 504, 0})
_MAX_RETRIES = 6
_BACKOFF_BASE_S = 45.0
_BACKOFF_CAP_S = 180.0


class OverpassClient:
    """Thin wrapper around the Overpass API."""

    def __init__(
        self,
        settings: Any | None = None,
        *,
        overpass_url: str | None = None,
        timeout_s: int | None = None,
        retry_on_error: bool = False,
    ) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("osm", {})

        self._url = overpass_url or cfg.get("overpass_url", DEFAULT_OVERPASS_URL)
        self._timeout = timeout_s or cfg.get("timeout_s", _TIMEOUT_S)
        self._delay = cfg.get("inter_request_delay_s", 1.0)
        self._retry_on_error = retry_on_error
        self._client = httpx.Client(
            timeout=self._timeout,
            headers={
                "Accept": "*/*",
                "User-Agent": "atoms_vs_ashes/1.0 (nuclear-siting-study; contact@project.eu)",
            },
        )
        self._last_http_status: int = 0
        # Per-site raw response accumulator consumed by batch.py for
        # log_raw_response().  Each entry is a dict with keys: query,
        # http_status, elapsed_ms, element_count, body.  See
        # reset_raw_call_log() / consume_raw_call_log().
        self._raw_call_log: list[dict[str, Any]] = []

    def health_check(self) -> bool:
        """Check Overpass API status endpoint."""
        try:
            resp = self._client.get(
                self._url.replace("/interpreter", "/status")
            )
            ok = resp.status_code == 200
            if ok:
                log.info("osm_health_ok")
            return ok
        except httpx.HTTPError as exc:
            log.warning("osm_health_error", error=str(exc))
            return False

    @property
    def was_rate_limited(self) -> bool:
        """True if the last query hit a retryable transient error (LL-017)."""
        return self._last_http_status in _RETRYABLE_STATUSES

    @property
    def was_error(self) -> bool:
        """True if the last query ended with any non-200 status."""
        return self._last_http_status != 200

    def query(self, overpass_ql: str) -> list[dict[str, Any]]:
        """Execute an Overpass QL query, return the ``elements`` list.

        When *retry_on_error* was passed to the constructor, transient failures
        (429, 504, 408, disconnect) are retried automatically with backoff
        and Overpass ``/status`` slot polling (LL-017 / LL-018).
        """
        if self._retry_on_error:
            return self._query_once_or_retry(overpass_ql)
        return self._query_raw(overpass_ql)

    def _query_raw(self, overpass_ql: str) -> list[dict[str, Any]]:
        """Low-level single-attempt query (no retry)."""
        self._last_http_status = 0
        t0 = time.monotonic()
        try:
            resp = self._client.post(
                self._url, data={"data": overpass_ql},
            )
            self._last_http_status = resp.status_code
            resp.raise_for_status()
            body = resp.json()
            elements = body.get("elements", [])
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            log.info("osm_query_ok", element_count=len(elements), elapsed_ms=elapsed_ms)
            self._dump_raw_response(overpass_ql, body, elapsed_ms)
            self._record_call(overpass_ql, body, elapsed_ms, status=resp.status_code)
            return elements
        except httpx.TimeoutException as exc:
            self._last_http_status = 408
            log.warning("osm_query_error", error=f"Timeout: {exc}")
            self._record_call(overpass_ql, None, int((time.monotonic() - t0) * 1000), status=408, error=str(exc))
            return []
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            self._last_http_status = status
            self._record_call(overpass_ql, None, int((time.monotonic() - t0) * 1000), status=status, error=str(exc))
            if status in (401, 403):
                log.error("osm_auth_error", status=status)
                raise
            log.warning("osm_query_error", error=str(exc), status=status)
            return []
        except httpx.HTTPError as exc:
            log.warning("osm_query_error", error=str(exc))
            self._record_call(overpass_ql, None, int((time.monotonic() - t0) * 1000), status=self._last_http_status, error=str(exc))
            return []
        except (ValueError, KeyError) as exc:
            log.warning("osm_parse_error", error=str(exc))
            self._record_call(overpass_ql, None, int((time.monotonic() - t0) * 1000), status=self._last_http_status, error=str(exc))
            return []

    # ------------------------------------------------------------------
    # Raw-response accumulator (consumed by batch.log_raw_response)
    # ------------------------------------------------------------------

    def _record_call(
        self,
        query: str,
        body: dict[str, Any] | None,
        elapsed_ms: int,
        *,
        status: int,
        error: str | None = None,
    ) -> None:
        """Append a per-call entry to the accumulator used by batch.py."""
        entry: dict[str, Any] = {
            "query": query,
            "http_status": status,
            "elapsed_ms": elapsed_ms,
            "element_count": len(body.get("elements", [])) if isinstance(body, dict) else 0,
            "body": body,
        }
        if error is not None:
            entry["error"] = error
        self._raw_call_log.append(entry)

    def reset_raw_call_log(self) -> None:
        """Clear the per-site raw-response accumulator before a new site."""
        self._raw_call_log = []

    def consume_raw_call_log(self) -> list[dict[str, Any]]:
        """Return the accumulated raw calls and clear the buffer."""
        out = self._raw_call_log
        self._raw_call_log = []
        return out

    def _dump_raw_response(
        self, query: str, body: dict[str, Any], elapsed_ms: int,
    ) -> None:
        """Persist the full Overpass JSON response to disk for audit."""
        if _RAW_RESPONSE_DIR is None:
            return
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:12]
            filename = f"{ts}_{query_hash}.json"
            payload = {
                "meta": {
                    "query": query,
                    "url": self._url,
                    "timestamp_utc": ts,
                    "http_status": self._last_http_status,
                    "elapsed_ms": elapsed_ms,
                    "element_count": len(body.get("elements", [])),
                },
                "response": body,
            }
            (_RAW_RESPONSE_DIR / filename).write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        except Exception as exc:
            log.warning("osm_raw_dump_failed", error=str(exc))

    # ------------------------------------------------------------------
    # LL-017 / LL-018: Retry with slot polling
    # ------------------------------------------------------------------

    def _query_once_or_retry(self, overpass_ql: str) -> list[dict[str, Any]]:
        """Auto-retry wrapper used when *retry_on_error* is True."""
        return self.query_with_retry(overpass_ql)

    def query_with_retry(
        self,
        overpass_ql: str,
        *,
        max_retries: int = _MAX_RETRIES,
        backoff_base: float = _BACKOFF_BASE_S,
        backoff_cap: float = _BACKOFF_CAP_S,
    ) -> list[dict[str, Any]]:
        """Execute *overpass_ql* with exponential backoff on transient errors.

        Retries on 429, 504, timeouts (408) and disconnects (status 0).
        Polls Overpass ``/status`` before each retry to wait for a slot.
        """
        elements: list[dict[str, Any]] = []
        for attempt in range(max_retries + 1):
            elements = self._query_raw(overpass_ql)
            if not self.was_rate_limited:
                return elements
            if attempt < max_retries:
                wait = min(backoff_base * (2 ** attempt), backoff_cap)
                log.warning(
                    "osm_query_retry",
                    attempt=attempt + 1,
                    wait_s=round(wait),
                    status=self._last_http_status,
                )
                self.wait_for_slot(max_wait=wait)
                time.sleep(random.uniform(2, 8))
            else:
                log.error(
                    "osm_query_exhausted",
                    status=self._last_http_status,
                    retries=max_retries,
                )
        return elements

    def wait_for_slot(self, max_wait: float = 120.0) -> None:
        """Poll Overpass ``/status`` until a query slot is available (LL-018)."""
        status_url = self._url.replace("/interpreter", "/status")
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            try:
                resp = self._client.get(status_url, timeout=5)
                if resp.status_code == 200:
                    text = resp.text
                    if "slots available now" in text:
                        time.sleep(1)
                        return
                    for line in text.splitlines():
                        if "Slot available after" in line and "in" in line:
                            parts = line.split("in ")
                            if parts:
                                try:
                                    secs = int(
                                        parts[-1].replace(" seconds.", "").strip()
                                    )
                                    sleep_for = min(
                                        secs + 2, deadline - time.monotonic()
                                    )
                                    if sleep_for > 0:
                                        log.info("osm_wait_slot", wait_s=round(sleep_for))
                                        time.sleep(sleep_for)
                                    return
                                except (ValueError, IndexError):
                                    pass
            except Exception:
                pass
            time.sleep(5)

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    def fetch_populated_places(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        *,
        min_population: int = 0,
    ) -> list[OsmElement]:
        """Return populated places within *radius_m* of the site."""
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["place"~"city|town|village|hamlet"]'
            f'["population"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out body;\n"
        )
        elements = self.query(ql)
        results: list[OsmElement] = []
        for el in elements:
            pop = _parse_population(el.get("tags", {}).get("population", ""))
            if pop is not None and pop >= min_population:
                results.append(
                    OsmElement(
                        osm_type=el.get("type", "node"),
                        osm_id=el.get("id", 0),
                        lat=el.get("lat"),
                        lon=el.get("lon"),
                        tags=el.get("tags", {}),
                    )
                )
        return results

    def fetch_amenities(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        amenity_types: list[str],
    ) -> list[OsmElement]:
        """Return amenity nodes/ways within *radius_m*."""
        types_re = "|".join(amenity_types)
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  nwr["amenity"~"{types_re}"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_road_density(
        self,
        lat: float,
        lon: float,
        radius_m: float,
    ) -> dict[str, Any]:
        """Estimate road density within *radius_m*."""
        ql = (
            f"[out:json][timeout:180][maxsize:104857600];\n"
            f"(\n"
            f'  way["highway"~"motorway|trunk|primary|secondary|tertiary"]'
            f"(around:{radius_m},{lat},{lon});\n"
            f");\n"
            f"out geom;\n"
        )
        elements = self.query(ql)
        by_class: dict[str, float] = {}
        total_km = 0.0

        for el in elements:
            hw_class = el.get("tags", {}).get("highway", "unknown")
            geom = el.get("geometry", [])
            length_km = _polyline_length_km(geom)
            by_class[hw_class] = by_class.get(hw_class, 0.0) + length_km
            total_km += length_km

        import math
        area_km2 = math.pi * (radius_m / 1000) ** 2
        density = total_km / area_km2 if area_km2 > 0 else 0.0

        return {
            "total_road_km": round(total_km, 2),
            "by_class_km": {k: round(v, 2) for k, v in by_class.items()},
            "density_km_per_km2": round(density, 3),
            "area_km2": round(area_km2, 2),
        }

    def fetch_waterways(
        self,
        lat: float,
        lon: float,
        radius_m: float,
    ) -> list[OsmElement]:
        """Return major waterways within *radius_m*."""
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["waterway"~"river|canal"](around:{radius_m},{lat},{lon});\n'
            f'  relation["waterway"~"river|canal"]'
            f"(around:{radius_m},{lat},{lon});\n"
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "way"),
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat") or el.get("lat"),
                lon=el.get("center", {}).get("lon") or el.get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_airports(
        self,
        lat: float,
        lon: float,
        radius_km: float = 80,
    ) -> list[OsmElement]:
        """Return airports and heliports within *radius_km* (HI-01)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["aeroway"~"aerodrome|helipad"](around:{radius_m},{lat},{lon});\n'
            f'  way["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});\n'
            f'  relation["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_military_areas(
        self,
        lat: float,
        lon: float,
        radius_km: float = 25,
    ) -> list[OsmElement]:
        """Return military installations within *radius_km* (HI-06)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["landuse"="military"](around:{radius_m},{lat},{lon});\n'
            f'  relation["landuse"="military"](around:{radius_m},{lat},{lon});\n'
            f'  node["military"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_transmitters(
        self,
        lat: float,
        lon: float,
        radius_km: float = 25,
    ) -> list[OsmElement]:
        """Return communication transmitters/towers within *radius_km* (HI-07)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  node["man_made"~"mast|tower|antenna"](around:{radius_m},{lat},{lon});\n'
            f'  node["tower:type"~"communication|transmission"](around:{radius_m},{lat},{lon});\n'
            f'  way["power"="substation"]["substation"="transmission"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_power_infrastructure(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50,
    ) -> list[OsmElement]:
        """Return HV power lines and substations within *radius_km* (NS-02)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:120];\n"
            f"(\n"
            f'  way["power"="line"]["voltage"](around:{radius_m},{lat},{lon});\n'
            f'  node["power"="substation"](around:{radius_m},{lat},{lon});\n'
            f'  way["power"="substation"](around:{radius_m},{lat},{lon});\n'
            f'  node["power"="plant"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "node"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_land_use(
        self,
        lat: float,
        lon: float,
        radius_km: float = 5,
    ) -> list[OsmElement]:
        """Return land use polygons within *radius_km* (NS-05)."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["landuse"](around:{radius_m},{lat},{lon});\n'
            f'  relation["landuse"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center;\n"
        )
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type=el.get("type", "way"),
                osm_id=el.get("id", 0),
                lat=el.get("lat") or el.get("center", {}).get("lat"),
                lon=el.get("lon") or el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    # ------------------------------------------------------------------
    # P11: Transport access queries (NS-03, A14)
    # ------------------------------------------------------------------

    def fetch_nearest_highway(
        self,
        lat: float,
        lon: float,
        radius_km: float = 10,
    ) -> list[OsmElement]:
        """Return motorway/trunk/primary highways within radius_km.

        Uses ``out center tags`` for centroid-based distance computation.
        """
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["highway"~"motorway|trunk|primary"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center tags;\n"
        )
        self._inter_request_delay(multiplier=5.0)
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type="way",
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat"),
                lon=el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_nearest_railway(
        self,
        lat: float,
        lon: float,
        radius_km: float = 15,
    ) -> list[OsmElement]:
        """Return railway lines within radius_km for proximity and classification.

        Queries both standard rail and narrow gauge.
        """
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["railway"="rail"](around:{radius_m},{lat},{lon});\n'
            f'  way["railway"="narrow_gauge"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center tags;\n"
        )
        self._inter_request_delay(multiplier=5.0)
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type="way",
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat"),
                lon=el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_nearest_navigable_waterway(
        self,
        lat: float,
        lon: float,
        radius_km: float = 10,
    ) -> list[OsmElement]:
        """Return navigable waterways (boat=yes or CEMT-tagged) within radius_km."""
        radius_m = radius_km * 1000
        ql = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["waterway"="river"]["boat"="yes"](around:{radius_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["boat"="yes"](around:{radius_m},{lat},{lon});\n'
            f'  way["waterway"="river"]["CEMT"](around:{radius_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["CEMT"](around:{radius_m},{lat},{lon});\n'
            f'  way["waterway"="river"]["motorboat"="yes"](around:{radius_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["motorboat"="yes"](around:{radius_m},{lat},{lon});\n'
            f");\n"
            f"out center tags;\n"
        )
        self._inter_request_delay(multiplier=5.0)
        elements = self.query(ql)
        return [
            OsmElement(
                osm_type="way",
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat"),
                lon=el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements
        ]

    def fetch_transport_combined(
        self,
        lat: float,
        lon: float,
        *,
        highway_radius_km: float = 10.0,
        railway_radius_km: float = 15.0,
        waterway_radius_km: float = 10.0,
    ) -> tuple[list[OsmElement], list[OsmElement], list[OsmElement]]:
        """Fetch all transport data in TWO Overpass queries (down from 3).

        Query A: highways + railways (dense, but same geographic footprint).
        Query B: waterways (lightweight, rarely large).

        This halves per-query complexity vs the single-combined approach,
        avoiding server-side timeouts on dense OSM areas while still being
        33% more efficient than the original 3-query approach.

        Returns:
            (hw_elements, rw_elements, ww_elements) — same format as the
            individual fetch methods, suitable for the existing parsers.
        """
        hw_m = int(highway_radius_km * 1000)
        rw_m = int(railway_radius_km * 1000)
        ww_m = int(waterway_radius_km * 1000)

        # --- Query A: highways + railways ---
        ql_a = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["highway"~"motorway|trunk|primary"](around:{hw_m},{lat},{lon});\n'
            f'  way["railway"="rail"](around:{rw_m},{lat},{lon});\n'
            f'  way["railway"="narrow_gauge"](around:{rw_m},{lat},{lon});\n'
            f");\n"
            f"out center tags;\n"
        )
        self._inter_request_delay(multiplier=5.0)
        elements_a = self.query(ql_a)

        hw_elements: list[OsmElement] = []
        rw_elements: list[OsmElement] = []

        for el in elements_a:
            tags = el.get("tags", {})
            osm_el = OsmElement(
                osm_type="way",
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat"),
                lon=el.get("center", {}).get("lon"),
                tags=tags,
            )
            if "highway" in tags:
                hw_elements.append(osm_el)
            elif "railway" in tags:
                rw_elements.append(osm_el)

        # --- Query B: waterways ---
        ql_b = (
            f"[out:json][timeout:90];\n"
            f"(\n"
            f'  way["waterway"="river"]["boat"="yes"](around:{ww_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["boat"="yes"](around:{ww_m},{lat},{lon});\n'
            f'  way["waterway"="river"]["CEMT"](around:{ww_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["CEMT"](around:{ww_m},{lat},{lon});\n'
            f'  way["waterway"="river"]["motorboat"="yes"](around:{ww_m},{lat},{lon});\n'
            f'  way["waterway"="canal"]["motorboat"="yes"](around:{ww_m},{lat},{lon});\n'
            f");\n"
            f"out center tags;\n"
        )
        self._inter_request_delay(multiplier=5.0)
        elements_b = self.query(ql_b)

        ww_elements: list[OsmElement] = [
            OsmElement(
                osm_type="way",
                osm_id=el.get("id", 0),
                lat=el.get("center", {}).get("lat"),
                lon=el.get("center", {}).get("lon"),
                tags=el.get("tags", {}),
            )
            for el in elements_b
        ]

        return hw_elements, rw_elements, ww_elements

    def _inter_request_delay(self, multiplier: float = 1.0) -> None:
        """Sleep for the configured inter-request delay (Overpass fair-use)."""
        time.sleep(self._delay * multiplier)

    # ------------------------------------------------------------------
    # FIX-03: Site area estimation (BF-02, A15, NS-05a)
    # ------------------------------------------------------------------

    _SITE_AREA_TAGS = (
        '"power"="plant"',
        '"power"="station"',
        '"landuse"="industrial"',
        '"man_made"="works"',
    )

    def fetch_site_area(
        self,
        lat: float,
        lon: float,
        radius_m: float = 2000,
    ) -> SiteAreaResult:
        """Estimate site area from OSM industrial/power polygons.

        Queries for closed ways with industrial/power tags, parses them
        into Shapely polygons, and selects the best candidate by proximity
        to the site coordinates.
        """
        ql_parts = []
        for tag in self._SITE_AREA_TAGS:
            ql_parts.append(f'  way[{tag}](around:{radius_m},{lat},{lon});')

        ql = (
            f"[out:json][timeout:60];\n"
            f"(\n"
            + "\n".join(ql_parts)
            + "\n);\n"
            f"out body geom;\n"
        )

        elements = self.query(ql)
        if not elements:
            return SiteAreaResult(
                error="No industrial/power polygons found in OSM",
                quality="not_found",
            )

        candidates = _parse_site_area_candidates(lat, lon, elements)
        if not candidates:
            return SiteAreaResult(
                error="OSM returned elements but none had valid closed polygons",
                quality="not_found",
            )

        best = _select_best_candidate(candidates)

        log.info(
            "site_area_fetch_ok",
            lat=lat, lon=lon,
            area_ha=round(best.area_ha, 2),
            osm_id=best.osm_id,
            distance_km=round(best.distance_km, 3),
            candidates=len(candidates),
        )

        largest_contiguous = _largest_contiguous_ha(best.geometry)

        quality = "high"
        if best.distance_km >= 1.0:
            quality = "medium"
        if best.area_ha < 5.0:
            quality = "low"

        return SiteAreaResult(
            site_area_ha=best.area_ha,
            buildable_area_ha=best.area_ha,
            largest_contiguous_ha=largest_contiguous,
            osm_id=best.osm_id,
            osm_type=best.osm_type,
            source_tags=best.tags,
            distance_km=best.distance_km,
            candidate_count=len(candidates),
            quality=quality,
        )

    def fetch_site_area_with_retry(
        self,
        lat: float,
        lon: float,
        radius_m: float = 2000,
        *,
        max_retries: int = 5,
        backoff_base: float = 10.0,
        backoff_cap: float = 60.0,
    ) -> SiteAreaResult:
        """``fetch_site_area`` with exponential backoff for transient errors.

        Waits for an available Overpass slot before each retry by polling
        the ``/status`` endpoint.
        """
        for attempt in range(max_retries + 1):
            result = self.fetch_site_area(lat, lon, radius_m)
            if result.error and self.was_rate_limited and attempt < max_retries:
                wait = min(backoff_base * (2 ** attempt), backoff_cap)
                log.warning(
                    "site_area_retry",
                    attempt=attempt + 1, wait_s=wait,
                    status=self._last_http_status,
                )
                self._wait_for_slot(wait)
                continue
            return result
        return result  # type: ignore[possibly-undefined]

    def _wait_for_slot(self, max_wait: float) -> None:
        """Deprecated — delegates to :meth:`wait_for_slot`."""
        self.wait_for_slot(max_wait=max_wait)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_population(value: str) -> int | None:
    """Best-effort parse of OSM population tag values."""
    if not value:
        return None
    cleaned = value.replace(",", "").replace(".", "").replace(" ", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return None


def _polyline_length_km(geometry: list[dict[str, float]]) -> float:
    """Sum haversine distances along a list of ``{lat, lon}`` nodes."""
    if len(geometry) < 2:
        return 0.0
    total = 0.0
    for i in range(len(geometry) - 1):
        a, b = geometry[i], geometry[i + 1]
        total += haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    return total


# ------------------------------------------------------------------
# FIX-03: Site area candidate parsing
# ------------------------------------------------------------------

def _parse_site_area_candidates(
    lat: float,
    lon: float,
    elements: list[dict[str, Any]],
) -> list[SiteAreaCandidate]:
    """Parse Overpass elements into SiteAreaCandidate objects with geodesic area."""
    from atoms_vs_ashes.geo import geodesic_area_ha

    candidates: list[SiteAreaCandidate] = []
    for el in elements:
        etype = el.get("type", "")
        if etype != "way":
            continue

        geom = _parse_way_geometry(el)
        if geom is None:
            continue

        area_ha = geodesic_area_ha(geom)
        if area_ha < 0.01:
            continue

        centroid = geom.centroid
        dist = haversine_km(lat, lon, centroid.y, centroid.x)
        tags = el.get("tags", {})

        candidates.append(SiteAreaCandidate(
            osm_id=el.get("id", 0),
            osm_type=etype,
            tags=tags,
            geometry=geom,
            area_ha=area_ha,
            centroid_lat=centroid.y,
            centroid_lon=centroid.x,
            distance_km=dist,
        ))

    return candidates


_MIN_PLAUSIBLE_PLANT_HA = 5.0
_PREFER_LARGER_DISTANCE_FACTOR = 3.0


def _select_best_candidate(candidates: list[SiteAreaCandidate]) -> SiteAreaCandidate:
    """Pick the best polygon from candidates.

    Primary sort: closest to site by centroid distance.
    Override: if the closest candidate is < 5 ha and a larger candidate
    exists within 3x the distance, prefer the larger one — small polygons
    near power plants are often ancillary buildings, not the plant itself.
    """
    candidates.sort(key=lambda c: (c.distance_km, -c.area_ha))
    best = candidates[0]

    if best.area_ha >= _MIN_PLAUSIBLE_PLANT_HA or len(candidates) == 1:
        return best

    threshold_km = max(best.distance_km * _PREFER_LARGER_DISTANCE_FACTOR, 2.0)
    for c in candidates[1:]:
        if c.distance_km > threshold_km:
            break
        if c.area_ha >= _MIN_PLAUSIBLE_PLANT_HA:
            log.info(
                "site_area_prefer_larger",
                rejected_osm_id=best.osm_id,
                rejected_area_ha=round(best.area_ha, 2),
                selected_osm_id=c.osm_id,
                selected_area_ha=round(c.area_ha, 2),
                selected_distance_km=round(c.distance_km, 3),
            )
            return c

    return best


def _largest_contiguous_ha(geometry: Any) -> float:
    """Return the area of the largest contiguous polygon in a geometry."""
    from shapely.geometry import MultiPolygon
    from atoms_vs_ashes.geo import geodesic_area_ha

    if isinstance(geometry, MultiPolygon):
        return max(geodesic_area_ha(p) for p in geometry.geoms)
    return geodesic_area_ha(geometry)


# ------------------------------------------------------------------
# Plant boundary functions (used by ingest/osm_area.py)
# ------------------------------------------------------------------

def _parse_way_geometry(elem: dict[str, Any]) -> Any:
    """Parse a closed way geometry into a Shapely Polygon."""
    from shapely.geometry import Polygon

    nodes = elem.get("geometry", [])
    if not nodes or len(nodes) < 4:
        return None

    coords = [(n["lon"], n["lat"]) for n in nodes]
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    if len(coords) < 4:
        return None

    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly if not poly.is_empty else None
    except Exception:
        return None


def _parse_relation_geometry(elem: dict[str, Any]) -> Any:
    """Parse a relation with outer/inner members into a Shapely geometry."""
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import unary_union

    members = elem.get("members", [])
    if not members:
        return None

    outers: list[Any] = []
    inners: list[Any] = []

    for member in members:
        if member.get("type") != "way":
            continue
        nodes = member.get("geometry", [])
        if not nodes or len(nodes) < 4:
            continue
        coords = [(n["lon"], n["lat"]) for n in nodes]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        if len(coords) < 4:
            continue
        try:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue
        except Exception:
            continue

        role = member.get("role", "outer")
        if role == "inner":
            inners.append(poly)
        else:
            outers.append(poly)

    if not outers:
        return None

    result = unary_union(outers)
    for inner in inners:
        try:
            result = result.difference(inner)
        except Exception:
            continue

    return result if not result.is_empty else None


def compute_geodesic_area_ha(geometry: Any) -> float:
    """Compute geodesic area in hectares using pyproj Geod."""
    from atoms_vs_ashes.geo import geodesic_area_ha
    return geodesic_area_ha(geometry)


def find_best_plant_boundary(
    lat: float,
    lon: float,
    boundaries: list[PlantBoundary],
) -> PlantBoundary | None:
    """Select the best plant boundary based on centroid distance and area."""
    if not boundaries:
        return None
    if len(boundaries) == 1:
        return boundaries[0]

    def score(b: PlantBoundary) -> tuple[float, float]:
        dist = haversine_km(lat, lon, b.centroid_lat, b.centroid_lon)
        return (dist, -b.area_ha)

    return min(boundaries, key=score)


def fetch_plant_boundaries(
    lat: float,
    lon: float,
    radius_m: float = 2000,
    overpass_url: str = DEFAULT_OVERPASS_URL,
) -> list[PlantBoundary]:
    """Fetch power=plant polygons near (lat, lon) from Overpass API."""
    ql = (
        f"[out:json][timeout:90];\n"
        f"(\n"
        f'  way["power"="plant"](around:{radius_m},{lat},{lon});\n'
        f'  relation["power"="plant"](around:{radius_m},{lat},{lon});\n'
        f");\n"
        f"out body geom;\n"
    )

    client = httpx.Client(timeout=_TIMEOUT_S)
    try:
        resp = client.post(overpass_url, data={"data": ql})
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception as exc:
        log.warning("osm_plant_fetch_error", error=str(exc), lat=lat, lon=lon)
        return []
    finally:
        client.close()

    boundaries: list[PlantBoundary] = []
    for el in elements:
        etype = el.get("type", "")
        if etype == "way":
            geom = _parse_way_geometry(el)
        elif etype == "relation":
            geom = _parse_relation_geometry(el)
        else:
            continue

        if geom is None:
            continue

        area_ha = compute_geodesic_area_ha(geom)
        centroid = geom.centroid
        tags = el.get("tags", {})

        boundaries.append(PlantBoundary(
            osm_id=el.get("id", 0),
            osm_type=etype,
            name=tags.get("name"),
            geometry=geom,
            area_ha=area_ha,
            centroid_lat=centroid.y,
            centroid_lon=centroid.x,
        ))

    return boundaries


def health_check(overpass_url: str = DEFAULT_OVERPASS_URL) -> bool:
    """Module-level health check for Overpass API."""
    try:
        resp = httpx.get(
            overpass_url.replace("/interpreter", "/status"),
            timeout=10,
        )
        return resp.status_code == 200
    except httpx.HTTPError:
        return False
