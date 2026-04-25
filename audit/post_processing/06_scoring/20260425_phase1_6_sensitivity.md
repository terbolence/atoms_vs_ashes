# Phase 1.6 sensitivity suite — 20260425

- Run ID: `p16_20260425T075225_014e4161`
- DB profile: `merged`
- Stages run: 1
- Pairs processed: **2904** (sites × SMRs)
- Baseline scored rows: **2264** / 8712
- Top-5 % slice: **113** pairs; top-10 % slice: **226** pairs.

## Executive summary

- Profiles compared vs `baseline`: **15**.
- Lowest top-10 % Jaccard: **0.1075** (profile `w_swing`, overlap 20/226).
- Largest mean |Δscore|: **0.2896** (profile `mc_10000`).

## Criterion importance (OAT, top 15)

Source: `20260425_oat_importance.csv` (48 criteria).

| Rank | Criterion | Family | Name | Importance | Mean |Δrank| |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | `NH-01` | NH | Seismic ground motion (PGA) | 0.1006 | 20.923 |
| 2 | `NS-05` | NS | Land availability / ownership / zoning | 0.071 | 14.769 |
| 3 | `NS-04` | NS | Site topography / grading | 0.068 | 14.154 |
| 4 | `HI-06` | HI | Military installations | 0.0621 | 12.923 |
| 5 | `RI-04` | RI | Population density (EPZ rings) | 0.0592 | 12.308 |
| 6 | `RI-06` | RI | Population projections (60-yr design life) | 0.0562 | 11.692 |
| 7 | `NH-05` | NH | Subsidence / karst / mining / oil & gas | 0.0476 | 9.894 |
| 8 | `NS-03` | NS | Transport access (heavy haul road / rail / port) | 0.0473 | 9.846 |
| 9 | `EP-02` | EP | Evacuation routes (road network) | 0.0444 | 9.24 |
| 10 | `NH-04` | NH | Geotechnical - slope stability | 0.0385 | 8.0 |
| 11 | `NH-02` | NH | Seismic surface rupture (capable faults) | 0.0325 | 6.769 |
| 12 | `NS-01` | NS | Cooling water / ultimate heat sink | 0.0266 | 5.538 |
| 13 | `HI-03` | HI | Toxic / gas releases | 0.0237 | 4.923 |
| 14 | `NH-03` | NH | Geotechnical - settlement and liquefaction | 0.0148 | 3.077 |
| 15 | `NS-02` | NS | Grid connection (detailed) | 0.0148 | 3.077 |

## Stages

| # | Stage | Iterations | Weight rows | MC rows | Threshold rows | Country rows | Audit file |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | MC @ 10000 | 10000 | 31944 | 2904 | 5808 | 2904 | `20260425_sensitivity_mc_10000.md` |

## Top-N stability vs. baseline (pct-based)

Top-5 % = **113** pairs; top-10 % = **226** pairs (fractions of the baseline scored slice).

| Profile | Scored pairs | Top-5 % overlap | Jaccard@5 % | Top-10 % overlap | Jaccard@10 % | Mean |Δ| | Max |Δ| | Pairs in drift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `country_balanced` | 2264 | 113/113 | 1.0 | 186/226 | 1.0 | 0.0409 | 0.528 | 2264 |
| `mc_10000` | 2264 | 64/113 | 0.4384 | 162/226 | 0.75 | 0.2896 | 1.009 | 2264 |
| `threshold_minus_25` | 3552 | 89/113 | 0.4611 | 154/226 | 0.4543 | 0.1959 | 0.621 | 3552 |
| `threshold_plus_25` | 3552 | 105/113 | 0.5932 | 162/226 | 0.4894 | 0.1835 | 0.688 | 3552 |
| `w_EP_minus_20` | 2264 | 113/113 | 1.0 | 184/226 | 0.9787 | 0.0671 | 0.54 | 2264 |
| `w_EP_plus_20` | 2264 | 113/113 | 1.0 | 186/226 | 1.0 | 0.0687 | 0.553 | 2264 |
| `w_HI_minus_20` | 2264 | 112/113 | 0.9912 | 184/226 | 0.9388 | 0.0646 | 0.544 | 2264 |
| `w_HI_plus_20` | 2264 | 106/113 | 0.8833 | 180/226 | 0.9375 | 0.0667 | 0.537 | 2264 |
| `w_NH_minus_20` | 2264 | 112/113 | 0.9912 | 180/226 | 0.9375 | 0.071 | 0.513 | 2264 |
| `w_NH_plus_20` | 2264 | 106/113 | 0.8833 | 176/226 | 0.8713 | 0.0689 | 0.572 | 2264 |
| `w_NS_minus_20` | 2264 | 106/113 | 0.8833 | 178/226 | 0.957 | 0.1023 | 0.657 | 2264 |
| `w_NS_plus_20` | 2264 | 112/113 | 0.9912 | 178/226 | 0.8812 | 0.088 | 0.52 | 2264 |
| `w_RI_minus_20` | 2264 | 106/113 | 0.8833 | 180/226 | 0.9 | 0.063 | 0.572 | 2264 |
| `w_RI_plus_20` | 2264 | 113/113 | 1.0 | 176/226 | 0.9362 | 0.0619 | 0.559 | 2264 |
| `w_swing` | 208 | 10/113 | 0.0885 | 20/226 | 0.1075 | 0.1621 | 0.32 | 208 |

