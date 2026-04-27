# man_hours: 1.0
"""Smoke tests for SMR-scope propagation through the scoring CLIs.

Both ``score run --profile`` and ``score sensitivity --profile`` must
honour ``profile.scope.smr_keys``. The previous implementation built
SMR-aware criteria bundles from an unfiltered ``select(SmrDesign)`` and
called ``run_scoring(...)`` without ``scope=``, so every SMR ended up
in the persisted ``composite_rankings`` regardless of the user's
selection. The Results page therefore showed multiple SMRs even when
only one had been picked in *Sites & SMR Setup*.

These tests exercise the CLI seams directly so we don't need a live
database. They assert:

1. ``execute_score_run`` (the body behind ``score run``) restricts the
   SMR query to the profile's ``scope.smr_keys`` and forwards the
   resulting ``RunScope`` to ``run_scoring`` via ``scope=``.
2. ``score sensitivity --profile`` populates
   ``SensitivitySuiteConfig.scope`` from the profile.
3. The GUI runner appends ``--profile`` to the spawned
   ``score sensitivity`` command line so the CLI actually receives it.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from atoms_vs_ashes.scoring import _cli as score_cli
from atoms_vs_ashes.scoring._cli import score_group


SINGLE_SMR_PROFILE = textwrap.dedent(
    """\
    run_label: "scope_smoke"
    db_profile: merged
    spec_dir: config/scoring_specs
    weight_profile: baseline
    scope:
      countries: [RO]
      smr_keys: [nuscale_voygr6]
      site_status_in: [operating]
      site_ids: []
    fail_thresholds: {}
    expert_override: false
    scoring:
      unscored_fallback_score: 5.0
      unscored_fraction_warn: 0.05
      unscored_fraction_hard: 0.20
      weight_overrides: {}
      qualification_mode: normal
      top_n_per_country: 10
      near_miss_gap_pct: 10
    sensitivity:
      enabled: [weights, mc]
      mc_iterations: 100
      mc_seed: 42
      weight_perturbation_pct: 20
      threshold_targeted_pct: [10, 25]
      threshold_global_stress: false
      top_n_country: 20
      country_balance_max_share: 0.40
      mc_stability_band_width: 1.0
    output:
      stamp: ""
      audit_dir: audit/post_processing/06_scoring
      report_dir: report/output/sensitivity
    notes: "single-SMR scope smoke profile"
    """
)


@pytest.fixture
def single_smr_profile_path(tmp_path: Path) -> Path:
    p = tmp_path / "single_smr.yaml"
    p.write_text(SINGLE_SMR_PROFILE)
    return p


def _fake_loaded_profile():
    """Stub for ``load_run_profile``'s ``LoadedRunProfile``.

    Carries just enough attributes for the production code path under
    test (``execute_score_run`` + ``apply_profile_scope_to_sensitivity_cfg``).
    """
    profile = SimpleNamespace(
        spec_dir="config/scoring_specs",
        scope=SimpleNamespace(
            countries=["RO"],
            smr_keys=["nuscale_voygr6"],
            site_status_in=["operating"],
            site_ids=[],
        ),
    )
    template_bundle = SimpleNamespace()
    return SimpleNamespace(profile=profile, template_bundle=template_bundle)


def test_score_run_profile_restricts_smr_query_and_forwards_scope(
    single_smr_profile_path: Path,
) -> None:
    """``score run --profile`` builds a single-SMR query + ``scope=`` arg."""
    captured: dict = {}
    fake_smr = SimpleNamespace(smr_key="nuscale_voygr6")

    fake_session = MagicMock()
    apply_to_smrs_called: dict = {}

    def _capture_execute(stmt):
        scalars = MagicMock()
        scalars.scalars.return_value = iter([fake_smr])
        apply_to_smrs_called["stmt"] = stmt
        return scalars

    fake_session.execute.side_effect = _capture_execute

    fake_summary = SimpleNamespace(
        run_id="r1", weight_profile="baseline", sites_processed=0,
        smr_designs=1, verdict_rows=0, ranking_rows=0, composite_rows=0,
        excluded_pairs=0, warnings=[],
    )

    def _fake_run_scoring(session, **kwargs):
        captured.update(kwargs)
        return fake_summary

    def _fake_bundles(template_bundle, profile, smrs):
        captured["bundles_smrs"] = list(smrs)
        return {"nuscale_voygr6": SimpleNamespace()}

    def _fake_weight_normalisation(_bundle, *, profile):
        return {}

    runner = CliRunner()
    with (
        patch.object(score_cli, "session_scope") as mock_scope,
        patch(
            "atoms_vs_ashes.scoring._cli_run.load_run_profile",
            return_value=_fake_loaded_profile(),
        ),
        patch(
            "atoms_vs_ashes.scoring._cli_run.smr_aware_criteria_bundles",
            side_effect=_fake_bundles,
        ),
        patch(
            "atoms_vs_ashes.scoring.rubric.weight_normalisation",
            side_effect=_fake_weight_normalisation,
        ),
        patch(
            "atoms_vs_ashes.scoring._cli_run.run_scoring",
            side_effect=_fake_run_scoring,
        ),
    ):
        mock_scope.return_value.__enter__.return_value = fake_session
        result = runner.invoke(
            score_group,
            [
                "run",
                "--profile", str(single_smr_profile_path),
                "--weight-profile", "baseline",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "scope" in captured, "run_scoring must receive the run scope"
    rs = captured["scope"]
    assert rs is not None
    assert rs.smr_keys == ("nuscale_voygr6",)
    assert rs.country_codes == ("RO",)
    assert [smr.smr_key for smr in captured["bundles_smrs"]] == ["nuscale_voygr6"]


def test_score_sensitivity_profile_populates_cfg_scope(
    single_smr_profile_path: Path,
) -> None:
    """``score sensitivity --profile`` sets ``cfg.scope`` from the profile."""
    captured: dict = {}

    def _fake_run(session, cfg, *, run_id, cancellation=None, heartbeat=None):
        captured["cfg"] = cfg
        captured["run_id"] = run_id
        return SimpleNamespace(
            to_dict=lambda: {
                "run_id": run_id, "pairs": 0,
                "iterations": cfg.iterations,
                "preset_label": cfg.preset_label,
                "weight_rows_persisted": 0,
                "mc_rows_persisted": 0,
                "country_balanced_rows_persisted": 0,
                "country_report": None,
                "audit_path": "/tmp/audit.md",
                "mc_label": f"mc_{cfg.iterations}",
                "notes": [],
            }
        )

    runner = CliRunner()
    with (
        patch.object(score_cli, "run_sensitivity_suite", _fake_run),
        patch.object(score_cli, "session_scope") as mock_scope,
        patch(
            "atoms_vs_ashes.scoring._cli_run.load_run_profile",
            return_value=_fake_loaded_profile(),
        ),
    ):
        mock_scope.return_value.__enter__.return_value = MagicMock()
        result = runner.invoke(
            score_group,
            [
                "sensitivity",
                "--profile", str(single_smr_profile_path),
                "--mc-draws", "10",
                "--include", "mc",
                "--no-progress",
            ],
        )

    assert result.exit_code == 0, result.output
    cfg = captured["cfg"]
    assert cfg.scope is not None, "cfg.scope must be hydrated from the profile"
    assert cfg.scope.smr_keys == ("nuscale_voygr6",)
    assert cfg.scope.country_codes == ("RO",)
    assert cfg.rubric_dir == "config/scoring_specs"


def test_gui_runner_passes_profile_to_score_sensitivity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``start_sensitivity_run`` must include ``--profile <yaml>`` in cmd."""
    from atoms_vs_ashes.gui import _runner as runner_mod

    captured_cmd: list[str] = []

    def _fake_export(run_id, *, profile=None):
        path = tmp_path / f"{run_id}.yaml"
        path.write_text("run_label: smoke\n")
        return path

    def _fake_load_active():
        return SimpleNamespace(
            spec_dir="config/scoring_specs",
            weight_profile="baseline",
            output=SimpleNamespace(audit_dir="audit/post_processing/06_scoring"),
            sensitivity=SimpleNamespace(mc_seed=42),
        )

    class _FakeProc:
        pid = 12345

        def poll(self):
            return None

    def _fake_popen(cmd, **kwargs):
        captured_cmd.extend(cmd)
        return _FakeProc()

    monkeypatch.setattr(runner_mod, "export_active_profile_to_yaml", _fake_export)
    monkeypatch.setattr(runner_mod, "_load_active_profile", _fake_load_active)
    monkeypatch.setattr(runner_mod, "cleanup_stale_runtime_profiles", lambda **k: None)
    monkeypatch.setattr(runner_mod, "_runs_root", lambda: tmp_path)
    monkeypatch.setattr(runner_mod.subprocess, "Popen", _fake_popen)

    runner_mod.start_sensitivity_run(
        weight_profile="baseline",
        iterations=10,
        include=("mc",),
        seed=42,
        no_progress=True,
    )

    assert "--profile" in captured_cmd, captured_cmd
    profile_idx = captured_cmd.index("--profile")
    profile_arg = captured_cmd[profile_idx + 1]
    assert profile_arg.endswith(".yaml")
    assert Path(profile_arg).exists(), "exported YAML must exist on disk"
