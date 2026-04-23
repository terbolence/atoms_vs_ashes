# man_hours: 4.0
"""Tests for ENTSO-E connector — parsing, computation, and transformation logic.

No network calls. Tests pure parsing against fixture XML and computation
logic against synthetic data.
"""

from __future__ import annotations

import pytest

from atoms_vs_ashes.connectors.entso_e.models import (
    BIDDING_ZONES,
    CRITERION_IDS,
    SOURCE_NAME,
    CapacityEntry,
    CapacityMetrics,
    EntsoEResult,
    GenerationUnit,
    InstalledCapacityAggregated,
    InterconnectionMetrics,
    InterconnectorSummary,
    NtcEntry,
    NtcTimeSeries,
    ZoneGridAssessment,
)
from atoms_vs_ashes.connectors.entso_e.parsers import (
    assess_nuclear_readiness,
    compute_capacity_metrics,
    compute_interconnection_metrics,
    determine_quality,
    identify_bidding_zone,
    is_acknowledgement,
    parse_flows_xml,
    parse_generation_units_xml,
    parse_installed_capacity_xml,
    parse_ntc_xml,
)

# ---------------------------------------------------------------------------
# Fixture XML data (from S-13 spec §10.5)
# ---------------------------------------------------------------------------

SAMPLE_CAPACITY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <mRID>ENTSOE_GL_1234</mRID>
  <type>A68</type>
  <process.processType>A33</process.processType>
  <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
  <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
  <createdDateTime>2025-01-15T10:00:00Z</createdDateTime>
  <time_Period.timeInterval>
    <start>2025-01-01T00:00Z</start>
    <end>2026-01-01T00:00Z</end>
  </time_Period.timeInterval>
  <TimeSeries>
    <mRID>1</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B14</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>1300</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>2</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B05</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>4800</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>3</mRID>
    <businessType>A37</businessType>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YRO-TEL------P</inBiddingZone_Domain.mRID>
    <MktPSRType>
      <psrType>B12</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>6400</quantity>
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>"""

SAMPLE_ACKNOWLEDGEMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Acknowledgement_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0">
  <mRID>ENTSOE_ACK_5678</mRID>
  <createdDateTime>2025-04-01T12:00:00Z</createdDateTime>
  <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
  <receiver_MarketParticipant.mRID codingScheme="A01">UNKNOWN</receiver_MarketParticipant.mRID>
  <Reason>
    <code>999</code>
    <text>No matching data found</text>
  </Reason>
</Acknowledgement_MarketDocument>"""

SAMPLE_PER_UNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <mRID>ENTSOE_GL_UNIT_001</mRID>
  <type>A71</type>
  <TimeSeries>
    <mRID>1</mRID>
    <MktPSRType>
      <psrType>B14</psrType>
      <PowerSystemResources>
        <mRID codingScheme="A01">CERNAVODA1</mRID>
        <name>Cernavoda Unit 1</name>
      </PowerSystemResources>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>706.5</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>2</mRID>
    <MktPSRType>
      <psrType>B05</psrType>
      <PowerSystemResources>
        <mRID codingScheme="A01">ROVINARI3</mRID>
        <name>Rovinari Group 3</name>
      </PowerSystemResources>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>330</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>3</mRID>
    <MktPSRType>
      <psrType>B04</psrType>
      <PowerSystemResources>
        <mRID codingScheme="A01">BRAZI1</mRID>
        <name>Brazi CCGT</name>
      </PowerSystemResources>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2026-01-01T00:00Z</end>
      </timeInterval>
      <resolution>P1Y</resolution>
      <Point>
        <position>1</position>
        <quantity>860</quantity>
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>"""

SAMPLE_NTC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Publication_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-5:publicationdocument:7:3">
  <mRID>ENTSOE_NTC_001</mRID>
  <type>A61</type>
  <TimeSeries>
    <mRID>1</mRID>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2025-04-01T00:00Z</end>
      </timeInterval>
      <resolution>P1M</resolution>
      <Point>
        <position>1</position>
        <quantity>800</quantity>
      </Point>
      <Point>
        <position>2</position>
        <quantity>850</quantity>
      </Point>
      <Point>
        <position>3</position>
        <quantity>900</quantity>
      </Point>
    </Period>
  </TimeSeries>
</Publication_MarketDocument>"""

