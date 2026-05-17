# man_hours: 4.1
"""Pydantic schema for ``config/run_profiles/<slug>.yaml``.

A *run profile* is the single source of truth for one execution of the
scoring + sensitivity pipeline. The schema is the contract between the
GUI / CLI and the engine: anything the GUI shows in its forms maps to a
field below, and any value the user types ends up here before reaching
:class:`atoms_vs_ashes.scoring.engine.ScoringEngine` or
:class:`atoms_vs_ashes.scoring.suite.SensitivitySuite`.

The validation logic that compares ``scope.countries`` to
``select distinct country_code from sites`` (and similar DB-backed
checks) lives in :mod:`atoms_vs_ashes.runprofile.loader` so this module
stays import-safe in non-DB contexts (tests, schema dumps for the GUI).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DbProfile = Literal["api", "llm", "merged"]
QualificationMode = Literal["normal", "strict"]
WeightProfile = Literal["baseline", "w_plus_20", "w_minus_20"]
SensitivityStage = Literal[
    "weights", "mc", "threshold", "country"
]
# Stages that the schema previously allowed but the engine never wired
# up. Kept here so legacy profiles still load: the field-validator on
# ``SensitivityBlock.enabled`` silently drops them on read.
_LEGACY_SENSITIVITY_STAGES = frozenset({"oat"})
SiteStatus = Literal[
    "announced",
    "pre_permit",
    "permitted",
    "construction",
    "operating",
    "planned_closure",
    "retired",
    "mothballed",
    "shelved",
    "cancelled",
    "other",
]


class ScopeBlock(BaseModel):
    """Country / SMR / site-status filter narrowing the run universe.

    Empty ``countries``/``smr_keys`` mean "no filter" (use everything in
    DB). The GUI surfaces these as multi-selects populated from
    ``GET /scope/countries`` and ``GET /scope/smrs``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    countries: list[str] = Field(default_factory=list)
    smr_keys: list[str] = Field(default_factory=list)
    site_status_in: list[SiteStatus] = Field(
        default_factory=lambda: [
            "announced",
            "pre_permit",
            "permitted",
            "construction",
            "operating",
            "planned_closure",
            "retired",
            "mothballed",
            "shelved",
            "cancelled",
            "other",
        ]
    )
    site_ids: list[str] = Field(default_factory=list)

    @field_validator("countries")
    @classmethod
    def _upper_iso(cls, v: list[str]) -> list[str]:
        return sorted({c.upper() for c in v if c})

    @field_validator("smr_keys")
    @classmethod
    def _strip_smr(cls, v: list[str]) -> list[str]:
        return sorted({s.strip() for s in v if s})


class ScoringBlock(BaseModel):
    """Scoring-time options the user controls per run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    unscored_fallback_score: float = Field(default=3.0, ge=0.0, le=10.0)
    unscored_fraction_warn: float = Field(default=0.05, ge=0.0, le=1.0)
    unscored_fraction_hard: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_overrides: dict[str, int] = Field(default_factory=dict)
    qualification_mode: QualificationMode = "normal"
    top_n_per_country: int = Field(default=10, ge=1, le=200)
    near_miss_gap_pct: float = Field(default=10.0, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def _hard_ge_warn(self) -> "ScoringBlock":
        if self.unscored_fraction_hard < self.unscored_fraction_warn:
            raise ValueError(
                "scoring.unscored_fraction_hard must be >= unscored_fraction_warn"
            )
        return self

    @field_validator("weight_overrides")
    @classmethod
    def _weights_in_range(cls, v: dict[str, int]) -> dict[str, int]:
        for cid, w in v.items():
            if not isinstance(w, int) or w < 1 or w > 10:
                raise ValueError(
                    f"scoring.weight_overrides[{cid}] must be int in [1, 10]; "
                    f"got {w!r}."
                )
        return v


class SensitivityBlock(BaseModel):
    """Sensitivity-suite options exposed to the user."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: list[SensitivityStage] = Field(
        default_factory=lambda: ["weights", "mc", "threshold", "country"]
    )
    mc_iterations: int = Field(default=10_000, ge=100, le=1_000_000)
    mc_seed: int = 42
    weight_perturbation_pct: float = Field(default=20.0, ge=0.0, le=100.0)
    threshold_targeted_pct: list[float] = Field(default_factory=lambda: [10.0, 25.0])
    threshold_global_stress: bool = True
    top_n_country: int = Field(default=20, ge=1, le=200)
    country_balance_max_share: float = Field(default=0.40, ge=0.0, le=1.0)
    mc_stability_band_width: float = Field(default=1.0, ge=0.0, le=10.0)

    @field_validator("enabled", mode="before")
    @classmethod
    def _dedup_stages(cls, v: list[str]) -> list[str]:
        """Drop legacy / unsupported stages and de-duplicate, in order.

        Runs in ``mode="before"`` so legacy values like ``"oat"`` are
        filtered *before* Pydantic enforces the ``SensitivityStage``
        Literal — that way an existing active-profile row carrying an
        old default still loads instead of raising a validation error.
        """
        if not isinstance(v, list):
            return v
        seen: list[str] = []
        for s in v:
            if s in _LEGACY_SENSITIVITY_STAGES:
                continue
            if s not in seen:
                seen.append(s)
        return seen

    @field_validator("threshold_targeted_pct")
    @classmethod
    def _positive_pct(cls, v: list[float]) -> list[float]:
        out = sorted({float(x) for x in v})
        for x in out:
            if x <= 0 or x > 100:
                raise ValueError(
                    f"sensitivity.threshold_targeted_pct entry {x} must be in (0, 100]"
                )
        return out


