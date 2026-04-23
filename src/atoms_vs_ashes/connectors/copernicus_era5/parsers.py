# man_hours: 3.0
"""Pure computation functions for S-04 Copernicus CDS/ERA5 connector.

No I/O, no network calls, no database imports. All functions are
fully testable from synthetic data. Implements:

  - Wind rose computation (u/v → 16-sector frequencies)
  - GEV distribution fitting (annual maxima → N-year return period)
  - SPI-12 computation (McKee et al. 1993 gamma-distribution approach)
  - Pasquill-Gifford stability class estimation (BLH + wind proxy)
  - CMIP6 temperature delta computation
  - Nearest grid cell search with distance computation
  - Coefficient of variation and seasonality helpers
  - Freezing rain proxy computation

LL-011 applies: implement a generic _flat_index for JSON-stat, but
here we focus on xarray dataset queries (nearest-cell selection) which
are handled by the client.
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np

from atoms_vs_ashes.connectors.copernicus_era5.models import (
    MIN_ANNUAL_MAXIMA,
    SECTOR_LABELS_16,
    SNOWFALL_THRESHOLD_MM,
    EXTREME_PRECIP_FACTOR,
    HOT_THRESHOLD_C,
    COLD_THRESHOLD_C,
    SPI_ZERO_MONTH_FILL,
)

# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

_EARTH_R_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two lat/lon points in km."""
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
    return 2.0 * _EARTH_R_KM * math.asin(math.sqrt(a))


def nearest_grid_indices(
    lats: np.ndarray,
    lons: np.ndarray,
    lat: float,
    lon: float,
) -> tuple[int, int, float, float, float]:
    """Find nearest grid cell for a (lat, lon) point.

    Parameters
    ----------
    lats : 1-D array of grid latitudes (ascending or descending)
    lons : 1-D array of grid longitudes
    lat, lon : site coordinates

    Returns
    -------
    (lat_idx, lon_idx, grid_lat, grid_lon, distance_km)
    """
    lat_idx = int(np.argmin(np.abs(lats - lat)))
    lon_idx = int(np.argmin(np.abs(lons - lon)))
    grid_lat = float(lats[lat_idx])
    grid_lon = float(lons[lon_idx])
    dist_km = haversine_km(lat, lon, grid_lat, grid_lon)
    return lat_idx, lon_idx, grid_lat, grid_lon, dist_km


# ---------------------------------------------------------------------------
# Wind rose
# ---------------------------------------------------------------------------

def compute_wind_rose(
    u_ms: np.ndarray,
    v_ms: np.ndarray,
    n_sectors: int = 16,
) -> tuple[dict[str, float], float, float]:
    """Compute wind rose from u/v component arrays.

    Convention: u is eastward, v is northward wind component.
    Wind direction = direction FROM which wind blows (meteorological).

    Parameters
    ----------
    u_ms, v_ms : arrays of wind components (any length, matched)
    n_sectors : number of sectors (16 = 22.5° each)

    Returns
    -------
    (sector_freq_dict, prevailing_direction_deg, mean_wind_speed_ms)
    where sector_freq_dict values sum to 1.0 (±0.01).
    """
    if len(u_ms) == 0 or len(v_ms) == 0:
        sector_freq = {lbl: 1.0 / n_sectors for lbl in SECTOR_LABELS_16[:n_sectors]}
        return sector_freq, 0.0, 0.0

    # Wind direction FROM: atan2(-u, -v) gives direction FROM in radians
    # 0 = North, clockwise positive (standard meteorological convention)
    direction_rad = np.arctan2(-u_ms, -v_ms)
    direction_deg = (np.degrees(direction_rad) + 360.0) % 360.0

    speed = np.sqrt(u_ms ** 2 + v_ms ** 2)
    mean_speed = float(np.mean(speed))

    # Bin into sectors
    sector_width = 360.0 / n_sectors
    # Rotate by half sector so bins are centred on sector label directions
    bins = np.arange(n_sectors + 1) * sector_width - sector_width / 2
    bins[0] = 0.0  # collapse near-0° with near-360°

    counts, _ = np.histogram(direction_deg, bins=np.linspace(0, 360, n_sectors + 1))

    labels = SECTOR_LABELS_16[:n_sectors]
    total = max(counts.sum(), 1)
    freqs = counts / total

    # Normalise in case of floating-point drift
    freqs = freqs / freqs.sum()

    sector_freq = {lbl: float(freqs[i]) for i, lbl in enumerate(labels)}

    # Prevailing direction = centre of most-common sector
    dominant_sector_idx = int(np.argmax(counts))
    prevailing_deg = dominant_sector_idx * sector_width
    # Adjust: histogram bins start at 0° (North), clockwise
    prevailing_deg = (prevailing_deg + 360.0) % 360.0

    return sector_freq, prevailing_deg, mean_speed


