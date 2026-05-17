<!-- man_hours: 1.2 -->
# Phase 2 Scored Site Examples

Generated at: 2026-05-17T12:40:07.065751+00:00

Detail CSV: `audit/post_processing/06_scoring/20260517_phase2_partial_data_detail.csv`
Summary CSV: `audit/post_processing/06_scoring/20260517_phase2_partial_data_summary.csv`

Examples are from read-only in-memory evaluation of working-tree scoring logic.
They are not persisted `ranking_scores` rows; DB-writing rescore remains consent-gated.

## EP-03

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | AT | Timelkam power station | 1.5 | scored | No measured relief; major river barrier (interim). | `major_river_barrier`=True<br>`waterway_count_epz`=163<br>`ep03_quality`=medium<br>`emergency_run_id`=20260512T184829_1d1e6d41<br>`emergency_fetched_at`=2026-05-12 21:49:07.082280+03:00 |
| median scored | PL | Szczecin power station | 9.5 | scored | No measured relief; open river/waterway context (interim screening). | `major_river_barrier`=False<br>`waterway_count_epz`=0<br>`ep03_quality`=medium<br>`emergency_run_id`=20260512T184829_1d1e6d41<br>`emergency_fetched_at`=2026-05-12 21:49:21.956791+03:00 |
| high scored | XK | Kosovo B power station | 9.5 | scored | No measured relief; open river/waterway context (interim screening). | `major_river_barrier`=False<br>`waterway_count_epz`=0<br>`ep03_quality`=medium<br>`emergency_run_id`=20260512T184829_1d1e6d41<br>`emergency_fetched_at`=2026-05-12 21:49:43.983859+03:00 |

## HI-02

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | BG | Ruse Iztok power station | 5.5 | scored | 5-10 km (project A7 pass-mark). | `nearest_seveso_km`=5.24<br>`hi02_quality`=high<br>`hi02_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 21:56:17.828465+03:00 |
| median scored | RS | Nikola Tesla power station | 9.5 | scored | > 20 km, or completed Seveso search found nothing in radius. | `hi02_quality`=low<br>`hi02_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 22:47:34.694517+03:00 |
| high scored | XK | Kosovo C power station | 9.5 | scored | > 20 km, or completed Seveso search found nothing in radius. | `hi02_quality`=not_applicable<br>`hi02_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 23:31:46.080760+03:00 |

## HI-03

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | AT | Duernrohr power station | 1.5 | scored | < 3 km. | `nearest_toxic_source_km`=0.69<br>`hi03_quality`=high<br>`hi03_search_completed`=True<br>`human_run_id`=20260512T184829_549c4b66<br>`human_fetched_at`=2026-05-12 21:48:30.586134+03:00 |
| median scored | RS | Kostolac power station | 9.5 | scored | > 25 km, or completed toxic-source search found nothing in radius. | `hi03_quality`=low<br>`hi03_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 22:46:38.105346+03:00 |
| high scored | XK | Kosovo C power station | 9.5 | scored | > 25 km, or completed toxic-source search found nothing in radius. | `hi03_quality`=not_applicable<br>`hi03_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 23:31:46.080760+03:00 |

## HI-04

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | BG | Ruse Iztok power station | 5.5 | scored | 4-8 km. | `nearest_flammable_storage_km`=5.24<br>`hi04_quality`=high<br>`hi04_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 21:56:17.828465+03:00 |
| median scored | RS | Nikola Tesla power station | 9.5 | scored | > 15 km, or completed flammable-storage search found nothing in radius. | `hi04_quality`=low<br>`hi04_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 22:47:34.694517+03:00 |
| high scored | XK | Kosovo C power station | 9.5 | scored | > 15 km, or completed flammable-storage search found nothing in radius. | `hi04_quality`=not_applicable<br>`hi04_search_completed`=True<br>`human_run_id`=hi06_spf_20260512_185043<br>`human_fetched_at`=2026-05-12 23:31:46.080760+03:00 |

## NH-09

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | AL | Porto Romano Power Station | 5.5 | scored | Benign flood-zone class but river/waterway proxy is within 2 km; routine flood-interface review. | `nearest_river_km`=0.0<br>`flood_zone_class_500yr`=negligible<br>`flood_zone_class`=negligible<br>`natural_run_id`=20260512T184829_1d1e6d41<br>`natural_fetched_at`=2026-05-12 21:49:06.391969+03:00 |
| median scored | RS | Kolubara B power station | 7.5 | scored | Low flood-zone class OR >= 4-6 km river separation; meets project A11. | `flood_zone_class_500yr`=negligible<br>`flood_zone_class`=negligible<br>`natural_run_id`=20260512T184804_724e6d22<br>`natural_fetched_at`=2026-05-12 22:23:03.635822+03:00 |
| high scored | XK | Kosovo C power station | 7.5 | scored | Low flood-zone class OR >= 4-6 km river separation; meets project A11. | `flood_zone_class_500yr`=negligible<br>`flood_zone_class`=negligible<br>`natural_run_id`=20260512T184804_724e6d22<br>`natural_fetched_at`=2026-05-12 22:30:53.008827+03:00 |

## NH-11

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | HR | Plomin power station | 2.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_mm`=65.53<br>`mean_annual_precip_corrected_mm`=1992.112<br>`extreme_precip_mm`=0.82<br>`extreme_precip_corrected_mm`=24.928<br>`natural_run_id`=20260512T184804_724e6d22 |
| median scored | RO | Oradea power station | 8.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_mm`=25.8<br>`mean_annual_precip_corrected_mm`=784.32<br>`extreme_precip_mm`=0.21<br>`extreme_precip_corrected_mm`=6.384<br>`natural_run_id`=20260512T184804_724e6d22 |
| high scored | XK | Kosovo B power station | 10.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_mm`=19.91<br>`mean_annual_precip_corrected_mm`=605.264<br>`extreme_precip_mm`=0.19<br>`extreme_precip_corrected_mm`=5.776<br>`natural_run_id`=20260512T184804_724e6d22 |

