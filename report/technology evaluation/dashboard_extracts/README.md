# SMR Evidence Corpora — Dashboard Extracts

This folder contains the structured evidence corpus used to feed the LLM evaluation runs in `../llm_runs/` and the economic model in `../economics/`. Every claim used in `../comparison_report.md` is traceable to one of these files.

## Structure of each design corpus

Every per-design `.md` file follows the same five-section template:

1. **Identity & headline parameters** — vendor, capacity, fuel form, coolant, primary jurisdiction.
2. **NEA SMR Dashboard 3rd Edition extract** — verbatim text from `../references/The NEA Small Modular Reactor Dashboard_ Third Edition.pdf` (NEA No. 7737, © OECD 2025) for that design's six readiness dimensions: Licensing, Siting, Financing, Supply chain, Engagement, Fuel.
3. **April 2026 evidence snapshot** — newer items not in the NEA Dashboard, drawn from web research and primary regulator pages, with URLs.
4. **Regulator docket / equivalent status** — what is filed, what is approved, what is pending; cited to NRC, ONR, ASNR, CNCAN, CNSC pages.
5. **Open data gaps for this design** — explicitly listed for the LLM run's `data_gap` confidence tag.

## Cross-cutting snapshots

- `00_haleu_supply_snapshot.md` — global HALEU supply chain status (Centrus, Urenco, DOE, Russian ban) — applies to Kairos, X-energy, Oklo, TerraPower.
- `00_romania_market_snapshot.md` — OPCOM Day-Ahead Market prices, EU CfD comparators, avoided-coal LCOE — feeds the economic model.

## Citation rules

- NEA verbatim quotes are marked with `> ` blockquote style and cite "NEA Dashboard 3rd Ed (2025), p. <page>".
- Web-sourced facts cite the URL inline.
- All dollar figures are nominal-year unless explicitly converted to 2025 USD (`USD 2025`).

## Designs covered

| # | File | Vendor | Design |
|---|------|--------|--------|
| 1 | `01_nuscale_entra1.md` | NuScale Power / ENTRA1 Energy | NPM, VOYGR-6 (462 MWe gross) |
| 2 | `02_bwrx_300.md` | GE Vernova Hitachi Nuclear Energy | BWRX-300 (300 MWe net) |
| 3 | `03_rolls_royce_smr.md` | Rolls-Royce SMR | RR SMR (470 MWe net) |
| 4 | `04_holtec_smr_300.md` | Holtec International | SMR-300 (300 MWe net) |
| 5 | `05_kairos_kp_fhr.md` | Kairos Power | KP-FHR Hermes 1, Hermes 2, KP-FHR-140 |
| 6 | `06_xenergy_xe_100.md` | X-energy | Xe-100 (4×80 MWe = 320 MWe gross/plant) |
| 7 | `07_oklo_aurora.md` | Oklo | Aurora Powerhouse (15-75 MWe) |
| 8 | `08_terrapower_natrium.md` | TerraPower | Natrium (345 MWe + storage 500 MWe peak) |
| 9 | `09_nuward.md` | EDF / NUWARD | NUWARD SMR (post-2024 reset, 2×200 MWe = 400 MWe) |
