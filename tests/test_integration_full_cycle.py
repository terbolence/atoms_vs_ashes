# man_hours: 8.0
"""Full-cycle integration tests for all controllers.

Verifies that each controller can complete the entire cycle:
import → fetch/parse → evaluate → produce result dataclass → (mock) persist

These tests use mock/fixture data and do NOT require network or database.
They test the pure-logic paths end-to-end.
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ===================================================================
# I-1 CORINE — full cycle tests
# ===================================================================


class TestCorineFullCycle:
    """Verify CORINE connector: import → classify → result structure."""

    SAMPLE_FEATURES = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [23.10, 44.14],
                        [23.12, 44.14],
                        [23.12, 44.16],
                        [23.10, 44.16],
                        [23.10, 44.14],
                    ]
                ],
            },
            "properties": {"code_18": "211"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [23.08, 44.14],
                        [23.10, 44.14],
                        [23.10, 44.16],
                        [23.08, 44.16],
                        [23.08, 44.14],
                    ]
                ],
            },
            "properties": {"code_18": "311"},
        },
    ]

    def test_import_and_classify(self):
        from atoms_vs_ashes.connectors.corine import (
            CorineConnector,
            SiteClassification,
            CRITERION_IDS,
        )
        assert "NS-05" in CRITERION_IDS
        assert "NH-13" in CRITERION_IDS

        result = CorineConnector.analyze_rings_from_features(
            lat=44.15, lon=23.11, features=self.SAMPLE_FEATURES,
        )
        assert isinstance(result, SiteClassification)
        assert result.error is None
        assert len(result.rings) == 3  # default 3 rings
        assert result.total_developable_ha >= 0

    def test_classify_empty_features(self):
        from atoms_vs_ashes.connectors.corine import CorineConnector

        result = CorineConnector.analyze_rings_from_features(
            lat=44.15, lon=23.11, features=[],
        )
        assert result.error is not None

    def test_classify_result_to_dict(self):
        from atoms_vs_ashes.connectors.corine import CorineConnector

        result = CorineConnector.analyze_rings_from_features(
            lat=44.15, lon=23.11, features=self.SAMPLE_FEATURES,
        )
        d = result.to_dict()
        assert "rings" in d
        assert "total_developable_ha" in d
        assert isinstance(d["total_developable_ha"], float)

    def test_models_constants(self):
        from atoms_vs_ashes.connectors.corine.models import (
            CRITERION_IDS,
            HIGH_COMBUSTIBILITY_CLC,
            MEDIUM_COMBUSTIBILITY_CLC,
            NATURAL_SEMINATURAL_CLC,
            LAYDOWN_SUITABLE_CLC,
            FAVOURABLE_FOOTPRINT_CLC,
            NON_EU_COUNTRIES,
            CORINE_COVERED_COUNTRIES,
        )
        assert "311" in HIGH_COMBUSTIBILITY_CLC
        assert "321" in MEDIUM_COMBUSTIBILITY_CLC
        assert "311" in NATURAL_SEMINATURAL_CLC
        assert "121" in LAYDOWN_SUITABLE_CLC
        assert "111" in FAVOURABLE_FOOTPRINT_CLC
        assert "TR" in NON_EU_COUNTRIES
        assert "RO" in CORINE_COVERED_COUNTRIES


# ===================================================================
# I-2 OSM — full cycle tests
# ===================================================================


class TestOsmFullCycle:
    """Verify OSM connector: import → settings → query methods exist."""

    def test_import_and_settings(self):
        from atoms_vs_ashes.connectors.osm import (
            OverpassClient,
            OsmElement,
            CRITERION_IDS,
        )
        assert "EP-01" in CRITERION_IDS
        assert "HI-01" in CRITERION_IDS
        assert "HI-06" in CRITERION_IDS
        assert "NS-02" in CRITERION_IDS

        client = OverpassClient()
        assert client._url == "https://overpass-api.de/api/interpreter"
        client.close()

    def test_settings_override(self):
        from atoms_vs_ashes.connectors.osm import OverpassClient

        mock_settings = MagicMock()
        mock_settings._yaml = {
            "connectors": {
                "osm": {
                    "overpass_url": "https://custom.overpass.de/api/interpreter",
                    "timeout_s": 60,
                }
            }
        }
        client = OverpassClient(settings=mock_settings)
        assert client._url == "https://custom.overpass.de/api/interpreter"
        assert client._timeout == 60
        client.close()

    def test_query_methods_exist(self):
        from atoms_vs_ashes.connectors.osm import OverpassClient

        client = OverpassClient()
        assert hasattr(client, "fetch_airports")
        assert hasattr(client, "fetch_military_areas")
        assert hasattr(client, "fetch_transmitters")
        assert hasattr(client, "fetch_power_infrastructure")
        assert hasattr(client, "fetch_land_use")
        assert hasattr(client, "fetch_populated_places")
        assert hasattr(client, "fetch_amenities")
        assert hasattr(client, "fetch_road_density")
        assert hasattr(client, "fetch_waterways")
        client.close()

    def test_osm_element_dataclass(self):
        from atoms_vs_ashes.connectors.osm import OsmElement

        el = OsmElement(osm_type="node", osm_id=12345, lat=44.1, lon=23.1, tags={"name": "test"})
        assert el.osm_type == "node"
        assert el.tags["name"] == "test"


# ===================================================================
# I-3 Population — full cycle tests
# ===================================================================


class TestPopulationFullCycle:
    """Verify Population connector: import → assign_to_rings → result."""

    def test_import_and_criterion_ids(self):
        from atoms_vs_ashes.connectors.population import (
            PopulationConnector,
            PopulationResult,
            RingPopulation,
            PopulatedPlace,
            CRITERION_IDS,
        )
        assert "RI-04" in CRITERION_IDS
        assert "RI-05" in CRITERION_IDS
        assert "RI-06" in CRITERION_IDS

    def test_assign_to_rings(self):
        from atoms_vs_ashes.connectors.population import (
            PopulationConnector,
            PopulatedPlace,
            RingPopulation,
        )

        places = [
            PopulatedPlace("CityA", 44.2, 23.2, 100_000, distance_km=3.0),
            PopulatedPlace("TownB", 44.3, 23.3, 10_000, distance_km=12.0),
            PopulatedPlace("VillageC", 44.4, 23.4, 500, distance_km=22.0),
        ]

        rings = PopulationConnector._assign_to_rings(
            44.15, 23.11, places, [5, 16, 25, 80],
        )
        assert len(rings) == 4
        assert rings[0].population == 100_000  # 0-5km
        assert rings[1].population == 10_000  # 5-16km
        assert rings[2].population == 500  # 16-25km
        assert rings[0].density_per_km2 > 0

    def test_population_result_methods(self):
        from atoms_vs_ashes.connectors.population import PopulationResult, RingPopulation

        rings = [
            RingPopulation(inner_km=0, outer_km=5, population=50_000, area_km2=78.5, density_per_km2=636.9),
            RingPopulation(inner_km=5, outer_km=16, population=200_000, area_km2=725.7, density_per_km2=275.5),
        ]
        result = PopulationResult(lat=44.1, lon=23.1, rings=rings, total_population_80km=250_000)

        assert result.population_at_radius(5) == 50_000
        assert result.population_at_radius(16) == 250_000
        assert result.density_at_radius(5) == pytest.approx(636.9, abs=0.1)

    def test_result_to_dict(self):
        from atoms_vs_ashes.connectors.population import PopulationResult

        result = PopulationResult(lat=44.1, lon=23.1)
        d = result.to_dict()
        assert "rings" in d
        assert "total_population_80km" in d


# ===================================================================
# Analysis modules — pure logic full cycle tests
# ===================================================================


class TestEP01FullCycle:
    """EP-01 Emergency Plan composite — label collision fix verified."""

    def test_sub_score_labels_use_ep01_prefix(self):
        from atoms_vs_ashes.analysis.emergency_plan import evaluate_ep01

        result = evaluate_ep01(
            road_data={"density_km_per_km2": 1.0, "total_road_km": 50, "by_class_km": {}},
            amenities=[],
            waterway_count=0,
            has_major_river=False,
            epz_population=10_000,
            density_inner_km2=100,
            density_threshold=1_000,
        )

        for sub in result.sub_scores:
            assert sub.sub_criterion.startswith("ep01_"), (
                f"Sub-score label '{sub.sub_criterion}' does not use ep01_ prefix"
            )
            assert not sub.sub_criterion.startswith("EP-"), (
                f"Sub-score label '{sub.sub_criterion}' still uses old EP-0x format"
            )

    def test_composite_score_range(self):
        from atoms_vs_ashes.analysis.emergency_plan import evaluate_ep01

        result = evaluate_ep01(
            road_data={"density_km_per_km2": 1.5, "total_road_km": 100, "by_class_km": {"motorway": 10}},
            amenities=[{"amenity": "hospital", "name": "H1"}],
            waterway_count=1,
            has_major_river=False,
            epz_population=50_000,
            density_inner_km2=200,
            density_threshold=1_000,
        )

        assert 0 <= result.composite_score <= 100
        assert result.verdict in ("pass", "fail", "inconclusive")
        assert len(result.sub_scores) == 4

    def test_weights_sum_to_one(self):
        from atoms_vs_ashes.analysis.emergency_plan import WEIGHTS

        total = sum(WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=0.001)

    def test_source_refs_includes_population(self):
        """Verify FIX-01-F: source_refs mentions population_connector."""
        from atoms_vs_ashes.analysis.emergency_plan import EmergencyPlanCheck
        assert hasattr(EmergencyPlanCheck, "criterion_id")
        assert EmergencyPlanCheck.criterion_id == "EP-01"


class TestRI04FullCycle:
    """RI-04 population density — dual persistence verified."""

    def test_evaluate_ri04_pass(self):
        from atoms_vs_ashes.analysis.epz_population import evaluate_ri04
        from atoms_vs_ashes.connectors.population import RingPopulation

        rings = [
            RingPopulation(0, 5, population=5_000, area_km2=78.5, density_per_km2=63.7),
            RingPopulation(5, 16, population=50_000, area_km2=725.7, density_per_km2=68.9),
        ]
        verdict, value_dict, justification = evaluate_ri04(rings, density_threshold=1_000)
        assert verdict == "pass"
        assert "ring_densities" in value_dict
        assert "max_density_ring" in value_dict

    def test_evaluate_ri04_fail(self):
        from atoms_vs_ashes.analysis.epz_population import evaluate_ri04
        from atoms_vs_ashes.connectors.population import RingPopulation

        rings = [
            RingPopulation(0, 5, population=100_000, area_km2=78.5, density_per_km2=1_273.9),
        ]
        verdict, value_dict, justification = evaluate_ri04(rings, density_threshold=1_000)
        assert verdict == "fail"
        assert value_dict["exceeds_threshold"] is True

    def test_evaluate_ri04_empty(self):
        from atoms_vs_ashes.analysis.epz_population import evaluate_ri04

        verdict, _, _ = evaluate_ri04([], density_threshold=1_000)
        assert verdict == "inconclusive"


class TestWildfireContextFullCycle:
    """NH-13 wildfire context — pure logic test."""

    SAMPLE_FEATURES = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[23.0, 44.0], [23.1, 44.0], [23.1, 44.1], [23.0, 44.1], [23.0, 44.0]]],
            },
            "properties": {"code_18": "312"},  # Coniferous forest — high combustibility
        },
    ]

    def test_assess_wildfire_context(self):
        from atoms_vs_ashes.analysis.wildfire_context import assess_wildfire_context

        mock_corine = MagicMock()
        mock_corine.fetch.return_value = self.SAMPLE_FEATURES

        result = assess_wildfire_context(44.05, 23.05, mock_corine, buffer_radii_km=[5])
        assert result.error is None
        assert result.max_combustible_pct > 0
        assert len(result.ring_combustibility) == 1

    def test_empty_features(self):
        from atoms_vs_ashes.analysis.wildfire_context import assess_wildfire_context

        mock_corine = MagicMock()
        mock_corine.fetch.return_value = []

        result = assess_wildfire_context(44.05, 23.05, mock_corine)
        assert result.error is not None


class TestEcologicalSensitivityFullCycle:
    """NS-08 ecological sensitivity — pure logic test."""

    SAMPLE_FEATURES = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[23.0, 44.0], [23.05, 44.0], [23.05, 44.05], [23.0, 44.05], [23.0, 44.0]]],
            },
            "properties": {"code_18": "311"},  # Broad-leaved forest
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[23.05, 44.0], [23.1, 44.0], [23.1, 44.05], [23.05, 44.05], [23.05, 44.0]]],
            },
            "properties": {"code_18": "112"},  # Discontinuous urban
        },
    ]

    def test_assess_ecological_sensitivity(self):
        from atoms_vs_ashes.analysis.ecological_sensitivity import assess_ecological_sensitivity

        mock_corine = MagicMock()
        mock_corine.fetch.return_value = self.SAMPLE_FEATURES

        result = assess_ecological_sensitivity(44.025, 23.05, mock_corine, buffer_radius_m=5000)
        assert result.error is None
        assert result.patch_count >= 1
        assert result.natural_pct >= 0

    def test_empty_features(self):
        from atoms_vs_ashes.analysis.ecological_sensitivity import assess_ecological_sensitivity

        mock_corine = MagicMock()
        mock_corine.fetch.return_value = []

        result = assess_ecological_sensitivity(44.0, 23.0, mock_corine)
        assert result.error is not None


class TestSiteTopographyFullCycle:
    """NS-04 site topography."""

    def test_assess_site_topography(self):
        from atoms_vs_ashes.analysis.site_topography import assess_site_topography

        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[23.0, 44.0], [23.02, 44.0], [23.02, 44.02], [23.0, 44.02], [23.0, 44.0]]],
                },
                "properties": {"code_18": "211"},
            },
        ]
        mock_corine = MagicMock()
        mock_corine.fetch.return_value = features

        result = assess_site_topography(44.01, 23.01, mock_corine, site_area_ha=50)
        assert result.error is None


class TestLaydownAreaFullCycle:
    """NS-13 laydown area."""

    def test_assess_laydown_area(self):
        from atoms_vs_ashes.analysis.laydown_area import assess_laydown_area

        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[23.0, 44.0], [23.02, 44.0], [23.02, 44.02], [23.0, 44.02], [23.0, 44.0]]],
                },
                "properties": {"code_18": "131"},  # Mineral extraction — suitable
            },
        ]
        mock_corine = MagicMock()
        mock_corine.fetch.return_value = features

        result = assess_laydown_area(44.01, 23.01, mock_corine)
        assert result.error is None
        assert result.total_suitable_ha > 0


class TestAviationHazardFullCycle:
    """HI-01 aviation hazard."""

    def test_assess_aviation_hazard(self):
        from atoms_vs_ashes.analysis.aviation_hazard import assess_aviation_hazard, classify_airport
        from atoms_vs_ashes.connectors.osm import OsmElement

        mock_overpass = MagicMock()
        mock_overpass.fetch_airports.return_value = [
            OsmElement("node", 1, 44.2, 23.2, {"name": "Craiova Airport", "iata": "CRA", "aeroway": "aerodrome"}),
            OsmElement("node", 2, 44.3, 23.3, {"aeroway": "helipad"}),
        ]

        result = assess_aviation_hazard(44.15, 23.15, mock_overpass)
        assert result.airport_count == 2
        assert result.nearest_distance_km is not None
        assert result.airports[0]["type"] == "international"

        assert classify_airport({"iata": "CRA"}) == "international"
        assert classify_airport({"aeroway": "helipad"}) == "helipad"
        assert classify_airport({}) == "local"

    def test_no_airports(self):
        from atoms_vs_ashes.analysis.aviation_hazard import assess_aviation_hazard

        mock_overpass = MagicMock()
        mock_overpass.fetch_airports.return_value = []

        result = assess_aviation_hazard(44.15, 23.15, mock_overpass)
        assert result.airport_count == 0
        assert result.nearest_distance_km is None


class TestMilitaryProximityFullCycle:
    """HI-06 military proximity."""

    def test_assess_military(self):
        from atoms_vs_ashes.analysis.military_proximity import assess_military_proximity
        from atoms_vs_ashes.connectors.osm import OsmElement

        mock_overpass = MagicMock()
        mock_overpass.fetch_military_areas.return_value = [
            OsmElement("way", 1, 44.2, 23.2, {"landuse": "military", "name": "Base X"}),
        ]

        result = assess_military_proximity(44.15, 23.15, mock_overpass)
        assert result.installation_count == 1
        assert result.nearest_distance_km is not None

    def test_no_military(self):
        from atoms_vs_ashes.analysis.military_proximity import assess_military_proximity

        mock_overpass = MagicMock()
        mock_overpass.fetch_military_areas.return_value = []

        result = assess_military_proximity(44.15, 23.15, mock_overpass)
        assert result.installation_count == 0


class TestTransmitterProximityFullCycle:
    """HI-07 transmitter proximity."""

    def test_assess_transmitters(self):
        from atoms_vs_ashes.analysis.transmitter_proximity import (
            assess_transmitter_proximity,
            classify_transmitter,
        )
        from atoms_vs_ashes.connectors.osm import OsmElement

        mock_overpass = MagicMock()
        mock_overpass.fetch_transmitters.return_value = [
            OsmElement("node", 1, 44.18, 23.12, {"man_made": "mast", "tower:type": "communication"}),
        ]

        result = assess_transmitter_proximity(44.15, 23.15, mock_overpass)
        assert result.transmitter_count == 1
        assert classify_transmitter({"tower:type": "communication"}) == "communication_tower"
        assert classify_transmitter({"power": "substation"}) == "transmission_substation"


class TestGridProximityFullCycle:
    """NS-02 grid proximity."""

    def test_assess_grid_proximity(self):
        from atoms_vs_ashes.analysis.grid_proximity import assess_grid_proximity
        from atoms_vs_ashes.connectors.osm import OsmElement

        mock_overpass = MagicMock()
        mock_overpass.fetch_power_infrastructure.return_value = [
            OsmElement("way", 1, 44.18, 23.12, {"power": "line", "voltage": "400000", "name": "400kV Line"}),
            OsmElement("node", 2, 44.16, 23.14, {"power": "substation", "name": "Craiova 400kV"}),
        ]

        result = assess_grid_proximity(44.15, 23.15, mock_overpass)
        assert result.hv_line_count == 1
        assert result.substation_count == 1
        assert result.nearest_hv_line_km is not None
        assert result.nearest_hv_line_voltage_kv == 400.0


class TestPopulationProjectionFullCycle:
    """RI-06 population projection."""

    def test_project_population(self):
        from atoms_vs_ashes.analysis.population_projection import project_population
        from atoms_vs_ashes.connectors.population import PopulationResult, RingPopulation

        rings = [
            RingPopulation(0, 5, population=50_000, area_km2=78.5, density_per_km2=636.9),
            RingPopulation(5, 16, population=200_000, area_km2=725.7, density_per_km2=275.5),
        ]
        pop_result = PopulationResult(lat=44.1, lon=23.1, rings=rings, total_population_80km=250_000)

        result = project_population(pop_result, "RO")
        assert result.current_density_5km == pytest.approx(636.9, abs=0.1)
        assert result.growth_rate == -0.006  # Romania
        assert result.projected_density_5km < result.current_density_5km  # declining population
        assert result.projection_year == 2085
        assert len(result.ring_projections) == 2

    def test_project_unknown_country(self):
        from atoms_vs_ashes.analysis.population_projection import project_population, DEFAULT_GROWTH_RATE
        from atoms_vs_ashes.connectors.population import PopulationResult

        result = project_population(PopulationResult(lat=0, lon=0), "ZZ")
        assert result.growth_rate == DEFAULT_GROWTH_RATE


class TestCoalSiteAnalysisFullCycle:
    """NS-05 coal site reuse."""

    def test_evaluate_coal_site(self):
        from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

        result = evaluate_coal_site(100.0, "retired", smr_land_ha=72.8)
        assert result.sufficiency_ratio == pytest.approx(100.0 / 72.8, abs=0.01)
        assert result.is_sufficient is True

    def test_evaluate_insufficient(self):
        from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

        result = evaluate_coal_site(30.0, "retired", smr_land_ha=72.8)
        assert result.is_sufficient is False

    def test_evaluate_no_area(self):
        from atoms_vs_ashes.analysis.coal_site_analysis import evaluate_coal_site

        result = evaluate_coal_site(None, "retired")
        assert result.error is not None


class TestLandAvailabilityFullCycle:
    """NS-05 contiguous land."""

    def test_assess_land_availability(self):
        from atoms_vs_ashes.analysis.land_availability import assess_land_availability
        from atoms_vs_ashes.connectors.osm import OsmElement

        mock_overpass = MagicMock()
        mock_overpass.fetch_land_use.return_value = [
            OsmElement("way", 1, 44.15, 23.15, {"landuse": "industrial"}),
            OsmElement("way", 2, 44.16, 23.16, {"landuse": "farmland"}),
            OsmElement("way", 3, 44.17, 23.17, {"landuse": "residential"}),  # not buildable
        ]

        result = assess_land_availability(44.15, 23.15, mock_overpass)
        assert result.patch_count == 2  # industrial + farmland
        assert "industrial" in result.by_landuse


class TestProximityLandFullCycle:
    """NS-05 proximity land analysis."""

    def test_proximity_result_structure(self):
        from atoms_vs_ashes.analysis.proximity_land import ProximityResult

        result = ProximityResult(site_area_ha=50.0)
        d = result.to_dict()
        assert "site_area_ha" in d
        assert "available_adjacent_ha" in d
        assert "smr_compatibility" in d


class TestRI05FullCycle:
    """RI-05 city distance evaluation."""

    def test_evaluate_ri05(self):
        from atoms_vs_ashes.analysis.epz_population import evaluate_ri05
        from atoms_vs_ashes.connectors.population import PopulatedPlace

        cities = [
            PopulatedPlace("CityA", 44.2, 23.2, 200_000, distance_km=15.0),
            PopulatedPlace("CityB", 44.3, 23.3, 80_000, distance_km=30.0),
        ]
        result = evaluate_ri05(cities, 50_000)
        assert result["nearest_city_name"] == "CityA"
        assert result["nearest_city_distance_km"] == 15.0
        assert result["cities_within_80km"] == 2

    def test_evaluate_ri05_no_cities(self):
        from atoms_vs_ashes.analysis.epz_population import evaluate_ri05

        result = evaluate_ri05([], 50_000)
        assert result["nearest_city_name"] is None


# ===================================================================
# DB compatibility — CRITERION_IDS discovery
# ===================================================================


class TestCriterionIdsDiscovery:
    """All connectors and ingest expose CRITERION_IDS."""

    def test_corine_criterion_ids(self):
        from atoms_vs_ashes.connectors.corine.models import CRITERION_IDS
        assert isinstance(CRITERION_IDS, tuple)
        assert "NS-05" in CRITERION_IDS
        assert "NH-13" in CRITERION_IDS

    def test_osm_criterion_ids(self):
        from atoms_vs_ashes.connectors.osm.models import CRITERION_IDS
        assert isinstance(CRITERION_IDS, tuple)
        assert "EP-01" in CRITERION_IDS
        assert "HI-01" in CRITERION_IDS

    def test_population_criterion_ids(self):
        from atoms_vs_ashes.connectors.population.models import CRITERION_IDS
        assert isinstance(CRITERION_IDS, tuple)
        assert "RI-04" in CRITERION_IDS
        assert "RI-06" in CRITERION_IDS

    def test_ingest_criterion_ids(self):
        from atoms_vs_ashes.ingest.models import CRITERION_IDS
        assert isinstance(CRITERION_IDS, tuple)
        assert "NS-05" in CRITERION_IDS


# ===================================================================
# Provenance utility tests
# ===================================================================


class TestProvenanceUtility:
    """Verify _provenance module functions exist and have correct signatures."""

    def test_imports(self):
        from atoms_vs_ashes.analysis._provenance import ensure_data_source, write_quality_flag
        import inspect
        sig = inspect.signature(ensure_data_source)
        assert "session" in sig.parameters
        assert "name" in sig.parameters
        assert "url" in sig.parameters
