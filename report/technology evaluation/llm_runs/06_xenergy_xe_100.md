# LLM Evaluation Run — X-energy Xe-100

```json
{
  "design_id": "xenergy_xe_100",
  "design_name": "X-energy Xe-100 (4 × 80 MWe = 320 MWe gross per standard reference plant)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "caution",
      "evidence": "Long Mott Energy CPA (Dow Seadrift) submitted March 2025; NRC accepted June 2025 — first Generation IV CPA accepted by NRC for commercial advanced reactor (NRC Long Mott project page). TRISO-X TF3 fuel facility CP issued 27 February 2026 — first new commercial reactor fuel facility licence in over 60 years (X-energy press 2026-02-27). CNSC VDR Phase 2 completed 2025. CNCAN engagement = none. Romanian licensability path not articulated.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "caution",
      "evidence": "TRISO-X HALEU pebbles. TRISO-X TF3 commercial fuel facility CP issued 27 Feb 2026 — operations target mid-2028 (X-energy press; WNN 2026-03). For European COD ~2032-2033, TF3 nameplate ramp uncertain. Centrus 12 MT/yr HALEU 'after 2030' (Reuters 2026-02-24). Caution rather than fail because TF3 is the most concrete HALEU pathway of any HALEU-dependent design — but European deployment by 2033 still uncertain.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "caution",
      "evidence": "TRISO spent fuel — Romania's National Strategy does not address this waste form. HTGR pebble-bed conditioning concept defined by US DOE; HTR-10/HTR-PM China precedent for pebble handling. Caution because conditioning concept exists but no Romanian pathway articulated.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "pass",
      "evidence": "Long Mott CPA accepted by NRC June 2025 = comprehensive safety review under way. Pebble-bed safety case mature thanks to HTR-10 (China) + HTTR (Japan) + HTR-PM (China) operational data. Inherent safety from large negative temperature coefficient + ceramic TRISO containment. CNSC VDR Phase 2 completed.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "caution",
      "evidence": "Xe-100 design frozen for Long Mott (Dow Seadrift) and AWS-Energy Northwest (Washington State); European deployment would require variant. Not a strict fail because the design is frozen for two US sites — caution because European-specific variant TBD.",
      "confidence": "indirect_evidence"
    },
    "a6_site_fit": {
      "verdict": "caution",
      "evidence": "4-module 320 MWe per plant — close to 462 MWe Doicești profile (would need 1.4 plants or one 6-module variant). High-temperature 750°C output requires different secondary loop than PWR. Cooling envelope different — air-cooling option theoretically possible due to high-temperature output. ~80 ha land take per 4-module plant. Insufficient European data on site envelope.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "caution",
      "evidence": "USD 500 M Amazon strategic investment (Oct 2024); DOE TF3 cooperative agreement USD 148.5 M (2024) + USD 50.5 M (Office of Clean Energy Demonstrations 2024); Long Mott Dow JV. AWS Master Agreement >5 GW by 2039. European financing structure unproven; X-energy balance sheet limited (start-up status).",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 4,
      "rationale": "Pebble-bed safety case based on HTR-10 + HTTR + HTR-PM operating fleet (HTR-PM commercial operation began Dec 2023 in Shidao Bay China). Long Mott CPA in NRC review = PSAR-equivalent. Inherent safety from negative temperature coefficient + ceramic TRISO containment. External hazards treated.",
      "evidence": "NRC Long Mott CPA acceptance Jun 2025; NEA Dashboard 3rd Ed p. 232; HTR-PM operational data.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 3,
      "rationale": "TRISO-X TF3 CP issued Feb 2026 — first commercial HALEU fuel facility licence in 60+ years. Long Mott still pre-construction; AWS-Energy Northwest in pre-application. HTR-PM China commercial pebble-bed operation provides some operating reference but for a different vendor's variant. Multiple novel subsystems but pebble-bed has Chinese operating-fleet precedent.",
      "evidence": "X-energy press 2026-02-27 (TRISO-X TF3 CP); Long Mott CPA acceptance Jun 2025.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 3,
      "rationale": "Modular factory fabrication; long-lead items in development. TRISO-X TF3 construction underway. Long Mott site preparation pending CP issuance (target Q1 2028). Construction philosophy articulated; modular factory assembly contemplated.",
      "evidence": "X-energy press releases 2025-2026; NEA Dashboard p. 232.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 3,
      "rationale": "TRISO-X TF3 single-source for HALEU pebbles (Oak Ridge TN; ops mid-2028). KHNP + Doosan + X-energy working group on Xe-100 deployment. Sealaska + Northwest Innovation Works + Iroquois Gas Transmission SMR Power Generation Hub (2025). Supplier ecosystem still being built.",
      "evidence": "NEA Dashboard 3rd Ed pp. 232-233.",
      "confidence": "indirect_evidence"
    },
    "b5_fuel_qualification": {
      "score": 2,
      "rationale": "HALEU TRISO pebbles. TRISO-X TF3 commercial CP issued Feb 2026; operations mid-2028. Lead test assemblies (LTAs) for Long Mott in development. Fuel qualification programme advanced but commercial fabrication facility under construction. Score 2 reflects HALEU dependency + commercial fabrication facility under construction.",
      "evidence": "X-energy press 2026-02-27; NEA Dashboard p. 233; HALEU snapshot.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 1,
      "rationale": "TRISO spent fuel; no European disposal pathway. Romanian National Strategy does not address pebble-bed waste. Higher volume per MWh than LWR (pebble waste higher volume than UO₂ assemblies despite lower fissile content). Conditioning concept defined by DOE; demonstration limited.",
      "evidence": "Romanian National Strategy 2014; HTR-PM China experience as indirect evidence.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 3,
      "rationale": "4-module compact reference plant; ~80 ha land take. High-temperature output requires different secondary loop. Air-cooling option theoretically possible. EPZ small claim (vendor_claim); not yet docketed by any European regulator.",
      "evidence": "X-energy design control document (vendor_claim); NRC Long Mott CPA siting section.",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 3,
      "rationale": "Continuous online refuelling provides operational flexibility. Vendor claims load-following but no quantitative envelope published for Xe-100 4-module plant. Score 3 reflects qualitative claim with limited quantitative substantiation.",
      "evidence": "X-energy design control document (vendor_claim).",
      "confidence": "data_gap"
    },
    "b9_security_safeguards": {
      "score": 3,
      "rationale": "NRC TF3 CP includes safeguards-by-design for fuel facility. Commercial reactor cyber TBD; IEC 62645 framework primarily LWR-derived. Pebble-bed online refuelling adds material-control complexity. Score 3 reflects partial articulation.",
      "evidence": "NRC TF3 CP SER (Feb 2026); IAEA STR-387 framework.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 3,
      "rationale": "Continuous-fuelling operating model unfamiliar to European operators. SNN Cernavodă PWR/CANDU operator base would require entirely new training. KHNP partnership provides some pebble-bed operating experience pathway.",
      "evidence": "X-energy disclosures; KHNP working group.",
      "confidence": "data_gap"
    },
    "b11_vendor_credibility": {
      "score": 4,
      "rationale": "X-energy + Amazon (USD 500 M strategic investment) + Dow + DOE = strong sponsor backing. KHNP partnership for Asian deployment. Long-term lifecycle support concept emerging. X-energy balance sheet limited but Amazon investment provides commercial scaling capacity.",
      "evidence": "Amazon press 2024-10-16; NEA Dashboard pp. 232-233.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 2.90,
  "b_aggregate_100pt": 58.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 0.0, "rationale": "No European industrial role articulated for Xe-100."},
    "c2_energy_sovereignty": {"modifier_pct": 0.0, "rationale": "TRISO-X TF3 US-only; HALEU pipeline allied (US/Centrus) but not European. C2 minimum 0."},
    "c3_cogeneration": {"modifier_pct": 5.0, "rationale": "High-temperature 750°C output is best-in-class for industrial heat / hydrogen / process steam. Dow Seadrift partnership demonstrates industrial cogeneration value at scale. Maximum +5%."},
    "c4_fleet_deployability": {"modifier_pct": 1.0, "rationale": "Amazon multi-site programme (>5 GW by 2039); first European site not identified. Dow Seadrift + AWS-Energy Northwest + KHNP = strong US/Asian pipeline; no European fleet."},
    "c5_eu_exportability": {"modifier_pct": 0.0, "rationale": "No EU-state engagement for Xe-100."},
    "c6_geopolitical_risk": {"modifier_pct": -5.0, "rationale": "TRISO-X TF3 single-source for fuel fabrication; HALEU pipeline US-only; export-control friction for HALEU and TRISO technology. Concentrated US dependency."},
    "c7_state_aid_risk": {"modifier_pct": -2.0, "rationale": "AWS Master Agreement is commercial-only; no European State-aid structure. EU State-aid path for hyperscaler-anchored SMR not yet structured."}
  },
  "c_modifier_pct_total": -1.0,
  "final_score": 2.87,
  "verdict": "pending",
  "verdict_drivers": [
    "Tier A1, A2, A3, A5, A6, A7 cautions — multiple data gaps for European deployment",
    "TRISO-X TF3 CP February 2026 is the most concrete HALEU pathway milestone of any HALEU-dependent design",
    "No European deployment pipeline (data-centre US-focused programme)",
    "Best-in-class cogeneration potential (750°C output) but not Romania-relevant"
  ],
  "data_gaps_critical": [
    "European deployment intent (no MoU with any EU state)",
    "TRISO-X TF3 nameplate ramp curve from mid-2028 first ops"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX for Xe-100 4-pack",
    "Quantitative grid-flexibility envelope",
    "Operating model and staffing for European deployment"
  ]
}
```

