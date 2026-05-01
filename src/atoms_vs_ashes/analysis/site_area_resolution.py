# man_hours: 1.5
"""Resolve a single site-area hectare figure from LLM, API, and NS-04 data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceTag = Literal[
    "llm",
    "api_footprint",
    "favourable_area",
    "favourable_band",
    "max_residual",
    "explicit_zero",
    "unidentified",
]


@dataclass(frozen=True)
class SiteAreaResolution:
    """Chosen hectare value and provenance for merged site-area repair."""

    value_ha: float | None
    source: SourceTag
    observation: str | None = None


def resolve_site_area_ha(
    llm_ha: float | None,
    api_footprint_ha: float | None,
    favourable_area_ha: float | None,
    *,
    big_ha: float = 10.0,
    tiny_ha: float = 1.0,
) -> SiteAreaResolution:
    """Pick one hectare value using the merged-DB precedence rule."""
    llm = _finite(llm_ha)
    api = _finite(api_footprint_ha)
    fav = _finite(favourable_area_ha)

    if llm is not None and llm > big_ha:
        return SiteAreaResolution(llm, "llm")
    if api is not None and api > big_ha:
        return SiteAreaResolution(api, "api_footprint")
    if fav is not None and fav > big_ha:
        return SiteAreaResolution(fav, "favourable_area")

    present = [v for v in (llm, api, fav) if v is not None]
    if not present:
        return _unidentified()

    if all(v == 0.0 for v in present):
        return SiteAreaResolution(0.0, "explicit_zero")

    max_present = max(present)
    if max_present < tiny_ha:
        return _unidentified()

    if tiny_ha <= max_present <= big_ha:
        if fav is not None:
            return SiteAreaResolution(fav, "favourable_band")
        return SiteAreaResolution(max_present, "max_residual")

    if fav is not None:
        return SiteAreaResolution(fav, "favourable_area")
    return SiteAreaResolution(max_present, "max_residual")


def _finite(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unidentified() -> SiteAreaResolution:
    return SiteAreaResolution(
        None,
        "unidentified",
        "area could not be identified",
    )
