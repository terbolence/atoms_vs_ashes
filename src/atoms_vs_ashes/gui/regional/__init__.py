# man_hours: 0.2
"""Results Regional tab (composite + map)."""

from __future__ import annotations

__all__ = ["render_regional_tab"]


def __getattr__(name: str):
    if name == "render_regional_tab":
        from atoms_vs_ashes.gui.regional.render import render_regional_tab

        return render_regional_tab
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
