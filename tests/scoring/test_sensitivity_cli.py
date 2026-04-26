"""Unit tests for ``ava score sensitivity`` CLI wiring.

Run without a live DB by patching ``session_scope`` + the orchestrator
at the CLI layer, and patching ``run_monte_carlo`` when exercising the
sensitivity-level forwarding.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from atoms_vs_ashes.scoring import _cli as score_cli
from atoms_vs_ashes.scoring import sensitivity as sens_mod
from atoms_vs_ashes.scoring._cli import score_group
from atoms_vs_ashes.scoring.sensitivity import MC_DEFAULT_ITERATIONS, MC_PRESETS


def _fake_suite_result(cfg) -> SimpleNamespace:
    return SimpleNamespace(
        to_dict=lambda: {
            "run_id": "test",
            "pairs": 0,
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


class TestCliHelp:
    def test_help_exposes_flag_names(self):
        runner = CliRunner()
        result = runner.invoke(score_group, ["sensitivity", "--help"])
        assert result.exit_code == 0, result.output
        for flag in ("--preset", "--mc-draws", "--no-progress", "--include"):
            assert flag in result.output

    def test_help_documents_presets(self):
        runner = CliRunner()
        result = runner.invoke(score_group, ["sensitivity", "--help"])
        assert result.exit_code == 0
        assert "test" in result.output
        assert "1000" in result.output
        assert "production" in result.output
        assert "10000" in result.output


class TestPresetAndOverride:
    def _invoke(self, *extra_args: str):
        captured: dict = {}

        def _fake_run(session, cfg, *, run_id, cancellation=None, heartbeat=None):
            captured["cfg"] = cfg
            captured["run_id"] = run_id
            captured["cancellation"] = cancellation
            captured["heartbeat"] = heartbeat
            return _fake_suite_result(cfg)

        runner = CliRunner()
        with (
            patch.object(score_cli, "run_sensitivity_suite", _fake_run),
            patch.object(score_cli, "session_scope") as mock_scope,
        ):
            mock_scope.return_value.__enter__.return_value = MagicMock()
            result = runner.invoke(
                score_group, ["sensitivity", *extra_args, "--no-progress"]
            )
        return result, captured

    def test_preset_test_maps_to_1000(self):
        result, captured = self._invoke("--preset", "test", "--include", "mc")
        assert result.exit_code == 0, result.output
        assert captured["cfg"].iterations == MC_PRESETS["test"] == 1000
        assert captured["cfg"].preset_label == "test"

    def test_preset_production_maps_to_10000(self):
        result, captured = self._invoke("--preset", "production", "--include", "mc")
        assert result.exit_code == 0, result.output
        assert captured["cfg"].iterations == 10000
        assert captured["cfg"].preset_label == "production"

    def test_mc_draws_override(self):
        result, captured = self._invoke("--mc-draws", "10", "--include", "mc")
        assert result.exit_code == 0, result.output
        assert captured["cfg"].iterations == 10
        assert captured["cfg"].preset_label is None

    def test_default_iterations_when_neither_flag_given(self):
        result, captured = self._invoke("--include", "mc")
        assert result.exit_code == 0, result.output
        assert captured["cfg"].iterations == MC_DEFAULT_ITERATIONS
        assert captured["cfg"].preset_label is None

    def test_preset_and_mc_draws_are_mutually_exclusive(self):
        result, _captured = self._invoke(
            "--preset", "test", "--mc-draws", "5", "--include", "mc"
        )
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output.lower()

    def test_mc_draws_must_be_positive(self):
        result, _captured = self._invoke("--mc-draws", "0", "--include", "mc")
        assert result.exit_code != 0
        assert ">= 1" in result.output or "must be" in result.output.lower()

    def test_no_progress_flag_sets_progress_enabled_false(self):
        result, captured = self._invoke(
            "--mc-draws", "7", "--include", "mc"
        )
        assert result.exit_code == 0
        assert captured["cfg"].progress_enabled is False


class TestRunMcSuiteForwardsIterations:
    def test_run_mc_suite_passes_iterations_to_run_monte_carlo(self):
        calls: list[int] = []

        def _fake_run_monte_carlo(
            site_id, smr_key, rows, verdicts, weights, *, iterations, seed
        ):
            calls.append(iterations)
            return SimpleNamespace(
                site_id=site_id,
                smr_key=smr_key,
                mean=0.0,
                p05=0.0,
                p95=0.0,
                stdev=0.0,
                iterations=iterations,
                stable=True,
                notes=[],
            )

        sites_rows = {("s1", "smr-a"): [], ("s2", "smr-b"): []}

        ticks: list[int] = []

        with patch.object(sens_mod, "run_monte_carlo", _fake_run_monte_carlo):
            sens_mod.run_mc_suite(
                sites_rows,
                {},
                weights={},
                iterations=7,
                progress_cb=lambda n: ticks.append(n),
                preset_label="test",
            )

        assert calls == [7, 7]
        assert sum(ticks) == len(sites_rows)


class TestProgressReporterFallback:
    def test_non_tty_fallback_emits_logs(self, tmp_path: Path):
        from rich.console import Console

        from atoms_vs_ashes.scoring._progress import ProgressReporter

        sink = tmp_path / "sink.txt"
        console = Console(file=sink.open("w"), force_terminal=False)
        with ProgressReporter(
            total=20, description="unit-test", enabled=True, console=console
        ) as p:
            for _ in range(20):
                p.advance(1)
        assert p._done == 20  # advance counted correctly
