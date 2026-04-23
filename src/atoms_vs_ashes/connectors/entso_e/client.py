# man_hours: 5.0
"""ENTSO-E Transparency Platform connector.

Fetches zone-level grid capacity data (A68, A71, A61, A11) and maps
sites to their bidding zone for NS-02 grid connection assessment.
"""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.http_audit import ConnectorHttpAuditLogger
from atoms_vs_ashes.connectors.entso_e.models import (
    BIDDING_ZONES,
    DEFAULT_API_URL,
    EIC_TO_COUNTRY,
    SOURCE_NAME,
    ZONE_DISPLAY_NAMES,
    BatchResult,
    EntsoEResult,
    ZoneGridAssessment,
    ZoneIngestionResult,
)
from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
from atoms_vs_ashes.connectors.entso_e.parsers import (
    assess_nuclear_readiness,
    compute_capacity_metrics,
    compute_interconnection_metrics,
    determine_quality,
    identify_bidding_zone,
    is_acknowledgement,
    parse_flows_xml,
    parse_generation_units_xml,
    parse_installed_capacity_xml,
    parse_ntc_xml,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_TIMEOUT_S = 30
_INTER_REQUEST_DELAY_S = 0.2
_MAX_RETRIES = 3
_RETRY_BASE_S = 2.0
_RETRY_MAX_S = 60.0
_CACHE_TTL_DAYS = 180
_REFERENCE_YEAR = 2025
_FLOW_SAMPLE_MONTHS = 1


class EntsoEConnector:
    """ENTSO-E Transparency Platform connector for NS-02 grid capacity."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get("entso_e", {})

        self._api_url: str = cfg.get("api_url", DEFAULT_API_URL)
        token = cfg.get("security_token")
        if not (isinstance(token, str) and token.strip()):
            token = os.environ.get("ENTSOE_SECURITY_TOKEN")
        self._token: str | None = (
            token.strip() if isinstance(token, str) and token.strip() else None
        )
        self._timeout: int = cfg.get("timeout_s", _TIMEOUT_S)
        self._delay: float = cfg.get("inter_request_delay_s", _INTER_REQUEST_DELAY_S)
        self._cache_dir: Path = Path(cfg.get("cache_dir", "sources/entso_e"))
        self._cache_ttl_days: int = cfg.get("cache_ttl_days", _CACHE_TTL_DAYS)
        self._reference_year: int = cfg.get("reference_year", _REFERENCE_YEAR)
        self._flow_sample_months: int = cfg.get("flow_sample_months", _FLOW_SAMPLE_MONTHS)

        self._bidding_zones: dict[str, str] = cfg.get("bidding_zones", BIDDING_ZONES)
        self._interconnectors: list[list[str]] = cfg.get("interconnectors", [])

        thresholds = cfg.get("nuclear_readiness_thresholds", {})
        self._large_unit_threshold_mw: int = thresholds.get("large_unit_threshold_mw", 400)

        self._client = httpx.Client(timeout=self._timeout)
        self._zone_assessments: dict[str, ZoneGridAssessment] = {}
        self._zones_loaded = False
        self._audit: ConnectorHttpAuditLogger | None = None

    def enable_audit_log(self, run_id: str) -> None:
        """Enable file-based HTTP audit logging under ``logs/entso_e/<run_id>/``."""
        self._audit = ConnectorHttpAuditLogger("entso_e", run_id)
        log.info("entsoe_audit_enabled", log_dir=str(self._audit.base_dir))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify API connectivity and token validity with a small test query."""
        if not self._token:
            log.warning("entsoe_no_token", msg="No security token configured")
            return False
        params = {
            "securityToken": self._token,
            "documentType": "A68",
            "processType": "A33",
            "in_Domain": "10YRO-TEL------P",
            "periodStart": f"{self._reference_year}01010000",
            "periodEnd": f"{self._reference_year}02010000",
        }
        audit_params = {k: str(v) for k, v in params.items()}
        t0 = time.monotonic()
        try:
            resp = self._client.get(self._api_url, params=params)
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            if self._audit:
                self._audit.log(
                    url=self._api_url,
                    params=audit_params,
                    response=resp,
                    attempt=1,
                    elapsed_ms=elapsed_ms,
                    endpoint_slug="health_A68",
                )
            if resp.status_code in (200, 204):
                ack, _ = is_acknowledgement(resp.text)
                if not ack:
                    log.info("entsoe_health_ok", status=resp.status_code)
                    return True
                log.info("entsoe_health_ok_ack", msg="Token valid but no data for test query")
                return True
            log.warning("entsoe_health_fail", status=resp.status_code)
            return False
        except httpx.HTTPError as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            if self._audit:
                self._audit.log(
                    url=self._api_url,
                    params=audit_params,
                    response=None,
                    error=str(exc),
                    attempt=1,
                    elapsed_ms=elapsed_ms,
                    endpoint_slug="health_A68",
                )
            log.error("entsoe_health_error", error=str(exc))
            return False

    def fetch(self, lat: float, lon: float, **params: Any) -> EntsoEResult:
        """Fetch grid assessment for a single site (zone lookup + unit matching).

        Parameters
        ----------
        lat, lon
            Site coordinates (WGS84).
        country_code
            Optional ISO 3166-1 alpha-2 code. If not provided, must be
            inferred from zone assessments (not implemented — pass explicitly).
        site_name
            Site name for fuzzy matching against A71 generation units.
        alternative_names
            Additional name variants to try during fuzzy matching.
        """
        country_code = params.get("country_code", "")
        if not country_code:
            return EntsoEResult(
                lat=lat, lon=lon,
                error="country_code required for zone lookup",
            )

        zone_eic = identify_bidding_zone(country_code, self._bidding_zones)
        if not zone_eic:
            return EntsoEResult(
                lat=lat, lon=lon, country_code=country_code,
                error=f"No bidding zone mapped for country {country_code}",
            )

        zone_name = f"{ZONE_DISPLAY_NAMES.get(country_code, country_code)} ({country_code})"

        assessment = self._zone_assessments.get(zone_eic)
        if assessment is None:
            return EntsoEResult(
                lat=lat, lon=lon,
                country_code=country_code,
                bidding_zone_eic=zone_eic,
                bidding_zone_name=zone_name,
                nuclear_readiness="insufficient",
                quality="insufficient",
                error="Zone data not loaded — call ingest_zones() first",
            )

        per_unit = None
        site_name = params.get("site_name", "")
        alternative_names = params.get("alternative_names")
        installed_mw = params.get("installed_capacity_mw")
        if site_name and assessment.units:
            per_unit = match_entsoe_units(
                site_name, alternative_names, assessment.units,
                installed_capacity_mw=installed_mw,
            )

        return EntsoEResult(
            lat=lat, lon=lon,
            country_code=country_code,
            bidding_zone_eic=zone_eic,
            bidding_zone_name=zone_name,
            capacity=assessment.capacity,
            interconnection=assessment.interconnection,
            per_unit_match=per_unit,
            nuclear_readiness=assessment.nuclear_readiness,
            reference_year=assessment.reference_year,
            quality=assessment.quality,
        )

    def ingest_zones(
        self,
        year: int | None = None,
    ) -> ZoneIngestionResult:
        """Query ENTSO-E API for all 23 bidding zones and compute assessments.

        This is the network-heavy phase. Run once per analysis year;
        results are cached in memory and optionally on disk.
        """
        year = year or self._reference_year
        result = ZoneIngestionResult()

        cached = self._load_cached_assessments(year)
        if cached:
            self._zone_assessments = cached
            self._zones_loaded = True
            result.n_zones_queried = len(cached)
            result.n_zones_with_data = sum(
                1 for z in cached.values() if z.quality != "insufficient"
            )
            result.n_zones_no_data = result.n_zones_queried - result.n_zones_with_data
            log.info("entsoe_zones_from_cache", n_zones=len(cached))
            return result

        t0 = time.monotonic()

        for country_code, zone_eic in self._bidding_zones.items():
            result.n_zones_queried += 1
            zone_name = f"{ZONE_DISPLAY_NAMES.get(country_code, country_code)} ({country_code})"

            try:
                assessment = self._query_zone(zone_eic, country_code, zone_name, year)
                self._zone_assessments[zone_eic] = assessment

                if assessment.quality != "insufficient":
                    result.n_zones_with_data += 1
                else:
                    result.n_zones_no_data += 1

                log.info(
                    "entsoe_zone_complete",
                    zone_eic=zone_eic, country=country_code,
                    quality=assessment.quality,
                    readiness=assessment.nuclear_readiness,
                    total_mw=(
                        assessment.capacity.total_installed_mw
                        if assessment.capacity else 0
                    ),
                )
            except Exception as exc:
                log.error(
                    "entsoe_zone_error",
                    zone_eic=zone_eic, country=country_code,
                    error=str(exc),
                )
                self._zone_assessments[zone_eic] = ZoneGridAssessment(
                    zone_eic=zone_eic,
                    zone_name=zone_name,
                    country_code=country_code,
                    reference_year=year,
                    quality="insufficient",
                    queried_at=datetime.now(timezone.utc),
                )
                result.n_zones_no_data += 1

        self._zones_loaded = True
        result.elapsed_s = time.monotonic() - t0

        self._save_cached_assessments(year)

        log.info(
            "entsoe_ingest_done",
            n_queried=result.n_zones_queried,
            n_with_data=result.n_zones_with_data,
            n_no_data=result.n_zones_no_data,
            elapsed_s=round(result.elapsed_s, 1),
        )
        return result

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EntsoEConnector:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Zone query orchestration
    # ------------------------------------------------------------------

    def _query_zone(
        self,
        zone_eic: str,
        country_code: str,
        zone_name: str,
        year: int,
    ) -> ZoneGridAssessment:
        """Query all data products for a single zone and compute assessment."""
        has_a68 = False
        has_a71 = False
        has_ntc = False
        has_flows = False

        # A68: Installed capacity aggregated
        capacity_agg = None
        xml = self._query_api({
            "documentType": "A68",
            "processType": "A33",
            "in_Domain": zone_eic,
            "periodStart": f"{year}01010000",
            "periodEnd": f"{year + 1}01010000",
        })
        if xml:
            ack, reason = is_acknowledgement(xml)
            if ack:
                log.info("entsoe_no_data", zone_eic=zone_eic, document="A68", reason=reason)
            else:
                capacity_agg = parse_installed_capacity_xml(xml, zone_eic, year)
                has_a68 = len(capacity_agg.entries) > 0

        # A71: Per-unit capacity
        units = None
        if has_a68:
            xml = self._query_api({
                "documentType": "A71",
                "processType": "A33",
                "in_Domain": zone_eic,
                "periodStart": f"{year}01010000",
                "periodEnd": f"{year + 1}01010000",
            })
            if xml:
                ack, _ = is_acknowledgement(xml)
                if not ack:
                    units = parse_generation_units_xml(xml, zone_eic)
                    has_a71 = len(units) > 0

        # Capacity metrics
        capacity_metrics = None
        if capacity_agg and has_a68:
            capacity_metrics = compute_capacity_metrics(capacity_agg, units)

        # NTC: Year-ahead for interconnectors touching this zone
        ntc_list = []
        zone_interconnectors = self._get_zone_interconnectors(zone_eic)
        for from_eic, to_eic in zone_interconnectors:
            xml = self._query_api({
                "documentType": "A61",
                "processType": "A01",
                "in_Domain": from_eic,
                "out_Domain": to_eic,
                "periodStart": f"{year}01010000",
                "periodEnd": f"{year + 1}01010000",
            })
            if xml:
                ack, _ = is_acknowledgement(xml)
                if not ack:
                    ntc = parse_ntc_xml(xml, from_eic, to_eic)
                    if ntc.entries:
                        ntc_list.append(ntc)
                        has_ntc = True

        # Flows: Sample one month
        flow_list = []
        if has_ntc and self._flow_sample_months > 0:
            for from_eic, to_eic in zone_interconnectors[:3]:
                xml = self._query_api({
                    "documentType": "A11",
                    "processType": "A16",
                    "in_Domain": from_eic,
                    "out_Domain": to_eic,
                    "periodStart": f"{year}01010000",
                    "periodEnd": f"{year}02010000",
                })
                if xml:
                    ack, _ = is_acknowledgement(xml)
                    if not ack:
                        flows = parse_flows_xml(xml, from_eic, to_eic)
                        if flows.entries:
                            flow_list.append(flows)
                            has_flows = True

        # Interconnection metrics
        interconnection = None
        if ntc_list:
            interconnection = compute_interconnection_metrics(
                ntc_list, flow_list,
                total_installed_mw=(
                    capacity_metrics.total_installed_mw
                    if capacity_metrics else 0.0
                ),
            )

        readiness = assess_nuclear_readiness(capacity_metrics, interconnection)
        quality = determine_quality(has_a68, has_a71, has_ntc, has_flows)

        return ZoneGridAssessment(
            zone_eic=zone_eic,
            zone_name=zone_name,
            country_code=country_code,
            reference_year=year,
            capacity=capacity_metrics,
            interconnection=interconnection,
            units=units if has_a71 else None,
            nuclear_readiness=readiness,
            quality=quality,
            queried_at=datetime.now(timezone.utc),
        )

    def _get_zone_interconnectors(
        self, zone_eic: str,
    ) -> list[tuple[str, str]]:
        """Return interconnector pairs where this zone is the 'from' side."""
        pairs: list[tuple[str, str]] = []
        for pair in self._interconnectors:
            if len(pair) == 2:
                if pair[0] == zone_eic:
                    pairs.append((pair[0], pair[1]))
                elif pair[1] == zone_eic:
                    pairs.append((pair[1], pair[0]))
        return pairs

    # ------------------------------------------------------------------
    # HTTP query with retry
    # ------------------------------------------------------------------

    def _query_api(self, params: dict[str, str]) -> str | None:
        """Execute a single ENTSO-E API query with retry and rate limiting."""
        if not self._token:
            log.warning("entsoe_no_token", params=params)
            return None

        full_params = {"securityToken": self._token, **params}
        audit_params = {k: str(v) for k, v in full_params.items()}
        doc = params.get("documentType", "api")

        for attempt in range(_MAX_RETRIES):
            t_req: float | None = None
            try:
                time.sleep(self._delay)
                t_req = time.monotonic()
                resp = self._client.get(self._api_url, params=full_params)
                elapsed_ms = int((time.monotonic() - t_req) * 1000)
                if self._audit:
                    self._audit.log(
                        url=self._api_url,
                        params=audit_params,
                        response=resp,
                        attempt=attempt + 1,
                        elapsed_ms=elapsed_ms,
                        endpoint_slug=str(doc),
                    )

                if resp.status_code == 200:
                    return resp.text

                if resp.status_code in (401, 403):
                    log.error(
                        "entsoe_auth_error",
                        status=resp.status_code,
                        document_type=params.get("documentType"),
                    )
                    return None

                if resp.status_code == 429:
                    delay = _retry_delay(attempt)
                    log.warning(
                        "entsoe_rate_limited",
                        attempt=attempt + 1, delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue

                if resp.status_code == 400:
                    log.warning(
                        "entsoe_bad_request",
                        status=400,
                        document_type=params.get("documentType"),
                        body=resp.text[:500],
                    )
                    return None

                if resp.status_code in (502, 503, 504):
                    delay = _retry_delay(attempt)
                    log.warning(
                        "entsoe_server_error",
                        status=resp.status_code, attempt=attempt + 1,
                        delay_s=round(delay, 1),
                    )
                    time.sleep(delay)
                    continue

                log.warning(
                    "entsoe_unexpected_status",
                    status=resp.status_code,
                    document_type=params.get("documentType"),
                )
                return None

            except httpx.TimeoutException as exc:
                elapsed_ms = (
                    int((time.monotonic() - t_req) * 1000)
                    if t_req is not None
                    else 0
                )
                if self._audit:
                    self._audit.log(
                        url=self._api_url,
                        params=audit_params,
                        response=None,
                        error=str(exc),
                        attempt=attempt + 1,
                        elapsed_ms=elapsed_ms,
                        endpoint_slug=str(doc),
                    )
                delay = _retry_delay(attempt)
                log.warning(
                    "entsoe_timeout",
                    attempt=attempt + 1, delay_s=round(delay, 1),
                    error=str(exc),
                )
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(delay)
                continue

            except httpx.HTTPError as exc:
                elapsed_ms = (
                    int((time.monotonic() - t_req) * 1000)
                    if t_req is not None
                    else 0
                )
                if self._audit:
                    self._audit.log(
                        url=self._api_url,
                        params=audit_params,
                        response=None,
                        error=str(exc),
                        attempt=attempt + 1,
                        elapsed_ms=elapsed_ms,
                        endpoint_slug=str(doc),
                    )
                log.warning("entsoe_network_error", error=str(exc))
                return None

        log.error(
            "entsoe_retries_exhausted",
            document_type=params.get("documentType"),
            max_retries=_MAX_RETRIES,
        )
        return None

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _load_cached_assessments(
        self, year: int,
    ) -> dict[str, ZoneGridAssessment] | None:
        """Load cached zone assessments from disk if fresh."""
        cache_file = self._cache_dir / "assessments" / f"zones_{year}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            age_days = (datetime.now(timezone.utc) - cached_at).days
            if age_days > self._cache_ttl_days:
                log.info("entsoe_cache_stale", age_days=age_days)
                return None

            assessments: dict[str, ZoneGridAssessment] = {}
            for zone_data in data.get("zones", []):
                assessment = _deserialize_zone_assessment(zone_data)
                assessments[assessment.zone_eic] = assessment

            log.info("entsoe_cache_loaded", n_zones=len(assessments), age_days=age_days)
            return assessments

        except Exception as exc:
            log.warning("entsoe_cache_load_error", error=str(exc))
            return None

    def _save_cached_assessments(self, year: int) -> None:
        """Save zone assessments to disk cache."""
        cache_dir = self._cache_dir / "assessments"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"zones_{year}.json"

        try:
            data = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "year": year,
                "zones": [a.to_dict() for a in self._zone_assessments.values()],
            }
            cache_file.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            log.info("entsoe_cache_saved", path=str(cache_file))
        except Exception as exc:
            log.warning("entsoe_cache_save_error", error=str(exc))


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _retry_delay(attempt: int, base: float = _RETRY_BASE_S, max_delay: float = _RETRY_MAX_S) -> float:
    delay = min(base * (2 ** attempt), max_delay)
    return delay * (0.5 + random.random() * 0.5)


def _deserialize_zone_assessment(data: dict[str, Any]) -> ZoneGridAssessment:
    """Reconstruct a ZoneGridAssessment from cached JSON dict."""
    from atoms_vs_ashes.connectors.entso_e.models import (
        CapacityMetrics,
        GenerationUnit,
        InterconnectionMetrics,
        InterconnectorSummary,
        PSR_TYPE_NAMES,
    )

    capacity = None
    if data.get("capacity"):
        c = data["capacity"]
        capacity = CapacityMetrics(
            total_installed_mw=c.get("total_installed_mw", 0),
            thermal_installed_mw=c.get("thermal_installed_mw", 0),
            nuclear_installed_mw=c.get("nuclear_installed_mw", 0),
            hydro_installed_mw=c.get("hydro_installed_mw", 0),
            wind_solar_installed_mw=c.get("wind_solar_installed_mw", 0),
            other_installed_mw=c.get("other_installed_mw", 0),
            capacity_by_type=c.get("capacity_by_type", {}),
            largest_unit_mw=c.get("largest_unit_mw"),
            largest_unit_name=c.get("largest_unit_name"),
            largest_unit_type=c.get("largest_unit_type"),
            units_above_400mw=c.get("units_above_400mw", 0),
            units_above_200mw=c.get("units_above_200mw", 0),
            nuclear_units=c.get("nuclear_units", 0),
            coal_units_above_200mw=c.get("coal_units_above_200mw", 0),
            has_nuclear_precedent=c.get("has_nuclear_precedent", False),
            smr_capacity_ratio=c.get("smr_capacity_ratio", 0),
        )

    interconnection = None
    if data.get("interconnection"):
        ic = data["interconnection"]
        neighbours = [
            InterconnectorSummary(
                neighbour_eic=n.get("neighbour_eic", ""),
                neighbour_name=n.get("neighbour_name", ""),
                ntc_export_mw=n.get("ntc_export_mw"),
                ntc_import_mw=n.get("ntc_import_mw"),
                mean_flow_mw=n.get("mean_flow_mw"),
                max_flow_mw=n.get("max_flow_mw"),
            )
            for n in ic.get("neighbours", [])
        ]
        interconnection = InterconnectionMetrics(
            n_interconnectors=ic.get("n_interconnectors", 0),
            total_ntc_export_mw=ic.get("total_ntc_export_mw", 0),
            total_ntc_import_mw=ic.get("total_ntc_import_mw", 0),
            max_single_interconnector_mw=ic.get("max_single_interconnector_mw", 0),
            interconnection_ratio=ic.get("interconnection_ratio", 0),
            neighbours=neighbours,
        )

    units = None
    if data.get("units"):
        units = [
            GenerationUnit(
                unit_name=u.get("unit_name", "Unknown"),
                unit_eic=u.get("unit_eic"),
                psr_type=u.get("psr_type", "B20"),
                psr_name=u.get("psr_name", PSR_TYPE_NAMES.get(u.get("psr_type", "B20"), "Other")),
                installed_mw=u.get("installed_mw", 0),
                voltage_kv=u.get("voltage_kv"),
                zone_eic=data.get("zone_eic", ""),
            )
            for u in data["units"]
        ]

    return ZoneGridAssessment(
        zone_eic=data.get("zone_eic", ""),
        zone_name=data.get("zone_name", ""),
        country_code=data.get("country_code", ""),
        reference_year=data.get("reference_year", 0),
        capacity=capacity,
        interconnection=interconnection,
        units=units,
        nuclear_readiness=data.get("nuclear_readiness", "insufficient"),
        quality=data.get("quality", "insufficient"),
    )
