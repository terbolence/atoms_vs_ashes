# Normalized Design Inputs — Power & Site Footprint

**Status:** LOCKED 2026-04-21 by project sponsor (user decision).
**Purpose:** single source of truth for `plant_net_mwe` and `site_area_hectares` across every downstream artefact: 9 YAMLs in `../economics/designs/`, economic model `smr_economics.py`, `comparison_report.md`, exported DOCX.
**Rule applied:** where a range was previously quoted, **the upper bound is used**. Where a vendor-disclosed figure was never given (Oklo), an explicit analyst inference is recorded and flagged.

## Decision table

| # | Design | Min. plant configuration | `plant_net_mwe` | `site_area_hectares` | Power source / rationale | Area source / rationale |
|---|--------|--------------------------|-----------------|----------------------|--------------------------|-------------------------|
| 1 | **NuScale ENTRA1** | 6 × 77 MWe (VOYGR-6, Doicești spec — project sponsor confirmed they will not build fewer) | **462** | **50** | NuScale 25-033 SDA (77 MWe/module); RoPower Doicești contract | NEA Dashboard + UAMPS / RoPower siting; upper bound of 30–50 ha quoted range |
| 2 | **GE Vernova Hitachi BWRX-300** | 1 × 300 MWe | **300** | **30** | BWRX-300 NRC pre-app + GEH disclosures | Single-unit compact BWR footprint (<30 ha) |
| 3 | **Rolls-Royce SMR** | 1 × 470 MWe | **470** | **50** | RR SMR GDA Step 2 (470 MWe nominal) | Upper bound of 30–50 ha range quoted in vendor materials |
| 4 | **Holtec SMR-300** | 1 × 300 MWe | **300** | **30** | Holtec SMR-300 NRC pre-app | Single-unit PWR compact footprint (<30 ha) |
| 5 | **Kairos KP-FHR** | 1 × 140 MWe KP-X (commercial) — Hermes 1/2 are 35 MWth demos, not representative | **140** | **50** | KP-X commercial design assumption (vendor has not disclosed) | Upper bound of vendor-quoted commercial FHR siting envelope |
| 6 | **X-energy Xe-100** | **4 × 80 MWe pack** — modules are technically independent, but NRC CP (Dow Seadrift + OPG Darlington) and every utility project to date are 4-pack submittals; single-module commercial deployment is not licensed anywhere | **320** | **80** | Dow Seadrift (4×80) + Darlington Xe-100 CP | NEA Dashboard / X-energy siting disclosures; upper bound for 4-pack envelope |
| 7 | **Oklo Aurora** | 1 × 75 MWe (Phase 2 upsized design) | **75** | **20** ⚠️ | Oklo Powerhouse Phase 2 (from 15–50 MWe original) | **analyst_inference** — Oklo has not published a site-area figure; 20 ha bounds a 75 MWe microreactor with EPZ buffer, auxiliary buildings and cooling envelope. Flagged in report. |
| 8 | **TerraPower Natrium** | 1 × 345 MWe baseload (500 MWe peak with molten-salt storage) | **345** | **80** | TerraPower Kemmerer CP; 345 MWe nameplate baseload | Kemmerer site disclosures; upper bound of 50–80 ha range |
| 9 | **EDF NUWARD** | 2 × 200 MWe (post-July-2024 reset — "higher value" rule; pre-reset 2×170 is obsolete) | **400** | **50** | EDF July-2024 design-reset disclosures; Joint Early Review Phase 2 | EDF NUWARD siting brief, 2-unit plant footprint |

## Notes on modularity (multi-module designs)

| Design | Modules per plant | Single-module deployable? | Why the chosen configuration? |
|--------|-------------------|---------------------------|-------------------------------|
| NuScale ENTRA1 | 6 | Technically yes (NRC SDA is per-module) | Project sponsor: **RoPower/Doicești contracts for 6 modules and will not build fewer**. 462 MWe used. |
| X-energy Xe-100 | 4 | Technically yes — but every NRC CP docketed and every utility commercial project uses the 4-pack. A 1×80 MWe commercial plant is **not currently licensable anywhere**. | Minimum commercially viable = 320 MWe. |
| Kairos KP-FHR | 1 (KP-X commercial) | Yes | Vendor KP-X commercial spec is single-unit 140 MWe. |
| NUWARD | 2 | No (post-reset architecture is inherently a pair) | 2×200 MWe = 400 MWe. |
| Natrium | 1 | n/a | Single 345 MWe unit. |

All other designs (BWRX-300, Rolls-Royce, Holtec, Oklo) are single-unit.

## How these values propagate

1. **`economics/designs/*.yaml`** — each design YAML has `plant_net_mwe` and a new field `site_area_hectares`.
2. **`economics/smr_economics.py`** — reads both fields, emits them in the summary CSV (`design_summary.csv`) and in the break-even CSV. `plant_net_mwe` is used for cumulative-MW calculations in Panel A / Panel B; `site_area_hectares` is reported but does not drive LCOE.
3. **`comparison_report.md`** — Section 1 has a "Plant footprint & power" summary table showing these exact numbers. Break-even table column "cumulative MW at n-units" uses `plant_net_mwe`.

## Change control

Any change to `plant_net_mwe` or `site_area_hectares` must (a) update this file, (b) update the corresponding YAML, (c) re-run `smr_economics.py`, (d) regenerate the report, (e) re-export DOCX. The economic model log prints a checksum of these two fields across all 9 designs at startup.
