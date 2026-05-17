# man_hours: 1.0
from __future__ import annotations

import uuid
from pathlib import Path

from scripts import backfill_s38_coast_distance as backfill


def _item(distance_km: float, name: str = "Braila power station"):
    return backfill.SiteCoastDistance(
        site_id=uuid.uuid4(),
        site_name=name,
        country_code="RO",
        distance_km=distance_km,
        feature_count=3,
        source_path=Path("data/cartography/ne_50m_coastline.geojson"),
    )


def test_summarize_reports_threshold_buckets_and_anchors() -> None:
    summary = backfill.summarize([
        _item(1.0, "Constanta test"),
        _item(4.0, "Near coast"),
        _item(7.0, "Coastal buffer"),
        _item(25.0, "Regional"),
        _item(120.0, "Braila power station"),
    ])

    assert summary["buckets"] == {
        "<2": 1,
        "2-5": 1,
        "5-10": 1,
        "10-50": 1,
        ">50": 1,
    }
    assert summary["anchors"][-1]["site_name"] == "Braila power station"


def test_merge_comment_is_idempotent() -> None:
    item = _item(121.234)
    first = backfill._merge_comment("GFMS: site is inland", item)
    second = backfill._merge_comment(first, item)

    assert second.count("Natural Earth coastline distance:") == 1
    assert "121.234 km" in second
    assert "GFMS: site is inland" in second
