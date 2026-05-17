# man_hours: 1.6
"""RunProfile parsing + spec-validation tests (no DB required).

Run profile YAMLs no longer ship in ``config/run_profiles/`` — the
GUI's source of truth lives in the ``active_run_profile`` DB row
(alembic 039). The tests below reproduce the former
``baseline.yaml`` / ``ro_focus.yaml`` shapes inline so the loader's
parsing + spec-validation paths stay covered.
"""

from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from atoms_vs_ashes.runprofile import (
    RunProfile,
    load_run_profile,
    parse_run_profile,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


_BASELINE_YAML = textwrap.dedent(
    """\
    run_label: "baseline"
    db_profile: merged
    spec_dir: config/scoring_specs
    weight_profile: baseline
    scope:
      countries: []
      smr_keys: [nuscale_voygr6]
      site_status_in: [operating, retired, mothballed]
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
      enabled: [weights, mc, threshold, oat, country]
      mc_iterations: 5000
      mc_seed: 42
      weight_perturbation_pct: 20
      threshold_targeted_pct: [10, 25]
      threshold_global_stress: true
      top_n_country: 20
      country_balance_max_share: 0.40
      mc_stability_band_width: 1.0
    output:
      stamp: ""
      audit_dir: audit/post_processing/06_scoring
      report_dir: report/output/sensitivity
    notes: "Repository default profile."
    """
)


_RO_FOCUS_YAML = textwrap.dedent(
    """\
    run_label: "ro_focus_q2"
    db_profile: merged
    spec_dir: config/scoring_specs
    weight_profile: baseline
    scope:
      countries: [RO]
      smr_keys: [nuscale_voygr6]
      site_status_in: [operating, retired, mothballed]
      site_ids: []
    fail_thresholds:
      NH-02: {E1: 5.0}
      NH-04: {E3: 25}
      NH-07: {E4: 50}
    expert_override: false
    scoring:
      unscored_fallback_score: 3.0
      unscored_fraction_warn: 0.05
      unscored_fraction_hard: 0.20
      weight_overrides: {}
      qualification_mode: normal
      top_n_per_country: 10
      near_miss_gap_pct: 10
    sensitivity:
      enabled: [weights, mc, threshold, oat]
      mc_iterations: 3000
      mc_seed: 42
      weight_perturbation_pct: 20
      threshold_targeted_pct: [10, 25]
      threshold_global_stress: false
      top_n_country: 10
      country_balance_max_share: 1.0
      mc_stability_band_width: 1.0
    output:
      stamp: ""
      audit_dir: audit/post_processing/06_scoring
      report_dir: report/output/sensitivity
    notes: "Romania-only fast iteration loop"
    """
)


def _write(tmp_path: Path, body: str, *, name: str = "profile.yaml") -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(body))
    return p


@pytest.fixture
def baseline_profile_path(tmp_path: Path) -> Path:
    return _write(tmp_path, _BASELINE_YAML, name="baseline.yaml")


@pytest.fixture
def ro_focus_profile_path(tmp_path: Path) -> Path:
    return _write(tmp_path, _RO_FOCUS_YAML, name="ro_focus.yaml")


def test_baseline_profile_loads(baseline_profile_path: Path):
    out = load_run_profile(baseline_profile_path)
    assert out.profile.run_label == "baseline"
    assert out.profile.db_profile == "merged"
    assert out.profile.fail_thresholds == {}
    assert len(out.compiled.criteria) == 48
    assert out.warnings == []


def test_legacy_non_merged_profile_loads_as_merged(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: legacy
        db_profile: api
        """,
    )
    profile, _sha = parse_run_profile(p)
    assert profile.db_profile == "merged"


def test_ro_focus_profile_loads(ro_focus_profile_path: Path):
    out = load_run_profile(ro_focus_profile_path)
    assert out.profile.scope.countries == ["RO"]
    assert out.profile.scope.smr_keys == ["nuscale_voygr6"]
    overrides = {(o.criterion_id, o.code) for o in out.compiled.overrides}
    assert ("NH-02", "E1") in overrides
    assert ("NH-04", "E3") in overrides
    assert ("NH-07", "E4") in overrides


def test_unknown_criterion_rejected(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: bad
        fail_thresholds:
          ZZ-99: {E1: 5.0}
        """,
    )
    with pytest.raises(ValueError, match="unknown criterion"):
        load_run_profile(p)


def test_unknown_code_rejected(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: bad
        fail_thresholds:
          NH-02: {E99: 5.0}
        """,
    )
    with pytest.raises(ValueError, match="not a known fail condition"):
        load_run_profile(p)


def test_out_of_bounds_rejected_without_expert(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: bad
        fail_thresholds:
          NH-02: {E1: 100.0}
        """,
    )
    with pytest.raises(ValueError, match="outside bounds"):
        load_run_profile(p)


def test_expert_override_records_warning(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: bad
        expert_override: true
        fail_thresholds:
          NH-02: {E1: 100.0}
        """,
    )
    out = load_run_profile(p)
    assert any("expert_override active" in w for w in out.warnings)


def test_weight_overrides_must_match_criterion(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: bad
        scoring:
          weight_overrides: {ZZ-99: 5}
        """,
    )
    with pytest.raises(ValueError, match="weight_overrides references unknown"):
        load_run_profile(p)


def test_qualification_mode_default_normal(baseline_profile_path: Path):
    out = load_run_profile(baseline_profile_path)
    assert out.profile.scoring.qualification_mode == "normal"


def test_uppercase_country_codes(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: case
        scope:
          countries: [ro, BG, md]
        """,
    )
    profile, _ = parse_run_profile(p)
    assert profile.scope.countries == ["BG", "MD", "RO"]


def test_db_site_status_enum_values_load(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        run_label: all_statuses
        scope:
          site_status_in: [cancelled, construction, mothballed, operating, retired, shelved]
        """,
    )
    profile, _ = parse_run_profile(p)
    assert profile.scope.site_status_in == [
        "cancelled",
        "construction",
        "mothballed",
        "operating",
        "retired",
        "shelved",
    ]


def test_canonical_dict_is_stable(baseline_profile_path: Path):
    out = load_run_profile(baseline_profile_path)
    a = out.profile.to_canonical_dict()
    b = RunProfile.model_validate(a).to_canonical_dict()
    assert a == b
