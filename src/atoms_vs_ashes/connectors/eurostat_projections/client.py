# man_hours: 6.0
"""S-17 Eurostat Demographic Projections connector.

Two-phase execution:
  Phase A — data ingestion (API queries + local NSO file loading, cached)
  Phase B — per-site computation (NUTS lookup + growth trajectory, ~0.1 ms/site)

Data sources:
  - EUROPOP2023 national projections (proj_23np) for EU-12 countries
  - EUROPOP2023 demographic indicators (proj_23ndbi)
  - EUROPOP2019 regional projections (proj_19rp3) for NUTS3 regions
  - Regional demographics (DEMO_R_PJANGRP3, DEMO_R_GIND3)
  - Regional economics (NAMA_10R_3POPGDP, LFST_R_LFE2EN2N, EDAT_LFSE_04)
  - NSO supplement files for non-EU countries (sources/nso_projections/*.json)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from atoms_vs_ashes.connectors.eurostat_projections.models import (
    IN_SCOPE_CANDIDATE,
    IN_SCOPE_EU,
    IN_SCOPE_NON_EU,
    STATISTICS_API_URL,
    EurostatProjectionsResult,
    IngestionResult,
    NsoProjection,
    PolicyProxyResult,
    PopulationProjectionResult,
    SocioeconomicResult,
    WorkforceResult,
)
from atoms_vs_ashes.connectors.eurostat_projections.parsers import (
    classify_growth,
    compute_deprivation_index,
    compute_growth_trajectory,
    compute_pop_change_pct_per_decade,
    compute_receptor_growth_factor,
    compute_retraining_pool_index,
    compute_urban_expansion_pressure,
    parse_jsonstat_employment,
    parse_jsonstat_indicators,
    parse_jsonstat_projection,
    parse_jsonstat_tabular,
    parse_nso_supplement,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_DEFAULT_CACHE_DIR = "sources/eurostat_projections"
_DEFAULT_NSO_DIR = "sources/nso_projections"
_DEFAULT_TIMEOUT_S = 30
_DEFAULT_INTER_REQUEST_DELAY = 0.5
_DEFAULT_PROJ_TTL_DAYS = 365
_DEFAULT_STATS_TTL_DAYS = 90

_EU12 = sorted(IN_SCOPE_EU)
_PROJECTION_YEARS_NATIONAL = ["2030", "2040", "2050", "2060", "2070", "2080"]
_PROJECTION_YEARS_REGIONAL = ["2030", "2040", "2050"]
_INDICATOR_CODES = ["MEDAGEPOP", "OLDDEP", "CNMIGRATRT", "NATGROWRT", "GROWRT"]

_NUTS_GEOJSON_PATH = "nuts/geojson/NUTS_RG_01M_2021_4326.geojson"

_DEFAULT_NUCLEAR_POLICY: dict[str, str] = {
    "PL": "favourable",
    "CZ": "favourable",
    "SK": "favourable",
    "HU": "favourable",
    "AT": "unfavourable",
    "SI": "neutral",
    "HR": "neutral",
    "BA": "unknown",
    "RS": "neutral",
    "ME": "unknown",
    "XK": "unknown",
    "AL": "unknown",
    "MK": "unknown",
    "RO": "favourable",
    "BG": "favourable",
    "MD": "unknown",
    "UA": "favourable",
    "BY": "favourable",
    "EE": "neutral",
    "LV": "neutral",
    "LT": "neutral",
    "AM": "favourable",
    "TR": "favourable",
}


class EurostatProjectionsConnector:
    """Fetches Eurostat EUROPOP projections and computes RI-06/NS-09/NS-10/NS-12."""

    def __init__(self, settings: Any | None = None) -> None:
        cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            cfg = settings._yaml.get("connectors", {}).get(
                "eurostat_projections", {}
            )

        gisco_cfg: dict[str, Any] = {}
        if settings and hasattr(settings, "_yaml"):
            gisco_cfg = settings._yaml.get("connectors", {}).get(
                "eurostat_gisco", {}
            )

        self._api_url: str = cfg.get("statistics_api_url", STATISTICS_API_URL)
        self._gisco_url: str = gisco_cfg.get(
            "gisco_base_url",
            "https://gisco-services.ec.europa.eu/distribution/v2",
        )
        self._timeout: int = cfg.get("timeout_s", _DEFAULT_TIMEOUT_S)
        self._delay: float = cfg.get(
            "inter_request_delay_s", _DEFAULT_INTER_REQUEST_DELAY
        )
        self._cache_dir = Path(cfg.get("cache_dir", _DEFAULT_CACHE_DIR))
        self._nso_dir = Path(cfg.get("nso_supplement_dir", _DEFAULT_NSO_DIR))
        self._proj_ttl_days: int = cfg.get(
            "projection_cache_ttl_days", _DEFAULT_PROJ_TTL_DAYS
        )
        self._stats_ttl_days: int = cfg.get(
            "statistics_cache_ttl_days", _DEFAULT_STATS_TTL_DAYS
        )

        self._national_proj_dataset: str = cfg.get(
            "national_projection_dataset", "proj_23np"
        )
        self._indicators_dataset: str = cfg.get(
            "national_indicators_dataset", "proj_23ndbi"
        )
        self._regional_proj_dataset: str = cfg.get(
            "regional_projection_dataset", "proj_19rp3"
        )

        nuclear_policy_cfg = cfg.get("nuclear_policy", {})
        self._nuclear_policy: dict[str, str] = {
            **_DEFAULT_NUCLEAR_POLICY,
            **nuclear_policy_cfg,
        }

        self._client = httpx.Client(timeout=self._timeout)

        self._national_bsl: dict[str, dict[str, float]] = {}
        self._national_lmig: dict[str, dict[str, float]] = {}
        self._national_hmig: dict[str, dict[str, float]] = {}
        self._indicators: dict[str, dict[str, float]] = {}
        self._regional_proj: dict[str, dict[str, float]] = {}
        self._regional_pop_age: dict[str, dict[str, float]] = {}
        self._regional_gdp_capita: dict[str, float] = {}
        self._nuts2_employment: dict[str, dict[str, float]] = {}
        self._nuts2_education: dict[str, float] = {}
        self._nuts2_unemployment: dict[str, float] = {}
        self._nso_supplements: dict[str, NsoProjection] = {}
        self._nuts3_to_nuts2: dict[str, str] = {}
        self._nuts3_country: dict[str, str] = {}
        self._data_loaded = False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the Eurostat Statistics API is reachable."""
        try:
            url = f"{self._api_url}/data/{self._national_proj_dataset}"
            params = [
                ("format", "JSON"), ("lang", "en"),
                ("projection", "BSL"), ("sex", "T"), ("age", "TOTAL"),
                ("geo", "RO"), ("time", "2050"),
            ]
            resp = self._client.get(url, params=params, timeout=10)
            ok = resp.status_code < 500
            if ok:
                log.info("projections_health_ok", status=resp.status_code)
            else:
                log.warning("projections_health_error", status=resp.status_code)
            return ok
        except httpx.HTTPError as exc:
            log.warning("projections_health_error", error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Phase A: Data ingestion
    # ------------------------------------------------------------------

    def ingest_projections(
        self,
        reference_year: int = 2023,
    ) -> IngestionResult:
        """Fetch all projection + statistics data and cache locally.

        This is the Phase A operation — run once, then Phase B (per-site)
        is instant lookups into the loaded data.
        """
        result = IngestionResult()
        t0 = time.monotonic()

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._nso_dir.mkdir(parents=True, exist_ok=True)

        eu12 = _EU12
        nuts3_codes = self._get_known_nuts3_codes(eu12)
        nuts2_codes = list({c[:4] for c in nuts3_codes if len(c) >= 4})

        self._national_bsl = self._load_or_fetch_national_projections(
            eu12, _PROJECTION_YEARS_NATIONAL, "BSL",
        )
        if self._national_bsl:
            result.n_countries_with_projections += len(self._national_bsl)

        self._national_lmig = self._load_or_fetch_national_projections(
            eu12, ["2050", "2080"], "LMIG",
        )
        self._national_hmig = self._load_or_fetch_national_projections(
            eu12, ["2050", "2080"], "HMIG",
        )

        self._indicators = self._load_or_fetch_national_indicators(
            eu12, ["2030", "2050", "2080"], _INDICATOR_CODES,
        )

        if nuts3_codes:
            self._regional_proj = self._load_or_fetch_regional_projections(
                nuts3_codes, _PROJECTION_YEARS_REGIONAL,
            )
            result.n_regions_with_data += len(self._regional_proj)

            self._regional_pop_age = self._load_or_fetch_regional_demographics(
                nuts3_codes, reference_year,
            )

        if nuts2_codes:
            self._nuts2_employment = self._load_or_fetch_regional_employment(
                nuts2_codes, reference_year,
            )
            self._nuts2_education = self._load_or_fetch_regional_education(
                nuts2_codes, reference_year,
            )
            self._nuts2_unemployment = self._load_or_fetch_regional_unemployment(
                nuts2_codes, reference_year,
            )
            self._regional_gdp_capita = self._load_or_fetch_gdp_per_capita(
                nuts3_codes + nuts2_codes, reference_year,
            )

        self._nso_supplements = self._load_nso_supplements()
        result.n_nso_supplements_loaded = len(self._nso_supplements)

        self._data_loaded = True
        result.elapsed_s = time.monotonic() - t0
        log.info(
            "projections_ingest_done",
            countries=result.n_countries_with_projections,
            regions=result.n_regions_with_data,
            nso=result.n_nso_supplements_loaded,
            elapsed_s=round(result.elapsed_s, 1),
        )
        return result

    def _get_known_nuts3_codes(self, country_codes: list[str]) -> list[str]:
        """Load known NUTS3 codes from cached NUTS index or GISCO."""
        cache_path = self._cache_dir / "nuts3_codes.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        nuts3 = self._download_nuts3_codes(country_codes)
        with open(cache_path, "w") as f:
            json.dump(nuts3, f)
        return nuts3

    def _download_nuts3_codes(self, country_codes: list[str]) -> list[str]:
        """Download NUTS3 codes from GISCO (lightweight properties-only request)."""
        try:
            url = f"{self._gisco_url}/{_NUTS_GEOJSON_PATH}"
            log.info("projections_nuts_download_start", url=url)
            resp = self._client.get(url, timeout=120)
            if resp.status_code == 404:
                url = url.replace("NUTS_RG_01M_2021_4326", "NUTS_RG_20M_2021_4326")
                resp = self._client.get(url, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            nuts3: list[str] = []
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                lvl = props.get("LEVL_CODE")
                code = props.get("NUTS_ID", "")
                cntr = props.get("CNTR_CODE", "")
                if lvl == 3 and cntr in country_codes:
                    nuts3.append(code)
                    self._nuts3_country[code] = cntr
                    self._nuts3_to_nuts2[code] = code[:4]

            log.info("projections_nuts_loaded", count=len(nuts3))
            return nuts3
        except Exception as exc:
            log.warning("projections_nuts_download_error", error=str(exc))
            return []

    def _load_or_fetch_national_projections(
        self,
        country_codes: list[str],
        years: list[str],
        variant: str,
    ) -> dict[str, dict[str, float]]:
        """Load national projections from cache or Eurostat API."""
        cache_path = self._cache_dir / f"national_proj_{variant}.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                cached = json.load(f)
            if cached:
                log.info("projections_national_cached", variant=variant)
                return cached

        t0 = time.monotonic()
        params = [("format", "JSON"), ("lang", "en"),
                  ("projection", variant), ("sex", "T"), ("age", "TOTAL")]
        for cc in country_codes:
            params.append(("geo", cc))
        for yr in years:
            params.append(("time", yr))

        raw = self._query_api(self._national_proj_dataset, params)
        if raw is None:
            return {}

        result = parse_jsonstat_projection(raw)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "projections_national_query_ok",
            variant=variant,
            countries=len(result),
            elapsed_ms=elapsed_ms,
        )

        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_national_indicators(
        self,
        country_codes: list[str],
        years: list[str],
        indicators: list[str],
    ) -> dict[str, dict[str, float]]:
        """Load demographic indicators from cache or Eurostat API."""
        cache_path = self._cache_dir / "national_indicators.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                cached = json.load(f)
            if cached:
                return cached

        params = [("format", "JSON"), ("lang", "en"), ("projection", "BSL")]
        for ind in indicators:
            params.append(("indic_de", ind))
        for cc in country_codes:
            params.append(("geo", cc))
        for yr in years:
            params.append(("time", yr))

        raw = self._query_api(self._indicators_dataset, params)
        if raw is None:
            return {}

        result = parse_jsonstat_indicators(raw)
        log.info("projections_indicators_query_ok", countries=len(result))

        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_regional_projections(
        self,
        nuts3_codes: list[str],
        years: list[str],
    ) -> dict[str, dict[str, float]]:
        """Load NUTS3 regional projections from cache or Eurostat API."""
        cache_path = self._cache_dir / "regional_proj.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                cached = json.load(f)
            if cached:
                return cached

        params = [("format", "JSON"), ("lang", "en"),
                  ("projection", "BSL"), ("sex", "T"), ("age", "TOTAL")]
        for code in nuts3_codes[:200]:
            params.append(("geo", code))
        for yr in years:
            params.append(("time", yr))

        raw = self._query_api(self._regional_proj_dataset, params)
        if raw is None:
            return {}

        result = parse_jsonstat_projection(raw)
        log.info("projections_regional_query_ok", regions=len(result))

        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_regional_demographics(
        self,
        nuts3_codes: list[str],
        year: int,
    ) -> dict[str, dict[str, float]]:
        """Load NUTS3 age-group population data."""
        cache_path = self._cache_dir / "regional_demographics.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        result: dict[str, dict[str, float]] = {}
        for age_group in ["TOTAL", "Y15-64", "Y_GE65"]:
            params = [
                ("format", "JSON"), ("lang", "en"),
                ("sex", "T"), ("age", age_group), ("time", str(year)),
            ]
            for code in nuts3_codes[:200]:
                params.append(("geo", code))

            raw = self._query_api("DEMO_R_PJANGRP3", params)
            if raw:
                parsed = parse_jsonstat_tabular(raw)
                for nuts3, val in parsed.items():
                    if nuts3 not in result:
                        result[nuts3] = {}
                    result[nuts3][age_group] = val

            time.sleep(self._delay)

        log.info("projections_demographics_ok", regions=len(result))
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_regional_employment(
        self,
        nuts2_codes: list[str],
        year: int,
    ) -> dict[str, dict[str, float]]:
        """Load NUTS2 employment by NACE sector."""
        cache_path = self._cache_dir / "regional_employment.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        params = [
            ("format", "JSON"), ("lang", "en"),
            ("sex", "T"), ("age", "Y15-64"), ("time", str(year)),
        ]
        for code in nuts2_codes:
            params.append(("geo", code))
        for nace in ["TOTAL", "B-E", "F", "D"]:
            params.append(("nace_r2", nace))

        raw = self._query_api("LFST_R_LFE2EN2N", params)
        if raw is None:
            return {}

        result = parse_jsonstat_employment(raw)
        log.info("projections_employment_ok", regions=len(result))
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_regional_education(
        self,
        nuts2_codes: list[str],
        year: int,
    ) -> dict[str, float]:
        """Load NUTS2 tertiary education rates."""
        cache_path = self._cache_dir / "regional_education.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        params = [
            ("format", "JSON"), ("lang", "en"),
            ("sex", "T"), ("age", "Y25-64"),
            ("isced11", "ED5-8"), ("time", str(year)),
        ]
        for code in nuts2_codes:
            params.append(("geo", code))

        raw = self._query_api("EDAT_LFSE_04", params)
        if raw is None:
            return {}

        result = parse_jsonstat_tabular(raw)
        log.info("projections_education_ok", regions=len(result))
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_regional_unemployment(
        self,
        nuts2_codes: list[str],
        year: int,
    ) -> dict[str, float]:
        """Load NUTS2 unemployment rates."""
        cache_path = self._cache_dir / "regional_unemployment.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        params = [
            ("format", "JSON"), ("lang", "en"),
            ("sex", "T"), ("age", "Y15-74"), ("time", str(year)),
        ]
        for code in nuts2_codes:
            params.append(("geo", code))

        raw = self._query_api("LFST_R_LFU3RT", params)
        if raw is None:
            return {}

        result = parse_jsonstat_tabular(raw)
        log.info("projections_unemployment_ok", regions=len(result))
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_or_fetch_gdp_per_capita(
        self,
        geo_codes: list[str],
        year: int,
    ) -> dict[str, float]:
        """Load NUTS3 GDP per capita (EUR per inhabitant)."""
        cache_path = self._cache_dir / "regional_gdp.json"
        if cache_path.is_file():
            with open(cache_path) as f:
                return json.load(f)

        params = [
            ("format", "JSON"), ("lang", "en"),
            ("unit", "EUR_HAB"), ("time", str(year - 1)),
        ]
        for code in geo_codes[:200]:
            params.append(("geo", code))

        raw = self._query_api("NAMA_10R_3POPGDP", params)
        if raw is None:
            return {}

        result = parse_jsonstat_tabular(raw)
        log.info("projections_gdp_ok", regions=len(result))
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    def _load_nso_supplements(self) -> dict[str, NsoProjection]:
        """Load all NSO supplement JSON files from the supplement directory."""
        supplements: dict[str, NsoProjection] = {}
        self._nso_dir.mkdir(parents=True, exist_ok=True)

        for json_file in sorted(self._nso_dir.glob("*.json")):
            try:
                with open(json_file) as f:
                    raw = json.load(f)
                nso = parse_nso_supplement(raw)
                if nso:
                    supplements[nso.country_code] = nso
                    log.info(
                        "projections_nso_loaded",
                        country=nso.country_code,
                        source=nso.source[:50],
                    )
            except Exception as exc:
                log.warning(
                    "projections_nso_parse_error",
                    file=str(json_file),
                    error=str(exc),
                )

        return supplements

    # ------------------------------------------------------------------
    # Phase B: Single-site computation
    # ------------------------------------------------------------------

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        country_code: str | None = None,
    ) -> EurostatProjectionsResult:
        """Compute population projection and socioeconomic metrics for a site."""
        if not self._data_loaded:
            self.ingest_projections()

        cc = country_code or _country_from_coords(lat, lon)

        nuts3 = self._find_nuts3_for_country(cc)
        nuts2 = self._nuts3_to_nuts2.get(nuts3, nuts3[:4] if nuts3 else None)

        try:
            if cc in IN_SCOPE_EU:
                return self._fetch_eu_site(lat, lon, cc, nuts3, nuts2)
            elif cc in IN_SCOPE_CANDIDATE:
                return self._fetch_candidate_site(lat, lon, cc, nuts3, nuts2)
            else:
                return self._fetch_nso_site(lat, lon, cc)
        except Exception as exc:
            log.error(
                "projections_fetch_error",
                lat=lat, lon=lon, country=cc, error=str(exc),
            )
            return EurostatProjectionsResult(
                lat=lat, lon=lon,
                country_code=cc or "??",
                nuts3_code=nuts3,
                nuts2_code=nuts2,
                quality="insufficient",
                error=str(exc),
            )

    def _fetch_eu_site(
        self,
        lat: float,
        lon: float,
        cc: str,
        nuts3: str | None,
        nuts2: str | None,
    ) -> EurostatProjectionsResult:
        """Build a result for a full-coverage EU member state."""
        nat_bsl = self._national_bsl.get(cc, {})
        nat_lmig = self._national_lmig.get(cc, {})
        nat_hmig = self._national_hmig.get(cc, {})
        reg_proj = self._regional_proj.get(nuts3, {}) if nuts3 else {}
        indicators = self._indicators.get(cc, {})

        nat_base_pop = nat_bsl.get("2022") or nat_bsl.get("2023", 0.0)

        if reg_proj:
            reg_pop_age = self._regional_pop_age.get(nuts3, {}) if nuts3 else {}
            base_pop_regional = reg_pop_age.get("TOTAL")
            trajectory = compute_growth_trajectory(
                nat_bsl, reg_proj, nat_base_pop, base_pop_regional,
            )
            spatial_level = "nuts3"
            proj_source = "europop2019_regional"
        else:
            trajectory = compute_growth_trajectory(nat_bsl, None, nat_base_pop, None)
            spatial_level = "national"
            proj_source = "europop2023"

        base_pop = trajectory.get("2022") or trajectory.get("2023", 0)
        if not base_pop:
            base_pop = int(nat_base_pop) if nat_base_pop else None

        proj_50 = trajectory.get("2050")
        proj_80 = trajectory.get("2080")
        proj_30 = trajectory.get("2030")
        proj_40 = trajectory.get("2040")
        proj_60 = trajectory.get("2060")

        change_50 = None
        change_80 = None
        if base_pop and proj_50:
            change_50 = compute_pop_change_pct_per_decade(
                base_pop, proj_50, 2022, 2050,
            )
        if base_pop and proj_80:
            change_80 = compute_pop_change_pct_per_decade(
                base_pop, proj_80, 2022, 2080,
            )

        growth_class = classify_growth(change_50 or 0.0)
        rgf = None
        if base_pop and proj_80:
            rgf = compute_receptor_growth_factor(base_pop, proj_80)

        nat_growth_rate = indicators.get("GROWRT")
        reg_growth_rate = None
        if change_50 is not None:
            reg_growth_rate = change_50
        expansion_pressure = None
        if reg_growth_rate is not None and nat_growth_rate is not None:
            expansion_pressure = compute_urban_expansion_pressure(
                reg_growth_rate, nat_growth_rate,
            )

        lmig_50 = int(nat_lmig.get(cc, {}).get("2050", 0)) or None if nat_lmig else None
        hmig_50 = int(nat_hmig.get(cc, {}).get("2050", 0)) or None if nat_hmig else None
        lmig_80 = int(nat_lmig.get(cc, {}).get("2080", 0)) or None if nat_lmig else None
        hmig_80 = int(nat_hmig.get(cc, {}).get("2080", 0)) or None if nat_hmig else None

        pop_proj = PopulationProjectionResult(
            base_population=int(base_pop) if base_pop else None,
            base_year=2022,
            projected_pop_2030=int(proj_30) if proj_30 else None,
            projected_pop_2040=int(proj_40) if proj_40 else None,
            projected_pop_2050=int(proj_50) if proj_50 else None,
            projected_pop_2060=int(proj_60) if proj_60 else None,
            projected_pop_2080=int(proj_80) if proj_80 else None,
            pop_change_pct_2050=round(change_50, 3) if change_50 is not None else None,
            pop_change_pct_2080=round(change_80, 3) if change_80 is not None else None,
            receptor_growth_factor_60yr=round(rgf, 4) if rgf else None,
            projection_lo_2050=lmig_50,
            projection_hi_2050=hmig_50,
            projection_lo_2080=lmig_80,
            projection_hi_2080=hmig_80,
            growth_classification=growth_class,
            urban_expansion_pressure=round(expansion_pressure, 3) if expansion_pressure is not None else None,
            median_age_2050=indicators.get("MEDAGEPOP"),
            old_age_dependency_2050=indicators.get("OLDDEP"),
            net_migration_rate_projected=indicators.get("CNMIGRATRT"),
            projection_source=proj_source,
            projection_variant="baseline",
            spatial_level=spatial_level,
        )

        socio = self._build_socioeconomic(cc, nuts3, nuts2)
        workforce = self._build_workforce(nuts3, nuts2)
        policy = self._build_policy_proxy(cc, workforce)

        quality = "high" if reg_proj else "medium"

        return EurostatProjectionsResult(
            lat=lat, lon=lon,
            country_code=cc,
            nuts3_code=nuts3,
            nuts2_code=nuts2,
            population_projection=pop_proj,
            socioeconomic=socio,
            workforce=workforce,
            policy_proxy=policy,
            source="eurostat_europop2023",
            reference_year=2022,
            quality=quality,
        )

    def _fetch_candidate_site(
        self,
        lat: float,
        lon: float,
        cc: str,
        nuts3: str | None,
        nuts2: str | None,
    ) -> EurostatProjectionsResult:
        """Build a result for an EU candidate country (partial data)."""
        nso = self._nso_supplements.get(cc)

        pop_proj: PopulationProjectionResult | None = None
        if nso:
            base_pop = nso.population_at(nso.base_year)
            proj_50 = nso.population_at(2050)
            proj_80 = nso.population_at(2080)
            change_50 = None
            rgf = None
            if base_pop and proj_50:
                change_50 = compute_pop_change_pct_per_decade(
                    base_pop, proj_50, nso.base_year, 2050,
                )
            if base_pop and proj_80:
                rgf = compute_receptor_growth_factor(base_pop, proj_80)
            pop_proj = PopulationProjectionResult(
                base_population=base_pop,
                base_year=nso.base_year,
                projected_pop_2030=nso.population_at(2030),
                projected_pop_2040=nso.population_at(2040),
                projected_pop_2050=proj_50,
                projected_pop_2060=nso.population_at(2060),
                projected_pop_2080=proj_80,
                pop_change_pct_2050=round(change_50, 3) if change_50 is not None else None,
                receptor_growth_factor_60yr=round(rgf, 4) if rgf else None,
                growth_classification=classify_growth(change_50 or 0.0),
                median_age_2050=nso.median_age_2050,
                old_age_dependency_2050=nso.old_age_dependency_2050,
                projection_source="nso",
                projection_variant=nso.projection_variant,
                spatial_level="national",
            )
        else:
            log.warning("projections_nso_missing", country=cc)

        policy = self._build_policy_proxy(cc, None)

        return EurostatProjectionsResult(
            lat=lat, lon=lon,
            country_code=cc,
            nuts3_code=None,
            nuts2_code=None,
            population_projection=pop_proj,
            policy_proxy=policy,
            source="nso_supplement",
            reference_year=nso.base_year if nso else 2023,
            quality="medium" if nso else "insufficient",
        )

    def _fetch_nso_site(
        self,
        lat: float,
        lon: float,
        cc: str,
    ) -> EurostatProjectionsResult:
        """Build a result for a non-EU country with NSO supplement only."""
        nso = self._nso_supplements.get(cc)

        if not nso:
            log.warning("projections_nso_missing", country=cc)
            policy = self._build_policy_proxy(cc, None)
            return EurostatProjectionsResult(
                lat=lat, lon=lon,
                country_code=cc,
                policy_proxy=policy,
                source="nso_supplements",
                quality="insufficient",
            )

        base_pop = nso.population_at(nso.base_year)
        proj_50 = nso.population_at(2050)
        proj_80 = nso.population_at(2080)
        change_50 = None
        rgf = None
        if base_pop and proj_50:
            change_50 = compute_pop_change_pct_per_decade(
                base_pop, proj_50, nso.base_year, 2050,
            )
        if base_pop and proj_80:
            rgf = compute_receptor_growth_factor(base_pop, proj_80)

        pop_proj = PopulationProjectionResult(
            base_population=base_pop,
            base_year=nso.base_year,
            projected_pop_2030=nso.population_at(2030),
            projected_pop_2040=nso.population_at(2040),
            projected_pop_2050=proj_50,
            projected_pop_2060=nso.population_at(2060),
            projected_pop_2080=proj_80,
            pop_change_pct_2050=round(change_50, 3) if change_50 is not None else None,
            receptor_growth_factor_60yr=round(rgf, 4) if rgf else None,
            growth_classification=classify_growth(change_50 or 0.0),
            median_age_2050=nso.median_age_2050,
            old_age_dependency_2050=nso.old_age_dependency_2050,
            projection_source="un_wpp" if "WPP" in (nso.source or "") else "nso",
            projection_variant=nso.projection_variant,
            spatial_level="national",
        )

        policy = self._build_policy_proxy(cc, None)

        return EurostatProjectionsResult(
            lat=lat, lon=lon,
            country_code=cc,
            population_projection=pop_proj,
            policy_proxy=policy,
            source="nso_supplement",
            reference_year=nso.base_year,
            quality="low",
        )

    def _build_socioeconomic(
        self,
        country_code: str,
        nuts3: str | None,
        nuts2: str | None,
    ) -> SocioeconomicResult | None:
        """Assemble socioeconomic metrics from pre-loaded data."""
        nuts3_gdp = self._regional_gdp_capita.get(nuts3) if nuts3 else None
        nuts2_gdp = self._regional_gdp_capita.get(nuts2) if nuts2 else None
        region_gdp = nuts3_gdp or nuts2_gdp

        national_gdp = _national_gdp_estimate(country_code)

        gdp_gap = None
        if region_gdp and national_gdp:
            gdp_gap = (region_gdp - national_gdp) / national_gdp * 100.0

        unemployment = (
            self._nuts2_unemployment.get(nuts2) if nuts2 else None
        )
        education = self._nuts2_education.get(nuts2) if nuts2 else None

        deprivation = None
        if gdp_gap is not None or unemployment is not None or education is not None:
            deprivation = compute_deprivation_index(gdp_gap, unemployment, education)

        fiscal_cap = None
        if region_gdp:
            eu_median = 30_000
            fiscal_cap = round(min(region_gdp / eu_median, 1.0), 4)

        return SocioeconomicResult(
            nuts3_gdp_per_capita_eur=round(region_gdp, 2) if region_gdp else None,
            national_gdp_per_capita_eur=national_gdp,
            gdp_gap_to_national_pct=round(gdp_gap, 2) if gdp_gap is not None else None,
            fiscal_capacity_index=fiscal_cap,
            deprivation_index=deprivation,
        )

    def _build_workforce(
        self,
        nuts3: str | None,
        nuts2: str | None,
    ) -> WorkforceResult | None:
        """Assemble workforce metrics from pre-loaded data."""
        pop_age = self._regional_pop_age.get(nuts3, {}) if nuts3 else {}
        total_pop = pop_age.get("TOTAL")
        working_age = pop_age.get("Y15-64")
        working_age_pct = None
        if total_pop and working_age and total_pop > 0:
            working_age_pct = round(working_age / total_pop * 100.0, 2)

        empl = self._nuts2_employment.get(nuts2, {}) if nuts2 else {}
        employment_total = empl.get("TOTAL")
        industry_pct = empl.get("B-E")
        construction_pct = empl.get("F")
        energy_pct = empl.get("D")

        unemployment = self._nuts2_unemployment.get(nuts2) if nuts2 else None
        education = self._nuts2_education.get(nuts2) if nuts2 else None

        retraining = None
        if any(v is not None for v in [industry_pct, energy_pct, construction_pct, unemployment]):
            retraining = compute_retraining_pool_index(
                industry_pct, energy_pct, construction_pct, unemployment,
            )

        return WorkforceResult(
            working_age_pop=int(working_age) if working_age else None,
            working_age_pct=working_age_pct,
            employment_rate_pct=None,
            unemployment_rate_pct=round(unemployment, 2) if unemployment else None,
            employment_industry_pct=round(industry_pct, 2) if industry_pct else None,
            employment_construction_pct=round(construction_pct, 2) if construction_pct else None,
            employment_energy_pct=round(energy_pct, 2) if energy_pct else None,
            tertiary_education_pct=round(education, 2) if education else None,
            retraining_pool_index=retraining,
        )

    def _build_policy_proxy(
        self,
        country_code: str,
        workforce: WorkforceResult | None,
    ) -> PolicyProxyResult:
        """Build NS-12 policy proxy from config + workforce data."""
        stance = self._nuclear_policy.get(country_code, "unknown")
        energy_dep = None
        edu_index = None
        if workforce:
            if workforce.employment_energy_pct is not None:
                energy_dep = round(workforce.employment_energy_pct / 100.0, 4)
            if workforce.tertiary_education_pct is not None:
                edu_index = round(
                    min(workforce.tertiary_education_pct / 35.0, 1.0), 4
                )

        return PolicyProxyResult(
            nuclear_policy_stance=stance,
            energy_sector_dependence=energy_dep,
            education_index=edu_index,
            policy_source="curated_2026",
        )

    def _find_nuts3_for_country(self, country_code: str | None) -> str | None:
        """Return the first NUTS3 code matching this country (representative only)."""
        if not country_code:
            return None
        for nuts3, cc in self._nuts3_country.items():
            if cc == country_code:
                return nuts3
        return None

    # ------------------------------------------------------------------
    # API query helper
    # ------------------------------------------------------------------

    def _query_api(
        self,
        dataset: str,
        params: list[tuple[str, str]],
        *,
        retries: int = 3,
    ) -> dict[str, Any] | None:
        """Query Eurostat Statistics API with retry on transient errors."""
        url = f"{self._api_url}/data/{dataset}"
        for attempt in range(retries):
            try:
                resp = self._client.get(url, params=params, timeout=self._timeout)
                if resp.status_code == 416:
                    log.info("projections_api_no_data", dataset=dataset)
                    return None
                resp.raise_for_status()
                time.sleep(self._delay)
                return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    log.warning(
                        "projections_api_error",
                        dataset=dataset,
                        status=exc.response.status_code,
                    )
                    return None
                log.warning(
                    "projections_api_retry",
                    dataset=dataset,
                    attempt=attempt + 1,
                    status=exc.response.status_code,
                )
                time.sleep(2 ** attempt)
            except httpx.HTTPError as exc:
                log.warning(
                    "projections_api_retry",
                    dataset=dataset,
                    attempt=attempt + 1,
                    error=str(exc),
                )
                time.sleep(2 ** attempt)

        log.error("projections_api_error", dataset=dataset, msg="all retries failed")
        return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def data_loaded(self) -> bool:
        return self._data_loaded

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EurostatProjectionsConnector:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _country_from_coords(lat: float, lon: float) -> str:
    """Rough bounding-box country guesser for in-scope countries.

    Used only as fallback when site.country_code is not passed.
    Callers should always pass country_code from the DB site record.
    """
    boxes: list[tuple[str, float, float, float, float]] = [
        ("PL", 49.0, 14.1, 54.9, 24.2),
        ("RO", 43.6, 20.2, 48.3, 29.7),
        ("BG", 41.2, 22.4, 44.2, 28.6),
        ("HU", 45.7, 16.1, 48.6, 22.9),
        ("CZ", 48.5, 12.1, 51.1, 18.9),
        ("SK", 47.7, 16.8, 49.6, 22.6),
        ("AT", 46.4, 9.5, 49.0, 17.2),
        ("SI", 45.4, 13.4, 46.9, 16.6),
        ("HR", 42.4, 13.5, 46.6, 19.5),
        ("EE", 57.5, 21.8, 59.7, 28.2),
        ("LV", 55.7, 20.9, 58.1, 28.2),
        ("LT", 53.9, 20.9, 56.5, 26.9),
        ("UA", 44.4, 22.1, 52.4, 40.2),
        ("BY", 51.3, 23.2, 56.2, 32.8),
        ("MD", 45.5, 26.6, 48.5, 30.2),
        ("AM", 38.8, 43.4, 41.3, 46.7),
        ("TR", 35.8, 25.6, 42.1, 44.8),
        ("RS", 41.9, 18.8, 46.2, 23.0),
        ("ME", 41.9, 18.4, 43.6, 20.4),
        ("MK", 41.1, 20.4, 42.4, 23.0),
        ("AL", 39.6, 19.3, 42.7, 21.1),
        ("BA", 42.6, 15.7, 45.3, 19.6),
        ("XK", 41.9, 20.0, 43.3, 21.8),
    ]
    for cc, min_lat, min_lon, max_lat, max_lon in boxes:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return cc
    return "??"


_NATIONAL_GDP_PER_CAPITA: dict[str, float] = {
    "PL": 17000, "CZ": 23000, "SK": 20000, "HU": 18000,
    "AT": 48000, "SI": 29000, "HR": 18000, "RO": 14900,
    "BG": 12500, "EE": 25000, "LV": 21000, "LT": 22000,
    "TR": 12000, "RS": 9000,  "ME": 9500,  "MK": 7000,
    "AL": 6500,  "BA": 7500,  "XK": 5000,  "MD": 4500,
    "UA": 4000,  "BY": 7500,  "AM": 6500,
}


def _national_gdp_estimate(country_code: str) -> float | None:
    return _NATIONAL_GDP_PER_CAPITA.get(country_code)
