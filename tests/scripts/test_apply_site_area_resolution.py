# man_hours: 2.5
import importlib.util
from pathlib import Path

import pytest


def _load_script(name: str):
    path = Path(__file__).resolve().parents[2] / "src" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_write_requires_explicit_consent():
    module = _load_script("apply_site_area_resolution")

    with pytest.raises(SystemExit) as exc:
        module.main(["--write"])

    assert "--write requires --i-consent-to-write" in str(exc.value)


def test_dry_run_does_not_connect_for_writes(monkeypatch):
    module = _load_script("apply_site_area_resolution")

    monkeypatch.setattr(module, "fetch_site_rows", lambda **_: [])
    monkeypatch.setattr(module, "load_manual_overrides", lambda _: {})

    def fail_connect(_db_name):
        raise AssertionError("dry-run should not open a write connection")

    monkeypatch.setattr(module, "connect", fail_connect)

    assert module.main([]) == 0


def test_apply_one_updates_sites_and_records_merge_audit():
    module = _load_script("apply_site_area_resolution")
    cursor = FakeCursor()

    module._apply_one(cursor, {
        "site_id": "aff5ffe6-fe7a-4de7-afad-9d4645a64cd9",
        "recommended_site_area_ha": 40.0,
        "recommended_source": "manual_verified",
        "recommended_confidence": "high",
        "confidence_score": 90,
        "review_flags": "S1;S2;S5",
        "candidate_values_json": '[{"value_ha": 40.0, "source": "manual_verified"}]',
        "expansion_potential_ha": 115.0,
        "current_site_area_ha": 0.16,
        "buildable_area_ha": 0.16,
        "largest_contiguous_ha": 0.16,
        "favourable_area_ha": 49.32,
        "llm_structured_ha": 40.0,
        "llm_db_site_area_ha": None,
        "llm_observation_text": "Site area: 40 ha.",
    }, "test_run")

    sql_text = "\n".join(sql for sql, _params in cursor.calls)
    assert "UPDATE sites" in sql_text
    assert "site_area_candidates_json" in sql_text
    assert "INSERT INTO merge_audit" in sql_text
    assert len(cursor.calls) == 2


class FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
