# man_hours: 0.4
"""Single-SMR scope tests for the national sensitivity suite."""

from atoms_vs_ashes.scoring.national_suite import _single_smr_scope


def test_single_smr_scope_is_none_without_key() -> None:
    assert _single_smr_scope(None) is None


def test_single_smr_scope_restricts_to_one_design() -> None:
    scope = _single_smr_scope("nuscale_voygr6")

    assert scope is not None
    assert scope.smr_keys == ("nuscale_voygr6",)
    assert scope.country_codes is None