class OutputBlock(BaseModel):
    """Where the run writes audits / reports."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stamp: str = Field(default="", description="YYYYMMDD or YYYYMMDD<suffix>")
    audit_dir: str = "audit/post_processing/06_scoring"
    report_dir: str = "report/output/sensitivity"


class RunProfile(BaseModel):
    """Complete run-profile YAML — see ``config/run_profiles/<slug>.yaml``.

    Layer-2 (user-editable) of the two-layer scoring model. Validation
    enforces structural correctness; DB-backed checks (countries exist,
    SMRs exist, fail_thresholds map cleanly onto loaded templates) live
    in :mod:`atoms_vs_ashes.runprofile.loader`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_label: str = Field(min_length=1, max_length=128)
    db_profile: DbProfile = "merged"
    spec_dir: str = "config/scoring_specs"
    weight_profile: WeightProfile = "baseline"
    scope: ScopeBlock = Field(default_factory=ScopeBlock)
    fail_thresholds: dict[str, dict[str, Any]] = Field(default_factory=dict)
    expert_override: bool = False
    scoring: ScoringBlock = Field(default_factory=ScoringBlock)
    sensitivity: SensitivityBlock = Field(default_factory=SensitivityBlock)
    output: OutputBlock = Field(default_factory=OutputBlock)
    notes: str = ""

    @field_validator("fail_thresholds")
    @classmethod
    def _normalize_fail_thresholds(
        cls, v: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        for cid, codes in v.items():
            if not isinstance(codes, dict):
                raise ValueError(
                    f"fail_thresholds[{cid}] must map code -> value; "
                    f"got {type(codes).__name__}"
                )
        return v

    @field_validator("db_profile", mode="before")
    @classmethod
    def _canonical_db_profile(cls, v: Any) -> str:
        """Legacy profiles load into the canonical merged DB profile."""
        return "merged"

    def has_explicit_scope(self) -> bool:
        """``True`` if the user pinned countries or SMRs."""
        return bool(self.scope.countries or self.scope.smr_keys)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Stable dict representation used for sha256 hashing."""
        return self.model_dump(mode="json")

    def with_path(self, path: Path) -> "RunProfileWithPath":
        return RunProfileWithPath(profile=self, path=path)


class RunProfileWithPath(BaseModel):
    """A loaded :class:`RunProfile` plus its on-disk path."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    profile: RunProfile
    path: Path


__all__ = [
    "DbProfile",
    "OutputBlock",
    "QualificationMode",
    "RunProfile",
    "RunProfileWithPath",
    "ScopeBlock",
    "ScoringBlock",
    "SensitivityBlock",
    "SensitivityStage",
    "SiteStatus",
    "WeightProfile",
]