## RI-03

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | AT | Zeltweg power station | 1.5 | scored | Karst aquifer screening proxy. | `aquifer_type`=karsts and chalkstones<br>`ri03_aquifer_screening_class`=karst<br>`ri03_quality`=medium<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:07.284379+03:00 |
| median scored | TR | Atakaş power station | 5.5 | scored | Moderate-permeability aquifer screening proxy. | `aquifer_type`=hard rocks<br>`ri03_aquifer_screening_class`=moderate<br>`ri03_quality`=medium<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:28.463435+03:00 |
| high scored | UA | Starobesheve power station | 7.5 | scored | Low-permeability aquifer screening proxy. | `aquifer_type`=low permeability<br>`ri03_aquifer_screening_class`=low<br>`ri03_quality`=medium<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:43.214230+03:00 |
| unscored caveat | BA | Ugljevik power station | 5.0 | unscored | no_band_matched — pass-mark default (unscored) | `ri03_quality`=low<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:08.723234+03:00 |

## RI-05

| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |
| --- | --- | --- | ---: | --- | --- | --- |
| low scored | CZ | Malesice power station | 0.0 | scored | Site embedded within 5 km of a >1M population centre. | `nearest_city_50k_km`=4.69<br>`nearest_city_pop`=1275406.0<br>`pop_density_16km`=1827.96<br>`pop_total_16km`=1469986<br>`ri05_required_distance_km`=48.0 |
| median scored | TR | Evrese power station | 5.5 | scored | GHSL 16 km population proxy indicates >=50k people in the wider screening ring, but no city-distance margin is available. | `pop_density_16km`=69.37<br>`pop_total_16km`=55784<br>`ri05_required_distance_km`=8.0<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:32.540409+03:00 |
| high scored | UA | Zmiivska power station | 9.5 | scored | No >=50k population-centre proxy within screening envelope. | `pop_density_16km`=52.78<br>`pop_total_16km`=42445<br>`radiological_run_id`=20260512T184829_1d1e6d41<br>`radiological_fetched_at`=2026-05-12 21:49:43.594734+03:00 |

