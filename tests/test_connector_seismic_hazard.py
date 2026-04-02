# man_hours: 8.0
"""Tests for the S-01 GEM/SHARE Seismic Hazard connector.

Covers: pure parsing, validation, result structures, fallback decisions,
integration with mocked HTTP, and batch operations with a test DB.
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
    parse_nrml_curve,
    parse_nrml_spectra,
    validate_coordinates_in_scope,
    validate_curve_monotonicity,
    validate_pga,
)

# ---------------------------------------------------------------------------
# Sample fixture data (trimmed from real EFEHR responses)
# ---------------------------------------------------------------------------

SAMPLE_MAP_CSV = """\
# longitude; latitude; PGA
23.1234; 44.1456; 0.1523
23.2234; 44.1456; 0.1498
23.1234; 44.2456; 0.1612
"""

SAMPLE_MAP_CSV_EMPTY = "# longitude; latitude; PGA\n"

SAMPLE_MAP_CSV_SINGLE = """\
# longitude; latitude; PGA
23.12; 44.15; 0.2000
"""

SAMPLE_CURVE_NRML = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves IMT="PGA" investigationTime="50.0">
    <hazardCurve>
      <IMLs>0.005 0.01 0.05 0.1 0.2 0.5 1.0 2.0</IMLs>
      <poEs>0.95 0.90 0.60 0.35 0.12 0.02 0.003 0.0002</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>"""

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

SAMPLE_MODEL_DISCOVERY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<models>
  <model id="68" name="SHARE 2013"/>
  <model id="142" name="ESHM20"/>
</models>"""

SAMPLE_MODEL_DISCOVERY_XML_NO_ESHM20 = """\
<?xml version="1.0" encoding="UTF-8"?>
<models>
  <model id="68" name="SHARE 2013"/>
