# man_hours: 5.0
"""S-10 Copernicus EMS connector — RRM + Rapid Mapping activation catalogue.

Queries the Copernicus Emergency Management Service APIs for flood-related
activations, builds a spatial index of flood footprints, and provides
per-site flash flood susceptibility assessment.

Two-phase execution: (A) catalogue ingestion (network), (B) site enrichment (local).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.copernicus_ems.models import (
    ACTIVATION_COUNTRIES,
    DEFAULT_CACHE_DIR,
    DEFAULT_SITE_BUFFER_KM,
    INSCOPE_COUNTRIES,
    PROJECT_BBOX,
    RAPID_API_URL,
    RAPID_CATEGORIES,
    RRM_API_URL,
    SOURCE_COMBINED,
    SOURCE_RAPID,
    SOURCE_RRM,
    CatalogueIngestionResult,
    FlashFloodAssessment,
    FloodFootprint,
    FootprintSummary,
    RapidActivation,
    RrmActivation,
)
from atoms_vs_ashes.connectors.copernicus_ems.parsers import (
    classify_susceptibility,
    determine_quality,
    parse_rapid_activation,
    parse_rrm_activation,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_TIMEOUT_S = 30
_INTER_REQUEST_DELAY_S = 1.0
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_RAW_DIR = _PROJECT_ROOT / "data" / "raw_responses" / "copernicus_ems"


class CopernicusEmsConnector:
    """Copernicus EMS RRM + Rapid Mapping flood activation connector."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("copernicus_ems")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("copernicus_ems", {})

        self._rrm_api_url: str = cfg.get("rrm_api_url", RRM_API_URL)
        self._rapid_api_url: str = cfg.get("rapid_api_url", RAPID_API_URL)
        self._cache_dir = Path(cfg.get("geodata_cache_dir", DEFAULT_CACHE_DIR))
        self._timeout: int = cfg.get("timeout_s", _TIMEOUT_S)
        self._inter_request_delay: float = cfg.get(
            "inter_request_delay_s", _INTER_REQUEST_DELAY_S
        )
        self._site_buffer_km: float = cfg.get("site_buffer_km", DEFAULT_SITE_BUFFER_KM)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 180)
        self._categories: list[str] = cfg.get("categories", ["Flood", "Storm"])

        thresholds = cfg.get("susceptibility_thresholds", {})
        self._medium_distance_km: float = thresholds.get("medium_distance_km", 10.0)
        self._low_distance_km: float = thresholds.get("low_distance_km", 50.0)

        self._client = httpx.Client(timeout=self._timeout, follow_redirects=True)

        self._rrm_activations: list[RrmActivation] = []
        self._rapid_activations: list[RapidActivation] = []
        self._footprints: list[FloodFootprint] = []
        self._footprint_centroids: list[tuple[float, float]] = []
        self._catalogue_loaded = False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify RRM API is reachable with a minimal request."""
        try:
            resp = self._client.get(
                self._rrm_api_url,
                params={"limit": 1},
                timeout=15,
            )
            return resp.status_code == 200
        except Exception as exc:
            log.warning("ems_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Catalogue fetching (Phase A)
    # ------------------------------------------------------------------

    def fetch_rrm_activations(self) -> list[RrmActivation]:
        """Fetch all European RRM activations (flood + storm), filtered client-side.

        The RRM API does not support server-side category/continent filtering,
        so we fetch all activations and keep those in Europe whose category
        matches our configured categories.
        """
        activations: list[RrmActivation] = []
        limit = 50
        offset = 0
        total_count: int | None = None
        accepted_cats = {c.lower() for c in self._categories}
        min_lon, min_lat, max_lon, max_lat = PROJECT_BBOX

        while True:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            try:
                resp = self._client.get(
                    self._rrm_api_url, params=params, timeout=self._timeout,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.TimeoutException as exc:
                log.warning("ems_rrm_timeout", error=str(exc))
                break
            except httpx.HTTPStatusError as exc:
                log.warning("ems_rrm_http_error", status=exc.response.status_code)
                break
            except Exception as exc:
                log.warning("ems_rrm_error", error=str(exc))
                break

            if total_count is None:
                total_count = data.get("count", 0)

            results = data.get("results", [])
            if not results:
                break

            for item in results:
                if item.get("continent", "").lower() != "europe":
                    continue
                if item.get("category", "").lower() not in accepted_cats:
                    continue
                activation = parse_rrm_activation(item)
                if not activation:
                    continue
                if activation.centroid_lon is not None:
                    if not (min_lon <= activation.centroid_lon <= max_lon
                            and min_lat <= activation.centroid_lat <= max_lat):
                        continue
                activations.append(activation)

            offset += limit
            if offset >= (total_count or 0):
                break
            time.sleep(self._inter_request_delay)

        log.info("ems_rrm_fetched", count=len(activations), categories=list(accepted_cats))
        return activations

    def fetch_rapid_activations(self) -> list[RapidActivation]:
        """Fetch Rapid Mapping activations (flood + storm) via offset pagination.

        Uses explicit offset/limit instead of ``next`` URLs because the
        Rapid API's ``next`` links use HTTP (causing 301 redirects) and
        sometimes return stale/duplicate pages.

        Includes activations from *all* European countries (not just inscope)
        because a flood in Germany near the Polish border is relevant to
        nearby Polish sites.
        """
        activations: list[RapidActivation] = []
        limit = 100
        offset = 0
        total_count: int | None = None
        page = 0
        accepted_cats = set(RAPID_CATEGORIES)
        min_lon, min_lat, max_lon, max_lat = PROJECT_BBOX

        while True:
            page += 1
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            try:
                resp = self._client.get(
                    self._rapid_api_url, params=params, timeout=self._timeout,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.TimeoutException as exc:
                log.warning("ems_rapid_timeout", page=page, offset=offset, error=str(exc))
                break
            except httpx.HTTPStatusError as exc:
                log.warning("ems_rapid_http_error", page=page, status=exc.response.status_code)
                break
            except Exception as exc:
                log.warning("ems_rapid_error", page=page, error=str(exc))
                break

            if total_count is None:
                total_count = data.get("count", 0)

            results = data.get("results", [])
            if not results:
                break

            for item in results:
                activation = parse_rapid_activation(item)
                if not activation:
                    continue
                if activation.category not in accepted_cats:
                    continue
                if not any(c in ACTIVATION_COUNTRIES for c in activation.countries):
                    continue
                if activation.centroid_lon is not None:
                    if not (min_lon <= activation.centroid_lon <= max_lon
                            and min_lat <= activation.centroid_lat <= max_lat):
                        continue
                activations.append(activation)

            log.info(
                "ems_rapid_page",
                page=page, fetched=len(results), offset=offset,
                total=total_count, inscope=len(activations),
            )

            offset += limit
            if offset >= (total_count or 0):
                break
            time.sleep(self._inter_request_delay)

        log.info("ems_rapid_fetched", count=len(activations), categories=list(accepted_cats))
        return activations

    def ingest_catalogue(self, run_id: str) -> CatalogueIngestionResult:
        """Fetch all relevant activations and build the spatial index.

        This is Phase A — network-heavy, run infrequently.
        """
        t0 = time.monotonic()
        result = CatalogueIngestionResult(run_id=run_id)

        self._rrm_activations = self.fetch_rrm_activations()
        result.n_rrm_fetched = len(self._rrm_activations)

        self._rapid_activations = self.fetch_rapid_activations()
        result.n_rapid_fetched = len(self._rapid_activations)

        self._save_catalogue_to_disk(run_id)

        self._build_centroid_index()
        result.n_footprints_total = len(self._footprint_centroids)

        self._catalogue_loaded = True
        result.elapsed_s = time.monotonic() - t0

        log.info(
            "ems_catalogue_ingested",
            rrm=result.n_rrm_fetched,
            rapid=result.n_rapid_fetched,
            centroids=result.n_footprints_total,
            elapsed_s=round(result.elapsed_s, 1),
        )
        return result

    def _save_catalogue_to_disk(self, run_id: str) -> None:
        """Persist raw catalogue data (RRM + Rapid activations) to disk."""
        out_dir = _RAW_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            (out_dir / "rrm_activations.json").write_text(
                json.dumps(
                    [{"code": a.code, "category": a.category,
                      "countries": a.countries,
                      "centroid_lat": a.centroid_lat,
                      "centroid_lon": a.centroid_lon,
                      "activation_time": str(a.activation_time) if a.activation_time else None}
                     for a in self._rrm_activations],
                    indent=2, default=str,
                ),
                encoding="utf-8",
            )
            (out_dir / "rapid_activations.json").write_text(
                json.dumps(
                    [{"code": a.code, "category": a.category,
                      "countries": a.countries,
                      "centroid_lat": a.centroid_lat,
                      "centroid_lon": a.centroid_lon,
                      "activation_time": str(a.activation_time) if a.activation_time else None}
                     for a in self._rapid_activations],
                    indent=2, default=str,
                ),
                encoding="utf-8",
            )
            log.info("ems_catalogue_saved_to_disk", path=str(out_dir))
        except OSError:
            log.warning("ems_catalogue_disk_save_failed", path=str(out_dir))

    def _build_centroid_index(self) -> None:
        """Build a simple centroid-based spatial index from activations.

        Uses activation centroids for proximity queries. Full geodata
        download and polygon-based spatial indexing is deferred to a
        future enhancement when geodata packages are available.
        """
        self._footprint_centroids = []
        self._footprints = []

        for act in self._rrm_activations:
            if act.centroid_lon is not None and act.centroid_lat is not None:
                self._footprint_centroids.append(
                    (act.centroid_lon, act.centroid_lat)
                )
                self._footprints.append(FloodFootprint(
                    activation_code=act.code,
                    activation_type="rrm",
                    activation_date=act.activation_time,
                    category=act.category.lower(),
                    countries=act.countries,
                    source_url=act.download_urls[0] if act.download_urls else None,
                ))

        for act in self._rapid_activations:
            if act.centroid_lon is not None and act.centroid_lat is not None:
                self._footprint_centroids.append(
                    (act.centroid_lon, act.centroid_lat)
                )
                self._footprints.append(FloodFootprint(
                    activation_code=act.code,
                    activation_type="rapid",
                    activation_date=act.activation_time,
                    category=act.category.lower() if act.category else "flood",
                    countries=act.countries,
                ))

        log.info("ems_centroid_index_built", n_centroids=len(self._footprint_centroids))

    # ------------------------------------------------------------------
    # Single-site assessment (Phase B — local, no network)
    # ------------------------------------------------------------------

    def assess_site(
        self, lat: float, lon: float,
    ) -> FlashFloodAssessment:
        """Assess flash flood susceptibility for a site using the catalogue.

        Requires prior call to ``ingest_catalogue()`` or loading from cache.
        """
        if not self._catalogue_loaded:
            return FlashFloodAssessment(
                lat=lat, lon=lon,
                error="Catalogue not loaded. Call ingest_catalogue() first.",
                quality="insufficient",
            )

        if not self._footprint_centroids:
            return FlashFloodAssessment(
                lat=lat, lon=lon,
                quality="insufficient",
                error="No activation data available in catalogue.",
            )

        from atoms_vs_ashes.geo import haversine_km

        nearest_dist: float | None = None
        nearest_idx: int | None = None
        events_within_buffer: list[tuple[int, float]] = []

        for i, (c_lon, c_lat) in enumerate(self._footprint_centroids):
            dist = haversine_km(lat, lon, c_lat, c_lon)
            if dist <= self._site_buffer_km:
                events_within_buffer.append((i, dist))
            if nearest_dist is None or dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = i

        n_events = len(events_within_buffer)

        footprint_summaries: list[FootprintSummary] = []
        for idx, dist in sorted(events_within_buffer, key=lambda x: x[1]):
            fp = self._footprints[idx]
            footprint_summaries.append(FootprintSummary(
                activation_code=fp.activation_code,
                activation_date=fp.activation_date,
                distance_km=round(dist, 2),
                category=fp.category,
            ))

        susceptibility = classify_susceptibility(
            intersection_area_km2=0.0,
            distance_km=nearest_dist,
            n_events=n_events,
            medium_distance_km=self._medium_distance_km,
            low_distance_km=self._low_distance_km,
            negligible_distance_km=self._site_buffer_km,
        )

        quality = determine_quality(n_events, susceptibility)

        nearest_code = None
        nearest_date = None
        if nearest_idx is not None:
            fp = self._footprints[nearest_idx]
            nearest_code = fp.activation_code
            nearest_date = fp.activation_date

        return FlashFloodAssessment(
            lat=lat,
            lon=lon,
            susceptibility=susceptibility,
            distance_to_nearest_km=round(nearest_dist, 2) if nearest_dist is not None else None,
            n_events_within_buffer=n_events,
            nearest_activation_code=nearest_code,
            nearest_activation_date=nearest_date,
            footprints_intersecting=footprint_summaries,
            source=SOURCE_COMBINED,
            quality=quality,
        )

    # ------------------------------------------------------------------
    # Batch delegation (to batch.py)
    # ------------------------------------------------------------------

    def enrich_batch(
        self,
        session: Any,
        run_id: str,
        *,
        site_ids: list[Any] | None = None,
        country_codes: list[str] | None = None,
    ) -> Any:
        from atoms_vs_ashes.connectors.copernicus_ems.batch import enrich_batch
        return enrich_batch(
            self, session, run_id,
            site_ids=site_ids, country_codes=country_codes,
        )

    def enrich_all(self, session: Any, run_id: str) -> Any:
        return self.enrich_batch(session, run_id)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> CopernicusEmsConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
