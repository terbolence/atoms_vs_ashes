# man_hours: 0.8
"""Dataclasses shared by GUI PDF report builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CriteriaReport:
    spec_dir: str
    compiled_sha256: str
    weight_profile: str
    qualification_mode: str
    criteria: list[Any]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MetricValue:
    key: str
    label: str
    value: Any
    units: str | None = None
    criterion_id: str | None = None


@dataclass(frozen=True)
class SiteMetricBundle:
    site_id: str
    smr_key: str
    core: list[MetricValue] = field(default_factory=list)
    criteria: list[MetricValue] = field(default_factory=list)


@dataclass(frozen=True)
class TopSiteReport:
    site_id: str
    smr_key: str
    rank: int | None
    name: str
    country_code: str
    status: str
    composite: float | None
    composite_low: float | None
    composite_high: float | None
    latitude: float | None
    longitude: float | None
    capacity_mw: float | None
    metrics: SiteMetricBundle
    detail: Any | None = None


@dataclass(frozen=True)
class CountrySensitivityReport:
    stability_rows: list[Any] = field(default_factory=list)
    sensitivity_snapshot: Any | None = None
    national_stability_rows: list[Any] = field(default_factory=list)
    national_sensitivity_snapshot: Any | None = None
    has_sensitivity: bool = False
    has_national_sensitivity: bool = False


@dataclass(frozen=True)
class CountryReport:
    country_code: str
    country_name: str
    top_n: int
    sites: list[TopSiteReport] = field(default_factory=list)
    sensitivity: CountrySensitivityReport = field(default_factory=CountrySensitivityReport)


@dataclass(frozen=True)
class CountryPackReport:
    run_id: str
    baseline_run_id: str
    weight_profile: str
    top_n: int
    scope_summary: str
    countries: list[CountryReport]
    sensitivity_run_id: str | None = None


@dataclass(frozen=True)
class ShortlistExecutiveRow:
    """One row in the consolidated shortlist table (PDF-friendly, pre-formatted)."""

    country_code: str
    national_rank: int | None
    band: str | None
    site_name: str
    site_id: str
    csr_composite: str
    cr_composite: str
    passed_exclusionary: str
    passed_avoidance: str
    acceptability: str


@dataclass(frozen=True)
class AvoidanceVerdictPdfRow:
    criterion_id: str
    verdict: str
    measured: str
    threshold: str
    justification_short: str


@dataclass(frozen=True)
class AvoidanceSitePdfSection:
    country_code: str
    site_name: str
    site_id: str
    smr_key: str
    composite: str
    verdict_rows: tuple[AvoidanceVerdictPdfRow, ...]


@dataclass(frozen=True)
class ShortlistPackReport:
    """Compact hand-pick shortlist + capped avoidance annex for PDF export."""

    scoring_run_id: str
    sensitivity_run_id: str
    smr_key: str
    weight_profile: str
    top_n: int
    scope_summary: str
    executive_rows: tuple[ShortlistExecutiveRow, ...]
    full_pass_included: bool
    full_pass_rows: tuple[tuple[str, str, str, str], ...]
    avoidance_sites_total: int
    avoidance_index_rows: tuple[tuple[str, str, str], ...]
    avoidance_sections: tuple[AvoidanceSitePdfSection, ...]

