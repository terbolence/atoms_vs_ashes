# LLM Evaluation Run — Oklo Aurora Powerhouse

```json
{
  "design_id": "oklo_aurora",
  "design_name": "Oklo Aurora Powerhouse (15-75 MWe per module sodium-cooled fast reactor)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "fail",
      "evidence": "NRC denied original Combined Licence Application January 2022, citing 'missing information on a number of safety topics'. Licensing Project Plan submitted Dec 2024. CLA re-submission targeted mid-2026 (publicly slipping). DOE Site Use Permit at INL (2019); DOE design-and-engineering phase approval 2025. CNCAN engagement = none. NRC denial + no docketed CLA + no European engagement = no credible licensability path for Romania COD-2033.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "fail",
      "evidence": "Metallic U-Zr HALEU. First-core fuel from EBR-II legacy stock at INL — INL-only and non-transferable. Argonne HALEU recycle SER approved by NRC April 2025 (NEI Magazine 2025-04). A3F (Advanced Fuel Fabrication Facility) at INL: FEED studies underway 2025-2026 with Eitter & Schaper; CP not yet docketed; commercial-scale HALEU output target post-2030. No European pathway. Russian-sourced alternative banned 2028.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "fail",
      "evidence": "Metallic spent fuel from sodium fast reactor — no Romanian conditioning or disposal pathway. National Strategy does not address sodium-cooled fast reactor waste streams. Sodium coolant management waste streams (sodium-aerosol contamination) require novel handling.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "caution",
      "evidence": "NRC denial 2022 cited missing information on a number of safety topics (specifically: source-term, accident analyses, safeguards). LPP not yet a full safety case. Sodium fast reactor safety case must address sodium-fire and sodium-water interaction scenarios — not yet at NRC review depth.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "fail",
      "evidence": "Conceptual design only for commercial Aurora; CLA re-submission targeted mid-2026 but not yet docketed. No design freeze for any commercial unit. Doicești COD 2033 = strict fail; mid-2030s European deployment also not credible.",
      "confidence": "direct_evidence"
    },
    "a6_site_fit": {
      "verdict": "fail",
      "evidence": "15-75 MWe per module; would need ~30 modules of 15 MWe (or ~6 of 75 MWe) to match 462 MWe Doicești profile. Sodium fast reactor cooling envelope different from PWR. Per-module cost economics break down at this aggregation. Size mismatch with coal-replacement workhorse profile = strict fail.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "caution",
      "evidence": "USD 1.4 B+ private funding since 2014; NYSE listing May 2024 (DA Davidson SPAC merger). Switch master PPA Dec 2023 for up to 12 GWe by 2044; ≥14 GW total LOIs/PPAs (Switch, Wyoming Hyperscale, Equinix, Diamondback, Vertiv, KHNP, Centrus, RPower, Liberty Energy, Prometheus Hyperscale). No signed CLA = financing structure for commercial deployment unproven.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 2,
      "rationale": "NRC denial 2022 cited missing information on a number of safety topics = serious gap. LPP submitted Dec 2024 not a full safety case. Sodium fast reactor safety architecture not yet validated by any regulator at construction-permit level for Aurora variant.",
      "evidence": "NRC CLA denial January 2022; LPP submission December 2024.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 1,
      "rationale": "No operating reference; design conceptual; multiple novel subsystems on critical path simultaneously: sodium fast reactor + metallic HALEU fuel + 10-year+ core life + factory-built integrated SMR. Heat-pipe variant for low-end (~15 MWe) introduces additional novelty.",
      "evidence": "Oklo public design disclosures; NEA Dashboard 3rd Ed p. 184.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 2,
      "rationale": "No construction at any commercial unit. FEED studies only for A3F (HALEU fabrication facility). J.B. Henderson and Centerline Construction selected for site preparation studies. Construction philosophy articulated but unverified at scale.",
      "evidence": "NEA Dashboard 3rd Ed p. 184.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 2,
      "rationale": "Vendor claim of using 75% existing supply-chain components (vendor_claim). Westinghouse MoU; AtkinsRéalis MoU for UK; Korea Hydro and Nuclear Power MoU. Specific safety-class supplier commitments limited. Supply chain for sodium-fast-reactor specifically very thin.",
      "evidence": "NEA Dashboard 3rd Ed pp. 184-185 (vendor_claim).",
      "confidence": "indirect_evidence"
    },
    "b5_fuel_qualification": {
      "score": 1,
      "rationale": "Metallic U-Zr HALEU fuel. EBR-II legacy fuel for first core (INL-only). No commercial fabrication; A3F FEED studies only. Lead test assemblies for sodium fast reactor not yet inserted in commercial reactor. Fuel form qualification not yet at lead-test-assembly stage in commercial conditions.",
      "evidence": "NEA Dashboard 3rd Ed p. 185; HALEU snapshot.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 1,
      "rationale": "Metallic spent fuel from sodium fast reactor — no Romanian pathway. Sodium-coolant waste streams require novel handling. No conditioning/disposal route articulated for European operator. Lowest possible score.",
      "evidence": "Romanian National Strategy 2014; Oklo public technical disclosures.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 2,
      "rationale": "Compact units; multi-module siting unproven; size mismatch with coal-site profile. INL site only for FOAK. Cooling envelope for sodium fast reactor different from PWR. Land take per MWe high due to module-level redundancy.",
      "evidence": "Oklo design disclosures; NEA Dashboard p. 184.",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 3,
      "rationale": "Vendor claims dispatchable but no quantitative envelope published. Sodium fast reactor architecture supports passive cool-down. 10-year+ core life means refuelling-driven grid availability is exceptional but flexibility envelope unclear.",
      "evidence": "Oklo public design disclosures (vendor_claim).",
      "confidence": "data_gap"
    },
    "b9_security_safeguards": {
      "score": 2,
      "rationale": "NRC denial 2022 cited safeguards among issues. Safeguards-by-design partially articulated. Cyber per IEC 62645 not specifically articulated for sodium fast reactor.",
      "evidence": "NRC CLA denial January 2022 SER.",
      "confidence": "direct_evidence"
    },
    "b10_operating_model": {
      "score": 2,
      "rationale": "Operating model for sodium fast reactor unfamiliar to European operators. Vendor claims minimal staffing for autonomous operation (vendor_claim) — not yet accepted by any regulator. SNN Cernavodă has zero sodium fast reactor experience.",
      "evidence": "Oklo public disclosures (vendor_claim).",
      "confidence": "data_gap"
    },
    "b11_vendor_credibility": {
      "score": 3,
      "rationale": "NYSE listed May 2024; Sam Altman board chair; Switch + Wyoming Hyperscale + 14 GW LOIs offtake portfolio strong. DOE backing. Vendor balance sheet adequate post-IPO; commercial scaling capability unproven. Lifecycle support concept for 60-year asset not yet structured.",
      "evidence": "Oklo NYSE filings; offtake LOI portfolio.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 1.75,
  "b_aggregate_100pt": 35.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 0.0, "rationale": "No European industrial role for Aurora."},
    "c2_energy_sovereignty": {"modifier_pct": 0.0, "rationale": "HALEU pipeline US-only via Centrus + EBR-II legacy stock at INL. No European industrial sovereignty."},
    "c3_cogeneration": {"modifier_pct": 1.0, "rationale": "Theoretical industrial heat extraction at 480°C; not articulated as a commercial use case for any signed offtake."},
    "c4_fleet_deployability": {"modifier_pct": 0.0, "rationale": "No European fleet pipeline."},
    "c5_eu_exportability": {"modifier_pct": 0.0, "rationale": "No EU-state engagement (UK MoU via AtkinsRéalis is industrial, not state-led)."},
    "c6_geopolitical_risk": {"modifier_pct": -8.0, "rationale": "US-INL legacy fuel single-source; A3F is INL-only; export-control friction for HALEU and metallic fuel technology. Most concentrated US dependency of any of the 9 designs."},
    "c7_state_aid_risk": {"modifier_pct": 0.0, "rationale": "No European structure to assess."}
  },
  "c_modifier_pct_total": -7.0,
  "final_score": 1.63,
  "verdict": "eliminated",
  "verdict_drivers": [
    "A1, A2, A3, A5, A6 fails — multiple structural barriers to Romanian deployment",
    "NRC denial 2022 + no docketed CLA = no credible licensing path",
    "Size mismatch with 462 MWe Doicești profile (would need ~30 modules)",
    "EBR-II legacy fuel pathway is INL-only and non-transferable"
  ],
  "data_gaps_critical": [
    "Aurora-INL CLA re-submission docketing date",
    "A3F (Advanced Fuel Fabrication Facility) CP application docketing"
  ],
  "data_gaps_other": [
    "Per-module overnight CAPEX disclosure",
    "European deployment intent (zero MoU with any EU state)",
    "Operating model staffing endorsement by any regulator"
  ]
}
```

