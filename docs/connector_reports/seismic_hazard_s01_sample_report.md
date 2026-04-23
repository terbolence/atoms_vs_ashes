# NH-01 Seismic Hazard — Connector Sample Report

**Connector slug:** `seismic_hazard`  
**Run date:** 2026-04-19  
**Criteria served:** NH-01 (Seismic ground motion)  
**Scope:** 363 sites across 20 countries  
**Sources:** EFEHR ESHM13 (map PGA), EFEHR ESHM20 (hazard curves + SA(T)), GEM Global v2023 (raster fallback)  

---

## Methodology

The seismic hazard connector assembles PGA, hazard curves, and spectral acceleration data from multiple sources with automatic fallback:

1. **PGA from EFEHR map endpoint** — queries the ESHM13 model (model ID 68) for PGA at 475-year and 2475-year return periods. The API returns a CSV grid within a bounding box around each site; the nearest grid node value is used. Grid resolution is ~0.1° (~10 km). ESHM20 map is non-functional as of 2026-04-13.

2. **Hazard curves from EFEHR curve endpoint** — queries the ESHM20 model (model ID 81) for the full PGA hazard curve (25 IML points vs. probability of exceedance over a 50-year investigation window). Returns NRML 0.3 XML format. Used to derive curve-based PGA when the map endpoint returns empty.

3. **SA(T) from per-period hazard curves** — for each of 6 spectral periods (0.10s, 0.20s, 0.30s, 0.50s, 1.00s, 2.00s), the `/curve` endpoint is queried with `imt=SA[period]`. The returned hazard curve is interpolated at PoE = 0.1 (475-year return period) via log-log interpolation to extract the spectral acceleration value. This workaround bypasses the broken `/spectra` (UHS) endpoint.

4. **GEM Global Seismic Hazard Map v2023 (fallback)** — a 3-arc-minute GeoTIFF raster of PGA at 475-year return period on reference rock (Vs30 = 760 m/s). Used when both the ESHM13 map and ESHM20 curve endpoints return no data (16 Ukrainian sites on the stable East European Craton). Provides PGA only (no 2475-year, no hazard curve, no SA(T)).

**Vs30 reference:** 760 m/s (rock site conditions) for all sources.  
**Investigation time:** 50 years for all hazard calculations.

---

## Metric Legend

| Metric | Unit | Derivation | Null means |
|--------|------|------------|------------|
| pga_475yr_g | g | PGA at 10% PoE in 50yr (≈475yr return period) from ESHM13 map nearest-grid-node, or ESHM20 curve interpolation, or GEM raster sampling | All three sources returned no data |
| pga_2475yr_g | g | PGA at 2% PoE in 50yr (≈2475yr return period) from ESHM13 map | GEM fallback used (only provides 475yr), or ESHM13 map returned empty for this return period |
| spectral_accel_json.hazard_curve | — | Full ESHM20 PGA hazard curve: 25 (IML, PoE) pairs over 50yr investigation time | ESHM20 curve endpoint returned empty for this location |
| spectral_accel_json.sa_values | g | SA(T) at 475yr for 6 periods, derived by interpolating per-period ESHM20 hazard curves at PoE = 0.1 | ESHM20 curve endpoint returned empty, or interpolation failed at curve tail |
| nh01_source | — | Source identifier: `efehr_eshm13`, `efehr_eshm20_curve`, or `gem_global_v2023` | — |
| nh01_quality | — | Quality grade (see below) | — |
| grid_distance_km | km | Haversine distance from site to nearest EFEHR grid node | GEM raster used (point-sampled, distance = 0) |

## Quality Grade Legend

| Grade | Meaning |
|-------|---------|
| high | PGA from EFEHR ESHM13 map endpoint; grid distance ≤ 15 km; value within plausible range (0–2 g) |
| medium | PGA from GEM global raster fallback (lower spatial resolution, ~5 km) or from ESHM20 curve interpolation (less precise than direct map values) |
| low | PGA from EFEHR but grid distance > 15 km, or hazard curve failed monotonicity validation, or PGA > 2 g |
| insufficient | No PGA obtainable from any source (none remain after this fix run) |

---

## Coverage Notes

- **22 sites** (16 UA + 4 UA western + 2 BY) are outside ESHM20 curve coverage — no hazard curves or SA(T) available. The 16 eastern UA sites use GEM raster fallback; the 4 western UA and 2 BY sites have ESHM13 map PGA but no curves.
- **UHS endpoint** (`/spectra`) remains non-functional for both ESHM13 and ESHM20 as of 2026-04-19. SA(T) is derived entirely from per-period `/curve` queries.
- **SA(2.00s)** returns null for a handful of very low-seismicity Polish sites where the 2-second spectral acceleration falls below the curve's minimum resolvable PoE.

