# man_hours: 0.3
"""Pure-logic tests for the SP-F decision matrix in
``src/scripts/replay_osm_military_from_logs.py``.

DB I/O paths are exercised manually in Phase 4 / Phase 5; this suite
pins the offline contract: ``--only-nulls`` is non-destructive,
``--overwrite-with-better`` flips only when the replayed value differs.
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
    name = "replay_osm_military_from_logs"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name,
        REPO_ROOT / "src" / "scripts" / "replay_osm_military_from_logs.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_only_nulls_writes_only_null_columns():
    m = _import_module()
    out = m.decide_hi06_writes(
        current={
            "nearest_military_class": "airfield",
            "nearest_high_consequence_military_km": None,
            "nearest_high_consequence_military_class": None,
        },
        replayed={
            "nearest_military_class": "airfield",
            "nearest_high_consequence_military_km": 18.4,
            "nearest_high_consequence_military_class": "airfield",
        },
        only_nulls=True,
        overwrite_with_better=False,
    )
    assert out == {
        "nearest_military_class": "skip-noop",
        "nearest_high_consequence_military_km": "write-null",
        "nearest_high_consequence_military_class": "write-null",
    }


def test_only_nulls_does_not_overwrite_diff():
    m = _import_module()
    out = m.decide_hi06_writes(
        current={
            "nearest_military_class": "training_area",
            "nearest_high_consequence_military_km": 25.0,
            "nearest_high_consequence_military_class": "depot",
        },
        replayed={
            "nearest_military_class": "depot",
            "nearest_high_consequence_military_km": 12.7,
            "nearest_high_consequence_military_class": "depot",
        },
        only_nulls=True,
        overwrite_with_better=False,
    )
    assert out["nearest_military_class"] == "skip-nonnull"
    assert out["nearest_high_consequence_military_km"] == "skip-nonnull"
    assert out["nearest_high_consequence_military_class"] == "skip-noop"


def test_overwrite_with_better_promotes_diffs():
    m = _import_module()
    out = m.decide_hi06_writes(
        current={
            "nearest_military_class": "training_area",
            "nearest_high_consequence_military_km": 25.0,
            "nearest_high_consequence_military_class": "depot",
        },
        replayed={
            "nearest_military_class": "depot",
            "nearest_high_consequence_military_km": 12.7,
            "nearest_high_consequence_military_class": "airfield",
        },
        only_nulls=False,
        overwrite_with_better=True,
    )
    assert out == {
        "nearest_military_class": "overwrite",
        "nearest_high_consequence_military_km": "overwrite",
        "nearest_high_consequence_military_class": "overwrite",
    }


def test_no_replay_skips():
    """When replay produces NULL (no airfield/depot in radius), do nothing."""
    m = _import_module()
    out = m.decide_hi06_writes(
        current={
            "nearest_military_class": None,
            "nearest_high_consequence_military_km": None,
            "nearest_high_consequence_military_class": None,
        },
        replayed={
            "nearest_military_class": "training_area",
            "nearest_high_consequence_military_km": None,
            "nearest_high_consequence_military_class": None,
        },
        only_nulls=True,
        overwrite_with_better=False,
    )
    assert out == {
        "nearest_military_class": "write-null",
        "nearest_high_consequence_military_km": "skip-no-replay",
        "nearest_high_consequence_military_class": "skip-no-replay",
    }


def test_distance_tolerance_1km():
    m = _import_module()
    out = m.decide_hi06_writes(
        current={
            "nearest_military_class": "depot",
            "nearest_high_consequence_military_km": 18.4,
            "nearest_high_consequence_military_class": "depot",
        },
        replayed={
            "nearest_military_class": "depot",
            "nearest_high_consequence_military_km": 18.6,
            "nearest_high_consequence_military_class": "depot",
        },
        only_nulls=False,
        overwrite_with_better=True,
    )
    assert out["nearest_high_consequence_military_km"] == "skip-noop"
