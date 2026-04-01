# man_hours: 3.0
"""Unit tests for site ingestion helpers (no DB required)."""

from atoms_vs_ashes.ingest.sites import (
    COUNTRY_NAME_TO_CODE,
    _build_alt_names,
    _derive_plant_type,
    _normalise_status,
    _parse_date,
    _safe_float,
    _safe_int,
)


def test_country_map_has_required_countries():
    required = {"Romania", "Serbia", "Armenia", "Poland", "Turkey"}
    assert required.issubset(set(COUNTRY_NAME_TO_CODE.keys()))


def test_country_map_iso_codes():
    assert COUNTRY_NAME_TO_CODE["Romania"] == "RO"
    assert COUNTRY_NAME_TO_CODE["Armenia"] == "AM"
    assert COUNTRY_NAME_TO_CODE["Turkey"] == "TR"


def test_normalise_status():
    assert _normalise_status("operating") == "operating"
    assert _normalise_status("pre-permit") == "pre_permit"
    assert _normalise_status("RETIRED") == "retired"
    assert _normalise_status(None) == "other"
    assert _normalise_status("") == "other"


def test_derive_plant_type():
    assert _derive_plant_type("lignite") == "lignite"
    assert _derive_plant_type("bituminous") == "coal"
    assert _derive_plant_type("sub-bituminous") == "coal"
    assert _derive_plant_type(None) == "coal"
    assert _derive_plant_type("lignite/bituminous") == "lignite"


def test_safe_int():
    assert _safe_int("2005") == 2005
    assert _safe_int("2005.0") == 2005
    assert _safe_int(None) is None
    assert _safe_int("--") is None


def test_safe_float():
    assert _safe_float("500.5") == 500.5
    assert _safe_float(None) is None
    assert _safe_float("--") is None


def test_parse_date():
    d = _parse_date("2030-12-31")
    assert d is not None
    assert d.year == 2030
    assert _parse_date(None) is None
    assert _parse_date("--") is None


def test_build_alt_names():
    assert _build_alt_names({"_alt_name_other": "Foo", "_alt_name_local": "Bar"}) == ["Foo", "Bar"]
    assert _build_alt_names({"_alt_name_other": None, "_alt_name_local": None}) is None
    assert _build_alt_names({"_alt_name_other": "--", "_alt_name_local": ""}) is None
    assert _build_alt_names({"_alt_name_other": "nan", "_alt_name_local": "NaN"}) is None


def test_str_or_none_nan():
    from atoms_vs_ashes.ingest.sites import _str_or_none
    assert _str_or_none("nan") is None
    assert _str_or_none("NaN") is None
    assert _str_or_none("None") is None
    assert _str_or_none("valid") == "valid"
