# LLM Evaluation Run — NUWARD (EDF)

```json
{
  "design_id": "nuward",
  "design_name": "NUWARD (EDF) — 2 × 200 MWe = 400 MWe integrated PWR (post-July-2024 reset)",
  "target_country": "RO",
  "evaluation_date": "2026-04-21",
  "tier_a": {
    "a1_licensability": {
      "verdict": "pass",
      "evidence": "Joint Early Review Phase 2 closed December 2025 by ASNR (FR), STUK (FI), SÚJB (CZ); closure reports published (NUWARD JER Phase 2 closure report). Phase 3 in preparation as of April 2026. Polish PAA observer (since Feb 2024). EDF as utility operator and lead industrial partner. CNCAN engagement = limited (NUWARD presented at trade fairs in Romania but no formal pre-licensing).",
      "confidence": "direct_evidence"
    },
    "a2_fuel_supply": {
      "verdict": "pass",
      "evidence": "Standard PWR LEU UO₂ <5% U-235 via Framatome (EDF subsidiary). Pre-application meetings with regulators have not flagged any fuel supply issues (NEA Dashboard 3rd Ed p. 193). No HALEU dependency. Best-in-class supply chain (Framatome FR + Westinghouse for components).",
      "confidence": "direct_evidence"
    },
    "a3_waste_pathway": {
      "verdict": "pass",
      "evidence": "Standard PWR LEU UO₂ spent fuel; French La Hague reprocessing precedent. Compatible with Romania's National Strategy. Saligny LILW disposal accepts PWR ILW.",
      "confidence": "direct_evidence"
    },
    "a4_safety_showstoppers": {
      "verdict": "caution",
      "evidence": "JER Phase 2 closure report (Dec 2025) identifies convergent regulator views on most topics, but divergence on EPZ definition and on passive safety system reliability metrics. These will need to be re-addressed under the post-reset design (the JER Phase 2 was on the pre-reset 2x170 MWe configuration). Post-reset 2x200 MWe safety case not yet under JER Phase 3 review.",
      "confidence": "direct_evidence"
    },
    "a5_design_freeze": {
      "verdict": "fail",
      "evidence": "EDF paused original NUWARD design and ordered reset July 2024. Reset moved from bespoke integral PWR with proprietary passive safety architecture to a more conventional integrated PWR (2x200 MWe = 400 MWe gross). Post-reset conceptual design freeze targeted mid-2026; JER Phase 3 in preparation. First COD slipped from 2030 to mid-2030s. Romania COD-2033 = strict fail; mid-2030s European deployment = caution.",
      "confidence": "direct_evidence"
    },
    "a6_site_fit": {
      "verdict": "caution",
      "evidence": "2x200 MWe configuration; cooling envelope similar to small PWR. EDF coastal + inland precedent in France. Land take ~50 ha for 2-unit plant. Transport envelope acceptable. CEE coal-replacement site fit possible but European-specific cooling not yet demonstrated post-reset.",
      "confidence": "indirect_evidence"
    },
    "a7_financeability": {
      "verdict": "caution",
      "evidence": "EUR 850 M committed since 2017 (EUR 500 M private + public matching; EUR 50 M France 2030; EUR 300 M French government 2024-2026). Commercial financing structure unproven post-reset. EDF state-backed = strong baseline; commercial PPA / CfD structure for first NUWARD plant TBD.",
      "confidence": "direct_evidence"
    }
  },
  "tier_b": {
    "b1_safety_case": {
      "score": 3,
      "rationale": "JER Phase 2 closure (Dec 2025) = pre-application equivalent for pre-reset design. Post-reset 2x200 MWe safety case not yet reviewed in depth; JER Phase 3 in preparation. Convergent regulator views on most pre-reset topics; divergence on EPZ + passive safety system reliability requires re-baselining.",
      "evidence": "NUWARD JER Phase 2 closure report (Dec 2025); NEA Dashboard 3rd Ed p. 192.",
      "confidence": "direct_evidence"
    },
    "b2_maturity_foak": {
      "score": 2,
      "rationale": "Design reset July 2024; conceptual design freeze targeted mid-2026; multiple novel subsystems re-baselined (revised 2x200 MWe configuration). No operating reference; first commercial unit construction not started. Score 2 reflects post-reset design status.",
      "evidence": "EDF NUWARD reset July 2024; NEA Dashboard 3rd Ed p. 192.",
      "confidence": "direct_evidence"
    },
    "b3_constructability": {
      "score": 2,
      "rationale": "Design freeze 24+ months out (mid-2026 target). FOAK construction not started; long-lead items not yet contracted post-reset. Construction philosophy articulated but configuration management baseline pending design freeze.",
      "evidence": "NEA Dashboard 3rd Ed p. 192; EDF reset disclosures.",
      "confidence": "indirect_evidence"
    },
    "b4_supply_chain": {
      "score": 3,
      "rationale": "Framatome + EDF + TechnicAtome + Naval Group + Tractebel + Edvance + CEA = strong consortium. ENDEL, Ponticelli, Egis, Vinci Construction, Bouygues Travaux Public, Eiffage, AlsymEx, Thermodyn, Boccard, Cegelec, AMIS, Daher = broad French supplier ecosystem. Westinghouse for some components. Supplier engagement under way.",
      "evidence": "NEA Dashboard 3rd Ed p. 192-193.",
      "confidence": "direct_evidence"
    },
    "b5_fuel_qualification": {
      "score": 5,
      "rationale": "Standard PWR LEU UO₂ <5% via Framatome — identical fuel form to operating commercial PWR fleet. Commercial fabrication at Framatome Romans-sur-Isère and Spain. Pre-application meetings with regulators have not flagged any fuel issues.",
      "evidence": "NEA Dashboard 3rd Ed p. 193.",
      "confidence": "direct_evidence"
    },
    "b6_waste_fit": {
      "score": 4,
      "rationale": "Standard PWR LEU UO₂ spent fuel; French La Hague reprocessing precedent (industry-leading back-end capability). Compatible with Romanian National Strategy. Cogeneration option (~100 MWt) is fuel-cycle-neutral.",
      "evidence": "Framatome fuel form; La Hague operational precedent.",
      "confidence": "direct_evidence"
    },
    "b7_site_envelope": {
      "score": 4,
      "rationale": "Compact 2x200 MWe; multiple cooling options proven via EDF French fleet experience. Coastal + inland precedent. Land take ~50 ha. Transport envelope: standard European road/rail. EPZ ≤2 km claim under JER Phase 3 review.",
      "evidence": "EDF NUWARD design control document; JER Phase 2 closure (EPZ section).",
      "confidence": "indirect_evidence"
    },
    "b8_grid_flexibility": {
      "score": 3,
      "rationale": "PWR baseload-dominant; vendor claims load-following capability but no quantitative envelope post-reset. EDF French fleet load-following experience supports vendor claims but post-reset configuration not yet specified.",
      "evidence": "EDF NUWARD design disclosures (vendor_claim).",
      "confidence": "data_gap"
    },
    "b9_security_safeguards": {
      "score": 3,
      "rationale": "Safeguards-by-design articulated for pre-reset design; cyber TBD. Reset may require re-baselining of security architecture. ASNR security framework mature.",
      "evidence": "JER Phase 2 closure report.",
      "confidence": "indirect_evidence"
    },
    "b10_operating_model": {
      "score": 4,
      "rationale": "EDF operator model — most experienced PWR operator in Europe (56-unit French fleet). Conventional PWR experience extensive. Romanian SNN PWR/CANDU operator base would adapt easily via French-language and EDF training pipelines.",
      "evidence": "EDF operator track record; NEA Dashboard p. 192.",
      "confidence": "direct_evidence"
    },
    "b11_vendor_credibility": {
      "score": 5,
      "rationale": "EDF (state-backed utility, EUR 100+ B revenue) + TechnicAtome + Framatome + Naval Group + ČEZ + Vattenfall + Edison + EDP + EnBW + ULC-Energy + Industria Polska + IGS Energy + Doosan Enerbility = very strong consortium. Long-term lifecycle support via EDF French fleet servicing.",
      "evidence": "NEA Dashboard 3rd Ed pp. 192-193.",
      "confidence": "direct_evidence"
    }
  },
  "b_aggregate_5pt": 3.30,
  "b_aggregate_100pt": 66.0,
  "tier_c": {
    "c1_eu_industrial": {"modifier_pct": 5.0, "rationale": "Fully European consortium: EDF + Framatome + TechnicAtome + Naval Group + Tractebel + Edvance + CEA + Ansaldo + ČEZ + Industria Polska. Best-in-class European industrial role; >50% European supply-chain content embedded by design. Maximum +5%."},
    "c2_energy_sovereignty": {"modifier_pct": 5.0, "rationale": "Framatome FR fuel; EU supply chain; non-Russian energy sovereignty maximised. Maximum +5%."},
    "c3_cogeneration": {"modifier_pct": 5.0, "rationale": "Cogeneration option (~100 MWt) explicitly designed in. District-heat + hydrogen + industrial process steam supported by design. Best-in-class designed-in cogeneration. Maximum +5%."},
    "c4_fleet_deployability": {"modifier_pct": 3.0, "rationale": "CZ (ČEZ), IT (Edison/Ansaldo), NL (ULC-Energy), SE (Vattenfall), PL (Industria Polska) active engagement; design reset slowed but consortium intact. Multiple-EU-state pipeline strong but post-reset deployment timeline uncertain."},
    "c5_eu_exportability": {"modifier_pct": 5.0, "rationale": "Active engagement with ≥3 EU states (CZ, IT, NL, SE, PL all have signed cooperation agreements). Maximum +5%."},
    "c6_geopolitical_risk": {"modifier_pct": -1.0, "rationale": "Mostly French / EU exposure; minimal export-control friction (EU internal market). Modest risk from EDF financial restructuring and French energy policy continuity."},
    "c7_state_aid_risk": {"modifier_pct": -3.0, "rationale": "French nuclear state aid mature; CEE deployment requires individual State-aid clearances. Cross-border CfD structure not yet established for SMR."}
  },
  "c_modifier_pct_total": 19.0,
  "final_score": 3.93,
  "verdict": "eliminated",
  "verdict_drivers": [
    "A5 fail: post-reset design freeze targeted mid-2026; first COD slipped to mid-2030s; Romania COD-2033 unrealistic",
    "Highest Tier C modifier of any of the 9 designs (+19%, near maximum +20% cap) reflecting full European industrial fit",
    "Strongest European consortium and best-in-class designed-in cogeneration (+5% C3)",
    "If A5 evaluated against mid-2030s European fleet target → caution rather than fail; verdict converts to pending"
  ],
  "data_gaps_critical": [
    "Post-reset design freeze date (mid-2026 target)",
    "Post-reset 2x200 MWe safety case under JER Phase 3 review"
  ],
  "data_gaps_other": [
    "Per-MWe overnight CAPEX for post-reset design",
    "Quantitative grid-flexibility envelope post-reset",
    "First commercial COD date for any NUWARD plant"
  ]
}
```

