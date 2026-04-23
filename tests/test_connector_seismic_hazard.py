# man_hours: 10.0
"""Tests for the S-01 GEM/SHARE Seismic Hazard connector.

Covers: pure parsing, validation, result structures, fallback decisions,
integration with mocked HTTP, and batch operations with a test DB.

Updated 2026-04-13 after API exploration revealed:
  - Model discovery XML uses nested <id>/<name> elements
  - ESHM20 curve returns NRML 0.3 format
  - ESHM13 model ID = 68 (not 142)
  - ESHM20 model ID = 81
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from atoms_vs_ashes.connectors.seismic_hazard import (
    BatchResult,
    GemRasterFallback,
    HazardCurve,
    SeismicHazardConnector,
    SeismicHazardResult,
    SiteEnrichmentSummary,
    UniformHazardSpectrum,
    nearest_value,
    parse_map_csv,
    parse_model_discovery,
    parse_nrml_curve,
    parse_nrml_spectra,
    validate_coordinates_in_scope,
    validate_curve_monotonicity,
    validate_pga,
)

# ---------------------------------------------------------------------------
# Sample fixture data (trimmed from real EFEHR responses, 2026-04-13)
# ---------------------------------------------------------------------------

SAMPLE_MAP_CSV = """\
# longitude; latitude; PGA
26.0821339; 44.4; 0.24212687778265965
26.182133900000004; 44.4; 0.2406849820590185
26.0821339; 44.5; 0.24996237652999578
"""

SAMPLE_MAP_CSV_EMPTY = "# longitude; latitude; PGA\n"

SAMPLE_MAP_CSV_SINGLE = """\
# longitude; latitude; PGA
23.12; 44.15; 0.2000
"""

# NRML 0.4 (spec-documented format)
SAMPLE_CURVE_NRML_04 = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves IMT="PGA" investigationTime="50.0">
    <hazardCurve>
      <IMLs>0.005 0.01 0.05 0.1 0.2 0.5 1.0 2.0</IMLs>
      <poEs>0.95 0.90 0.60 0.35 0.12 0.02 0.003 0.0002</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>"""

# NRML 0.3 (actual EFEHR response for ESHM20 curves)
SAMPLE_CURVE_NRML_03 = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ns2:nrml xmlns:ns2="http://openquake.org/xmlns/nrml/0.3" xmlns:ns1="http://www.opengis.net/gml">
    <ns2:hazardResult ns1:id="gml_id_15092">
        <ns2:config>
            <ns2:hazardProcessing saDamping="0.05" saPeriod="0.1" IDmodel="European Seismic hazard Model 2020 (ESHM20)" investigationTimeSpan="50.0"/>
        </ns2:config>
        <ns2:hazardCurveField quantileValue="0.5" statistics="mean" ns1:id="gml_id_15093">
            <ns2:IML IMT="PGA">5.0E-4 0.001 0.005 0.01 0.05 0.1 0.2 0.5 1.0 2.0 3.0</ns2:IML>
            <ns2:HCNode ns1:id="gml_id_15094">
                <ns2:site>
                    <ns1:Point srsName="4326">
                        <ns1:pos>26.0821339 44.4</ns1:pos>
                    </ns1:Point>
                </ns2:site>
                <ns2:hazardCurve>
                    <ns2:poE>1.0 1.0 0.9999 0.9998 0.9462 0.8524 0.6965 0.5018 0.3123 0.0028 0.000002</ns2:poE>
                </ns2:hazardCurve>
            </ns2:HCNode>
        </ns2:hazardCurveField>
    </ns2:hazardResult>
</ns2:nrml>"""

SAMPLE_CURVE_NRML_NO_NS = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml>
  <hazardCurves IMT="PGA" investigationTime="50.0">
    <hazardCurve>
      <IMLs>0.005 0.01 0.05 0.1 0.2 0.5 1.0 2.0</IMLs>
      <poEs>0.95 0.90 0.60 0.35 0.12 0.02 0.003 0.0002</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>"""

SAMPLE_CURVE_NRML_MALFORMED = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves IMT="PGA">
  </hazardCurves>
