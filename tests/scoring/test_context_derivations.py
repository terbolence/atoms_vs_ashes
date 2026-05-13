# man_hours: 0.4
"""Unit tests for derived context values used by the scoring engine.

Locks in the SP-F sentinel-aware behaviour of
:func:`atoms_vs_ashes.scoring.merge_context_derivations.apply_derived_context_values`:

- ``nearest_military_airfield_km`` is no longer auto-defaulted to 999.0.
- The HI-06 OSM military taxonomy is consulted before falling back to a
  null sentinel that the HI-01 rubric ``... is null`` branch can match.
- ``hi0X_search_completed`` flags are derived from the HI quality columns.
- Landlocked-country flag derives from ISO 3166-1 alpha-2.
"""

from __future__ import annotations

from atoms_vs_ashes.scoring.merge_context_derivations import (
    apply_derived_context_values,
)


class TestMilitaryAirfieldDistanceDerivation:
    def test_explicit_value_preserved(self) -> None:
        values = {"nearest_military_airfield_km": 12.5}
        apply_derived_context_values(values)
        assert values["nearest_military_airfield_km"] == 12.5

    def test_high_consequence_airfield_used_as_primary_signal(self) -> None:
        values = {
            "nearest_high_consequence_military_class": "airfield",
            "nearest_high_consequence_military_km": 18.3,
            "nearest_military_class": "training_area",
            "nearest_military_km": 5.0,
            "hi06_quality": "ok",
        }
        apply_derived_context_values(values)
        assert values["nearest_military_airfield_km"] == 18.3

    def test_falls_back_to_nearest_military_when_airfield_is_nearest(self) -> None:
        values = {
            "nearest_high_consequence_military_class": "depot",
            "nearest_high_consequence_military_km": 22.0,
            "nearest_military_class": "airfield",
            "nearest_military_km": 11.0,
            "hi06_quality": "ok",
        }
        apply_derived_context_values(values)
        assert values["nearest_military_airfield_km"] == 11.0

    def test_search_completed_no_airfield_yields_null_sentinel(self) -> None:
        """The previously unconditional 999.0 default is gone; a completed
        HI-06 search that found no airfield must leave the key explicitly
        ``None`` so the HI-01 ``is null`` favourable branch can fire."""
        values = {
            "nearest_military_class": "other",
            "nearest_military_km": 7.0,
            "nearest_high_consequence_military_class": None,
            "nearest_high_consequence_military_km": None,
            "hi06_quality": "ok",
        }
        apply_derived_context_values(values)
        assert "nearest_military_airfield_km" in values
        assert values["nearest_military_airfield_km"] is None

    def test_search_not_run_leaves_key_absent(self) -> None:
        """If HI-06 did not run (quality is None / no_data / failed), the
        key must be absent so the rubric falls through to unscored rather
        than silently producing a favourable verdict."""
        values: dict[str, object] = {
            "nearest_military_class": None,
            "nearest_military_km": None,
            "nearest_high_consequence_military_class": None,
            "nearest_high_consequence_military_km": None,
            "hi06_quality": None,
        }
        apply_derived_context_values(values)
        assert "nearest_military_airfield_km" not in values

    def test_no_data_quality_leaves_key_absent(self) -> None:
        values: dict[str, object] = {
            "nearest_military_class": None,
            "hi06_quality": "no_data",
        }
        apply_derived_context_values(values)
        assert "nearest_military_airfield_km" not in values


class TestHiSearchCompletedSentinels:
    def test_search_completed_when_quality_is_ok(self) -> None:
        values = {
            "hi02_quality": "ok",
            "hi04_quality": "verified",
            "hi05_quality": "medium",
            "hi08_quality": "approximate",
        }
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is True
        assert values["hi04_search_completed"] is True
        assert values["hi05_search_completed"] is True
        assert values["hi08_search_completed"] is True

    def test_search_not_completed_when_quality_missing(self) -> None:
        values: dict[str, object] = {}
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is False
        assert values["hi04_search_completed"] is False
        assert values["hi05_search_completed"] is False
        assert values["hi08_search_completed"] is False

    def test_search_not_completed_when_quality_is_failure(self) -> None:
        values = {"hi02_quality": "no_data", "hi04_quality": "failed"}
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is False
        assert values["hi04_search_completed"] is False


class TestLandlockedDerivation:
    def test_austria_is_landlocked(self) -> None:
        values = {"country_code": "AT"}
        apply_derived_context_values(values)
        assert values["country_is_landlocked"] is True

    def test_romania_is_not_landlocked(self) -> None:
        values = {"country_code": "RO"}
        apply_derived_context_values(values)
        assert values["country_is_landlocked"] is False

    def test_country_code_lowercase_normalised(self) -> None:
        values = {"country_code": "cz"}
        apply_derived_context_values(values)
        assert values["country_is_landlocked"] is True

    def test_missing_country_code_defaults_false(self) -> None:
        values: dict[str, object] = {}
        apply_derived_context_values(values)
        assert values["country_is_landlocked"] is False
