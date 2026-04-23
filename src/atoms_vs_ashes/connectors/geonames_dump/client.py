# man_hours: 3.0
"""GeoNames cities5000.zip — download, cache, nearest populated place ≥ threshold."""

from __future__ import annotations

import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from atoms_vs_ashes.connectors.geonames_dump.models import (
    DEFAULT_ARCHIVE,
    DEFAULT_BASE_URL,
    DEFAULT_FEATURE_CLASS,
    DEFAULT_MIN_POPULATION,
    DEFAULT_TXT_NAME,
    NearestGeonamesResult,
)
from atoms_vs_ashes.connectors.geonames_dump.parsers import (
    haversine_km_vec,
    parse_geonames_line,
    row_matches_ri05_filter,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE = "sources/geonames"
_DOWNLOAD_TIMEOUT_S = 120


class GeonamesDumpConnector:
    """Loads filtered GeoNames cities and answers nearest-neighbour queries."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("geonames_dump", {})

        self._base_url: str = cfg.get("base_url", DEFAULT_BASE_URL).rstrip("/") + "/"
        self._archive_name: str = cfg.get("archive_name", DEFAULT_ARCHIVE)
        self._txt_name: str = cfg.get("txt_name", DEFAULT_TXT_NAME)
        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE))
        self._download_timeout: int = cfg.get("download_timeout_s", _DOWNLOAD_TIMEOUT_S)
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", 90)
        self._min_population: int = int(cfg.get("min_population", DEFAULT_MIN_POPULATION))
        self._feature_class: str = cfg.get("city_feature_class", DEFAULT_FEATURE_CLASS)

        self._client = httpx.Client(timeout=self._download_timeout)
        self._dump_mtime: datetime | None = None
        self._city_lats: np.ndarray | None = None
        self._city_lons: np.ndarray | None = None
        self._ids: np.ndarray | None = None
        self._pops: np.ndarray | None = None
        self._names: list[str] | None = None
        self._countries: list[str] | None = None
        self._fcodes: list[str] | None = None
        self._loaded = False

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def txt_path(self) -> Path:
        return self._cache_dir / self._txt_name

    def zip_path(self) -> Path:
        return self._cache_dir / self._archive_name

    def data_loaded(self) -> bool:
        return self._loaded

    def city_count(self) -> int:
        if self._city_lats is None:
            return 0
        return int(self._city_lats.shape[0])

    def health_check(self) -> bool:
        try:
            url = self._base_url
            r = self._client.head(url, timeout=15)
            return r.status_code < 500
        except httpx.HTTPError as exc:
            log.warning("geonames_dump_health_fail", error=str(exc))
            return False

    def ensure_local_data(self, *, force: bool = False) -> Path:
        """Download zip if missing or stale; extract cities5000.txt. Returns path to .txt."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        zpath = self.zip_path()
        tpath = self.txt_path()

        need_download = force or not zpath.is_file()
        if not need_download and zpath.is_file():
            age = datetime.now(timezone.utc) - datetime.fromtimestamp(
                zpath.stat().st_mtime, tz=timezone.utc,
            )
            if age.days > self._cache_ttl_days:
                need_download = True

        if need_download:
            url = f"{self._base_url}{self._archive_name}"
            log.info("geonames_dump_download", url=url)
            resp = self._client.get(url, timeout=self._download_timeout)
            resp.raise_for_status()
            zpath.write_bytes(resp.content)
            log.info("geonames_dump_download_ok", bytes=len(resp.content))

        if force or not tpath.is_file():
            with zipfile.ZipFile(zpath, "r") as zf:
                names = zf.namelist()
                member = self._txt_name
                if member not in names:
                    txts = [n for n in names if n.endswith(".txt")]
                    if not txts:
                        raise FileNotFoundError(f"No .txt in {self._archive_name}")
                    member = txts[0]
                zf.extract(member, self._cache_dir)
                extracted = self._cache_dir / member
                if extracted != tpath:
                    extracted.replace(tpath)

        self._dump_mtime = datetime.fromtimestamp(
            tpath.stat().st_mtime, tz=timezone.utc,
        )
        return tpath

    def load_cities(self, *, force: bool = False) -> int:
        """Parse TSV and build numpy index. Returns number of cities after filter."""
        tpath = self.ensure_local_data(force=force)
        ids: list[int] = []
        names: list[str] = []
        countries: list[str] = []
        fcodes: list[str] = []
        lats: list[float] = []
        lons: list[float] = []
        pops: list[int] = []

        with open(tpath, encoding="utf-8", errors="replace") as f:
            for line in f:
                row = parse_geonames_line(line)
                if row is None:
                    continue
                if not row_matches_ri05_filter(
                    row,
                    min_population=self._min_population,
                    feature_class=self._feature_class,
                ):
                    continue
                ids.append(row.geoname_id)
                names.append(row.name)
                countries.append(row.country_code)
                fcodes.append(row.feature_code)
                lats.append(row.lat)
                lons.append(row.lon)
                pops.append(row.population)

        self._ids = np.array(ids, dtype=np.int64)
        self._names = names
        self._countries = countries
        self._fcodes = fcodes
        self._city_lats = np.array(lats, dtype=np.float64)
        self._city_lons = np.array(lons, dtype=np.float64)
        self._pops = np.array(pops, dtype=np.int64)
        self._loaded = True

        log.info(
            "geonames_dump_loaded",
            path=str(tpath),
            cities=self.city_count(),
            min_population=self._min_population,
        )
        return self.city_count()

    def nearest_for(self, lat: float, lon: float) -> NearestGeonamesResult | None:
        """Nearest filtered city to (lat, lon), or None if index empty."""
        if not self._loaded or self._city_lats is None or self._city_lats.size == 0:
            return None
        dists = haversine_km_vec(lat, lon, self._city_lats, self._city_lons)
        idx = int(np.argmin(dists))
        dist = float(dists[idx])
        return NearestGeonamesResult(
            geoname_id=int(self._ids[idx]),
            name=self._names[idx],
            population=int(self._pops[idx]),
            country_code=self._countries[idx],
            distance_km=dist,
            feature_code=self._fcodes[idx],
        )

    def dump_date_iso(self) -> str:
        if self._dump_mtime:
            return self._dump_mtime.date().isoformat()
        return date.today().isoformat()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GeonamesDumpConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
