# man_hours: 4.0
"""Pydantic schema + YAML loader for ``config/scoring_rubrics/*.yaml``.

One YAML file per criterion family (nh/hi/ri/ep/ns). The loader reads
all files in the rubric directory, validates them against the
``Rubric`` schema, and returns a flat dict keyed by ``criterion_id`` so
downstream code (engine, exclusionary, avoidance, composite) can look
up a criterion without caring which file it came from.

Reference: Phase 1.2 of ``siting_report_end_to_end_4a5dbb0d.plan.md``
and ``report/sites_evaluation/`` criterion tables (sections 03–07).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class Band(BaseModel):
    """One band in the 0–10 rubric (e.g. ``[7, 8]`` → Excellent)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score_range: tuple[float, float] = Field(min_length=2, max_length=2)
    condition_expr: str
    descriptor: str = ""

    @field_validator("score_range")
    @classmethod
    def _score_range_in_bounds(cls, v: tuple[float, float]) -> tuple[float, float]:
        lo, hi = v
        if not (0 <= lo <= hi <= 10):
            raise ValueError(f"score_range {v!r} must satisfy 0 <= lo <= hi <= 10")
        return v


class SubScore(BaseModel):
    """A sub-criterion used when a rubric aggregates several metrics.

    Example: NH-11 (precipitation) aggregates SPI-12, snow burden and
    annual precip. Each ``SubScore`` carries its own bands.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    weight: float | None = None
    primary_metric: str | None = None
    bands: list[Band]


class Aggregation(BaseModel):
    """How to fold sub-score scores into the criterion score."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: Literal[
        "mean_of_sub_scores",
        "weighted_mean_of_sub_scores",
        "min_of_sub_scores",
        "max_of_sub_scores",
    ]
    round_to: float | None = None
    cap_if_any_sub_score_below: dict[str, float] | None = None


class FailCondition(BaseModel):
    """Exclusionary / avoidance / review trigger attached to a criterion.

    ``pass_mark`` (optional, only meaningful when ``action == 'exclude'``)
    is the minimum 0–10 ranking score the criterion must reach for the
    site to clear the floor. A site whose evaluated score is strictly
    below ``pass_mark`` triggers the floor with a synthetic exclusion
    verdict carrying ``code = "<code>:floor"``. See
    ``report/methodology/exclusionary_floors.md`` for the source-of-truth
    rule table.

    ``extra='allow'`` mirrors :class:`Criterion`: the engine sometimes
    receives the spec YAMLs (``config/scoring_specs/*.yaml``) directly
    via ``--rubric-dir`` (see ``gui/_runner.py``), and those carry
    spec-only fields like ``threshold`` and ``threshold_affects_expr``
    that the runtime FailCondition simply ignores.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    code: str
    action: Literal["exclude", "avoidance_penalty", "screen_flag", "review_flag"]
    condition_expr: str
    descriptor: str = ""
    pass_mark: float | None = Field(default=None, ge=0.0, le=10.0)


class QualityFloor(BaseModel):
    """How much ±1-band uncertainty the engine should propagate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    low_quality_uncertainty_bands: int = 1


class DbFields(BaseModel):
    """Data anchors for a criterion — API columns + LLM prompt keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    api: list[str] = Field(default_factory=list)
    llm: str | list[str] | None = None


class Criterion(BaseModel):
    """A single rubric criterion (BF-01, NH-02, EP-05, …)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    criterion_id: str
    name: str
    phases: list[Literal["basic_filter", "exclusionary", "avoidance", "ranking"]]
    weight_factor: int = Field(ge=1, le=10)
    normalised_weight_pct: float = Field(ge=0.0, le=100.0)
    weight_factors: dict[str, int] | None = None
    weight_basis_source: dict[str, str] | None = None
    primary_metric: str | None = None
    db_fields: DbFields = Field(default_factory=DbFields)
    bands: list[Band] = Field(default_factory=list)
    sub_scores: list[SubScore] = Field(default_factory=list)
    aggregation: Aggregation | None = None
    fail_conditions: list[FailCondition] = Field(default_factory=list)
    quality_floor: QualityFloor = Field(default_factory=QualityFloor)
    notes: str | None = None

    @field_validator("weight_factors")
    @classmethod
    def _weight_factors_in_bounds(
        cls, v: dict[str, int] | None
    ) -> dict[str, int] | None:
        if v is None:
            return None
        for basis_name, weight in v.items():
            if not (1 <= weight <= 10):
                raise ValueError(
                    f"weight_factors['{basis_name}'] = {weight} must satisfy 1 <= w <= 10"
                )
        return v

    @property
    def family(self) -> str:
        """Two-letter family prefix (``nh``, ``hi``, ``ri``, ``ep``, ``ns``, ``bf``)."""
        head = self.criterion_id.split("-", 1)[0].lower()
        return head[:2]

    @property
    def is_exclusionary(self) -> bool:
        return "exclusionary" in self.phases or any(
            fc.action == "exclude" for fc in self.fail_conditions
        )

    @property
    def is_avoidance(self) -> bool:
        return "avoidance" in self.phases or any(
            fc.action == "avoidance_penalty" for fc in self.fail_conditions
        )

    @property
    def is_ranking(self) -> bool:
        return "ranking" in self.phases

    @property
    def participates_in_composite(self) -> bool:
        """True for criteria whose scores enter the weighted composite."""
        return self.is_ranking and not self.is_exclusionary

    @property
    def exclusion_pass_marks(self) -> dict[str, float]:
        """E-code -> pass_mark for every ``action: exclude`` condition.

        Returns an empty dict if the criterion has no exclusionary fail
        conditions, or if no ``pass_mark`` is declared. Used by
        :mod:`atoms_vs_ashes.scoring._safety_floor` to evaluate the
        ranking-score floor alongside the existing ``condition_expr``.
        """
        return {
            fc.code: float(fc.pass_mark)
            for fc in self.fail_conditions
            if fc.action == "exclude" and fc.pass_mark is not None
        }

    def llm_prompt_keys(self) -> list[str]:
        """Return LLM prompt keys declared on this criterion (may be empty)."""
        if self.db_fields.llm is None:
            return []
        if isinstance(self.db_fields.llm, str):
            return [self.db_fields.llm]
        return list(self.db_fields.llm)


