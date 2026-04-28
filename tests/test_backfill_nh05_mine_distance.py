# man_hours: 0.25
"""Regression tests for NH-05 mine-distance backfill parsing."""

from __future__ import annotations

import pytest

from scripts.backfill_nh05_mine_distance import distance_from_raw_response


def test_distance_from_raw_response_reads_egdi_mine_layers() -> None:
    response_body = {
        "layers": [
            {
                "layer_name": "ms:egdi_mines",
                "response_body": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [0.01, 0.0]},
                            "properties": {"name": "test mine"},
                        }
                    ],
                },
            },
            {
                "layer_name": "ms:unrelated",
                "response_body": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [9.0, 9.0]},
                            "properties": {},
                        }
                    ],
                },
            },
        ]
    }

    distance_km, feature_count = distance_from_raw_response(
        response_body, lat=0.0, lon=0.0,
    )

    assert feature_count == 1
    assert distance_km == pytest.approx(1.112, abs=0.01)