---

## Summary

| Metric | Value |
|--------|-------|
| Total sites | 363 |
| Sites with PGA | 363 (100%) |
| Sites with SA(T) | 341 (93.9%) |
| Sites insufficient | 0 |
| PGA range | 0.000–0.564 g |
| Sources | efehr_eshm13 (347), gem_global_v2023 (16) |

---

## 1. Tekirdağ Malkara power station (TR)

| Field | Value |
|-------|-------|
| **Site ID** | `0ada7b2a-f928-4c21-b082-4c7345094245` |
| **Country** | TR |
| **Latitude** | 40.638726 |
| **Longitude** | 27.004295 |
| **PGA 475yr** | 0.56420 g |
| **PGA 2475yr** | 1.13274 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 4.7 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 1.000000e+00 |
| 0.003063 | 1.000000e+00 |
| 0.004401 | 9.999999e-01 |
| 0.006323 | 9.999976e-01 |
| 0.009086 | 9.999620e-01 |
| 0.013055 | 9.996255e-01 |
| 0.018759 | 9.974102e-01 |
| 0.026954 | 9.872712e-01 |
| 0.038730 | 9.552740e-01 |
| 0.055650 | 8.836321e-01 |
| 0.079963 | 7.652540e-01 |
| 0.114899 | 6.136807e-01 |
| 0.165096 | 4.539221e-01 |
| 0.237225 | 3.070297e-01 |
| 0.340866 | 1.855305e-01 |
| 0.489786 | 9.675563e-02 |
| 0.703768 | 4.201519e-02 |
| 1.011236 | 1.467915e-02 |
| 1.453032 | 3.954784e-03 |
| 2.087845 | 7.692574e-04 |
| 3.000000 | 9.423793e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 1.146338 |
| 0.20s | 1.357602 |
| 0.30s | 1.252258 |
| 0.50s | 0.924330 |
| 1.00s | 0.554739 |
| 2.00s | 0.247417 |

---

## 2. Porto Romano Power Station (AL)

| Field | Value |
|-------|-------|
| **Site ID** | `e6ecead0-54d1-41fe-8268-1253d0d7ef3e` |
| **Country** | AL |
| **Latitude** | 41.371141 |
| **Longitude** | 19.425201 |
| **PGA 475yr** | 0.39298 g |
| **PGA 2475yr** | 0.79056 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 4.8 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 1.000000e+00 |
| 0.003063 | 1.000000e+00 |
| 0.004401 | 9.999999e-01 |
| 0.006323 | 9.999968e-01 |
| 0.009086 | 9.999463e-01 |
| 0.013055 | 9.994699e-01 |
| 0.018759 | 9.964406e-01 |
| 0.026954 | 9.829485e-01 |
| 0.038730 | 9.408433e-01 |
| 0.055650 | 8.473392e-01 |
| 0.079963 | 6.954689e-01 |
| 0.114899 | 5.090573e-01 |
| 0.165096 | 3.294083e-01 |
| 0.237225 | 1.884558e-01 |
| 0.340866 | 9.559911e-02 |
| 0.489786 | 4.303429e-02 |
| 0.703768 | 1.709999e-02 |
| 1.011236 | 5.913522e-03 |
| 1.453032 | 1.730921e-03 |
| 2.087845 | 4.215384e-04 |
| 3.000000 | 7.772886e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.848893 |
| 0.20s | 0.828017 |
| 0.30s | 0.638942 |
| 0.50s | 0.392057 |
| 1.00s | 0.181904 |
| 2.00s | 0.068076 |

---

## 3. Oslomej power station (MK)

| Field | Value |
|-------|-------|
| **Site ID** | `756218bb-3f16-443e-b6c6-400cd0ce2f87` |
| **Country** | MK |
| **Latitude** | 41.582133 |
| **Longitude** | 21.000288 |
| **PGA 475yr** | 0.34558 g |
| **PGA 2475yr** | 0.72652 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 2.5 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 1.000000e+00 |
| 0.003063 | 9.999999e-01 |
| 0.004401 | 9.999974e-01 |
| 0.006323 | 9.999443e-01 |
| 0.009086 | 9.994056e-01 |
| 0.013055 | 9.958394e-01 |
| 0.018759 | 9.800847e-01 |
| 0.026954 | 9.332009e-01 |
| 0.038730 | 8.354709e-01 |
| 0.055650 | 6.864185e-01 |
| 0.079963 | 5.111424e-01 |
| 0.114899 | 3.439969e-01 |
| 0.165096 | 2.093773e-01 |
| 0.237225 | 1.151276e-01 |
| 0.340866 | 5.683953e-02 |
| 0.489786 | 2.492069e-02 |
| 0.703768 | 9.534243e-03 |
| 1.011236 | 3.116036e-03 |
| 1.453032 | 8.402672e-04 |
| 2.087845 | 1.774746e-04 |
| 3.000000 | 2.723507e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.645259 |
| 0.20s | 0.622968 |
| 0.30s | 0.476027 |
| 0.50s | 0.287853 |
| 1.00s | 0.130554 |
| 2.00s | 0.048807 |

