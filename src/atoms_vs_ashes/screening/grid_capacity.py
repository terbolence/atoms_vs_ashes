# man_hours: 8.0
"""BF-01 Grid Capacity Basic Filter.

For each site, determine which of the deployable SMR designs can be
accommodated based on the site's grid / installed capacity, and record a
pass / fail / inconclusive verdict in ``screening_results``.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import DataQualityFlag, ScreeningResult, Site
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.screening.base import CheckSummary, ScreeningCheck, register_check

log = get_logger(__name__)

CRITERION_ID = "BF-01"
PHASE = "basic_filter"


def _resolve_capacity(site: Site) -> float | None:
    """Return the best available capacity figure for *site*.

    Preference order:
    1. ``grid_capacity_mw`` (explicit grid connection data)
    2. ``installed_capacity_mw`` (coal plant nameplate as proxy)
    """
    for attr in ("grid_capacity_mw", "installed_capacity_mw"):
        val = getattr(site, attr, None)
        if val is not None:
            return float(val)
    return None


def _smr_thresholds(settings: Settings) -> list[tuple[str, str, float]]:
    """Return ``(key, display_name, capacity_mwe)`` sorted ascending by MWe."""
    entries: list[tuple[str, str, float]] = []
    for key, spec in settings.smr_types.items():
        entries.append((key, spec["name"], float(spec["capacity_mwe"])))
    entries.sort(key=lambda t: t[2])
    return entries


def _build_threshold_text(smrs: list[tuple[str, str, float]]) -> str:
    """Compact human-readable threshold summary."""
    if not smrs:
        return ""
    parts = [f"{smrs[0][2]:.0f} MWe (min: {smrs[0][1]})"]
    ref = [s for s in smrs if s[0] == "nuscale_voygr6"]
    if ref:
        parts.append(f"{ref[0][2]:.0f} MWe (ref: {ref[0][1]})")
    parts.append(f"{smrs[-1][2]:.0f} MWe (max: {smrs[-1][1]})")
    return " / ".join(parts)


def evaluate_site(
    site_capacity_mw: float | None,
    smrs: list[tuple[str, str, float]],
) -> tuple[str, dict[str, Any], str]:
    """Pure-logic evaluation returning ``(verdict, value_dict, justification)``.

    Separated from DB concerns for easy unit testing.
    """
    if site_capacity_mw is None:
        return (
            "inconclusive",
            {"site_capacity_mw": None, "compatible": [], "incompatible": []},
            "No grid or installed capacity data available for this site",
        )

    compatible: list[str] = []
    incompatible: list[str] = []
    compatible_names: list[str] = []
    incompatible_names: list[str] = []

    for key, name, mwe in smrs:
        if site_capacity_mw >= mwe:
            compatible.append(key)
            compatible_names.append(f"{name} ({mwe:.0f} MWe)")
        else:
            incompatible.append(key)
            incompatible_names.append(f"{name} ({mwe:.0f} MWe)")

    verdict = "pass" if compatible else "fail"

    value_dict: dict[str, Any] = {
        "site_capacity_mw": site_capacity_mw,
        "compatible": compatible,
        "incompatible": incompatible,
    }

    n_compat = len(compatible)
    n_total = len(smrs)

    if verdict == "fail":
        justification = (
            f"Site capacity {site_capacity_mw:.0f} MW is below the minimum "
            f"SMR requirement ({smrs[0][2]:.0f} MWe for {smrs[0][1]})"
        )
    elif n_compat == n_total:
        justification = (
            f"Site capacity {site_capacity_mw:.0f} MW supports all "
            f"{n_total} SMR configurations"
        )
    else:
        justification = (
            f"Site capacity {site_capacity_mw:.0f} MW supports "
            f"{n_compat} of {n_total} SMR configurations "
            f"({', '.join(compatible_names)})"
        )
        if incompatible_names:
            justification += f" but not {', '.join(incompatible_names)}"

    return verdict, value_dict, justification


@register_check
class GridCapacityCheck(ScreeningCheck):
    """BF-01: Grid Capacity Basic Filter."""

    criterion_id = CRITERION_ID
    phase = PHASE

    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningResult]:
        smrs = _smr_thresholds(settings)
        if not smrs:
            log.warning("no_smr_types_configured")
            return []

        threshold_text = _build_threshold_text(smrs)
        sites = session.execute(select(Site)).scalars().all()
        results: list[ScreeningResult] = []

        for site in sites:
            capacity = _resolve_capacity(site)
            verdict, value_dict, justification = evaluate_site(capacity, smrs)

            if verdict == "inconclusive":
                session.add(
                    DataQualityFlag(
                        site_id=site.site_id,
                        dataset="sites",
                        dimension="grid_capacity",
                        level="low",
                        detail=(
                            "Neither grid_capacity_mw nor installed_capacity_mw "
                            "is set; BF-01 screening inconclusive"
                        ),
                        run_id=run_id,
                    )
                )

            results.append(
                ScreeningResult(
                    site_id=site.site_id,
                    criterion_id=self.criterion_id,
                    phase=self.phase,
                    verdict=verdict,
                    value=json.dumps(value_dict),
                    threshold=threshold_text,
                    justification=justification,
                    source_refs="sites.grid_capacity_mw / sites.installed_capacity_mw",
                    run_id=run_id,
                )
            )

        return results

    def summarise(
        self,
        results: list[ScreeningResult],
        smrs: list[tuple[str, str, float]],
    ) -> dict[str, Any]:
        """Build a tiered summary of results for display."""
        buckets: dict[str, int] = {
            "all_configs": 0,
            "reference_plus": 0,
            "mid_range": 0,
            "small_only": 0,
            "fail": 0,
            "inconclusive": 0,
        }

        ref_mwe = 462.0
        mid_floor = 300.0
        min_mwe = smrs[0][2] if smrs else 75.0
        max_mwe = smrs[-1][2] if smrs else 500.0

        for r in results:
            if r.verdict == "inconclusive":
                buckets["inconclusive"] += 1
                continue
            if r.verdict == "fail":
                buckets["fail"] += 1
                continue
            val = json.loads(r.value) if r.value else {}
            cap = val.get("site_capacity_mw", 0) or 0
            if cap >= max_mwe:
                buckets["all_configs"] += 1
            elif cap >= ref_mwe:
                buckets["reference_plus"] += 1
            elif cap >= mid_floor:
                buckets["mid_range"] += 1
            else:
                buckets["small_only"] += 1

        return buckets
