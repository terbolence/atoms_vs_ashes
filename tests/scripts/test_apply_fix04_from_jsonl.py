# man_hours: 0.6
"""Pure-logic tests for ``src/scripts/_apply_fix04_from_jsonl.py``.

No DB, no Overpass, no filesystem (except the JSONL fixture written
into ``tmp_path``). Exercises ``iter_records``, ``select_record``,
``classify_payload``, and ``empty_counts`` — the parts of the FIX-04
replay that don't touch SQLAlchemy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "src" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _import_module():
    import importlib.util
    name = "_apply_fix04_from_jsonl"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "_apply_fix04_from_jsonl.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# iter_records
# ---------------------------------------------------------------------------

class TestIterRecords:
    def test_yields_one_per_nonblank_line(self, tmp_path):
        m = _import_module()
        f = tmp_path / "fix04.jsonl"
        f.write_text(
            json.dumps({"site_id": "a"}) + "\n"
            + "\n"  # blank line
            + json.dumps({"site_id": "b"}) + "\n",
            encoding="utf-8",
        )
        records = list(m.iter_records(f))
        assert [(ln, rec["site_id"]) for ln, rec in records] == [
            (1, "a"), (3, "b"),
        ]

    def test_raises_value_error_on_bad_json(self, tmp_path):
        m = _import_module()
        f = tmp_path / "broken.jsonl"
        f.write_text("{not-json}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON at line 1"):
            list(m.iter_records(f))


# ---------------------------------------------------------------------------
# select_record
# ---------------------------------------------------------------------------

class TestSelectRecord:
    def test_no_filters_passes(self):
        m = _import_module()
        rec = {"site_id": "x", "country_code": "RO"}
        assert m.select_record(rec, countries=None, site_ids=None) is True

    def test_country_match_passes(self):
        m = _import_module()
        rec = {"site_id": "x", "country_code": "ro"}
        assert m.select_record(rec, countries={"RO"}, site_ids=None) is True

    def test_country_mismatch_filtered(self):
        m = _import_module()
        rec = {"site_id": "x", "country_code": "BG"}
        assert m.select_record(rec, countries={"RO"}, site_ids=None) is False

    def test_site_id_match_passes(self):
        m = _import_module()
        rec = {"site_id": "uuid-1", "country_code": "RO"}
        assert (
            m.select_record(rec, countries=None, site_ids={"uuid-1"}) is True
        )

    def test_site_id_mismatch_filtered(self):
        m = _import_module()
        rec = {"site_id": "uuid-2", "country_code": "RO"}
        assert (
            m.select_record(rec, countries=None, site_ids={"uuid-1"}) is False
        )

    def test_both_filters_must_pass(self):
        m = _import_module()
        rec = {"site_id": "uuid-1", "country_code": "RO"}
        assert m.select_record(
            rec, countries={"RO"}, site_ids={"uuid-1"},
        ) is True
        assert m.select_record(
            rec, countries={"BG"}, site_ids={"uuid-1"},
        ) is False
        assert m.select_record(
            rec, countries={"RO"}, site_ids={"uuid-9"},
        ) is False


# ---------------------------------------------------------------------------
# classify_payload
# ---------------------------------------------------------------------------

class TestClassifyPayload:
    def test_apply_when_payload_dict_present(self):
        m = _import_module()
        rec = {
            "fetch": {"military": {"military_count": 0, "quality": "not_found"}},
            "fetch_errors": None,
        }
        action, payload = m.classify_payload(rec, "military")
        assert action == "apply"
        assert payload == {"military_count": 0, "quality": "not_found"}

    def test_skip_error_when_label_in_fetch_errors(self):
        m = _import_module()
        rec = {
            "fetch": {"military": {"military_count": 0}},
            "fetch_errors": {"military": "504"},
        }
        action, payload = m.classify_payload(rec, "military")
        assert action == "skip-error"
        assert payload is None

    def test_skip_no_payload_when_fetch_missing(self):
        m = _import_module()
        action, payload = m.classify_payload({}, "power")
        assert action == "skip-no-payload"
        assert payload is None

    def test_skip_no_payload_when_label_value_is_none(self):
        m = _import_module()
        rec = {"fetch": {"power": None}, "fetch_errors": None}
        action, payload = m.classify_payload(rec, "power")
        assert action == "skip-no-payload"
        assert payload is None

    def test_skip_no_payload_when_label_value_not_dict(self):
        m = _import_module()
        rec = {"fetch": {"transmitter": "oops"}, "fetch_errors": None}
        action, payload = m.classify_payload(rec, "transmitter")
        assert action == "skip-no-payload"
        assert payload is None

    def test_unrelated_domain_error_does_not_block(self):
        m = _import_module()
        # An error on a *different* label should not block this one.
        rec = {
            "fetch": {"power": {"hv_line_count": 1}},
            "fetch_errors": {"military": "504"},
        }
        action, payload = m.classify_payload(rec, "power")
        assert action == "apply"
        assert payload == {"hv_line_count": 1}


# ---------------------------------------------------------------------------
# empty_counts
# ---------------------------------------------------------------------------

class TestEmptyCounts:
    def test_shape_matches_replay_summary(self):
        m = _import_module()
        c = m.empty_counts()
        assert c["considered"] == 0
        assert c["filtered_out"] == 0
        assert c["commit_errors"] == 0
        for bucket in ("applied", "skip_error", "skip_no_payload"):
            assert set(c[bucket].keys()) == set(m.DOMAIN_LABELS)
            assert all(v == 0 for v in c[bucket].values())