## Analyst Summary

**Headline finding.** Oklo Aurora is **eliminated** for Romanian deployment by **A1, A2, A3, A5, and A6 failures**. The combination of (a) NRC denial of the 2022 CLA, (b) the EBR-II legacy fuel pathway being INL-only and non-transferable, (c) absence of any docketed commercial CLA as of April 2026 with vendor schedule slipping, and (d) module size mismatch with the Doicești 462 MWe coal-replacement profile makes Aurora a **US-only data-centre play in the April 2026 snapshot** — not a credible European coal-replacement candidate at any timeline.

**Key strengths.** First, the **NYSE listing (May 2024)** and the **Switch + Wyoming Hyperscale + 14 GW LOI portfolio** make Oklo the most commercially aggressive sodium-fast-reactor vendor and gives it a balance sheet that exceeds Kairos's. Second, **Sam Altman's board involvement** and the data-centre offtake portfolio reflect a serious commercial strategy. Third, **NRC's April 2025 SER approval of Argonne's HALEU recycle process** is a real (if narrow) regulatory milestone for the EBR-II fuel pathway. Fourth, the **10-year+ core life** would, if validated, be a substantial operating-cost advantage.

**Key weaknesses.** First, the **NRC denial of the 2022 CLA cited missing information on safety topics** — this is the only outright NRC denial of any of the 9 designs evaluated, and the LPP (Dec 2024) does not yet replace it with a full safety case. Second, the **size mismatch** — Aurora at 15-75 MWe per module would require ~30 modules at 15 MWe (or 6 at 75 MWe) to match the Doicești profile, multiplying licensing and siting cost. Third, the **EBR-II legacy fuel** is the world's most constrained HALEU pathway — limited stockpile, INL-only, non-transferable. Fourth, the **C6 modifier of −8 %** reflects the most concentrated US-jurisdiction dependency of any of the 9 designs.

**Most critical data gap.** The **Aurora-INL CLA re-submission docketing date** — vendor states mid-2026 but the publicly-known schedule has been slipping. Without a docketed CLA, there is no commercial design at construction-permit-application maturity.

**What would change the verdict.** Even with **NRC docketing of the CLA, A3F CP application, and a binding HALEU commitment** that satisfies A2, the **size mismatch** and **A3 (waste pathway)** failures would keep Aurora at `pending` at best — not `shortlist_secondary`. Aurora is best characterised as a **US-only data-centre / off-grid industrial play**, not a coal-replacement workhorse.
