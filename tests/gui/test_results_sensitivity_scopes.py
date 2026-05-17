# man_hours: 0.6
"""Scope-dispatch tests for Results Sensitivity/Stability data helpers."""

from __future__ import annotations

from contextlib import contextmanager

from atoms_vs_ashes.gui import _results_data_sens as sens_mod
from atoms_vs_ashes.gui import _results_data_stability as stab_mod


@contextmanager
def _fake_scope():
    yield object()


def test_sensitivity_snapshot_passes_country_to_all_sections(monkeypatch) -> None:
    calls: dict[str, tuple] = {}

    def composite(session, run_id, country):
        calls["composite"] = (run_id, country)
        return {"mc_10": 1}

    def country_rows(session, run_id, country):
        calls["country"] = (run_id, country)
        return []

    def threshold_rows(session, run_id, country, profile):
        calls["threshold"] = (run_id, country, profile)
        return []

    monkeypatch.setattr(sens_mod, "session_scope", lambda: _fake_scope())
    monkeypatch.setattr(sens_mod, "_composite_breakdown", composite)
    monkeypatch.setattr(sens_mod, "_country_balance_rows", country_rows)
    monkeypatch.setattr(sens_mod, "_threshold_sensitivity_rows", threshold_rows)

    snap = sens_mod.sensitivity_snapshot(
        "sens-1", country_code="RO", baseline_weight_profile="expert",
    )

    assert snap.country_code == "RO"
    assert calls == {
        "composite": ("sens-1", "RO"),
        "country": ("sens-1", "RO"),
        "threshold": ("sens-1", "RO", "expert"),
    }


def test_site_stability_ledger_passes_country_scope(monkeypatch) -> None:
    calls: dict[str, tuple] = {}

    def mc_profile(session, run_id):
        calls["mc"] = (run_id,)
        return "mc_10"

    def stability_rows(session, run_id, mc, country):
        calls["rows"] = (run_id, mc, country)
        return []

    monkeypatch.setattr(stab_mod, "session_scope", lambda: _fake_scope())
    monkeypatch.setattr(stab_mod, "_largest_mc_profile", mc_profile)
    monkeypatch.setattr(stab_mod, "_stability_rows", stability_rows)

    assert stab_mod.site_stability_ledger("sens-1", country_code="FR") == []
    assert calls == {
        "mc": ("sens-1",),
        "rows": ("sens-1", "mc_10", "FR"),
    }


def test_explicit_stability_helpers_keep_regional_and_national_scopes(monkeypatch) -> None:
    calls: list[tuple] = []

    def fake_ledger(run_id, *, country_code=None):
        calls.append((run_id, country_code))
        return []

    monkeypatch.setattr(stab_mod, "site_stability_ledger", fake_ledger)

    assert stab_mod.regional_stability_ledger("regional-1") == []
    assert stab_mod.national_stability_ledger("national-1", country_code="RO") == []
    assert calls == [("regional-1", None), ("national-1", "RO")]