</nrml>"""

SAMPLE_SPECTRA_NRML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <uniformHazardSpectra investigationTime="50.0">
    <periods>0.10 0.20 0.50 1.00 2.00</periods>
    <uhs poe="0.1">
      <IMLs>0.35 0.28 0.15 0.08 0.03</IMLs>
    </uhs>
  </uniformHazardSpectra>
</nrml>"""

# Real model discovery XML from EFEHR (2026-04-13)
SAMPLE_MODEL_DISCOVERY_XML = """\
<models>\
<model><id>74</id><name>Global Seismic Hz Assessment Program (GSHAP)</name></model>\
<model><id>68</id><name>European Seismic Hazard Model 2013 (ESHM13)</name></model>\
<model><id>81</id><name>European Seismic hazard Model 2020 (ESHM20)</name></model>\
</models>"""

# Attribute-style (for backward compat testing)
SAMPLE_MODEL_DISCOVERY_XML_ATTRS = """\
<?xml version="1.0" encoding="UTF-8"?>
<models>
  <model id="68" name="SHARE 2013"/>
  <model id="142" name="ESHM20"/>
</models>"""

SAMPLE_MODEL_DISCOVERY_XML_NO_ESHM20 = """\
<models>\
<model><id>68</id><name>European Seismic Hazard Model 2013 (ESHM13)</name></model>\
</models>"""

SAMPLE_EFEHR_ERROR = """\
<errors><error>Error is: Command not found for CommandCode: CCODEerror</error></errors>"""


# ===================================================================
# Unit tests — Pure parsing (no I/O)
# ===================================================================


class TestParseMapCsv:
    def test_basic_parse(self):
        rows = parse_map_csv(SAMPLE_MAP_CSV)
        assert len(rows) == 3
        assert rows[0] == pytest.approx((26.0821339, 44.4, 0.2421269), abs=1e-4)

    def test_empty_csv(self):
        rows = parse_map_csv(SAMPLE_MAP_CSV_EMPTY)
        assert rows == []

    def test_blank_string(self):
        assert parse_map_csv("") == []
        assert parse_map_csv("   \n\n") == []

    def test_single_row(self):
        rows = parse_map_csv(SAMPLE_MAP_CSV_SINGLE)
        assert len(rows) == 1
        assert rows[0] == pytest.approx((23.12, 44.15, 0.2000))

    def test_malformed_line_skipped(self):
        csv = "# header\n23.1; 44.1\nnot;a;number\n23.2; 44.2; 0.15"
        rows = parse_map_csv(csv)
        assert len(rows) == 1

    def test_extra_whitespace(self):
        csv = "#  header \n  23.1 ;  44.1 ;  0.15  \n"
        rows = parse_map_csv(csv)
        assert len(rows) == 1
        assert rows[0] == pytest.approx((23.1, 44.1, 0.15))


class TestParseModelDiscovery:
    """Test the model discovery XML parser — nested elements are the real format."""

    def test_nested_elements(self):
        models = parse_model_discovery(SAMPLE_MODEL_DISCOVERY_XML)
        assert len(models) == 3
        ids = {m[0] for m in models}
        assert 68 in ids
        assert 81 in ids
        assert 74 in ids

    def test_finds_eshm20(self):
        models = parse_model_discovery(SAMPLE_MODEL_DISCOVERY_XML)
        eshm20 = [m for m in models if m[0] == 81]
        assert len(eshm20) == 1
        assert "ESHM20" in eshm20[0][1]

    def test_finds_eshm13(self):
        models = parse_model_discovery(SAMPLE_MODEL_DISCOVERY_XML)
        eshm13 = [m for m in models if m[0] == 68]
        assert len(eshm13) == 1
        assert "ESHM13" in eshm13[0][1] or "2013" in eshm13[0][1]

    def test_attribute_style_backward_compat(self):
        models = parse_model_discovery(SAMPLE_MODEL_DISCOVERY_XML_ATTRS)
        assert len(models) == 2
        ids = {m[0] for m in models}
        assert 68 in ids
        assert 142 in ids

    def test_malformed_xml(self):
        assert parse_model_discovery("not xml") == []

    def test_empty_models(self):
        assert parse_model_discovery("<models></models>") == []


