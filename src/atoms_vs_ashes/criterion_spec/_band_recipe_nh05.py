# man_hours: 0.4
"""NH-05 geotechnical mine-distance band recipe."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.schema import BandSpec


def _km(value: float) -> str:
    rounded = round(float(value), 6)
    if rounded.is_integer():
        return f"{rounded:.1f}"
    return f"{rounded:g}"


def nh05_mine_composite(pivot_km: float) -> list[BandSpec]:
    """Return ranking-only NH-05 bands from the editable mine-distance pivot."""
    f = max(float(pivot_km), 0.1)
    m = "mining_void_distance_km"
    return [
        BandSpec(
            score_range=(9, 10),
            condition_expr=(
                "karst_severity == 'none' and subsidence_risk_class in [null, 'none'] and "
                f"({m} >= {_km(5.0 * f)} or {m} is null)"
            ),
            descriptor="No karst; mine-feature distance well above the score-5 pivot (or unknown).",
        ),
        BandSpec(
            score_range=(7, 8),
            condition_expr=(
                "karst_severity in [null, 'none'] and "
                "subsidence_risk_class in [null, 'none', 'low'] and "
                f"({m} >= {_km(2.0 * f)} or {m} is null)"
            ),
            descriptor="Clear mine-distance margin with low geotechnical proxy risk (or unknown).",
        ),
        BandSpec(
            score_range=(5, 6),
            condition_expr=(
                "karst_severity in [null, 'none', 'moderate'] and "
                f"({m} is null or {m} >= {_km(f)}) and "
                "subsidence_risk_class in [null, 'none', 'low', 'moderate', 'high']"
            ),
            descriptor="At or above the mine-distance score-5 pivot; review possible.",
        ),
        BandSpec(
            score_range=(3, 4),
            condition_expr=(
                f"{m} >= {_km(0.5 * f)} and {m} < {_km(f)} "
                "and karst_severity != 'high'"
            ),
            descriptor="Below the mine-distance pivot but not extreme.",
        ),
        BandSpec(
            score_range=(1, 2),
            condition_expr=f"{m} < {_km(0.5 * f)} or karst_severity == 'high'",
            descriptor="Close mine feature or high karst proxy; severe review signal.",
        ),
    ]
