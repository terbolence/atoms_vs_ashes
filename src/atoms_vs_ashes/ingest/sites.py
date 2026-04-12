# man_hours: 18.0
"""Ingest coal plant sites from the GEM Global Coal Plant Tracker XLSX.

Each ``gem_location_id`` maps to one ``Site`` row with **plant-level
aggregated** data (total capacity, dominant status, unit count).
Individual generating units are stored in ``site_units``.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import AuditLog, Country, Site, SiteUnit
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

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

_STATUS_PRIORITY = [
    "operating", "construction", "permitted", "pre_permit",
    "announced", "mothballed", "shelved", "cancelled",
    "planned_closure", "retired", "other",
]

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


def _aggregate_status(statuses: list[str]) -> str:
    """Pick the highest-priority status across a plant's units."""
    status_set = set(statuses)
    for s in _STATUS_PRIORITY:
        if s in status_set:
            return s
    return "other"


def _aggregate_first_non_null(values: list[Any]) -> Any:
    for v in values:
        if v is not None:
            return v
    return None


def _build_unit_extended(raw_row: pd.Series) -> dict[str, Any]:
    extended: dict[str, Any] = {}
    for col in _EXTENDED_COLUMNS:
        val = raw_row.get(col)
        if val is not None and str(val).strip() and str(val).strip() != "--":
            extended[col] = str(val).strip()
    return extended


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

    Groups all unit rows by ``gem_location_id`` and creates:
    - One ``Site`` row per plant location with aggregated totals.
    - One ``SiteUnit`` row per generating unit.

    Returns the number of site (plant) records inserted.
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

    location_groups: dict[str, list[tuple[int, pd.Series]]] = defaultdict(list)
    no_location: list[tuple[int, pd.Series]] = []

    for idx, raw_row in df.iterrows():
        loc_id = _str_or_none(raw_row.get("GEM location ID"))
        if loc_id:
            location_groups[loc_id].append((idx, raw_row))
        else:
            no_location.append((idx, raw_row))

    inserted = 0
    total_units = 0

    for loc_id, unit_rows in location_groups.items():
        site, n_units = _create_plant_with_units(
            session, loc_id, unit_rows, tracker_path, run_id,
        )
        if site:
            inserted += 1
            total_units += n_units

    for idx, raw_row in no_location:
        site, n_units = _create_single_unit_plant(
            session, idx, raw_row, tracker_path, run_id,
        )
        if site:
            inserted += 1
            total_units += n_units

    log.info("sites_inserted", plants=inserted, units=total_units)
    return inserted


def _create_plant_with_units(
    session: Session,
    loc_id: str,
    unit_rows: list[tuple[int, pd.Series]],
    tracker_path: Path,
    run_id: str,
) -> tuple[Site | None, int]:
    """Create one Site + N SiteUnit rows for a multi-unit (or single-unit) plant."""
    mapped_rows = []
    for idx, raw_row in unit_rows:
        mapped = {target: raw_row.get(src) for src, target in _COLUMN_MAP.items()}
        mapped["_idx"] = idx
        mapped["_raw_row"] = raw_row
        mapped_rows.append(mapped)

    representative = mapped_rows[0]
    lat = _safe_float(representative.get("latitude"))
    lon = _safe_float(representative.get("longitude"))
    if lat is None or lon is None:
        log.warning("missing_coordinates", loc_id=loc_id,
                    name=representative.get("name"))
        return None, 0

    capacities = [_safe_float(m.get("installed_capacity_mw")) for m in mapped_rows]
    statuses = [_normalise_status(m.get("_raw_status")) for m in mapped_rows]
    total_capacity = sum(c for c in capacities if c is not None) or None
    operating_cap = sum(
        c for c, s in zip(capacities, statuses) if c is not None and s == "operating"
    ) or None
    plant_status = _aggregate_status(statuses)

    start_years = [_safe_int(m.get("start_year")) for m in mapped_rows]
    valid_starts = [y for y in start_years if y is not None]
    earliest_start = min(valid_starts) if valid_starts else None

    retired_years = [_safe_int(m.get("retired_year")) for m in mapped_rows]
    all_retired = all(s in ("retired", "cancelled") for s in statuses)
    latest_retired = max((y for y in retired_years if y is not None), default=None) if all_retired else None

    country_name = str(representative["country_name"]).strip()
    country_code = COUNTRY_NAME_TO_CODE.get(country_name, "XX")

    alt_names_all: list[str] = []
    for m in mapped_rows:
        an = _build_alt_names(m)
        if an:
            alt_names_all.extend(an)
    alt_names = list(dict.fromkeys(alt_names_all)) if alt_names_all else None

    plant_extended: dict[str, Any] = {}
    for m in mapped_rows:
        ext = _build_unit_extended(m["_raw_row"])
        for k, v in ext.items():
            if k != "Unit name" and k not in plant_extended:
                plant_extended[k] = v

    geom_wkt = f"SRID=4326;POINT({lon} {lat})"
    site_id = uuid.uuid4()

    site = Site(
        site_id=site_id,
        name=str(representative.get("name", "")).strip(),
        alternative_names=alt_names,
        country_code=country_code,
        country_name=country_name,
        latitude=lat,
        longitude=lon,
        geom=geom_wkt,
        location_accuracy=_str_or_none(representative.get("location_accuracy")),
        local_area=_str_or_none(representative.get("local_area")),
        subnational_unit=_str_or_none(representative.get("subnational_unit")),
        region=_str_or_none(representative.get("region")),
        plant_type=_derive_plant_type(representative.get("_raw_coal_type")),
        installed_capacity_mw=total_capacity,
        operating_capacity_mw=operating_cap,
        status=plant_status,
        start_year=earliest_start,
        retired_year=latest_retired,
        planned_retirement=_parse_date(
            _aggregate_first_non_null([m.get("planned_retirement") for m in mapped_rows])
        ),
        coal_phaseout_year=_safe_int(
            _aggregate_first_non_null([m.get("coal_phaseout_year") for m in mapped_rows])
        ),
        net_zero_year=_safe_int(
            _aggregate_first_non_null([m.get("net_zero_year") for m in mapped_rows])
        ),
        owner_operator=_str_or_none(representative.get("owner_operator")),
        parent_company=_str_or_none(representative.get("parent_company")),
        combustion_technology=_str_or_none(representative.get("combustion_technology")),
        coal_type=_str_or_none(representative.get("_raw_coal_type")),
        coal_source=_str_or_none(representative.get("coal_source")),
        location=_str_or_none(representative.get("location")),
        permits=_str_or_none(representative.get("permits")),
        permit_date=_parse_date(representative.get("permit_date")),
        owner_gem_id=_str_or_none(representative.get("owner_gem_id")),
        parent_gem_id=_str_or_none(representative.get("parent_gem_id")),
        gem_unit_phase_id=None,
        gem_location_id=loc_id,
        wiki_url=_str_or_none(representative.get("wiki_url")),
        extended_data=plant_extended if plant_extended else None,
        unit_count=len(mapped_rows),
        last_verified=datetime.now(timezone.utc),
    )
    session.add(site)
    session.add(AuditLog(
        operation="insert",
        table_name="sites",
        site_id=site_id,
        after_value={
            "name": site.name,
            "gem_location_id": loc_id,
            "unit_count": len(mapped_rows),
            "total_capacity_mw": float(total_capacity) if total_capacity else None,
        },
        source_file=str(tracker_path),
        source_row=int(mapped_rows[0]["_idx"]),
        run_id=run_id,
        message=f"Ingested plant with {len(mapped_rows)} unit(s)",
    ))

    for m in mapped_rows:
        unit_ext = _build_unit_extended(m["_raw_row"])
        unit_status = _normalise_status(m.get("_raw_status"))
        unit = SiteUnit(
            unit_id=uuid.uuid4(),
            site_id=site_id,
            gem_unit_phase_id=_str_or_none(m.get("gem_unit_phase_id")),
            unit_name=_str_or_none(m["_raw_row"].get("Unit name")),
            capacity_mw=_safe_float(m.get("installed_capacity_mw")),
            status=unit_status,
            start_year=_safe_int(m.get("start_year")),
            retired_year=_safe_int(m.get("retired_year")),
            planned_retirement=_parse_date(m.get("planned_retirement")),
            combustion_technology=_str_or_none(m.get("combustion_technology")),
            coal_type=_str_or_none(m.get("_raw_coal_type")),
            extended_data=unit_ext if unit_ext else None,
        )
        session.add(unit)

    return site, len(mapped_rows)