class TestParseNrmlCurve:
    def test_nrml04_parse(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_04)
        assert curve is not None
        assert curve.imt == "PGA"
        assert curve.investigation_time == 50.0
        assert len(curve.imls) == 8
        assert len(curve.poes) == 8
        assert curve.imls[0] == pytest.approx(0.005)
        assert curve.poes[-1] == pytest.approx(0.0002)

    def test_nrml03_parse(self):
        """ESHM20 returns NRML 0.3 with ns2: prefixed elements."""
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_03)
        assert curve is not None
        assert curve.imt == "PGA"
        assert curve.investigation_time == 50.0
        assert len(curve.imls) == 11
        assert len(curve.poes) == 11
        assert curve.imls[0] == pytest.approx(5e-4)
        assert curve.poes[0] == pytest.approx(1.0)

    def test_no_namespace(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_NO_NS)
        assert curve is not None
        assert len(curve.imls) == 8

    def test_malformed_xml(self):
        assert parse_nrml_curve("not xml at all") is None

    def test_incomplete_curve(self):
        assert parse_nrml_curve(SAMPLE_CURVE_NRML_MALFORMED) is None

    def test_efehr_error_response(self):
        assert parse_nrml_curve(SAMPLE_EFEHR_ERROR) is None

    def test_to_dict(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_04)
        d = curve.to_dict()
        assert d["imt"] == "PGA"
        assert len(d["imls"]) == 8
        assert len(d["poes"]) == 8


class TestParseNrmlSpectra:
    def test_basic_parse(self):
        uhs = parse_nrml_spectra(SAMPLE_SPECTRA_NRML)
        assert uhs is not None
        assert uhs.poe == pytest.approx(0.1)
        assert uhs.investigation_time == 50.0
        assert len(uhs.periods) == 5
        assert len(uhs.sa_values) == 5
        assert uhs.periods[0] == pytest.approx(0.10)
        assert uhs.sa_values[0] == pytest.approx(0.35)

    def test_malformed_xml(self):
        assert parse_nrml_spectra("<broken") is None

    def test_empty_spectra(self):
        xml = (
            '<?xml version="1.0"?>'
            '<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">'
            "</nrml>"
        )
        assert parse_nrml_spectra(xml) is None

    def test_efehr_error_response(self):
        assert parse_nrml_spectra(SAMPLE_EFEHR_ERROR) is None

    def test_to_dict(self):
        uhs = parse_nrml_spectra(SAMPLE_SPECTRA_NRML)
        d = uhs.to_dict()
        assert d["poe"] == pytest.approx(0.1)
        assert len(d["periods"]) == 5


class TestNearestValue:
    def test_exact_match(self):
        grid = [(23.12, 44.15, 0.20)]
        val, dist = nearest_value(grid, 44.15, 23.12)
        assert val == pytest.approx(0.20)
        assert dist < 0.01

    def test_picks_closest(self):
        grid = [
            (23.00, 44.00, 0.10),
            (23.12, 44.15, 0.20),
            (24.00, 45.00, 0.30),
        ]
        val, dist = nearest_value(grid, 44.14, 23.11)
        assert val == pytest.approx(0.20)
        assert dist < 2.0

    def test_empty_grid_raises(self):
        with pytest.raises(ValueError, match="Empty grid"):
            nearest_value([], 44.0, 23.0)

    def test_single_distant_point(self):
        grid = [(0.0, 0.0, 0.50)]
        val, dist = nearest_value(grid, 44.0, 23.0)
        assert val == pytest.approx(0.50)
        assert dist > 1000


class TestPgaValidation:
    def test_normal_value(self):
        level, detail = validate_pga(0.15)
        assert level == "high"
        assert detail is None

    def test_zero(self):
        level, _ = validate_pga(0.0)
        assert level == "high"

    def test_high_but_plausible(self):
        level, _ = validate_pga(1.8)
        assert level == "high"

    def test_unusually_high(self):
        level, detail = validate_pga(2.5)
        assert level == "low"
        assert "2.5" in detail

    def test_implausibly_high(self):
        level, _ = validate_pga(5.1)
        assert level == "insufficient"

    def test_negative(self):
        level, _ = validate_pga(-0.1)
        assert level == "insufficient"

    def test_none(self):
        level, _ = validate_pga(None)
        assert level == "insufficient"


