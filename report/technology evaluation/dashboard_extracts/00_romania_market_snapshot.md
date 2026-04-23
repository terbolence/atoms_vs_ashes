# Romania Electricity Market — April 2026 Snapshot

This snapshot feeds the **economic model** in `../economics/` and Tier B criterion **B7 (Economic competitiveness)** in `../smr_evaluation_methodology.md` v1.1. All prices are nominal-year EUR/MWh unless stated.

## OPCOM Day-Ahead Market (DAM) — wholesale electricity prices

The OPCOM DAM weighted-average wholesale price is the primary benchmark for any Romanian SMR LCOE comparison.

| Period | Weighted-avg EUR/MWh | Arithmetic-avg EUR/MWh | Source |
|--------|---------------------|------------------------|--------|
| 2024 (annual) | 103.51 | n/a | [OPCOM 2025 highlights](https://www.opcom.ro/anunturi-stiri-comunicate-tip/en/1447/1) |
| 2025 (annual) | 114.21 | 108.16 | [OPCOM 2025 highlights](https://www.opcom.ro/anunturi-stiri-comunicate-tip/en/1447/1); also `OPCOM_2025_Annual_Market_Report.pdf` in `../references/` |
| Mar 2025 | n/a | 106.36 | [CBAM 2025-03](https://cbam.rs/romania-electricity-prices-on-opcom-market-experience-significant-changes-in-march-2025/) |
| Aug 2025 | see monthly report | n/a | `OPCOM_Monthly_Aug2025.pdf` in `../references/` |
| Dec 2024 | 141.08 | n/a | `OPCOM_Monthly_Dec2025.pdf` (comparison row) |
| Dec 2025 | 117.64 | n/a | `OPCOM_Monthly_Dec2025.pdf` |
| Jan 2026 | 150.51 | n/a | [Serbia-Energy 2026-01](https://serbia-energy.eu/romania-opcom-day-ahead-power-prices-rise-to-e150-5-mwh-in-january-2026-amid-higher-trading-value/) |

### Benchmark bands used in the economic model

- **DAM mid-2025**: ~110 EUR/MWh (rounded annual weighted average).
- **DAM 2024–2025 corridor**: 100–120 EUR/MWh.
- **DAM stress band 2025–2026**: 100–150 EUR/MWh (captures monthly excursions).

## EU Contract-for-Difference (CfD) reference points

Because OPCOM DAM does not capture the long-term certainty an SMR investor needs, we also benchmark against EU CfD strike prices.

| Project | Strike price (nominal) | Indexation | Source |
|---------|------------------------|-----------|--------|
| Hinkley Point C (UK) | £92.50/MWh in 2012 prices → ~**£133/MWh** late 2025; projected **~£150/MWh by 2030** (~178 EUR/MWh at 1.18 EUR/GBP) | RPI-indexed | [Guardian 2025-11-28](https://www.theguardian.com/uk-news/2025/nov/28/uk-energy-bill-payers-edf-hinkley-point-c-sizewell-c) |
| Sizewell C (UK) | Nuclear levy / RAB model — strike-price economics differ from Hinkley CfD | Pending | Same as above |
| Rolls-Royce SMR LCOE target (UK) | **< £70/MWh (~83 EUR/MWh)** — vendor target, not a contracted strike | n/a | [NucNet 2025-03-07](https://www.nucnet.org/news/analysis-shows-competitive-lcoe-target-for-small-modular-reactors-7-3-2025) |

### Benchmark bands used in the economic model

- **CfD low (vendor target)**: 80–90 EUR/MWh — Rolls-Royce SMR public LCOE goal.
- **CfD high (Hinkley indexed)**: 150–180 EUR/MWh — actual UK new-nuclear contract economics today.

## Avoided-coal LCOE (proxy for coal-to-nuclear conversion value)

For the Doicești project specifically, the relevant counterfactual is the LCOE of CE Oltenia / Complexul Energetic Oltenia coal generation, including the rising EU ETS carbon cost.

| Component (typical Romanian lignite plant, 2024-2025 estimate) | Value | Notes |
|---------------------------------------------------------------|-------|-------|
| Lignite fuel cost | ~25 EUR/MWh | Romanian extraction cost |
| Variable O&M | ~5 EUR/MWh | |
| Fixed O&M | ~12 EUR/MWh | Aged plant |
| EU ETS allowance pass-through (90 EUR/t CO₂ × ~1.05 t CO₂/MWh) | ~95 EUR/MWh | EUA price end-2025 |
| **Avoided-coal LCOE incl. carbon** | **~135-145 EUR/MWh** | Sensitivity: ±20 EUR/MWh on EUA price |
| Avoided-coal LCOE excl. carbon | ~40-45 EUR/MWh | Without ETS pass-through |

### Benchmark bands used in the economic model

- **Avoided-coal incl. ETS at EUA = 90 EUR/t**: 130–150 EUR/MWh.
- **Avoided-coal incl. ETS at EUA = 60 EUR/t**: 105–125 EUR/MWh (downside sensitivity).
- **Avoided-coal incl. ETS at EUA = 130 EUR/t**: 160–180 EUR/MWh (upside sensitivity).

## Macro inputs

- **Currency**: EUR; reference EUR/USD ~1.08 (Q1 2026); EUR/GBP ~1.18.
- **Romanian sovereign rating**: BBB-/Baa3 (investment grade); cost-of-debt for SNN is materially supported by Eximbank, EBRD, and EU Just Transition Fund instruments.
- **WACC assumptions for the model**:
  - Base case: **8.0%** real (mixed sovereign + EU green-finance instruments).
  - Low case (full EU green CfD + Just Transition support): **6.0%**.
  - High case (commercial-only project finance, no concessional support): **10.0%**.
- **Construction inflation index**: 3.5% nominal (EU CPI projection); the model uses real EUR throughout.

## Mapping to economic model inputs

The numbers above flow directly into `common_assumptions.yaml` as:

```yaml
benchmarks:
  romania_dam_eur_mwh:
    low: 100
    mid: 110
    high: 150
  uk_cfd_eur_mwh:
    rolls_royce_target: 83
    hinkley_indexed_2025: 158
    hinkley_indexed_2030: 178
  avoided_coal_incl_ets_eur_mwh:
    low_eua_60: 115
    base_eua_90: 140
    high_eua_130: 170
```

## References saved in `../references/`

- `OPCOM_2025_Annual_Market_Report.pdf` — OPCOM Annual Report 2025 (full year statistics, English version)
- `OPCOM_Monthly_Dec2025.pdf` — December 2025 monthly market report
- `OPCOM_Monthly_Aug2025.pdf` — August 2025 monthly market report
