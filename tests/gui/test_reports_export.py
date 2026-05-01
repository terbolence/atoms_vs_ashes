"""Focused tests for GUI PDF report export helpers."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from atoms_vs_ashes.runtime.scope import RunScope
from atoms_vs_ashes.gui.reports.criteria_data import build_criteria_report
from atoms_vs_ashes.gui.reports.models import (
    CountryPackReport,
    CountryReport,
    CountrySensitivityReport,
    CriteriaReport,
    MetricValue,
    SiteMetricBundle,
    TopSiteReport,
)
from atoms_vs_ashes.gui.reports.pdf import (
    render_country_pack_pdf,
    render_criteria_pdf,
)


def test_criteria_payload_includes_all_criteria_and_bands(monkeypatch):
    preview = SimpleNamespace(
        spec_dir="config/scoring_specs",
        compiled_sha256="abc123",
        weight_profile="baseline",
        qualification_mode="normal",
        warnings=[],
        criteria=[
            SimpleNamespace(
                criterion_id="NH-01",
                bands=[SimpleNamespace(score_range=(5, 6))],
            ),
            SimpleNamespace(
                criterion_id="NS-02",
                bands=[SimpleNamespace(score_range=(7, 8))],
            ),
        ],
    )
    monkeypatch.setattr(
        "atoms_vs_ashes.gui.reports.criteria_data.build_live_preview",
        lambda profile, spec_dir: preview,
    )
    profile = SimpleNamespace(spec_dir="config/scoring_specs")

    report = build_criteria_report(profile)

    assert [c.criterion_id for c in report.criteria] == ["NH-01", "NS-02"]
    assert report.criteria[0].bands[0].score_range == (5, 6)


def test_country_sensitivity_is_country_scoped(monkeypatch):
    from atoms_vs_ashes.gui.reports import country_sensitivity as mod

    seen = {}
    def fake_stability(run_id, country_code):
        seen["stability_country"] = country_code
        return [SimpleNamespace(band="A")]

    def fake_snapshot(run_id, country_code, baseline_weight_profile):
        seen["sensitivity_country"] = country_code
        return SimpleNamespace(
            country_balance=[{"delta": 1}],
            threshold_sweep=[],
            composite_by_profile={"mc_1000": 10},
        )

    monkeypatch.setattr(
        mod,
        "site_stability_ledger",
        fake_stability,
    )
    monkeypatch.setattr(
        mod,
        "sensitivity_snapshot",
        fake_snapshot,
    )

    out = mod.build_country_sensitivity(
        sensitivity_run_id="sens-1",
        country_code="RO",
        baseline_weight_profile="baseline",
    )

    assert seen == {"stability_country": "RO", "sensitivity_country": "RO"}
    assert out.has_sensitivity is True


def test_country_pack_respects_top_n_and_scope(monkeypatch):
    from atoms_vs_ashes.gui.reports import country_data as mod

    seen = {}
    site_id = uuid.uuid4()

    class SessionCtx:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        mod,
        "country_coverage_matrix",
        lambda run_id, weight_profile, scope: [SimpleNamespace(country_code="RO")],
    )

    def fake_ledger(run_id, country_code, weight_profile, include_eliminated, limit, scope):
        seen["limit"] = limit
        seen["scope"] = scope
        return [
            SimpleNamespace(
                site_id=site_id, smr_key="demo", rank_position=1, name="Demo",
                country_code="RO", status="pass", composite=8.0,
                composite_low=7.5, composite_high=8.5,
            )
        ]

    monkeypatch.setattr(mod, "country_site_ledger", fake_ledger)
    monkeypatch.setattr(mod, "session_scope", lambda: SessionCtx())
    monkeypatch.setattr(
        mod,
        "load_template_bundle_from_db",
        lambda session, spec_dir, seed_if_empty: SimpleNamespace(by_id={}),
    )
    monkeypatch.setattr(
        mod,
        "build_site_metrics",
        lambda session, site_id, smr_key, templates: SiteMetricBundle(
            site_id=str(site_id), smr_key=smr_key,
        ),
    )
    monkeypatch.setattr(
        mod,
        "site_detail",
        lambda run_id, site_id, smr_key, weight_profile: SimpleNamespace(
            latitude=44.0, longitude=25.0, capacity_mw=1000.0,
        ),
    )
    monkeypatch.setattr(
        mod,
        "build_country_sensitivity",
        lambda **kwargs: CountrySensitivityReport(),
    )
    profile = SimpleNamespace(
        scoring=SimpleNamespace(top_n_per_country=1),
        spec_dir="config/scoring_specs",
    )
    scope = RunScope(country_codes=("RO",))

    report = mod.build_country_pack_report(
        run_id="run-1",
        baseline_run_id="run-1",
        weight_profile="baseline",
        profile=profile,
        scope=scope,
    )

    assert seen == {"limit": 1, "scope": scope}
    assert report.countries[0].sites[0].name == "Demo"


def test_pdf_renderers_return_pdf_bytes(monkeypatch):
    pytest.importorskip("reportlab")
    monkeypatch.setattr(
        "atoms_vs_ashes.gui.reports.pdf.country_chart_images",
        lambda country: [],
    )
    criteria = CriteriaReport(
        spec_dir="db://test",
        compiled_sha256="abc",
        weight_profile="baseline",
        qualification_mode="normal",
        criteria=[_criterion()],
    )
    country = CountryPackReport(
        run_id="run-1",
        baseline_run_id="run-1",
        weight_profile="baseline",
        top_n=1,
        scope_summary="countries=1",
        countries=[_country()],
    )

    assert render_criteria_pdf(criteria).startswith(b"%PDF")
    assert render_country_pack_pdf(country).startswith(b"%PDF")


def _criterion():
    return SimpleNamespace(
        criterion_id="NH-01",
        name="Seismic",
        phases=["ranking"],
        weight_factor=9,
        weight_normalised=0.1,
        primary_metric="pga_2475yr_g",
        fail_codes=[
            SimpleNamespace(
                code="A10", action="avoidance_penalty", metric="pga_2475yr_g",
                condition_expr="pga_2475yr_g > 0.5", units="g",
            )
        ],
        bands=[
            SimpleNamespace(
                score_range=(5, 6),
                condition_expr="pga_2475yr_g <= 0.5",
                descriptor="Boundary",
            )
        ],
    )


def _country():
    metric = SiteMetricBundle(
        site_id="site-1",
        smr_key="demo",
        core=[
            MetricValue("grid_export_capacity_mw", "Export Power", 600.0, "MW"),
            MetricValue("buildable_area_ha", "Available surface area", 20.0, "ha"),
        ],
        criteria=[MetricValue("pga_2475yr_g", "PGA", 0.2, "g", "NH-01")],
    )
    detail = SimpleNamespace(
        strengths=[],
        all_criterion_scores=[
            SimpleNamespace(criterion_id="NH-01", family="nh", score_0_10=7.0)
        ],
    )
    site = TopSiteReport(
        site_id="site-1",
        smr_key="demo",
        rank=1,
        name="Demo site",
        country_code="RO",
        status="pass",
        composite=7.5,
        composite_low=7.0,
        composite_high=8.0,
        latitude=44.0,
        longitude=25.0,
        capacity_mw=1000.0,
        metrics=metric,
        detail=detail,
    )
    return CountryReport(
        country_code="RO",
        country_name="Romania",
        top_n=1,
        sites=[site],
        sensitivity=CountrySensitivityReport(),
    )

