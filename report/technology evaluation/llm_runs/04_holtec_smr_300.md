# LLM Evaluation Run — Holtec SMR-300

```json
{
  "design_id": "holtec_smr_300",
  "design_name": "Holtec International SMR-300 (300 MWe net integral PWR)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "pass",
      "evidence": "NRC accepted Part 1 of phased Construction Permit Application + Limited Work Authorization for Pioneer Units 1+2 at Palisades on 13 February 2026 (NRC project page; ANS 2026-01-14). UK GDA Step 2 (Fundamental Assessment) completed 31 March 2026 — ONR/EA/NRW found 'no fundamental shortfalls' (ONR 2026-03; WNN 2026-03). CNSC VDR Phase 1 completed 2020 (legacy SMR-160 design).",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "pass",
      "evidence": "Framatome GAIA 17×17 fuel assembly contract signed 2020 — already used in operating PWRs. Standard LEU UO₂ <5% U-235; no HALEU dependency. GNF-A MoU 2018 for control rod drive mechanisms.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "pass",
      "evidence": "Standard PWR LEU UO₂ spent fuel via Framatome GAIA assembly — well-characterised in EU LWR experience. Holtec is the world's largest spent-fuel cask vendor (HI-STORM, HI-STAR), so spent-fuel storage pathway is internally available. Saligny LILW disposal accepts PWR ILW.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "caution",
      "evidence": "UK GDA Step 2 found 'no fundamental shortfalls' but identified 14 regulatory observations carried into Step 3 (GOV.UK Step 2 closure report). NRC CPA Part 1 acceptance (Feb 2026) is partial — Part 2 expected mid-2027; safety case not yet fully reviewed. Power uprate from SMR-160 to SMR-300 (2x scale change) introduced in 2023; safety case re-baselined.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "caution",
      "evidence": "CPA Part 2 expected mid-2027; UK GDA Step 3 still ahead. Design freeze incomplete for vendor's stated 2030 first-unit COD at Palisades. Doicești 2033 COD requires CPA Part 2 + UK GDA Step 3 + CNCAN site-specific licensing — caution rather than fail given multi-jurisdictional momentum.",
      "confidence": "indirect_evidence"
    },
    "a6_site_fit": {
      "verdict": "pass",
      "evidence": "300 MWe single integral PWR; <30 ha footprint. Palisades site already characterised (existing Holtec ownership). Cooling-water demand within typical CEE coal-site envelope. UK Cottam (Nottinghamshire) siting referenced in GDA Step 2 page = inland precedent. Hybrid cooling option available.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "pass",
      "evidence": "DOE Advanced Reactor Demonstration Program USD 116 M (2020); Korea ECA financing agreements 2023; UK DESNZ GBP 30 M (2024); Holtec invested USD 400 M in SMR programme by 2021. Member of Mid-Atlantic Clean Hydrogen Hub (DOE up to USD 750 M). Holtec is privately held but a USD ~3-5 B revenue company.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 4,
      "rationale": "NRC CPA Part 1 includes PSAR; UK GDA Step 2 review found 'no fundamental shortfalls'. Level 1 PSA available; Level 2 in progress. Holtec power-uprate from SMR-160 to SMR-300 in 2023 means safety case re-baselined recently — score not 5 because re-baseline is recent.",
      "evidence": "NRC CPA Part 1 acceptance Feb 2026; ONR Step 2 closure report Mar 2026; NEA Dashboard 3rd Ed p. 144.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 3,
      "rationale": "Original SMR-160 design but power-uprated to SMR-300 in 2023 = significant scale change recent. No operating reference unit; Palisades is the FOAK. Multiple novel subsystems still in qualification (passive containment, ASEM concept). Construction not started. Score 3 reflects pre-construction status with recent design re-baseline.",
      "evidence": "NEA Dashboard 3rd Ed p. 144; Holtec 2023 announcement of SMR-160 → SMR-300 transition.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 3,
      "rationale": "Vertical integration into ASEM passive containment; Hyundai E&C contracted; modularised design but novel manufacturing required. Sheffield SMR factory pending final decision (GBP 1.5 B). Long-lead items not yet fully contracted for Pioneer Units. Construction philosophy articulated but not validated at scale.",
      "evidence": "NEA Dashboard 3rd Ed p. 145; UK Sheffield SMR factory siting announcement.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 4,
      "rationale": "Holtec in-house manufacturing (large heavy-forging facility in Camden NJ); Hyundai E&C; Framatome (GAIA fuel); Mitsubishi Electric (I&C); Sheffield Forgemasters MoU; Sheffield Advanced Manufacturing Research Centre. UK Holtec Heavy Industries pending FID. Multi-source for some safety-class items.",
      "evidence": "NEA Dashboard 3rd Ed pp. 144-145.",
      "confidence": "direct_evidence"
    },
    "b5_fuel_qualification": {
      "score": 5,
      "rationale": "Framatome GAIA 17×17 — standard PWR LEU UO₂ assembly already in commercial use. Commercial fabrication at Framatome's facilities. Fuel similar to operating commercial PWR fleet — no further qualification needed.",
      "evidence": "Framatome-Holtec contract 2020; NEA Dashboard p. 145.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 4,
      "rationale": "Standard PWR LEU UO₂ spent fuel via Framatome GAIA. Holtec's HI-STORM dry cask storage is a global market leader — internal back-end capability exceptional. Saligny LILW pathway accepts PWR ILW. Holtec experience at Palisades restart provides US precedent for SF management.",
      "evidence": "Holtec dry cask product line; Framatome GAIA fuel form.",
      "confidence": "direct_evidence"
    },
    "b7_site_envelope": {
      "score": 3,
      "rationale": "Single-unit 300 MWe; Palisades has once-through Lake Michigan cooling but European inland sites need hybrid. UK Cottam inland site contemplated — cooling envelope not yet demonstrated for inland European site. Footprint <30 ha. Land take and transport envelope acceptable.",
      "evidence": "NEA Dashboard p. 144; UK GDA Step 2 closure report.",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 3,
      "rationale": "Vendor claims load-following but no public quantitative envelope for SMR-300 (post-uprate). Integral PWR architecture allows passive cool-down — grid flexibility envelope re-baselined post-uprate. Score 3 reflects data gap.",
      "evidence": "Holtec design control document (vendor_claim).",
      "confidence": "data_gap"
    },
    "b9_security_safeguards": {
      "score": 4,
      "rationale": "NRC CPA Part 1 includes physical protection plan; cyber per IEC 62645 in NRC + UK GDA. Safeguards-by-design integration partially articulated. Insider-threat mitigation per US 10 CFR 73.55.",
      "evidence": "NRC CPA Part 1 SER section; UK GDA Step 2 closure security section.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 4,
      "rationale": "Conventional integral PWR operating model; Holtec Palisades restart team provides experienced PWR operators. Training pipeline via Holtec University. Romanian SNN PWR/CANDU operator base would cross-train.",
      "evidence": "Holtec Palisades restart team experience; NEA Dashboard p. 144.",
      "confidence": "indirect_evidence"
    },
    "b11_vendor_credibility": {
      "score": 4,
      "rationale": "Holtec is a USD 3-5 B revenue private company with global spent-fuel cask market leadership. Hyundai E&C partnership for EPC; Korea ECA financing support; DOE backing. Sheffield SMR factory FID pending = uncertainty on UK industrial commitment scale. Vendor balance sheet adequate for 60-year commitment but not yet stress-tested.",
      "evidence": "Holtec corporate disclosures; NEA Dashboard pp. 144-145.",
      "confidence": "indirect_evidence"
    }
  },
  "b_aggregate_5pt": 3.70,
  "b_aggregate_100pt": 74.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 2.0, "rationale": "Sheffield SMR factory pending FID (GBP 1.5 B); Framatome (FR) fuel; Sheffield Forgemasters and AMRC MoUs. Substantial UK potential; Romanian role not established."},
    "c2_energy_sovereignty": {"modifier_pct": 5.0, "rationale": "Framatome (FR) fuel supply; non-Russian energy sovereignty maximised."},
    "c3_cogeneration": {"modifier_pct": 1.0, "rationale": "Mid-Atlantic Clean Hydrogen Hub membership = articulated US hydrogen cogeneration use case. Steam extraction technically feasible."},
    "c4_fleet_deployability": {"modifier_pct": 3.0, "rationale": "Palisades Pioneer Units 1+2; Oyster Creek site under consideration; UK GBN finalist; Ukraine MoUs; Entergy MoA. Pipeline broad but no signed multi-unit programme outside US."},
    "c5_eu_exportability": {"modifier_pct": 3.0, "rationale": "UK + Ukraine + US engagement. Ukraine is non-EU; UK is non-EU. Only 0 binding EU-state engagements (despite supplier MoUs in CZ via Sheffield). Below the +5% threshold of ≥3 EU states."},
    "c6_geopolitical_risk": {"modifier_pct": -2.0, "rationale": "Hyundai (KR) + Holtec (US) dependencies; Ukraine MoUs add geopolitical complexity. Single-jurisdiction risk for some long-lead items."},
    "c7_state_aid_risk": {"modifier_pct": -3.0, "rationale": "UK GBN structure being clarified; EU State-aid not yet structured for SMR-300. Sheffield factory FID linkage to UK government support adds State-aid notification risk."}
  },
  "c_modifier_pct_total": 9.0,
  "final_score": 4.03,
  "verdict": "pending",
  "verdict_drivers": [
    "Tier A4 + A5 caution: NRC CPA is partial (Part 1 only); UK GDA Step 2 done but Step 3 ahead; design re-baselined 2x in 2023 (SMR-160 → SMR-300)",
    "Tier B aggregate 3.70 with strong fundamentals (standard PWR fuel + Holtec spent-fuel expertise)",
    "EU exportability limited (only UK + Ukraine engagement, no binding EU-state commitments)",
    "Strong financial backing via DOE + UK DESNZ + Korea ECA"
  ],
  "data_gaps_critical": [
    "NRC CPA Part 2 docketing date (mid-2027 stated but not docketed)",
    "Sheffield SMR factory FID timeline"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX disclosure",
    "Quantitative grid-flexibility envelope post-uprate",
    "Cottam (UK) land-rights agreement"
  ]
}
```

