# man_hours: 1.0
from __future__ import annotations

import json
from pathlib import Path

from atoms_vs_ashes.connectors.natural_earth import (
    compute_distance_to_coast_km,
    load_coastline_dataset,
)


def _write_coastline(path: Path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0.0, -5.0], [0.0, 5.0]],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compute_distance_to_synthetic_coastline(tmp_path: Path) -> None:
    asset = tmp_path / "coast.geojson"
    _write_coastline(asset)
    dataset = load_coastline_dataset(asset)

    coastal = compute_distance_to_coast_km(0.0, 0.01, dataset)
    inland = compute_distance_to_coast_km(0.0, 1.0, dataset)

    assert coastal.distance_km < 2.0
    assert inland.distance_km > 100.0
    assert inland.feature_count == 1


def test_vendored_coastline_distinguishes_braila_from_constanta() -> None:
    dataset = load_coastline_dataset()

    braila = compute_distance_to_coast_km(45.165033, 27.923383, dataset)
    constanta = compute_distance_to_coast_km(44.173333, 28.638333, dataset)

    assert braila.distance_km > 50.0
    assert constanta.distance_km < 10.0
