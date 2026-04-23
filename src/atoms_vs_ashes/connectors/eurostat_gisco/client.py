# man_hours: 6.0
"""S-16 Eurostat GISCO connector.

Downloads Urban Audit Cities GeoJSON and city population data from
Eurostat, then computes RI-05 (nearest city >50k, settlement hierarchy)
for each candidate site.

Two-phase execution:
  Phase A — download/cache reference data (cities GeoJSON + populations)
  Phase B — per-site computation (haversine distance, hierarchy classification)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.eurostat_gisco.models import (
    CITY_POP_THRESHOLD,
    EUROSTAT_API_URL,
    GISCO_BASE_URL,
    IN_SCOPE_ALL,
    SOURCE_NAME,
    CityRecord,
    EurostatGiscoResult,
)
from atoms_vs_ashes.connectors.eurostat_gisco.parsers import (
    build_result,
    compute_city_proximity,
    parse_cities_geojson,
    parse_eurostat_jsonstat_populations,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/eurostat_gisco"
_CITIES_GEOJSON_PATH = "urau/geojson/URAU_RG_100K_2021_4326_CITIES.geojson"
_DOWNLOAD_TIMEOUT_S = 120
_API_TIMEOUT_S = 30
_INTER_REQUEST_DELAY_S = 0.5
_POPULATION_INDICATOR = "DE1001V"
_POPULATION_BATCH_SIZE = 50


class EurostatGiscoConnector:
    """Fetches Urban Audit city data and computes RI-05 city proximity."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("eurostat_gisco", {})

        self._gisco_base_url: str = cfg.get("gisco_base_url", GISCO_BASE_URL)
        self._eurostat_api_url: str = cfg.get("eurostat_api_url", EUROSTAT_API_URL)
        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._download_timeout: int = cfg.get("timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._api_timeout: int = cfg.get("api_timeout_s", _API_TIMEOUT_S)
        self._inter_request_delay: float = cfg.get(
            "inter_request_delay_s", _INTER_REQUEST_DELAY_S,
        )
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 180)
        self._city_search_radius_km: float = cfg.get("city_search_radius_km", 100)
        self._city_min_population: int = cfg.get(
            "city_min_population", CITY_POP_THRESHOLD,
        )

        self._client = httpx.Client(timeout=self._download_timeout)
        self._cities: list[CityRecord] | None = None
        self._data_loaded = False

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def data_loaded(self) -> bool:
        return self._data_loaded

    def health_check(self) -> bool:
        """Verify GISCO distribution API is reachable."""
        try:
            url = f"{self._gisco_base_url}/urau/"
            resp = self._client.head(url, timeout=10)
            ok = resp.status_code < 400
            if ok:
                log.info("gisco_health_ok")
            return ok
        except httpx.HTTPError as exc:
            log.warning("gisco_health_error", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Phase A: Data ingestion
    # ------------------------------------------------------------------

    def load_data(self, *, force: bool = False) -> int:
        """Download and cache cities + populations. Returns city count."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        cities_path = self._cache_dir / "cities.geojson"
        pop_path = self._cache_dir / "city_populations.json"

        cities_raw = self._load_or_download_cities(cities_path, force=force)
        self._cities = parse_cities_geojson(cities_raw)
        log.info("gisco_cities_parsed", count=len(self._cities))

        populations = self._load_or_fetch_populations(pop_path, force=force)
        self._merge_populations(populations)

        cities_with_pop = sum(1 for c in self._cities if c.population is not None)
        log.info(
            "gisco_data_loaded",
            total_cities=len(self._cities),
            cities_with_population=cities_with_pop,
            cities_above_threshold=sum(
                1 for c in self._cities
                if c.population is not None and c.population >= self._city_min_population
            ),
        )

        self._data_loaded = True
        return len(self._cities)

    def _load_or_download_cities(
        self, cache_path: Path, *, force: bool = False,
    ) -> dict[str, Any]:
        """Load cities GeoJSON from cache or download from GISCO."""
        if cache_path.is_file() and cache_path.stat().st_size > 0 and not force:
            log.info("gisco_cities_cached", path=str(cache_path))
            with open(cache_path) as f:
                return json.load(f)

        url = f"{self._gisco_base_url}/{_CITIES_GEOJSON_PATH}"
        log.info("gisco_cities_download_start", url=url)
        resp = self._client.get(url, timeout=self._download_timeout)
        resp.raise_for_status()
        data = resp.json()

        with open(cache_path, "w") as f:
            json.dump(data, f)
        log.info("gisco_cities_download_ok", features=len(data.get("features", [])))
        return data

    def _load_or_fetch_populations(
        self, cache_path: Path, *, force: bool = False,
    ) -> dict[str, int]:
        """Load city populations from cache or fetch from Eurostat API."""
        if cache_path.is_file() and cache_path.stat().st_size > 0 and not force:
            log.info("gisco_populations_cached", path=str(cache_path))
            with open(cache_path) as f:
                return json.load(f)

        if self._cities is None:
            return {}

        in_scope_codes = [
            c.city_code for c in self._cities
            if c.country_code in IN_SCOPE_ALL or c.country_code in {
                "DE", "IT", "FR", "GR",
            }
        ]
        all_codes = [c.city_code for c in self._cities]

        populations = self._fetch_populations_batched(all_codes)

        with open(cache_path, "w") as f:
            json.dump(populations, f)
        log.info("gisco_populations_fetched", count=len(populations))
        return populations

    def _fetch_populations_batched(
        self, city_codes: list[str],
    ) -> dict[str, int]:
        """Query Eurostat urb_cpop1 in batches."""
        populations: dict[str, int] = {}

        for i in range(0, len(city_codes), _POPULATION_BATCH_SIZE):
            batch = city_codes[i : i + _POPULATION_BATCH_SIZE]
            try:
                batch_pops = self._fetch_population_batch(batch)
                populations.update(batch_pops)
            except Exception as exc:
                log.warning(
                    "gisco_population_batch_error",
                    batch_start=i, error=str(exc),
                )

            if i + _POPULATION_BATCH_SIZE < len(city_codes):
                time.sleep(self._inter_request_delay)

            if (i // _POPULATION_BATCH_SIZE + 1) % 5 == 0:
                log.info(
                    "gisco_population_progress",
                    fetched=min(i + _POPULATION_BATCH_SIZE, len(city_codes)),
                    total=len(city_codes),
                    found=len(populations),
                )

        return populations

    def _fetch_population_batch(
        self, city_codes: list[str],
    ) -> dict[str, int]:
        """Fetch population for a batch of city codes from Eurostat."""
        url = f"{self._eurostat_api_url}/data/urb_cpop1"
        params: dict[str, Any] = {
            "format": "JSON",
            "lang": "en",
            "indic_ur": _POPULATION_INDICATOR,
        }
        for code in city_codes:
            params.setdefault("cities", [])
        params_list = [("format", "JSON"), ("lang", "en"), ("indic_ur", _POPULATION_INDICATOR)]
        for code in city_codes:
            params_list.append(("cities", code))

        resp = self._client.get(url, params=params_list, timeout=self._api_timeout)
        resp.raise_for_status()
        data = resp.json()
        return parse_eurostat_jsonstat_populations(data)

    def _merge_populations(self, populations: dict[str, int]) -> None:
        """Merge fetched populations into loaded city records."""
        if not self._cities:
            return
        for city in self._cities:
            pop = populations.get(city.city_code)
            if pop is not None:
                city.population = pop

    # ------------------------------------------------------------------
    # Phase B: Per-site computation
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        max_distance_km: float | None = None,
        min_population: int | None = None,
    ) -> EurostatGiscoResult:
        """Compute RI-05 city proximity for a single site."""
        if not self._data_loaded or self._cities is None:
            self.load_data()

        max_dist = max_distance_km or self._city_search_radius_km
        min_pop = min_population or self._city_min_population

        try:
            city_prox = compute_city_proximity(
                lat, lon, self._cities,
                max_distance_km=max_dist,
                min_population=min_pop,
            )

            quality = "high"
            if not city_prox.nearest_city_name:
                quality = "low"

            return build_result(
                lat, lon, city_prox, quality=quality,
            )
        except Exception as exc:
            log.error("gisco_fetch_error", lat=lat, lon=lon, error=str(exc))
            return build_result(
                lat, lon, quality="insufficient",
                error=str(exc),
            )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EurostatGiscoConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