class Rubric(BaseModel):
    """One YAML file worth of criteria (one family)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    family: str
    pass_mark_default: float = 5.0
    criteria: list[Criterion]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


# Sidecar files that live alongside template/rubric YAMLs in
# ``config/scoring_specs/`` but are NOT criterion families. Mirrors
# ``criterion_spec.loader.THRESHOLD_METADATA_FILENAME``; keep in sync if
# new sidecar shapes are introduced.
_SIDECAR_FILENAMES = frozenset({"threshold_metadata.yaml"})


def load_rubric_file(path: Path) -> Rubric:
    """Load + validate a single rubric YAML file."""
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return Rubric.model_validate(data)


def load_rubric_bundle(rubric_dir: str | Path) -> dict[str, Criterion]:
    """Load every ``*.yaml`` in ``rubric_dir`` and return a flat dict.

    Raises ``ValueError`` on duplicate ``criterion_id`` across files so
    a typo in one rubric cannot silently shadow another family.
    """
    root = Path(rubric_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Rubric directory not found: {root}")
    bundle: dict[str, Criterion] = {}
    for path in sorted(root.glob("*.yaml")):
        if path.name in _SIDECAR_FILENAMES:
            continue
        rubric = load_rubric_file(path)
        for crit in rubric.criteria:
            if crit.criterion_id in bundle:
                raise ValueError(
                    f"Duplicate criterion_id '{crit.criterion_id}' "
                    f"(second occurrence in {path.name})"
                )
            bundle[crit.criterion_id] = crit
    if not bundle:
        raise ValueError(f"No criteria loaded from {root} — empty rubric bundle")
    return bundle


_PERTURBATION_MULTIPLIERS: dict[str, float] = {
    "baseline": 1.0,
    "w_plus_20": 1.2,
    "w_minus_20": 0.8,
}


def _resolve_basis_weight(crit: Criterion, basis: str | None) -> tuple[int, str]:
    """Return ``(weight_value, basis_used)`` for a criterion.

    When ``basis`` is None or "baseline", returns ``crit.weight_factor`` with
    basis label ``"baseline"``. When ``basis`` names an entry in
    ``crit.weight_factors``, returns that value with the named label. When
    ``basis`` is named but absent from ``crit.weight_factors``, falls back to
    the baseline weight and logs a warning so the audit trail records the gap.
    """
    if basis is None or basis == "baseline":
        return crit.weight_factor, "baseline"
    table = crit.weight_factors or {}
    if basis in table:
        return table[basis], basis
    logger.warning(
        "criterion %s has no weight_factors['%s']; falling back to baseline=%d",
        crit.criterion_id,
        basis,
        crit.weight_factor,
    )
    return crit.weight_factor, "baseline"


def weight_normalisation(
    bundle: dict[str, Criterion],
    profile: str = "baseline",
    basis: str | None = None,
) -> dict[str, float]:
    """Return normalised decimal weights keyed by criterion_id.

    ``profile`` is a sensitivity perturbation (``baseline``, ``w_plus_20``,
    ``w_minus_20``) applied as a multiplicative factor on top of the basis
    weight. ``basis`` selects the weight-source per criterion: ``None`` (or
    ``"baseline"``) reads the legacy ``weight_factor`` field, while a string
    such as ``"epri"`` or ``"s_and_l"`` reads ``criterion.weight_factors[basis]``
    when present (otherwise falls back to ``weight_factor`` with a warning, so
    the rerun is reproducible even when only a subset of criteria carry the
    new basis values).

    Exclusionary criteria are gate-only; only non-exclusionary ranking
    criteria participate in the denominator.
    """
    if profile not in _PERTURBATION_MULTIPLIERS:
        raise KeyError(
            f"Unknown sensitivity profile '{profile}'. "
            f"Expected one of {sorted(_PERTURBATION_MULTIPLIERS)}."
        )
    mult = _PERTURBATION_MULTIPLIERS[profile]
    perturbed: dict[str, float] = {}
    for cid, c in bundle.items():
        if not c.participates_in_composite:
            continue
        weight_value, _ = _resolve_basis_weight(c, basis)
        perturbed[cid] = weight_value * mult
    total = sum(perturbed.values())
    if total <= 0:
        raise ValueError("Rubric bundle has no composite scoring weight to normalise")
    return {cid: w / total for cid, w in perturbed.items()}


def weight_basis_resolution(
    bundle: dict[str, Criterion],
    basis: str | None = None,
) -> dict[str, tuple[int, str]]:
    """Per-criterion ``(weight_value, basis_used)`` tuples.

    Useful for audit trails and renderer-facing provenance: the renderer can
    print ``weight 0.0308 (basis: epri)`` per criterion bullet (FB-LL-09) by
    calling this in tandem with :func:`weight_normalisation`.
    """
    return {
        cid: _resolve_basis_weight(c, basis)
        for cid, c in bundle.items()
        if c.participates_in_composite
    }
