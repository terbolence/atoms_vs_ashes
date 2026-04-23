# NH-11 — `mean_annual_precip_mm` backfill

_Generated 2026-04-20 18:54 UTC by `scripts/run_curation05_nh11_annual_precip.py`._

Source: parses `annual=<N>mm` out of `site_natural_hazards.nh11_comment` (written by the Copernicus ERA5 connector). Never overwrites a non-NULL value.

## Summary

- Rows scanned: **363**
- Rows with `nh11_comment` set: **363**
- Rows with `annual=<N>mm` parsed: **363**
- Rows with comment but no parseable annual value: **0** (likely NOAA-only / non-ERA5)
- Rows already populated before this run: **0**
- Rows written this run: **363**

## Plausibility flags

- < 100 mm/yr: **363** row(s)
- > 5000 mm/yr: **0** row(s)

> **WARNING — UPSTREAM CONNECTOR BUG SUSPECTED.** Effectively every row is below the low-outlier threshold. The Copernicus ERA5 connector (`src/atoms_vs_ashes/connectors/copernicus_era5/client.py` `_extract_precipitation`) treats the ERA5 monthly-means `total_precipitation` field as `m per month` and multiplies by 1000 to get mm. ERA5 monthly means are actually a daily-mean rate (m/day); the value must additionally be multiplied by the number of days in the month before summing across the year. This is **out of scope** for the current post-processing curation plan, but the values stored in the new `mean_annual_precip_mm` column are therefore ~30× too low. The column was still backfilled (faithful to the comment), and the bug should be fixed in a follow-up before the values are used for scoring.

### Low outliers (< 100 mm/yr) — first 30

| Country | Site | mm/yr |
|---|---|---|
| AL | Porto Romano Power Station | 41 |
| AT | Duernrohr power station | 25 |
| AT | Enns Power Station | 29 |
| AT | Mellach power station | 27 |
| AT | Riedersbach power station | 44 |
| AT | St Andrae power station | 33 |
| AT | Timelkam power station | 45 |
| AT | Voitsberg power station | 32 |
| AT | Zeltweg power station | 32 |
| BA | Banovici power station | 34 |
| BA | Bugojno Thermal Power Project | 42 |
| BA | Gacko Thermal Power Plant | 49 |
| BA | Glinica power station | 53 |
| BA | Kakanj Thermal Power Plant | 34 |
| BA | Kamengrad Thermal Power Plant | 39 |
| BA | Kongora Thermal Power Plant | 51 |
| BA | Miljevina power station | 34 |
| BA | Stanari Thermal Power Plant | 35 |
| BA | Tuzla Thermal Power Plant | 34 |
| BA | Ugljevik power station | 27 |
| BG | Bobov Dol power station | 17 |
| BG | Brikel power station | 20 |
| BG | Deven power station | 21 |
| BG | Lom Power Station | 18 |
| BG | Maritsa 3 power station | 21 |
| BG | Maritsa Iztok-1 power station | 20 |
| BG | Maritsa Iztok-2 power station | 22 |
| BG | Maritsa Iztok-3 power station | 20 |
| BG | Maritsa Iztok-4 power station | 20 |
| BG | Republika power station | 19 |
| … | _333 more rows omitted_ | |

## Sample writes

| Country | Site | mm/yr |
|---|---|---|
| AL | Porto Romano Power Station | 41 |
| AT | Duernrohr power station | 25 |
| AT | Enns Power Station | 29 |
| AT | Mellach power station | 27 |
| AT | Riedersbach power station | 44 |
| AT | St Andrae power station | 33 |
| AT | Timelkam power station | 45 |
| AT | Voitsberg power station | 32 |
| AT | Zeltweg power station | 32 |
| BA | Banovici power station | 34 |
