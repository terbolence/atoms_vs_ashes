# LLM Evaluation Run — Rolls-Royce SMR

```json
{
  "design_id": "rolls_royce_smr",
  "design_name": "Rolls-Royce SMR (470 MWe net close-coupled three-loop PWR)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "pass",
      "evidence": "UK GDA Step 3 in progress (started 31 Jul 2024; Step 2 closed earlier in 2024). UK Government granted nuclear justification for the design March 2026 (NucNet 2026-03-05). 13 April 2026 Rolls-Royce SMR signed two-stage landmark contract with GBE-N for Wylfa first units. Czech SÚJB engaged via observers; ČEZ Early Works Agreement at Temelín signed July 2025. Polish PAA observers; IAEA Technical Safety Review completed 2024.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "pass",
      "evidence": "Standard LEU UO₂ <5% U-235 PWR fuel. Westinghouse Electric Company contract signed 2023 for fuel design and supply. No HALEU dependency. Westinghouse Springfields Fuels (UK) and Columbia (US) commercial fabrication available.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "pass",
      "evidence": "Standard PWR LEU UO₂ spent fuel; UK GDA Step 1+2 includes waste assessment. Compatible with Romania's National Strategy. Saligny LILW disposal pathway accepts standard PWR ILW. Westinghouse standard fuel form aligned with EU LWR experience.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "pass",
      "evidence": "UK GDA Step 2 closed earlier in 2024; Step 3 (detailed assessment) in progress. UK Government nuclear justification granted March 2026. IAEA Technical Safety Review 2024. Three-loop close-coupled PWR architecture builds on Westinghouse PWR safety pedigree.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "caution",
      "evidence": "UK GDA Step 3 not yet complete; Wylfa landmark contract is two-stage with site-specific design completion in stage 2. Vendor public statement that design is frozen for FOAK is vendor_claim until GDA Step 3 closes. Doicești COD 2033 is unlikely without GDA Step 3 closure ~2027 plus site-specific licensing in CZ or RO. For mid-2030s European COD this is a pass; for 2033 Doicești COD it is caution.",
      "confidence": "indirect_evidence"
    },
    "a6_site_fit": {
      "verdict": "pass",
      "evidence": "470 MWe single PWR; cooling options articulated for both coastal (Wylfa once-through) and inland (CZ Temelín cooling tower). Land take ~30-50 ha. Transport envelope: standard European road/rail. ČEZ Temelín feasibility supports inland CEE coal-replacement profile.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "pass",
      "evidence": "GBP 490 M+ committed (UK Research and Innovation GBP 210 M; Rolls-Royce Group + BNF Resources + Constellation + QIA GBP 280 M). ČEZ acquired 20% equity Oct 2024. UK GBE-N landmark contract April 2026. Rolls-Royce Group balance sheet ~GBP 5+ B revenue.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 4,
      "rationale": "UK GDA Step 2 closure includes hazards assessment + PSAR-equivalent + Level 1 PSA. Step 3 in progress. IAEA Technical Safety Review 2024 confirmed conventional PWR safety architecture. External hazards treated against WENRA reference levels. Score not 5 because GDA Step 3 not yet complete.",
      "evidence": "UK GDA Step 2 closure report; IAEA TSR 2024; NEA Dashboard 3rd Ed p. 216.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 3,
      "rationale": "Detailed design complete; FOAK procurement underway via Wylfa contract April 2026. No operating reference unit; first unit construction not yet started. Three-loop close-coupled PWR architecture = relatively conservative design choice (no novel coolant/fuel/spectrum). Score 3 reflects pre-construction status.",
      "evidence": "GBE-N contract press release April 2026; UK GDA Step 2 closure.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 4,
      "rationale": "Three-loop close-coupled PWR; design in late freeze; Sheffield Module Development Facility under development at University AMRC. Long-lead items being contracted. Vendor claims 4-year construction cycle (vendor_claim). Czech Škoda JS + ÚJV Řež contracted 2025 as Czech industrial partners.",
      "evidence": "NEA Dashboard 3rd Ed p. 216; E&T magazine 2025-08; Rolls-Royce SMR press release Apr 2026.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 4,
      "rationale": "AtkinsRéalis, BAM Nuttall, Laing O'Rourke, Jacobs, Sheffield Forgemasters, Škoda JS (CZ), Curtiss-Wright (UK partner), Nuclear AMRC, Assystem, The Welding Institute, UK National Nuclear Laboratory. Strong UK + Czech industrial spine. Multi-source for safety-class items.",
      "evidence": "NEA Dashboard 3rd Ed pp. 216-217; Rolls-Royce SMR press releases 2024-2026.",
      "confidence": "direct_evidence"
    },
    "b5_fuel_qualification": {
      "score": 5,
      "rationale": "Standard PWR LEU UO₂ via Westinghouse — identical fuel form to operating commercial PWR fleet (Sizewell B, Westinghouse-fuelled Loviisa upgrades, Springfields-supplied fleet). Commercial fabrication at Springfields (UK) and Columbia SC (US). Fuel similar to operating commercial PWR fleet — no further qualification needed.",
      "evidence": "Westinghouse-Rolls-Royce SMR fuel agreement 2023; NEA Dashboard p. 217.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 4,
      "rationale": "Standard PWR LEU UO₂ spent fuel; conditioning route established via UK PWR experience. Volume per MWh within EU LWR experience. UK GDA waste assessment in progress for Step 3. ČEZ Temelín spent-fuel pathway established.",
      "evidence": "UK GDA Step 1+2 environmental assessments; NEA Dashboard p. 216.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 4,
      "rationale": "Wylfa coastal once-through cooling; CZ Temelín cooling-tower variant; multiple cooling options proven. Land take ~30 ha for single 470 MWe unit. Transport envelope: standard European road/rail. EPZ ≤2 km vendor_claim — UK GDA Step 2 closure addresses but Step 3 confirms.",
      "evidence": "Rolls-Royce SMR design control document; UK GDA Step 2 closure report.",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 4,
      "rationale": "Vendor claims minimum stable load 25% with ramp ≥5%/min; primary frequency control demonstrated (vendor_claim). Three-loop architecture supports faster response than integral PWRs. Black-start capability claimed.",
      "evidence": "Rolls-Royce SMR design control document (vendor_claim).",
      "confidence": "indirect_evidence"
    },
    "b9_security_safeguards": {
      "score": 4,
      "rationale": "UK GDA includes security assessment and cyber per IEC 62645. Rolls-Royce military pedigree supports robust physical protection concept. Insider-threat mitigation per ONR requirements.",
      "evidence": "UK GDA Step 2 closure report; ONR security framework.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 4,
      "rationale": "Conventional PWR operating model; ONR-approved staffing concept under development; ČEZ Temelín existing PWR operator base would adapt easily. Romanian SNN staffing concept compatible with PWR. Training pipeline via UK industry + Czech ÚJV Řež.",
      "evidence": "Rolls-Royce SMR + ČEZ Early Works Agreement July 2025; NEA Dashboard p. 216.",
      "confidence": "indirect_evidence"
    },
    "b11_vendor_credibility": {
      "score": 5,
      "rationale": "Rolls-Royce Group + ČEZ (20% equity) + UK Government + GBE-N consortium = very strong. Rolls-Royce's military reactor pedigree (UK Astute-class submarines) provides decades of reactor lifecycle support experience. Long-term financial commitment supported by ČEZ ownership.",
      "evidence": "Rolls-Royce Group financials; ČEZ equity acquisition press release Oct 2024; GBE-N contract press release Apr 2026.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 4.00,
  "b_aggregate_100pt": 80.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 3.0, "rationale": "Czech Škoda JS + ÚJV Řež + ČEZ ownership 20%; multiple UK suppliers. Strong EU industrial role anchored by Czech base. Romanian content not yet established."},
    "c2_energy_sovereignty": {"modifier_pct": 5.0, "rationale": "Westinghouse PWR fuel via Springfields (UK) and Columbia (US); UK + CZ supply chain; non-Russian energy sovereignty maximised."},
    "c3_cogeneration": {"modifier_pct": 2.0, "rationale": "Industria Polska Central Hydrogen Cluster engagement = articulated cogeneration use case for hydrogen production. Steam extraction technically feasible."},
    "c4_fleet_deployability": {"modifier_pct": 5.0, "rationale": "Up to 6 units at Temelín (3 GWe target); Wylfa initial UK GBE-N programme; multiple UK sites planned via GBE-N; Industria Polska multiple sites; Vattenfall Ringhals finalist; Solway Cumbria."},
    "c5_eu_exportability": {"modifier_pct": 5.0, "rationale": "EU active engagement: CZ (Temelín Early Works Agreement), NL (ULC-Energy MoU), PL (Industria approval), SE (Vattenfall finalist). ≥3 EU states with binding commitments."},
    "c6_geopolitical_risk": {"modifier_pct": -2.0, "rationale": "UK + EU exposure; modest Brexit-related export-control friction for some safety-class components; mitigated by ČEZ ownership and Czech industrial base."},
    "c7_state_aid_risk": {"modifier_pct": -3.0, "rationale": "UK State aid OK; EU CfD/RAB structures not yet notified for cross-border deployment. Czech State aid for Temelín 3 GWe will be largest test case."}
  },
  "c_modifier_pct_total": 15.0,
  "final_score": 4.60,
  "verdict": "pending",
  "verdict_drivers": [
    "Tier A5 caution: design freeze not formally complete (UK GDA Step 3 in progress; Wylfa contract is two-stage)",
    "Otherwise the strongest European-led design with very high Tier B (4.00) and very high Tier C (+15%)",
    "If A5 resolved (GDA Step 3 closure ~2027) verdict converts to shortlist_primary at 4.60",
    "Czech ČEZ Temelín route is the most credible CEE deployment path"
  ],
  "data_gaps_critical": [
    "UK GDA Step 3 closure date (~2027 expected but not committed)",
    "Wylfa stage-2 site-specific design completion timeline"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX disclosure (vendor LCOE target <£70/MWh implies a specific CAPEX but not published)",
    "Czech State-aid clearance for Temelín 3 GWe pathway"
  ]
}
```