class TestCurveMonotonicity:
    def test_valid_curve_nrml04(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_04)
        assert validate_curve_monotonicity(curve) is True

    def test_valid_curve_nrml03(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_03)
        assert validate_curve_monotonicity(curve) is True

    def test_non_monotonic(self):
        curve = HazardCurve(
            imt="PGA",
            imls=[0.01, 0.1, 0.5],
            poes=[0.5, 0.8, 0.1],
        )
        assert validate_curve_monotonicity(curve) is False

    def test_constant_poe(self):
        curve = HazardCurve(imt="PGA", imls=[0.01, 0.1], poes=[0.5, 0.5])
        assert validate_curve_monotonicity(curve) is True


class TestCoordinateValidation:
    def test_in_scope(self):
        assert validate_coordinates_in_scope(44.15, 23.12) is True

    def test_out_of_scope_north(self):
        assert validate_coordinates_in_scope(65.0, 23.0) is False

    def test_out_of_scope_west(self):
        assert validate_coordinates_in_scope(44.0, 5.0) is False

    def test_boundary(self):
        assert validate_coordinates_in_scope(35.0, 12.0) is True
        assert validate_coordinates_in_scope(60.0, 46.0) is True


class TestResultStructure:
    def test_seismic_hazard_result_to_dict(self):
        result = SeismicHazardResult(
            lat=44.15,
            lon=23.12,
            model_id=68,
            model_name="ESHM13",
            pga_475yr=0.15,
            pga_2475yr=0.30,
            source="efehr_eshm13",
        )
        d = result.to_dict()
        assert d["lat"] == 44.15
        assert d["pga_475yr"] == pytest.approx(0.15)
        assert d["pga_2475yr"] == pytest.approx(0.30)
        assert d["source"] == "efehr_eshm13"
        assert d["vs30_reference"] == 760.0
        assert d["hazard_curve"] is None
        assert d["uhs"] is None

    def test_result_with_curve_and_uhs(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_04)
        uhs = parse_nrml_spectra(SAMPLE_SPECTRA_NRML)
        result = SeismicHazardResult(
            lat=44.15, lon=23.12,
            pga_475yr=0.15,
            hazard_curve=curve,
            uhs=uhs,
            sa_values={"0.10s": 0.35, "1.00s": 0.08},
        )
        d = result.to_dict()
        assert d["hazard_curve"] is not None
        assert d["uhs"] is not None
        assert "0.10s" in d["sa_values"]

    def test_batch_result_summary_line(self):
        br = BatchResult(
            run_id="test-001",
            total_sites=20,
            succeeded=19,
            failed=1,
            skipped_cached=0,
            elapsed_s=72.5,
        )
        line = br.summary_line()
        assert "20 sites" in line
        assert "19 ok" in line
        assert "1 failed" in line

    def test_batch_result_short_elapsed(self):
        br = BatchResult(run_id="t", elapsed_s=3.2, total_sites=1, succeeded=1)
        line = br.summary_line()
        assert "3.2 s" in line

    def test_batch_result_to_dict(self):
        br = BatchResult(
            run_id="run-x",
            total_sites=2,
            succeeded=1,
            failed=1,
            per_site=[
                SiteEnrichmentSummary(
                    site_id=uuid.uuid4(), site_name="Site A",
                    status="ok", pga_475yr=0.15, source="efehr_eshm13",
                    elapsed_ms=200,
                ),
                SiteEnrichmentSummary(
                    site_id=uuid.uuid4(), site_name="Site B",
                    status="error", error="timeout",
                    elapsed_ms=30000,
                ),
            ],
        )
        d = br.to_dict()
        assert d["total_sites"] == 2
        assert len(d["per_site"]) == 2
        assert d["per_site"][0]["status"] == "ok"
        assert d["per_site"][1]["status"] == "error"


