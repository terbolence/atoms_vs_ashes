# man_hours: 1.6
"""Persistence-shape tests for :mod:`runprofile.persist`.

Plan §5 of ``scoring_control_gui_872d4eb7`` requires every run to
record:

- the path + sha256 of the user's :class:`RunProfile`,
- the path + sha256 of the compiled :class:`Criterion` bundle,
- a structured ``scope_summary`` (resolved scope, fail-threshold
  overrides, expert-override deviations).

These tests exercise the helpers that turn a profile into a
:class:`DatasetMeta` without touching the database, plus the small
markdown renderer reused by the audit MD writers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.runprofile import (
    RunProfile,
    ScopeBlock,
    build_scope_summary,
    dataset_meta_for_profile,
    expert_override_diffs,
    render_provenance_md,
)
from atoms_vs_ashes.runprofile.schema import RunProfileWithPath


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def compiled_no_overrides():
    return compile_bundle(load_template_bundle(str(SPEC_DIR)))


@pytest.fixture(scope="module")
def compiled_with_override():
    return compile_bundle(
        load_template_bundle(str(SPEC_DIR)),
        fail_thresholds={"NH-02": {"E1": 4.5}},
        expert_override=False,
    )


def test_scope_summary_carries_qualification_and_thresholds(
    compiled_no_overrides,
):
    profile = RunProfile(
        run_label="ro_focus",
        scope=ScopeBlock(countries=["RO"], smr_keys=["natrium_nominal"]),
        fail_thresholds={"NH-02": {"E1": 4.5}},
    )
    summary = build_scope_summary(profile, compiled_no_overrides)
    assert summary["scope"]["country_codes"] == ["RO"]
    assert summary["scope"]["smr_keys"] == ["natrium_nominal"]
    assert summary["fail_thresholds"] == {"NH-02": {"E1": 4.5}}
    assert summary["qualification_mode"] == "normal"
    assert summary["weight_profile"] == "baseline"


def test_expert_override_diffs_only_records_deviations(
    compiled_with_override,
):
    """Diffs should fire only when user_value != recommended_value."""
    profile = RunProfile(
        run_label="ro_focus",
        fail_thresholds={"NH-02": {"E1": 4.5}},
    )
    diffs = expert_override_diffs(profile, compiled_with_override)
    assert "NH-02" in diffs and "E1" in diffs["NH-02"]
    entry = diffs["NH-02"]["E1"]
    assert entry["value"] == 4.5
    assert entry["recommended_value"] == 8.0
    assert entry["out_of_bounds"] is False


def test_dataset_meta_round_trips_hashes(tmp_path: Path, compiled_no_overrides):
    profile = RunProfile(run_label="baseline", scope=ScopeBlock(countries=["RO"]))
    profile_path = tmp_path / "baseline.yaml"
    profile_path.write_text("run_label: baseline\n")
    pwp = RunProfileWithPath(profile=profile, path=profile_path)
    meta = dataset_meta_for_profile(
        profile_with_path=pwp,
        compiled=compiled_no_overrides,
        spec_dir=SPEC_DIR,
        n_sites_total=42,
        n_smrs=8,
        n_criteria_ranking=21,
    )
    assert meta.run_profile_path == str(profile_path)
    assert meta.run_profile_sha256 and len(meta.run_profile_sha256) == 64
    assert meta.spec_bundle_sha256 == compiled_no_overrides.sha256
    assert meta.n_countries_in_scope == 1
    assert meta.n_sites_total == 42
    assert meta.scope_summary["scope"]["country_codes"] == ["RO"]


def test_render_provenance_md_emits_header_when_populated(
    tmp_path: Path, compiled_with_override
):
    profile = RunProfile(
        run_label="ro_focus",
        fail_thresholds={"NH-02": {"E1": 4.5}},
    )
    profile_path = tmp_path / "ro_focus.yaml"
    profile_path.write_text("run_label: ro_focus\n")
    meta = dataset_meta_for_profile(
        profile_with_path=RunProfileWithPath(profile=profile, path=profile_path),
        compiled=compiled_with_override,
        spec_dir=SPEC_DIR,
    )
    md = render_provenance_md(meta)
    assert "## Provenance" in md
    assert meta.run_profile_sha256 in md
    assert meta.spec_bundle_sha256 in md
    assert "Expert overrides" in md