## Analyst Summary

**Headline finding.** Rolls-Royce SMR is the **highest-scoring European-led SMR** by Tier B + Tier C combination (4.60), but **A5 (design freeze) caution forces verdict `pending`** rather than `shortlist_primary` for a 2033 Doicești COD. For a mid-2030s European deployment (which matches the realistic Czech Temelín timeline), all gates pass and the design is `shortlist_primary` at 4.60. The April 2026 GBE-N landmark contract for Wylfa, the ČEZ 20% equity position, and the UK Government's nuclear justification (March 2026) make this the **strongest European industrial proposition** of the nine designs.

**Key strengths.** First, the **fully European industrial spine** (Rolls-Royce + Czech Škoda JS + ČEZ + ÚJV Řež + UK supplier ecosystem) drives both C1 (+3 %) and C5 (+5 %) modifiers and avoids US export-control friction. Second, the **published LCOE target of <£70/MWh** (~83 EUR/MWh) is the most aggressive vendor target among the nine candidates and would, if achieved, set a new floor for European SMR economics. Third, **vendor balance-sheet strength** plus the 20 % ČEZ equity stake gives the consortium long-term lifecycle commitment unmatched by US start-ups. Fourth, the **ČEZ Temelín 3 GWe programme** is the most credible CEE multi-unit pipeline of any design.

