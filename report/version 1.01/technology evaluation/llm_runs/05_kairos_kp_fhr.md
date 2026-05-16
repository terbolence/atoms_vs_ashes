# LLM Evaluation Run — Kairos Power KP-FHR (Hermes 1, Hermes 2, KP-FHR-140)

```json
{
  "design_id": "kairos_kp_fhr",
  "design_name": "Kairos Power KP-FHR — Hermes 1 (35 MWth demo) / Hermes 2 (50 MWe demo) / KP-FHR-140 (commercial)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "caution",
      "evidence": "Hermes 1 NRC Construction Permit issued December 2023 (research-reactor pathway under 10 CFR 50.21(c)). Hermes 2 NRC CP issued November 2024 (first power-producing Gen IV reactor CP from NRC). Commercial KP-FHR-140 has no NRC CP application docketed. CNCAN engagement = none. Romanian licensability path not articulated. Caution rather than fail because Hermes 2 CP and NRC engagement establish licensability for the demonstration; commercial KP-FHR-140 is the gating issue.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "fail",
      "evidence": "TRISO pebble fuel at 10-20% U-235 (HALEU). LEFFF (Los Alamos) for Hermes 1+2 initial cores — lab scale, US-only. Urenco MoU 2023 for KP-FHR commercial HALEU is non-binding. As of April 2026: Centrus 12 MT/yr commercial HALEU production target 'after 2030' (Reuters 2026-02-24); Russian HALEU import ban total 2028. Designs requiring HALEU first-core delivery before ~2030 fail A2. Romania COD-2033 European deployment of commercial KP-FHR-140 = fail.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "caution",
      "evidence": "TRISO spent fuel — Romania's National Strategy (HG 1259/2011) does not address this waste form. Conditioning concept for TRISO defined by US DOE but not demonstrated at scale. Caution because the conditioning concept exists and is conceptually compatible with deep geological disposal — but no Romanian pathway articulated.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "caution",
      "evidence": "Hermes 1 CP issued Dec 2023 = NRC reviewed safety case for the demo. Hermes 2 CP issued Nov 2024. Pebble-bed FHR safety case still under construction for commercial KP-FHR-140 — multi-pebble fluoride salt + TRISO has no operating reference fleet. FLiBe coolant chemistry and tritium control have known engineering challenges; safety case for commercial-scale not yet in NRC review.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "fail",
      "evidence": "Hermes 1+2 are demonstration reactors under research-reactor pathway. Commercial KP-FHR-140 design (140 MWe twin-module plant) not yet at construction-permit-application maturity. No NRC CP application docketed for commercial variant. Doicești COD 2033 = fail; mid-2030s commercial KP-FHR European deployment also unrealistic.",
      "confidence": "direct_evidence"
    },
    "a6_site_fit": {
      "verdict": "caution",
      "evidence": "Hermes 1 = 35 MWth (no electrical output); Hermes 2 = 50 MWe; commercial KP-FHR-140 = 140 MWe. To match 462 MWe Doicești coal-replacement profile would need ~3.3 KP-FHR-140 plants = greater siting/licensing cost. High-temperature 650°C output supports cogeneration. Insufficient European data on cooling envelope for FHR at scale.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "caution",
      "evidence": "USD 303 M DOE Advanced Reactor Demonstration Program; Google Master Plant Development Agreement Oct 2024 for 500 MW by 2035 (USD value undisclosed); TVA PPA Aug 2025 for up to 50 MW from Hermes 2. No European financing structure. Kairos Power balance sheet limited (start-up).",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 3,
      "rationale": "Hermes 1 CP issued = Level 1 PSA equivalent for demo. Hermes 2 CP issued = power-producing demo safety case. Commercial KP-FHR-140 safety case at conceptual stage. FLiBe coolant + TRISO + HALEU = three novel subsystems; full-scale safety case still pending.",
      "evidence": "NRC Hermes 1 CP Dec 2023; NRC Hermes 2 CP Nov 2024; Kairos Power technical disclosures.",
      "confidence": "indirect_evidence"
    },
    "b2_maturity_foak": {
      "score": 2,
      "rationale": "Hermes 1 not yet operating (foundation work in progress April 2026; first operations targeted 2027-2028). Commercial KP-FHR-140 conceptual; multiple novel subsystems on critical path simultaneously: fluoride salt (FLiBe) coolant, TRISO pebble fuel, HALEU, online refuelling. FHR has no operating reference globally.",
      "evidence": "Kairos Tennessee location page; Hermes 2 ground-breaking April 2026.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 3,
      "rationale": "Construction underway at Hermes 1 (drilled piers, seismic isolators); Hermes 2 ground broken 17 April 2026. Salt Production Facility at Albuquerque under construction since 2024. Materion produced 14 t FLiBe by late 2023. ETU 2.0 reactor vessel completed 2025. Construction philosophy articulated but unproven at commercial scale.",
      "evidence": "NEA Dashboard 3rd Ed pp. 166-167; Kairos press releases 2024-2026.",
      "confidence": "direct_evidence"
    },
    "b4_supply_chain": {
      "score": 3,
      "rationale": "Salt Production Facility (Albuquerque); Materion + Kairos partnership for FLiBe; Barnard Construction. Most components in-house at Kairos Albuquerque campus. KP-OMADA advisory group of North American utilities. Limited multi-source for safety-class items; FHR-specific supply chain still being built.",
      "evidence": "NEA Dashboard 3rd Ed pp. 166-167.",
      "confidence": "indirect_evidence"
    },
    "b5_fuel_qualification": {
      "score": 1,
      "rationale": "Novel TRISO pebble fuel at HALEU enrichment for FHR application. LEFFF (Los Alamos) for Hermes lab-scale fabrication only. Urenco MoU 2023 non-binding. No commercial fabrication facility for KP-FHR pebbles. Fuel qualification not yet at lead-test-assembly stage in commercial reactor.",
      "evidence": "NEA Dashboard 3rd Ed p. 167; HALEU snapshot in dashboard_extracts/00_haleu_supply_snapshot.md.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 1,
      "rationale": "TRISO spent fuel — no European disposal pathway; Romanian National Strategy does not address this waste form. Salt-coolant waste streams (tritium-contaminated FLiBe) require novel conditioning. No conditioning/disposal route articulated for European operator.",
      "evidence": "Romanian National Strategy 2014; Kairos Power public technical disclosures.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 3,
      "rationale": "Compact reactor; 35 MWth Hermes 1 small footprint; 140 MWe commercial twin-module ~50 ha. Air cooling theoretically possible due to high-temperature output; insufficient European data. EPZ small claim is vendor_claim.",
      "evidence": "Kairos Power design disclosures (vendor_claim).",
      "confidence": "data_gap"
    },
    "b8_grid_flexibility": {
      "score": null,
      "rationale": "No quantitative grid-services envelope published for commercial KP-FHR-140. Online refuelling provides operational flexibility but not quantified for grid-frequency response. Data gap.",
      "evidence": "Kairos Power public technical disclosures (no quantitative grid-flexibility envelope).",
      "confidence": "data_gap"
    },
    "b9_security_safeguards": {
      "score": 3,
      "rationale": "NRC CPs for Hermes include physical protection plans. Cyber per IEC 62645 not yet articulated for HTGR-FHR — IEC framework primarily LWR-derived. Safeguards-by-design partially integrated. Insider-threat mitigation per US 10 CFR 73.55.",
      "evidence": "NRC Hermes CPs SER security sections.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 3,
      "rationale": "Operating model for FHR not yet demonstrated. Staffing model for first-of-kind FHR unclear. SNN Cernavodă PWR/CANDU operator base would require entirely new training pipeline. KP-OMADA utility advisory group nascent.",
      "evidence": "Kairos Power public disclosures; KP-OMADA membership.",
      "confidence": "data_gap"
    },
    "b11_vendor_credibility": {
      "score": 3,
      "rationale": "Kairos Power = SPV start-up. Google Master Plant Development Agreement Oct 2024 for 500 MW = strong but data-centre-customer-only. TVA PPA Aug 2025 for 50 MW. No European EPC partner. DOE USD 303 M backing. Vendor balance sheet limited; lifecycle support concept for 60-year asset not yet structured.",
      "evidence": "Kairos Power 2024-2025 disclosures; Google + TVA agreements.",
      "confidence": "indirect_evidence"
    }
  },
  "b_aggregate_5pt": 2.30,
  "b_aggregate_100pt": 46.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 0.0, "rationale": "No European industrial role articulated for KP-FHR."},
    "c2_energy_sovereignty": {"modifier_pct": 0.0, "rationale": "HALEU pipeline US-only via Centrus/General Matter/Orano (with DOE task orders); no Russian dependency but no European industrial sovereignty either. C2 minimum 0."},
    "c3_cogeneration": {"modifier_pct": 3.0, "rationale": "High-temperature 650°C output is excellent for industrial heat. Strong cogeneration potential for hydrogen, district heat, industrial process steam. Not maximum +5% because no signed European cogeneration LoI."},
    "c4_fleet_deployability": {"modifier_pct": 0.0, "rationale": "No European fleet pipeline. Google PPA is data-centre-specific."},
    "c5_eu_exportability": {"modifier_pct": 0.0, "rationale": "No EU-state engagement."},
    "c6_geopolitical_risk": {"modifier_pct": -8.0, "rationale": "HALEU pipeline single-source US (Centrus/General Matter/Orano); Russian alternative banned 2028; export-control friction for HALEU and TRISO technology. Concentrated geopolitical exposure to US."},
    "c7_state_aid_risk": {"modifier_pct": 0.0, "rationale": "No European structure to assess."}
  },
  "c_modifier_pct_total": -5.0,
  "final_score": 2.19,
  "verdict": "eliminated",
  "verdict_drivers": [
    "A2 fail: HALEU dependency for commercial KP-FHR before 2030 not credible for Romania COD-2033",
    "A5 fail: Commercial KP-FHR-140 design not yet at NRC CP-application maturity",
    "Multiple novel subsystems (FLiBe coolant + TRISO pebbles + HALEU + online refuelling) on critical path simultaneously",
    "Strong cogeneration potential (650°C output) but no European deployment pipeline"
  ],
  "data_gaps_critical": [
    "Commercial KP-FHR-140 NRC CP application docketing schedule",
    "European fuel cycle pathway for TRISO HALEU pebbles"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX for commercial KP-FHR-140",
    "Operating model and staffing for European deployment",
    "Cyber-architecture framework for FHR (IEC 62645 LWR-derived)"
  ]
}
```