class TestFallbackDecision:
    """Test that fallback is triggered in the right scenarios."""

    def test_empty_efehr_triggers_fallback(self):
        connector = SeismicHazardConnector()
        connector._eshm13_id = 68
        connector._models_discovered = True

        with patch.object(connector, "_request_with_retry", return_value=None):
            result = connector.fetch_all(44.15, 23.12)
            assert result.pga_475yr is None or "gem" in result.source

    def test_empty_map_csv_triggers_bbox_expansion(self):
        """When the first map query returns empty CSV, connector retries with larger bbox."""
        connector = SeismicHazardConnector()
        connector._eshm13_id = 68
        connector._models_discovered = True
        connector._inter_request_delay = 0.0

        call_count = 0

        def mock_request(url, params):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.text = SAMPLE_MAP_CSV_EMPTY if call_count <= 1 else SAMPLE_MAP_CSV_SINGLE
            resp.status_code = 200
            return resp

        with patch.object(connector, "_request_with_retry", side_effect=mock_request):
            with patch.object(connector, "fetch_hazard_curve", return_value=None):
                with patch.object(connector, "fetch_uhs", return_value=None):
                    result = connector.fetch_all(44.15, 23.12)

        assert call_count >= 2


# ===================================================================
# Integration tests — mocked HTTP
# ===================================================================


def _mock_response(text: str, status_code: int = 200) -> httpx.Response:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.text = text
    resp.status_code = status_code
    return resp


class TestFetchPgaFullFlow:
    def test_fetches_two_return_periods(self):
        connector = SeismicHazardConnector()
        connector._eshm13_id = 68
        connector._models_discovered = True
        connector._inter_request_delay = 0.0

        responses = iter([
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
        ])

        with patch.object(
            connector, "_request_with_retry",
            side_effect=lambda *a, **kw: next(responses),
        ):
            pga_475, pga_2475, dist, source = connector.fetch_pga(44.43, 26.10)

        assert pga_475 is not None
        assert pga_2475 is not None
        assert dist >= 0
        assert source == "efehr_eshm13"


class TestModelDiscoveryCaching:
    def test_discovers_both_models(self):
        connector = SeismicHazardConnector()
        assert connector._eshm20_id is None
        assert connector._eshm13_id is None

        resp = _mock_response(SAMPLE_MODEL_DISCOVERY_XML)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            connector.discover_models(44.15, 23.12)

        assert connector._eshm20_id == 81
        assert connector._eshm13_id == 68
        assert connector._models_discovered is True

    def test_caches_after_first_call(self):
        connector = SeismicHazardConnector()
        resp = _mock_response(SAMPLE_MODEL_DISCOVERY_XML)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            mid = connector.discover_model(44.15, 23.12)

        assert mid is not None

        with patch.object(connector, "_request_with_retry") as mock_req:
            mid2 = connector.discover_model(47.0, 15.0)
            mock_req.assert_not_called()
        assert mid2 is not None

    def test_fallback_to_first_model(self):
        connector = SeismicHazardConnector()
        no_eshm = "<models><model><id>99</id><name>Unknown Model</name></model></models>"
        resp = _mock_response(no_eshm)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            connector.discover_models(44.15, 23.12)
        assert connector._eshm13_id == 99

    def test_handles_no_response(self):
        connector = SeismicHazardConnector()
        with patch.object(connector, "_request_with_retry", return_value=None):
            mid = connector.discover_model(44.15, 23.12)
        assert mid is None


class TestFetchAll:
    def _make_connector(self) -> SeismicHazardConnector:
        conn = SeismicHazardConnector()
        conn._eshm13_id = 68
        conn._eshm20_id = 81
        conn._models_discovered = True
        conn._inter_request_delay = 0.0
        return conn

    def test_full_flow_success(self):
        connector = self._make_connector()

        map_resp = _mock_response(SAMPLE_MAP_CSV)
        curve_resp = _mock_response(SAMPLE_CURVE_NRML_03)
        error_resp = _mock_response(SAMPLE_EFEHR_ERROR)

        # Call sequence: 2 map (PGA 475yr + 2475yr for ESHM13),
        # then curve ESHM20 (succeeds), then spectra ESHM20 + ESHM13 (both error)
        responses = iter([
            map_resp,       # PGA 475yr map (ESHM13)
            map_resp,       # PGA 2475yr map (ESHM13)
            curve_resp,     # Hazard curve (ESHM20 — NRML 0.3, succeeds)
            error_resp,     # Spectra ESHM20 (error)
            error_resp,     # Spectra ESHM13 (error)
        ])

        with patch.object(
            connector, "_request_with_retry",
            side_effect=lambda *a, **kw: next(responses),
        ):
            result = connector.fetch_all(44.43, 26.10)

        assert result.pga_475yr is not None
        assert result.source == "efehr_eshm13"
        assert result.quality in ("high", "medium", "low")
        assert result.hazard_curve is not None

    def test_gem_fallback_when_efehr_down(self):
        connector = self._make_connector()

        with patch.object(connector, "_request_with_retry", return_value=None):
            with patch.object(connector._gem_fallback, "sample", return_value=0.18):
                result = connector.fetch_all(44.15, 23.12)

        assert result.source == "gem_global_v2023"
        assert result.pga_475yr == pytest.approx(0.18)
        assert result.quality == "medium"
        assert result.hazard_curve is None
        assert result.uhs is None