## Weight sensitivity by category (±20 %)

| Category | Avg mean |Δscore| | Avg top-10 % overlap (of 226) |
| --- | ---: | ---: |
| `EP` | 0.0679 | 185 |
| `HI` | 0.0657 | 182 |
| `NH` | 0.0699 | 178 |
| `NS` | 0.0951 | 178 |
| `RI` | 0.0624 | 178 |

## Site stability banding (regional, all SMRs)

_Percentiles computed across all scored (site, SMR) pairs._

Source: `20260425_site_bands.csv` (257 sites).

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 14 | 5.4 % |
| B | 8 | 3.1 % |
| C | 2 | 0.8 % |
| D | 46 | 17.9 % |
| E | 0 | 0.0 % |
| F | 2 | 0.8 % |
| G | 3 | 1.2 % |
| H | 182 | 70.8 % |

### Band A sites (top-5 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Turceni power station | RO | 1.0 | 1.0 | 1.0 |
| Opalenie power station | PL | 1.0 | 1.0 | 1.0 |
| Dolna Odra power station | PL | 0.9333 | 0.9333 | 1.0 |
| Çoban Yıldız power station | TR | 0.9333 | 0.9333 | 1.0 |
| Puchaczow power station | PL | 0.9333 | 0.9333 | 1.0 |
| Polaniec power station | PL | 0.9333 | 0.9333 | 0.9333 |
| Mohacs power station | HU | 0.9333 | 0.9333 | 0.9333 |
| Konya Karapınar power station | TR | 0.8667 | 1.0 | 1.0 |
| Eren-1 power station | TR | 0.8667 | 0.9333 | 1.0 |
| Akdeniz Enerji power station | TR | 0.8667 | 0.9333 | 1.0 |
| Braila power station | RO | 0.8667 | 0.9333 | 0.9333 |
| Yeşilovacık power station | TR | 0.8667 | 0.9333 | 0.9333 |
| Zelwa power station | BY | 0.8667 | 0.8667 | 0.9333 |
| Starobesheve power station | UA | 0.8 | 0.9333 | 0.9333 |

### Band B sites (top-10 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Zarnowiec power station | PL | 0.5333 | 0.8667 | 0.9333 |
| Opole power station | PL | 0.2 | 0.9333 | 0.9333 |
| Braila power station | RO | 0.0667 | 0.9333 | 0.9333 |
| Chvaletice power station | CZ | 0.0667 | 0.8667 | 0.9333 |
| Pocerady power station | CZ | 0.0667 | 0.8 | 0.9333 |
| Romag Termo power station | RO | 0.0667 | 0.8 | 0.9333 |
| Burshtyn power station | UA | 0.0 | 0.8 | 0.9333 |
| Turów power station | PL | 0.0 | 0.8 | 0.9333 |

## Site stability banding — NuScale `nuscale_voygr6`

_Percentiles computed on the NuScale-only pool._

Source: `20260425_site_bands_nuscale_voygr6.csv` (257 sites).

| Band | Sites | Share |
| --- | ---: | ---: |
| A | 12 | 4.7 % |
| B | 8 | 3.1 % |
| C | 3 | 1.2 % |
| D | 46 | 17.9 % |
| E | 1 | 0.4 % |
| F | 2 | 0.8 % |
| G | 1 | 0.4 % |
| H | 184 | 71.6 % |

### Band A sites (top-5 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Opalenie power station | PL | 1.0 | 1.0 | 1.0 |
| Turceni power station | RO | 0.9333 | 1.0 | 1.0 |
| Dolna Odra power station | PL | 0.9333 | 0.9333 | 1.0 |
| Çoban Yıldız power station | TR | 0.9333 | 0.9333 | 1.0 |
| Puchaczow power station | PL | 0.9333 | 0.9333 | 1.0 |
| Polaniec power station | PL | 0.9333 | 0.9333 | 0.9333 |
| Mohacs power station | HU | 0.9333 | 0.9333 | 0.9333 |
| Eren-1 power station | TR | 0.8667 | 0.9333 | 1.0 |
| Konya Karapınar power station | TR | 0.8667 | 0.9333 | 1.0 |
| Braila power station | RO | 0.8667 | 0.9333 | 0.9333 |
| Akdeniz Enerji power station | TR | 0.8667 | 0.9333 | 0.9333 |
| Yeşilovacık power station | TR | 0.8 | 0.9333 | 0.9333 |

