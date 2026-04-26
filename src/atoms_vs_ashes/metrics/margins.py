# man_hours: 2.0
"""Compute per-pair failure margins and aggregate them by country.

Reads ``ScreeningVerdict`` rows + a :class:`TemplateBundle` (the new
CriterionSpec layer) + the user's ``fail_thresholds`` overrides, then
emits the ``per_pair_failures`` and ``per_country_margins`` panels of
the :class:`MetricsBundle`. Floor failures (``code:floor``) are listed
without a numeric gap — there is no single threshold to subtract; their
gap is exposed via the per-band sensitivity panel.

This module is intentionally small (≈200 lines): it exists so the
margin maths can evolve without touching the assembly path in
:mod:`atoms_vs_ashes.metrics.builder`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.criterion_spec.schema import (
    CriterionTemplate,
    ThresholdSpec,
)
from atoms_vs_ashes.db.models import ScreeningVerdict
from atoms_vs_ashes.metrics._margin_helpers import (
    base_code,
    coerce_numeric,
    is_floor_code,
    normalise_gap,
    parse_measured_json,
    percentile_of,
    severity_for,
    signed_gap,
    top_examples,
)
from atoms_vs_ashes.metrics.bundle import (
    PerCountryMarginPanel,
    PerCriterionMargin,
    PerPairFailure,
)


def _override_value(
    *,
    fail_thresholds: Mapping[str, Mapping[str, Any]],
    criterion_id: str,
    code: str,
) -> Any | None:
    overrides = fail_thresholds.get(criterion_id, {})
    if not isinstance(overrides, Mapping):
        return None
    return overrides.get(code)


def _resolve_threshold_value(
    spec: ThresholdSpec,
    *,
    fail_thresholds: Mapping[str, Mapping[str, Any]],
    criterion_id: str,
    code: str,
) -> Any:
    override = _override_value(
        fail_thresholds=fail_thresholds, criterion_id=criterion_id, code=code
    )
    return override if override is not None else spec.default_value


def _build_failure(
    verdict: ScreeningVerdict,
    *,
    template: CriterionTemplate | None,
    fail_thresholds: Mapping[str, Mapping[str, Any]],
    country_by_site: Mapping[Any, str],
    site_names: Mapping[str, str],
) -> PerPairFailure:
    """Convert one fail/inconclusive verdict into a :class:`PerPairFailure`."""
    code_raw = verdict.prompt_key or ""
    is_floor = is_floor_code(code_raw)
    canonical_code = base_code(code_raw)
    spec = (
        template.threshold_for_code(canonical_code or "")
        if template and canonical_code
        else None
    )
    metric = spec.metric if spec else None
    op = spec.op if spec else None
    threshold_value: Any = None
    if spec is not None and not is_floor:
        threshold_value = _resolve_threshold_value(
            spec,
            fail_thresholds=fail_thresholds,
            criterion_id=verdict.criterion_id,
            code=canonical_code or "",
        )

    measured = parse_measured_json(verdict.measured_value, metric)
    margin: float | None = None
    margin_norm: float | None = None
    if (
        spec is not None
        and not is_floor
        and spec.kind == "numeric"
        and op in ("<", "<=", ">", ">=", "==")
    ):
        m_num = coerce_numeric(measured)
        t_num = coerce_numeric(threshold_value)
        if m_num is not None and t_num is not None:
            margin = signed_gap(value=m_num, threshold=t_num, op=op)
            margin_norm = normalise_gap(margin, t_num)

    severity = "floor" if is_floor else severity_for(margin_norm)

    return PerPairFailure(
        site_id=str(verdict.site_id),
        site_name=site_names.get(str(verdict.site_id)),
        country_code=country_by_site.get(verdict.site_id, "??"),
        smr_key=verdict.smr_key,
        criterion_id=verdict.criterion_id,
        code=canonical_code,
        action=("exclude" if not is_floor else "exclude_floor"),
        metric=metric,
        value=measured,
        threshold=threshold_value,
        margin=margin,
        margin_norm=margin_norm,
        severity=severity,
    )


def collect_per_pair_failures(
    verdicts_by_pair: Mapping[tuple, Sequence[ScreeningVerdict]],
    *,
    template_bundle: TemplateBundle,
    fail_thresholds: Mapping[str, Mapping[str, Any]] | None = None,
    country_by_site: Mapping[Any, str],
    site_names: Mapping[str, str] | None = None,
    smr_filter: str | None = None,
) -> list[PerPairFailure]:
    """Walk failing verdicts and compute :class:`PerPairFailure` rows."""
    fail_thresholds = fail_thresholds or {}
    site_names = site_names or {}
    failures: list[PerPairFailure] = []
    for pair, verdicts in verdicts_by_pair.items():
        if smr_filter is not None and pair[1] != smr_filter:
            continue
        for v in verdicts:
            if v.phase != "exclusionary" or v.verdict != "fail":
                continue
            template = template_bundle.by_id.get(v.criterion_id)
            failures.append(
                _build_failure(
                    v,
                    template=template,
                    fail_thresholds=fail_thresholds,
                    country_by_site=country_by_site,
                    site_names=site_names,
                )
            )
    failures.sort(
        key=lambda f: (f.country_code, f.criterion_id, str(f.site_id))
    )
    return failures


def _country_pass_counts(
    pair_outcomes: Iterable,
) -> dict[str, dict[str, int]]:
    """Compute ``{country: {n_total, n_passed}}`` from pair outcomes."""
    out: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n_total": 0, "n_passed": 0}
    )
    for o in pair_outcomes:
        country = getattr(o, "country_code", "??")
        out[country]["n_total"] += 1
        if getattr(o, "bucket", None) == "survived":
            out[country]["n_passed"] += 1
    return out


def aggregate_per_country_margins(
    failures: Iterable[PerPairFailure],
    *,
    country_pair_counts: Mapping[str, Mapping[str, int]],
    examples_per_criterion: int = 3,
) -> list[PerCountryMarginPanel]:
    """Aggregate per-pair rows into per-country, per-criterion summaries."""
    grouped: dict[str, dict[tuple[str, str | None], list[PerPairFailure]]]
    grouped = defaultdict(lambda: defaultdict(list))
    for f in failures:
        grouped[f.country_code][(f.criterion_id, f.code)].append(f)

    panels: list[PerCountryMarginPanel] = []
    for country, by_crit in grouped.items():
        crits: list[PerCriterionMargin] = []
        for (cid, code), rows in by_crit.items():
            gaps = [r.margin for r in rows if r.margin is not None]
            metric = next((r.metric for r in rows if r.metric), None)
            examples = top_examples(
                [
                    {
                        "site_id": r.site_id,
                        "site_name": r.site_name,
                        "smr_key": r.smr_key,
                        "value": r.value,
                        "threshold": r.threshold,
                        "gap": r.margin,
                        "gap_norm": r.margin_norm,
                        "severity": r.severity,
                    }
                    for r in rows
                ],
                n=examples_per_criterion,
            )
            crits.append(
                PerCriterionMargin(
                    criterion_id=cid,
                    code=code,
                    metric=metric,
                    units=None,
                    n_eliminated=len(rows),
                    median_gap=percentile_of(gaps, 50),
                    p90_gap=percentile_of(gaps, 90),
                    max_gap=max(gaps) if gaps else None,
                    examples=examples,
                )
            )
        crits.sort(key=lambda c: (-c.n_eliminated, c.criterion_id))

        counts = country_pair_counts.get(country, {})
        panels.append(
            PerCountryMarginPanel(
                country_code=country,
                n_sites_total=int(counts.get("n_total", 0)),
                n_sites_passed=int(counts.get("n_passed", 0)),
                criteria_eliminating_sites=crits,
            )
        )
    panels.sort(key=lambda p: (-p.n_sites_total, p.country_code))
    return panels


__all__ = [
    "aggregate_per_country_margins",
    "collect_per_pair_failures",
]
