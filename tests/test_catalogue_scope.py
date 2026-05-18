# man_hours: 0.3
"""Tests for supplementary catalogue scope widening."""

from __future__ import annotations

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.runtime.catalogue_scope import (
    scope_including_supplementary_catalogue,
    supplementary_site_statuses,
)
from atoms_vs_ashes.runtime.scope import RunScope


def test_supplementary_site_statuses_include_iernut_construction():
    settings = Settings()
    statuses = supplementary_site_statuses(settings, country_codes=frozenset({"RO"}))
    assert "construction" in statuses


def test_scope_widens_for_construction_supplementary_site():
    settings = Settings()
    narrow = RunScope(
        smr_keys=("nuscale_voygr6",),
        site_status_in=("operating", "retired", "mothballed"),
    )
    wide = scope_including_supplementary_catalogue(narrow, settings)
    assert "construction" in wide.site_status_in
    assert set(narrow.site_status_in).issubset(wide.site_status_in)


def test_scope_unchanged_when_construction_already_allowed():
    settings = Settings()
    base = RunScope(
        smr_keys=("nuscale_voygr6",),
        site_status_in=("operating", "retired", "mothballed", "construction"),
    )
    assert scope_including_supplementary_catalogue(base, settings) is base
