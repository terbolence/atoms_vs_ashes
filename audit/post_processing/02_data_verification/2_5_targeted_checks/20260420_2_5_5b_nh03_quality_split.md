# NH-03 — quality / source column split

_Generated 2026-04-20 18:55 UTC by `scripts/run_curation03_nh03_quality_split.py`._

Methodology: `docs/post_processing/data_curation_methodology.md`, Task 3.

## Summary

- Rows scanned: **363**
- Rows whose `nh03_quality` was a provenance tag and got rewritten (value moved to `nh03_source`, quality recomputed): **363**
- Rows already in the new contract (clean quality + non-NULL source): **0**
- Rows with clean quality but no source — source inferred from comment if possible: **0**
- Rows with unknown `nh03_quality` value (left untouched): **0**

## `nh03_quality` distribution — before vs. after

| Value | Before | After |
|---|---:|---:|
| `'medium'` | 0 | 354 |
| `'no_data'` | 0 | 9 |
| `'zhu_global_1km'` | 363 | 0 |

## `nh03_source` distribution — after

| Value | Count |
|---|---:|
| `'zhu_global_1km'` | 363 |

## Sample rewrites (first 15)

| Country | Site | quality (old → new) | source (new) |
|---|---|---|---|
| AL | Porto Romano Power Station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Duernrohr power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Enns Power Station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Mellach power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Riedersbach power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | St Andrae power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Timelkam power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Voitsberg power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| AT | Zeltweg power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Banovici power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Bugojno Thermal Power Project | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Gacko Thermal Power Plant | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Glinica power station | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Kakanj Thermal Power Plant | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
| BA | Kamengrad Thermal Power Plant | `'zhu_global_1km'` → `'medium'` | `'zhu_global_1km'` |
