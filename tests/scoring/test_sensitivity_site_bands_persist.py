"""Tests for regional + national stability-band persistence."""

from __future__ import annotations

from types import SimpleNamespace

from atoms_vs_ashes.scoring import _suite_sensitivity_site_bands_persist as mod


def test_persist_site_bands_writes_regional_and_each_country(monkeypatch) -> None:
    calls: list[tuple[str | None, int]] = []

    def fake_compute_bands(session, *, baseline_label, smr_filter, country_filter):
        assert baseline_label == "baseline"
        assert smr_filter is None
        n = 3 if country_filter is None else {"FR": 2, "RO": 1}[country_filter]
        return [SimpleNamespace(site_id=i) for i in range(n)], ["w_plus"]

    def fake_persist_site_bands(
        session, *, run_id, bands, smr_filter, country_filter,
    ):
        assert run_id == "sens-1"
        assert smr_filter is None
        calls.append((country_filter, len(bands)))
        return len(bands)

    monkeypatch.setattr(mod, "compute_bands", fake_compute_bands)
    monkeypatch.setattr(mod, "persist_site_bands", fake_persist_site_bands)

    summary = mod.persist_site_bands_for_sensitivity_run(
        object(),
        run_id="sens-1",
        baseline_label="baseline",
        country_codes=("RO", "FR", "RO", "??", ""),
    )

    assert calls == [(None, 3), ("FR", 2), ("RO", 1)]
    assert summary.rows_by_scope == {"XX": 3, "FR": 2, "RO": 1}
    assert summary.total_rows == 6


def test_regional_wrapper_keeps_old_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "persist_site_bands_for_sensitivity_run",
        lambda *args, **kwargs: mod.SiteBandPersistSummary({"XX": 4}),
    )

    assert mod.persist_regional_site_bands_for_sensitivity_run(
        object(), run_id="sens-1", baseline_label="baseline",
    ) == 4
