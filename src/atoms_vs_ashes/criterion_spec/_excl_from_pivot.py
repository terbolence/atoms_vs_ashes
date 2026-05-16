# man_hours: 0.6
"""Derive a hard exclusion ``condition_expr`` from a band recipe + pivot.

For criteria that declare a ``band_recipe`` and carry an exclusionary
``fail_condition`` keyed by the same ``fail_code``, the compiler uses
this helper to keep the *hard* fail expression in lock-step with the
score-5 band boundary. One number — the pivot — therefore drives both
the bands and the exclusion, eliminating drift between e.g. NH-02's
band-5 boundary (5 km) and its hand-written 8 km hard fail.

The recipe kinds in scope are the simple monotonic ones used by today's
exclusionary criteria (``higher_is_better`` family,
``fault_distance_higher_is_better``, ``score_percent_higher_is_better``,
and ``lower_is_better``). Composite recipes (mine composite, flood
distance/elevation, capacity margin) are intentionally rejected: they
combine multiple metrics, so a single-metric derivation would silently
drop guard clauses. If a composite recipe is ever wired up to an
exclusionary code, the rule must be made explicit in YAML.
"""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec._compiler_helpers import fmt_number
from atoms_vs_ashes.criterion_spec.schema import BandRecipeKind


_HIGHER_BETTER_KINDS: frozenset[str] = frozenset(
    {
        "higher_is_better",
        "fault_distance_higher_is_better",
        "score_percent_higher_is_better",
    }
)


def excl_expr_from_recipe(
    kind: BandRecipeKind, metric: str, pivot: float
) -> str:
    """Return the hard exclusion ``condition_expr`` for ``(kind, metric, pivot)``.

    * ``higher_is_better`` / ``fault_distance_higher_is_better`` /
      ``score_percent_higher_is_better`` — exclude when the metric is
      strictly below the score-5 pivot, e.g. ``nearest_fault_km < 5``.
    * ``lower_is_better`` — exclude when the metric is strictly above
      the score-5 pivot, e.g. ``slope_angle_deg > 8``.

    Composite recipes raise :class:`ValueError` rather than guessing.
    """
    if not metric:
        raise ValueError("excl_expr_from_recipe requires a non-empty metric name")
    if kind in _HIGHER_BETTER_KINDS:
        return f"{metric} < {fmt_number(pivot)}"
    if kind == "lower_is_better":
        return f"{metric} > {fmt_number(pivot)}"
    raise ValueError(
        f"recipe kind {kind!r} is not supported for exclusion derivation; "
        "composite recipes must keep their hand-written condition_expr."
    )


__all__ = ["excl_expr_from_recipe"]
