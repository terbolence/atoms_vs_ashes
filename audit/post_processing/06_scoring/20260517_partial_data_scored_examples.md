<!-- man_hours: 1.0 -->
# Partial Data Scored-Site Examples

Read-only working-tree evaluation from
`audit/post_processing/06_scoring/20260517_partial_data_detail.csv`. No DB
writes.

## EP-03

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Porto Romano Power Station | AL | 9.5 | scored | No measured relief; open river/waterway context (interim screening). | `major_river_barrier=False`, `waterway_count_epz=0`, `relief_m_per_10km=None` | Plausible as an interim EP geography score only: open river/waterway context, but relief still needs GEE/DEM backfill for final confidence. |
| Mecsek Hills power station | HU | 5.5 | scored | No measured relief; manageable barrier/waterway context (interim). | `major_river_barrier=False`, `waterway_count_epz=14`, `relief_m_per_10km=None` | Plausible mid score: no major barrier, but many waterways increase evacuation-routing complexity. |
| Timelkam power station | AT | 1.5 | scored | No measured relief; major river barrier (interim). | `major_river_barrier=True`, `waterway_count_epz=163`, `relief_m_per_10km=None` | Plausible adverse score: high crossing count and major river barrier make the interim signal conservative. |

## HI-02

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Duernrohr power station | AT | 9.5 | scored | > 20 km, or completed Seveso search found nothing in radius. | `nearest_seveso_km=None`, `hi02_quality=high`, `hi02_search_completed=True` | Plausible favourable score: completed search with no facility found is treated as evidence. |
| Ruse Iztok power station | BG | 5.5 | scored | 5-10 km (project A7 pass-mark). | `nearest_seveso_km=5.24`, `hi02_quality=high`, `hi02_search_completed=True` | Plausible pass-mark score: just above the project avoidance threshold. |
| Porto Romano Power Station | AL | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `nearest_seveso_km=None`, `hi02_quality=not_applicable`, `hi02_search_completed=False` | Corrected by audit: `not_applicable` is not favourable completed-search evidence. |

## HI-03

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Timelkam power station | AT | 9.5 | scored | > 25 km, or completed toxic-source search found nothing in radius. | `nearest_toxic_source_km=None`, `hi03_quality=medium`, `hi03_search_completed=True` | Plausible favourable score: completed search with no toxic source in radius. |
| Mellach power station | AT | 5.5 | scored | 8-15 km (project A8 pass-mark). | `nearest_toxic_source_km=10.21`, `hi03_quality=high`, `hi03_search_completed=True` | Plausible pass-mark score: measured source distance is above A8 but not comfortably remote. |
| Duernrohr power station | AT | 1.5 | scored | < 3 km. | `nearest_toxic_source_km=0.69`, `hi03_quality=high`, `hi03_search_completed=True` | Plausible adverse score: source is close enough to require review. |
| Porto Romano Power Station | AL | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `nearest_toxic_source_km=None`, `hi03_quality=not_applicable`, `hi03_search_completed=False` | Correctly unscored: out-of-coverage/non-applicable is not favourable evidence. |

## HI-04

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Duernrohr power station | AT | 9.5 | scored | > 15 km, or completed flammable-storage search found nothing in radius. | `nearest_flammable_storage_km=None`, `hi04_quality=high`, `hi04_search_completed=True` | Plausible favourable score: completed search with no storage in radius. |
| Ruse Iztok power station | BG | 5.5 | scored | 4-8 km. | `nearest_flammable_storage_km=5.24`, `hi04_quality=high`, `hi04_search_completed=True` | Plausible mid score: close enough to matter, but outside the most adverse bands. |
| Porto Romano Power Station | AL | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `nearest_flammable_storage_km=None`, `hi04_quality=not_applicable`, `hi04_search_completed=False` | Correctly unscored: `not_applicable` remains a coverage/data-status marker. |

## NH-09

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Duernrohr power station | AT | 7.5 | scored | Low flood-zone class OR >= 4-6 km river separation; meets project A11. | `river_distance_km=None`, `flood_zone_class_500yr=negligible` | Plausible but limited: flood-zone class carries the score where river distance is absent. |
| Porto Romano Power Station | AL | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `river_distance_km=0.0`, `flood_zone_class_500yr=negligible` | Correctly not favourable: river separation is zero, so benign flood-zone class alone should not imply a high score. |

## NH-11

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Bobov Dol power station | BG | 10.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_corrected_mm=524.4`, `extreme_precip_corrected_mm=5.47` | Plausible favourable proxy: corrected annual and extreme precipitation sit in favourable bands. |
| Enns Power Station | AT | 6.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_corrected_mm=874.61`, `extreme_precip_corrected_mm=10.94` | Plausible middle score: wet shoulder plus moderate extreme-proxy signal. |
| Plomin power station | HR | 2.0 | scored | aggregated(mean_of_sub_scores) | `mean_annual_precip_corrected_mm=1992.11`, `extreme_precip_corrected_mm=24.93` | Plausible adverse proxy: both corrected metrics are high tails; still ranking-grade, not IDF/design rainfall. |

## RI-03

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Porto Romano Power Station | AL | 7.5 | scored | Low-permeability aquifer screening proxy. | `aquifer_type=low permeability`, `ri03_aquifer_screening_class=low` | Plausible favourable-ish proxy: lower permeability limits groundwater transport potential. |
| Duernrohr power station | AT | 5.5 | scored | Moderate-permeability aquifer screening proxy. | `aquifer_type=sedimentary sands`, `ri03_aquifer_screening_class=moderate` | Plausible mid score: sandy sedimentary aquifer is not treated as low-risk. |
| Zeltweg power station | AT | 1.5 | scored | Karst aquifer screening proxy. | `aquifer_type=karsts and chalkstones`, `ri03_aquifer_screening_class=karst` | Plausible adverse score: karst is a high-sensitivity proxy for groundwater dispersion. |
| Ugljevik power station | BA | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `aquifer_type=None`, `ri03_aquifer_screening_class=None` | Correctly unscored because aquifer evidence is missing. |

## RI-05

| Site | Country | Score | Flag | Band / reason | Key fields | Plausibility note |
| --- | --- | ---: | --- | --- | --- | --- |
| Riedersbach power station | AT | 9.5 | scored | Nearest >=50k population-centre proxy exceeds required distance by >= 50 %. | `nearest_city_50k_km=30.11`, `nearest_city_pop=146631`, `ri05_required_distance_km=16.0`, `ri05_distance_margin_pct=88.188` | Plausible favourable score: observed distance comfortably exceeds the population-tier distance. |
| Mellach power station | AT | 5.5 | scored | Nearest >=50k population-centre proxy meets required distance (pass mark). | `nearest_city_50k_km=19.04`, `nearest_city_pop=269997`, `ri05_required_distance_km=16.0`, `ri05_distance_margin_pct=19.0` | Plausible pass-mark score: distance is above the required tier but not by a wide margin. |
| Malesice power station | CZ | 0.0 | scored | Site embedded within 5 km of a >1M population centre. | `nearest_city_50k_km=4.69`, `nearest_city_pop=1275406`, `ri05_required_distance_km=48.0`, `ri05_distance_margin_pct=-90.229` | Plausible severe score: very close to a large population centre. |
| Porto Romano Power Station | AL | 5.0 | unscored | no_band_matched - pass-mark default (unscored) | `nearest_city_50k_km=None`, `nearest_city_pop=225176`, `ri05_required_distance_km=16.0`, `ri05_distance_margin_pct=None` | Correctly unscored: population proxy exists, but distance evidence is absent. |
