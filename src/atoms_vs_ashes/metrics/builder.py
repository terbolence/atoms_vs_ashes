# man_hours: 2.0
"""Build a :class:`MetricsBundle` from pre-loaded scoring artefacts.

Pure-data assembly: takes a :class:`FailureBreakdown` (existing
verdict-driven aggregator), a list of baseline composite rows, and an
optional sensitivity blob, and emits the JSON-serialisable
:class:`MetricsBundle` consumed by audit MDs and the GUI.

Composites are split by ``passed_exclusionary`` so the per-country
panel can attach mean / p10 / p90 of *survivor* composites; the bundle
also holds the unranked list of survivors as ``top_n_per_country``
(plan §9 ``top_n_per_country``).

This is a slim first cut — the per-country failure-margin panel
(``per_country_margins``), the near-miss panel, and the qualification
mode wiring extend this builder in subsequent todos in the same plan.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, Mapping, Sequence

from atoms_vs_ashes.metrics._stats import composite_distribution, sort_top_n
from atoms_vs_ashes.metrics.bundle import (
    CountryStatPanel,
    CriterionStatPanel,
    MetricsBundle,
    NearMissPanel,
    PerCountryMarginPanel,
    PerPairFailure,
    SensitivityPanel,
    SmrStatPanel,
    SummaryPanel,
    TopNRow,
)
from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)


def _summary(
    breakdown: FailureBreakdown, *, qualification_mode: str
) -> SummaryPanel:
    return SummaryPanel(
        total_pairs=breakdown.total_pairs,
        survived=breakdown.survived,
        hard_only=breakdown.hard_only,
        floor_only=breakdown.floor_only,
        both=breakdown.both,
        n_distinct_sites=breakdown.n_distinct_sites,
        n_distinct_smrs=breakdown.n_distinct_smrs,
        qualification_mode=qualification_mode,
    )


def _criterion_panels(rows: Iterable[CriterionStat]) -> list[CriterionStatPanel]:
    return [CriterionStatPanel(**asdict(r)) for r in rows]


def _smr_panels(rows: Iterable[SmrStat]) -> list[SmrStatPanel]:
    return [SmrStatPanel(**asdict(r)) for r in rows]


def _country_panels(
    rows: Iterable[CountryStat],
    composites_by_country: Mapping[str, list[float]],
) -> list[CountryStatPanel]:
    panels: list[CountryStatPanel] = []
    for r in rows:
        scores = composites_by_country.get(r.country_code, [])
        dist = composite_distribution(scores)
        panels.append(
            CountryStatPanel(
                country_code=r.country_code,
                n_sites=r.n_sites,
                n_pairs=r.n_pairs,
                survived=r.survived,
                hard_only=r.hard_only,
                floor_only=r.floor_only,
                both=r.both,
                n_sites_with_survivor=r.n_sites_with_survivor,
                mean_composite=dist["mean"],
                p10_composite=dist["p10"],
                p90_composite=dist["p90"],
            )
        )
    return panels


def _composites_by_country(
    composites,
    country_by_site: Mapping[str, str],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for c in composites:
        if not getattr(c, "passed_exclusionary", False):
            continue
        score = getattr(c, "composite_score", None)
        if score is None:
            continue
        country = country_by_site.get(str(c.site_id), "??")
        out.setdefault(country, []).append(float(score))
    return out


def _top_n_rows(
    composites,
    *,
    site_names: Mapping[str, str],
    country_by_site: Mapping[str, str],
    top_n_per_country: int,
    qualification_mode: str,
) -> list[TopNRow]:
    """Emit the per-country shortlist sorted by composite score."""
    by_country: dict[str, list] = {}
    for c in composites:
        if not getattr(c, "passed_exclusionary", False):
            continue
        if qualification_mode == "strict" and not getattr(c, "passed_avoidance", True):
            continue
        country = country_by_site.get(str(c.site_id), "??")
        by_country.setdefault(country, []).append(c)

    rows: list[TopNRow] = []
    for country, items in by_country.items():
        ranked = sort_top_n(items, top_n_per_country)
        for rank, c in enumerate(ranked, start=1):
            rows.append(
                TopNRow(
                    country_code=country,
                    smr_key=c.smr_key,
                    rank=rank,
                    site_id=str(c.site_id),
                    site_name=site_names.get(str(c.site_id)),
                    composite_score=(
                        float(c.composite_score)
                        if c.composite_score is not None
                        else None
                    ),
                    composite_score_low=(
                        float(c.composite_score_low)
                        if c.composite_score_low is not None
                        else None
                    ),
                    composite_score_high=(
                        float(c.composite_score_high)
                        if c.composite_score_high is not None
                        else None
                    ),
                    family_scores=dict(c.per_category_scores or {}),
                    qualification_mode=qualification_mode,
                )
            )
    return rows


def build_metrics_bundle(  # noqa: PLR0913 - GUI-facing API
    *,
    run_id: str,
    breakdown: FailureBreakdown,
    composites: Sequence,
    country_by_site: Mapping[str, str],
    site_names: Mapping[str, str] | None = None,
    qualification_mode: str = "normal",
    top_n_per_country: int = 10,
    sensitivity: SensitivityPanel | None = None,
    near_miss: NearMissPanel | None = None,
    provenance: dict | None = None,
    per_pair_failures: Sequence[PerPairFailure] | None = None,
    per_country_margins: Sequence[PerCountryMarginPanel] | None = None,
) -> MetricsBundle:
    """Assemble the dashboard payload from existing scoring artefacts."""
    site_names = site_names or {}
    composites_by_country = _composites_by_country(composites, country_by_site)
    summary = _summary(breakdown, qualification_mode=qualification_mode)
    return MetricsBundle(
        run_id=run_id,
        summary=summary,
        per_criterion=_criterion_panels(breakdown.per_criterion),
        per_country=_country_panels(breakdown.per_country, composites_by_country),
        per_smr=_smr_panels(breakdown.per_smr),
        per_pair_failures=list(per_pair_failures or []),
        top_n_per_country=_top_n_rows(
            composites,
            site_names=site_names,
            country_by_site=country_by_site,
            top_n_per_country=top_n_per_country,
            qualification_mode=qualification_mode,
        ),
        per_country_margins=list(per_country_margins or []),
        near_miss=near_miss or NearMissPanel(),
        sensitivity=sensitivity or SensitivityPanel(),
        provenance=provenance or {},
        multi_failure_histogram=dict(breakdown.multi_failure_histogram),
    )


__all__ = ["build_metrics_bundle"]
