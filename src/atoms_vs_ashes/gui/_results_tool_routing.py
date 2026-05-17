# man_hours: 0.4
"""Pure Results-page tool routing helpers."""

SCORING_TOOLS = {
    "Coverage",
    "Sites",
    "Failure Diagnostics",
    "Avoidance Diagnostics",
    "Regional Overview",
}
REGIONAL_SENSITIVITY_TOOLS = {"Regional Stability", "Regional Sensitivity"}
NATIONAL_SENSITIVITY_TOOLS = {"National Stability", "National Sensitivity"}


def run_kind_for_tool(tool: str) -> str:
    """Return the persisted run kind required by a Results-page tool."""
    if tool in NATIONAL_SENSITIVITY_TOOLS:
        return "national_sensitivity"
    if tool in REGIONAL_SENSITIVITY_TOOLS:
        return "sensitivity"
    return "scoring"


__all__ = [
    "NATIONAL_SENSITIVITY_TOOLS",
    "REGIONAL_SENSITIVITY_TOOLS",
    "SCORING_TOOLS",
    "run_kind_for_tool",
]