### Band B sites (top-10 % in ≥ 80 % of scenarios)

| Site | Country | Top-5 % | Top-10 % | Top-30 % |
| --- | --- | ---: | ---: | ---: |
| Zelwa power station | BY | 0.7333 | 0.8667 | 0.9333 |
| Starobesheve power station | UA | 0.6 | 0.9333 | 0.9333 |
| Zarnowiec power station | PL | 0.2667 | 0.8667 | 0.9333 |
| Opole power station | PL | 0.2 | 0.9333 | 0.9333 |
| Chvaletice power station | CZ | 0.0667 | 0.8667 | 0.9333 |
| Pocerady power station | CZ | 0.0667 | 0.8 | 0.9333 |
| Braila power station | RO | 0.0 | 0.9333 | 0.9333 |
| Turów power station | PL | 0.0 | 0.8 | 0.9333 |

## Country roll-up

Source: `20260425_country_rankings_summary.csv` (17 countries).

| Country | n sites | K | Band A | Band B | Band C | Mean Jaccard | Min Jaccard |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AT | 6 | 6 | 0 | 0 | 1 | 0.9333 | 0.0 |
| BA | 6 | 6 | 0 | 0 | 1 | 0.9333 | 0.0 |
| BG | 7 | 7 | 1 | 0 | 0 | 0.9333 | 0.0 |
| BY | 2 | 2 | 1 | 0 | 0 | 0.9667 | 0.5 |
| CZ | 23 | 10 | 2 | 1 | 0 | 0.9333 | 0.0 |
| HR | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| HU | 10 | 10 | 1 | 0 | 0 | 0.9333 | 0.0 |
| LV | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| MD | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| ME | 1 | 1 | 1 | 0 | 0 | 0.9333 | 0.0 |
| MK | 4 | 4 | 1 | 0 | 0 | 0.9333 | 0.0 |
| PL | 41 | 13 | 2 | 2 | 1 | 0.9265 | 0.3077 |
| RO | 19 | 10 | 2 | 0 | 1 | 0.9236 | 0.4 |
| RS | 7 | 7 | 1 | 0 | 0 | 0.9524 | 0.2857 |
| SK | 5 | 5 | 1 | 0 | 0 | 0.9333 | 0.0 |
| TR | 106 | 32 | 5 | 1 | 2 | 0.8893 | 0.3824 |
| UA | 17 | 10 | 1 | 0 | 1 | 0.8218 | 0.0 |

## Country balance (baseline top-10 %)

| Country | Count |
| --- | ---: |
| PL | 82 |
| TR | 56 |
| RO | 40 |
| UA | 16 |
| CZ | 16 |
| BY | 8 |
| HU | 8 |

- Stage 1 country-balance report: max_share=**0.4** (flagged: **False**; threshold 40 %).

## Weight profiles persisted

Each stage writes into ``composite_rankings`` using these labels:

- `baseline` — original Phase 1.5 run (not written by this script).
- `w_<CAT>_plus_20` / `w_<CAT>_minus_20` — per-category weight perturbation for CAT ∈ {NH, HI, RI, EP, NS}.
- `w_swing` — swing-weight profile (rescale by observed 0–10 score range across the survivor pool, then renormalise).
- `mc_10000` — Monte Carlo @ N=10000.
- `threshold_plus_25` / `threshold_minus_25` — numeric context scaled by ±25 %.
- `country_balanced` — baseline clone used by the top-N check.

## Notes

- (no stage-level notes)

## Per-stage JSON

```json
[
  {
    "run_id": "p16_20260425T075225_014e4161",
    "pairs": 2904,
    "iterations": 10000,
    "preset_label": null,
    "weight_rows_persisted": 31944,
    "mc_rows_persisted": 2904,
    "country_balanced_rows_persisted": 2904,
    "threshold_rows_persisted": 5808,
    "country_report": {
      "total_sites": 208,
      "top_n": 20,
      "max_share": 0.4,
      "flagged": false,
      "country_counts": {
        "PL": 8,
        "RO": 8,
        "TR": 4
      }
    },
    "audit_path": "audit/post_processing/06_scoring/20260425_sensitivity_mc_10000.md",
    "mc_label": "mc_10000",
    "notes": []
  }
]
```
