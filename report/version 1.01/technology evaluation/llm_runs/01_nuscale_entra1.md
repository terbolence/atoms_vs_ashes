# LLM Evaluation Run — NuScale ENTRA1 (NPM, VOYGR-6 config)

```json
{
  "design_id": "nuscale_entra1",
  "design_name": "NuScale ENTRA1 (NuScale Power Module, 6 × 77 MWe VOYGR-6 config; 462 MWe gross)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "pass",
      "evidence": "NRC issued Standard Design Approval for the NuScale US460 (77 MWe NPM) on 29 May 2025 (NRC press release 25-033, https://www.nrc.gov/cdn/doc-collection-news/2025/25-033.pdf). CNCAN approved the project's Licensing Basis Document in 2023 (NEA SMR Dashboard 3rd Ed (2025), p. 198); IAEA SEED mission 2024 confirmed Doicești site meets international safety standards. SNN FID 12 Feb 2026 triggers formal CNCAN construction-permit dossier in Pre-EPC phase.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "pass",
      "evidence": "Standard LEU UO₂ <5% U-235 (Framatome HTP2 design; NEA Dashboard 3rd Ed p. 199). Framatome contract for fuel assemblies for the initial core and reloads (signed 2015 with Areva, now Framatome). No HALEU dependency. Framatome fabricates at facilities in the US and Europe.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "pass",
      "evidence": "Standard PWR fuel form (UO₂ <5%), compatible with Romania's National Strategy for Spent Fuel and Radioactive Waste Management (HG 1259/2011, ANDR-administered). Saligny LILW disposal facility (DFDSMA) accepts standard LWR ILW; Cernavodă dry cask precedent (CANDU spent fuel) demonstrates Romanian SF storage capability. Conditioning route demonstrated for PWR fuel.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "pass",
      "evidence": "NRC SDA issuance 29 May 2025 means a complete safety review including Level 1 and Level 2 PSA, severe accident analysis, and external hazards treatment (NRC US460 SDA project page, https://www.nrc.gov/reactors/new-reactors/advanced/who-were-working-with/applicant-projects/nuscale-us460). No unresolved generic safety issues remain in NRC docket. WENRA O1–O7 mapping for the 50 MWe variant published in 2020-2023 NRC SER carries forward to US460.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "pass",
      "evidence": "Design frozen as US460 reference (NRC SDA 29 May 2025). Doicești pre-EPC phase 2026-2027 finalises site-specific deviations from reference. SNN Board approved FID 12 Feb 2026 supports detailed engineering for COD 2033 of unit 1 (https://nuclearelectrica.ro/snn/en/2026/02/12/the-doicesti-small-modular-reactors-smr-project-obtains-the-final-investment-decision-and-enters-the-third-stage-of-development/).",
      "confidence": "direct_evidence"
    },
    "a6_site_fit": {
      "verdict": "caution",
      "evidence": "Doicești is a former coal site with constrained Argeș-basin water availability; CNCAN LBD allows multiple cooling options. Specific cooling configuration (river / hybrid / cooling tower) not finalised in public domain. NuScale supports hybrid mechanical-draft cooling tower variant (vendor_claim). Land take ~30-50 ha for VOYGR-6; transport envelope compatible with European road/rail. EPZ ≤ site boundary is vendor_claim pending CNCAN docketed decision.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "pass",
      "evidence": "SNN FID approved 12 Feb 2026 (USD 4.9B ±20-30% total project cost). Stage 3 (Pre-EPC) budget ~USD 600M for 15 months until mid-2027. Phased funding: only first 77 MWe module funded initially; remaining five contingent on first-unit performance (Power Magazine 2026-02). Romanian state backing + EU Just Transition Fund + Eximbank/EBRD instruments support cost-of-debt. Hinkley Point C and Paks II precedents for EU State-aid clearance available.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 4,
      "rationale": "PSAR-equivalent fully reviewed by NRC for SDA issuance (May 2025); deterministic + Level 1/2 PSA published; severe accident management documented in DCD. External hazards (seismic, flood, extreme weather, aircraft impact) explicitly treated. Source term independently challenged by NRC ACRS. Score not 5 because the SDA is for a generic site; site-specific Doicești hazards (Argeș flooding, Vrancea seismic zone) require CNCAN re-validation in Pre-EPC.",
      "evidence": "NRC US460 SDA decision 25-033 (29 May 2025); NEA Dashboard 3rd Ed p. 198-199.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 3,
      "rationale": "Detailed design complete (US460 SDA); FOAK procurement underway for Doicești (Doosan RPV; Doosan-Alleima SG tubes). However, no operating reference unit exists (Carbon-Free Power Project at Idaho cancelled Nov 2023 due to cost overruns). Doicești is the FOAK; multiple subsystems (e.g., natural-circulation primary, 12-NPM control room concept) still in qualification.",
      "evidence": "NRC SDA US460; CFPP cancellation announcement Nov 2023; NEA Dashboard 3rd Ed p. 198.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 3,
      "rationale": "Design freeze achieved; modular factory fabrication for NPM (Doosan, BWXT). Long-lead items contracted (RPV upper internals at Doosan since 2023). Doicești civil works to follow Pre-EPC. Not score 4-5 because Doicești is the first site to construct a VOYGR plant — constructability evidence is theoretical.",
      "evidence": "NEA Dashboard 3rd Ed p. 198; Doosan-Alleima SG tube order 2025.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 4,
      "rationale": "Mature supply chain via Framatome, Doosan Enerbility, BWXT, Sarens, Samsung C&T, PaR Systems, Concurrent Technologies. ENTRA1 selected for EU Industrial Alliance on SMRs Project-Working Group 2024. Sargent and Lundy for engineering; Enercon for licensing. Multi-source supply for safety-class items (e.g., Doosan + BWXT for forgings).",
      "evidence": "NEA Dashboard 3rd Ed pp. 198-199; ENTRA1 + EU SMR Alliance 2024.",
      "confidence": "direct_evidence"
    },
    "b5_fuel_qualification": {
      "score": 5,
      "rationale": "Standard LEU UO₂ HTP2 design at <5% U-235; HTP2 approved by NRC by incorporation by reference in 2023 final rule. Commercial fabrication at multiple non-Russian Framatome facilities (US, France). Fuel similar to operating commercial PWR fleet — no further qualification needed.",
      "evidence": "NRC final rule on 50 MWe NPM SDA (Feb 2023); NEA Dashboard 3rd Ed p. 199.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 4,
      "rationale": "Standard PWR LEU UO₂ spent fuel; conditioning route established via Cernavodă precedent (CANDU SF dry cask) and Saligny LILW pathway. Volume per MWh within EU LWR experience. Decommissioning cost basis published in NRC US460 SDA. ANDR programme supports standard LWR waste streams.",
      "evidence": "Romanian National Strategy 2014; NRC US460 SDA decommissioning section.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 3,
      "rationale": "Wet cooling baseline; hybrid mechanical-draft cooling tower variant available (vendor_claim). Land take ~30-50 ha for VOYGR-6 acceptable. Transport envelope: standard European road/rail-compatible NPM modules. EPZ ≤ site boundary is vendor_claim — CNCAN final EPZ decision pending. Not score 4-5 because dry/hybrid cooling option for VOYGR-6 not yet proven at scale and CNCAN EPZ ruling not docketed.",
      "evidence": "NuScale design control document (vendor_claim); Doicești CNCAN Licensing Basis Document 2023 (NEA Dashboard p. 198).",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 4,
      "rationale": "VOYGR multi-module configuration provides flexibility at plant level: each NPM can be independently shut down or load-followed (vendor_claim minimum stable load 20% of rated per module; ramp ~5%/min). Primary frequency control claimed but not independently demonstrated. Black-start capability via decay-heat removal not explicitly demonstrated.",
      "evidence": "NuScale design control document (vendor_claim); NRC SDA SER section on operations.",
      "confidence": "indirect_evidence"
    },
    "b9_security_safeguards": {
      "score": 4,
      "rationale": "NRC SDA includes physical protection plan and cyber architecture compliant with IEC 62645 (per US 10 CFR 73.55). Safeguards-by-design articulated for IAEA verification (international safeguards plan in DCD). Insider-threat mitigation in security plan section of NRC SER.",
      "evidence": "NRC US460 SDA SER security section; IAEA STR-387 framework alignment per vendor.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 4,
      "rationale": "Operator staffing concept compatible with NRC requirements (12-NPM 268-staff plant; 6-NPM proportionally smaller). SNN Cernavodă has experienced PWR/CANDU operator base for crew development. Training pipeline via NuScale E2 Centers (8 worldwide as of early 2025). Not score 5 because the multi-module shared-control-room concept is novel and CNCAN endorsement of staffing levels TBD.",
      "evidence": "NEA Dashboard 3rd Ed p. 199; NuScale E2 Centers programme.",
      "confidence": "indirect_evidence"
    },
    "b11_vendor_credibility": {
      "score": 4,
      "rationale": "NuScale Power + ENTRA1 Energy strategic alliance separates technology owner from project owner — clarifies long-term commercial responsibility. Doosan + Fluor + Framatome consortium provides EPC backing with European nuclear track record. Warranty and lifecycle support arrangements being negotiated in Doicești EPC. Not score 5 because NuScale's standalone balance sheet (post-Carbon-Free Power Project cancellation) is constrained; ENTRA1 SPV mitigates this.",
      "evidence": "NuScale 2025 financial filings; SNN FID press release 12 Feb 2026; NEA Dashboard p. 199.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 3.75,
  "b_aggregate_100pt": 75.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 3.0, "rationale": "Framatome (FR) fuel; Doosan-Alleima SG tubes (KR/SE); ENTRA1 selected for EU SMR Industrial Alliance Project-Working Group. Romanian content limited to BoP and civil works at Doicești; EU industrial role substantial but not yet ≥40% European content."},
    "c2_energy_sovereignty": {"modifier_pct": 5.0, "rationale": "Entire fuel cycle non-Russian: Cameco (CA) NUF6, Urenco (UK/NL/DE) enrichment, Framatome (FR/US) fabrication. No HALEU dependency. Best-in-class energy sovereignty for non-Russian fuel cycle."},
    "c3_cogeneration": {"modifier_pct": 1.0, "rationale": "Steam extraction technically feasible at NPM level; not the default Doicești configuration. GS Energy + Uljin County Korea MoU 2024 contemplates hydrogen production cogeneration but is not Romania-relevant."},
    "c4_fleet_deployability": {"modifier_pct": 3.0, "rationale": "Doicești as first European fleet unit; Polish Decision-in-Principle 2023 supports potential Polish deployment. Standardised VOYGR-6 design enables multi-site rollout but not yet contracted at multiple sites."},
    "c5_eu_exportability": {"modifier_pct": 3.0, "rationale": "Active engagement: RO (Doicești FID), PL (DiP). UK GBN eliminated 2024 (down from previous engagement). 2 EU states with binding commitments — below the +5% threshold of ≥3 EU states."},
    "c6_geopolitical_risk": {"modifier_pct": -2.0, "rationale": "US export-control friction for some safety-class components; mitigated by Doosan KR + Framatome FR multi-sourcing. NuScale's post-CFPP balance sheet adds modest commercial-risk exposure."},
    "c7_state_aid_risk": {"modifier_pct": -3.0, "rationale": "Doicești phased FID structure (1 module first, 5 contingent) may require EU State-aid review for top-up financing if first module commissioning is delayed. RAB-style structure not yet notified."}
  },
  "c_modifier_pct_total": 10.0,
  "final_score": 4.13,
  "verdict": "shortlist_primary",
  "verdict_drivers": [
    "All Tier A gates pass (only A6 caution = data-gap on cooling/EPZ specifics)",
    "Strongest jurisdictional + commercial position: NRC SDA 2025 + SNN FID 2026 + EU SMR Alliance",
    "Standard LEU UO₂ fuel via Framatome eliminates HALEU exposure",
    "Phased Doicești FID is a positive precedent but adds State-aid risk for top-up financing"
  ],
  "data_gaps_critical": [
    "Doicești final cooling configuration (river/hybrid/tower) not in public domain",
    "CNCAN docketed EPZ decision pending"
  ],
  "data_gaps_other": [
    "Detailed per-MWe overnight CAPEX disclosure for Doicești is opaque",
    "Learning-rate evidence for VOYGR fleet weak (no completed second plant)"
  ]
}
```

