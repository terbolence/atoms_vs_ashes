# man_hours: 0.2
"""Natural Earth static-vector helpers."""

from atoms_vs_ashes.connectors.natural_earth.coastline import (
    CoastDistance,
    CoastlineDataset,
    compute_distance_to_coast_km,
    default_coastline_path,
    load_coastline_dataset,
)

__all__ = [
    "CoastDistance",
    "CoastlineDataset",
    "compute_distance_to_coast_km",
    "default_coastline_path",
    "load_coastline_dataset",
]
