# NS-04 — `favourable_area_ha` derivation & review

_Generated 2026-04-20 18:57 UTC by `scripts/run_curation02_ns04_favourable_area.py`._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 2.

## Summary

- Rows scanned: **363**
- Rows already populated before this run: **0**
- Rows written this run: **363**

## Method counts

| Method | Count |
|---|---:|
| `comment_buildable_x_fav_pct` | 363 |

## Implausibility flags

Sites where `favourable_area_ha < 1.0` ha AND `sites.site_area_ha > 50.0` ha. These rows are flagged for manual review only — no auto-fix.

- Total flagged: **3**

| Country | Site | site_area_ha | favourable_area_ha | buildable (parsed) | fav % (parsed) | method | hypothesis |
|---|---|---:|---:|---:|---:|---|---|
| HR | Ploče power station | 238.7 | 0.00 | 0.0 | 34 | `comment_buildable_x_fav_pct` | `unknown` |
| MK | Bitola power station | 145.7 | 0.00 | 0.0 | 0 | `comment_buildable_x_fav_pct` | `unknown` |
| TR | Çan (18 Mart) power station | 81.2 | 0.00 | 0.0 | 0 | `comment_buildable_x_fav_pct` | `unknown` |

## Sample writes

| Country | Site | Method | favourable_area_ha |
|---|---|---|---:|
| AL | Porto Romano Power Station | `comment_buildable_x_fav_pct` | 42.12 |
| AT | Duernrohr power station | `comment_buildable_x_fav_pct` | 288.97 |
| AT | Enns Power Station | `comment_buildable_x_fav_pct` | 41.49 |
| AT | Mellach power station | `comment_buildable_x_fav_pct` | 142.13 |
| AT | Riedersbach power station | `comment_buildable_x_fav_pct` | 90.15 |
| AT | St Andrae power station | `comment_buildable_x_fav_pct` | 112.86 |
| AT | Timelkam power station | `comment_buildable_x_fav_pct` | 150.39 |
| AT | Voitsberg power station | `comment_buildable_x_fav_pct` | 22.13 |
| AT | Zeltweg power station | `comment_buildable_x_fav_pct` | 0.00 |
| BA | Banovici power station | `comment_buildable_x_fav_pct` | 6.16 |
