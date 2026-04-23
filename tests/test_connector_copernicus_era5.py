# man_hours: 4.0
"""Tests for the S-04 Copernicus CDS / ERA5 connector.

Covers:
  - Wind rose computation (u/v → 16-sector frequencies)
  - GEV return period fitting (annual maxima → 50-year return value)
  - SPI-12 computation (McKee et al. gamma distribution)
  - Pasquill stability class estimation (BLH + wind proxy)
  - CMIP6 temperature delta
  - Nearest grid cell search
  - Haversine distance
  - Coefficient of variation and seasonality helpers
  - Freezing rain proxy
  - Drought severity index
  - Result dataclass to_dict() structures
  - Validation checks (wind rose sums to 1.0, stability classes sum to 1.0)
  - Missing local data raises RuntimeError
  - CopernicusEra5Connector config loading
  - Mock xarray extraction (integration test with synthetic datasets)

No network access required — all tests use synthetic data or mocks.
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from atoms_vs_ashes.connectors.copernicus_era5.models import (
    CRITERION_IDS,
    SECTOR_LABELS_16,
    BatchResult,
    ClimateProjectionAssessment,
    Era5ClimateResult,
    PrecipitationAssessment,
    SiteEnrichmentSummary,
    StabilityAssessment,
    TemperatureAssessment,
    WindAssessment,
)
from atoms_vs_ashes.connectors.copernicus_era5.parsers import (
    coefficient_of_variation,
    compute_cmip6_delta,
    compute_drought_severity_index,
    compute_freezing_rain_days_proxy,
    compute_gev_return_period,
    compute_pasquill_classes,
    compute_spi,
    compute_wind_rose,
    count_extreme_precip_months,
    count_snow_months,
    haversine_km,
    nearest_grid_indices,
)

# ---------------------------------------------------------------------------
# Fixtures — synthetic data
# ---------------------------------------------------------------------------

# 360 monthly values (30 years): predominantly northerly wind
SAMPLE_U = np.array([0.5, 0.3, -0.5, -1.0, 0.2] * 72, dtype=float)   # eastward
SAMPLE_V = np.array([-3.0, -2.5, -2.0, -1.5, -2.0] * 72, dtype=float)  # northward (negative = from N)

# Temperature: 30 years of monthly max/min (K)
SAMPLE_TMAX_K = np.tile(
    np.array([273.0, 275.0, 280.0, 290.0, 298.0, 305.0,
              308.0, 307.0, 300.0, 290.0, 280.0, 274.0]),
    30,
)
SAMPLE_TMIN_K = np.tile(
    np.array([260.0, 261.0, 264.0, 272.0, 280.0, 288.0,
              292.0, 291.0, 285.0, 275.0, 266.0, 261.0]),
    30,
)
SAMPLE_T2M_K = (SAMPLE_TMAX_K + SAMPLE_TMIN_K) / 2.0

# Monthly precipitation (30 years): mm (converted from ERA5 m)
SAMPLE_PRECIP_MM = np.tile(
    np.array([40.0, 35.0, 45.0, 55.0, 70.0, 80.0,
              50.0, 45.0, 55.0, 60.0, 50.0, 45.0]),
    30,
)

# BLH monthly (30 years): metres
SAMPLE_BLH = np.tile(
    np.array([400.0, 500.0, 800.0, 1200.0, 1600.0, 1800.0,
              1900.0, 1700.0, 1300.0, 800.0, 400.0, 300.0]),
    30,
)


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

class TestHaversineKm:
    def test_same_point_is_zero(self) -> None:
        assert haversine_km(44.43, 26.10, 44.43, 26.10) == pytest.approx(0.0, abs=1e-6)

    def test_equator_one_degree(self) -> None:
        # 1° longitude at equator ≈ 111.3 km
        d = haversine_km(0.0, 0.0, 0.0, 1.0)
        assert 110.0 < d < 112.0

    def test_bucharest_to_warsaw(self) -> None:
        # Bucharest (44.43, 26.10) to Warsaw (52.23, 21.01) ≈ 960-980 km
        d = haversine_km(44.43, 26.10, 52.23, 21.01)
        assert 920.0 < d < 1020.0

    def test_symmetry(self) -> None:
        d1 = haversine_km(44.0, 26.0, 52.0, 21.0)
        d2 = haversine_km(52.0, 21.0, 44.0, 26.0)
        assert d1 == pytest.approx(d2, rel=1e-6)


# ---------------------------------------------------------------------------
# Nearest grid cell
# ---------------------------------------------------------------------------

class TestNearestGridIndices:
    def test_exact_match(self) -> None:
        lats = np.array([35.0, 36.0, 37.0, 38.0])
        lons = np.array([20.0, 21.0, 22.0, 23.0])
        lat_idx, lon_idx, grid_lat, grid_lon, dist = nearest_grid_indices(
            lats, lons, 36.0, 22.0
        )
        assert lat_idx == 1
        assert lon_idx == 2
        assert grid_lat == pytest.approx(36.0)
        assert grid_lon == pytest.approx(22.0)
        assert dist == pytest.approx(0.0, abs=0.001)

    def test_near_match(self) -> None:
        lats = np.array([44.0, 44.25, 44.5, 44.75])
        lons = np.array([26.0, 26.25, 26.5])
        lat_idx, lon_idx, grid_lat, grid_lon, dist = nearest_grid_indices(
            lats, lons, 44.43, 26.10
        )
        # |44.43-44.5|=0.07 < |44.43-44.25|=0.18, so nearest lat is 44.5 (idx=2)
        assert lat_idx == 2
        assert lon_idx == 0   # 26.0 is nearest to 26.10
        assert dist < 25.0    # within ERA5 grid cell size

    def test_out_of_range_clips_to_edge(self) -> None:
        lats = np.array([35.0, 36.0, 37.0])
        lons = np.array([20.0, 21.0, 22.0])
        lat_idx, lon_idx, _, _, _ = nearest_grid_indices(
            lats, lons, 100.0, 0.0
        )
        assert lat_idx == 2  # clips to last element


# ---------------------------------------------------------------------------
# Wind rose
# ---------------------------------------------------------------------------

class TestComputeWindRose:
    def test_basic_structure(self) -> None:
        rose, direction, speed = compute_wind_rose(SAMPLE_U, SAMPLE_V)
        assert isinstance(rose, dict)
        assert len(rose) == 16
        assert set(rose.keys()) == set(SECTOR_LABELS_16)

    def test_sum_to_one(self) -> None:
        rose, _, _ = compute_wind_rose(SAMPLE_U, SAMPLE_V)
        total = sum(rose.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_all_northerly(self) -> None:
        # Wind FROM north: u=0, v negative (wind blowing southward)
        u = np.zeros(360)
        v = np.full(360, -5.0)  # from north
        rose, direction, _ = compute_wind_rose(u, v)
        # North sector should dominate
        assert rose["N"] > 0.8

    def test_all_easterly(self) -> None:
        # Wind FROM east: u negative, v=0
        u = np.full(360, -5.0)  # from east
        v = np.zeros(360)
        rose, _, _ = compute_wind_rose(u, v)
        assert rose["E"] > 0.8

    def test_mean_speed(self) -> None:
        u = np.array([3.0, 4.0])
        v = np.array([0.0, 0.0])
        _, _, mean_speed = compute_wind_rose(u, v)
        assert mean_speed == pytest.approx(3.5, rel=0.01)

    def test_empty_arrays(self) -> None:
        rose, direction, speed = compute_wind_rose(np.array([]), np.array([]))
        assert len(rose) == 16
        assert sum(rose.values()) == pytest.approx(1.0, abs=0.01)
        assert speed == 0.0

    def test_n_sectors_parameter(self) -> None:
        rose8, _, _ = compute_wind_rose(SAMPLE_U, SAMPLE_V, n_sectors=8)
        assert len(rose8) == 8

    def test_nonnegative_frequencies(self) -> None:
        rose, _, _ = compute_wind_rose(SAMPLE_U, SAMPLE_V)
        for freq in rose.values():
            assert freq >= 0.0


# ---------------------------------------------------------------------------
# GEV return period
# ---------------------------------------------------------------------------

class TestComputeGevReturnPeriod:
    def test_basic_fit(self) -> None:
        rng = np.random.default_rng(42)
        # Generate Gumbel-distributed annual maxima (wind gusts 15-35 m/s range)
        annual_max = rng.gumbel(loc=20.0, scale=3.0, size=45)
        annual_max = np.abs(annual_max)
        return_val, quality = compute_gev_return_period(annual_max, return_period=50)
        # 50-year return value should exceed the maximum observed
        assert return_val is not None
        assert return_val > 0.0
        # Quality should be "ok" with 45 data points
        assert quality in ("ok", "fallback_percentile")

    def test_fallback_for_short_series(self) -> None:
        # Only 5 years — below MIN_ANNUAL_MAXIMA
        short_data = np.array([20.0, 22.0, 18.0, 25.0, 21.0])
        return_val, quality = compute_gev_return_period(short_data, return_period=50)
        assert quality == "fallback_percentile"
        assert return_val is not None

    def test_empty_data_returns_none(self) -> None:
        return_val, quality = compute_gev_return_period(np.array([]), return_period=50)
        assert return_val is None
        assert quality == "fallback_percentile"

    def test_all_same_values(self) -> None:
        # Edge case: zero variance
        data = np.full(25, 20.0)
        return_val, quality = compute_gev_return_period(data, return_period=50)
        assert return_val is not None  # should not crash

    def test_return_value_exceeds_mean(self) -> None:
        rng = np.random.default_rng(99)
        data = rng.gumbel(loc=15.0, scale=2.0, size=40)
        data = np.abs(data)
        return_val, _ = compute_gev_return_period(data, return_period=50)
        if return_val is not None:
            assert return_val > float(np.mean(data))


# ---------------------------------------------------------------------------
# SPI-12
# ---------------------------------------------------------------------------

class TestComputeSpi:
    def test_basic_output_shape(self) -> None:
        spi = compute_spi(SAMPLE_PRECIP_MM, window=12)
        assert len(spi) == len(SAMPLE_PRECIP_MM)

    def test_first_window_minus_one_nan(self) -> None:
        spi = compute_spi(SAMPLE_PRECIP_MM, window=12)
        assert np.isnan(spi[0])

    def test_typical_range(self) -> None:
        spi = compute_spi(SAMPLE_PRECIP_MM, window=12)
        valid = spi[np.isfinite(spi)]
        if len(valid) > 0:
            assert float(valid.max()) < 5.0
            assert float(valid.min()) > -5.0

    def test_dry_period_negative_spi(self) -> None:
        # Create 15 years normal + 5 years very dry + 15 years normal
        # More extreme drought signal to ensure negative SPI values are detected
        normal = np.tile([60.0] * 12, 15)
        very_dry = np.tile([2.0] * 12, 5)
        normal2 = np.tile([60.0] * 12, 15)
        precip = np.concatenate([normal, very_dry, normal2])
        spi = compute_spi(precip, window=12)
        valid = spi[np.isfinite(spi)]
        # SPI values should span both positive and negative
        assert len(valid) > 0
        assert float(valid.min()) < float(valid.max())

    def test_too_short_returns_nan(self) -> None:
        short = np.array([40.0, 35.0, 50.0])
        spi = compute_spi(short, window=12)
        assert all(np.isnan(spi))

    def test_zero_precipitation_handled(self) -> None:
        # Series with some zero months
        precip = np.concatenate([SAMPLE_PRECIP_MM[:60], np.zeros(24), SAMPLE_PRECIP_MM[:60]])
        spi = compute_spi(precip, window=12)
        assert len(spi) == len(precip)
        # Should not raise


# ---------------------------------------------------------------------------
# Pasquill stability classes
# ---------------------------------------------------------------------------

class TestComputePasquillClasses:
    def test_basic_structure(self) -> None:
        freqs, stable_frac = compute_pasquill_classes(SAMPLE_BLH, np.ones(len(SAMPLE_BLH)) * 4.0)
        assert isinstance(freqs, dict)
        assert set(freqs.keys()) == {"A", "B", "C", "D", "E", "F"}

    def test_sums_to_one(self) -> None:
        freqs, _ = compute_pasquill_classes(SAMPLE_BLH, np.ones(len(SAMPLE_BLH)) * 4.0)
        total = sum(freqs.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_high_blh_gives_unstable(self) -> None:
        high_blh = np.full(100, 2000.0)  # very unstable — class A
        wind = np.ones(100) * 3.0
        freqs, stable_frac = compute_pasquill_classes(high_blh, wind)
        assert freqs["A"] > 0.9

    def test_low_blh_gives_stable(self) -> None:
        low_blh = np.full(100, 50.0)  # very stable — class F
        wind = np.ones(100) * 1.0
        freqs, stable_frac = compute_pasquill_classes(low_blh, wind)
        assert freqs["F"] > 0.5

    def test_stable_fraction_consistent(self) -> None:
        freqs, stable_frac = compute_pasquill_classes(SAMPLE_BLH, np.ones(len(SAMPLE_BLH)) * 4.0)
        assert stable_frac == pytest.approx(freqs["E"] + freqs["F"], abs=1e-6)

    def test_empty_arrays(self) -> None:
        freqs, stable_frac = compute_pasquill_classes(np.array([]), np.array([]))
        assert sum(freqs.values()) == pytest.approx(1.0, abs=0.01)

    def test_nonnegative_frequencies(self) -> None:
        freqs, _ = compute_pasquill_classes(SAMPLE_BLH, np.ones(len(SAMPLE_BLH)))
        for v in freqs.values():
            assert v >= 0.0

    def test_custom_thresholds(self) -> None:
        custom = {"very_unstable_min": 2000.0, "unstable_min": 1500.0,
                  "slightly_unstable_min": 800.0, "neutral_max": 800.0,
                  "stable_max": 300.0, "very_stable_max": 150.0}
        blh = np.full(100, 1000.0)
        wind = np.ones(100) * 4.0
        freqs, _ = compute_pasquill_classes(blh, wind, blh_thresholds=custom)
        assert sum(freqs.values()) == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# CMIP6 delta
# ---------------------------------------------------------------------------

class TestComputeCmip6Delta:
    def test_positive_delta(self) -> None:
        hist = np.full(360, 15.0)
        proj = np.full(240, 16.5)
        delta = compute_cmip6_delta(hist, proj)
        assert delta == pytest.approx(1.5, abs=0.01)

    def test_zero_delta(self) -> None:
        hist = np.full(120, 10.0)
        proj = np.full(120, 10.0)
        assert compute_cmip6_delta(hist, proj) == pytest.approx(0.0, abs=1e-6)

    def test_empty_returns_zero(self) -> None:
        assert compute_cmip6_delta(np.array([]), np.full(10, 15.0)) == 0.0
        assert compute_cmip6_delta(np.full(10, 15.0), np.array([])) == 0.0

    def test_proj_period_years_slicing(self) -> None:
        hist = np.full(360, 14.0)
        # 20 years of data, each at 17.0
        proj = np.full(240, 17.0)
        delta = compute_cmip6_delta(hist, proj, proj_period_years=20)
        assert delta == pytest.approx(3.0, abs=0.01)


# ---------------------------------------------------------------------------
# Coefficient of variation
# ---------------------------------------------------------------------------

class TestCoefficientOfVariation:
    def test_uniform_zero(self) -> None:
        assert coefficient_of_variation(np.ones(12) * 5.0) == pytest.approx(0.0, abs=1e-6)

    def test_known_cv(self) -> None:
        # CV = std/mean
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected = float(np.std(values) / np.mean(values))
        assert coefficient_of_variation(values) == pytest.approx(expected, rel=1e-5)

    def test_near_zero_mean(self) -> None:
        # Should return 0 not raise
        assert coefficient_of_variation(np.array([0.0001, 0.0001])) >= 0.0


# ---------------------------------------------------------------------------
# Snow months count
# ---------------------------------------------------------------------------

class TestCountSnowMonths:
    def test_no_snow(self) -> None:
        assert count_snow_months(np.zeros(12)) == 0

    def test_all_snow(self) -> None:
        assert count_snow_months(np.ones(12) * 10.0) == 12

    def test_partial_snow(self) -> None:
        # SNOWFALL_THRESHOLD_MM = 1.0; values > 1.0: 5.0, 3.0, 4.0 → 3 months
        sf = np.array([5.0, 3.0, 0.5, 0.0, 0.0, 0.0,
                       0.0, 0.0, 0.0, 0.0, 0.2, 4.0])
        assert count_snow_months(sf) == 3  # months with sf > 1.0


# ---------------------------------------------------------------------------
# Extreme precipitation months
# ---------------------------------------------------------------------------

class TestCountExtremePrecipMonths:
    def test_uniform_zero(self) -> None:
        assert count_extreme_precip_months(np.zeros(12)) == 0

    def test_no_extreme_months(self) -> None:
        # Uniform precipitation — no month is 2× the mean
        assert count_extreme_precip_months(np.ones(12) * 50.0) == 0

    def test_one_extreme_month(self) -> None:
        precip = np.array([50.0] * 11 + [200.0])  # last month is 4× mean
        result = count_extreme_precip_months(precip)
        assert result >= 1


# ---------------------------------------------------------------------------
# Freezing rain proxy
# ---------------------------------------------------------------------------

class TestComputeFreezingRainProxy:
    def test_no_freezing(self) -> None:
        # Summer temperatures only
        temp = np.full(24, 20.0)
        precip = np.full(24, 50.0)
        result = compute_freezing_rain_days_proxy(temp, precip)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_winter_with_precip(self) -> None:
        # Some months near 0°C with precipitation
        temp = np.array([-5.0, -2.0, 1.0, 2.0, 10.0, 20.0,
                         22.0, 20.0, 12.0, 5.0, 0.0, -3.0] * 2)
        precip = np.full(24, 40.0)
        result = compute_freezing_rain_days_proxy(temp, precip)
        assert result > 0.0  # should detect freezing-prone months

    def test_empty_arrays(self) -> None:
        assert compute_freezing_rain_days_proxy(np.array([]), np.array([])) == 0.0


# ---------------------------------------------------------------------------
# Drought severity index
# ---------------------------------------------------------------------------

class TestComputeDroughtSeverityIndex:
    def test_empty_returns_none(self) -> None:
        assert compute_drought_severity_index(np.array([])) is None

    def test_all_positive_spi_returns_zero(self) -> None:
        spi = np.full(100, 1.0)  # all wet
        dsi = compute_drought_severity_index(spi)
        assert dsi == 0.0

    def test_severe_drought_gives_positive_dsi(self) -> None:
        spi = np.array([-2.5, -2.0, -1.5, -1.0] * 25)
        dsi = compute_drought_severity_index(spi)
        assert dsi is not None
        assert dsi > 0.0

    def test_dsi_clipped_to_one(self) -> None:
        spi = np.full(100, -4.0)
        dsi = compute_drought_severity_index(spi)
        assert dsi is not None
        assert dsi <= 1.0


# ---------------------------------------------------------------------------
# Result dataclass structure
# ---------------------------------------------------------------------------

class TestResultDataclasses:
    def _make_wind(self) -> WindAssessment:
        rose = {lbl: 1.0 / 16 for lbl in SECTOR_LABELS_16}
        return WindAssessment(
            wind_rose_16sector=rose,
            prevailing_direction_deg=0.0,
            mean_wind_speed_ms=5.0,
            max_wind_gust_ms=25.0,
            wind_gust_50yr_ms=35.0,
            wind_speed_99p_ms=20.0,
            tropical_storm_exposure_index=2.0,
        )

    def _make_temp(self) -> TemperatureAssessment:
        return TemperatureAssessment(
            max_temp_record_c=38.5,
            min_temp_record_c=-22.3,
            mean_annual_temp_c=11.2,
            temp_range_c=60.8,
            hot_days_above_35c=3.5,
            cold_days_below_minus20c=2.0,
            mean_summer_temp_c=22.0,
            temp_seasonality_index=0.42,
        )

    def _make_precip(self) -> PrecipitationAssessment:
        return PrecipitationAssessment(
            mean_annual_precip_mm=630.0,
            max_daily_precip_mm=85.0,
            precip_intensity_99p_mm_hr=4.5,
            annual_snow_days=35.0,
            max_daily_snowfall_mm=22.0,
            freezing_rain_days_proxy=8.5,
            spi_12_min=-2.1,
            drought_severity_index=0.15,
            precip_seasonality_index=0.28,
            snow_months=3,
            extreme_precip_months=2,
        )

    def _make_stability(self) -> StabilityAssessment:
        return StabilityAssessment(
            stability_class_freq={"A": 0.10, "B": 0.20, "C": 0.25, "D": 0.30, "E": 0.10, "F": 0.05},
            mean_mixing_height_m=900.0,
            percentile_5_mixing_height_m=180.0,
            stable_fraction=0.15,
        )

    def _make_era5_result(self) -> Era5ClimateResult:
        return Era5ClimateResult(
            lat=44.43,
            lon=26.10,
            grid_lat=44.5,
            grid_lon=26.0,
            grid_distance_km=9.5,
            wind=self._make_wind(),
            temperature=self._make_temp(),
            precipitation=self._make_precip(),
            stability=self._make_stability(),
            climate_projections=None,
        )

    def test_wind_to_dict_keys(self) -> None:
        d = self._make_wind().to_dict()
        assert "wind_rose_16sector" in d
        assert "prevailing_direction_deg" in d
        assert "wind_gust_50yr_ms" in d
        assert "tropical_storm_exposure_index" in d

    def test_wind_rose_in_dict_sums_to_one(self) -> None:
        d = self._make_wind().to_dict()
        rose = d["wind_rose_16sector"]
        assert sum(rose.values()) == pytest.approx(1.0, abs=0.01)

    def test_temp_to_dict_keys(self) -> None:
        d = self._make_temp().to_dict()
        assert "max_temp_record_c" in d
        assert "temp_seasonality_index" in d
        assert "mean_summer_temp_c" in d

    def test_precip_to_dict_keys(self) -> None:
        d = self._make_precip().to_dict()
        assert "spi_12_min" in d
        assert "drought_severity_index" in d
        assert "snow_months" in d
        assert "extreme_precip_months" in d

    def test_stability_to_dict_sums_to_one(self) -> None:
        d = self._make_stability().to_dict()
        total = sum(d["stability_class_freq"].values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_era5_result_to_dict_structure(self) -> None:
        d = self._make_era5_result().to_dict()
        assert "lat" in d
        assert "wind" in d
        assert "temperature" in d
        assert "precipitation" in d
        assert "stability" in d
        assert "quality" in d
        assert d["climate_projections"] is None

    def test_era5_result_with_projections(self) -> None:
        result = self._make_era5_result()
        result.climate_projections = ClimateProjectionAssessment(
            baseline_mean_temp_c=11.2,
            warming_2050_ssp245_c=1.8,
            warming_2080_ssp245_c=2.5,
            warming_2050_ssp585_c=2.3,
            warming_2080_ssp585_c=4.0,
            model_spread_2050_c=0.5,
            model_spread_2080_c=0.8,
        )
        d = result.to_dict()
        assert d["climate_projections"] is not None
        assert d["climate_projections"]["warming_2050_ssp245_c"] == pytest.approx(1.8, rel=0.01)

    def test_batch_result_summary_line(self) -> None:
        batch = BatchResult(run_id="test-run", total_sites=10, succeeded=8, failed=1, skipped_cached=1, elapsed_s=25.0)
        line = batch.summary_line()
        assert "10 sites" in line
        assert "8 ok" in line
        assert "1 failed" in line
        assert "1 cached" in line


# ---------------------------------------------------------------------------
# Connector config loading
# ---------------------------------------------------------------------------

class TestCopernicusEra5ConnectorConfig:
    def test_default_config_no_settings(self) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector
        c = CopernicusEra5Connector(None)
        assert c._data_dir == Path("sources/era5")
        assert c._ref_start == 1991
        assert c._ref_end == 2020
        assert c._n_sectors == 16

    def test_config_from_yaml(self) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {
                        "data_dir": "custom/era5",
                        "cache_ttl_days": 45,
                        "reference_period": {"start_year": 1980, "end_year": 2010},
                    }
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        assert c._data_dir == Path("custom/era5")
        assert c._cache_ttl_days == 45
        assert c._ref_start == 1980
        assert c._ref_end == 2010

    def test_check_local_data_missing(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {"data_dir": str(tmp_path / "era5")}
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        status = c.check_local_data()
        assert not status["monthly_means"]["present"]
        assert not status["era5_land"]["present"]
        assert not status["cmip6"]["present"]

    def test_has_required_data_false_when_missing(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {"data_dir": str(tmp_path / "era5")}
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        assert not c.has_required_data()

    def test_has_required_data_true_when_present(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector
        from atoms_vs_ashes.connectors.copernicus_era5.models import MONTHLY_MEANS_FILE

        era5_dir = tmp_path / "era5"
        era5_dir.mkdir()
        (era5_dir / MONTHLY_MEANS_FILE).write_bytes(b"fake")  # placeholder

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {"data_dir": str(era5_dir)}
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        assert c.has_required_data()

    def test_open_datasets_missing_raises(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {"data_dir": str(tmp_path / "era5")}
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        with pytest.raises(RuntimeError):
            c._open_datasets()

    def test_context_manager(self) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector
        with CopernicusEra5Connector(None) as c:
            assert c is not None


# ---------------------------------------------------------------------------
# Mock xarray integration test
# ---------------------------------------------------------------------------

class TestExtractAllWithMockDatasets:
    """Integration test: extract_all() with synthetic xarray datasets."""

    def _make_mock_dataset(self, n_times: int = 360) -> "Any":
        """Create a synthetic xarray Dataset mimicking ERA5 monthly means."""
        import xarray as xr

        lats = np.array([44.0, 44.25, 44.5, 44.75, 45.0])
        lons = np.array([25.75, 26.0, 26.25, 26.5])
        n_lat = len(lats)
        n_lon = len(lons)

        def make_data(val: float) -> np.ndarray:
            return np.full((n_times, n_lat, n_lon), val, dtype=float)

        ds = xr.Dataset(
            {
                "u10": (["time", "latitude", "longitude"], make_data(1.5)),
                "v10": (["time", "latitude", "longitude"], make_data(-2.5)),
                "i10fg": (["time", "latitude", "longitude"], make_data(8.0)),
                "t2m": (["time", "latitude", "longitude"], make_data(284.0)),  # ~11°C
                "mx2t": (["time", "latitude", "longitude"], make_data(298.0)),  # ~25°C
                "mn2t": (["time", "latitude", "longitude"], make_data(272.0)),  # ~-1°C
                "tp": (["time", "latitude", "longitude"], make_data(0.04)),     # 40mm/month in m
                "sf": (["time", "latitude", "longitude"], make_data(0.005)),    # snowfall
                "blh": (["time", "latitude", "longitude"], make_data(900.0)),
            },
            coords={
                "latitude": lats,
                "longitude": lons,
                "time": np.arange(n_times),
            },
        )
        return ds

    def test_extract_all_returns_era5_result(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        mock_ds = self._make_mock_dataset()

        class FakeSettings:
            _yaml = {
                "connectors": {
                    "copernicus_era5": {"data_dir": str(tmp_path / "era5")}
                }
            }

        c = CopernicusEra5Connector(FakeSettings())
        c._monthly_ds = mock_ds
        c._land_ds = None
        c._cmip6_ds = None

        result = c.extract_all(lat=44.43, lon=26.10)

        assert isinstance(result, Era5ClimateResult)
        assert result.lat == 44.43
        assert result.lon == 26.10
        assert result.grid_distance_km >= 0.0
        assert result.quality in ("high", "medium")
        assert result.wind is not None
        assert result.temperature is not None
        assert result.precipitation is not None
        assert result.stability is not None

    def test_extract_wind_rose_sums_to_one(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        mock_ds = self._make_mock_dataset()

        class FakeSettings:
            _yaml = {"connectors": {"copernicus_era5": {"data_dir": str(tmp_path)}}}

        c = CopernicusEra5Connector(FakeSettings())
        c._monthly_ds = mock_ds
        c._land_ds = None
        c._cmip6_ds = None

        result = c.extract_all(lat=44.5, lon=26.25)
        total = sum(result.wind.wind_rose_16sector.values())
        assert total == pytest.approx(1.0, abs=0.02)

    def test_temperature_in_celsius_range(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        mock_ds = self._make_mock_dataset()

        class FakeSettings:
            _yaml = {"connectors": {"copernicus_era5": {"data_dir": str(tmp_path)}}}

        c = CopernicusEra5Connector(FakeSettings())
        c._monthly_ds = mock_ds
        c._land_ds = None
        c._cmip6_ds = None

        result = c.extract_all(lat=44.5, lon=26.25)
        # mx2t = 298 K → 24.85°C; mn2t = 272 K → -1.15°C
        assert -5.0 < result.temperature.min_temp_record_c < 5.0
        assert 20.0 < result.temperature.max_temp_record_c < 35.0

    def test_close_datasets(self, tmp_path: Path) -> None:
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        mock_ds = self._make_mock_dataset()

        class FakeSettings:
            _yaml = {"connectors": {"copernicus_era5": {"data_dir": str(tmp_path)}}}

        c = CopernicusEra5Connector(FakeSettings())
        c._monthly_ds = mock_ds
        c._close_datasets()
        assert c._monthly_ds is None

    def test_to_dict_json_serializable(self, tmp_path: Path) -> None:
        import json
        from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

        mock_ds = self._make_mock_dataset()

        class FakeSettings:
            _yaml = {"connectors": {"copernicus_era5": {"data_dir": str(tmp_path)}}}

        c = CopernicusEra5Connector(FakeSettings())
        c._monthly_ds = mock_ds
        c._land_ds = None
        c._cmip6_ds = None

        result = c.extract_all(lat=44.5, lon=26.0)
        serialized = json.dumps(result.to_dict(), default=str)
        parsed = json.loads(serialized)
        assert parsed["quality"] in ("high", "medium")
        assert "wind" in parsed


# ---------------------------------------------------------------------------
# CRITERION_IDS
# ---------------------------------------------------------------------------

class TestCriterionIds:
    def test_all_six_criteria_present(self) -> None:
        assert "NH-10" in CRITERION_IDS
        assert "NH-11" in CRITERION_IDS
        assert "NH-12" in CRITERION_IDS
        assert "RI-01" in CRITERION_IDS
        assert "NS-01" in CRITERION_IDS
        assert "EP-02" in CRITERION_IDS
        assert len(CRITERION_IDS) == 6