**Key weaknesses.** First, **GDA Step 3 closure timing is the binding constraint**: until Step 3 is closed (~2027 expected), the design freeze is incomplete, and the Doicești-style 2033 COD is not realistic. Second, **the Wylfa landmark contract is two-stage**, with the site-specific design completion in stage 2 — so vendor "design frozen" claims are not yet certified. Third, **EU State-aid clearance for Temelín 3 GWe and the broader CEE programme** has not been tested; Czech and Polish State-aid pathways differ from the UK CfD precedent.

**Most critical data gap.** The **per-MWe overnight CAPEX figure** is conspicuously absent from public disclosures — Rolls-Royce only publishes the LCOE target. Until this is disclosed and validated through the GBE-N contract negotiations, the economic model has to estimate CAPEX from the LCOE working backwards (~7 500 USD/kWe FOAK).

**What would change the verdict.** Verdict converts to `shortlist_primary` (4.60) on **GDA Step 3 closure** (~2027). It could degrade to `shortlist_secondary` if the Wylfa stage-2 contract slips materially or if first concrete is not poured by 2028. For Romanian deployment specifically, the design is a **strong candidate for a future second site** (post-Doicești) — likely competitive with BWRX-300 — but is not in the running for Doicești itself given the SNN-NuScale commitment.
