# NH-06 — bearing capacity audit (read-only)

_Generated 2026-04-20 18:58 UTC by `scripts/run_curation04_bearing_capacity_audit.py`._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 4.

## Source

`src/atoms_vs_ashes/connectors/soilgrids/models.py::estimate_bearing_capacity`
uses a USDA-texture-class lookup table (base 50–200 kPa) scaled by `bulk_density / 1.5` and clamped to ×0.6–×1.5. With 11 entries the expected output band is ~30–300 kPa.

## BEARING_CAPACITY_TABLE (base values)

| Soil class | Base (kPa) |
|---|---:|
| clay | 75 |
| clay_loam | 100 |
| loam | 100 |
| loamy_sand | 150 |
| sand | 200 |
| sandy_clay | 100 |
| sandy_clay_loam | 125 |
| sandy_loam | 150 |
| silt | 50 |
| silt_loam | 75 |
| silty_clay | 75 |
| silty_clay_loam | 100 |

## Summary

- Rows scanned: **363**
- Rows with `bearing_capacity_kpa` set: **310**
- Rows with non-NULL value but NULL `soil_type`: **0**
- Low outliers (< 30 kPa): **0**
- High outliers (> 300 kPa): **0**

## Per-soil distribution

| Soil class | Count | min | median | mean | max |
|---|---:|---:|---:|---:|---:|
| `'clay'` | 10 | 62.0 | 66.8 | 65.9 | 69.5 |
| `'clay_loam'` | 116 | 73.3 | 88.7 | 87.9 | 95.3 |
| `'loam'` | 87 | 60.0 | 82.7 | 83.1 | 97.3 |
| `'loamy_sand'` | 10 | 106.0 | 117.0 | 117.8 | 133.0 |
| `'sandy_clay_loam'` | 3 | 105.8 | 109.2 | 108.1 | 109.2 |
| `'sandy_loam'` | 15 | 97.0 | 118.0 | 117.1 | 131.0 |
| `'silt_loam'` | 17 | 53.5 | 61.5 | 60.8 | 63.5 |
| `'silty_clay'` | 4 | 65.5 | 66.5 | 66.6 | 68.0 |
| `'silty_clay_loam'` | 48 | 71.3 | 85.3 | 85.4 | 96.0 |

## Verdict

All values fall within the expected 30–300 kPa Terzaghi-style screening band, every value has a matching `soil_type`, and the per-class medians line up with the lookup table. Apparent low values (60–90 kPa) reflect clay/silty-clay-dominated textures, which are correct for the methodology. **No connector change needed.**
