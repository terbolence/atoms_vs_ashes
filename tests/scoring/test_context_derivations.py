# man_hours: 1.2
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


class TestNh11PrecipitationProxyDerivation:
    def test_under_scaled_monthly_means_are_corrected(self) -> None:
        values = {
            "mean_annual_precip_mm": 25.0,
            "extreme_precip_mm": 0.3,
        }
        apply_derived_context_values(values)
        assert values["mean_annual_precip_corrected_mm"] == 760.0
        assert round(values["extreme_precip_corrected_mm"], 2) == 9.12

    def test_plausible_precipitation_values_are_preserved(self) -> None:
        values = {
            "mean_annual_precip_mm": 650.0,
            "extreme_precip_mm": 42.0,
        }
        apply_derived_context_values(values)
        assert values["mean_annual_precip_corrected_mm"] == 650.0
        assert values["extreme_precip_corrected_mm"] == 42.0

    def test_no_data_quality_leaves_key_absent(self) -> None:
        values: dict[str, object] = {
            "nearest_military_class": None,
            "hi06_quality": "no_data",
        }
        apply_derived_context_values(values)
        assert "nearest_military_airfield_km" not in values


class TestHi01AirportClassDistanceDerivation:
    def test_nearest_airport_class_sets_light_distance(self) -> None:
        values = {
            "nearest_airport_km": 7.3,
            "nearest_airport_type": "small_airport",
            "nearest_airport_class": "small_airport",
            "hi01_comment": "Nearest large: 34.2 km; Nearest medium: 18.1 km",
        }
        apply_derived_context_values(values)
        assert values["nearest_small_airport_km"] == 7.3
        assert values["nearest_light_airport_km"] == 7.3
        assert values["nearest_large_airport_km"] == 34.2
        assert values["nearest_medium_airport_km"] == 18.1
        assert values["nearest_major_airport_km"] == 18.1

    def test_nearer_shadowed_major_airport_is_exposed_from_comment(self) -> None:
        values = {
            "nearest_airport_km": 1.39,
            "nearest_airport_type": "heliport",
            "nearest_airport_class": "heliport",
            "hi01_comment": "Nearest: EMS pad (heliport) at 1.4 km; Nearest medium: 4.3 km",
        }
        apply_derived_context_values(values)
        assert values["nearest_heliport_km"] == 1.39
        assert values["nearest_light_airport_km"] == 1.39
        assert values["nearest_medium_airport_km"] == 4.3
        assert values["nearest_major_airport_km"] == 4.3

    def test_nearest_medium_aliases_type2_distance(self) -> None:
        values = {
            "nearest_airport_km": 12.0,
            "nearest_airport_type": "medium_airport",
            "nearest_airport_class": "medium_airport",
        }
        apply_derived_context_values(values)
        assert values["nearest_medium_airport_km"] == 12.0
        assert values["nearest_type2_airport_km"] == 12.0
        assert values["nearest_major_airport_km"] == 12.0


class TestHiSearchCompletedSentinels:
    def test_search_completed_when_quality_is_ok(self) -> None:
        values = {
            "hi02_quality": "ok",
            "hi04_quality": "verified",
            "hi05_quality": "medium",
            "hi07_quality": "screening",
            "hi08_quality": "approximate",
        }
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is True
        assert values["hi04_search_completed"] is True
        assert values["hi05_search_completed"] is True
        assert values["hi07_search_completed"] is True
        assert values["hi08_search_completed"] is True

    def test_search_not_completed_when_quality_missing(self) -> None:
        values: dict[str, object] = {}
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is False
        assert values["hi04_search_completed"] is False
        assert values["hi05_search_completed"] is False
        assert values["hi07_search_completed"] is False
        assert values["hi08_search_completed"] is False

    def test_search_not_completed_when_quality_is_failure(self) -> None:
        values = {"hi02_quality": "no_data", "hi04_quality": "failed", "hi07_quality": "no_data"}
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is False
        assert values["hi04_search_completed"] is False
        assert values["hi07_search_completed"] is False

    def test_not_applicable_quality_counts_as_completed_search(self) -> None:
        values = {"hi02_quality": "not_applicable", "hi03_quality": "not_applicable"}
        apply_derived_context_values(values)
        assert values["hi02_search_completed"] is True
        assert values["hi03_search_completed"] is True


class TestHi07TransmitterDerivation:
    def test_transmitter_count_alias_and_quality_sentinel(self) -> None:
        values = {"transmitter_count": 3, "nearest_transmitter_km": 8.5, "hi07_quality": "ok"}

        apply_derived_context_values(values)

        assert values["transmitter_count_10km"] == 3
        assert values["nearest_transmitter_km"] == 8.5
        assert values["hi07_search_completed"] is True


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


class TestRi05PopulationCentreProxy:
    def test_nearest_city_population_derives_required_distance_and_margin(self) -> None:
        values = {
            "nearest_city_pop": 146_631,
            "nearest_city_50k_km": 30.1,
        }

        apply_derived_context_values(values)

        assert values["ri05_required_distance_km"] == 16.0
        assert values["ri05_distance_margin_pct"] == 88.125

    def test_larger_nearest_city_uses_larger_proxy_distance(self) -> None:
        values = {
            "nearest_city_pop": 1_200_000,
            "nearest_city_50k_km": 36.0,
        }

        apply_derived_context_values(values)

        assert values["ri05_required_distance_km"] == 48.0
        assert values["ri05_distance_margin_pct"] == -25.0

    def test_missing_population_leaves_ri05_proxy_absent(self) -> None:
        values = {"nearest_city_50k_km": 6.7}

        apply_derived_context_values(values)

        assert "ri05_required_distance_km" not in values
        assert "ri05_distance_margin_pct" not in values

    def test_ghsl_density_infers_city_population_tier(self) -> None:
        values = {
            "nearest_city_pop": None,
            "pop_density_16km": 320.0,
            "nearest_city_50k_km": 20.0,
        }
        apply_derived_context_values(values)
        assert values["nearest_city_pop"] == 500_000
        assert values["ri05_required_distance_km"] == 32.0


class TestEp03ReliefDerivation:
    def test_gee_relief_maps_to_rubric_anchor(self) -> None:
        values = {"ep03_gee_relief_16km_m": 88.0}
        apply_derived_context_values(values)
        assert values["relief_m_per_10km"] == 88.0


class TestRi03AquiferScreeningDerivation:
    def test_low_permeability_label(self) -> None:
        values = {"aquifer_type": "low permeability"}
        apply_derived_context_values(values)
        assert values["ri03_aquifer_screening_class"] == "low"

    def test_karst_label(self) -> None:
        values = {"aquifer_type": "karstic carbonate"}
        apply_derived_context_values(values)
        assert values["ri03_aquifer_screening_class"] == "karst"


class TestHi03SearchCompleted:
    def test_hi03_quality_ok_sets_sentinel(self) -> None:
        values = {"hi03_quality": "medium"}
        apply_derived_context_values(values)
        assert values["hi03_search_completed"] is True
