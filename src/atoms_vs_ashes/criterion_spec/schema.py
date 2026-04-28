# man_hours: 4.0
"""Pydantic schema for ``config/scoring_specs/*.yaml`` templates.

A *spec template* is a frozen, repo-committed best-practice description
of one criterion. It mirrors the existing rubric YAML format verbatim
(so today's behaviour is preserved on day one) but adds an optional
``threshold`` block on each ``fail_condition`` carrying the IAEA-anchored
recommended value, rationale, source citations, and hard ``bounds``
metadata that the GUI surfaces via the (i) info icon.

User overrides target *only* the named E/A failure thresholds; the
:mod:`compiler` translates ``(template + user fail_thresholds)`` into the
existing :class:`atoms_vs_ashes.scoring.rubric.Criterion` model so the
engine, exclusionary/avoidance evaluators, safety floor, and threshold
driver stay untouched.

See also:
- ``.cursor/plans/scoring_control_gui_872d4eb7.plan.md`` §2 for the
  two-layer model rationale.
- :mod:`atoms_vs_ashes.scoring.rubric` for the runtime ``Criterion``
  the compiler produces.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BandRecipeKind = Literal[
    "higher_is_better",
    "fault_distance_higher_is_better",
    "lower_is_better",
    "score_percent_higher_is_better",
    "capacity_margin",
    "flood_distance_or_elevation",
    "nh05_mine_composite",
]


class BandRecipeSpec(BaseModel):
    """When set, :func:`compile_bundle` can rebuild ``bands`` from a fail value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: BandRecipeKind
    fail_code: str = Field(
        ...,
        description=(
            "Key in fail_thresholds; may be band-only (no matching FailCondition row)."
        ),
    )
    metric: str | None = Field(
        default=None,
        description="Metric for recipes when the template omits primary_metric (e.g. BF-01).",
    )
    score5_pivot: float | None = None
    elevation_pass_m: float | None = None


class RecommendedValue(BaseModel):
    """IAEA / NUREG anchor + rationale shown by the GUI's (i) icon."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: Any
    rationale: str = ""
    sources: list[str] = Field(default_factory=list)


class ThresholdBounds(BaseModel):
    """Hard min/max enforced by the run-profile validator.

    For numeric thresholds both ``min`` and ``max`` are required. For
    categorical thresholds (``op == '=='`` against a string/bool literal)
    the GUI marks the row read-only and bounds are advisory only — the
    template still ships them so we can audit "which user-controlled
    parameters are categorical".
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    min: float | None = None
    max: float | None = None


class ThresholdSpec(BaseModel):
    """User-mutable failure threshold metadata attached to a fail_condition.

    The compiler uses ``metric``/``op``/``default_value`` to regenerate
    a simple ``"{metric} {op} {value}"`` ``condition_expr`` whenever the
    user overrides the threshold. When *no* override is supplied the
    original ``condition_expr`` on the fail_condition is preserved
    verbatim — this is what guarantees byte-equivalent parity with the
    legacy rubric loader.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str
    op: Literal["<", "<=", ">", ">=", "==", "!="]
    default_value: Any
    units: str | None = None
    label: str = ""
    kind: Literal["numeric", "categorical"] = "numeric"
    recommended: RecommendedValue
    bounds: ThresholdBounds = Field(default_factory=ThresholdBounds)

    @field_validator("default_value")
    @classmethod
    def _coerce_numeric_default(cls, v: Any) -> Any:
        return v

    def is_in_bounds(self, value: Any) -> bool:
        """Return ``True`` iff ``value`` is within ``bounds`` (numeric only)."""
        if self.kind != "numeric":
            return True
        try:
            f = float(value)
        except (TypeError, ValueError):
            return False
        if self.bounds.min is not None and f < self.bounds.min:
            return False
        if self.bounds.max is not None and f > self.bounds.max:
            return False
        return True


class BandSpec(BaseModel):
    """One band in the 0–10 ladder. Carried verbatim from the rubric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score_range: tuple[float, float] = Field(min_length=2, max_length=2)
    condition_expr: str
    descriptor: str = ""

    @field_validator("score_range")
    @classmethod
    def _score_range_in_bounds(
        cls, v: tuple[float, float]
    ) -> tuple[float, float]:
        lo, hi = v
        if not (0 <= lo <= hi <= 10):
            raise ValueError(
                f"score_range {v!r} must satisfy 0 <= lo <= hi <= 10"
            )
        return v