## Analyst Summary

**Headline finding.** NUWARD is **eliminated** for **Romania COD-2033** by A5 (design freeze) failure — the post-July-2024 design reset means the conceptual design freeze is targeted only for mid-2026, with first COD slipping to mid-2030s. **For a mid-2030s European fleet target** (i.e., any Romanian site with COD ~2036+), A5 converts to caution and the verdict converts to `pending` at a final score of **3.93** (the second-highest computed final score after BWRX-300, before considering the A5 timing). The **+19 % Tier C modifier** is the highest of any of the nine designs and reflects the **best-in-class European industrial fit** (full EU consortium, French La Hague back-end, designed-in cogeneration, ≥3-EU-state pipeline).

**Key strengths.** First, the **fully European consortium** (EDF + TechnicAtome + Framatome + Naval Group + ČEZ + Edison/Ansaldo + Industria Polska + Vattenfall + ULC-Energy) drives the maximum C1 (+5 %), C2 (+5 %), C5 (+5 %) modifiers — the only design to achieve this triple maximum. Second, **designed-in cogeneration** (~100 MWt extraction option) is best-in-class — Romania's coal-replacement programme would benefit if district-heat coupling matters at the chosen site. Third, the **JER Phase 2 closure (Dec 2025)** by ASNR + STUK + SÚJB demonstrates real EU-coordinated regulatory progress, even if Phase 3 is in preparation. Fourth, **EDF as the most experienced PWR operator in Europe** (56-unit French fleet) provides the strongest operating-model credibility (B10 = 4) for Romanian deployment.

**Key weaknesses.** First, the **July 2024 design reset** is the single largest project-management risk — even the JER Phase 3 review must restart on the new 2x200 MWe configuration. Second, the **first COD date is publicly "mid-2030s" without a firm date** — no NUWARD plant is yet under construction anywhere. Third, **CNCAN engagement is limited** to trade-fair presentations — no pre-licensing dossier filed. Fourth, the **divergence between regulators on EPZ definition and passive safety system reliability** in the JER Phase 2 closure must be resolved before deployment in any new EU state.

**Most critical data gap.** The **post-reset design freeze date** — vendor target is mid-2026, but reset programmes routinely slip. Without design freeze, EPC contracting cannot proceed and first COD cannot be predicted with any confidence.

**What would change the verdict.** If the **mid-2026 design freeze is achieved** + **JER Phase 3 progresses on schedule** + **CNCAN pre-licensing is initiated for a Romanian site**, the verdict converts to `pending` at 3.93 and (on Phase 3 closure) potentially `shortlist_secondary`. NUWARD is best positioned as the **strongest "European next-cycle" candidate** — not in the running for Doicești but a credible front-runner for any Romanian site with COD ~2036-2040.