---

## 4. Bar power station (ME)

| Field | Value |
|-------|-------|
| **Site ID** | `3795824b-cb76-48dd-a65c-764c757ddc76` |
| **Country** | ME |
| **Latitude** | 42.100000 |
| **Longitude** | 19.100000 |
| **PGA 475yr** | 0.28936 g |
| **PGA 2475yr** | 0.68879 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 1.5 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 9.999999e-01 |
| 0.003063 | 9.999984e-01 |
| 0.004401 | 9.999683e-01 |
| 0.006323 | 9.996564e-01 |
| 0.009086 | 9.974656e-01 |
| 0.013055 | 9.866170e-01 |
| 0.018759 | 9.505368e-01 |
| 0.026954 | 8.679292e-01 |
| 0.038730 | 7.324863e-01 |
| 0.055650 | 5.660678e-01 |
| 0.079963 | 4.045628e-01 |
| 0.114899 | 2.737460e-01 |
| 0.165096 | 1.797737e-01 |
| 0.237225 | 1.158096e-01 |
| 0.340866 | 7.214440e-02 |
| 0.489786 | 4.193104e-02 |
| 0.703768 | 2.174718e-02 |
| 1.011236 | 9.649605e-03 |
| 1.453032 | 3.528549e-03 |
| 2.087845 | 1.018115e-03 |
| 3.000000 | 2.063673e-04 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.639383 |
| 0.20s | 0.674658 |
| 0.30s | 0.547302 |
| 0.50s | 0.347325 |
| 1.00s | 0.166838 |
| 2.00s | 0.065095 |

---

## 5. Bacau CHP power station (RO)

| Field | Value |
|-------|-------|
| **Site ID** | `dac2a974-a2de-46c5-b581-03985a9ae7d0` |
| **Country** | RO |
| **Latitude** | 46.530524 |
| **Longitude** | 26.940874 |
| **PGA 475yr** | 0.28061 g |
| **PGA 2475yr** | 0.49719 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 4.6 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 1.000000e+00 |
| 0.003063 | 1.000000e+00 |
| 0.004401 | 1.000000e+00 |
| 0.006323 | 1.000000e+00 |
| 0.009086 | 9.999990e-01 |
| 0.013055 | 9.999713e-01 |
| 0.018759 | 9.995832e-01 |
| 0.026954 | 9.965467e-01 |
| 0.038730 | 9.821277e-01 |
| 0.055650 | 9.371400e-01 |
| 0.079963 | 8.389006e-01 |
| 0.114899 | 6.811712e-01 |
| 0.165096 | 4.876346e-01 |
| 0.237225 | 3.014424e-01 |
| 0.340866 | 1.585724e-01 |
| 0.489786 | 7.022367e-02 |
| 0.703768 | 2.579715e-02 |
| 1.011236 | 7.625872e-03 |
| 1.453032 | 1.689164e-03 |
| 2.087845 | 2.484409e-04 |
| 3.000000 | 2.019920e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.931715 |
| 0.20s | 1.007575 |
| 0.30s | 0.826396 |
| 0.50s | 0.611444 |
| 1.00s | 0.311067 |
| 2.00s | 0.106551 |

---

## 6. Trbovlje power station (SI)

| Field | Value |
|-------|-------|
| **Site ID** | `008a3366-6f56-4c1a-ac5d-6b0c75b7c7fd` |
| **Country** | SI |
| **Latitude** | 46.126132 |
| **Longitude** | 15.061808 |
| **PGA 475yr** | 0.26174 g |
| **PGA 2475yr** | 0.49753 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 3.3 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 9.999996e-01 |
| 0.003063 | 9.999948e-01 |
| 0.004401 | 9.999492e-01 |
| 0.006323 | 9.996186e-01 |
| 0.009086 | 9.977731e-01 |
| 0.013055 | 9.899644e-01 |
| 0.018759 | 9.653059e-01 |
| 0.026954 | 9.068334e-01 |
| 0.038730 | 8.008271e-01 |
| 0.055650 | 6.503957e-01 |
| 0.079963 | 4.788847e-01 |
| 0.114899 | 3.176327e-01 |
| 0.165096 | 1.895054e-01 |
| 0.237225 | 1.017160e-01 |
| 0.340866 | 4.902909e-02 |
| 0.489786 | 2.111082e-02 |
| 0.703768 | 8.033615e-03 |
| 1.011236 | 2.662512e-03 |
| 1.453032 | 7.473551e-04 |
| 2.087845 | 1.723291e-04 |
| 3.000000 | 3.018717e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.612294 |
| 0.20s | 0.563749 |
| 0.30s | 0.417764 |
| 0.50s | 0.244376 |
| 1.00s | 0.106062 |
| 2.00s | 0.037377 |