## Analyst Summary

**Headline finding.** Holtec SMR-300 is a **credible second-tier candidate** with a final score of 4.03 — but the **A4 and A5 cautions** (NRC CPA Part 1 only; UK GDA Step 3 ahead; design re-baselined twice between SMR-160 and SMR-300 in 2023) force the verdict to `pending`. The strengths are very real: the **March 2026 UK GDA Step 2 closure** (no fundamental shortfalls across safety, security, safeguards, environment) and the **February 2026 NRC CPA Part 1 acceptance** put it firmly in the active commercial-deployment pipeline. The weakness is **timing of completion**: Part 2 + Step 3 + CNCAN site-specific licensing for any 2033 European COD are achievable but not guaranteed.

**Key strengths.** First, **Holtec's spent-fuel cask leadership** (HI-STORM/HI-STAR is a global market leader) gives the SMR-300 the strongest internal back-end capability of any non-LWR-vendor-led design. Second, **Framatome GAIA 17×17 fuel** provides the cleanest possible LEU UO₂ supply chain. Third, the **DOE + UK DESNZ + Korea ECA financing stack** (USD 116 M + GBP 30 M + Korean ECA) is well-distributed across allied jurisdictions. Fourth, the **Mid-Atlantic Clean Hydrogen Hub** membership shows commercially mature cogeneration thinking.

