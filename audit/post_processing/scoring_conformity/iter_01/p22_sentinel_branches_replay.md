<!-- man_hours: 0.3 -->
# Engine replay against persisted context (run anchor: 20260513T030738_70d5bc2c)

Read-only replay of the scoring engine for the three anchor sites (Timelkam, Brăila, Riedersbach). The engine reads the merged DB context but does not persist a new ranking row. Use to compare the post-fix band against the reviewer expectations recorded in [anchor_score_conformity.md](anchor_score_conformity.md).

## Timelkam (AT)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Timelkam (AT) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Timelkam (AT) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Timelkam (AT) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Timelkam (AT) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Timelkam (AT) | NH-08 | [9,10] | 9.5 | [7.5, 10.0] | Non-coastal OR elevation >= 50 m AMSL OR landlocked country. |  |
| Timelkam (AT) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |

## Brăila (RO)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Brăila (RO) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Brăila (RO) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Brăila (RO) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Brăila (RO) | NH-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Brăila (RO) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |

## Riedersbach (AT)

| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |
|---|---|---|---:|---|---|---|
| Riedersbach (AT) | HI-02 | [9,10] | 9.5 | [9.0, 10.0] | > 20 km, or completed Seveso search found nothing in radius. |  |
| Riedersbach (AT) | HI-04 | [9,10] | 9.5 | [9.0, 10.0] | > 15 km, or completed flammable-storage search found nothing in radius. |  |
| Riedersbach (AT) | HI-05 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | HI-08 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
| Riedersbach (AT) | NH-07 | [9,10] | 9.5 | [9.0, 10.0] | No plausible pathway (including connector-null / beyond search radius). |  |
| Riedersbach (AT) | NH-08 | [9,10] | 9.5 | [7.5, 10.0] | Non-coastal OR elevation >= 50 m AMSL OR landlocked country. |  |
| Riedersbach (AT) | NH-13 | unscored | 5.0 | [5.0, 5.0] | no_band_matched — pass-mark default (unscored) | unscored |
