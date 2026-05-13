# man_hours: 0.5
"""Pure-logic tests for ``src/scripts/preview_ourairports_vs_db.py``.

No DB, no CSV, no network — only the diff matrix, tolerance handling,
and the markdown rendering.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _import_module():
    """Import the pure-logic helper used by the HI-01 preview CLI."""
    import importlib.util
    name = "_preview_ourairports_diff"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name,
        REPO_ROOT / "src" / "scripts" / "_preview_ourairports_diff.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# diff_site
# ---------------------------------------------------------------------------

class TestDiffSite:
    def test_in_sync_returns_no_diffs(self):
        m = _import_module()
        proposed = {
            "nearest_airport_km": 12.34,
            "nearest_airport_name": "Demo",
            "nearest_airport_type": "small_airport",
            "nearest_airport_class": "small_airport",
            "nearest_airport_runway_length_m": 1500.0,
            "nearest_airport_scheduled_service": False,
            "nearest_flight_path_km": 6.17,
            "airport_count": 2,
            "quality": "high",
        }
        db = {
            "nearest_airport_km": Decimal("12.34"),
            "nearest_airport_name": "Demo",
            "nearest_airport_type": "small_airport",
            "nearest_airport_class": "small_airport",
            "nearest_airport_runway_length_m": Decimal("1500.0"),
            "nearest_airport_scheduled_service": False,
            "flight_path_distance_km": Decimal("6.17"),
            "airport_count": 2,
            "hi01_quality": "high",
        }
        assert m.diff_site(db_row=db, proposed=proposed) == []

    def test_distance_within_tolerance_is_in_sync(self):
        """0.005 km drift on `nearest_airport_km` is below the 0.01 km tol."""
        m = _import_module()
        proposed = {
            "nearest_airport_km": 12.345,
            "nearest_flight_path_km": 6.005,
            "nearest_airport_runway_length_m": 1500.4,
        }
        db = {
            "nearest_airport_km": Decimal("12.34"),
            "flight_path_distance_km": Decimal("6.00"),
            "nearest_airport_runway_length_m": Decimal("1500.0"),
        }
        diffs = m.diff_site(db_row=db, proposed=proposed,
                            columns=("nearest_airport_km",
                                     "flight_path_distance_km",
                                     "nearest_airport_runway_length_m"))
        assert diffs == []

    def test_distance_outside_tolerance_is_a_diff(self):
        m = _import_module()
        proposed = {"nearest_airport_km": 13.0}
        db = {"nearest_airport_km": Decimal("12.34")}
        diffs = m.diff_site(db_row=db, proposed=proposed,
                            columns=("nearest_airport_km",))
        assert len(diffs) == 1
        assert diffs[0].column == "nearest_airport_km"
        assert diffs[0].current == 12.34
        assert diffs[0].proposed == 13.0

    def test_string_diff_detected(self):
        m = _import_module()
        proposed = {"nearest_airport_name": "New Airfield"}
        db = {"nearest_airport_name": "Old Airfield"}
        diffs = m.diff_site(db_row=db, proposed=proposed,
                            columns=("nearest_airport_name",))
        assert len(diffs) == 1

    def test_null_to_value_is_a_diff(self):
        m = _import_module()
        diffs = m.diff_site(
            db_row={"nearest_airport_runway_length_m": None},
            proposed={"nearest_airport_runway_length_m": 1500.0},
            columns=("nearest_airport_runway_length_m",),
        )
        assert len(diffs) == 1
        assert diffs[0].current is None
        assert diffs[0].proposed == 1500.0

    def test_value_to_null_is_a_diff(self):
        m = _import_module()
        diffs = m.diff_site(
            db_row={"nearest_airport_runway_length_m": Decimal("1500.0")},
            proposed={"nearest_airport_runway_length_m": None},
            columns=("nearest_airport_runway_length_m",),
        )
        assert len(diffs) == 1
        assert diffs[0].current == 1500.0
        assert diffs[0].proposed is None

    def test_both_null_is_in_sync(self):
        m = _import_module()
        diffs = m.diff_site(
            db_row={"nearest_airport_runway_length_m": None},
            proposed={"nearest_airport_runway_length_m": None},
            columns=("nearest_airport_runway_length_m",),
        )
        assert diffs == []

    def test_bool_false_does_not_collapse_to_zero(self):
        """False scheduled_service must not match a 0-ish numeric proposal."""
        m = _import_module()
        diffs = m.diff_site(
            db_row={"nearest_airport_scheduled_service": False},
            proposed={"nearest_airport_scheduled_service": True},
            columns=("nearest_airport_scheduled_service",),
        )
        assert len(diffs) == 1
        assert diffs[0].current is False
        assert diffs[0].proposed is True

    def test_flight_path_column_renamed_from_result_key(self):
        """DB col `flight_path_distance_km` reads result key `nearest_flight_path_km`."""
        m = _import_module()
        diffs = m.diff_site(
            db_row={"flight_path_distance_km": Decimal("4.00")},
            proposed={"nearest_flight_path_km": 5.50},
            columns=("flight_path_distance_km",),
        )
        assert len(diffs) == 1
        assert diffs[0].column == "flight_path_distance_km"
        assert diffs[0].current == 4.0
        assert diffs[0].proposed == 5.5


# ---------------------------------------------------------------------------
# render_report_md
# ---------------------------------------------------------------------------

def test_render_report_no_changes():
    m = _import_module()
    md = m.render_report_md(
        total_sites=22,
        sites_with_changes=[],
        sites_unchanged=22,
        fetch_errors=[],
        column_change_counts={c: 0 for c in m.HI01_COLUMNS},
        run_id="hi01-preview-test",
    )
    assert "# HI-01 OurAirports — preview report" in md
    assert "Total sites considered: **22**" in md
    assert "_No sites would change. Apply step is a no-op._" in md


def test_render_report_with_changes_and_truncation():
    m = _import_module()
    sites = [
        {
            "site_id": f"00000000-0000-0000-0000-{i:012d}",
            "country_code": "RO",
            "name": f"Site {i}",
            "diffs": [{"column": "nearest_airport_km",
                       "current": 1.0, "proposed": 2.0}],
        }
        for i in range(5)
    ]
    md = m.render_report_md(
        total_sites=10,
        sites_with_changes=sites,
        sites_unchanged=5,
        fetch_errors=[],
        column_change_counts={"nearest_airport_km": 5},
        run_id="hi01-preview-test",
        head_limit=3,
    )
    assert "Sites with at least one proposed change: **5**" in md
    assert "### RO — Site 0" in md
    assert "### RO — Site 2" in md  # within head_limit
    assert "### RO — Site 3" not in md  # truncated
    assert "_+ 2 more sites" in md


def test_render_report_with_fetch_errors():
    m = _import_module()
    md = m.render_report_md(
        total_sites=2,
        sites_with_changes=[],
        sites_unchanged=1,
        fetch_errors=[{"site_id": "x", "name": "Bad",
                       "country_code": "RO", "error": "boom"}],
        column_change_counts={c: 0 for c in m.HI01_COLUMNS},
        run_id="hi01-preview-test",
    )
    assert "Fetch errors: **1**" not in md or "Fetch errors: **1**" in md
    assert "## Fetch errors" not in md  # no_changes branch returns early
    # Re-render in the with-changes branch and ensure error section appears
    md2 = m.render_report_md(
        total_sites=2,
        sites_with_changes=[{
            "site_id": "y", "country_code": "RO", "name": "OK",
            "diffs": [{"column": "nearest_airport_km",
                       "current": 1.0, "proposed": 2.0}],
        }],
        sites_unchanged=0,
        fetch_errors=[{"site_id": "x", "name": "Bad",
                       "country_code": "RO", "error": "boom"}],
        column_change_counts={"nearest_airport_km": 1},
        run_id="hi01-preview-test",
    )
    assert "## Fetch errors" in md2
    assert "| Bad | RO | `boom` |" in md2
