# man_hours: 3.0
"""Pure parsing logic for S-12 SEVESO III data sources.

Handles Minerva SEVESO CSV, national register CSVs, and
facility deduplication/merge logic.  No I/O, no HTTP, no database.
"""

from __future__ import annotations

import csv
import io
import math
import re
from typing import Any

from atoms_vs_ashes.connectors.eea_industrial.models import IndustrialFacility
from atoms_vs_ashes.connectors.eea_industrial.parsers import classify_hazard
from atoms_vs_ashes.connectors.seveso.models import (
    EU_SEVESO_COUNTRIES,
    MergeStats,
    MinervaEstablishment,
    NationalFacility,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Minerva CSV parsing
# ---------------------------------------------------------------------------

_MINERVA_COL_ALIASES: dict[str, list[str]] = {
    "name": ["EstablishmentName", "establishment_name", "Name", "name"],
    "country": ["Country", "country", "CountryCode", "country_code"],
    "latitude": ["Latitude", "latitude", "lat", "Lat"],
    "longitude": ["Longitude", "longitude", "lon", "Lon"],
    "seveso_status": ["SevesoStatus", "seveso_status", "Seveso", "Tier", "tier"],
    "activity": ["Activity", "activity", "MainActivity", "main_activity"],
    "region": ["Region", "region", "NUTS", "nuts"],
    "city": ["City", "city", "Municipality", "municipality"],
    "substances": ["Substances", "substances", "DangerousSubstances"],
}

# Country name → ISO 3166-1 alpha-2 (for Minerva CSVs that use full names)
_COUNTRY_NAME_MAP: dict[str, str] = {
    "poland": "PL", "czech republic": "CZ", "czechia": "CZ",
    "slovakia": "SK", "hungary": "HU", "austria": "AT",
    "slovenia": "SI", "croatia": "HR", "bulgaria": "BG",
    "romania": "RO", "estonia": "EE", "latvia": "LV",
    "lithuania": "LT", "serbia": "RS", "turkey": "TR",
    "bosnia and herzegovina": "BA", "bosnia": "BA",
    "montenegro": "ME", "albania": "AL",
    "north macedonia": "MK", "macedonia": "MK",
    "kosovo": "XK", "moldova": "MD", "ukraine": "UA",
    "belarus": "BY", "armenia": "AM",
}


def parse_minerva_csv(
    text: str,
    *,
    country_filter: set[str] | None = None,
) -> list[MinervaEstablishment]:
    """Parse a JRC Minerva SEVESO establishment CSV.

    Parameters
    ----------
    text
        Raw CSV text content.
    country_filter
        If provided, only include establishments in these countries.
    """
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        log.warning("minerva_csv_empty_headers")
        return []

    headers = list(reader.fieldnames)
    col_map = _resolve_minerva_columns(headers)

    establishments: list[MinervaEstablishment] = []
    skipped = 0

    for row in reader:
        lat = _safe_float(row.get(col_map.get("latitude", ""), ""))
        lon = _safe_float(row.get(col_map.get("longitude", ""), ""))
        if lat is None or lon is None:
            skipped += 1
            continue

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            skipped += 1
            continue

        country_raw = (row.get(col_map.get("country", ""), "") or "").strip()
        cc = _normalise_country(country_raw)
        if country_filter and cc not in country_filter:
            continue

        name = (row.get(col_map.get("name", ""), "") or "").strip()
        if not name:
            name = "Unknown establishment"

        seveso_raw = (row.get(col_map.get("seveso_status", ""), "") or "").strip()
        tier = _normalise_tier(seveso_raw)

        establishments.append(MinervaEstablishment(
            name=name,
            country_code=cc,
            latitude=lat,
            longitude=lon,
            seveso_tier=tier,
            activity=(row.get(col_map.get("activity", ""), "") or "").strip() or None,
            region=(row.get(col_map.get("region", ""), "") or "").strip() or None,
            city=(row.get(col_map.get("city", ""), "") or "").strip() or None,
            substances=(row.get(col_map.get("substances", ""), "") or "").strip() or None,
        ))

    if skipped:
        log.info("minerva_csv_skipped", count=skipped)
    log.info("minerva_csv_parsed", count=len(establishments))
    return establishments


# ---------------------------------------------------------------------------
# National register CSV parsing
# ---------------------------------------------------------------------------

def parse_national_csv(
    text: str,
    country_code: str,
) -> list[NationalFacility]:
    """Parse a national SEVESO register CSV with standardised schema.

    Expected columns: name, latitude, longitude, seveso_tier,
    hazard_categories, activity, source_url
    """
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        log.warning("national_csv_empty_headers", country=country_code)
        return []

    facilities: list[NationalFacility] = []
    skipped = 0

    for row in reader:
        lat = _safe_float(row.get("latitude", ""))
        lon = _safe_float(row.get("longitude", ""))
        if lat is None or lon is None:
            skipped += 1
            continue

        name = (row.get("name", "") or "").strip()
        if not name:
            name = "Unknown facility"

        tier = _normalise_tier(row.get("seveso_tier", "") or "")
        hazard_raw = (row.get("hazard_categories", "") or "").strip()
        hazard_cats = _parse_hazard_categories(hazard_raw)

        facilities.append(NationalFacility(
            name=name,
            latitude=lat,
            longitude=lon,
            seveso_tier=tier,
            hazard_categories=hazard_cats,
            activity=(row.get("activity", "") or "").strip() or None,
            source_url=(row.get("source_url", "") or "").strip() or None,
            country_code=country_code.upper(),
        ))

    if skipped:
        log.info("national_csv_skipped", country=country_code, count=skipped)
    log.info("national_csv_parsed", country=country_code, count=len(facilities))
    return facilities


# ---------------------------------------------------------------------------
# Facility merge / deduplication
# ---------------------------------------------------------------------------

def merge_facilities(
    eprtr: list[IndustrialFacility],
    minerva: list[MinervaEstablishment],
    national: list[NationalFacility],
    *,
    distance_threshold_m: float = 500.0,
    name_similarity_threshold: float = 0.8,
) -> tuple[list[IndustrialFacility], MergeStats]:
    """Merge E-PRTR, Minerva, and national register facilities.

    Strategy:
    1. Start with E-PRTR facilities as the base.
    2. Match Minerva records to E-PRTR by proximity + name similarity.
       Enrich matched E-PRTR records with SEVESO tier from Minerva.
    3. Add unmatched Minerva records as new facilities.
    4. Merge national records (deduplicate against existing).

    Returns (merged_facilities, merge_stats).
    """
    stats = MergeStats(
        eprtr_count=len(eprtr),
        minerva_count=len(minerva),
        national_count=len(national),
    )

    merged = list(eprtr)
    dist_threshold_km = distance_threshold_m / 1000.0

    # Phase 1: Match Minerva → E-PRTR
    for m_est in minerva:
        match_idx = _find_best_match(
            m_est.latitude, m_est.longitude, m_est.name,
            merged, dist_threshold_km, name_similarity_threshold,
        )
        if match_idx is not None:
            _enrich_with_minerva(merged[match_idx], m_est)
            stats.minerva_matched += 1
        else:
            new_fac = _minerva_to_facility(m_est)
            merged.append(new_fac)
            stats.minerva_unmatched += 1

    # Phase 2: Merge national records
    for n_fac in national:
        match_idx = _find_best_match(
            n_fac.latitude, n_fac.longitude, n_fac.name,
            merged, dist_threshold_km, name_similarity_threshold,
        )
        if match_idx is not None:
            _enrich_with_national(merged[match_idx], n_fac)
            stats.duplicates_removed += 1
        else:
            new_fac = _national_to_facility(n_fac)
            merged.append(new_fac)

    stats.merged_total = len(merged)

    log.info("seveso_merge_complete", **stats.to_dict())
    return merged, stats


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_best_match(
    lat: float,
    lon: float,
    name: str,
    facilities: list[IndustrialFacility],
    dist_threshold_km: float,
    name_threshold: float,
) -> int | None:
    """Find the best matching facility by proximity + name similarity."""
    from atoms_vs_ashes.geo import haversine_km

    best_idx: int | None = None
    best_score = 0.0

    for idx, fac in enumerate(facilities):
        dist = haversine_km(lat, lon, fac.latitude, fac.longitude)
        if dist > dist_threshold_km:
            continue

        sim = _name_similarity(name, fac.name)
        if sim < name_threshold:
            continue

        score = sim * (1.0 - dist / dist_threshold_km)
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def _name_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity on word tokens (case-insensitive).

    Avoids the need for rapidfuzz/thefuzz dependency.
    """
    if not a or not b:
        return 0.0
    words_a = set(re.sub(r"[^\w\s]", "", a.lower()).split())
    words_b = set(re.sub(r"[^\w\s]", "", b.lower()).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _enrich_with_minerva(
    facility: IndustrialFacility,
    minerva: MinervaEstablishment,
) -> None:
    """Enrich an E-PRTR facility with Minerva SEVESO data."""
    if minerva.seveso_tier in ("upper", "lower"):
        facility.seveso_status = minerva.seveso_tier
    if not facility.hazard_categories and minerva.seveso_tier:
        facility.hazard_categories = {"chemical", "toxic", "fire"}
    if "minerva" not in facility.source:
        facility.source = f"{facility.source}+minerva"


def _enrich_with_national(
    facility: IndustrialFacility,
    national: NationalFacility,
) -> None:
    """Enrich an existing facility with national register data."""
    if national.seveso_tier in ("upper", "lower") and not facility.seveso_status:
        facility.seveso_status = national.seveso_tier
    facility.hazard_categories.update(national.hazard_categories)
    if "national" not in facility.source:
        facility.source = f"{facility.source}+national"


def _minerva_to_facility(m: MinervaEstablishment) -> IndustrialFacility:
    """Convert a Minerva establishment to an IndustrialFacility."""
    hazard_cats = classify_hazard(seveso_status=m.seveso_tier)
    return IndustrialFacility(
        facility_id=f"minerva-{m.country_code}-{hash(m.name) % 100000:05d}",
        name=m.name,
        latitude=m.latitude,
        longitude=m.longitude,
        country_code=m.country_code,
        seveso_status=m.seveso_tier,
        hazard_categories=hazard_cats if hazard_cats else {"chemical", "toxic", "fire"},
        source="minerva",
    )


def _national_to_facility(n: NationalFacility) -> IndustrialFacility:
    """Convert a national register facility to an IndustrialFacility."""
    return IndustrialFacility(
        facility_id=f"national-{n.country_code}-{hash(n.name) % 100000:05d}",
        name=n.name,
        latitude=n.latitude,
        longitude=n.longitude,
        country_code=n.country_code,
        seveso_status=n.seveso_tier,
        hazard_categories=n.hazard_categories if n.hazard_categories else {"chemical", "toxic", "fire"},
        source="national",
    )


def _normalise_country(raw: str) -> str:
    """Normalise a country name or code to ISO 3166-1 alpha-2."""
    if not raw:
        return ""
    stripped = raw.strip().upper()
    if len(stripped) == 2:
        return stripped
    lower = raw.strip().lower()
    return _COUNTRY_NAME_MAP.get(lower, stripped[:2])


def _normalise_tier(raw: str) -> str:
    """Normalise SEVESO tier to 'upper', 'lower', or 'unknown'."""
    if not raw:
        return "unknown"
    lower = raw.strip().lower()
    if "upper" in lower:
        return "upper"
    if "lower" in lower:
        return "lower"
    return "unknown"


def _parse_hazard_categories(raw: str) -> set[str]:
    """Parse semicolon-separated hazard categories."""
    if not raw:
        return set()
    valid = {"explosion", "toxic", "fire", "chemical"}
    cats = set()
    for part in raw.split(";"):
        cleaned = part.strip().lower()
        if cleaned in valid:
            cats.add(cleaned)
        elif cleaned == "explosion":
            cats.add("chemical")
    return cats


def _safe_float(val: Any) -> float | None:
    """Safely parse a value to float."""
    if val is None:
        return None
    try:
        f = float(str(val).strip())
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _resolve_minerva_columns(headers: list[str]) -> dict[str, str]:
    """Resolve Minerva CSV column names to logical field names."""
    col_map: dict[str, str] = {}
    header_lower = {h.lower().strip(): h for h in headers}
    for field_name, aliases in _MINERVA_COL_ALIASES.items():
        for alias in aliases:
            if alias in headers:
                col_map[field_name] = alias
                break
            if alias.lower() in header_lower:
                col_map[field_name] = header_lower[alias.lower()]
                break
    return col_map
