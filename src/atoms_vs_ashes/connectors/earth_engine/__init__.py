# man_hours: 0.3
"""S-06 Google Earth Engine — lazy export of client (avoids structlog on models-only imports)."""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.connectors.earth_engine.models import CRITERION_IDS

__all__ = ["CRITERION_IDS", "EarthEngineConnector"]


def __getattr__(name: str) -> Any:
    if name == "EarthEngineConnector":
        from atoms_vs_ashes.connectors.earth_engine.client import EarthEngineConnector

        return EarthEngineConnector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