SAMPLE_FLOWS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <mRID>ENTSOE_FLOW_001</mRID>
  <type>A11</type>
  <TimeSeries>
    <mRID>1</mRID>
    <Period>
      <timeInterval>
        <start>2025-01-01T00:00Z</start>
        <end>2025-01-02T00:00Z</end>
      </timeInterval>
      <resolution>PT60M</resolution>
      <Point>
        <position>1</position>
        <quantity>450</quantity>
      </Point>
      <Point>
        <position>2</position>
        <quantity>520</quantity>
      </Point>
      <Point>
        <position>3</position>
        <quantity>380</quantity>
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>"""


# ===================================================================
# Acknowledgement detection
# ===================================================================

class TestAcknowledgementDetection:

    def test_acknowledgement_detected(self):
        is_ack, reason = is_acknowledgement(SAMPLE_ACKNOWLEDGEMENT_XML)
        assert is_ack is True
        assert reason == "No matching data found"

    def test_data_document_not_acknowledgement(self):
        is_ack, reason = is_acknowledgement(SAMPLE_CAPACITY_XML)
        assert is_ack is False
        assert reason is None

    def test_empty_string(self):
        is_ack, reason = is_acknowledgement("")
        assert is_ack is False

    def test_malformed_xml(self):
        is_ack, reason = is_acknowledgement("<not valid xml")
        assert is_ack is False


# ===================================================================
# A68: Installed capacity parsing
# ===================================================================

class TestParseInstalledCapacityXml:

    def test_parse_romania_capacity(self):
        result = parse_installed_capacity_xml(
            SAMPLE_CAPACITY_XML, "10YRO-TEL------P", 2025,
        )
        assert result.zone_eic == "10YRO-TEL------P"
        assert result.year == 2025
        assert len(result.entries) == 3

    def test_capacity_values(self):
        result = parse_installed_capacity_xml(
            SAMPLE_CAPACITY_XML, "10YRO-TEL------P", 2025,
        )
        assert result.by_type("B14") == pytest.approx(1300.0)
        assert result.by_type("B05") == pytest.approx(4800.0)
        assert result.by_type("B12") == pytest.approx(6400.0)

    def test_total_capacity(self):
        result = parse_installed_capacity_xml(
            SAMPLE_CAPACITY_XML, "10YRO-TEL------P", 2025,
        )
        assert result.total_mw == pytest.approx(12500.0)

    def test_missing_psr_type_defaults_to_b20(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <TimeSeries>
    <MktPSRType>
    </MktPSRType>
    <Period>
      <Point><position>1</position><quantity>100</quantity></Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>"""
        result = parse_installed_capacity_xml(xml, "TEST", 2025)
        assert len(result.entries) == 1
        assert result.entries[0].psr_type == "B20"


# ===================================================================
# A71: Per-unit capacity parsing
# ===================================================================

class TestParseGenerationUnitsXml:

    def test_parse_three_units(self):
        units = parse_generation_units_xml(SAMPLE_PER_UNIT_XML, "10YRO-TEL------P")
        assert len(units) == 3

    def test_unit_names(self):
        units = parse_generation_units_xml(SAMPLE_PER_UNIT_XML, "10YRO-TEL------P")
        names = {u.unit_name for u in units}
        assert "Cernavoda Unit 1" in names
        assert "Rovinari Group 3" in names
        assert "Brazi CCGT" in names

    def test_unit_capacities(self):
        units = parse_generation_units_xml(SAMPLE_PER_UNIT_XML, "10YRO-TEL------P")
        by_name = {u.unit_name: u for u in units}
        assert by_name["Cernavoda Unit 1"].installed_mw == pytest.approx(706.5)
        assert by_name["Rovinari Group 3"].installed_mw == pytest.approx(330.0)
        assert by_name["Brazi CCGT"].installed_mw == pytest.approx(860.0)

    def test_unit_psr_types(self):
        units = parse_generation_units_xml(SAMPLE_PER_UNIT_XML, "10YRO-TEL------P")
        by_name = {u.unit_name: u for u in units}
        assert by_name["Cernavoda Unit 1"].psr_type == "B14"
        assert by_name["Rovinari Group 3"].psr_type == "B05"
        assert by_name["Brazi CCGT"].psr_type == "B04"

    def test_unit_eic_codes(self):
        units = parse_generation_units_xml(SAMPLE_PER_UNIT_XML, "10YRO-TEL------P")
        by_name = {u.unit_name: u for u in units}
        assert by_name["Cernavoda Unit 1"].unit_eic == "CERNAVODA1"


