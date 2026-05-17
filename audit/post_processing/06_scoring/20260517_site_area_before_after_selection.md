<!-- man_hours: 1.5 -->

# Site Area Before/After Audit Selection

**Source audit CSV:** `audit/post_processing/06_scoring/20260517_site_area_confidence.csv`

This file is a review artifact only. No database update has been applied. "Post state" means the value and provenance that `apply_site_area_resolution.py --write --i-consent-to-write` would write for rows accepted by the user. The apply path does not change `buildable_area_ha`, `largest_contiguous_ha`, or `favourable_area_ha`.

**Full DB coverage (all 361 sites):** see `audit/post_processing/06_scoring/20260517_site_area_coverage_all_sites.md` (gap lists + full register).

## Category Coverage

| Category | Covered by |
| --- | --- |
| Tiny OSM footprint (`S1`) | Doicesti, Mintia-Deva, Lüminer |
| Tiny footprint with large regional envelope (`S2`) | Mintia-Deva, Zabrze, Karapinar |
| Contiguous/buildable physical inconsistency (`S3`/`S4`) | Porto Romano, Tuzla, Kozienice, Karapinar, Meda |
| Existing merge-audit mismatch (`S5`) | Doicesti, Mintia-Deva, Porto Romano, Duernrohr, Tuzla, Kozienice, Zabrze |
| LLM/API conflict (`S6`) | Doicesti, Mintia-Deva, Duernrohr, Tuzla, Kozienice |
| Weak OSM / WorldCover proxy (`S7`) | Kozienice, Karapinar, Meda |
| Cancelled/never-built ambiguity (`S8`) | Porto Romano, Doicesti, Karapinar, Meda |
| New inference sources | `buildable_area_inference`, `contiguous_capped_inference`, `favourable_envelope_inference`, `capacity_bounded_inference` |
| Previously unidentified sample rows now estimated | Zabrze, Karapinar, Lüminer, Meda |

## Initial vs Proposed Post State

| Site | Why selected | Initial `site_area_ha` | Initial buildable | Initial contiguous | Favourable envelope | Proposed `site_area_ha` | Proposed source | Confidence | Write eligible | Flags |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| Doicesti power station | User-known/web-supported 40 ha site value replaces the tiny OSM polygon. | 0.16 | 0.16 | 0.16 | 49.32 | 40 | llm_web_observation | medium (55) | True | S1;S5;S6;S8 |
| Mintia-Deva power station | Tiny OSM polygon is replaced by cited web/LLM footprint evidence. | 0.01 | 0.01 | 0.01 | 131.99 | 329.78 | llm_web_observation | medium (65) | True | S1;S2;S5;S6 |
| Porto Romano Power Station | Cancelled/never-built no longer forces zero; capped contiguous and capacity evidence produce a review estimate. | 5.75 | 5.75 | 616.36 | 42.12 | 64 | contiguous_capped_inference | review (40) | True | S3;S4;S5;S8 |
| Duernrohr power station | Cited web observation and structured audit agree on a larger retired-site footprint. | 10.15 | 10.15 | 10.15 | 288.97 | 120 | llm_web_observation | medium (65) | True | S5;S6 |
| Tuzla Thermal Power Plant | Operating site with severe contiguous/buildable inconsistency and web-supported replacement. | 6.27 | 6.27 | 301.35 | 36.39 | 130 | llm_web_observation | medium (55) | True | S3;S4;S5;S6 |
| Kozienice power station | Weak/conflicting OSM footprint is replaced by larger cited web footprint. | 8.76 | 20.61 | 187.47 | 15.45 | 400 | llm_web_observation | medium (55) | True | S3;S4;S5;S6;S7 |
| Zabrze power station | No longer unidentified; discounted favourable envelope beats tiny footprint and capacity-only fallback. | 5.06 | 5.06 | 5.06 | 94.48 | 70.86 | favourable_envelope_inference | low (27) | True | S2;S5 |
| Karapinar Konya Şeker power station | No longer unidentified; large buildable envelope is selected while contiguous area is capped. | 5.09 | 312.24 | 1247.24 | 243.52 | 312.24 | buildable_area_inference | review (42) | True | S2;S3;S4;S5;S7;S8 |
| Lüminer Enerji power station | No longer unidentified; tiny polygon is replaced by a low-confidence capacity estimate. | 0.02 | 0.02 | 0.02 | 0 | 12.8 | capacity_bounded_inference | low (25) | True | S1 |
| Meda power station | No longer unidentified; buildable area is selected and oversized contiguous area is capped. | — | 200.55 | 622.18 | 82.25 | 200.55 | buildable_area_inference | review (47) | True | S3;S7;S8 |

