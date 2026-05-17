# man_hours: 1.0
"""CLI smoke tests for emergency-planning enrichment scope."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

from click.testing import CliRunner

from atoms_vs_ashes.analysis import emergency_plan
from atoms_vs_ashes.db import engine as db_engine


def test_enrich_ep_composite_forwards_site_scope(monkeypatch):
    from atoms_vs_ashes import cli

    site_id = "af7f107f-71b5-5a33-8125-9ccb7060f895"
    captured = {}

    class FakeEmergencyPlanCheck:
        def __init__(self, *, site_ids=None, country_codes=None):
            captured["site_ids"] = site_ids
            captured["country_codes"] = country_codes

        def run(self, session, settings, run_id):
            captured["run_id"] = run_id
            return SimpleNamespace(total=1, passed=1, failed=0, inconclusive=0)

    class FakeSession:
        def commit(self):
            captured["committed"] = True

    @contextmanager
    def fake_session_scope():
        yield FakeSession()

    monkeypatch.setattr(cli, "init_engine", lambda settings: None)
    monkeypatch.setattr(cli, "check_connection", lambda settings: True)
    monkeypatch.setattr(emergency_plan, "EmergencyPlanCheck", FakeEmergencyPlanCheck)
    monkeypatch.setattr(db_engine, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli.main,
        [
            "--run-id",
            "test-ep-scope",
            "enrich-ep-composite",
            "--site-id",
            site_id,
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["site_ids"] == (site_id,)
    assert captured["country_codes"] is None
    assert captured["run_id"] == "test-ep-scope"
    assert captured["committed"] is True