**Key weaknesses.** First, the **2023 power-uprate from SMR-160 to SMR-300 (2× scale change)** means the entire safety case was re-baselined recently — the NRC CPA Part 1 + UK GDA Step 2 reviews have validated this re-baseline, but the cumulative "design frozen" maturity is lower than for a design that has not changed. Second, **EU exportability is the weakest of any pass-Tier-A candidate** — Ukraine and UK are non-EU; CZ engagement is via Sheffield supplier MoUs rather than ČEZ-style equity or operator commitment. Third, the **Sheffield SMR factory FID is pending** — until this commitment is firm, UK industrial role is provisional.

**Most critical data gap.** The **NRC CPA Part 2 docketing schedule** (vendor-stated mid-2027 but not yet committed by NRC). Without a docketed Part 2, vendor's stated 2030 Palisades COD slips to 2032+, and Doicești 2033 COD becomes infeasible.

**What would change the verdict.** Verdict converts to `shortlist_secondary` (4.03) on **NRC CPA Part 2 docketing** + **UK GDA Step 3 progress demonstrated**. It would degrade to `watch` if Sheffield SMR factory FID is cancelled or if Palisades unit-1 commissioning slips beyond 2034. **For Romanian deployment**, this is a credible alternative for a future second site (post-Doicești) but not for Doicești itself.