---

## 7. Glinica power station (BA)

| Field | Value |
|-------|-------|
| **Site ID** | `e2d645e3-c829-4aac-8f6f-d6a5507fd5fa` |
| **Country** | BA |
| **Latitude** | 43.333000 |
| **Longitude** | 17.800000 |
| **PGA 475yr** | 0.25822 g |
| **PGA 2475yr** | 0.51725 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 3.9 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 9.999995e-01 |
| 0.002131 | 9.999941e-01 |
| 0.003063 | 9.999492e-01 |
| 0.004401 | 9.996570e-01 |
| 0.006323 | 9.981316e-01 |
| 0.009086 | 9.918837e-01 |
| 0.013055 | 9.722819e-01 |
| 0.018759 | 9.251367e-01 |
| 0.026954 | 8.368589e-01 |
| 0.038730 | 7.054960e-01 |
| 0.055650 | 5.465774e-01 |
| 0.079963 | 3.865582e-01 |
| 0.114899 | 2.493483e-01 |
| 0.165096 | 1.469580e-01 |
| 0.237225 | 7.935025e-02 |
| 0.340866 | 3.934214e-02 |
| 0.489786 | 1.790492e-02 |
| 0.703768 | 7.404234e-03 |
| 1.011236 | 2.725340e-03 |
| 1.453032 | 8.658232e-04 |
| 2.087845 | 2.249826e-04 |
| 3.000000 | 4.307405e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.518959 |
| 0.20s | 0.514779 |
| 0.30s | 0.396689 |
| 0.50s | 0.244318 |
| 1.00s | 0.116062 |
| 2.00s | 0.044404 |

---

## 8. Ploče power station (HR)

| Field | Value |
|-------|-------|
| **Site ID** | `7af0e000-3d19-4e5e-b504-f74897f1510c` |
| **Country** | HR |
| **Latitude** | 43.050000 |
| **Longitude** | 17.433333 |
| **PGA 475yr** | 0.25798 g |
| **PGA 2475yr** | 0.55256 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 6.8 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 9.999999e-01 |
| 0.001483 | 9.999988e-01 |
| 0.002131 | 9.999873e-01 |
| 0.003063 | 9.998976e-01 |
| 0.004401 | 9.993483e-01 |
| 0.006323 | 9.966821e-01 |
| 0.009086 | 9.867867e-01 |
| 0.013055 | 9.591647e-01 |
| 0.018759 | 9.003471e-01 |
| 0.026954 | 8.022385e-01 |
| 0.038730 | 6.698813e-01 |
| 0.055650 | 5.205986e-01 |
| 0.079963 | 3.755058e-01 |
| 0.114899 | 2.509200e-01 |
| 0.165096 | 1.549664e-01 |
| 0.237225 | 8.834863e-02 |
| 0.340866 | 4.651910e-02 |
| 0.489786 | 2.259975e-02 |
| 0.703768 | 1.002373e-02 |
| 1.011236 | 3.964851e-03 |
| 1.453032 | 1.353080e-03 |
| 2.087845 | 3.787833e-04 |
| 3.000000 | 7.838483e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.536159 |
| 0.20s | 0.546178 |
| 0.30s | 0.431198 |
| 0.50s | 0.271109 |
| 1.00s | 0.129764 |
| 2.00s | 0.049760 |

---

## 9. Republika power station (BG)

