# man_hours: 1.0
"""Pure-logic tests for :class:`RunScope` filter primitives.

These tests intentionally avoid a live database — they cover the
session-free helpers (``is_unrestricted``, ``has_*``, ``filter_pairs``,
``to_dict``) so engine + sensitivity callers can rely on the contract
without reaching for a Postgres fixture.
"""

from __future__ import annotations

from atoms_vs_ashes.runtime import RunScope
from atoms_vs_ashes.runprofile.schema import RunProfile, ScopeBlock
from atoms_vs_ashes.runtime.scope import scope_from_run_profile


def test_unrestricted_scope_passes_everything_through() -> None:
    scope = RunScope()
    pairs = [("S1", "natrium_nominal"), ("S2", "voygr6")]
    assert scope.is_unrestricted() is True
    assert scope.filter_pairs(
        pairs, allowed_sites=None, allowed_smrs=None
    ) == pairs


def test_filter_pairs_drops_outside_country_and_smr() -> None:
    scope = RunScope(country_codes=("RO",), smr_keys=("natrium_nominal",))
    pairs = [
        ("S1", "natrium_nominal"),
        ("S1", "voygr6"),
        ("S2", "natrium_nominal"),
        ("S2", "voygr6"),
    ]
    out = scope.filter_pairs(
        pairs,
        allowed_sites=frozenset({"S1"}),
        allowed_smrs=frozenset({"natrium_nominal"}),
    )
    assert out == [("S1", "natrium_nominal")]


def test_filter_pairs_handles_empty_allowlists() -> None:
    """An *empty* allowlist must drop everything (no accidental wildcards)."""
    scope = RunScope(site_ids=())
    pairs = [("S1", "natrium_nominal")]
    assert scope.filter_pairs(
        pairs, allowed_sites=frozenset(), allowed_smrs=None
    ) == []


def test_to_dict_round_trips_user_input() -> None:
    scope = RunScope(
        country_codes=("RO", "BG"),
        smr_keys=("natrium_nominal",),
        site_status_in=("active",),
    )
    d = scope.to_dict()
    assert d["country_codes"] == ["RO", "BG"]
    assert d["smr_keys"] == ["natrium_nominal"]
    assert d["site_status_in"] == ["active"]
    assert d["site_ids"] is None


def test_scope_from_run_profile_translates_filters() -> None:
    profile = RunProfile(
        run_label="ro_focus",
        scope=ScopeBlock(countries=["RO"], smr_keys=["natrium_nominal"]),
    )
    scope = scope_from_run_profile(profile)
    assert scope.country_codes == ("RO",)
    assert scope.smr_keys == ("natrium_nominal",)
    assert scope.site_ids is None
    assert scope.is_unrestricted() is False
