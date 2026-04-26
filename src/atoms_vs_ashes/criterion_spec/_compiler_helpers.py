# man_hours: 1.5
"""Internal helpers for :mod:`atoms_vs_ashes.criterion_spec.compiler`.

Kept private (leading underscore) so the public package surface
(``criterion_spec/__init__.py``) only exposes the high-level
``compile_bundle`` entry point.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from atoms_vs_ashes.criterion_spec.schema import (
    BandSpec,
    SubScoreSpec,
    ThresholdSpec,
)
from atoms_vs_ashes.scoring.rubric import Band, Criterion, SubScore


def render_condition(spec: ThresholdSpec, value: Any) -> str:
    """Emit ``"{metric} {op} {value}"`` with deterministic literal formatting."""
    if spec.kind == "numeric":
        return f"{spec.metric} {spec.op} {fmt_number(value)}"
    return f"{spec.metric} {spec.op} {fmt_literal(value)}"


def fmt_number(value: Any) -> str:
    f = float(value)
    if f.is_integer():
        return str(int(f))
    return repr(f)


def fmt_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return f"'{value}'"
    return str(value)


def deviation_pct(value: Any, recommended: Any) -> float | None:
    """Return signed percent deviation; ``None`` if either value is non-numeric."""
    try:
        uv, rv = float(value), float(recommended)
    except (TypeError, ValueError):
        return None
    if rv == 0:
        return 0.0 if uv == 0 else float("inf")
    return (uv - rv) / abs(rv) * 100.0


def band_to_runtime(b: BandSpec) -> Band:
    return Band(
        score_range=tuple(b.score_range),
        condition_expr=b.condition_expr,
        descriptor=b.descriptor,
    )


def sub_score_to_runtime(s: SubScoreSpec) -> SubScore:
    return SubScore(
        key=s.key,
        weight=s.weight,
        primary_metric=s.primary_metric,
        bands=[band_to_runtime(b) for b in s.bands],
    )


def normalise_weights(
    compiled: dict[str, Criterion], *, profile: str
) -> dict[str, float]:
    """Same semantics as :func:`scoring.rubric.weight_normalisation`."""
    multipliers = {"baseline": 1.0, "w_plus_20": 1.2, "w_minus_20": 0.8}
    if profile not in multipliers:
        raise KeyError(
            f"Unknown weight profile '{profile}'. "
            f"Expected one of {sorted(multipliers)}."
        )
    mult = multipliers[profile]
    raw = {cid: c.weight_factor * mult for cid, c in compiled.items()}
    total = sum(raw.values())
    if total <= 0:
        raise ValueError("Compiled bundle has zero total weight factor.")
    return {cid: w / total for cid, w in raw.items()}


def bundle_sha256(compiled: dict[str, Criterion]) -> str:
    """Stable SHA256 over the canonical JSON of every compiled criterion."""
    payload = {
        cid: c.model_dump(mode="json") for cid, c in sorted(compiled.items())
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


__all__ = [
    "band_to_runtime",
    "bundle_sha256",
    "deviation_pct",
    "fmt_literal",
    "fmt_number",
    "normalise_weights",
    "render_condition",
    "sub_score_to_runtime",
]
