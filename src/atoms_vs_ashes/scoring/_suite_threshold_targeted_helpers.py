# man_hours: 1.0
"""Internal helpers for :mod:`._suite_threshold_targeted`.

Kept private so the targeted-threshold driver stays under the 300-line
budget enforced by ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any, Sequence

from atoms_vs_ashes.criterion_spec.compiler import compile_bundle
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.criterion_spec.schema import (
    CriterionTemplate,
    FailConditionSpec,
)
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.scoring.composite import CompositeResult
from atoms_vs_ashes.scoring.rubric import Criterion


@dataclass
class TargetedThreshold:
    """Identifies one user-controllable threshold and its current value."""

    criterion_id: str
    code: str
    metric: str
    op: str
    units: str | None
    base_value: float
    recommended_value: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TargetedThresholdRow:
    """Single (target, perturbation) outcome row."""

    criterion_id: str
    code: str
    metric: str
    op: str
    units: str | None
    base_value: float
    perturbed_value: float
    perturbation_pct: float
    direction: str
    n_pairs_added: int
    n_pairs_removed: int
    n_pairs_evaluated: int
    mean_margin_delta: float | None
    median_margin_delta: float | None
    p95_margin_delta: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TargetedThresholdSuiteResult:
    """Full output of one targeted-threshold sensitivity sweep."""

    rows: list[TargetedThresholdRow] = field(default_factory=list)
    targets: list[TargetedThreshold] = field(default_factory=list)
    pct_steps: tuple[float, ...] = ()
    n_pairs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": [r.to_dict() for r in self.rows],
            "targets": [t.to_dict() for t in self.targets],
            "pct_steps": list(self.pct_steps),
            "n_pairs": self.n_pairs,
        }


def list_targeted_thresholds(
    template_bundle: TemplateBundle, profile: RunProfile
) -> list[TargetedThreshold]:
    """Enumerate every numeric, user-controllable fail threshold + base value."""
    targets: list[TargetedThreshold] = []
    for cid in sorted(template_bundle.by_id):
        template = template_bundle.by_id[cid]
        for fc in template.fail_conditions:
            target = _maybe_target(template, fc, profile)
            if target is not None:
                targets.append(target)
    return targets


def _maybe_target(
    template: CriterionTemplate,
    fc: FailConditionSpec,
    profile: RunProfile,
) -> TargetedThreshold | None:
    spec = fc.threshold
    if spec is None or spec.kind != "numeric":
        return None
    try:
        rec = float(spec.recommended.value)
    except (TypeError, ValueError):
        return None
    user_value: Any = (
        profile.fail_thresholds.get(template.criterion_id, {}).get(fc.code)
    )
    base_value = rec if user_value is None else float(user_value)
    return TargetedThreshold(
        criterion_id=template.criterion_id,
        code=fc.code,
        metric=spec.metric,
        op=spec.op,
        units=spec.units,
        base_value=base_value,
        recommended_value=rec,
    )


def build_overrides(
    profile: RunProfile,
    cid: str,
    code: str,
    perturbed_value: float,
) -> dict[str, dict[str, Any]]:
    """Clone the profile's fail_thresholds and inject one override."""
    new_thresholds: dict[str, dict[str, Any]] = {
        k: dict(v) for k, v in profile.fail_thresholds.items()
    }
    new_thresholds.setdefault(cid, {})[code] = perturbed_value
    return new_thresholds


def compile_for_profile(
    template_bundle: TemplateBundle,
    profile: RunProfile,
    *,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Criterion]:
    """Compile a bundle keeping the profile's weight overrides + profile."""
    return compile_bundle(
        template_bundle,
        fail_thresholds=fail_thresholds,
        weight_overrides=profile.scoring.weight_overrides,
        weight_profile=profile.weight_profile,
        expert_override=True,
    ).criteria


def diff_results(
    base: dict[tuple, CompositeResult],
    perturbed: dict[tuple, CompositeResult],
) -> tuple[int, int, list[float]]:
    """Return (n_added, n_removed, composite_deltas) of perturbed vs base."""
    added = 0
    removed = 0
    deltas: list[float] = []
    for key, base_res in base.items():
        new_res = perturbed.get(key)
        if new_res is None:
            continue
        if base_res.passed_exclusionary and not new_res.passed_exclusionary:
            removed += 1
        elif not base_res.passed_exclusionary and new_res.passed_exclusionary:
            added += 1
        if (
            base_res.composite_score is not None
            and new_res.composite_score is not None
        ):
            deltas.append(
                float(new_res.composite_score) - float(base_res.composite_score)
            )
    return added, removed, deltas


def percentile(values: Sequence[float], pct: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    idx = max(
        0,
        min(
            len(sorted_values) - 1,
            int(round(pct * (len(sorted_values) - 1))),
        ),
    )
    return sorted_values[idx]


def perturb_value(base: float, pct: float, direction: str) -> float:
    sign = -1.0 if direction == "down" else 1.0
    return base * (1.0 + sign * pct / 100.0)


def make_row(
    target: TargetedThreshold,
    pct: float,
    direction: str,
    perturbed_value: float,
    *,
    added: int,
    removed: int,
    deltas: list[float],
    n_pairs: int,
) -> TargetedThresholdRow:
    return TargetedThresholdRow(
        criterion_id=target.criterion_id,
        code=target.code,
        metric=target.metric,
        op=target.op,
        units=target.units,
        base_value=target.base_value,
        perturbed_value=perturbed_value,
        perturbation_pct=pct,
        direction=direction,
        n_pairs_added=added,
        n_pairs_removed=removed,
        n_pairs_evaluated=n_pairs,
        mean_margin_delta=(sum(deltas) / len(deltas)) if deltas else None,
        median_margin_delta=median(deltas) if deltas else None,
        p95_margin_delta=percentile(deltas, 0.95),
    )


__all__ = [
    "TargetedThreshold",
    "TargetedThresholdRow",
    "TargetedThresholdSuiteResult",
    "build_overrides",
    "compile_for_profile",
    "diff_results",
    "list_targeted_thresholds",
    "make_row",
    "percentile",
    "perturb_value",
]
