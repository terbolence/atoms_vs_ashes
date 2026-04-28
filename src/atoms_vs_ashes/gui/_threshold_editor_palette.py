# man_hours: 0.25
"""Warm HSL palette for threshold-editor importance (exclusionary vs avoidance).

Hue differs (red vs orange); saturation and lightness patterns match so the two
families read as related signal levels.
"""

from __future__ import annotations

from typing import Literal

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview, FailConditionPreview

EXCL_BAR = "hsl(4, 56%, 46%)"
AVOID_BAR = "hsl(28, 56%, 46%)"
EXCL_ROW_BG = "hsl(4, 38%, 96%)"
AVOID_ROW_BG = "hsl(28, 38%, 96%)"
NEUTRAL_ROW_BG = "hsl(210, 14%, 97%)"
DARK_EXCL_ROW_BG = "hsl(4, 42%, 22%)"
DARK_AVOID_ROW_BG = "hsl(28, 44%, 22%)"
DARK_NEUTRAL_ROW_BG = "hsl(210, 22%, 20%)"
DARK_ROW_TEXT = "hsl(210, 40%, 96%)"
LIGHT_ROW_TEXT = "hsl(222, 47%, 11%)"

CriterionImportance = Literal["exclusionary", "avoidance", "ranking"]


def criterion_importance(crit: CriterionPreview) -> CriterionImportance:
    if crit.is_exclusionary:
        return "exclusionary"
    if "avoidance" in crit.phases or any(
        fc.action == "avoidance_penalty" for fc in crit.fail_codes
    ):
        return "avoidance"
    return "ranking"


def action_kind_label(action: str) -> str:
    if action == "exclude":
        return "exclusionary"
    if action == "avoidance_penalty":
        return "avoidance"
    return "ranking-only"


def fc_accent_bar(fc: FailConditionPreview) -> str | None:
    if fc.action == "exclude":
        return EXCL_BAR
    if fc.action == "avoidance_penalty":
        return AVOID_BAR
    return None


def criterion_expander_label(crit: CriterionPreview) -> str:
    core = (
        f"**{crit.criterion_id}** — {crit.name}  "
        f"  weight: {crit.weight_factor} ({crit.weight_normalised:.1%})"
    )
    if crit.is_exclusionary and crit.exclusion_pass_mark is not None:
        core += f"  pass-mark (floor): {crit.exclusion_pass_mark:g}"
    imp = criterion_importance(crit)
    if imp == "exclusionary":
        return f":red[{core}]"
    if imp == "avoidance":
        return f":orange[{core}]"
    return core


__all__ = [
    "AVOID_BAR",
    "AVOID_ROW_BG",
    "DARK_AVOID_ROW_BG",
    "DARK_EXCL_ROW_BG",
    "DARK_NEUTRAL_ROW_BG",
    "DARK_ROW_TEXT",
    "EXCL_BAR",
    "EXCL_ROW_BG",
    "LIGHT_ROW_TEXT",
    "NEUTRAL_ROW_BG",
    "action_kind_label",
    "criterion_expander_label",
    "criterion_importance",
    "fc_accent_bar",
]
