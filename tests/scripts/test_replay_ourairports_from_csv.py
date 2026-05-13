# man_hours: 0.6
"""Pure-logic tests for ``src/scripts/replay_ourairports_from_csv.py``.

No DB, no CSV download — only the decision matrix and the markdown
preview rendering. The DB I/O and CSV-loading paths are covered by
manual smoke runs (Phase 4 / Phase 5), not by this unit suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _import_module():
    import importlib.util
    name = "replay_ourairports_from_csv"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name,
        REPO_ROOT / "src" / "scripts" / "replay_ourairports_from_csv.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # required for @dataclass resolution
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# decide_writes
# ---------------------------------------------------------------------------

class TestDecideWrites:
    def test_only_nulls_writes_only_null_columns(self):
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": "small_airport",
                "nearest_airport_runway_length_m": None,
                "nearest_airport_scheduled_service": None,
            },
            replayed={
                "nearest_airport_class": "small_airport",
                "nearest_airport_runway_length_m": 1500.0,
                "nearest_airport_scheduled_service": True,
            },
            only_nulls=True,
            overwrite_with_better=False,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_class"] == "skip-noop"
        assert verdict["nearest_airport_runway_length_m"] == "write-null"
        assert verdict["nearest_airport_scheduled_service"] == "write-null"

    def test_only_nulls_does_not_overwrite_nonnull_diff(self):
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": "medium_airport",
                "nearest_airport_runway_length_m": 1200.0,
                "nearest_airport_scheduled_service": False,
            },
            replayed={
                "nearest_airport_class": "small_airport",
                "nearest_airport_runway_length_m": 800.0,
                "nearest_airport_scheduled_service": True,
            },
            only_nulls=True,
            overwrite_with_better=False,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_class"] == "skip-nonnull"
        assert verdict["nearest_airport_runway_length_m"] == "skip-nonnull"
        assert verdict["nearest_airport_scheduled_service"] == "skip-nonnull"

    def test_overwrite_with_better_promotes_diffs(self):
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": "medium_airport",
                "nearest_airport_runway_length_m": 1200.0,
                "nearest_airport_scheduled_service": False,
            },
            replayed={
                "nearest_airport_class": "large_airport",
                "nearest_airport_runway_length_m": 3500.0,
                "nearest_airport_scheduled_service": True,
            },
            only_nulls=False,
            overwrite_with_better=True,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_class"] == "overwrite"
        assert verdict["nearest_airport_runway_length_m"] == "overwrite"
        assert verdict["nearest_airport_scheduled_service"] == "overwrite"

    def test_no_replay_value_skips(self):
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": None,
                "nearest_airport_runway_length_m": None,
                "nearest_airport_scheduled_service": None,
            },
            replayed={
                "nearest_airport_class": "heliport",
                "nearest_airport_runway_length_m": None,
                "nearest_airport_scheduled_service": False,
            },
            only_nulls=True,
            overwrite_with_better=False,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_class"] == "write-null"
        assert verdict["nearest_airport_runway_length_m"] == "skip-no-replay"
        assert verdict["nearest_airport_scheduled_service"] == "write-null"

    def test_runway_length_tolerance(self):
        """1 m drift is treated as a no-op (Numeric(8,1) round-trip noise)."""
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": "small_airport",
                "nearest_airport_runway_length_m": 1219.0,
                "nearest_airport_scheduled_service": False,
            },
            replayed={
                "nearest_airport_class": "small_airport",
                "nearest_airport_runway_length_m": 1219.2,
                "nearest_airport_scheduled_service": False,
            },
            only_nulls=False,
            overwrite_with_better=True,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_runway_length_m"] == "skip-noop"

    def test_boolean_equality_does_not_collapse_to_zero(self):
        """``False`` and ``None`` must not be conflated by float coercion."""
        m = _import_module()
        decisions = m.decide_writes(
            current={
                "nearest_airport_class": None,
                "nearest_airport_runway_length_m": None,
                "nearest_airport_scheduled_service": False,
            },
            replayed={
                "nearest_airport_class": None,
                "nearest_airport_runway_length_m": None,
                "nearest_airport_scheduled_service": True,
            },
            only_nulls=False,
            overwrite_with_better=True,
        )
        verdict = {d.column: d.action for d in decisions}
        assert verdict["nearest_airport_scheduled_service"] == "overwrite"


# ---------------------------------------------------------------------------
# render_three_site_preview_md
# ---------------------------------------------------------------------------

def test_render_three_site_preview_md_shape():
    m = _import_module()
    decisions = m.decide_writes(
        current={
            "nearest_airport_class": "small_airport",
            "nearest_airport_runway_length_m": None,
            "nearest_airport_scheduled_service": False,
        },
        replayed={
            "nearest_airport_class": "small_airport",
            "nearest_airport_runway_length_m": 1500.0,
            "nearest_airport_scheduled_service": True,
        },
        only_nulls=True,
        overwrite_with_better=False,
    )
    md = m.render_three_site_preview_md(
        [
            {
                "site_id": "00000000-0000-0000-0000-000000000001",
                "country": "RO", "name": "Test Plant",
                "lat": 44.5, "lon": 26.0,
                "replay": {
                    "_nearest_airport_km": 12.3,
                    "_nearest_airport_name": "Demo Airfield",
                    "_nearest_airport_ident": "RO-XYZ",
                    "_nearest_airport_country": "RO",
                },
                "decisions": decisions,
            },
        ],
        mode="only-nulls",
    )
    assert "# HI-01 / OurAirports — three-site dry-run preview" in md
    assert "RO — Test Plant" in md
    assert "ident=`RO-XYZ`" in md
    assert "**write-null**" in md  # decision verdict appears
    assert "rubric-band shift forecast: **none**" in md