class SubScoreSpec(BaseModel):
    """A sub-criterion (composite criteria use these)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    weight: float | None = None
    primary_metric: str | None = None
    bands: list[BandSpec]


class AggregationSpec(BaseModel):
    """How sub-score scores fold into the criterion score."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: Literal[
        "mean_of_sub_scores",
        "weighted_mean_of_sub_scores",
        "min_of_sub_scores",
        "max_of_sub_scores",
    ]
    round_to: float | None = None
    cap_if_any_sub_score_below: dict[str, float] | None = None


class FailConditionSpec(BaseModel):
    """Exclusionary / avoidance / review trigger for a criterion.

    ``threshold`` is the structured user-control surface. When omitted
    the fail_condition is treated as static (e.g. categorical screen
    flags, complex multi-clause expressions); the compiler simply copies
    the original ``condition_expr`` through.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    action: Literal[
        "exclude", "avoidance_penalty", "screen_flag", "review_flag"
    ]
    condition_expr: str
    descriptor: str = ""
    pass_mark: float | None = Field(default=None, ge=0.0, le=10.0)
    threshold: ThresholdSpec | None = None
    threshold_affects_expr: bool = True
    """If False, user threshold edits never rewrite ``condition_expr`` (band pivots)."""


class QualityFloorSpec(BaseModel):
    """How much ±1-band uncertainty the engine should propagate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    low_quality_uncertainty_bands: int = 1


class DbFieldsSpec(BaseModel):
    """Data anchors for a criterion — API columns + LLM prompt keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    api: list[str] = Field(default_factory=list)
    llm: str | list[str] | None = None


BandKind = Literal[
    "numeric_lower_better",
    "numeric_higher_better",
    "numeric_window",
    "categorical_ladder",
    "multi_metric_AND",
    "composite_subscores",
]


class CriterionTemplate(BaseModel):
    """A single criterion's frozen best-practice template.

    The shape is a strict superset of today's rubric ``Criterion`` plus
    a ``band_kind`` discriminant and structured ``threshold`` metadata
    on each fail_condition.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    criterion_id: str
    name: str
    phases: list[
        Literal["basic_filter", "exclusionary", "avoidance", "ranking"]
    ]
    weight_factor: int = Field(ge=1, le=10)
    normalised_weight_pct: float = Field(ge=0.0, le=100.0)
    primary_metric: str | None = None
    band_kind: BandKind | None = None
    db_fields: DbFieldsSpec = Field(default_factory=DbFieldsSpec)
    bands: list[BandSpec] = Field(default_factory=list)
    sub_scores: list[SubScoreSpec] = Field(default_factory=list)
    aggregation: AggregationSpec | None = None
    fail_conditions: list[FailConditionSpec] = Field(default_factory=list)
    quality_floor: QualityFloorSpec = Field(default_factory=QualityFloorSpec)
    band_recipe: BandRecipeSpec | None = None

    @property
    def family(self) -> str:
        head = self.criterion_id.split("-", 1)[0].lower()
        return head[:2]

    def threshold_for_code(self, code: str) -> ThresholdSpec | None:
        """Return the ``ThresholdSpec`` for ``code`` or ``None``."""
        for fc in self.fail_conditions:
            if fc.code == code:
                return fc.threshold
        return None


class TemplateFile(BaseModel):
    """One YAML file's worth of criteria (one family)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    family: str
    pass_mark_default: float = 5.0
    criteria: list[CriterionTemplate]


__all__ = [
    "AggregationSpec",
    "BandKind",
    "BandRecipeKind",
    "BandRecipeSpec",
    "BandSpec",
    "CriterionTemplate",
    "DbFieldsSpec",
    "FailConditionSpec",
    "QualityFloorSpec",
    "RecommendedValue",
    "SubScoreSpec",
    "TemplateFile",
    "ThresholdBounds",
    "ThresholdSpec",
]
