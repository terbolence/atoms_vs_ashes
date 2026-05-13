<!-- man_hours: 0.3 -->
# Engine replay against persisted context (run anchor: 20260513T030738_70d5bc2c)

Read-only replay of the scoring engine for the three anchor sites (Timelkam, Brăila, Riedersbach). The engine reads the merged DB context but does not persist a new ranking row. Use to compare the post-fix band against the reviewer expectations recorded in [anchor_score_conformity.md](anchor_score_conformity.md).

## Timelkam (AT)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Timelkam (AT) | BF-01 | [5,6] | 5.5 | [5.0, 6.0] | Note: substation 15-30 km OR 110-219 kV; reinforcement plausible. |  |
| Timelkam (AT) | BF-02 | [3,4] | 3.5 | [3.0, 4.0] | 50-80% of required area; phased layout required. |  |
| Timelkam (AT) | EP-01 | [3,4] | 3.5 | [3.0, 4.0] | 40-54; severe EP ranking penalty, not exclusionary by itself. |  |
| Timelkam (AT) | EP-02 | [5,6] | 5.5 | [5.0, 6.0] | Adequate primary routes (0.5-1.0). |  |
| Timelkam (AT) | EP-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | EP-04 | [5,6] | 5.5 | [5.0, 6.0] | 9-25. |  |
| Timelkam (AT) | EP-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | HI-01 | [9,10] | 9.5 | [9.0, 10.0] | Only small / GA / heliport airport nearby; no military airbase within 60 km. |  |
| Timelkam (AT) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Timelkam (AT) | HI-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Timelkam (AT) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | HI-06 | [3,4] | 3.5 | [3.0, 4.0] | Airfield/depot 4-8 km or training area 2-5 km. |  |
| Timelkam (AT) | HI-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NH-01 | [9,10] | 9.5 | [9.0, 10.0] | Very low long-return seismic demand; strong margin to the A10 design-envelope boundary. |  |
| Timelkam (AT) | NH-02 | [9,10] | 9.5 | [9.0, 10.0] | Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level. |  |
| Timelkam (AT) | NH-03 | [9,10] | 9.5 | [9.0, 10.0] | Negligible susceptibility (Stage-1 favourable default). |  |
| Timelkam (AT) | NH-04 | [3,4] | 3.5 | [3.0, 4.0] | Significant slopes; stability study required. |  |
| Timelkam (AT) | NH-05 | [9,10] | 9.5 | [9.0, 10.0] | No karst; mine distance favourable or unknown with no subsidence signal. |  |
| Timelkam (AT) | NH-06 | [3,4] | 3.5 | [3.0, 4.0] | Bearing 50-80 kPa; bedrock > 20 m; GW < 2 m. |  |
| Timelkam (AT) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Timelkam (AT) | NH-08 | [9,10] | 9.5 | [7.5, 10.0] | Non-coastal OR elevation >= 50 m AMSL OR landlocked country. |  |
| Timelkam (AT) | NH-09 | [9,10] | 9.5 | [9.0, 10.0] | Favourable flood-zone class OR outside 1000-yr extent (>= 10 km / >= 30.5 m separation). |  |
| Timelkam (AT) | NH-10 | [9,10] | 9.5 | [9.0, 10.0] | Low wind region; standard EN 1991-1-4. |  |
| Timelkam (AT) | NH-11 | unscored | 4.0 | [4.0, 4.0] | aggregated(mean_of_sub_scores) | partial_unscored |
| Timelkam (AT) | NH-12 | unscored | 9.5 | [9.0, 10.0] | aggregated(min_of_sub_scores) |  |
| Timelkam (AT) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NH-14 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-01 | unscored | 7.0 | [7.0, 7.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Timelkam (AT) | NS-02 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Timelkam (AT) | NS-03 | unscored | 9.0 | [8.0, 9.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Timelkam (AT) | NS-04 | [5,6] | 5.5 | [5.0, 6.0] | 40-60 %. |  |
| Timelkam (AT) | NS-05 | [7,8] | 7.5 | [7.0, 8.0] | Buildable >= 25 ha AND contiguous >= 14 ha. |  |
| Timelkam (AT) | NS-06 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-08 | [7,8] | 7.5 | [7.0, 8.0] | 10-25 km OR natural land 15-30 %. |  |
| Timelkam (AT) | NS-09 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-10 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-11 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-12 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NS-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | RI-01 | unscored | 5.0 | [5.0, 5.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Timelkam (AT) | RI-02 | [1,2] | 1.5 | [1.0, 2.0] | < 10 m3/s. |  |
| Timelkam (AT) | RI-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | RI-04 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Timelkam (AT) | RI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | RI-06 | [7,8] | 7.5 | [7.0, 8.0] | -0.5 % to 0 %. |  |

## Brăila (RO)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Brăila (RO) | BF-01 | [5,6] | 5.5 | [5.0, 6.0] | Note: substation 15-30 km OR 110-219 kV; reinforcement plausible. |  |
| Brăila (RO) | BF-02 | [5,6] | 5.5 | [5.0, 6.0] | 80-100% of required area with documented expansion / layout flexibility. |  |
| Brăila (RO) | EP-01 | [5,6] | 5.5 | [5.0, 6.0] | 55-69. |  |
| Brăila (RO) | EP-02 | [1,2] | 1.5 | [1.0, 2.0] | Severe egress constraints. |  |
| Brăila (RO) | EP-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | EP-04 | [5,6] | 5.5 | [5.0, 6.0] | 9-25. |  |
| Brăila (RO) | EP-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | HI-01 | [9,10] | 9.5 | [9.0, 10.0] | Only small / GA / heliport airport nearby; no military airbase within 60 km. |  |
| Brăila (RO) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Brăila (RO) | HI-03 | [7,8] | 7.5 | [7.0, 8.0] | 15-25 km. |  |
| Brăila (RO) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Brăila (RO) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | HI-06 | [5,6] | 5.5 | [5.0, 6.0] | Airfield/depot 8-15 km or training area >= 5 km (project A5 boundary). |  |
| Brăila (RO) | HI-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NH-01 | [5,6] | 5.5 | [5.0, 6.0] | At or below the A10 score-5 design-envelope boundary; acceptable only with vendor-specific confirmation. |  |
| Brăila (RO) | NH-02 | [9,10] | 9.5 | [9.0, 10.0] | Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level. |  |
| Brăila (RO) | NH-03 | [3,4] | 3.5 | [3.0, 4.0] | High susceptibility without documented mitigation. |  |
| Brăila (RO) | NH-04 | [7,8] | 7.5 | [7.0, 8.0] | Gentle; minimal earthworks. |  |
| Brăila (RO) | NH-05 | [9,10] | 9.5 | [9.0, 10.0] | No karst; mine distance favourable or unknown with no subsidence signal. |  |
| Brăila (RO) | NH-06 | [5,6] | 5.5 | [5.0, 6.0] | Typical European mixed conditions (bearing 80-150 kPa). |  |
| Brăila (RO) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Brăila (RO) | NH-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NH-09 | [9,10] | 9.5 | [9.0, 10.0] | Favourable flood-zone class OR outside 1000-yr extent (>= 10 km / >= 30.5 m separation). |  |
| Brăila (RO) | NH-10 | [9,10] | 9.5 | [9.0, 10.0] | Low wind region; standard EN 1991-1-4. |  |
| Brăila (RO) | NH-11 | unscored | 4.0 | [4.0, 4.0] | aggregated(mean_of_sub_scores) | partial_unscored |
| Brăila (RO) | NH-12 | unscored | 9.5 | [9.0, 10.0] | aggregated(min_of_sub_scores) |  |
| Brăila (RO) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NH-14 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-01 | unscored | 7.0 | [6.0, 7.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Brăila (RO) | NS-02 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Brăila (RO) | NS-03 | unscored | 8.0 | [7.0, 8.0] | aggregated(weighted_mean_of_sub_scores) |  |
| Brăila (RO) | NS-04 | [7,8] | 7.5 | [7.0, 8.0] | 60-80 %. |  |
| Brăila (RO) | NS-05 | [7,8] | 7.5 | [7.0, 8.0] | Buildable >= 25 ha AND contiguous >= 14 ha. |  |
| Brăila (RO) | NS-06 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-08 | [7,8] | 7.5 | [7.0, 8.0] | 10-25 km OR natural land 15-30 %. |  |
| Brăila (RO) | NS-09 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-10 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-11 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-12 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NS-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | RI-01 | unscored | 5.0 | [5.0, 5.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Brăila (RO) | RI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 500 m3/s. |  |
| Brăila (RO) | RI-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | RI-04 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Brăila (RO) | RI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | RI-06 | [7,8] | 7.5 | [7.0, 8.0] | -0.5 % to 0 %. |  |

## Riedersbach (AT)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Riedersbach (AT) | BF-01 | [5,6] | 5.5 | [5.0, 6.0] | Note: substation 15-30 km OR 110-219 kV; reinforcement plausible. |  |
| Riedersbach (AT) | BF-02 | [1,2] | 1.5 | [1.0, 2.0] | < 50% of required area; insufficient for nuclear island at screening. |  |
| Riedersbach (AT) | EP-01 | [5,6] | 5.5 | [5.0, 6.0] | 55-69. |  |
| Riedersbach (AT) | EP-02 | [5,6] | 5.5 | [5.0, 6.0] | Adequate primary routes (0.5-1.0). |  |
| Riedersbach (AT) | EP-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | EP-04 | [5,6] | 5.5 | [5.0, 6.0] | 9-25. |  |
| Riedersbach (AT) | EP-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | HI-01 | [9,10] | 9.5 | [9.0, 10.0] | Only small / GA / heliport airport nearby; no military airbase within 60 km. |  |
| Riedersbach (AT) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Riedersbach (AT) | HI-03 | [7,8] | 7.5 | [7.0, 8.0] | 15-25 km. |  |
| Riedersbach (AT) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Riedersbach (AT) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | HI-06 | [7,8] | 7.5 | [7.0, 8.0] | Nearest airfield/depot 15-30 km. |  |
| Riedersbach (AT) | HI-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NH-01 | [9,10] | 9.5 | [9.0, 10.0] | Very low long-return seismic demand; strong margin to the A10 design-envelope boundary. |  |
| Riedersbach (AT) | NH-02 | [9,10] | 9.5 | [9.0, 10.0] | Very strong separation from mapped capable faults; surface-rupture concern effectively screened at desk-study level. |  |
| Riedersbach (AT) | NH-03 | [3,4] | 3.5 | [3.0, 4.0] | High susceptibility without documented mitigation. |  |
| Riedersbach (AT) | NH-04 | [3,4] | 3.5 | [3.0, 4.0] | Significant slopes; stability study required. |  |
| Riedersbach (AT) | NH-05 | [9,10] | 9.5 | [9.0, 10.0] | No karst; mine distance favourable or unknown with no subsidence signal. |  |
| Riedersbach (AT) | NH-06 | [5,6] | 5.5 | [5.0, 6.0] | Typical European mixed conditions (bearing 80-150 kPa). |  |
| Riedersbach (AT) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Riedersbach (AT) | NH-08 | [9,10] | 9.5 | [7.5, 10.0] | Non-coastal OR elevation >= 50 m AMSL OR landlocked country. |  |
| Riedersbach (AT) | NH-09 | [9,10] | 9.5 | [9.0, 10.0] | Favourable flood-zone class OR outside 1000-yr extent (>= 10 km / >= 30.5 m separation). |  |
| Riedersbach (AT) | NH-10 | [9,10] | 9.5 | [9.0, 10.0] | Low wind region; standard EN 1991-1-4. |  |
| Riedersbach (AT) | NH-11 | unscored | 4.0 | [4.0, 4.0] | aggregated(mean_of_sub_scores) | partial_unscored |
| Riedersbach (AT) | NH-12 | unscored | 9.5 | [9.0, 10.0] | aggregated(min_of_sub_scores) |  |
| Riedersbach (AT) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NH-14 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-01 | unscored | 7.0 | [6.0, 7.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Riedersbach (AT) | NS-02 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Riedersbach (AT) | NS-03 | unscored | 7.0 | [7.0, 7.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Riedersbach (AT) | NS-04 | [5,6] | 5.5 | [5.0, 6.0] | 40-60 %. |  |
| Riedersbach (AT) | NS-05 | [3,4] | 3.5 | [3.0, 4.0] | Buildable >= 8 ha OR contiguous >= 5 ha; complex ownership. |  |
| Riedersbach (AT) | NS-06 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-07 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-08 | [5,6] | 5.5 | [5.0, 6.0] | 5-10 km OR natural land 30-50 %. |  |
| Riedersbach (AT) | NS-09 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-10 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-11 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-12 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NS-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | RI-01 | unscored | 5.0 | [5.0, 5.0] | aggregated(weighted_mean_of_sub_scores) | partial_unscored |
| Riedersbach (AT) | RI-02 | [7,8] | 7.5 | [7.0, 8.0] | 100-500 m3/s. |  |
| Riedersbach (AT) | RI-03 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | RI-04 | unscored | 5.5 | [5.0, 6.0] | aggregated(min_of_sub_scores) |  |
| Riedersbach (AT) | RI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | RI-06 | [5,6] | 5.5 | [5.0, 6.0] | 0 % to +0.3 %. |  |
