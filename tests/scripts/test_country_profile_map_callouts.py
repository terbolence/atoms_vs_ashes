"""Unit tests for ``_country_profile_map._callout_text`` flag enrichment.

The 2026-05-24 results-table flag-name enrichment makes country status
maps surface real avoidance / exclusionary criteria in the PNG callout
text. Without this, the maps only said ``Avoidance flag`` and gave the
reader no idea which criterion drove the marker colour.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts._country_profile_map import (  # noqa: E402
    CALLOUT_FLAG_LIMIT,
    _callout_text,
    _map_extent,
    _popup_html,
)


def _avoidance_row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "national_rank": 4,
        "name": "Mintia-Deva power station",
        "status": "avoidance-flag",
        "composite": 6.234,
        "avoidance_named": ["Toxic/Gas Releases (HI-03)"],
        "hard_fail_named": [],
    }
    base.update(overrides)
    return base


def test_callout_renders_oneliner_rank_name_and_flags() -> None:
    """2026-05-26 polish round 3.1: the callout is a single line of
    ``#<rank> <name> | <flag list>`` so the reader can identify the
    plant on the map without cross-referencing the table. The
    remaining per-site data (capacity, surface, score) lives in the
    table cells below the map."""
    text = _callout_text(_avoidance_row())

    assert text == "#4 Mintia-Deva | Toxic/Gas Releases (HI-03)"
    assert "\n" not in text


def test_callout_caps_flags_at_three_for_png_legibility() -> None:
    """RO maps can crowd; cap the PNG label at 3 flags so the box stays
    readable. The HTML popup carries the full list."""
    row = _avoidance_row(
        avoidance_named=[
            "Aircraft Crash (HI-01)",
            "Toxic/Gas Releases (HI-03)",
            "Grid Connection (NS-02)",
            "Distance to Population Centres (RI-05)",
            "Site Footprint Adequacy (NS-05)",
        ],
    )

    text = _callout_text(row)

    assert text == (
        "#4 Mintia-Deva | Aircraft Crash (HI-01), "
        "Toxic/Gas Releases (HI-03), "
        "Grid Connection (NS-02)"
    )
    assert "Distance to Population Centres (RI-05)" not in text
    assert "Site Footprint Adequacy (NS-05)" not in text
    assert CALLOUT_FLAG_LIMIT == 3


def test_callout_for_hard_fail_row_uses_hard_fail_named() -> None:
    row = {
        "national_rank": None,
        "name": "Brasov power station",
        "status": "hard-fail",
        "composite": None,
        "avoidance_named": [],
        "hard_fail_named": [
            "Emergency Planning Feasibility (EP-01)",
            "Geotechnical: Subsidence (NH-05)",
        ],
    }

    text = _callout_text(row)

    assert text == (
        "#- Brasov | Emergency Planning Feasibility (EP-01), "
        "Geotechnical: Subsidence (NH-05)"
    )


def test_callout_for_full_pass_row_shows_rank_name_and_status_label() -> None:
    """2026-05-26 polish round 3.1: full-pass rows previously rendered
    as just ``#<rank>``. Per user direction every callout must now
    expose rank, name, and a flag-style trailer; for full-pass rows
    the trailer is the status label ``Full pass``."""
    row = {
        "national_rank": 1,
        "name": "Cernavoda power station",
        "status": "pass",
        "composite": 7.412,
        "avoidance_named": [],
        "hard_fail_named": [],
    }

    text = _callout_text(row)

    assert text == "#1 Cernavoda | Full pass"


def test_callout_handles_missing_named_keys_gracefully() -> None:
    """Pre-enrichment callers may not populate the named-flag keys;
    the writer must still produce a single-line label that carries
    rank + name without raising."""
    row = {
        "national_rank": 2,
        "name": "Legacy site",
        "status": "avoidance-flag",
        "composite": 5.0,
    }
    assert _callout_text(row) == "#2 Legacy site | Avoidance flag"


def test_map_extent_default_zooms_out_25pct() -> None:
    """The default ``padding_frac=0.50`` widens the visible window 25%
    relative to the previous ``0.30`` baseline.

    For a fixed input span the new total width is `span * 2.0`, the old
    total width was `span * 1.6`. The ratio is `2.0 / 1.6 = 1.25`.
    """
    rows = [
        {"longitude": 20.0, "latitude": 45.0},
        {"longitude": 30.0, "latitude": 50.0},
    ]

    new_extent = _map_extent(rows)
    old_extent = _map_extent(rows, padding_frac=0.30)

    new_lon_span = new_extent[1] - new_extent[0]
    old_lon_span = old_extent[1] - old_extent[0]
    new_lat_span = new_extent[3] - new_extent[2]
    old_lat_span = old_extent[3] - old_extent[2]

    assert new_lon_span / old_lon_span == pytest.approx(1.25, rel=1e-3)
    assert new_lat_span / old_lat_span == pytest.approx(1.25, rel=1e-3)


def test_map_extent_floor_pads_scale_with_zoom() -> None:
    """Single-point inputs hit the floor pad. The 2026-05-25 polish
    raises the floor pads so a single-site country still gets a wider
    surrounding view."""
    rows = [{"longitude": 25.0, "latitude": 47.0}]

    extent = _map_extent(rows)

    lon_pad = (extent[1] - extent[0]) / 2.0
    lat_pad = (extent[3] - extent[2]) / 2.0
    assert lon_pad == pytest.approx(1.875, rel=1e-3)
    assert lat_pad == pytest.approx(1.25, rel=1e-3)


def test_popup_html_carries_full_flag_lists() -> None:
    row = _avoidance_row(
        avoidance_named=[
            "Aircraft Crash (HI-01)",
            "Toxic/Gas Releases (HI-03)",
            "Grid Connection (NS-02)",
            "Distance to Population Centres (RI-05)",
        ],
    )

    html_text = _popup_html(row)

    assert "Avoidance flags:" in html_text
    assert "Aircraft Crash (HI-01)" in html_text
    assert "Distance to Population Centres (RI-05)" in html_text
