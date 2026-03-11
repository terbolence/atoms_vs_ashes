"""Ingest coal plant sites from the GEM Global Coal Plant Tracker XLSX."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import AuditLog, Country, Site
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# GEM source countries → ISO 3166-1 alpha-2 mapping for the study region.
# Keys are the values appearing in the "Country/Area" column of the tracker.
COUNTRY_NAME_TO_CODE: dict[str, str] = {
    "Poland": "PL",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    "Slovakia": "SK",
    "Hungary": "HU",
    "Austria": "AT",
    "Slovenia": "SI",
    "Croatia": "HR",
    "Bosnia and Herzegovina": "BA",
    "Serbia": "RS",
    "Montenegro": "ME",
    "Kosovo": "XK",
    "Albania": "AL",
    "North Macedonia": "MK",
    "Romania": "RO",
    "Bulgaria": "BG",
    "Moldova": "MD",
    "Ukraine": "UA",
    "Belarus": "BY",
    "Estonia": "EE",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Armenia": "AM",
    "Turkey": "TR",
    "Türkiye": "TR",
}

# GEM tracker column name → Site model field
_COLUMN_MAP: dict[str, str] = {
    "GEM unit/phase ID": "gem_unit_phase_id",
    "GEM location ID": "gem_location_id",
    "Country/Area": "country_name",
    "Wiki URL": "wiki_url",
    "Plant name": "name",
    "Plant name (other)": "_alt_name_other",
    "Plant name (local)": "_alt_name_local",
    "Owner": "owner_operator",
    "Owner GEM Entity ID": "owner_gem_id",
    "Parent": "parent_company",
    "Parent GEM Entity ID": "parent_gem_id",
    "Capacity (MW)": "installed_capacity_mw",
    "Status": "_raw_status",
    "Start year": "start_year",
    "Retired year": "retired_year",
    "Planned retirement": "planned_retirement",
    "Coal phaseout year": "coal_phaseout_year",
    "Net zero year": "net_zero_year",
    "Combustion technology": "combustion_technology",
    "Coal type": "_raw_coal_type",
    "Coal source": "coal_source",
    "Location": "location",
    "Local area (taluk, county)": "local_area",
    "Subnational unit (province, state)": "subnational_unit",
    "Region": "region",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Location accuracy": "location_accuracy",
    "Permits": "permits",
    "Permit Date": "permit_date",
}

# Columns carried into extended_data JSONB
_EXTENDED_COLUMNS = [
    "Unit name",
    "Conversion to (fuel)",
    "Conversion to (GEM unit ID)",
    "Alternate Fuel",
    "Major area (prefecture, district)",
    "Subregion",
    "Permit Parsed",
    "Captive",
    "Captive industry use",
    "Captive residential use",
    "CHP",
    "Capacity factor",
    "Plant age (years)",
    "Heat rate (Btu per kWh)",
    "Emission factor (kg of CO2 per TJ)",
    "Annual CO2 (million tonnes / annum)",
    "Remaining plant lifetime (years)",
    "Lifetime CO2 (million tonnes)",
    "China capacity payment recipient",
]

_STATUS_MAP: dict[str, str] = {
    "operating": "operating",
    "retired": "retired",
    "mothballed": "mothballed",
    "announced": "announced",
    "pre-permit": "pre_permit",
    "permitted": "permitted",
    "construction": "construction",
    "shelved": "shelved",
    "cancelled": "cancelled",
}

_COAL_TYPE_TO_PLANT_TYPE: dict[str, str] = {
    "lignite": "lignite",
    "bituminous": "coal",
    "sub-bituminous": "coal",
    "anthracite": "coal",
    "unknown": "coal",
}


def _normalise_status(raw: str | None) -> str:
    if not raw:
        return "other"
    return _STATUS_MAP.get(raw.strip().lower(), "other")


def _derive_plant_type(coal_type_raw: str | None) -> str:
    if not coal_type_raw:
        return "coal"
    first = coal_type_raw.split("/")[0].strip().lower()
    return _COAL_TYPE_TO_PLANT_TYPE.get(first, "coal")


def _safe_int(val: Any) -> int | None:
    if val is None or val == "" or val == "--":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    if val is None or val == "" or val == "--":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _build_alt_names(row: dict[str, Any]) -> list[str] | None:
    names: list[str] = []
    for key in ("_alt_name_other", "_alt_name_local"):
        v = row.get(key)
        s = str(v).strip() if v is not None else ""
        if s and s not in ("--", "nan", "NaN", "None"):
            names.append(s)
    return names if names else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_coal_tracker(
    session: Session,
    settings: Settings,
    *,
    run_id: str,
    project_root: Path | None = None,
) -> int:
    """Parse, filter, normalise and insert GEM Coal Plant Tracker data.

    Returns the number of site records inserted.
    """
    root = project_root or Path(settings.source_files.get("coal_tracker", "")).parent.parent
    tracker_path = root / settings.source_files["coal_tracker"]
    sheet = settings.source_files.get("coal_tracker_sheet", "Units")

    log.info("reading_coal_tracker", path=str(tracker_path), sheet=sheet)
    df = pd.read_excel(tracker_path, sheet_name=sheet, dtype=str)
    df.columns = df.columns.str.strip()

    in_scope = set(COUNTRY_NAME_TO_CODE.keys())
    df = df[df["Country/Area"].isin(in_scope)].copy()
    log.info("filtered_in_scope", rows=len(df))

    _ensure_countries(session, df)

    # Deduplicate to one row per GEM location ID (aggregate at plant level)
    seen_locations: dict[str, bool] = {}
    inserted = 0

    for idx, raw_row in df.iterrows():
        mapped = {target: raw_row.get(src) for src, target in _COLUMN_MAP.items()}

        loc_id = mapped.get("gem_location_id")
        if loc_id and loc_id in seen_locations:
            continue
        if loc_id:
            seen_locations[loc_id] = True

        lat = _safe_float(mapped.get("latitude"))
        lon = _safe_float(mapped.get("longitude"))
        if lat is None or lon is None:
            log.warning("missing_coordinates", row=idx, name=mapped.get("name"))
            continue

        country_name = str(mapped["country_name"]).strip()
        country_code = COUNTRY_NAME_TO_CODE.get(country_name, "XX")

        raw_status = mapped.get("_raw_status")
        status = _normalise_status(raw_status)
        plant_type = _derive_plant_type(mapped.get("_raw_coal_type"))
        alt_names = _build_alt_names(mapped)

        extended: dict[str, Any] = {}
        for col in _EXTENDED_COLUMNS:
            val = raw_row.get(col)
            if val is not None and str(val).strip() and str(val).strip() != "--":
                extended[col] = str(val).strip()

        geom_wkt = f"SRID=4326;POINT({lon} {lat})"

        site = Site(
            site_id=uuid.uuid4(),
            name=str(mapped.get("name", "")).strip(),
            alternative_names=alt_names,
            country_code=country_code,
            country_name=country_name,
            latitude=lat,
            longitude=lon,
            geom=geom_wkt,
            location_accuracy=_str_or_none(mapped.get("location_accuracy")),
            local_area=_str_or_none(mapped.get("local_area")),
            subnational_unit=_str_or_none(mapped.get("subnational_unit")),
            region=_str_or_none(mapped.get("region")),
            plant_type=plant_type,
            installed_capacity_mw=_safe_float(mapped.get("installed_capacity_mw")),
            status=status,
            start_year=_safe_int(mapped.get("start_year")),
            retired_year=_safe_int(mapped.get("retired_year")),
            planned_retirement=_parse_date(mapped.get("planned_retirement")),
            coal_phaseout_year=_safe_int(mapped.get("coal_phaseout_year")),
            net_zero_year=_safe_int(mapped.get("net_zero_year")),
            owner_operator=_str_or_none(mapped.get("owner_operator")),
            parent_company=_str_or_none(mapped.get("parent_company")),
            combustion_technology=_str_or_none(mapped.get("combustion_technology")),
            coal_type=_str_or_none(mapped.get("_raw_coal_type")),
            coal_source=_str_or_none(mapped.get("coal_source")),
            location=_str_or_none(mapped.get("location")),
            permits=_str_or_none(mapped.get("permits")),
            permit_date=_parse_date(mapped.get("permit_date")),
            owner_gem_id=_str_or_none(mapped.get("owner_gem_id")),
            parent_gem_id=_str_or_none(mapped.get("parent_gem_id")),
            gem_unit_phase_id=_str_or_none(mapped.get("gem_unit_phase_id")),
            gem_location_id=_str_or_none(loc_id),
            wiki_url=_str_or_none(mapped.get("wiki_url")),
            extended_data=extended if extended else None,
            last_verified=datetime.now(timezone.utc),
        )
        session.add(site)

        session.add(AuditLog(
            operation="insert",
            table_name="sites",
            site_id=site.site_id,
            after_value={"name": site.name, "gem_location_id": site.gem_location_id},
            source_file=str(tracker_path),
            source_row=int(idx) if isinstance(idx, (int, float)) else None,
            run_id=run_id,
            message="Ingested from GEM Coal Plant Tracker",
        ))
        inserted += 1

    log.info("sites_inserted", count=inserted)
    return inserted


def load_supplementary_sites(
    session: Session,
    settings: Settings,
    *,
    run_id: str,
) -> int:
    """Insert the manually defined supplementary Romanian sites."""
    inserted = 0
    for entry in settings.supplementary_sites:
        _ensure_country_row(session, entry["country_code"], entry["country_name"])

        lat = entry["latitude"]
        lon = entry["longitude"]
        geom_wkt = f"SRID=4326;POINT({lon} {lat})"

        site = Site(
            site_id=uuid.uuid4(),
            name=entry["name"],
            country_code=entry["country_code"],
            country_name=entry["country_name"],
            latitude=lat,
            longitude=lon,
            geom=geom_wkt,
            plant_type=entry.get("plant_type", "thermal"),
            status=entry.get("status", "operating"),
            subnational_unit=entry.get("subnational_unit"),
            location=entry.get("location"),
            last_verified=datetime.now(timezone.utc),
        )
        session.add(site)
        session.add(AuditLog(
            operation="insert",
            table_name="sites",
            site_id=site.site_id,
            after_value={"name": site.name, "source": "supplementary_config"},
            run_id=run_id,
            message="Supplementary Romanian site from config",
        ))
        inserted += 1
    log.info("supplementary_sites_inserted", count=inserted)
    return inserted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _str_or_none(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("--", "nan", "NaN", "None"):
        return None
    return s


def _parse_date(val: Any):
    if val is None or str(val).strip() in ("", "--"):
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _ensure_countries(session: Session, df: pd.DataFrame) -> None:
    """Insert Country rows for all distinct countries in the dataframe."""
    for country_name in df["Country/Area"].dropna().unique():
        name = str(country_name).strip()
        code = COUNTRY_NAME_TO_CODE.get(name)
        if code:
            _ensure_country_row(session, code, name)


def _ensure_country_row(session: Session, code: str, name: str) -> None:
    existing = session.get(Country, code)
    if not existing:
        session.add(Country(country_code=code, country_name=name))
