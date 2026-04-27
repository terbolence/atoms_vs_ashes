# man_hours: 1.0
"""Batch SMR pass/fail helpers (used in tests and CLI diagnostics)."""

from __future__ import annotations

from typing import Any


def evaluate_site(
    site_value: float | None,
    smrs: list[tuple[str, str, float]],
    *,
    site_key: str,
    unit_singular: str,
    value_fmt: str,
) -> tuple[str, dict[str, Any], str]:
    """Return ``(verdict, value_dict, justification)`` for one site value vs an SMR list.

    * ``smrs`` is ``(smr_key, display_name, requirement)`` sorted ascending
      by the requirement (MWe, ha, …). A site is *compatible* with a design
      if ``site_value >= requirement`` (or ``>`` is not used — equality passes).
    """
    n = len(smrs)
    if site_value is None:
        val: dict[str, Any] = {
            site_key: None,
            "compatible": [],
            "incompatible": [k for k, _, _ in smrs],
        }
        return (
            "inconclusive",
            val,
            f"No {site_key.replace('_', ' ')} data; cannot compare to {n} SMR requirements.",
        )

    compatible: list[str] = []
    incompatible: list[str] = []
    for key, _name, need in smrs:
        (compatible if site_value >= need else incompatible).append(key)

    val = {
        site_key: site_value,
        "compatible": compatible,
        "incompatible": incompatible,
    }
    vtxt = value_fmt % (site_value,)

    if not compatible:
        vdict = {site_key: site_value, "compatible": [], "incompatible": incompatible}
        just = (
            f"Site {unit_singular} {vtxt} is below the smallest SMR in scope "
            f"({smrs[0][1]} requires {smrs[0][2]}{_suffix(unit_singular)})."
        )
        return "fail", vdict, just

    if not incompatible:
        return (
            "pass",
            val,
            f"Site {unit_singular} {vtxt} meets or exceeds all {n} SMR requirements "
            f"in scope (all clear).",
        )

    next_gate = _first_requirement_not_met(smrs, site_value)
    last_ok = _last_requirement_met(smrs, site_value)
    j_extra = f"{len(compatible)} of {n} — next unmet: {next_gate[1]}"
    if last_ok is not None:
        j_extra += f"; best fit through {last_ok[1]}."

    return "pass", val, j_extra


def _first_requirement_not_met(
    smrs: list[tuple[str, str, float]], site_value: float
) -> tuple[str, str, float]:
    for t in smrs:
        if site_value < t[2]:
            return t
    return smrs[-1]


def _last_requirement_met(
    smrs: list[tuple[str, str, float]], site_value: float
) -> tuple[str, str, float] | None:
    last: tuple[str, str, float] | None = None
    for t in smrs:
        if site_value >= t[2]:
            last = t
    return last


def _suffix(unit: str) -> str:
    if "MW" in unit or "MWe" in unit:
        return " MWe"
    if "ha" in unit:
        return " ha"
    return f" {unit}"