# ===================================================================
# NTC parsing
# ===================================================================

class TestParseNtcXml:

    def test_parse_ntc_entries(self):
        ntc = parse_ntc_xml(SAMPLE_NTC_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert len(ntc.entries) == 3
        assert ntc.from_eic == "10YRO-TEL------P"
        assert ntc.to_eic == "10YHU-MAVIR----U"

    def test_ntc_values(self):
        ntc = parse_ntc_xml(SAMPLE_NTC_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        values = [e.mw for e in ntc.entries]
        assert values == [800.0, 850.0, 900.0]

    def test_ntc_mean(self):
        ntc = parse_ntc_xml(SAMPLE_NTC_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert ntc.mean_mw == pytest.approx(850.0)

    def test_ntc_max(self):
        ntc = parse_ntc_xml(SAMPLE_NTC_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert ntc.max_mw == pytest.approx(900.0)


# ===================================================================
# Flow parsing
# ===================================================================

class TestParseFlowsXml:

    def test_parse_flow_entries(self):
        flows = parse_flows_xml(SAMPLE_FLOWS_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert len(flows.entries) == 3

    def test_flow_values(self):
        flows = parse_flows_xml(SAMPLE_FLOWS_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        values = [e.mw for e in flows.entries]
        assert values == [450.0, 520.0, 380.0]

    def test_flow_mean(self):
        flows = parse_flows_xml(SAMPLE_FLOWS_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert flows.mean_mw == pytest.approx(450.0)

    def test_flow_max(self):
        flows = parse_flows_xml(SAMPLE_FLOWS_XML, "10YRO-TEL------P", "10YHU-MAVIR----U")
        assert flows.max_mw == pytest.approx(520.0)


# ===================================================================
# Capacity metrics computation
# ===================================================================

class TestComputeCapacityMetrics:

    def _make_capacity(self) -> InstalledCapacityAggregated:
        return InstalledCapacityAggregated(
            zone_eic="10YRO-TEL------P", year=2025,
            entries=[
                CapacityEntry("B14", "Nuclear", 1300),
                CapacityEntry("B05", "Fossil Hard coal", 4800),
                CapacityEntry("B12", "Hydro Water Reservoir", 6400),
                CapacityEntry("B16", "Solar", 2500),
                CapacityEntry("B19", "Wind Onshore", 1600),
            ],
        )

    def _make_units(self) -> list[GenerationUnit]:
        return [
            GenerationUnit("Cernavoda 1", "C1", "B14", "Nuclear", 706.5),
            GenerationUnit("Cernavoda 2", "C2", "B14", "Nuclear", 706.5),
            GenerationUnit("Rovinari 3", "R3", "B05", "Hard coal", 330),
            GenerationUnit("Turceni 4", "T4", "B05", "Hard coal", 330),
            GenerationUnit("Mintia 5", "M5", "B05", "Hard coal", 210),
            GenerationUnit("Brazi CCGT", "B1", "B04", "Gas", 860),
        ]

    def test_total_installed(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.total_installed_mw == pytest.approx(16600.0)

    def test_thermal_installed(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.thermal_installed_mw == pytest.approx(4800.0)

    def test_nuclear_installed(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.nuclear_installed_mw == pytest.approx(1300.0)

    def test_hydro_installed(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.hydro_installed_mw == pytest.approx(6400.0)

    def test_wind_solar_installed(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.wind_solar_installed_mw == pytest.approx(4100.0)

    def test_nuclear_precedent(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.has_nuclear_precedent is True

    def test_no_nuclear_precedent(self):
        cap = InstalledCapacityAggregated(
            zone_eic="TEST", year=2025,
            entries=[CapacityEntry("B05", "Hard coal", 5000)],
        )
        metrics = compute_capacity_metrics(cap)
        assert metrics.has_nuclear_precedent is False

    def test_smr_capacity_ratio(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        expected = 462.0 / 16600.0
        assert metrics.smr_capacity_ratio == pytest.approx(expected, abs=1e-4)

    def test_with_units(self):
        metrics = compute_capacity_metrics(self._make_capacity(), self._make_units())
        assert metrics.largest_unit_mw == pytest.approx(860.0)
        assert metrics.largest_unit_name == "Brazi CCGT"
        assert metrics.units_above_400mw == 3  # 706.5, 706.5, 860
        assert metrics.units_above_200mw == 6
        assert metrics.nuclear_units == 2
        assert metrics.coal_units_above_200mw == 3  # 330, 330, 210

    def test_without_units(self):
        metrics = compute_capacity_metrics(self._make_capacity())
        assert metrics.largest_unit_mw is None
        assert metrics.units_above_400mw == 0


# ===================================================================
# Interconnection metrics computation
# ===================================================================

class TestComputeInterconnectionMetrics:

    def test_basic_metrics(self):
        ntc_list = [
            NtcTimeSeries("RO", "HU", [NtcEntry("", "", 800)]),
            NtcTimeSeries("RO", "BG", [NtcEntry("", "", 600)]),
        ]
        metrics = compute_interconnection_metrics(ntc_list, total_installed_mw=16600)
        assert metrics.n_interconnectors == 2
        assert metrics.total_ntc_export_mw == pytest.approx(1400.0)

    def test_interconnection_ratio(self):
        ntc_list = [
            NtcTimeSeries("RO", "HU", [NtcEntry("", "", 800)]),
        ]
        metrics = compute_interconnection_metrics(ntc_list, total_installed_mw=10000)
        assert metrics.interconnection_ratio == pytest.approx(800.0 / 10000.0, abs=1e-4)

    def test_empty_ntc_list(self):
        metrics = compute_interconnection_metrics([], total_installed_mw=10000)
        assert metrics.n_interconnectors == 0
        assert metrics.total_ntc_export_mw == 0.0


# ===================================================================
# Nuclear readiness classification
# ===================================================================

class TestAssessNuclearReadiness:

    def test_none_capacity(self):
        assert assess_nuclear_readiness(None) == "insufficient"

    def test_very_small_zone(self):
        cap = CapacityMetrics(total_installed_mw=300)
        assert assess_nuclear_readiness(cap) == "insufficient"

    def test_limited_zone(self):
        cap = CapacityMetrics(total_installed_mw=800)
        assert assess_nuclear_readiness(cap) == "limited"

    def test_moderate_zone(self):
        cap = CapacityMetrics(total_installed_mw=3000)
        assert assess_nuclear_readiness(cap) == "moderate"

    def test_moderate_with_nuclear_precedent(self):
        cap = CapacityMetrics(total_installed_mw=3000, has_nuclear_precedent=True)
        assert assess_nuclear_readiness(cap) == "good"

    def test_good_zone(self):
        cap = CapacityMetrics(total_installed_mw=7000)
        assert assess_nuclear_readiness(cap) == "good"

    def test_good_with_nuclear_precedent(self):
        cap = CapacityMetrics(total_installed_mw=7000, has_nuclear_precedent=True)
        assert assess_nuclear_readiness(cap) == "excellent"

    def test_excellent_large_zone(self):
        cap = CapacityMetrics(total_installed_mw=15000, has_nuclear_precedent=True)
        assert assess_nuclear_readiness(cap) == "excellent"

    def test_excellent_no_nuclear_but_large_units(self):
        cap = CapacityMetrics(total_installed_mw=15000, units_above_400mw=3)
        assert assess_nuclear_readiness(cap) == "excellent"

    def test_good_large_no_nuclear_few_large_units(self):
        cap = CapacityMetrics(total_installed_mw=15000, units_above_400mw=1)
        assert assess_nuclear_readiness(cap) == "good"

    def test_boundary_500mw(self):
        cap = CapacityMetrics(total_installed_mw=500)
        assert assess_nuclear_readiness(cap) == "limited"

    def test_boundary_499mw(self):
        cap = CapacityMetrics(total_installed_mw=499)
        assert assess_nuclear_readiness(cap) == "insufficient"


# ===================================================================
# Quality determination
# ===================================================================

class TestDetermineQuality:

    def test_full_data(self):
        assert determine_quality(True, True, True, True) == "high"

    def test_a68_and_a71(self):
        assert determine_quality(True, True, False, False) == "medium"

    def test_a68_and_ntc(self):
        assert determine_quality(True, False, True, False) == "medium"

    def test_a68_only(self):
        assert determine_quality(True, False, False, False) == "low"

    def test_no_data(self):
        assert determine_quality(False, False, False, False) == "insufficient"


# ===================================================================
# Bidding zone identification
# ===================================================================

class TestIdentifyBiddingZone:

    def test_romania(self):
        assert identify_bidding_zone("RO") == "10YRO-TEL------P"

    def test_poland(self):
        assert identify_bidding_zone("PL") == "10YPL-AREA-----S"

    def test_all_23_countries(self):
        for cc in BIDDING_ZONES:
            eic = identify_bidding_zone(cc)
            assert eic is not None, f"No EIC for {cc}"
            assert len(eic) >= 10, f"EIC too short for {cc}: {eic}"

    def test_unknown_country(self):
        assert identify_bidding_zone("XX") is None

    def test_case_insensitive(self):
        assert identify_bidding_zone("ro") == "10YRO-TEL------P"

    def test_custom_zones(self):
        custom = {"XX": "10YXX-TEST-----Z"}
        assert identify_bidding_zone("XX", custom) == "10YXX-TEST-----Z"


# ===================================================================
# Result dataclass structure
# ===================================================================

class TestResultStructure:

    def test_entsoe_result_to_dict(self):
        result = EntsoEResult(
            lat=44.43, lon=26.10,
            country_code="RO",
            bidding_zone_eic="10YRO-TEL------P",
            bidding_zone_name="Romania (RO)",
            nuclear_readiness="excellent",
            reference_year=2025,
            quality="high",
        )
        d = result.to_dict()
        for key in [
            "lat", "lon", "country_code", "bidding_zone_eic",
            "bidding_zone_name", "nuclear_readiness", "reference_year",
            "source", "quality",
        ]:
            assert key in d, f"Missing key: {key}"

    def test_capacity_metrics_to_dict(self):
        metrics = CapacityMetrics(
            total_installed_mw=16600,
            nuclear_installed_mw=1300,
            has_nuclear_precedent=True,
            smr_capacity_ratio=0.028,
        )
        d = metrics.to_dict()
        assert d["total_installed_mw"] == 16600
        assert d["has_nuclear_precedent"] is True

    def test_zone_assessment_to_dict(self):
        assessment = ZoneGridAssessment(
            zone_eic="10YRO-TEL------P",
            zone_name="Romania (RO)",
            country_code="RO",
            reference_year=2025,
            nuclear_readiness="excellent",
            quality="high",
        )
        d = assessment.to_dict()
        assert d["zone_eic"] == "10YRO-TEL------P"
        assert d["nuclear_readiness"] == "excellent"


# ===================================================================
# Constants and model integrity
# ===================================================================

class TestConstants:

    def test_criterion_ids(self):
        assert CRITERION_IDS == ("NS-02",)

    def test_source_name(self):
        assert SOURCE_NAME == "entsoe_transparency_platform"

    def test_bidding_zones_count(self):
        assert len(BIDDING_ZONES) == 23

    def test_all_eic_codes_unique(self):
        eics = list(BIDDING_ZONES.values())
        assert len(eics) == len(set(eics))


# ===================================================================
# Per-unit fuzzy matching (FIX-02-B §3.2.1)
# ===================================================================

class TestNormalise:
    """Tests for the improved name normalisation function."""

    def test_strips_diacritics(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("Bełchatów") == "belchatow"

    def test_strips_suffix_power_station(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("Tušimice power station") == "tusimice"

    def test_strips_suffix_power_plant(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("Rovinari Power Plant") == "rovinari"

    def test_strips_suffix_thermal(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("Turceni Thermal") == "turceni"

    def test_strips_suffix_kraftwerk(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("Dürnrohr Kraftwerk") == "durnrohr"

    def test_lowercase(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("ROVINARI") == "rovinari"

    def test_empty_string(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        assert normalise("") == ""

    def test_splits_underscores(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        result = normalise("CTE_Rovinari_ROVI3_CA")
        assert "rovinari" in result.split()

    def test_splits_camelcase(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        result = normalise("CteTurceni")
        tokens = result.split()
        assert "turceni" in tokens

    def test_strips_trailing_digits(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        result = normalise("CetCraiova2")
        assert "craiova" in result.split()

    def test_splits_dot_separator(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import normalise
        result = normalise("EPVR.B1")
        assert "." not in result


class TestExtractCoreTokens:
    """Tests for TSO prefix/suffix stripping and core-name extraction."""

    def test_strips_tso_prefix_cte(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        tokens = extract_core_tokens("CTE_Rovinari_ROVI3_CA")
        assert "rovinari" in tokens

    def test_strips_tso_prefix_tpp(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        tokens = extract_core_tokens("TPP_BOBOV_DOL_G1")
        assert "bobov" in tokens
        assert "dol" in tokens

    def test_strips_tso_prefix_te(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        tokens = extract_core_tokens("TE_GACKO_G1")
        assert "gacko" in tokens

    def test_strips_code_suffixes(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        tokens = extract_core_tokens("CTE_Rovinari_ROVI3_CA")
        assert "ca" not in tokens

    def test_empty_input(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        assert extract_core_tokens("") == []

    def test_unknown_unit(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_core_tokens
        tokens = extract_core_tokens("Unknown")
        assert "unknown" in tokens


class TestExtractAbbreviation:
    """Tests for Czech-style coded abbreviation extraction."""

    def test_czech_echv(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_abbreviation
        assert extract_abbreviation("ECHV_G1____") == "chv"

    def test_czech_edet(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_abbreviation
        assert extract_abbreviation("EDET_G1____") == "det"

    def test_czech_eled(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_abbreviation
        assert extract_abbreviation("ELED_G4") == "led"

    def test_non_coded_name_returns_none(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_abbreviation
        assert extract_abbreviation("Rovinari Group 3") is None

    def test_short_code_returns_none(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import extract_abbreviation
        assert extract_abbreviation("EG1") is None


class TestCapacityConfirms:
    """Tests for capacity proximity confirmation."""

    def test_exact_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(820.0, 820.0) is True

    def test_close_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(810.0, 800.0) is True

    def test_unit_is_one_block(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(330.0, 1920.0) is True

    def test_unit_way_too_large(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(5000.0, 100.0) is False

    def test_zero_site_capacity(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(820.0, 0.0) is False

    def test_zero_unit_capacity(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import capacity_confirms
        assert capacity_confirms(0.0, 820.0) is False


class TestMatchEntsoEUnits:
    """Tests for multi-stage matching of ENTSO-E A71 units to site names."""

    def _make_units(self) -> list[GenerationUnit]:
        return [
            GenerationUnit("Cernavoda Unit 1", "C1", "B14", "Nuclear", 706.5),
            GenerationUnit("Cernavoda Unit 2", "C2", "B14", "Nuclear", 706.5),
            GenerationUnit("Rovinari Group 3", "R3", "B05", "Hard coal", 330),
            GenerationUnit("Rovinari Group 4", "R4", "B05", "Hard coal", 330),
            GenerationUnit("Turceni Unit 5", "T5", "B05", "Hard coal", 330),
            GenerationUnit("Turceni Unit 6", "T6", "B05", "Hard coal", 330),
            GenerationUnit("Brazi CCGT", "B1", "B04", "Gas", 860),
        ]

    def test_stage1_exact_match_rovinari(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("Rovinari", None, self._make_units())
        assert result.matched is True
        assert result.strategy == "fuzzy_direct"
        assert result.unit_count >= 1
        matched_names = [u.unit_name for u in result.matched_units]
        assert any("Rovinari" in n for n in matched_names)

    def test_multiple_units_summed(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("Rovinari", None, self._make_units())
        assert result.matched is True
        assert result.unit_count == 2
        assert result.capacity_mw == pytest.approx(660.0)

    def test_stage1_underscore_split_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("CTE_Rovinari_ROVI3_CA", "R3", "B02", "Lignite", 882)]
        result = match_entsoe_units("Rovinari power station", None, units)
        assert result.matched is True
        assert result.strategy == "fuzzy_direct"

    def test_stage1_camelcase_split_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("CteTurceni_TURC1_CA", "T1", "B02", "Lignite", 526)]
        result = match_entsoe_units("Turceni power station", None, units)
        assert result.matched is True

    def test_stage2_tso_prefix_strip_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("TPP_BOBOV_DOL_G1", "BD1", "B05", "Coal", 150)]
        result = match_entsoe_units(
            "Bobov Dol power station", None, units,
            installed_capacity_mw=300.0,
        )
        assert result.matched is True

    def test_stage2_rejects_without_capacity(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("TPP_RUSE_G4", "RS4", "B02", "Lignite", 110)]
        result = match_entsoe_units("Ruse Iztok power station", None, units)
        assert result.matched is False

    def test_stage2_rejects_capacity_mismatch(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("TPP_MARITSA_3_G1", "M3", "B02", "Lignite", 120)]
        result = match_entsoe_units(
            "Maritsa Iztok-2 power station", None, units,
            installed_capacity_mw=2162.0,
        )
        assert result.matched is False

    def test_stage3_abbreviation_with_capacity(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("ECHV_G1____", "CHV1", "B02", "Lignite", 820)]
        result = match_entsoe_units(
            "Chvaletice power station", None, units,
            installed_capacity_mw=820.0,
        )
        assert result.matched is True
        assert result.strategy == "abbreviation_capacity"

    def test_stage3_abbreviation_without_capacity_fails(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("ECHV_G1____", "CHV1", "B02", "Lignite", 820)]
        result = match_entsoe_units("Chvaletice power station", None, units)
        assert result.matched is False

    def test_no_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("Fantanele Wind Farm", None, self._make_units())
        assert result.matched is False
        assert result.capacity_mw is None

    def test_alternative_names_used(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units(
            "Some Unknown Name", ["Cernavoda"], self._make_units(),
        )
        assert result.matched is True
        matched_names = [u.unit_name for u in result.matched_units]
        assert any("Cernavoda" in n for n in matched_names)

    def test_diacritics_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("Bełchatów B01", "BEL1", "B02", "Lignite", 370)]
        result = match_entsoe_units("Belchatow", None, units)
        assert result.matched is True
        assert result.capacity_mw == pytest.approx(370.0)

    def test_suffix_stripping_helps_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [GenerationUnit("Turceni Unit 5", "T5", "B05", "Hard coal", 330)]
        result = match_entsoe_units("Turceni power station", None, units)
        assert result.matched is True

    def test_empty_units_list(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("Rovinari", None, [])
        assert result.matched is False

    def test_empty_site_name(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("", None, self._make_units())
        assert result.matched is False

    def test_unknown_units_counted(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        units = [
            GenerationUnit("Rovinari Group 3", "R3", "B05", "Hard coal", 330),
            GenerationUnit("Unknown", None, "B02", "Lignite", 500),
            GenerationUnit("Unknown", None, "B04", "Gas", 200),
        ]
        result = match_entsoe_units("Rovinari", None, units)
        assert result.matched is True
        assert result.zone_unknown_count == 2
        assert result.zone_unknown_total_mw == pytest.approx(700.0)

    def test_match_result_to_dict_includes_strategy(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import match_entsoe_units
        result = match_entsoe_units("Rovinari", None, self._make_units())
        d = result.to_dict()
        assert "matched" in d
        assert "strategy" in d
        assert "capacity_mw" in d
        assert "zone_unknown_count" in d
        assert isinstance(d["matched_unit_names"], list)


# ===================================================================
# EntsoEResult with per_unit_match field
# ===================================================================

class TestEntsoEResultWithMatch:

    def test_to_dict_includes_per_unit_match(self):
        from atoms_vs_ashes.connectors.entso_e.matcher import MatchResult
        result = EntsoEResult(
            lat=44.43, lon=26.10,
            country_code="RO",
            per_unit_match=MatchResult(
                matched=True,
                strategy="fuzzy_direct",
                capacity_mw=660.0,
                unit_count=2,
                best_score=85.0,
            ),
            quality="high",
        )
        d = result.to_dict()
        assert d["per_unit_match"] is not None
        assert d["per_unit_match"]["matched"] is True
        assert d["per_unit_match"]["capacity_mw"] == 660.0
        assert d["per_unit_match"]["strategy"] == "fuzzy_direct"

    def test_to_dict_per_unit_match_none(self):
        result = EntsoEResult(lat=44.43, lon=26.10, quality="medium")
        d = result.to_dict()
        assert d["per_unit_match"] is None


# ===================================================================
# Voltage parsing fix (FIX-02-C)
# ===================================================================

class TestParseVoltageKv:
    """Tests for the multi-voltage parsing fix in grid_proximity."""

    def test_single_voltage(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": "400000"}) == pytest.approx(400.0)

    def test_multi_voltage(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": "400000;220000"}) == pytest.approx(400.0)

    def test_duplicate_voltage(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": "110000;110000"}) == pytest.approx(110.0)

    def test_empty_voltage(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": ""}) is None

    def test_no_voltage_tag(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({}) is None

    def test_invalid_voltage(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": "invalid"}) is None

    def test_trailing_semicolon(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": "400000;"}) == pytest.approx(400.0)

    def test_leading_semicolon(self):
        from atoms_vs_ashes.analysis.grid_proximity import _parse_voltage_kv
        assert _parse_voltage_kv({"voltage": ";220000"}) == pytest.approx(220.0)
