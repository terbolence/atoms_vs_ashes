# LLM Evaluation Run — TerraPower Natrium

```json
{
  "design_id": "terrapower_natrium",
  "design_name": "TerraPower Natrium (345 MWe baseload + 500 MWe peak with thermal storage)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "pass",
      "evidence": "NRC issued Construction Permit for Kemmerer Unit 1 on 18 December 2025 — first sodium-cooled fast reactor CP issued by NRC for commercial-scale deployment (NRC project page; NRC release 26-028; WNN 2025-12-18; TerraPower press 2025-12-18). NRC continues review of the operating-licence application. CNCAN engagement = none. Romanian licensability path not articulated.",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "fail",
      "evidence": "HALEU metallic U-Zr alloy. First core requires ~9 t HALEU; Centrus production ~1 t/yr (April 2026), 12 t/yr 'after 2030' (Reuters 2026-02-24). Russian alternative banned 2028. Romans-sur-Isère pilot (TerraPower-Framatome) inaugurated 2025 = pilot scale only. No European HALEU pipeline. Vendor publicly slipped first power from 2030 to 2031-2032 due to HALEU uncertainty. For Romania COD-2033 European deployment = fail.",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "caution",
      "evidence": "Metallic spent fuel from sodium fast reactor; conditioning concept defined but not demonstrated at scale. Romans-sur-Isère is a pilot fabrication facility, not a back-end facility. Romania's National Strategy does not address sodium-cooled fast reactor waste streams. Caution because TerraPower-Framatome French industrial partnership provides one credible European conditioning pathway under development.",
      "confidence": "indirect_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "pass",
      "evidence": "NRC CP issued December 2025 = comprehensive safety review including PSAR-equivalent + Level 1/2 PSA + severe accident analysis published. Sodium fast reactor safety case validated by NRC. WENRA-mappable.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "pass",
      "evidence": "NRC CP issuance 18 Dec 2025 = design frozen for FOAK Kemmerer Unit 1. Configuration management mature. Bechtel EPC contracted; Doosan RPV; Westinghouse heat exchangers; AECOM I&C. Long-lead components contracted.",
      "confidence": "direct_evidence"
    },
    "a6_site_fit": {
      "verdict": "caution",
      "evidence": "345 MWe baseload + 500 MWe peak with 5.5 h thermal storage. Cooling envelope for sodium fast reactor different from PWR. Wyoming Kemmerer site = inland; cooling tower configuration. European inland site fit possible but cooling-envelope demonstration limited. Storage value monetisation requires intra-day price spreads — Romanian DAM has limited spread.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "caution",
      "evidence": "DOE matching funds USD 2 B (2020); USD 750 M additional 2022 (Bill Gates + SK Inc); USD 9 M DARPA 2024; Wyoming USD 12 M; State of Wyoming USD 5 M matching. Total Wyoming project ~USD 4 B. PacifiCorp PPA for Wyoming. EU financing structure for Natrium not yet articulated.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 4,
      "rationale": "NRC CP issued Dec 2025 includes PSAR-equivalent + Level 1/2 PSA + severe accident analysis. Significant work on sodium-fire scenarios and sodium-water interaction. External hazards treated. Score not 5 because first-of-kind sodium fast reactor commercial CP — operating-fleet validation still pending.",
      "evidence": "NRC release 26-028 (Dec 2025); NRC project page Kemmerer.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 2,
      "rationale": "No operating reference unit; HALEU first core delayed due to Centrus capacity (vendor slip from 2030 to 2031-2032). Multiple novel subsystems on critical path simultaneously: sodium cooling + metallic fuel + HALEU + integrated thermal storage. NRC CP in hand but pre-construction (only non-nuclear excavation underway).",
      "evidence": "WNA Natrium product page; TerraPower press 2025-12-18.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 3,
      "rationale": "Wyoming non-nuclear construction underway (excavation, site preparation since mid-2024). Long-lead components contracted: Doosan RPV, Westinghouse heat exchangers, HD Hyundai HI forging, AECOM I&C, PaR Systems handling machine, Curtiss-Wright protection system. Sodium test facility ready for components. Construction philosophy articulated but unproven at scale.",
      "evidence": "TerraPower 2025-2026 supplier announcements; NEA Dashboard 3rd Ed p. 226.",
      "confidence": "direct_evidence"
    },
    "b4_supply_chain": {
      "score": 4,
      "rationale": "Bechtel EPC; Doosan Enerbility (RPV + components); Westinghouse (heat exchangers); AECOM (I&C); HD Hyundai HI (forging); Centrus (HALEU); Framatome (Romans-sur-Isère pilot fuel); AtkinsRéalis (US deployment); PaR Systems; Curtiss-Wright. Strong supplier ecosystem; multi-source for some safety-class items.",
      "evidence": "NEA Dashboard 3rd Ed pp. 226-227; TerraPower 2025 supplier announcements.",
      "confidence": "direct_evidence"
    },
    "b5_fuel_qualification": {
      "score": 1,
      "rationale": "HALEU metallic U-Zr fuel. First commercial fabrication = Romans-sur-Isère pilot 2025 (test-pin scale). No lead test assemblies in commercial sodium fast reactor operation. EBR-II provided over 30 years of metallic-fuel R&D but at non-commercial scale. Score 1 reflects HALEU dependency + commercial fabrication facility at pilot scale.",
      "evidence": "NEA Dashboard 3rd Ed p. 227; Romans-sur-Isère 2025 inauguration.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 2,
      "rationale": "Metallic spent fuel from sodium fast reactor; Romans-sur-Isère = pilot fabrication only. Conditioning concept defined but not demonstrated. Romanian National Strategy does not address; French La Hague does not currently process metallic FR fuel.",
      "evidence": "Romanian National Strategy 2014; Romans-sur-Isère 2025 facility scope.",
      "confidence": "indirect_evidence"
    },
    "b7_site_envelope": {
      "score": 3,
      "rationale": "Sodium fast reactor; 345 MWe + storage; cooling envelope different from PWR. Wyoming Kemmerer is inland with cooling-tower configuration — direct precedent for European inland sites. Land take ~50-80 ha. Transport envelope: standard road/rail-compatible major components.",
      "evidence": "TerraPower Kemmerer site disclosures; NEA Dashboard p. 226.",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 5,
      "rationale": "500 MWe peak / 345 MWe baseload + 5.5 h molten-salt thermal storage = excellent flexibility envelope. Quantitative envelope published. Storage decoupling allows ramp >10%/min for peak block. Black-start capability claimed. Best-in-class grid flexibility of the 9 designs evaluated.",
      "evidence": "TerraPower design control document; PacifiCorp PPA structure (Wyoming).",
      "confidence": "direct_evidence"
    },
    "b9_security_safeguards": {
      "score": 4,
      "rationale": "NRC CP includes safeguards-by-design + cyber per IEC 62645. Sodium fast reactor adds material-control complexity but NRC review addressed. Insider-threat mitigation per US 10 CFR 73.55.",
      "evidence": "NRC release 26-028; SER security section.",
      "confidence": "direct_evidence"
    },
    "b10_operating_model": {
      "score": 3,
      "rationale": "Sodium fast reactor operating model unfamiliar to European operators. PacifiCorp Wyoming has zero SFR experience but Bechtel EPC role brings operational expertise. SNN Cernavodă PWR/CANDU operator base would require entirely new training pipeline.",
      "evidence": "PacifiCorp + TerraPower partnership disclosures.",
      "confidence": "data_gap"
    },
    "b11_vendor_credibility": {
      "score": 4,
      "rationale": "TerraPower + Cascade Investment (Bill Gates) + DOE USD 2 B + Bechtel EPC + Doosan + Westinghouse + Framatome (FR) + KHNP MoU + FANR (UAE) MoU = very strong consortium. Romans-sur-Isère pilot inaugurated 2025 demonstrates French industrial partnership. Long-term lifecycle support concept emerging.",
      "evidence": "TerraPower disclosures; NEA Dashboard pp. 226-227; Romans-sur-Isère 2025.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 3.00,
  "b_aggregate_100pt": 60.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 1.0, "rationale": "Romans-sur-Isère TerraPower-Framatome pilot fuel facility = first European industrial footprint. Scale is pilot only; Bechtel/Doosan/Westinghouse/HD Hyundai are non-EU."},
    "c2_energy_sovereignty": {"modifier_pct": 0.0, "rationale": "HALEU pipeline US-only via Centrus; Romans-sur-Isère is fuel-pilot scale. C2 minimum 0."},
    "c3_cogeneration": {"modifier_pct": 2.0, "rationale": "High-temperature 510°C output supports industrial cogeneration; thermal storage decouples electricity output from heat extraction = unique flexibility for cogeneration. Not maximum +5% because no signed European cogeneration LoI."},
    "c4_fleet_deployability": {"modifier_pct": 1.0, "rationale": "PacifiCorp + Sabey Data Centers + Energy Northwest = US fleet potential. KHNP MoU; FANR (UAE) MoU. First European site TBD."},
    "c5_eu_exportability": {"modifier_pct": 0.0, "rationale": "No EU-state engagement for Natrium deployment. Romans-sur-Isère is supply-side, not deployment-side."},
    "c6_geopolitical_risk": {"modifier_pct": -7.0, "rationale": "HALEU pipeline US-only via Centrus; Russian-fuel ban affects transition; export-control friction for HALEU and metallic FR fuel technology. Concentrated US dependency."},
    "c7_state_aid_risk": {"modifier_pct": -2.0, "rationale": "DOE USD 2 B + State of Wyoming co-funding is US-specific structure. EU State-aid path for Natrium not yet articulated."}
  },
  "c_modifier_pct_total": -5.0,
  "final_score": 2.85,
  "verdict": "eliminated",
  "verdict_drivers": [
    "A2 fail: HALEU first-core requirement (~9 t) for Romania COD-2033 not credible",
    "Best-in-class grid flexibility (B8 = 5) thanks to integrated thermal storage",
    "NRC CP issued Dec 2025 + Romans-sur-Isère pilot 2025 = strong design-freeze evidence",
    "C6 −7%: HALEU pipeline US-only single-source dependency"
  ],
  "data_gaps_critical": [
    "Centrus 9 t first-core HALEU delivery date for Wyoming",
    "European deployment intent (no MoU with any EU state)"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX disclosure (USD 4 B / 345 MWe = ~11.6 k$/kWe nominal but storage capacity not disaggregated)",
    "Operating model and staffing for European deployment",
    "Quantification of storage value in EU markets"
  ]
}
```