# ---------------------------------------------------------------------------
# GEV distribution fitting
# ---------------------------------------------------------------------------

def compute_gev_return_period(
    annual_maxima: np.ndarray,
    return_period: int = 50,
) -> tuple[float | None, str]:
    """Fit GEV distribution to annual maxima and compute return period value.

    Uses scipy.stats.genextreme (Generalised Extreme Value distribution),
    which covers Gumbel (shape=0), Fréchet (shape<0), Weibull (shape>0).

    Parameters
    ----------
    annual_maxima : 1-D array of annual maximum values (e.g., wind gusts in m/s)
    return_period : return period in years (default 50)

    Returns
    -------
    (return_value, fit_quality)
    where fit_quality is "ok" or "fallback_percentile".
    Fallback if data too short, GEV fit fails, or fit produces implausible values.
    """
    try:
        from scipy import stats as scipy_stats
    except ImportError:
        return _empirical_percentile_fallback(annual_maxima, return_period)

    data = np.asarray(annual_maxima, dtype=float)
    data = data[np.isfinite(data)]

    if len(data) < MIN_ANNUAL_MAXIMA:
        return _empirical_percentile_fallback(data, return_period)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shape, loc, scale = scipy_stats.genextreme.fit(data)

        # Compute return level: T-year return period → exceedance prob = 1/T
        p_exceed = 1.0 / return_period
        return_level = scipy_stats.genextreme.ppf(1.0 - p_exceed, shape, loc=loc, scale=scale)

        # Plausibility check: return level should be > max observed and < 5× max
        if not np.isfinite(return_level):
            return _empirical_percentile_fallback(data, return_period)
        if return_level < float(data.max()) * 0.5:
            # Implausibly low — probably shape parameter issue
            return _empirical_percentile_fallback(data, return_period)

        return float(return_level), "ok"

    except Exception:
        return _empirical_percentile_fallback(data, return_period)


def _empirical_percentile_fallback(
    data: np.ndarray,
    return_period: int,
) -> tuple[float | None, str]:
    """Return empirical percentile as fallback when GEV fit is unavailable."""
    if len(data) == 0:
        return None, "fallback_percentile"
    percentile = max(0.0, min(99.9, (1.0 - 1.0 / return_period) * 100.0))
    return float(np.percentile(data, percentile)), "fallback_percentile"


# ---------------------------------------------------------------------------
# SPI — Standardized Precipitation Index
# ---------------------------------------------------------------------------

def compute_spi(
    monthly_precip_mm: np.ndarray,
    window: int = 12,
) -> np.ndarray:
    """Compute SPI using gamma distribution (McKee et al. 1993).

    Parameters
    ----------
    monthly_precip_mm : array of monthly precipitation totals (mm)
                        length should be multiple of 12 for meaningful SPI
    window : accumulation window in months (default 12 for SPI-12)

    Returns
    -------
    SPI values (same length as input, first `window-1` values are NaN).
    Typical range: -4 (extreme drought) to +4 (extremely wet).
    """
    try:
        from scipy import stats as scipy_stats
    except ImportError:
        return np.full(len(monthly_precip_mm), np.nan)

    data = np.asarray(monthly_precip_mm, dtype=float)
    n = len(data)

    if n < window:
        return np.full(n, np.nan)

    # Compute rolling sums
    rolling = np.full(n, np.nan)
    for i in range(window - 1, n):
        rolling[i] = float(np.sum(data[i - window + 1: i + 1]))

    spi = np.full(n, np.nan)

    for i in range(window - 1, n):
        val = rolling[i]
        if not np.isfinite(val) or val < 0:
            spi[i] = np.nan
            continue

        # Gather same calendar month's rolling values for distribution fitting
        month_idx = i % 12
        same_month_vals = [
            rolling[j] for j in range(month_idx + window - 1, n, 12)
            if j <= i and np.isfinite(rolling[j])
        ]
        if len(same_month_vals) < 4:
            # Not enough data for distribution fitting — use all available
            same_month_vals = rolling[window - 1: i + 1]
            same_month_vals = same_month_vals[np.isfinite(same_month_vals)]

        same_month_vals = np.array(same_month_vals, dtype=float)
        same_month_vals = same_month_vals[same_month_vals >= 0]

        if len(same_month_vals) < 4:
            spi[i] = np.nan
            continue

        # Handle zero-precip months
        n_zero = float(np.sum(same_month_vals == 0))
        n_total = float(len(same_month_vals))
        prob_zero = n_zero / n_total

        if val == 0.0:
            # Map zero precip to a very low SPI
            spi[i] = scipy_stats.norm.ppf(prob_zero * 0.5 + 1e-6)
            continue

        # Fit gamma distribution to non-zero values
        nonzero = same_month_vals[same_month_vals > 0]
        if len(nonzero) < 3:
            spi[i] = SPI_ZERO_MONTH_FILL
            continue

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                alpha, loc, beta = scipy_stats.gamma.fit(nonzero, floc=0)

            # CDF of gamma at current value
            p_nonzero = scipy_stats.gamma.cdf(val, alpha, loc=loc, scale=beta)
            # Mixture: P(X ≤ x) = prob_zero + (1 - prob_zero) * F_gamma(x)
            p_total = prob_zero + (1.0 - prob_zero) * p_nonzero

            # Clip to avoid ±inf from norm.ppf
            p_total = max(1e-6, min(1 - 1e-6, p_total))
            spi[i] = scipy_stats.norm.ppf(p_total)
        except Exception:
            spi[i] = np.nan

    return spi