| Field | Value |
|-------|-------|
| **Site ID** | `33a015dd-51e0-497e-b0d3-4b1b3f070438` |
| **Country** | BG |
| **Latitude** | 42.607124 |
| **Longitude** | 23.078699 |
| **PGA 475yr** | 0.22056 g |
| **PGA 2475yr** | 0.49645 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 0.8 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 1.000000e+00 |
| 0.002131 | 9.999999e-01 |
| 0.003063 | 9.999985e-01 |
| 0.004401 | 9.999732e-01 |
| 0.006323 | 9.996974e-01 |
| 0.009086 | 9.976467e-01 |
| 0.013055 | 9.873839e-01 |
| 0.018759 | 9.528411e-01 |
| 0.026954 | 8.728403e-01 |
| 0.038730 | 7.400510e-01 |
| 0.055650 | 5.734941e-01 |
| 0.079963 | 4.061484e-01 |
| 0.114899 | 2.640895e-01 |
| 0.165096 | 1.580316e-01 |
| 0.237225 | 8.678073e-02 |
| 0.340866 | 4.340379e-02 |
| 0.489786 | 1.958234e-02 |
| 0.703768 | 7.866098e-03 |
| 1.011236 | 2.762000e-03 |
| 1.453032 | 8.293954e-04 |
| 2.087845 | 2.038267e-04 |
| 3.000000 | 3.795931e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.541684 |
| 0.20s | 0.531221 |
| 0.30s | 0.405423 |
| 0.50s | 0.246766 |
| 1.00s | 0.114654 |
| 2.00s | 0.042792 |

---

## 10. Istok power station (XK)

| Field | Value |
|-------|-------|
| **Site ID** | `d9f32912-81f1-4b1c-a2b1-f04298217cec` |
| **Country** | XK |
| **Latitude** | 42.783333 |
| **Longitude** | 20.483333 |
| **PGA 475yr** | 0.21172 g |
| **PGA 2475yr** | 0.49262 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 1.9 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 9.999998e-01 |
| 0.002131 | 9.999930e-01 |
| 0.003063 | 9.998993e-01 |
| 0.004401 | 9.991021e-01 |
| 0.006323 | 9.943413e-01 |
| 0.009086 | 9.747554e-01 |
| 0.013055 | 9.197967e-01 |
| 0.018759 | 8.113635e-01 |
| 0.026954 | 6.553143e-01 |
| 0.038730 | 4.831662e-01 |
| 0.055650 | 3.293204e-01 |
| 0.079963 | 2.116777e-01 |
| 0.114899 | 1.306154e-01 |
| 0.165096 | 7.799172e-02 |
| 0.237225 | 4.481286e-02 |
| 0.340866 | 2.432416e-02 |
| 0.489786 | 1.213638e-02 |
| 0.703768 | 5.391981e-03 |
| 1.011236 | 2.060957e-03 |
| 1.453032 | 6.540589e-04 |
| 2.087845 | 1.635434e-04 |
| 3.000000 | 2.937782e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.341490 |
| 0.20s | 0.335424 |
| 0.30s | 0.253310 |
| 0.50s | 0.151603 |
| 1.00s | 0.070471 |
| 2.00s | 0.027933 |

---

## 11. Kolubara B power station (RS)

| Field | Value |
|-------|-------|
| **Site ID** | `d30af109-79cb-4ab5-a878-6f574b58116a` |
| **Country** | RS |
| **Latitude** | 44.467500 |
| **Longitude** | 20.284440 |
| **PGA 475yr** | 0.18351 g |
| **PGA 2475yr** | 0.39673 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 3.6 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 9.999999e-01 |
| 0.001032 | 9.999992e-01 |
| 0.001483 | 9.999893e-01 |
| 0.002131 | 9.998983e-01 |
| 0.003063 | 9.993039e-01 |
| 0.004401 | 9.964129e-01 |
| 0.006323 | 9.857254e-01 |
| 0.009086 | 9.555147e-01 |
| 0.013055 | 8.898262e-01 |
| 0.018759 | 7.786103e-01 |
| 0.026954 | 6.289720e-01 |
| 0.038730 | 4.648318e-01 |
| 0.055650 | 3.138012e-01 |
| 0.079963 | 1.940381e-01 |
| 0.114899 | 1.102642e-01 |
| 0.165096 | 5.762996e-02 |
| 0.237225 | 2.762751e-02 |
| 0.340866 | 1.206863e-02 |
| 0.489786 | 4.766504e-03 |
| 0.703768 | 1.684361e-03 |
| 1.011236 | 5.231946e-04 |
| 1.453032 | 1.401797e-04 |
| 2.087845 | 3.152469e-05 |
| 3.000000 | 5.620538e-06 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.295692 |
| 0.20s | 0.296699 |
| 0.30s | 0.226997 |
| 0.50s | 0.136542 |
| 1.00s | 0.061316 |
| 2.00s | 0.022810 |

---

## 12. Oroszlány power station (HU)

