# man_hours: 0.5
"""Pure helpers for Regional tab (map quartiles, label truncation)."""

from __future__ import annotations

import pandas as pd


def truncate_site_label(name: str, max_len: int = 36) -> str:
    if len(name) <= max_len:
        return name
    return name[: max_len - 1] + "…"


# Single source for map + legend (quartile 0 = lowest composite in filter).
QUARTILE_PALETTE: list[tuple[int, int, int]] = [
    (55, 126, 184),
    (77, 175, 74),
    (152, 78, 163),
    (228, 26, 28),
]
MISSING_COMPOSITE_RGB: tuple[int, int, int] = (150, 150, 150)


def composite_quartile(series: pd.Series) -> pd.Series:
    """Assign 0–3 quartile index per row (same index as *series*). NaN → -1."""
    out = pd.Series(-1, index=series.index, dtype=int)
    valid = series.dropna()
    if len(valid) == 0:
        return out
    if len(valid) < 4:
        out.loc[valid.index] = 0
        return out
    try:
        cats = pd.qcut(valid, 4, labels=False, duplicates="drop")
        out.loc[cats.index] = cats.astype(int)
    except (ValueError, TypeError):
        out.loc[valid.index] = 0
    return out


def quartile_rgb(q: int) -> tuple[int, int, int]:
    """Discrete palette for quartile 0–3 (low → high composite)."""
    if q < 0:
        return MISSING_COMPOSITE_RGB
    return QUARTILE_PALETTE[min(q, 3)]
