# HALEU Global Supply Chain — April 2026 Snapshot

This snapshot is referenced by every non-LWR design corpus (Kairos, X-energy, Oklo, TerraPower) and feeds Hard Gate **A2 (Front-end fuel supply)** in `../smr_evaluation_methodology.md` v1.1.

## Summary verdict (April 2026)

The Western HALEU supply chain remains **structurally short of demand for the rest of this decade**. Designs that need first-core HALEU before ~2030 carry an A2 **caution**; designs that need it before 2028 (when the Russian-uranium import ban becomes total in the US) carry an A2 **fail** for any Romania COD-2033 plan that depends on a US-sourced HALEU supply chain.

## Producers and capacity

| Entity | Status (April 2026) | Capacity now | Capacity target | Source |
|--------|--------------------|--------------|-----------------|--------|
| Centrus Energy (American Centrifuge, Piketon OH) | Only NRC-licensed Western HALEU producer; received $900 M DOE task order in Jan 2026 | ~1 t HALEU/yr | 12 t/yr "sometime after 2030" | [Reuters 2026-02-24](https://www.reuters.com/business/energy/us-federal-grants-help-jumpstart-nuclear-fuel-supply-chain--reeii-2026-02-24/); [Centrus IR](https://investors.centrusenergy.com/news-releases/news-release-details/centrus-energy-secures-contract-extension-department-energy) |
| Urenco USA (Eunice NM) | Received NRC authorisation for LEU+ (up to 10% U-235); excluded from $2.7 B DOE task orders | LEU+ small quantities late 2025 | Commercial LEU+ mid-2026; +15% LEU capacity 2025–2027 | [Reuters 2026-03-24](https://www.reuters.com/business/energy/low-enriched-uranium-could-offer-faster-deployment-small-reactors--reeii-2026-03-24/) |
| General Matter (Paducah KY) | $900 M DOE task order Jan 2026 to develop new HALEU enrichment capacity | None yet | TBD post-2030 | [ANS 2026-01](https://www.ans.org/news/article-7652/doe-awards-27b-for-haleu-and-leu-enrichment/) |
| Orano Federal Services (Oak Ridge TN) | $900 M DOE task order Jan 2026 | None yet | TBD post-2030 | Same as above |
| Rosatom (Russia) | Historical Western HALEU monopoly; **total US import ban effective 2028** | Not available to US/EU | n/a | [Reuters 2026-02-24](https://www.reuters.com/business/energy/us-federal-grants-help-jumpstart-nuclear-fuel-supply-chain--reeii-2026-02-24/) |

## Demand vs supply (DOE projection)

- 2024 baseline: ~1 t HALEU/yr Western capacity (Centrus only).
- 2035 demand projection: **up to 50 t HALEU/yr** to supply announced advanced-reactor / SMR fleet.
- Gap: ~50× shortfall vs 2035 announced demand even if all four current US task-order recipients hit nameplate by 2030.

## DOE response

- **$2.7 billion** in HALEU + LEU enrichment task orders awarded January 2026 across Centrus, General Matter, Orano (Urenco excluded).
- **Centrus DOE production contract extended** through **30 June 2026**, with options for further extensions.
- **DOE Conditional commitments** to supply HALEU to five advanced-reactor developers (TerraPower, X-energy, Kairos, Oklo, Westinghouse).
- **HALEU Availability Program** continues under the Energy Act of 2020.

## Russian-fuel-free constraint (US Prohibiting Russian Uranium Imports Act)

- Limited waivers possible until **31 December 2027**.
- **Total prohibition effective 2028**.
- Implication for European deployment: even if Centrus-produced HALEU exists, US export-control timing is the binding constraint for any 2030+ first core for European fleets that source via the US.

## LEU+ (5–10% enrichment) as alternative pathway

Several developers are pivoting to LEU+ (5–10% U-235) which can be produced on existing centrifuge infrastructure with limited upgrades, in order to escape the HALEU bottleneck:

- **Urenco USA Eunice** has NRC authorisation for LEU+; commercial production targeted mid-2026.
- LEU+ does NOT remove the requirement for HALEU-fuelled designs (Natrium, Xe-100, KP-FHR-140, Aurora) — these designs need ≥10% to <20% U-235 in the active core.
- LEU+ pathway is therefore **not a substitute** for these four designs; it is only an option for designs that can be re-engineered around it.

## Mapping to evaluation criteria

| Design | Fuel form & enrichment | A2 verdict for Romania COD 2033 | Reasoning |
|--------|------------------------|----------------------------------|-----------|
| NuScale ENTRA1 | UO₂, < 5% U-235 | **pass** | Standard LEU; Framatome supply since SDA in 2025 |
| BWRX-300 | UO₂, < 5% U-235 | **pass** | Standard BWR fuel; Cameco/Urenco/Orano/GNF-A consortium contracted by OPG |
| Rolls-Royce SMR | UO₂, < 5% U-235 | **pass** | Standard PWR fuel; Westinghouse contracted |
| Holtec SMR-300 | UO₂, < 5% U-235 | **pass** | Standard PWR fuel; Framatome GAIA 17×17 |
| Kairos KP-FHR | TRISO pebbles, 10–20% U-235 (HALEU) | **caution** | LEFFF (Los Alamos) for Hermes; commercial KP-FHR-140 needs HALEU pipeline by ~2030 |
| X-energy Xe-100 | TRISO-X pebbles, 10–20% U-235 (HALEU) | **caution** | TX-1 fuel facility licence Feb 2026; ops mid-2028; ramp uncertain for European FOAK |
| Oklo Aurora | Metallic U-Zr alloy, 10–20% U-235 (HALEU) | **fail** | First fuel from EBR-II legacy (US only); A3F at INL not before 2030 for commercial-scale; pathway not transferable to Romania |
| TerraPower Natrium | Metallic U-Zr alloy, 10–20% U-235 (HALEU) | **fail** | Wyoming first core depends on Centrus + Framatome HALEU pilot; Russian-supply replacement needed; no European HALEU pipeline by 2033 |
| NUWARD | UO₂, < 5% U-235 | **pass** | Standard PWR fuel via Framatome (EDF subsidiary) |

## References saved in `../references/`

- (None of the HALEU references are saved as PDFs in `references/`; all citations are URL-based to live regulator and trade-press pages, captured in this snapshot.)