| Field | Value |
|-------|-------|
| **Site ID** | `651839d3-4e8f-4214-89aa-1f96ea221121` |
| **Country** | HU |
| **Latitude** | 47.501741 |
| **Longitude** | 18.271075 |
| **PGA 475yr** | 0.15625 g |
| **PGA 2475yr** | 0.34524 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 0.9 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 9.995361e-01 |
| 0.000718 | 9.987750e-01 |
| 0.001032 | 9.968978e-01 |
| 0.001483 | 9.925562e-01 |
| 0.002131 | 9.832351e-01 |
| 0.003063 | 9.648529e-01 |
| 0.004401 | 9.319255e-01 |
| 0.006323 | 8.788575e-01 |
| 0.009086 | 8.022596e-01 |
| 0.013055 | 7.030317e-01 |
| 0.018759 | 5.868424e-01 |
| 0.026954 | 4.630083e-01 |
| 0.038730 | 3.425317e-01 |
| 0.055650 | 2.357681e-01 |
| 0.079963 | 1.499602e-01 |
| 0.114899 | 8.765611e-02 |
| 0.165096 | 4.687452e-02 |
| 0.237225 | 2.283140e-02 |
| 0.340866 | 1.007687e-02 |
| 0.489786 | 4.005992e-03 |
| 0.703768 | 1.422551e-03 |
| 1.011236 | 4.458988e-04 |
| 1.453032 | 1.207134e-04 |
| 2.087845 | 2.759476e-05 |
| 3.000000 | 5.043284e-06 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.257201 |
| 0.20s | 0.256924 |
| 0.30s | 0.192247 |
| 0.50s | 0.111727 |
| 1.00s | 0.046139 |
| 2.00s | 0.015503 |

---

## 13. Zeltweg power station (AT)

| Field | Value |
|-------|-------|
| **Site ID** | `33d83e11-cfcd-47cb-be5e-82ca0fc352cc` |
| **Country** | AT |
| **Latitude** | 47.250000 |
| **Longitude** | 15.166667 |
| **PGA 475yr** | 0.13474 g |
| **PGA 2475yr** | 0.26521 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 5.7 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 9.999997e-01 |
| 0.000718 | 9.999962e-01 |
| 0.001032 | 9.999661e-01 |
| 0.001483 | 9.997652e-01 |
| 0.002131 | 9.987113e-01 |
| 0.003063 | 9.943731e-01 |
| 0.004401 | 9.804422e-01 |
| 0.006323 | 9.455949e-01 |
| 0.009086 | 8.772141e-01 |
| 0.013055 | 7.704948e-01 |
| 0.018759 | 6.351060e-01 |
| 0.026954 | 4.912400e-01 |
| 0.038730 | 3.586706e-01 |
| 0.055650 | 2.491380e-01 |
| 0.079963 | 1.655908e-01 |
| 0.114899 | 1.053041e-01 |
| 0.165096 | 6.350821e-02 |
| 0.237225 | 3.575816e-02 |
| 0.340866 | 1.847180e-02 |
| 0.489786 | 8.615809e-03 |
| 0.703768 | 3.571891e-03 |
| 1.011236 | 1.289907e-03 |
| 1.453032 | 3.984871e-04 |
| 2.087845 | 1.010155e-04 |
| 3.000000 | 2.016363e-05 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.288388 |
| 0.20s | 0.279627 |
| 0.30s | 0.210104 |
| 0.50s | 0.122391 |
| 1.00s | 0.052707 |
| 2.00s | 0.019024 |

---

## 14. Martinska power station (SK)

| Field | Value |
|-------|-------|
| **Site ID** | `06defca3-9105-437f-afd4-52f5603d9b8e` |
| **Country** | SK |
| **Latitude** | 49.059218 |
| **Longitude** | 18.907019 |
| **PGA 475yr** | 0.12501 g |
| **PGA 2475yr** | 0.30370 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 4.9 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 9.899580e-01 |
| 0.000718 | 9.788170e-01 |
| 0.001032 | 9.578397e-01 |
| 0.001483 | 9.218997e-01 |
| 0.002131 | 8.661696e-01 |
| 0.003063 | 7.880934e-01 |
| 0.004401 | 6.893850e-01 |
| 0.006323 | 5.768132e-01 |
| 0.009086 | 4.608060e-01 |
| 0.013055 | 3.521324e-01 |
| 0.018759 | 2.584793e-01 |
| 0.026954 | 1.829907e-01 |
| 0.038730 | 1.250610e-01 |
| 0.055650 | 8.221968e-02 |
| 0.079963 | 5.161782e-02 |
| 0.114899 | 3.065460e-02 |
| 0.165096 | 1.703732e-02 |
| 0.237225 | 8.762050e-03 |
| 0.340866 | 4.114779e-03 |
| 0.489786 | 1.736990e-03 |
| 0.703768 | 6.458365e-04 |
| 1.011236 | 2.070160e-04 |
| 1.453032 | 5.500074e-05 |
| 2.087845 | 1.159864e-05 |
| 3.000000 | 1.829179e-06 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.112577 |
| 0.20s | 0.113748 |
| 0.30s | 0.084217 |
| 0.50s | 0.048179 |
| 1.00s | 0.020016 |
| 2.00s | 0.006979 |

