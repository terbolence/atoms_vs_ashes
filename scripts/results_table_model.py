# man_hours: 0.8
"""Constants and row model for the v1.2 results-table deliverable."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/data"
)
FIGURES_DIR = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures"
)
FAILURE_SECTION = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/"
    "consolidated_failure_section.md"
)

PUBLISHED_COUNTRIES: tuple[str, ...] = (
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)
NO_PASS_COUNTRIES: tuple[str, ...] = ("AL", "SI", "XK")
COUNTRY_ORDER: tuple[str, ...] = PUBLISHED_COUNTRIES + NO_PASS_COUNTRIES

COUNTRY_NAMES: dict[str, str] = {
    "AL": "Albania",
    "AT": "Austria",
    "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria",
    "CZ": "Czechia",
    "HR": "Croatia",
    "HU": "Hungary",
    "LV": "Latvia",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MK": "North Macedonia",
    "PL": "Poland",
    "RO": "Romania",
    "RS": "Serbia",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "UA": "Ukraine",
    "XK": "Kosovo",
}

CSV_COLUMNS = [
    "country_code",
    "country",
    "rank",
    "site",
    "status",
    "power_export_proxy_mw",
    "site_surface_area_ha",
    "composite_score",
    "mc_interval",
    "national_stability_band",
    "top_tier_probability",
    "exclusionary_outcome",
    "avoidance_or_failure_note",
]


@dataclass(frozen=True)
class SiteRow:
    country_code: str
    country: str
    rank: str
    site: str
    status: str
    power_export_proxy_mw: str
    site_surface_area_ha: str
    composite_score: str
    mc_interval: str
    national_stability_band: str
    top_tier_probability: str
    exclusionary_outcome: str
    avoidance_or_failure_note: str
