# man_hours: 0.8
"""Sensitivity runs must pin all baseline reads to one scoring parent."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from atoms_vs_ashes.scoring import suite as suite_mod
from atoms_vs_ashes.scoring._suite_config import SensitivitySuiteConfig


def test_sensitivity_suite_uses_resolved_scoring_parent_everywhere(monkeypatch):
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        suite_mod,
        "_resolve_baseline_run_id",
        lambda session, *, weight_profile_base: "score-latest",
    )
    monkeypatch.setattr(
        suite_mod,
        "start_run",
        lambda session, **kwargs: SimpleNamespace(
            run_id=kwargs["run_id"],
            run_kind=kwargs["run_kind"],
            parent_run_id=kwargs["parent_run_id"],
            persisted=True,
        ),
    )
    monkeypatch.setattr(suite_mod, "complete_run", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        suite_mod,
        "load_bundle_for_run_snapshot",
        lambda *args, **kwargs: ({}, "snapshot-1"),
    )
    monkeypatch.setattr(suite_mod, "link_run_to_snapshot", lambda *args, **kwargs: None)
    monkeypatch.setattr(suite_mod, "weight_normalisation", lambda *args, **kwargs: {})

    def fake_load_pairs(session, *, weight_profile_base, run_id_filter, scope):
        calls["pairs_parent"] = run_id_filter
        return {}, {}, {}

    def fake_load_baseline(session, *, weight_profile_base, run_id_filter, scope):
        calls["baseline_parent"] = run_id_filter
        return {}

    def fake_site_bands(session, *, run_id, baseline_label, country_codes):
        calls["site_bands_run_id"] = run_id
        return SimpleNamespace(rows_by_scope={}, total_rows=0)

    monkeypatch.setattr(suite_mod, "load_pairs", fake_load_pairs)
    monkeypatch.setattr(suite_mod, "load_baseline_composites", fake_load_baseline)
    monkeypatch.setattr(
        suite_mod,
        "persist_site_bands_for_sensitivity_run",
        fake_site_bands,
    )
    monkeypatch.setattr(suite_mod, "write_audit_md", lambda *args, **kwargs: Path())

    result = suite_mod.run_sensitivity_suite(
        SimpleNamespace(flush=lambda: None),
        SensitivitySuiteConfig(
            include_weights=False,
            include_mc=False,
            include_country=False,
            include_threshold=False,
            weight_profile_base="baseline",
        ),
        run_id="sens-new",
    )

    assert result.run_id == "sens-new"
    assert calls == {
        "pairs_parent": "score-latest",
        "baseline_parent": "score-latest",
        "site_bands_run_id": "sens-new",
    }