---

## 15. Vresova TPS power station (CZ)

| Field | Value |
|-------|-------|
| **Site ID** | `5f4ed23c-cea2-41ef-a3e8-ac863e1bdcd6` |
| **Country** | CZ |
| **Latitude** | 50.255816 |
| **Longitude** | 12.695936 |
| **PGA 475yr** | 0.09733 g |
| **PGA 2475yr** | 0.21635 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 5.0 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 7.966135e-01 |
| 0.000718 | 7.629696e-01 |
| 0.001032 | 7.230733e-01 |
| 0.001483 | 6.777291e-01 |
| 0.002131 | 6.280755e-01 |
| 0.003063 | 5.751290e-01 |
| 0.004401 | 5.193316e-01 |
| 0.006323 | 4.603657e-01 |
| 0.009086 | 3.976268e-01 |
| 0.013055 | 3.312332e-01 |
| 0.018759 | 2.630454e-01 |
| 0.026954 | 1.968857e-01 |
| 0.038730 | 1.375080e-01 |
| 0.055650 | 8.886252e-02 |
| 0.079963 | 5.274327e-02 |
| 0.114899 | 2.857619e-02 |
| 0.165096 | 1.406799e-02 |
| 0.237225 | 6.291708e-03 |
| 0.340866 | 2.572002e-03 |
| 0.489786 | 9.715549e-04 |
| 0.703768 | 3.417805e-04 |
| 1.011236 | 1.126177e-04 |
| 1.453032 | 3.375970e-05 |
| 2.087845 | 8.522989e-06 |
| 3.000000 | 1.681094e-06 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.120988 |
| 0.20s | 0.124413 |
| 0.30s | 0.092036 |
| 0.50s | 0.051073 |
| 1.00s | 0.018933 |
| 2.00s | 0.005622 |

---

## 16. Kuchurgan power station (MD)

| Field | Value |
|-------|-------|
| **Site ID** | `b3eb5dd2-98cf-40c4-b9ee-2a86fd066093` |
| **Country** | MD |
| **Latitude** | 46.629027 |
| **Longitude** | 29.939714 |
| **PGA 475yr** | 0.08468 g |
| **PGA 2475yr** | 0.15569 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 4.6 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 1.000000e+00 |
| 0.000718 | 1.000000e+00 |
| 0.001032 | 1.000000e+00 |
| 0.001483 | 9.999999e-01 |
| 0.002131 | 9.999958e-01 |
| 0.003063 | 9.999152e-01 |
| 0.004401 | 9.990634e-01 |
| 0.006323 | 9.937803e-01 |
| 0.009086 | 9.728699e-01 |
| 0.013055 | 9.162673e-01 |
| 0.018759 | 8.054442e-01 |
| 0.026954 | 6.412706e-01 |
| 0.038730 | 4.511001e-01 |
| 0.055650 | 2.751567e-01 |
| 0.079963 | 1.435996e-01 |
| 0.114899 | 6.347065e-02 |
| 0.165096 | 2.345277e-02 |
| 0.237225 | 7.062352e-03 |
| 0.340866 | 1.651102e-03 |
| 0.489786 | 2.888902e-04 |
| 0.703768 | 4.215639e-05 |
| 1.011236 | 7.010436e-06 |
| 1.453032 | 1.269799e-06 |
| 2.087845 | 1.918404e-07 |
| 3.000000 | 1.830299e-08 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.208488 |
| 0.20s | 0.226570 |
| 0.30s | 0.194330 |
| 0.50s | 0.157813 |
| 1.00s | 0.088205 |
| 2.00s | 0.031220 |

---

## 17. Bielsko-Biala power station (PL)

