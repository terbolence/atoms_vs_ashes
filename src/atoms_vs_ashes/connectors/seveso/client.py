# man_hours: 3.5
"""S-12 SEVESO III connector.

Builds a unified hazardous facility database from three sources:
1. E-PRTR facilities (via EeaIndustrialConnector)
2. JRC Minerva SEVESO establishment CSV (local file)
3. National register CSVs (per-country local files)

Then performs proximity queries using the merged spatial index.

Source CRS: EPSG:4326 (WGS84).
Coverage: EU-27 (full), RS/TR (partial), others (national files only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atoms_vs_ashes.connectors.eea_industrial.client import EeaIndustrialConnector
from atoms_vs_ashes.connectors.eea_industrial.models import (
    IndustrialFacility,
    IndustrialProximityResult,
)
from atoms_vs_ashes.connectors.seveso.models import (
    SOURCE_NAME,
    MergeStats,
)
from atoms_vs_ashes.connectors.seveso.parsers import (
    merge_facilities,
    parse_minerva_csv,
    parse_national_csv,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_MINERVA_PATH = "sources/seveso/minerva_seveso.csv"
_DEFAULT_NATIONAL_DIR = "sources/seveso/national"
_DEFAULT_CACHE_TTL_DAYS = 90


class SevesoConnector:
    """SEVESO III three-source fusion connector.

    Wraps EeaIndustrialConnector with Minerva and national register
    data for enriched SEVESO-specific facility proximity analysis.
    """

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "connector_config"):
            cfg = settings.connector_config("seveso")
        elif settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("seveso", {})

        self._minerva_path = Path(cfg.get("minerva_local_path", _DEFAULT_MINERVA_PATH))
        self._national_dir = Path(cfg.get("national_data_dir", _DEFAULT_NATIONAL_DIR))
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _DEFAULT_CACHE_TTL_DAYS)
        self._dedup_distance_m: float = cfg.get("dedup_distance_threshold_m", 500.0)
        self._dedup_name_threshold: float = cfg.get("dedup_name_similarity_threshold", 0.8)
        self._search_radius_km: float = cfg.get("max_search_radius_km", 25.0)

        self._eea = EeaIndustrialConnector(settings)
        self._eea._search_radius_km = self._search_radius_km
        self._index_built = False
        self._merge_stats: MergeStats | None = None

    # ------------------------------------------------------------------
    # Data lifecycle
    # ------------------------------------------------------------------

    @property
    def minerva_path(self) -> Path:
        return self._minerva_path

    @property
    def national_dir(self) -> Path:
        return self._national_dir

    def minerva_exists(self) -> bool:
        """Check whether the Minerva SEVESO CSV is available."""
        return self._minerva_path.is_file() and self._minerva_path.stat().st_size > 0

    def national_files_available(self) -> list[str]:
        """List country codes with available national register CSVs."""
        if not self._national_dir.is_dir():
            return []
        return sorted(
            p.stem.upper()
            for p in self._national_dir.glob("*.csv")
            if p.stat().st_size > 0
        )

    # ------------------------------------------------------------------
    # Facility index build
    # ------------------------------------------------------------------

    def build_facility_index(self) -> MergeStats:
        """Build the unified facility database from all three sources.

        Must be called before any fetch() or enrich operations.
        """
        # Phase A: Load E-PRTR (via EeaIndustrialConnector)
        eprtr_index = self._eea.ensure_loaded()
        eprtr_facilities = list(eprtr_index.facilities)
        log.info("seveso_eprtr_loaded", count=len(eprtr_facilities))

        # Phase B: Load Minerva SEVESO
        minerva_establishments = []
        if self.minerva_exists():
            text = self._minerva_path.read_text(encoding="utf-8-sig")
            minerva_establishments = parse_minerva_csv(text)
            log.info("seveso_minerva_loaded", count=len(minerva_establishments))
        else:
            log.warning(
                "seveso_minerva_missing",
                path=str(self._minerva_path),
            )

        # Phase C: Load national register files
        national_facilities = []
        for cc in self.national_files_available():
            csv_path = self._national_dir / f"{cc.lower()}.csv"
            if not csv_path.exists():
                csv_path = self._national_dir / f"{cc.upper()}.csv"
            if csv_path.exists():
                try:
                    text = csv_path.read_text(encoding="utf-8-sig")
                    parsed = parse_national_csv(text, cc)
                    national_facilities.extend(parsed)
                    log.info("seveso_national_loaded", country=cc, count=len(parsed))
                except Exception as exc:
                    log.error(
                        "seveso_national_parse_error",
                        country=cc, error=str(exc),
                    )

        # Phase D: Merge and deduplicate
        merged, stats = merge_facilities(
            eprtr_facilities,
            minerva_establishments,
            national_facilities,
            distance_threshold_m=self._dedup_distance_m,
            name_similarity_threshold=self._dedup_name_threshold,
        )

        # Phase E: Rebuild spatial index with merged facilities
        self._eea.load_external_facilities(merged)
        self._index_built = True
        self._merge_stats = stats

        log.info(
            "seveso_index_built",
            total_facilities=stats.merged_total,
            eprtr=stats.eprtr_count,
            minerva=stats.minerva_count,
            national=stats.national_count,
            minerva_matched=stats.minerva_matched,
        )
        return stats

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify data sources are available and loadable."""
        eea_ok = self._eea.data_exists()
        minerva_ok = self.minerva_exists()
        if not eea_ok and not minerva_ok:
            log.warning("seveso_health_check_failed", reason="no data files found")
            return False
        try:
            if not self._index_built:
                self.build_facility_index()
            return self._eea.facility_index is not None and self._eea.facility_index.facility_count > 0
        except Exception as exc:
            log.warning("seveso_health_check_failed", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Point query
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str = "",
    ) -> IndustrialProximityResult:
        """Query SEVESO/industrial facility proximity for a single site.

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        country_code
            ISO 3166-1 alpha-2 code for data quality assessment.
        """
        if not self._index_built:
            self.build_facility_index()

        result = self._eea.fetch(lat, lon, country_code=country_code)
        result.source = SOURCE_NAME

        # Enrich data_sources_used with SEVESO-specific sources
        sources = list(result.data_sources_used)
        if self.minerva_exists():
            sources.append("minerva")
        for cc in self.national_files_available():
            sources.append(f"national_{cc}")
        result.data_sources_used = sorted(set(sources))

        return result

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._eea.close()
        self._index_built = False

    def __enter__(self) -> SevesoConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
