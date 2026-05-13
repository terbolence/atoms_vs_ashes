# man_hours: 0.5
"""Pure-logic tests for ``src/scripts/_verify_fix04_threeway.py``.

Exercises the per-cell verdict classifier and the record-level
evaluator without DB or filesystem dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "src" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _import_module():
    import importlib.util
    name = "_verify_fix04_threeway"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "_verify_fix04_threeway.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# classify_cell
# ---------------------------------------------------------------------------

class TestClassifyCellFlagged:
    def test_ok_flip(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="ns02_quality", a="medium", b="high", c="high",
            was_flagged=True,
        )
        assert v == "ok-flip"

    def test_fail_flip_no_op(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="ns02_quality", a="medium", b="high", c="medium",
            was_flagged=True,
        )
        assert v == "fail-flip-no-op"

    def test_fail_flip_mismatch(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="ns02_quality", a="medium", b="high", c="insufficient",
            was_flagged=True,
        )
        assert v == "fail-flip-mismatch"


class TestClassifyCellNotFlagged:
    def test_ok_stable(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="hv_line_count", a=42, b=42, c=42, was_flagged=False,
        )
        assert v == "ok-stable"

    def test_fail_stable_drift_pre(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="hv_line_count", a=40, b=42, c=42, was_flagged=False,
        )
        assert v == "fail-stable-drift-pre"

    def test_fail_stable_mismatch(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="hv_line_count", a=42, b=42, c=99, was_flagged=False,
        )
        assert v == "fail-stable-mismatch"


class TestClassifyCellNumericTolerance:
    def test_distance_tolerance_treated_as_equal(self):
        m = _import_module()
        # Tolerance is 0.01 km on nearest_*_km (per _preview_fix04_diff).
        v = m.classify_cell(
            db_col="nearest_military_km", a=2.16, b=2.165, c=2.165,
            was_flagged=False,
        )
        assert v == "ok-stable"

    def test_distance_outside_tolerance_treated_as_diff(self):
        m = _import_module()
        v = m.classify_cell(
            db_col="nearest_military_km", a=2.16, b=2.99, c=2.99,
            was_flagged=True,
        )
        assert v == "ok-flip"


# ---------------------------------------------------------------------------
# evaluate_record + flagged_set
# ---------------------------------------------------------------------------

class TestEvaluateRecord:
    def _record(self):
        # Single-domain record (military) for a clean unit test.
        return {
            "site_id": "abc",
            "diff": [
                {"domain": "military", "column": "military_count"},
                {"domain": "military", "column": "hi06_quality"},
            ],
            "fetch": {
                "military": {
                    "nearest_military_km": 2.16,
                    "nearest_military_name": "Bunker",
                    "military_count": 42,
                    "quality": "high",
                },
            },
            "db": {
                "military": {
                    "nearest_military_km": 2.16,
                    "nearest_military_name": "Bunker",
                    "military_count": 0,
                    "hi06_quality": "not_found",
                },
            },
        }

    def _post_state_clean(self):
        return {
            "military": {
                "nearest_military_km": 2.16,
                "nearest_military_name": "Bunker",
                "military_count": 42,
                "hi06_quality": "high",
            },
            "transmitter": {
                "nearest_transmitter_km": None, "transmitter_type": None,
                "transmitter_count": None, "hi07_quality": None,
            },
            "power": {
                "nearest_hv_line_km": None, "nearest_substation_km": None,
                "hv_line_count": None, "substation_count": None,
                "hv_line_voltage_kv": None, "ns02_quality": None,
            },
        }

    def test_clean_apply_has_no_failures_on_military_columns(self):
        m = _import_module()
        rec = self._record()
        flagged = m.flagged_set(rec)
        assert flagged == {
            ("military", "military_count"),
            ("military", "hi06_quality"),
        }
        # Build a JSONL fetch+db that's empty for transmitter/power so the
        # verdicts on those columns are deterministic (None==None==None).
        rec["fetch"]["transmitter"] = {
            "nearest_transmitter_km": None, "transmitter_type": None,
            "transmitter_count": None, "quality": None,
        }
        rec["fetch"]["power"] = {
            "nearest_hv_line_km": None, "nearest_substation_km": None,
            "hv_line_count": None, "substation_count": None,
            "hv_line_voltage_kv": None, "quality": None,
        }
        rec["db"]["transmitter"] = {
            "nearest_transmitter_km": None, "transmitter_type": None,
            "transmitter_count": None, "hi07_quality": None,
        }
        rec["db"]["power"] = {
            "nearest_hv_line_km": None, "nearest_substation_km": None,
            "hv_line_count": None, "substation_count": None,
            "hv_line_voltage_kv": None, "ns02_quality": None,
        }
        post = self._post_state_clean()
        failures, verdicts = m.evaluate_record(
            rec=rec, db_state=post, flagged=flagged,
        )
        assert failures == []
        # Two flagged cells became ok-flip; everything else is ok-stable.
        assert verdicts["ok-flip"] == 2
        assert verdicts["fail-flip-no-op"] == 0
        assert verdicts["fail-flip-mismatch"] == 0
        assert verdicts["fail-stable-mismatch"] == 0


# ---------------------------------------------------------------------------
# update_flip_counts
# ---------------------------------------------------------------------------

class TestUpdateFlipCounts:
    def test_landed_when_no_failure_for_flagged_cell(self):
        m = _import_module()
        flip_counts = m.empty_flip_counts()
        flagged = {("military", "military_count")}
        failures: list[dict] = []
        landed = m.update_flip_counts(
            flip_counts=flip_counts, flagged=flagged, failures=failures,
        )
        assert landed == 1
        assert flip_counts["military"]["military_count"] == {
            "expected": 1, "landed": 1,
        }

    def test_not_landed_when_failure_on_flagged_cell(self):
        m = _import_module()
        flip_counts = m.empty_flip_counts()
        flagged = {("military", "military_count")}
        failures = [{
            "domain": "military", "column": "military_count",
            "verdict": "fail-flip-no-op", "was_flagged": True,
        }]
        landed = m.update_flip_counts(
            flip_counts=flip_counts, flagged=flagged, failures=failures,
        )
        assert landed == 0
        assert flip_counts["military"]["military_count"] == {
            "expected": 1, "landed": 0,
        }