## Analyst Summary

**Headline finding.** TerraPower Natrium is **eliminated** for Romanian deployment by **A2 (HALEU front-end fuel supply)** failure, despite the strongest sodium-fast-reactor design-freeze evidence (NRC Construction Permit issued 18 December 2025) and the strongest grid-flexibility envelope of any of the nine designs (B8 = 5). The **structural HALEU bottleneck** (Centrus ~1 t/yr current, 12 t/yr "after 2030", Russian alternative banned 2028) closes the Romania COD-2033 window. Vendor publicly slipped Wyoming first-power from 2030 to 2031-2032 due to HALEU uncertainty.

**Key strengths.** First, the **NRC Construction Permit issued December 2025** is a substantive milestone — first sodium-fast-reactor commercial CP from NRC, with full PSAR-equivalent + Level 1/2 PSA + severe accident analysis published. Second, the **integrated 5.5 h molten-salt thermal storage** giving 345 MWe baseload / 500 MWe peak is a **structural advantage** for any market with intra-day price spreads — driving the maximum B8 = 5 grid-flexibility score. Third, the **TerraPower-Framatome Romans-sur-Isère pilot fuel facility inauguration in 2025** is the only European industrial footprint among the four HALEU-dependent designs evaluated, and it is the basis for the +1 % C1 modifier (the only positive C1 modifier among non-LWR designs). Fourth, the **vendor consortium** (TerraPower + Cascade Investment + DOE USD 2 B + Bechtel + Doosan + Westinghouse + Framatome + KHNP + FANR) is very strong.

**Key weaknesses.** First, the **HALEU first-core requirement** of ~9 t is the binding constraint — neither Centrus nor any combination of US enrichers can deliver this on a 2030-2033 schedule. Second, **no European deployment intent** — Romans-sur-Isère is supply-side only, not deployment-side. Third, **storage-value monetisation** requires intra-day price spreads that Romania's DAM does not currently exhibit (annual weighted average ~110-115 EUR/MWh with limited spread). Fourth, **Romanian National Strategy does not address sodium-cooled fast reactor waste streams** — major back-end policy work would be required.

**Most critical data gap.** **Centrus 9 t first-core HALEU delivery date** for Wyoming. Without this, even the FOAK Kemmerer plant cannot start operations.

**What would change the verdict.** Even with **a binding HALEU commitment** for first European core, the **storage-value monetisation gap** in Romania's DAM and the **non-standard waste pathway** would keep Natrium at `pending` rather than `shortlist`. Natrium is best characterised as a **flexible-grid play for markets with strong intra-day spread** (e.g., California, Texas, Iberia post-2030), not for a baseload coal-replacement workhorse in Romania.