## Analyst Summary

**Headline finding.** NuScale ENTRA1 in the 6 × 77 MWe VOYGR-6 configuration is the **strongest candidate for first-of-a-kind European deployment** in the April 2026 evidence snapshot. The combination of (a) NRC US460 Standard Design Approval issued 29 May 2025, (b) the Doicești project's SNN Final Investment Decision on 12 February 2026, and (c) EU SMR Industrial Alliance Project-Working Group selection in 2024 produces a **Tier A profile that is the cleanest of the nine designs evaluated**: every gate passes, with only A6 (site-fit) at caution due to data gaps on cooling-tower specifics and CNCAN's pending EPZ decision. The final score of 4.13 places it in `shortlist_primary`.

**Key strengths.** First, **standard LEU UO₂ fuel via Framatome** eliminates the HALEU supply-chain exposure that is the binding constraint for four of the nine comparator designs. Second, the **NRC SDA + Romanian Licensing Basis Document approval (2023)** combination provides a defensible WENRA-mappable safety case for CNCAN. Third, **ENTRA1 Energy as a separate commercial vehicle** clarifies long-term commercial responsibility and partially insulates the Doicești project from NuScale Power Corporation's standalone balance-sheet exposure post-CFPP cancellation. Fourth, the **phased FID structure** (1 module first, 5 contingent) is a financially prudent risk-mitigation that most other developers cannot offer.