## Candidate Evidence Snapshot

| Site | Candidate summary (`source=value/tier/score/write`) | Expansion potential | Parsed buildable text | Regional method |
| --- | --- | ---: | ---: | --- |
| Doicesti power station | llm_web_structured=40 ha/low/45/write=True<br>llm_web_observation=40 ha/medium/55/write=True<br>osm_polygon=0.16 ha/none/0/write=False<br>favourable_envelope_inference=49.32 ha/review/42/write=True<br>capacity_bounded_inference=49.32 ha/review/35/write=True | 115 | 40 | comment_buildable_x_fav_pct |
| Mintia-Deva power station | llm_web_structured=329.78 ha/medium/55/write=True<br>llm_web_observation=329.78 ha/medium/65/write=True<br>osm_polygon=0.01 ha/none/0/write=False<br>favourable_envelope_inference=98.99 ha/review/42/write=True<br>capacity_bounded_inference=102.8 ha/review/35/write=True | 59.78 | 270 | comment_buildable_x_fav_pct |
| Porto Romano Power Station | llm_web_structured=5.75 ha/none/15/write=False<br>osm_polygon=5.75 ha/none/0/write=False<br>contiguous_capped_inference=64 ha/review/40/write=True<br>favourable_envelope_inference=42.12 ha/review/35/write=True<br>capacity_bounded_inference=64 ha/review/35/write=True | 0 | 0 | comment_buildable_x_fav_pct |
| Duernrohr power station | llm_web_structured=120 ha/medium/55/write=True<br>llm_web_observation=120 ha/medium/65/write=True<br>osm_polygon=10.15 ha/none/10/write=False<br>buildable_area_inference=10.15 ha/review/42/write=True<br>contiguous_capped_inference=10.15 ha/review/40/write=True<br>favourable_envelope_inference=216.73 ha/review/35/write=True<br>capacity_bounded_inference=64.16 ha/review/28/write=True | 23 | 80 | comment_buildable_x_fav_pct |
| Tuzla Thermal Power Plant | llm_web_structured=130 ha/low/45/write=True<br>llm_web_observation=130 ha/medium/55/write=True<br>osm_polygon=6.27 ha/none/0/write=False<br>contiguous_capped_inference=131.2 ha/review/40/write=True<br>favourable_envelope_inference=27.29 ha/review/27/write=True<br>capacity_bounded_inference=131.2 ha/review/35/write=True | 320 | 130 | comment_buildable_x_fav_pct |
| Kozienice power station | llm_web_structured=400 ha/low/45/write=True<br>llm_web_observation=400 ha/medium/55/write=True<br>osm_polygon=8.76 ha/none/0/write=False<br>buildable_area_inference=20.61 ha/review/27/write=True<br>contiguous_capped_inference=187.47 ha/review/25/write=True<br>favourable_envelope_inference=7.72 ha/review/42/write=True<br>capacity_bounded_inference=400 ha/review/35/write=True | 313 | 350 | comment_buildable_x_fav_pct |
| Zabrze power station | osm_polygon=5.06 ha/none/3/write=False<br>favourable_envelope_inference=70.86 ha/low/27/write=True<br>capacity_bounded_inference=8.64 ha/low/28/write=True | — | — | comment_buildable_x_fav_pct |
| Karapinar Konya Şeker power station | osm_polygon=5.09 ha/none/0/write=False<br>buildable_area_inference=312.24 ha/review/42/write=True<br>contiguous_capped_inference=312.24 ha/review/40/write=True<br>favourable_envelope_inference=243.52 ha/review/42/write=True<br>capacity_bounded_inference=160 ha/review/28/write=True | — | — | comment_buildable_x_fav_pct |
| Lüminer Enerji power station | osm_polygon=0.02 ha/none/5/write=False<br>capacity_bounded_inference=12.8 ha/low/25/write=True | — | — | comment_buildable_x_fav_pct |
| Meda power station | buildable_area_inference=200.55 ha/review/47/write=True<br>contiguous_capped_inference=200.55 ha/review/45/write=True<br>favourable_envelope_inference=82.25 ha/review/40/write=True<br>capacity_bounded_inference=61.6 ha/review/33/write=True | — | — | comment_buildable_x_fav_pct |

## Audit Notes

- Rows with `write_eligible=True` are recommendations only. They have not been written to the DB.
- `review` confidence means an estimate exists but conflicts or threshold crossings remain visible for human approval.
- `capacity_bounded_inference` uses `installed_capacity_mw * 0.08 ha/MWe`, bounded by credible local spatial evidence when such evidence exists.
- Cancelled / never-built status no longer writes `0 ha` when nonzero spatial or project-land evidence exists.
