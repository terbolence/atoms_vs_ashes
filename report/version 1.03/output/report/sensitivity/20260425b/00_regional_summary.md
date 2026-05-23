# Regional sensitivity summary — 20260425b

_Generated on 2026-04-25 (UTC) from audit CSVs._

This document presents **site stability banding** (A–H) at two scopes:

- **Regional — all SMRs pooled** (257 sites).
- **Regional — NuScale `nuscale_voygr6` only** (257 sites).

Per-country rankings (with local top-K shortlists and within-country bands) live in `national/`.

## 1. Band counts — all SMRs pooled

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 5 | 1.9 % |
| B | 3 | 1.2 % |
| C | 1 | 0.4 % |
| D | 31 | 12.1 % |
| E | 1 | 0.4 % |
| F | 2 | 0.8 % |
| G | 3 | 1.2 % |
| H | 211 | 82.1 % |
| **A–G (named)** | **46** | **17.9 %** |

![A–H band counts (all SMRs)](figures/band_counts_ah_global.png)

## 2. Band counts — NuScale `nuscale_voygr6`

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 5 | 1.9 % |
| B | 3 | 1.2 % |
| C | 1 | 0.4 % |
| D | 31 | 12.1 % |
| E | 1 | 0.4 % |
| F | 2 | 0.8 % |
| G | 3 | 1.2 % |
| H | 211 | 82.1 % |
| **A–G (named)** | **46** | **17.9 %** |

![A–H band counts (NuScale)](figures/band_counts_ah_nuscale.png)

## 3. Top sites — NuScale (Band A/B/C, ≤ 25)

| Rank | Site | Country | Band | Top-5 % rate | Top-10 % rate | Top-30 % rate |
| ---: | --- | --- | :---: | ---: | ---: | ---: |
| 1 | Turceni power station | RO | A | 1.0 | 1.0 | 1.0 |
| 2 | Opalenie power station | PL | A | 1.0 | 1.0 | 1.0 |
| 3 | Çoban Yıldız power station | TR | A | 0.8667 | 0.9333 | 1.0 |
| 4 | Polaniec power station | PL | A | 0.8667 | 0.9333 | 0.9333 |
| 5 | Konya Karapınar power station | TR | A | 0.8 | 0.9333 | 1.0 |
| 6 | Dolna Odra power station | PL | B | 0.2667 | 0.9333 | 1.0 |
| 7 | Puchaczow power station | PL | B | 0.2 | 0.9333 | 1.0 |
| 8 | Eren-1 power station | TR | B | 0.1333 | 0.8667 | 1.0 |
| 9 | Akdeniz Enerji power station | TR | C | 0.0667 | 0.6 | 1.0 |

## 4. Top sites — all SMRs (Band A/B/C, ≤ 25)

| Rank | Site | Country | Band | Top-5 % rate | Top-10 % rate | Top-30 % rate |
| ---: | --- | --- | :---: | ---: | ---: | ---: |
| 1 | Turceni power station | RO | A | 1.0 | 1.0 | 1.0 |
| 2 | Opalenie power station | PL | A | 1.0 | 1.0 | 1.0 |
| 3 | Çoban Yıldız power station | TR | A | 0.8667 | 0.9333 | 1.0 |
| 4 | Polaniec power station | PL | A | 0.8667 | 0.9333 | 0.9333 |
| 5 | Konya Karapınar power station | TR | A | 0.8 | 0.9333 | 1.0 |
| 6 | Dolna Odra power station | PL | B | 0.2667 | 0.9333 | 1.0 |
| 7 | Puchaczow power station | PL | B | 0.2 | 0.9333 | 1.0 |
| 8 | Eren-1 power station | TR | B | 0.1333 | 0.8667 | 1.0 |
| 9 | Akdeniz Enerji power station | TR | C | 0.0667 | 0.6 | 1.0 |

## 5. Country roll-up (all-SMR)

| Country | n sites | K (shortlist) | Band A | Band B | Band C | Mean Jaccard vs baseline top-K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AT | 6 | 6 | 0 | 0 | 1 | 0.9333 |
| BA | 6 | 6 | 0 | 0 | 1 | 0.9333 |
| BG | 7 | 7 | 1 | 0 | 0 | 0.9333 |
| BY | 2 | 2 | 1 | 0 | 0 | 0.9667 |
| CZ | 23 | 10 | 2 | 1 | 0 | 0.9333 |
| HR | 1 | 1 | 1 | 0 | 0 | 0.9333 |
| HU | 10 | 10 | 1 | 0 | 0 | 0.9333 |
| LV | 1 | 1 | 1 | 0 | 0 | 0.9333 |
| MD | 1 | 1 | 1 | 0 | 0 | 0.9333 |
| ME | 1 | 1 | 1 | 0 | 0 | 0.9333 |
| MK | 4 | 4 | 1 | 0 | 0 | 0.9333 |
| PL | 41 | 13 | 1 | 1 | 0 | 0.9265 |
| RO | 19 | 10 | 1 | 0 | 0 | 0.9236 |
| RS | 7 | 7 | 1 | 0 | 0 | 0.9524 |
| SK | 5 | 5 | 1 | 0 | 0 | 0.9333 |
| TR | 106 | 32 | 2 | 2 | 0 | 0.8893 |
| UA | 17 | 10 | 1 | 0 | 1 | 0.8218 |

## 6. Source artefacts

- `20260425b_site_bands.csv` — all-SMR bands.
- `20260425b_site_bands_nuscale_voygr6.csv` — NuScale bands.
- `20260425b_country_rankings_summary.csv` — country roll-up.
- Methodology: [`report/methodology/sensitivity_analysis.md`](../../methodology/sensitivity_analysis.md).
