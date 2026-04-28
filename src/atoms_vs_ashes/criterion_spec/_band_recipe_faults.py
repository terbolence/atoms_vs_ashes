"""Fault-distance scoring band recipe helpers."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.schema import BandSpec


def _km(value: float) -> str:
    rounded = round(float(value), 6)
    if rounded.is_integer():
        return f"{rounded:.1f}"
    return f"{rounded:g}"


def fault_distance_higher_is_better(metric: str, score5_pivot: float) -> list[BandSpec]:
    """Return NH-02 capable-fault separation bands."""
    f = max(float(score5_pivot), 1e-6)
    pivot_label = f"{_km(f)} km"
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=f"{metric} >= {_km(5.0 * f)}",
            descriptor=(
                "Very strong separation from mapped capable faults; "
                "surface-rupture concern effectively screened at desk-study level."
            ),
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=f"{metric} >= {_km(2.0 * f)}",
            descriptor=(
                "Clear separation from mapped capable faults; comfortably above "
                f"the {pivot_label} score boundary."
            ),
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=f"{metric} >= {_km(f)}",
            descriptor=(
                f"Borderline acceptable separation: meets the {pivot_label} score boundary; "
                "check against the 8 km conservative screen and local capability evidence."
            ),
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=f"{metric} >= {_km(0.5 * f)}",
            descriptor=(
                f"Below the {pivot_label} score boundary; close enough to require detailed "
                "paleoseismic review and likely site rejection if the fault is capable."
            ),
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{metric} >= {_km(0.2 * f)}",
            descriptor=(
                "Very close to a mapped fault; severe surface-rupture concern "
                "with little practical siting margin."
            ),
        ),
        BandSpec(
            score_range=(0, 0),
            condition_expr=f"{metric} < {_km(0.2 * f)}",
            descriptor=(
                "Within or adjacent to a mapped fault trace; surface rupture "
                "cannot be screened out."
            ),
        ),
    ]
