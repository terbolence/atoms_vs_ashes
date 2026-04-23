# man_hours: 1.0
"""Config + result dataclasses for the sensitivity suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from atoms_vs_ashes.scoring.sensitivity import MC_DEFAULT_ITERATIONS

INCLUDE_CHOICES = ("weights", "mc", "threshold", "country")
DEFAULT_AUDIT_DIR = Path("audit/post_processing/06_scoring")
DEFAULT_RUBRIC_DIR = "config/scoring_rubrics"


@dataclass
class SensitivitySuiteConfig:
    """User-facing sensitivity-run parameters (mirrored on the CLI)."""

    iterations: int = MC_DEFAULT_ITERATIONS
    preset_label: str | None = None
    include_weights: bool = True
    include_mc: bool = True
    include_country: bool = True
    include_threshold: bool = False
    weight_profile_base: str = "baseline"
    seed: int = 42
    rubric_dir: str = DEFAULT_RUBRIC_DIR
    audit_dir: Path = field(default_factory=lambda: DEFAULT_AUDIT_DIR)
    progress_enabled: bool = True
    top_n_country: int = 20


@dataclass
class SensitivitySuiteResult:
    """Machine-readable return value for tests / callers."""

    run_id: str
    pairs: int
    iterations: int
    preset_label: str | None
    weight_rows_persisted: int
    mc_rows_persisted: int
    country_balanced_rows_persisted: int
    country_report: dict | None
    audit_path: Path
    mc_label: str
    threshold_rows_persisted: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "pairs": self.pairs,
            "iterations": self.iterations,
            "preset_label": self.preset_label,
            "weight_rows_persisted": self.weight_rows_persisted,
            "mc_rows_persisted": self.mc_rows_persisted,
            "country_balanced_rows_persisted": self.country_balanced_rows_persisted,
            "threshold_rows_persisted": self.threshold_rows_persisted,
            "country_report": self.country_report,
            "audit_path": str(self.audit_path),
            "mc_label": self.mc_label,
            "notes": self.notes,
        }
