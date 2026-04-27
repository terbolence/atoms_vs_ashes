# man_hours: 1.0
"""Pure models and math for exclusionary failure diagnostics."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

from atoms_vs_ashes.criterion_spec.loader import load_template_bundle

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC_DIR = _REPO_ROOT / "config" / "scoring_specs"
_STEPS = (5.0, 10.0, 25.0)


@dataclass(frozen=True)
class ThresholdMeta:
    metric: str
    op: str
    units: str | None
    base_value: float


@dataclass(frozen=True)
class ExclusionFailureRow:
    site_id: str
    site_name: str
    country_code: str
    smr_key: str
    criterion_id: str
    criterion_name: str
    code: str
    measured: float | None
    threshold: float | None
    units: str | None
    required_relaxation_pct: float | None
    justification: str

    @property
    def criterion_label(self) -> str:
        return f"{self.criterion_id} — {self.criterion_name}"

    @property
    def pair_key(self) -> tuple[str, str]:
        return (self.site_id, self.smr_key)


@dataclass(frozen=True)
class ParetoRow:
    criterion_id: str
    criterion_label: str
    n_sites: int
    n_pairs: int
    n_countries: int
    n_failures: int
    n_numeric: int
    median_relaxation_pct: float | None

    @property
    def numeric_coverage_pct(self) -> float:
        return self.n_numeric / self.n_failures * 100 if self.n_failures else 0.0


@dataclass(frozen=True)
class GapDistributionRow:
    criterion_label: str
    site_name: str
    country_code: str
    smr_key: str
    code: str
    measured: float | None
    threshold: float | None
    units: str | None
    required_relaxation_pct: float
    justification: str


@dataclass(frozen=True)
class UnlockCurveRow:
    criterion_label: str
    step_pct: float
    criterion_failures_resolved: int
    single_criterion_survivor_unlocks: int


@dataclass(frozen=True)
class DiagnosticsSummary:
    n_failures: int
    n_numeric_failures: int
    n_sites: int
    n_pairs: int


@dataclass(frozen=True)
class ExclusionDiagnostics:
    summary: DiagnosticsSummary
    pareto: list[ParetoRow]
    gaps: list[GapDistributionRow]
    unlocks: list[UnlockCurveRow]
    failures: list[ExclusionFailureRow]


def required_relaxation_pct(
    measured: float | None, threshold: float | None, op: str | None,
) -> float | None:
    """Return direction-aware threshold relaxation needed for pass."""
    if measured is None or threshold is None or op is None or threshold == 0:
        return None
    if op in (">", ">="):
        raw = measured - threshold
    elif op in ("<", "<="):
        raw = threshold - measured
    else:
        return None
    return max(0.0, raw / abs(threshold) * 100.0)


def margin_from_payload(
    criterion_id: str,
    code: str,
    measured_value: str | None,
    *,
    numeric_measured: Any = None,
    numeric_threshold: Any = None,
    threshold_text: str | None = None,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
) -> tuple[float | None, float | None, str | None, float | None]:
    """Extract measured, threshold, units, and relaxation from a verdict."""
    payload = _json_dict(measured_value)
    if code.endswith(":floor"):
        measured = _float(payload.get("score_0_10"))
        threshold = _float(payload.get("pass_mark"))
        pct = required_relaxation_pct(measured, threshold, "<")
        return measured, threshold, None, pct

    meta = _threshold_meta(criterion_id, code, fail_thresholds or {})
    expr = _parse_expr(threshold_text)
    op = meta.op if meta else (expr[1] if expr else None)
    units = meta.units if meta else None
    threshold = _float(numeric_threshold)
    if threshold is None:
        threshold = meta.base_value if meta else (expr[2] if expr else None)
    measured = _float(numeric_measured)
    if measured is None:
        metric = meta.metric if meta else (expr[0] if expr else None)
        measured = _float(payload.get(metric)) if metric else None
    pct = required_relaxation_pct(measured, threshold, op)
    return measured, threshold, units, pct


def aggregate_diagnostics(
    failures: list[ExclusionFailureRow],
    *,
    unlock_steps: tuple[float, ...] = _STEPS,
) -> ExclusionDiagnostics:
    """Build Pareto, gap-distribution, and unlock rows from failures."""
    gaps = [
        GapDistributionRow(
            criterion_label=f.criterion_label, site_name=f.site_name,
            country_code=f.country_code, smr_key=f.smr_key, code=f.code,
            measured=f.measured, threshold=f.threshold, units=f.units,
            required_relaxation_pct=f.required_relaxation_pct,
            justification=f.justification[:240],
        )
        for f in failures if f.required_relaxation_pct is not None
    ]
    summary = DiagnosticsSummary(
        n_failures=len(failures), n_numeric_failures=len(gaps),
        n_sites=len({f.site_id for f in failures}),
        n_pairs=len({f.pair_key for f in failures}),
    )
    return ExclusionDiagnostics(
        summary=summary, pareto=_pareto_rows(failures), gaps=gaps,
        unlocks=_unlock_rows(failures, unlock_steps), failures=failures,
    )


def _pareto_rows(failures: list[ExclusionFailureRow]) -> list[ParetoRow]:
    grouped: dict[str, list[ExclusionFailureRow]] = defaultdict(list)
    for f in failures:
        grouped[f.criterion_id].append(f)
    out = []
    for cid, rows in grouped.items():
        vals = [r.required_relaxation_pct for r in rows if r.required_relaxation_pct is not None]
        out.append(ParetoRow(
            criterion_id=cid, criterion_label=rows[0].criterion_label,
            n_sites=len({r.site_id for r in rows}),
            n_pairs=len({r.pair_key for r in rows}),
            n_countries=len({r.country_code for r in rows}),
            n_failures=len(rows), n_numeric=len(vals),
            median_relaxation_pct=median(vals) if vals else None,
        ))
    return sorted(out, key=lambda r: (-r.n_sites, r.criterion_id))


def _unlock_rows(
    failures: list[ExclusionFailureRow], steps: tuple[float, ...],
) -> list[UnlockCurveRow]:
    by_site: dict[str, list[ExclusionFailureRow]] = defaultdict(list)
    by_site_criterion: dict[tuple[str, str], list[ExclusionFailureRow]] = defaultdict(list)
    for f in failures:
        by_site[f.site_id].append(f)
        by_site_criterion[(f.site_id, f.criterion_id)].append(f)
    labels = {f.criterion_id: f.criterion_label for f in failures}
    out: list[UnlockCurveRow] = []
    for cid, label in labels.items():
        for step in steps:
            resolved = {
                sid for (sid, c), rows in by_site_criterion.items()
                if c == cid and _all_clear(rows, step)
            }
            unlocked = {
                sid for sid, rows in by_site.items()
                if {r.criterion_id for r in rows} == {cid} and _all_clear(rows, step)
            }
            out.append(UnlockCurveRow(label, step, len(resolved), len(unlocked)))
    return out


def _all_clear(rows: list[ExclusionFailureRow], step: float) -> bool:
    return all(
        r.required_relaxation_pct is not None
        and r.required_relaxation_pct <= step
        for r in rows
    )


@lru_cache(maxsize=1)
def _template_index() -> dict[tuple[str, str], Any]:
    bundle = load_template_bundle(_SPEC_DIR)
    return {
        (cid, fc.code): fc
        for cid, tmpl in bundle.by_id.items()
        for fc in tmpl.fail_conditions
    }


def _threshold_meta(cid: str, code: str, thresholds: dict[str, dict[str, Any]]):
    fc = _template_index().get((cid, code.replace(":floor", "")))
    spec = getattr(fc, "threshold", None)
    if spec is None or spec.kind != "numeric":
        return None
    value = thresholds.get(cid, {}).get(fc.code, spec.default_value)
    return ThresholdMeta(spec.metric, spec.op, spec.units, float(value))


def _json_dict(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    try:
        obj = json.loads(text)
    except (TypeError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def _parse_expr(text: str | None) -> tuple[str, str, float] | None:
    if not text:
        return None
    pattern = r"([A-Za-z_][\w.]*)\s*(<=|>=|<|>|==|!=)\s*(-?\d+(?:\.\d+)?)"
    m = re.search(pattern, text)
    return (m.group(1), m.group(2), float(m.group(3))) if m else None


def _float(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


__all__ = [
    "DiagnosticsSummary", "ExclusionDiagnostics", "ExclusionFailureRow",
    "GapDistributionRow", "ParetoRow", "UnlockCurveRow",
    "aggregate_diagnostics", "margin_from_payload",
    "required_relaxation_pct",
]