**Key weaknesses.** First, **Doicești is the first VOYGR plant in construction anywhere in the world** — there is no operating reference unit, and the Carbon-Free Power Project (Idaho) was cancelled in November 2023 due to cost overruns. Second, **per-MWe overnight CAPEX disclosure remains opaque**: the USD 4.9B headline mixes EPC, owner's costs, IDC, infrastructure, and contingency in unknown proportions. Third, the **vendor's claim of an EPZ ≤ site boundary** is not yet endorsed by CNCAN and is the largest single regulatory risk in the Pre-EPC phase.

**Most critical data gap.** The **Doicești final cooling configuration** — given the constrained Argeș-basin water availability — could materially affect both project CAPEX (hybrid cooling adds ~$200-400 M for VOYGR-6) and CNCAN site-suitability assessment. This should be the first item resolved in the Pre-EPC phase mid-2026.

**What would change the verdict.** The verdict would move from `shortlist_primary` to `shortlist_primary` (no change) if the cooling configuration is resolved cleanly. It could degrade to `shortlist_secondary` if either (i) the first-module commissioning is delayed beyond 2034 or (ii) per-module construction cost on the first three units exceeds USD 12 000/kWe. It would degrade to `pending` if CNCAN issues a docketed adverse EPZ ruling or rejects any safety topical that materially affects the SDA.
