# man_hours: 0.25
"""ISO 3166-1 alpha-2 → display name lookup for the Results page.

The dataset is dominated by Europe + nuclear-relevant neighbours; we
keep an explicit mapping rather than pulling ``pycountry`` so the GUI
has zero new runtime dependencies. Unknown codes are returned as-is
so the picker degrades to the raw two-letter code instead of crashing.
"""

from __future__ import annotations

_CC_TO_NAME: dict[str, str] = {
    "AL": "Albania", "AT": "Austria", "BA": "Bosnia and Herzegovina",
    "BE": "Belgium", "BG": "Bulgaria", "BY": "Belarus", "CH": "Switzerland",
    "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DK": "Denmark",
    "EE": "Estonia", "ES": "Spain", "FI": "Finland", "FR": "France",
    "GB": "United Kingdom", "GR": "Greece", "HR": "Croatia", "HU": "Hungary",
    "IE": "Ireland", "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg",
    "LV": "Latvia", "MD": "Moldova", "ME": "Montenegro", "MK": "North Macedonia",
    "MT": "Malta", "NL": "Netherlands", "NO": "Norway", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "RS": "Serbia", "SE": "Sweden",
    "SI": "Slovenia", "SK": "Slovakia", "TR": "Türkiye", "UA": "Ukraine",
    "XK": "Kosovo",
}


def country_name(code: str | None) -> str:
    """Return ``"Country (CC)"`` or the raw code when unknown / empty."""
    if not code:
        return "—"
    cc = str(code).upper()
    name = _CC_TO_NAME.get(cc)
    return f"{name} ({cc})" if name else cc


def country_label_map(codes: list[str]) -> dict[str, str]:
    """Build ``{code: 'Country (CC)'}`` for picker ``format_func`` use."""
    return {c: country_name(c) for c in codes}


__all__ = ["country_label_map", "country_name"]