## Analyst Summary

**Headline finding.** X-energy Xe-100 is **pending verdict** with a final score of 2.87. The **27 February 2026 NRC Construction Permit for the TRISO-X TF3 fuel facility** — the first new commercial reactor fuel facility licence in over 60 years — is the most concrete HALEU-pathway milestone of any HALEU-dependent design and converts what would otherwise be an A2 fail into A2 caution. The **June 2025 NRC acceptance of the Long Mott Energy CPA** (Dow Seadrift) makes Xe-100 the first Generation IV commercial CPA in NRC review. But for **Romanian deployment** there is **no engagement of any kind**, and the Tier B aggregate is held down by HALEU dependency (B5) and TRISO waste-form fit (B6).

**Key strengths.** First, the **HTR-PM commercial pebble-bed operation in China** (operational since December 2023) provides operating-fleet precedent for the pebble-bed safety case, even though it is a different vendor's variant. Second, the **best-in-class high-temperature 750°C output** is excellent for industrial cogeneration — driving the maximum +5 % C3 modifier and explaining the Dow Seadrift partnership. Third, the **Amazon Master Agreement** (USD 500 M investment + >5 GW by 2039) provides the strongest hyperscaler offtake of any SMR design. Fourth, **TRISO-X TF3** unlocks the HALEU bottleneck for X-energy specifically — a structural advantage over Kairos, Oklo, and TerraPower.

**Key weaknesses.** First, **no European deployment pipeline of any kind** — TRISO waste-form fit (B6 = 1) is incompatible with the Romanian National Strategy as written. Second, **size mismatch** — 4-module 320 MWe plant ≠ 462 MWe Doicești profile. Third, **TRISO-X TF3 nameplate ramp from mid-2028 first ops** is the largest schedule risk; even with the CP in hand, mid-2028 to commercial-rate output is 2-4 years. Fourth, **continuous-online-refuelling operating model** is unfamiliar to European operators.

**Most critical data gap.** **European deployment intent** — without a single MoU with any EU state, the Xe-100 is not a credible Romanian deployment candidate even if all technical gates were met.

**What would change the verdict.** Verdict could move from `pending` to `shortlist_secondary` if (i) X-energy signs MoUs with ≥3 EU states (driving C5 to +5 %) AND (ii) TRISO-X TF3 ramps to commercial rate by 2030. Even then, the design is best characterised as **a niche industrial-cogeneration play**, not a baseload coal replacement for Romania.
