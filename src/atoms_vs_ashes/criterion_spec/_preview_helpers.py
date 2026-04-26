# man_hours: 0.5
"""Internal helpers for :mod:`atoms_vs_ashes.criterion_spec.preview`.

Kept separate so the public ``preview`` module stays under the 300-line
limit imposed by ``.cursor/rules/file-size-python.mdc``.
"""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.criterion_spec.compiler import CompiledBundle, OverrideRecord
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.runprofile.schema import RunProfile


def override_for(
    cid: str, code: str, overrides: list[OverrideRecord]
) -> OverrideRecord | None:
    for ov in overrides:
        if ov.criterion_id == cid and ov.code == code:
            return ov
    return None


def diff_vs_recommended(compiled: CompiledBundle) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ov in compiled.overrides:
        if ov.user_value == ov.recommended_value:
            continue
        rows.append(
            {
                "criterion_id": ov.criterion_id,
                "code": ov.code,
                "metric": ov.metric,
                "op": ov.op,
                "user_value": ov.user_value,
                "recommended_value": ov.recommended_value,
                "deviation_pct": ov.deviation_pct,
                "out_of_bounds": ov.out_of_bounds,
            }
        )
    return rows


def validation_warnings(
    template_bundle: TemplateBundle,
    profile: RunProfile,
) -> list[str]:
    warnings: list[str] = []
    by_id = template_bundle.by_id
    for cid, codes in profile.fail_thresholds.items():
        if cid not in by_id:
            warnings.append(f"unknown_criterion={cid}")
            continue
        valid_codes = {fc.code for fc in by_id[cid].fail_conditions}
        for code in codes:
            if code not in valid_codes:
                warnings.append(f"unknown_code={cid}/{code}")
    for cid in profile.scoring.weight_overrides:
        if cid not in by_id:
            warnings.append(f"unknown_weight_override_criterion={cid}")
    return warnings


def pass_mark_lookup(template_bundle: TemplateBundle) -> dict[str, float]:
    out: dict[str, float] = {}
    for tf in template_bundle.families.values():
        for crit in tf.criteria:
            out[crit.criterion_id] = tf.pass_mark_default
    return out


def safe_thresholds(
    template_bundle: TemplateBundle,
    profile: RunProfile,
) -> dict[str, dict[str, Any]]:
    """Drop unknown criterion / code pairs so :func:`compile_bundle` succeeds."""
    out: dict[str, dict[str, Any]] = {}
    by_id = template_bundle.by_id
    for cid, codes in profile.fail_thresholds.items():
        if cid not in by_id:
            continue
        valid_codes = {fc.code for fc in by_id[cid].fail_conditions}
        kept = {code: v for code, v in codes.items() if code in valid_codes}
        if kept:
            out[cid] = kept
    return out


__all__ = [
    "diff_vs_recommended",
    "override_for",
    "pass_mark_lookup",
    "safe_thresholds",
    "validation_warnings",
]
