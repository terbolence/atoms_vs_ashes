# man_hours: 0.8
"""Constants and row model for the results-table deliverable.

Paths default to the v1.02 location for byte-equivalent builds against
the v1.02 ledger set. ``configure_from_format(fmt)`` rebinds them to a
``results_table`` block declared in ``report_format.json``; this is how
the v1.03 build re-targets the same code at the v1.03 ledger directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from report_format_config import ReportFormatConfig

REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATA_DIR = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/data"
)
_DEFAULT_FIGURES_DIR = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/figures"
)
_DEFAULT_FAILURE_SECTION = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/"
    "consolidated_failure_section.md"
)

DATA_DIR: Path = _DEFAULT_DATA_DIR
FIGURES_DIR: Path = _DEFAULT_FIGURES_DIR
FAILURE_SECTION: Path = _DEFAULT_FAILURE_SECTION


def configure(
    *,
    data_dir: Path | None = None,
    figures_dir: Path | None = None,
    failure_section: Path | None = None,
) -> None:
    """Rebind module-level ledger paths.

    Callers that have already imported a constant via
    ``from results_table_model import DATA_DIR`` see no change. Modules
    that dereference ``results_table_model.DATA_DIR`` at call time pick
    up the new binding. ``results_table_data`` and ``results_table_flags``
    are written that way; manual ``from ... import DATA_DIR`` usage
    outside this package is not supported.
    """
    global DATA_DIR, FIGURES_DIR, FAILURE_SECTION
    if data_dir is not None:
        DATA_DIR = Path(data_dir)
    if figures_dir is not None:
        FIGURES_DIR = Path(figures_dir)
    if failure_section is not None:
        FAILURE_SECTION = Path(failure_section)


def configure_from_format(fmt: "ReportFormatConfig") -> None:
    """Configure paths from the optional ``results_table`` block of
    ``report_format.json``. Missing keys retain the v1.02 default."""
    block = (fmt.data.get("results_table") or {}) if hasattr(fmt, "data") else {}
    root = fmt.report_root
    configure(
        data_dir=(root / block["data_dir"]) if "data_dir" in block else None,
        figures_dir=(root / block["figures_dir"]) if "figures_dir" in block else None,
        failure_section=(
            (root / block["failure_section"])
            if "failure_section" in block else None
        ),
    )

# Canonical build: scripts/build_results_table_deliverable.py (also via build_report.py).
RESULTS_TABLE_OUTPUT_STEM = "atoms_vs_ashes_results_table"

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
    "owner",
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
    owner: str
    status: str
    power_export_proxy_mw: str
    site_surface_area_ha: str
    composite_score: str
    mc_interval: str
    national_stability_band: str
    top_tier_probability: str
    exclusionary_outcome: str
    avoidance_or_failure_note: str