# ---------------------------------------------------------------------------
# Pasquill-Gifford stability classes (BLH proxy)
# ---------------------------------------------------------------------------

def compute_pasquill_classes(
    blh_m: np.ndarray,
    wind_speed_ms: np.ndarray,
    blh_thresholds: dict[str, float] | None = None,
) -> tuple[dict[str, float], float]:
    """Estimate Pasquill-Gifford stability classes from BLH and wind speed.

    This is a screening-grade proxy: full Pasquill classification requires
    hourly surface observations (solar radiation, cloud cover). BLH from
    ERA5 captures convective instability well but underestimates stable
    stratification. This proxy is appropriate for Stage 1-2 siting.

    Parameters
    ----------
    blh_m : array of boundary layer heights (m), monthly or hourly
    wind_speed_ms : array of wind speeds (m/s), same length as blh_m
    blh_thresholds : optional dict with custom BLH class thresholds

    Returns
    -------
    (class_freq_dict, stable_fraction)
    where class_freq_dict has keys A-F summing to 1.0.
    """
    defaults = {
        "very_unstable_min": 1500.0,   # class A
        "unstable_min": 1000.0,        # class B
        "slightly_unstable_min": 500.0, # class C
        "neutral_max": 500.0,          # class D
        "stable_max": 200.0,           # class E
        "very_stable_max": 100.0,      # class F
    }
    if blh_thresholds:
        defaults.update(blh_thresholds)
    thr = defaults

    blh = np.asarray(blh_m, dtype=float)
    wind = np.asarray(wind_speed_ms, dtype=float)

    if len(blh) == 0:
        return {cls: 1.0 / 6 for cls in ("A", "B", "C", "D", "E", "F")}, 0.25

    counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    n = len(blh)
    ws = wind if len(wind) == n else np.ones(n) * 4.0

    for h, w in zip(blh, ws):
        if not np.isfinite(h):
            counts["D"] += 1
        elif h >= thr["very_unstable_min"]:
            counts["A"] += 1
        elif h >= thr["unstable_min"]:
            counts["B"] += 1
        elif h >= thr["slightly_unstable_min"]:
            counts["C"] += 1
        elif w >= 5.0:
            # Neutral with moderate wind
            counts["D"] += 1
        elif h >= thr["very_stable_max"]:
            counts["E"] += 1
        else:
            counts["F"] += 1

    total = max(sum(counts.values()), 1)
    freqs = {cls: counts[cls] / total for cls in counts}

    # Normalise
    total_freq = sum(freqs.values())
    if total_freq > 0:
        freqs = {cls: v / total_freq for cls, v in freqs.items()}

    stable_fraction = freqs.get("E", 0.0) + freqs.get("F", 0.0)

    return freqs, stable_fraction


# ---------------------------------------------------------------------------
# CMIP6 temperature delta
# ---------------------------------------------------------------------------

def compute_cmip6_delta(
    hist_temps: np.ndarray,
    proj_temps: np.ndarray,
    proj_period_years: int | None = None,
) -> float:
    """Compute temperature change (ΔT in °C) between projection and historical baseline.

    Parameters
    ----------
    hist_temps : baseline temperature values (K or °C, monthly or annual)
    proj_temps : projection period temperature values (same units)
    proj_period_years : number of years to use from end of proj_temps (None = all)

    Returns
    -------
    delta_T in the same units as input
    """
    hist = np.asarray(hist_temps, dtype=float)
    proj = np.asarray(proj_temps, dtype=float)

    hist = hist[np.isfinite(hist)]
    proj = proj[np.isfinite(proj)]

    if proj_period_years and len(proj) > proj_period_years * 12:
        proj = proj[-(proj_period_years * 12):]
    elif proj_period_years and len(proj) > proj_period_years:
        proj = proj[-proj_period_years:]

    if len(hist) == 0 or len(proj) == 0:
        return 0.0

    return float(np.mean(proj) - np.mean(hist))


