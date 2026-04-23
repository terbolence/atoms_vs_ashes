# man_hours: 6.0
"""FIX-03: Site area enrichment via OSM Overpass + CORINE fallback.

Criteria served: BF-02 (land area adequacy), A15 (site area adequacy),
NS-05a (contiguous land area).

Follows the ``assess_and_persist()`` pattern established by other analysis
modules, with batch enrichment mirroring ``seismic_hazard/batch.py``.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_observation
from atoms_vs_ashes.connectors.corine import (
    CORINE_COVERED_COUNTRIES,
    CorineConnector,
    DEVELOPABLE_CODES,
    parse_clc_features,
)
from atoms_vs_ashes.connectors.osm import OverpassClient
from atoms_vs_ashes.connectors.osm.models import SiteAreaResult
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.geo import geodesic_area_ha, buffer_circle_wgs84
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

CRITERION_ID = "NS-05"
SOURCE_NAME_OSM = "osm_overpass_site_area"
SOURCE_NAME_CORINE = "corine_clc_site_area"

# CLC class 121 = Industrial or commercial units
_CLC_INDUSTRIAL = "121"
_CORINE_BUFFER_M = 1000


@dataclass
class SiteEnrichmentSummary:
    """Per-site outcome within a batch run."""

    site_id: uuid.UUID
    site_name: str
    status: str  # "ok" | "error" | "cached" | "not_found"
    site_area_ha: float | None = None
    source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class BatchResult:
    """Aggregate outcome of a site-area batch enrichment run."""

    run_id: str
    total_sites: int = 0
    succeeded: int = 0
    failed: int = 0
    not_found: int = 0
    skipped_cached: int = 0
    corine_fallback: int = 0
    elapsed_s: float = 0.0
    per_site: list[SiteEnrichmentSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "not_found": self.not_found,
            "skipped_cached": self.skipped_cached,
            "corine_fallback": self.corine_fallback,
            "elapsed_s": round(self.elapsed_s, 1),
            "per_site": [
                {
                    "site_id": str(s.site_id),
                    "site_name": s.site_name,
                    "status": s.status,
                    "site_area_ha": s.site_area_ha,
                    "source": s.source,
                    "error": s.error,
                    "elapsed_ms": s.elapsed_ms,
                }
                for s in self.per_site
            ],
        }

    def summary_line(self) -> str:
        mins = self.elapsed_s / 60
        elapsed = f"{mins:.1f} min" if mins >= 1 else f"{self.elapsed_s:.1f} s"
        return (
            f"{self.total_sites} sites: {self.succeeded} ok, "
            f"{self.not_found} not_found, {self.failed} failed, "
            f"{self.skipped_cached} cached, {self.corine_fallback} corine_fallback "
            f"({elapsed})"
        )


class SiteAreaEnricher:
    """Enriches site area data using OSM Overpass with CORINE CLC fallback."""

    def __init__(
        self,
        settings: Any | None = None,
        *,
        cache_ttl_days: int = 365,
        inter_request_delay: float = 2.0,
    ) -> None:
        self._overpass = OverpassClient(settings)
        self._corine = CorineConnector(settings)
        self._cache_ttl_days = cache_ttl_days
        self._inter_request_delay = inter_request_delay

    def close(self) -> None:
        self._overpass.close()
        self._corine.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def health_check(self) -> dict[str, bool]:
        return {
            "osm": self._overpass.health_check(),
            "corine": self._corine.health_check(),
        }

    # ------------------------------------------------------------------
    # Single-site enrichment
    # ------------------------------------------------------------------

    def enrich_site(
        self,
        site_id: uuid.UUID,
        session: Session,
        run_id: str,
    ) -> SiteEnrichmentSummary:
        """Fetch and persist site area for a single DB site."""
        site = session.get(Site, site_id)
        if site is None:
            return SiteEnrichmentSummary(
                site_id=site_id, site_name="<unknown>", status="error",
                error=f"Site {site_id} not found",
            )

        t0 = time.monotonic()

        cached = self._check_cache(session, site_id, run_id)
        if cached:
            elapsed = int((time.monotonic() - t0) * 1000)
            return SiteEnrichmentSummary(
                site_id=site_id, site_name=site.name, status="cached",
                site_area_ha=float(site.site_area_ha) if site.site_area_ha else None,
                source="cached", elapsed_ms=elapsed,
            )

        try:
            result = self._fetch_with_fallback(
                float(site.latitude), float(site.longitude),
                site.country_code,
            )
            self._persist(session, site, result, run_id)
            session.commit()
            elapsed = int((time.monotonic() - t0) * 1000)

            status = "ok" if result.site_area_ha else "not_found"
            return SiteEnrichmentSummary(
                site_id=site_id, site_name=site.name, status=status,
                site_area_ha=result.site_area_ha,
                source=result.source, elapsed_ms=elapsed,
            )
        except Exception as exc:
            session.rollback()
            self._persist_error(session, site_id, run_id, str(exc))
            session.commit()
            elapsed = int((time.monotonic() - t0) * 1000)
            log.error("site_area_error", site_id=str(site_id), error=str(exc))
            return SiteEnrichmentSummary(
                site_id=site_id, site_name=site.name, status="error",
                error=str(exc), elapsed_ms=elapsed,
            )

    # ------------------------------------------------------------------
    # Batch enrichment
    # ------------------------------------------------------------------

    def enrich_batch(
        self,
        session: Session,
        run_id: str,
        *,
        site_ids: list[uuid.UUID] | None = None,
        country_codes: list[str] | None = None,
    ) -> BatchResult:
        batch = BatchResult(run_id=run_id)
        batch_start = time.monotonic()

        query = session.query(Site)
        if site_ids is not None:
            if not site_ids:
                return batch
            query = query.filter(Site.site_id.in_(site_ids))
        elif country_codes is not None:
            query = query.filter(Site.country_code.in_(country_codes))

        sites = query.order_by(Site.country_code, Site.name).all()
        batch.total_sites = len(sites)
        if not sites:
            return batch

        ensure_data_source(
            session, name=SOURCE_NAME_OSM,
            url="https://overpass-api.de/api/interpreter",
            description="OSM Overpass for FIX-03 site area enrichment",
        )

        for i, site in enumerate(sites):
            site_start = time.monotonic()

            cached = self._check_cache(session, site.site_id, run_id)
            if cached:
                batch.skipped_cached += 1
                elapsed_ms = int((time.monotonic() - site_start) * 1000)
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name, status="cached",
                    site_area_ha=float(site.site_area_ha) if site.site_area_ha else None,
                    source="cached", elapsed_ms=elapsed_ms,
                ))
                continue

            try:
                result = self._fetch_with_fallback(
                    float(site.latitude), float(site.longitude),
                    site.country_code,
                )
                self._persist(session, site, result, run_id)
                session.commit()

                elapsed_ms = int((time.monotonic() - site_start) * 1000)

                if result.site_area_ha:
                    batch.succeeded += 1
                    status = "ok"
                else:
                    batch.not_found += 1
                    status = "not_found"

                if result.source == "corine_clc_121":
                    batch.corine_fallback += 1

                log.info(
                    "site_area_enrich_ok",
                    site_id=str(site.site_id), site_name=site.name,
                    index=i + 1, total=len(sites),
                    area_ha=result.site_area_ha,
                    source=result.source,
                    elapsed_ms=elapsed_ms,
                )
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name, status=status,
                    site_area_ha=result.site_area_ha,
                    source=result.source, elapsed_ms=elapsed_ms,
                ))

            except Exception as exc:
                session.rollback()
                log.error(
                    "site_area_enrich_error",
                    site_id=str(site.site_id), error=str(exc),
                )
                self._persist_error(session, site.site_id, run_id, str(exc))
                session.commit()
                batch.failed += 1
                elapsed_ms = int((time.monotonic() - site_start) * 1000)
                batch.per_site.append(SiteEnrichmentSummary(
                    site_id=site.site_id, site_name=site.name, status="error",
                    error=str(exc), elapsed_ms=elapsed_ms,
                ))

            if (i + 1) % 25 == 0:
                log.info(
                    "site_area_batch_progress",
                    completed=i + 1, total=len(sites),
                    succeeded=batch.succeeded, failed=batch.failed,
                    not_found=batch.not_found,
                    elapsed_s=round(time.monotonic() - batch_start, 1),
                )

            time.sleep(self._inter_request_delay)

        batch.elapsed_s = time.monotonic() - batch_start
        log.info(
            "site_area_batch_done", run_id=run_id,
            total=batch.total_sites, succeeded=batch.succeeded,
            failed=batch.failed, not_found=batch.not_found,
            cached=batch.skipped_cached, corine_fallback=batch.corine_fallback,
            elapsed_s=round(batch.elapsed_s, 1),
        )
        return batch

    def enrich_all(self, session: Session, run_id: str) -> BatchResult:
        return self.enrich_batch(session, run_id)

    # ------------------------------------------------------------------
    # Internal: fetch strategies
    # ------------------------------------------------------------------

    def _fetch_with_fallback(
        self,
        lat: float,
        lon: float,
        country_code: str,
    ) -> SiteAreaResult:
        """Try OSM first, then CORINE fallback for EU countries."""
        result = self._overpass.fetch_site_area_with_retry(lat, lon)

        if result.site_area_ha is not None:
            return result

        log.info("site_area_fetch_fallback", lat=lat, lon=lon, reason=result.error)

        if country_code in CORINE_COVERED_COUNTRIES:
            corine_result = self._corine_fallback(lat, lon)
            if corine_result is not None:
                return corine_result

        return SiteAreaResult(
            error=f"No polygon found (OSM: {result.error}; CORINE: {'N/A — non-EU' if country_code not in CORINE_COVERED_COUNTRIES else 'no CLC 121'})",
            quality="not_found",
            source="none",
        )

    def _corine_fallback(self, lat: float, lon: float) -> SiteAreaResult | None:
        """Use CORINE CLC class 121 (Industrial/commercial) as fallback."""
        features = self._corine.fetch(lat, lon, radius_m=_CORINE_BUFFER_M)
        if not features:
            return None

        parsed = parse_clc_features(features)
        if not parsed:
            return None

        search_circle = buffer_circle_wgs84(lat, lon, _CORINE_BUFFER_M)

        industrial_area_ha = 0.0
        largest_patch_ha = 0.0
        patch_count = 0

        for feat_geom, clc_code in parsed:
            if clc_code != _CLC_INDUSTRIAL:
                continue
            try:
                clipped = search_circle.intersection(feat_geom)
                if clipped.is_empty:
                    continue
                area = geodesic_area_ha(clipped)
                industrial_area_ha += area
                largest_patch_ha = max(largest_patch_ha, area)
                patch_count += 1
            except Exception:
                continue

        if patch_count == 0:
            return None

        log.info(
            "site_area_corine_fallback_ok",
            lat=lat, lon=lon,
            area_ha=round(industrial_area_ha, 2),
            patches=patch_count,
        )

        return SiteAreaResult(
            site_area_ha=industrial_area_ha,
            buildable_area_ha=industrial_area_ha,
            largest_contiguous_ha=largest_patch_ha,
            candidate_count=patch_count,
            source="corine_clc_121",
            quality="medium",
        )

    # ------------------------------------------------------------------
    # Internal: persistence
    # ------------------------------------------------------------------

    def _check_cache(
        self,
        session: Session,
        site_id: uuid.UUID,
        run_id: str,
    ) -> bool:
        """Return True if site already has fresh site_area_ha data.

        Cache is valid if the data exists, quality is not 'not_found',
        and the data is younger than ``cache_ttl_days``.
        """
        infra = session.get(SiteInfrastructureV2, site_id)
        if infra is None or infra.ns05_quality in (None, "not_found"):
            return False
        if infra.fetched_at is None:
            return False
        from datetime import timedelta
        age = datetime.now(timezone.utc) - infra.fetched_at
        return age.days < self._cache_ttl_days

    def _persist(
        self,
        session: Session,
        site: Site,
        result: SiteAreaResult,
        run_id: str,
    ) -> None:
        """Write site area results to sites + site_infrastructure_v2."""
        now = datetime.now(timezone.utc)

        if result.site_area_ha is not None:
            site.site_area_ha = result.site_area_ha

        infra = session.get(SiteInfrastructureV2, site.site_id)
        if infra is None:
            infra = SiteInfrastructureV2(site_id=site.site_id)
            session.add(infra)

        infra.buildable_area_ha = result.buildable_area_ha
        infra.largest_contiguous_ha = result.largest_contiguous_ha
        infra.ns05_quality = result.quality
        infra.ns05_comment = _build_comment(result)
        infra.fetched_at = now
        infra.run_id = run_id

        source_name = SOURCE_NAME_OSM if result.source != "corine_clc_121" else SOURCE_NAME_CORINE
        ensure_data_source(
            session, name=source_name,
            url="https://overpass-api.de/api/interpreter" if source_name == SOURCE_NAME_OSM else "https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer",
            description=f"Site area enrichment ({source_name})",
        )

        if result.quality == "not_found":
            write_observation(
                session, site_id=site.site_id, criterion_id=CRITERION_ID,
                observation=f"No site area polygon found. {result.error or ''}".strip(),
                run_id=run_id, confidence="low", impact="negative",
            )

    def _persist_error(
        self,
        session: Session,
        site_id: uuid.UUID,
        run_id: str,
        error: str,
    ) -> None:
        write_observation(
            session, site_id=site_id, criterion_id=CRITERION_ID,
            observation=f"Site area enrichment failed: {error}",
            run_id=run_id, confidence="low", impact="blocking",
        )


def _build_comment(result: SiteAreaResult) -> str:
    """Build a human-readable comment for ns05_comment."""
    parts: list[str] = [f"source={result.source}"]
    if result.osm_id:
        parts.append(f"osm_id={result.osm_type}/{result.osm_id}")
    if result.source_tags:
        tag_str = ", ".join(f"{k}={v}" for k, v in result.source_tags.items()
                           if k in ("name", "landuse", "power", "man_made", "industrial"))
        if tag_str:
            parts.append(f"tags=[{tag_str}]")
    if result.distance_km:
        parts.append(f"dist={result.distance_km:.2f}km")
    if result.candidate_count > 1:
        parts.append(f"candidates={result.candidate_count}")
    return "; ".join(parts)