def _create_single_unit_plant(
    session: Session,
    idx: int,
    raw_row: pd.Series,
    tracker_path: Path,
    run_id: str,
) -> tuple[Site | None, int]:
    """Create a Site + single SiteUnit for rows without a gem_location_id."""
    mapped = {target: raw_row.get(src) for src, target in _COLUMN_MAP.items()}

    lat = _safe_float(mapped.get("latitude"))
    lon = _safe_float(mapped.get("longitude"))
    if lat is None or lon is None:
        log.warning("missing_coordinates", row=idx, name=mapped.get("name"))
        return None, 0

    country_name = str(mapped["country_name"]).strip()
    country_code = COUNTRY_NAME_TO_CODE.get(country_name, "XX")
    status = _normalise_status(mapped.get("_raw_status"))
    plant_type = _derive_plant_type(mapped.get("_raw_coal_type"))
    alt_names = _build_alt_names(mapped)
    capacity = _safe_float(mapped.get("installed_capacity_mw"))
    operating_cap = capacity if status == "operating" and capacity else None

    extended = _build_unit_extended(raw_row)
    geom_wkt = f"SRID=4326;POINT({lon} {lat})"
    site_id = uuid.uuid4()

    site = Site(
        site_id=site_id,
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
        installed_capacity_mw=capacity,
        operating_capacity_mw=operating_cap,
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
        gem_location_id=None,
        wiki_url=_str_or_none(mapped.get("wiki_url")),
        extended_data=extended if extended else None,
        unit_count=1,
        last_verified=datetime.now(timezone.utc),
    )
    session.add(site)
    session.add(AuditLog(
        operation="insert",
        table_name="sites",
        site_id=site_id,
        after_value={"name": site.name, "gem_location_id": None},
        source_file=str(tracker_path),
        source_row=int(idx) if isinstance(idx, (int, float)) else None,
        run_id=run_id,
        message="Ingested single-unit plant (no location ID)",
    ))

    unit = SiteUnit(
        unit_id=uuid.uuid4(),
        site_id=site_id,
        gem_unit_phase_id=_str_or_none(mapped.get("gem_unit_phase_id")),
        unit_name=_str_or_none(raw_row.get("Unit name")),
        capacity_mw=capacity,
        status=status,
        start_year=_safe_int(mapped.get("start_year")),
        retired_year=_safe_int(mapped.get("retired_year")),
        planned_retirement=_parse_date(mapped.get("planned_retirement")),
        combustion_technology=_str_or_none(mapped.get("combustion_technology")),
        coal_type=_str_or_none(mapped.get("_raw_coal_type")),
        extended_data=extended if extended else None,
    )
    session.add(unit)

    return site, 1


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
            unit_count=1,
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
