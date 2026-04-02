# man_hours: 1.0
"""Screening engine — evaluates sites against configurable criteria."""

from atoms_vs_ashes.screening.base import (
    CheckSummary,
    ScreeningCheck,
    all_checks,
    get_check,
    register_check,
)

# Import concrete checks so they self-register via @register_check.
import atoms_vs_ashes.screening.grid_capacity  # noqa: F401
import atoms_vs_ashes.screening.land_area  # noqa: F401
import atoms_vs_ashes.analysis.epz_population  # noqa: F401  — RI-04, RI-05
import atoms_vs_ashes.analysis.emergency_plan  # noqa: F401  — EP-01

__all__ = [
    "CheckSummary",
    "ScreeningCheck",
    "all_checks",
    "get_check",
    "register_check",
]