## Analyst Summary

**Headline finding.** Kairos KP-FHR is **eliminated** for Romanian deployment by **A2 (HALEU front-end fuel supply) and A5 (design freeze)** failures. The Hermes 1 demonstration reactor is making good engineering progress (NRC CP issued December 2023; foundation work in 2025-2026), and Hermes 2 broke ground 17 April 2026 as the first power-producing Generation IV reactor in NRC-permitted construction. But the **commercial KP-FHR-140 design is conceptual** — no NRC CP application has been docketed — and **first commercial HALEU deliveries before ~2030 are not credible** for any non-US deployment given the Centrus/General Matter/Orano production trajectory.

**Key strengths.** First, the **Google Master Plant Development Agreement** (October 2024 for 500 MW by 2035) and the **TVA PPA** (August 2025 for 50 MW) make Kairos the **only Generation IV vendor with both a hyperscaler offtake and a regulated-utility offtake**. Second, the **high-temperature 650°C output** is excellent for industrial cogeneration, hydrogen production, or district heat — driving the +3 % C3 modifier. Third, the **NRC's research-reactor pathway** for Hermes 1+2 has unlocked a faster regulatory cycle than the commercial pathway and is delivering real progress.

**Key weaknesses.** First, **multiple novel subsystems on critical path simultaneously** — FLiBe fluoride-salt coolant + TRISO pebble fuel + HALEU enrichment + online refuelling — make B2 (technology maturity) the lowest of any active design. Second, **HALEU dependency before 2030** (see `dashboard_extracts/00_haleu_supply_snapshot.md`) closes the Romania COD-2033 window. Third, **size mismatch with Doicești-style 462 MWe coal-replacement profile** would require ~3.3 KP-FHR-140 plants — multiplying siting and licensing cost. Fourth, **no European deployment pipeline** of any kind.

**Most critical data gap.** The **commercial KP-FHR-140 NRC CP application docketing schedule** is the gating item. Until this is filed and accepted, the commercial design is not a credible deployment candidate anywhere — let alone in Europe.

**What would change the verdict.** Verdict could move from `eliminated` to `pending` if (i) Centrus / General Matter / Orano publish a binding HALEU delivery commitment that maps to a specific KP-FHR-140 European COD before ~2030, AND (ii) the commercial KP-FHR-140 NRC CP is docketed and accepted. Both conditions are required. Even then, the size mismatch makes Kairos a niche cogeneration / industrial-heat candidate rather than a coal-replacement workhorse.