class TestHealthCheck:
    def test_healthy(self):
        connector = SeismicHazardConnector()
        resp = MagicMock()
        resp.status_code = 200
        with patch.object(connector._client, "get", return_value=resp):
            assert connector.health_check() is True

    def test_unhealthy(self):
        connector = SeismicHazardConnector()
        with patch.object(
            connector._client, "get",
            side_effect=httpx.ConnectError("down"),
        ):
            assert connector.health_check() is False


class TestRetryLogic:
    def test_retries_on_500(self):
        connector = SeismicHazardConnector()
        connector._base_delay = 0.0
        connector._max_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 500
        fail_resp.request = MagicMock()

        ok_resp = MagicMock(spec=httpx.Response)
        ok_resp.status_code = 200
        ok_resp.text = SAMPLE_MAP_CSV

        with patch.object(
            connector._client, "get", side_effect=[fail_resp, ok_resp]
        ):
            resp = connector._request_with_retry("http://test", {})

        assert resp is not None
        assert resp.status_code == 200

    def test_gives_up_after_max_retries(self):
        connector = SeismicHazardConnector()
        connector._base_delay = 0.0
        connector._max_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 500
        fail_resp.request = MagicMock()

        with patch.object(
            connector._client, "get", return_value=fail_resp
        ):
            resp = connector._request_with_retry("http://test", {})

        assert resp is None

    def test_no_retry_on_400(self):
        connector = SeismicHazardConnector()
        connector._base_delay = 0.0

        fail_resp = MagicMock(spec=httpx.Response)
        fail_resp.status_code = 404

        with patch.object(
            connector._client, "get", return_value=fail_resp
        ) as mock_get:
            resp = connector._request_with_retry("http://test", {})
            assert mock_get.call_count == 1

        assert resp is None


class TestConnectorSettings:
    def test_defaults_without_settings(self):
        connector = SeismicHazardConnector()
        assert connector._timeout == 30
        assert connector._inter_request_delay == 0.5
        assert connector._cache_ttl_days == 365
        assert connector._default_imt == "PGA"
        assert "share" in connector._base_url

    def test_from_settings(self, settings):
        connector = SeismicHazardConnector(settings)
        assert connector._base_url == "http://appsrvr.share-eu.org:8080/share"
        assert connector._timeout == 30


class TestContextManager:
    def test_enter_exit(self):
        with SeismicHazardConnector() as conn:
            assert isinstance(conn, SeismicHazardConnector)


# ===================================================================
# GEM Raster Fallback tests
# ===================================================================


class TestGemRasterFallback:
    def test_no_tiff_raises(self, tmp_path):
        fb = GemRasterFallback(tmp_path)
        with pytest.raises(FileNotFoundError, match="No GeoTIFF"):
            fb._open()

    def test_sample_returns_none_when_no_tiff(self, tmp_path):
        fb = GemRasterFallback(tmp_path)
        assert fb.sample(44.0, 23.0) is None

    def test_rasterio_not_installed(self, tmp_path):
        (tmp_path / "test.tif").write_bytes(b"fake")
        fb = GemRasterFallback(tmp_path)
        with patch.dict("sys.modules", {"rasterio": None}):
            with pytest.raises((ImportError, TypeError)):
                fb._open()
