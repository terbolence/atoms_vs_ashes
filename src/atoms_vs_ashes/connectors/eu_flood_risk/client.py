# man_hours: 6.0
"""S-08 EU Flood Risk Maps connector — JRC/GloFAS raster + EEA APSFR vector.

Downloads and caches GloFAS flood hazard GeoTIFF tiles and the EEA APSFR
GeoPackage, then provides per-site flood depth sampling and regulatory
flood risk designation queries.

Source CRS: EPSG:4326 (WGS84) for both JRC GloFAS and EEA APSFR.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.eu_flood_risk.models import (
    DEFAULT_CACHE_DIR,
    EU_MEMBER_STATES,
    GLOFAS_BASE_URL,
    RETURN_PERIODS,
    SOURCE_APSFR,
    SOURCE_COMBINED,
    SOURCE_GLOFAS,
    TILE_EXTENTS_URL,
    ApsfrDesignation,
    EuFloodRiskResult,
    FloodDepthProfile,
    TileExtent,
)
from atoms_vs_ashes.connectors.eu_flood_risk.parsers import (
    build_flood_depth_profile,
    classify_flood_hazard,
    compute_flood_exposure_class,
    compute_flood_return_period_threshold,
    count_sampled_return_periods,
    determine_quality,
    determine_screening_flags,
    filter_tiles_for_bbox,
    find_covering_tile,
    parse_tile_extents,
    validate_depth_profile,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_TIMEOUT_S = 60
_TILE_DOWNLOAD_TIMEOUT_S = 300
_APSFR_DOWNLOAD_TIMEOUT_S = 600
_CHUNK_SIZE = 1 << 20  # 1 MiB


class EuFloodRiskConnector:
    """JRC/GloFAS flood hazard raster + EEA APSFR vector connector."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("eu_flood_risk")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("eu_flood_risk", {})

        self._glofas_base_url: str = cfg.get("glofas_base_url", GLOFAS_BASE_URL)
        self._tile_extents_url: str = cfg.get("tile_extents_url", TILE_EXTENTS_URL)
        self._return_periods: tuple[int, ...] = tuple(
            cfg.get("return_periods", RETURN_PERIODS)
        )
        self._cache_dir = Path(cfg.get("cache_dir", DEFAULT_CACHE_DIR))
        self._timeout: int = cfg.get("timeout_s", _TIMEOUT_S)
        self._tile_download_timeout: int = cfg.get(
            "tile_download_timeout_s", _TILE_DOWNLOAD_TIMEOUT_S
        )
        self._apsfr_download_timeout: int = cfg.get(
            "apsfr_download_timeout_s", _APSFR_DOWNLOAD_TIMEOUT_S
        )
        self._cache_ttl_days: int = cfg.get("glofas_cache_ttl_days", 365)

        bbox_cfg = cfg.get("project_bbox", {})
        self._project_bbox = (
            bbox_cfg.get("min_lon", 12.0),
            bbox_cfg.get("min_lat", 35.0),
            bbox_cfg.get("max_lon", 45.0),
            bbox_cfg.get("max_lat", 60.0),
        )

        self._exclusion_depth_rp100_m: float = cfg.get(
            "exclusion_depth_rp100_m", 0.5
        )
        self._avoidance_depth_rp500_m: float = cfg.get(
            "avoidance_depth_rp500_m", 0.0
        )

        self._client = httpx.Client(timeout=self._timeout)

        self._tile_index: list[TileExtent] | None = None
        self._raster_datasets: dict[str, Any] = {}  # key: "RP{rp}/{tile_id}"
        self._apsfr_index: Any | None = None
        self._apsfr_records: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify JRC tile extents URL is reachable."""
        try:
            resp = self._client.head(self._tile_extents_url, timeout=15)
            return resp.status_code < 400
        except Exception as exc:
            log.warning("flood_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Tile index management
    # ------------------------------------------------------------------

    def _tile_extents_path(self) -> Path:
        return self._cache_dir / "glofas" / "tile_extents.geojson"

    def _ensure_tile_index(self) -> list[TileExtent]:
        """Load or download tile_extents.geojson and build the tile index."""
        if self._tile_index is not None:
            return self._tile_index

        cached = self._tile_extents_path()
        if cached.is_file():
            log.info("flood_tile_index_cached", path=str(cached))
            with open(cached) as f:
                geojson = json.load(f)
        else:
            log.info("flood_tile_index_downloading", url=self._tile_extents_url)
            resp = self._client.get(self._tile_extents_url, timeout=30)
            resp.raise_for_status()
            geojson = resp.json()
            cached.parent.mkdir(parents=True, exist_ok=True)
            with open(cached, "w") as f:
                json.dump(geojson, f)

        all_tiles = parse_tile_extents(geojson)
        min_lon, min_lat, max_lon, max_lat = self._project_bbox
        self._tile_index = filter_tiles_for_bbox(
            all_tiles, min_lon, min_lat, max_lon, max_lat
        )
        log.info(
            "flood_tile_index_loaded",
            total_tiles=len(all_tiles),
            project_tiles=len(self._tile_index),
        )
        return self._tile_index

    # ------------------------------------------------------------------
    # GeoTIFF tile download and sampling
    # ------------------------------------------------------------------

    def _tile_path(self, return_period: int, tile: TileExtent) -> Path:
        fname = f"{tile.filename_stem(return_period)}.tif"
        return self._cache_dir / "glofas" / f"RP{return_period}" / fname

    def _download_tile(self, return_period: int, tile: TileExtent) -> Path:
        """Download a single GeoTIFF tile if not cached."""
        path = self._tile_path(return_period, tile)
        if path.is_file() and path.stat().st_size > 0:
            return path

        fname = f"{tile.filename_stem(return_period)}.tif"
        url = f"{self._glofas_base_url}/RP{return_period}/{fname}"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tif.part")

        log.info("flood_tile_downloading", url=url, dest=str(path))
        try:
            with httpx.stream(
                "GET", url, timeout=self._tile_download_timeout, follow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=_CHUNK_SIZE):
                        f.write(chunk)
            os.replace(str(tmp), str(path))
            size_mb = path.stat().st_size / (1024 * 1024)
            log.info("flood_tile_downloaded", tile_id=tile.tile_id, tile_name=tile.tile_name, rp=return_period, size_mb=round(size_mb, 1))
        except Exception as exc:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            log.warning("flood_tile_download_failed", tile_id=tile.tile_id, tile_name=tile.tile_name, rp=return_period, error=str(exc))
            raise

        return path

    def _open_raster(self, return_period: int, tile: TileExtent) -> Any:
        """Open a raster dataset, caching the handle."""
        key = f"RP{return_period}/{tile.tile_id}"
        if key in self._raster_datasets:
            return self._raster_datasets[key]

        path = self._tile_path(return_period, tile)
        if not path.is_file():
            path = self._download_tile(return_period, tile)

        try:
            import rasterio  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "rasterio is required for EU Flood Risk raster sampling. "
                "Install with: pip install rasterio"
            ) from exc

        ds = rasterio.open(str(path))
        self._raster_datasets[key] = ds
        return ds

    def sample_flood_depth(
        self, lat: float, lon: float, return_period: int,
    ) -> float | None:
        """Sample flood depth at a point for a single return period.

        Returns depth in metres, 0.0 for no inundation, or None if
        the point is outside the modelled domain (nodata).
        """
        tiles = self._ensure_tile_index()
        tile = find_covering_tile(tiles, lon, lat)
        if tile is None:
            return None

        try:
            ds = self._open_raster(return_period, tile)
        except Exception as exc:
            log.warning(
                "flood_raster_open_failed",
                tile_id=tile.tile_id, rp=return_period, error=str(exc),
            )
            return None

        return self._sample_point(ds, lon, lat)

    @staticmethod
    def _sample_point(ds: Any, lon: float, lat: float) -> float | None:
        """Pure raster point sampling — testable with mock dataset."""
        import math

        bounds = ds.bounds
        if not (bounds.left <= lon <= bounds.right
                and bounds.bottom <= lat <= bounds.top):
            return None

        try:
            for val in ds.sample([(lon, lat)]):
                raw = float(val[0])
                if math.isnan(raw):
                    return None
                if ds.nodata is not None and raw == float(ds.nodata):
                    return None
                return max(0.0, raw)
        except Exception:
            return None

        return None

    def sample_all_return_periods(
        self, lat: float, lon: float,
    ) -> FloodDepthProfile:
        """Sample flood depth for all configured return periods."""
        tiles = self._ensure_tile_index()
        tile = find_covering_tile(tiles, lon, lat)
        tile_id = tile.tile_id if tile else None

        depths: dict[int, float | None] = {}
        for rp in self._return_periods:
            if tile is None:
                depths[rp] = None
                continue
            try:
                ds = self._open_raster(rp, tile)
                depths[rp] = self._sample_point(ds, lon, lat)
            except Exception as exc:
                log.warning(
                    "flood_sample_error",
                    rp=rp, tile_id=tile.tile_id, lat=lat, lon=lon, error=str(exc),
                )
                depths[rp] = None

        return build_flood_depth_profile(depths, tile_id=tile_id)

    # ------------------------------------------------------------------
    # APSFR vector queries
    # ------------------------------------------------------------------

    def _apsfr_gpkg_path(self) -> Path:
        return self._cache_dir / "apsfr" / "apsfr.gpkg"

    def _ensure_apsfr_index(self) -> None:
        """Load the APSFR spatial index from cached GeoPackage."""
        if self._apsfr_index is not None:
            return

        gpkg_path = self._apsfr_gpkg_path()
        if not gpkg_path.is_file():
            log.info("flood_apsfr_not_cached", path=str(gpkg_path))
            self._apsfr_index = "empty"
            return

        try:
            import fiona  # type: ignore[import-untyped]
            from shapely.geometry import shape  # type: ignore[import-untyped]
            from shapely import STRtree  # type: ignore[import-untyped]
        except ImportError as exc:
            log.warning("flood_apsfr_import_error", error=str(exc))
            self._apsfr_index = "empty"
            return

        records: list[dict[str, Any]] = []
        geometries = []

        try:
            layers = fiona.listlayers(str(gpkg_path))
            target_layer = layers[0] if layers else None
            if target_layer is None:
                self._apsfr_index = "empty"
                return

            with fiona.open(str(gpkg_path), layer=target_layer) as src:
                for feat in src:
                    try:
                        geom = shape(feat["geometry"])
                        if not geom.is_valid:
                            geom = geom.buffer(0)
                        if geom.is_empty:
                            continue
                    except Exception:
                        continue

                    props = feat.get("properties", {})
                    records.append({
                        "geometry": geom,
                        "apsfr_id": props.get("apsfr_id") or props.get("APSFR_ID") or props.get("id", ""),
                        "country_code": props.get("country_code") or props.get("MS") or "",
                        "probability_scenario": (
                            props.get("probability_scenario")
                            or props.get("probScenario")
                            or props.get("PROB_SCENARIO")
                            or "unknown"
                        ).lower(),
                        "source_type": (
                            props.get("source_type")
                            or props.get("sourceType")
                            or props.get("SOURCE_TYPE")
                            or "unknown"
                        ).lower(),
                        "unit_of_management": (
                            props.get("unit_of_management")
                            or props.get("UoM")
                            or props.get("UOM_NAME")
                        ),
                        "reporting_cycle": int(
                            props.get("reporting_cycle")
                            or props.get("CYCLE")
                            or 2
                        ),
                    })
                    geometries.append(geom)

        except Exception as exc:
            log.warning("flood_apsfr_load_error", error=str(exc))
            self._apsfr_index = "empty"
            return

        if geometries:
            self._apsfr_index = STRtree(geometries)
        else:
            self._apsfr_index = "empty"

        self._apsfr_records = records
        log.info("flood_apsfr_loaded", n_polygons=len(records))

    def query_apsfr(
        self, lat: float, lon: float,
    ) -> list[ApsfrDesignation]:
        """Query APSFR spatial index for designations at a point."""
        self._ensure_apsfr_index()

        if self._apsfr_index == "empty" or self._apsfr_index is None:
            return []

        from shapely.geometry import Point  # type: ignore[import-untyped]

        point = Point(lon, lat)
        try:
            indices = self._apsfr_index.query(point)
            results: list[ApsfrDesignation] = []
            for idx in indices:
                rec = self._apsfr_records[idx]
                if rec["geometry"].contains(point):
                    results.append(ApsfrDesignation(
                        apsfr_id=str(rec["apsfr_id"]),
                        country_code=str(rec["country_code"]),
                        probability_scenario=str(rec["probability_scenario"]),
                        source_type=str(rec["source_type"]),
                        unit_of_management=rec.get("unit_of_management"),
                        reporting_cycle=int(rec.get("reporting_cycle", 2)),
                    ))
            return results
        except Exception as exc:
            log.warning("flood_apsfr_query_error", error=str(exc), lat=lat, lon=lon)
            return []

    # ------------------------------------------------------------------
    # Single-site fetch (core API)
    # ------------------------------------------------------------------

    def fetch(
        self, lat: float, lon: float, *, country_code: str | None = None,
    ) -> EuFloodRiskResult:
        """Fetch combined flood risk assessment for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code, used for quality determination.
        """
        depth_profile = self.sample_all_return_periods(lat, lon)
        apsfr_list = self.query_apsfr(lat, lon)

        is_permanent_water = False
        is_spurious = False

        hazard_class = classify_flood_hazard(
            depth_profile, apsfr_list,
            is_spurious=is_spurious,
            is_permanent_water=is_permanent_water,
            exclusion_depth_rp100_m=self._exclusion_depth_rp100_m,
            avoidance_depth_rp500_m=self._avoidance_depth_rp500_m,
        )
        exposure_class = compute_flood_exposure_class(depth_profile)
        rp_threshold = compute_flood_return_period_threshold(depth_profile)
        screening_flags = determine_screening_flags(
            depth_profile, apsfr_list,
            exclusion_depth_rp100_m=self._exclusion_depth_rp100_m,
            avoidance_depth_rp500_m=self._avoidance_depth_rp500_m,
        )

        has_coastal_apsfr = any(
            a.source_type == "coastal" for a in apsfr_list
        )

        sources = [SOURCE_GLOFAS]
        if apsfr_list:
            sources.append(SOURCE_APSFR)

        quality = determine_quality(
            depth_profile, apsfr_list,
            country_code=country_code,
            is_permanent_water=is_permanent_water,
            is_spurious=is_spurious,
        )

        validation_issues = validate_depth_profile(depth_profile)
        error = "; ".join(validation_issues) if validation_issues else None
        if validation_issues:
            quality = "low"

        return EuFloodRiskResult(
            lat=lat,
            lon=lon,
            flood_depth=depth_profile,
            apsfr=apsfr_list,
            hazard_class=hazard_class,
            screening_flags=screening_flags,
            flood_exposure_class=exposure_class,
            flood_return_period_threshold=rp_threshold,
            is_permanent_water=is_permanent_water,
            is_spurious_depth=is_spurious,
            coastal_flood_assessed=has_coastal_apsfr,
            sources=sources,
            quality=quality,
            error=error,
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
        from atoms_vs_ashes.connectors.eu_flood_risk.batch import enrich_batch
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
        for ds in self._raster_datasets.values():
            try:
                ds.close()
            except Exception:
                pass
        self._raster_datasets.clear()
        self._client.close()

    def __enter__(self) -> EuFloodRiskConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