</models>"""


# ===================================================================
# Unit tests — Pure parsing (no I/O)
# ===================================================================


class TestParseMapCsv:
    def test_basic_parse(self):
        rows = parse_map_csv(SAMPLE_MAP_CSV)
        assert len(rows) == 3
        assert rows[0] == pytest.approx((23.1234, 44.1456, 0.1523))

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


class TestParseNrmlCurve:
    def test_basic_parse(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML)
        assert curve is not None
        assert curve.imt == "PGA"
        assert curve.investigation_time == 50.0
        assert len(curve.imls) == 8
        assert len(curve.poes) == 8
        assert curve.imls[0] == pytest.approx(0.005)
        assert curve.poes[-1] == pytest.approx(0.0002)

    def test_no_namespace(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML_NO_NS)
        assert curve is not None
        assert len(curve.imls) == 8

    def test_malformed_xml(self):
        assert parse_nrml_curve("not xml at all") is None

    def test_incomplete_curve(self):
        assert parse_nrml_curve(SAMPLE_CURVE_NRML_MALFORMED) is None

    def test_to_dict(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML)
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
        assert dist < 2.0  # within ~2 km

    def test_empty_grid_raises(self):
        with pytest.raises(ValueError, match="Empty grid"):
            nearest_value([], 44.0, 23.0)

    def test_single_distant_point(self):
        grid = [(0.0, 0.0, 0.50)]
        val, dist = nearest_value(grid, 44.0, 23.0)
        assert val == pytest.approx(0.50)
        assert dist > 1000  # very far


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
    def test_valid_curve(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML)
        assert validate_curve_monotonicity(curve) is True

    def test_non_monotonic(self):
        curve = HazardCurve(
            imt="PGA",
            imls=[0.01, 0.1, 0.5],
            poes=[0.5, 0.8, 0.1],  # 0.8 > 0.5 → non-monotonic
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
            model_id=142,
            model_name="ESHM20",
            pga_475yr=0.15,
            pga_2475yr=0.30,
            source="efehr_eshm20",
        )
        d = result.to_dict()
        assert d["lat"] == 44.15
        assert d["pga_475yr"] == pytest.approx(0.15)
        assert d["pga_2475yr"] == pytest.approx(0.30)
        assert d["source"] == "efehr_eshm20"
        assert d["vs30_reference"] == 760.0
        assert d["hazard_curve"] is None
        assert d["uhs"] is None

    def test_result_with_curve_and_uhs(self):
        curve = parse_nrml_curve(SAMPLE_CURVE_NRML)
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
                    status="ok", pga_475yr=0.15, source="efehr_eshm20",
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
    """Test that GEM fallback is triggered in the right scenarios."""

    def test_empty_efehr_triggers_fallback(self):
        connector = SeismicHazardConnector()
        connector._model_id_cache = 142

        with patch.object(connector, "_request_with_retry", return_value=None):
            result = connector.fetch_all(44.15, 23.12)
            assert result.pga_475yr is None or result.source == "gem_global_v2023"

    def test_empty_map_csv_triggers_bbox_expansion(self):
        """When the first map query returns empty CSV, connector retries with larger bbox."""
        connector = SeismicHazardConnector()
        connector._model_id_cache = 142
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
        connector._model_id_cache = 142

        responses = iter([
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
            _mock_response(SAMPLE_MAP_CSV),
        ])

        with patch.object(
            connector, "_request_with_retry", side_effect=lambda *a, **kw: next(responses)
        ):
            pga_475, pga_2475, dist = connector.fetch_pga(44.15, 23.12)

        assert pga_475 is not None
        assert pga_2475 is not None
        assert dist >= 0


class TestModelDiscoveryCaching:
    def test_caches_after_first_call(self):
        connector = SeismicHazardConnector()
        assert connector._model_id_cache is None

        resp = _mock_response(SAMPLE_MODEL_DISCOVERY_XML)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            mid = connector.discover_model(44.15, 23.12)

        assert mid == 142
        assert connector._model_id_cache == 142

        # Second call should NOT make any HTTP request
        with patch.object(connector, "_request_with_retry") as mock_req:
            mid2 = connector.discover_model(47.0, 15.0)
            mock_req.assert_not_called()
        assert mid2 == 142

    def test_fallback_to_first_model(self):
        connector = SeismicHazardConnector()
        resp = _mock_response(SAMPLE_MODEL_DISCOVERY_XML_NO_ESHM20)
        with patch.object(connector, "_request_with_retry", return_value=resp):
            mid = connector.discover_model(44.15, 23.12)
        assert mid == 68  # falls back to SHARE 2013 (first model)

    def test_handles_no_response(self):
        connector = SeismicHazardConnector()
        with patch.object(connector, "_request_with_retry", return_value=None):
            mid = connector.discover_model(44.15, 23.12)
        assert mid is None


class TestFetchAll:
    def _make_connector(self) -> SeismicHazardConnector:
        conn = SeismicHazardConnector()
        conn._model_id_cache = 142
        conn._inter_request_delay = 0.0
        return conn

    def test_full_flow_success(self):
        connector = self._make_connector()

        map_resp = _mock_response(SAMPLE_MAP_CSV)
        curve_resp = _mock_response(SAMPLE_CURVE_NRML)
        spectra_resp = _mock_response(SAMPLE_SPECTRA_NRML)

        responses = iter([
            map_resp, map_resp,   # PGA 475yr + retry, PGA 2475yr + retry
            map_resp, map_resp,
            curve_resp,
            spectra_resp,
        ])

        with patch.object(
            connector, "_request_with_retry",
            side_effect=lambda *a, **kw: next(responses),
        ):
            result = connector.fetch_all(44.15, 23.12)

        assert result.pga_475yr is not None
        assert result.source == "efehr_eshm20"
        assert result.quality in ("high", "medium", "low")

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
        with patch.object(connector._client, "get", side_effect=httpx.ConnectError("down")):
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

        with patch.object(connector._client, "get", return_value=fail_resp) as mock_get:
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
        assert connector._model_name == "ESHM20"
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