# ---------------------------------------------------------------------------
# Precipitation / temperature seasonality helpers
# ---------------------------------------------------------------------------

def coefficient_of_variation(values: np.ndarray) -> float:
    """Compute coefficient of variation (std / mean). Returns 0 if mean ≈ 0."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return 0.0
    mean = float(np.mean(v))
    if abs(mean) < 1e-9:
        return 0.0
    return float(np.std(v) / mean)


def count_snow_months(
    monthly_snowfall_mean_mm: np.ndarray,
    threshold_mm: float = SNOWFALL_THRESHOLD_MM,
) -> int:
    """Count calendar months where mean snowfall exceeds threshold."""
    snow = np.asarray(monthly_snowfall_mean_mm, dtype=float)
    return int(np.sum(snow > threshold_mm))


def count_extreme_precip_months(
    monthly_precip_mean_mm: np.ndarray,
    factor: float = EXTREME_PRECIP_FACTOR,
) -> int:
    """Count months where mean precipitation exceeds factor × annual mean/12."""
    precip = np.asarray(monthly_precip_mean_mm, dtype=float)
    if len(precip) == 0:
        return 0
    annual_mean_month = float(np.mean(precip))
    return int(np.sum(precip > factor * annual_mean_month))


def count_threshold_days_from_monthly(
    monthly_max_c: np.ndarray,
    threshold_c: float,
    above: bool = True,
) -> float:
    """Estimate average annual days above/below a temperature threshold.

    Uses monthly maximum/minimum temperature means as a proxy.
    ERA5 monthly means are a rough proxy — actual daily threshold counts
    require hourly data.
    """
    temps = np.asarray(monthly_max_c, dtype=float)
    # Each monthly value represents ~30.4 days
    days_per_month = 30.4
    if above:
        fraction = np.maximum(0.0, np.minimum(1.0, (temps - threshold_c) / 10.0))
    else:
        fraction = np.maximum(0.0, np.minimum(1.0, (threshold_c - temps) / 10.0))
    return float(np.mean(fraction) * days_per_month * 12.0)


# ---------------------------------------------------------------------------
# Freezing rain proxy
# ---------------------------------------------------------------------------

def compute_freezing_rain_days_proxy(
    monthly_temp_c: np.ndarray,
    monthly_precip_mm: np.ndarray,
    freeze_threshold_c: float = 0.0,
) -> float:
    """Estimate average annual days with potential freezing precipitation.

    Proxy: months where mean temperature is near the freezing point (±3°C)
    and precipitation occurs. This identifies times when precipitation could
    fall as freezing rain rather than snow or liquid rain.

    Returns an estimated annual day count.
    """
    temp = np.asarray(monthly_temp_c, dtype=float)
    precip = np.asarray(monthly_precip_mm, dtype=float)

    if len(temp) == 0 or len(precip) == 0:
        return 0.0

    n = min(len(temp), len(precip))
    temp = temp[:n]
    precip = precip[:n]

    # Months where temp is near freezing and precip occurs
    near_freeze = (temp >= freeze_threshold_c - 3.0) & (temp <= freeze_threshold_c + 3.0)
    has_precip = precip > 0.5

    freeze_months = np.sum(near_freeze & has_precip)

    # Each qualifying month contributes a fraction of days
    # Approximate: assume half the month has precip in qualifying months
    days_per_month = 30.4 / 2.0
    return float(freeze_months / max(len(temp) / 12.0, 1.0) * days_per_month)


# ---------------------------------------------------------------------------
# Drought severity index
# ---------------------------------------------------------------------------

def compute_drought_severity_index(spi_series: np.ndarray) -> float | None:
    """Compute a normalized drought severity index from SPI series.

    Returns a value between 0 (no drought) and 1 (severe persistent drought),
    based on the frequency and intensity of drought months (SPI < -1).
    """
    spi = np.asarray(spi_series, dtype=float)
    spi = spi[np.isfinite(spi)]

    if len(spi) == 0:
        return None

    # Drought months = SPI < -1.0
    drought_mask = spi < -1.0
    if not any(drought_mask):
        return 0.0

    drought_freq = float(np.mean(drought_mask))
    drought_intensity = float(np.mean(-spi[drought_mask]))  # positive = worse

    # Combined index: frequency × intensity / 3.0 (normalise so max ~1.0)
    dsi = drought_freq * drought_intensity / 3.0
    return float(min(1.0, dsi))