| Field | Value |
|-------|-------|
| **Site ID** | `73fe8f06-c53b-4877-9c1d-5caf3d8f2749` |
| **Country** | PL |
| **Latitude** | 49.811696 |
| **Longitude** | 19.052943 |
| **PGA 475yr** | 0.05162 g |
| **PGA 2475yr** | 0.13611 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 2.5 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 9.259582e-01 |
| 0.000718 | 8.851106e-01 |
| 0.001032 | 8.263674e-01 |
| 0.001483 | 7.479103e-01 |
| 0.002131 | 6.512228e-01 |
| 0.003063 | 5.418161e-01 |
| 0.004401 | 4.284932e-01 |
| 0.006323 | 3.211836e-01 |
| 0.009086 | 2.281244e-01 |
| 0.013055 | 1.538729e-01 |
| 0.018759 | 9.895901e-02 |
| 0.026954 | 6.097689e-02 |
| 0.038730 | 3.615273e-02 |
| 0.055650 | 2.067884e-02 |
| 0.079963 | 1.140855e-02 |
| 0.114899 | 6.050586e-03 |
| 0.165096 | 3.062570e-03 |
| 0.237225 | 1.464415e-03 |
| 0.340866 | 6.529803e-04 |
| 0.489786 | 2.675237e-04 |
| 0.703768 | 9.906061e-05 |
| 1.011236 | 3.238163e-05 |
| 1.453032 | 9.082083e-06 |
| 2.087845 | 2.100347e-06 |
| 3.000000 | 3.749639e-07 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.041317 |
| 0.20s | 0.046799 |
| 0.30s | 0.036823 |
| 0.50s | 0.022737 |
| 1.00s | 0.010208 |
| 2.00s | 0.003640 |

---

## 18. Burshtyn power station (UA)

| Field | Value |
|-------|-------|
| **Site ID** | `c47eb6a3-49c1-4879-95b6-9bcd53b7af04` |
| **Country** | UA |
| **Latitude** | 49.210383 |
| **Longitude** | 24.666536 |
| **PGA 475yr** | 0.03375 g |
| **PGA 2475yr** | 0.12358 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; UHS: unavailable (spectra endpoint non-functional); Grid distance: 1.6 km |
| **Fetched** | 2026-04-19 01:14 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** Not available (site outside ESHM20 coverage)

**Spectral accelerations:** Not available (no ESHM20 curve coverage for this location)

---

## 19. Kurzeme power station (LV)

| Field | Value |
|-------|-------|
| **Site ID** | `1a5b8f8f-f4be-4514-8738-755d25e19b41` |
| **Country** | LV |
| **Latitude** | 57.409408 |
| **Longitude** | 21.594695 |
| **PGA 475yr** | 0.01827 g |
| **PGA 2475yr** | 0.06793 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; Hazard curve: 25 IML points; SA(T) from curves: 6 periods; Grid distance: 1.3 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** 25 IML points, investigation time = 50.0 yr

| IML (g) | PoE (50yr) |
|---------|------------|
| 0.000500 | 6.277283e-01 |
| 0.000718 | 5.736647e-01 |
| 0.001032 | 5.116315e-01 |
| 0.001483 | 4.441507e-01 |
| 0.002131 | 3.744887e-01 |
| 0.003063 | 3.061829e-01 |
| 0.004401 | 2.425025e-01 |
| 0.006323 | 1.860014e-01 |
| 0.009086 | 1.382055e-01 |
| 0.013055 | 9.957102e-02 |
| 0.018759 | 6.964035e-02 |
| 0.026954 | 4.734104e-02 |
| 0.038730 | 3.130285e-02 |
| 0.055650 | 2.013168e-02 |
| 0.079963 | 1.257362e-02 |
| 0.114899 | 7.607102e-03 |
| 0.165096 | 4.438745e-03 |
| 0.237225 | 2.485235e-03 |
| 0.340866 | 1.326924e-03 |
| 0.489786 | 6.710514e-04 |
| 0.703768 | 3.191286e-04 |
| 1.011236 | 1.416192e-04 |
| 1.453032 | 5.811622e-05 |
| 2.087845 | 2.182108e-05 |
| 3.000000 | 7.410853e-06 |

**Spectral accelerations SA(T) at 475yr (PoE = 0.1 / 50yr):**

| Period | SA (g) |
|--------|--------|
| 0.10s | 0.035545 |
| 0.20s | 0.025578 |
| 0.30s | 0.016437 |
| 0.50s | 0.008669 |
| 1.00s | 0.002930 |
| 2.00s | 0.000820 |

---

## 20. Zelwa power station (BY)

| Field | Value |
|-------|-------|
| **Site ID** | `fac3d0b5-36a5-48ae-8494-f2f08e4342f4` |
| **Country** | BY |
| **Latitude** | 53.150000 |
| **Longitude** | 24.816700 |
| **PGA 475yr** | 0.00433 g |
| **PGA 2475yr** | 0.01813 g |
| **Source** | efehr_eshm13 |
| **Quality** | high |
| **Comment** | Model: ESHM13; UHS: unavailable (spectra endpoint non-functional); Grid distance: 6.0 km |
| **Fetched** | 2026-04-19 01:13 UTC |
| **Run ID** | `20260418T221335_7b59a623` |

**Hazard curve:** Not available (site outside ESHM20 coverage)

**Spectral accelerations:** Not available (no ESHM20 curve coverage for this location)

---
