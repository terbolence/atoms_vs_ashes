# SMR Technology Evaluation Methodology

**Project:** Atoms vs Ashes — SMR Siting Assessment for Coal-to-Nuclear Conversion in Central, Eastern, and Southern Europe
**Sponsor:** Government of Romania / Nuclearelectrica S.A. (SNN)
**Reference design:** NuScale ENTRA1 (NuScale Power Module, 6 × 77 MWe VOYGR configuration; 462 MWe gross) [^1]
**Comparator designs evaluated:** GE Vernova Hitachi BWRX-300; Rolls-Royce SMR; Holtec SMR-300; Kairos Power KP-FHR (Hermes); X-energy Xe-100; Oklo Aurora; TerraPower Natrium; NUWARD (EDF) [^2]
**Lead jurisdiction:** Romania (CNCAN) — secondary applicability: Bulgaria (BNRA), Czech Republic (SÚJB), Poland (PAA), Hungary (HAEA), Slovakia (ÚJD), and other CEE/SEE states
**Project COD target:** **2033 (Doicești ENTRA1 unit 1, per Feb 2026 FID); fleet rollout 2033–2040.** [^3]
**Document status:** v1.1 — supersedes v1.0 (which superseded the synthesis essay previously stored under `smr_evaluation_prompt.md`).

[^1]: ENTRA1 is the commercial vehicle for NuScale's 77 MWe Power Module as referenced in NEA SMR Dashboard 3rd Ed. (2025), p. 198. The 6-module 462 MWe configuration historically marketed as VOYGR-6 is the reference for this project. The 77 MWe US460 design received NRC Standard Design Approval on 29 May 2025 (NRC press release 25-033).
[^2]: NUWARD added in v1.1 (April 2026). The EDF NUWARD design was reset in January 2025 to a 400 MWe two-PWR configuration with cogeneration option (~100 MWt). Conceptual design freeze targeted for mid-2026; Joint Early Review Phase 3 began 21 January 2026 with FR/FI/CZ/PL/SE/NL regulators (IT as observer). Tier A5 (design freeze) caution at evaluation date.
[^3]: SNN final investment decision for the Doicești project was approved by shareholders on 12 February 2026. RoPower Nuclear S.A. (50/50 SNN + Nova Power & Gas / E-INFRA) is the SPV. Total estimated cost ~USD 4.9 billion (±20–30%). Romania has committed to funding only the first 77 MWe module initially; the remaining five modules are contingent on first-unit performance. Operational target ~2033 (per Romanian PM and SNN press materials Feb 2026).

---

## 1. Purpose and Scope

This document defines the methodology by which a candidate SMR design is evaluated for deployment on a coal-replacement site within the Atoms vs Ashes study region. It is the controlling reference for the LLM prompt in `smr_evaluation_prompt.md` and for any spreadsheet or matrix used in the technology down-selection.

Three filters are inherited from the project's input specification:

1. The design is licensable or in an advanced licensing process.
2. The design is deployable within approximately 7–10 years of FID (i.e. commercial operation no later than ~2033 for the Doicești unit and ~2040 for the broader fleet).
3. The design is capable of flexible operation in VRE-dominated grids.

These three are **necessary but not sufficient**. A credible European down-selection must additionally test whether the design can satisfy European safety objectives, fit the host-country infrastructure, secure fuel and waste pathways, be manufactured and built on schedule, and remain financeable and operable over decades. This methodology operationalises that broader screen, drawing on IAEA infrastructure guidance (NG-G-3.1, IAEA Milestones), the NEA SMR Dashboard (3rd edition, 2024) readiness dimensions, WENRA's application of new-reactor safety objectives to SMRs (RHWG report 2021, updated 2023), and EU requirements on nuclear safety (Directive 2014/87/Euratom) and spent fuel/waste management (Directive 2011/70/Euratom).

## 2. Structure of the Screen

A flat list of criteria is unsuitable for technology down-selection because criteria are not commensurable. This methodology uses three tiers:

| Tier | Type | Logic | Outcome |
|------|------|-------|---------|
| A | Hard gates | Binary pass / fail / data-gap | A single fail eliminates the design from the European deployment shortlist |
| B | Weighted criteria | 1–5 score × explicit weight | Aggregate weighted score (0–100) for shortlist ranking |
| C | Strategic-fit modifiers | ±% adjustment to the Tier B aggregate | Reflects alignment with the Romanian / EU industrial and policy strategy |

The 1–5 scoring scale is consistent with `requirements/06_scoring_matrix.md §8.1` and uses the same descriptors (Excellent / Good / Acceptable / Marginal / Poor). The Pass/Fail/Caution convention for hard gates is consistent with `screening_verdicts` in the project database schema.

**Confidence convention.** For every gate verdict and every Tier B score, evidence shall be tagged with one of: `direct_evidence` (vendor docs, regulator statement, peer-reviewed source), `indirect_evidence` (industry analysis, secondary reporting), `analyst_inference` (analyst reasoning from related facts), `data_gap` (no evidence found). A gate may be passed only on `direct_evidence` or `indirect_evidence`. A `data_gap` on a hard gate yields verdict `caution` and prevents shortlisting until the gap is closed.

---

## 3. Tier A — Hard Gates

A design is dropped from the European shortlist if any of the following gates is failed. A `caution` verdict (typically on `data_gap`) blocks shortlisting until resolved.

### A1. Jurisdictional licensability on a credible timeline

| Field | Specification |
|-------|---------------|
| Condition | The design has either (a) a CNCAN pre-licensing engagement with no unresolved showstopper, or (b) a completed licence/design approval in another credible jurisdiction (US NRC SDA/CP, UK GDA, Canadian VDR, French ASN review) plus a defensible mapping of that approval to CNCAN's national implementation of Directive 2014/87/Euratom. |
| Evidence required | (a) CNCAN public statement or vendor confirmation of pre-licensing activity; (b) regulator publication (NRC SDA, ONR/EA GDA decision, etc.); (c) WENRA-aligned safety case mapping. |
| Source authority | Directive 2014/87/Euratom; CNCAN regulatory framework; WENRA RHWG *Report on the Applicability of WENRA Safety Objectives to SMRs* (2021); IAEA SSR-1 (Rev.1). |
| Fail trigger | Pre-application has not started AND no foreign approval exists, AND a credible path to CNCAN approval before the project COD target has not been articulated. |

### A2. Front-end fuel supply with no exposure to sanctioned suppliers

| Field | Specification |
|-------|---------------|
| Condition | Credible, contractable supply for the first core and at least the first five reloads, sourced from suppliers not subject to EU restrictive measures. For HALEU-dependent designs, a non-Russian HALEU supply route must be identified (Centrus, Urenco, Orano, General Matter, or equivalent) **with a delivery date that matches the design's FOAK timeline**. |
| Evidence required | Vendor MoU or contract; Euratom Supply Agency (ESA) opinion or precedent; for HALEU, a **published commitment from a non-Russian enricher with a credible production schedule that aligns with the project COD target**. Press releases announcing intent are not sufficient. |
| Source authority | Euratom Treaty Chapter VI; ESA Annual Report; EU restrictive measures (Council Decisions on Russia); NEA SMR Dashboard fuel-readiness dimension; US DOE HALEU Availability Program documentation; Centrus/Urenco/Orano facility-status disclosures. |
| Fail trigger | Sole-source dependency on TVEL or any other sanctioned supplier; no credible non-Russian HALEU pathway for HALEU designs by project COD. **As of April 2026: Centrus 12 MT/yr commercial production target is "after 2030"; Urenco UK Capenhurst HALEU facility commissioning targeted 2031; DOE projects 50 MT/yr deficit by 2035; Russian HALEU import ban effective 2028.** Designs requiring HALEU first-core delivery before ~2030 have very weak evidence for `pass`. |

### A3. Spent-fuel, waste, and decommissioning compatibility with Romania's national programme

| Field | Specification |
|-------|---------------|
| Condition | The design's spent-fuel form, intermediate-level waste streams, and decommissioning concept are compatible with Romania's National Strategy for the Safe Management of Spent Fuel and Radioactive Waste, or a defensible amendment pathway exists. |
| Evidence required | Vendor waste characterisation; comparison against ANDR (Romanian Nuclear Agency) and the L&ILW disposal pathway at Saligny (DFDSMA); for non-LWR fuels (TRISO, metallic), explicit treatment of conditioning, transport, and interim storage. |
| Source authority | Directive 2011/70/Euratom; Romanian Government Decision 1259/2011 (and updates); IAEA SSG-23. |
| Fail trigger | The design produces a waste form for which no conditioning/disposal pathway has been articulated AND for which the host country's programme has not committed to development. |

### A4. No unresolved safety showstoppers

| Field | Specification |
|-------|---------------|
| Condition | The design demonstrates practical elimination of accident sequences with early or large releases, treats external hazards consistent with WENRA reference levels and IAEA SSG-9 / SSG-18 / SSG-21 / SSG-79, and has no unresolved generic safety issue raised by the lead regulator. |
| Evidence required | PSAR-equivalent safety case at Tier 1 or higher maturity; deterministic + probabilistic analyses; severe accident management strategy; source term analysis. |
| Source authority | WENRA RHWG safety objectives O1–O7 for new reactors; IAEA SSR-2/1; SF-1. |
| Fail trigger | Open safety issue rated as showstopper by any reviewing regulator, with no published resolution path. |

### A5. Design freeze sufficient for first commercial unit

| Field | Specification |
|-------|---------------|
| Condition | The design is at "Design Certification" or "Reference Design Frozen" status sufficient to support detailed engineering for a first commercial unit **before the project COD target — 2033 for Doicești unit 1, 2033–2040 for the broader European fleet**. FOAK engineering still open is acceptable provided it does not affect the safety case. |
| Evidence required | Vendor public design status; configuration management baseline; EPC engagement evidence. |
| Source authority | NEA SMR Dashboard (technical readiness dimension); IEC 62443 configuration baselines for I&C. |
| Fail trigger | Conceptual design only; major reactor-island components not at preliminary design; design freeze date later than ~24 months before required FID. |

### A6. Site-envelope fit for at least one credible site in the project portfolio

| Field | Specification |
|-------|---------------|
| Condition | The design's nominal cooling-water demand, footprint (including modular transport envelope), and exclusion-zone / EPZ assumptions are compatible with at least one of the candidate coal-replacement sites in the project's site database, given realistic European inland-river constraints (drought, summer river-temperature limits, low-flow events). |
| Evidence required | Vendor parameter envelope; project site database (`site_infrastructure_v2`, `site_natural_hazards`); IAEA SSG-18 hydrological screening. |
| Source authority | IAEA *Site Evaluation for Nuclear Installations* (SSR-1 Rev.1); IAEA SSG-18; EPRI Siting Guide 3002023910. |
| Fail trigger | Nominal once-through cooling demand cannot be met at any candidate site under drought conditions AND the design has no proven dry/hybrid-cooling variant. |

### A7. Financeable project structure

| Field | Specification |
|-------|---------------|
| Condition | A credible project-finance structure exists for the first European unit (vendor equity, EPC backing, host utility balance sheet, EU State-aid clearance pathway, eligible financing instrument such as a CfD, RAB, or PPA). For NuScale specifically, the Doicești FID (February 2026) is a positive precedent and may be cited. |
| Evidence required | Public financing arrangement, Letter of Interest from an export credit agency, EU State-aid notification or precedent (Hinkley Point C, Paks II), or a published RAB/CfD framework in the host country. |
| Source authority | NEA SMR Dashboard (financing readiness dimension); EU State-aid framework (TFEU Art. 107–108); EIB / ECA financing precedents. |
| Fail trigger | No financing pathway exists AND vendor is incapable of carrying the project on its balance sheet. |

---

## 4. Tier B — Weighted Criteria

Each criterion is scored 1–5 (descriptors per `requirements/06_scoring_matrix.md §8.1`). The weighted aggregate is

\[
S = \sum_i w_i \cdot c_i \quad \text{where } \sum_i w_i = 1.0
\]

The aggregate is reported on a 1–5 scale and on a normalised 0–100 scale (where 100 = "all 5s"). Below each criterion the table gives the scoring band, the data sources to consult, and the source authority.

### Weight allocation

| # | Criterion | Weight |
|---|-----------|--------|
| B1 | Safety-case robustness | 15% |
| B2 | Technology maturity / FOAK risk | 15% |
| B3 | Constructability and schedule realism | 10% |
| B4 | Supply-chain maturity | 10% |
| B5 | Fuel qualification status | 10% |
| B6 | Spent-fuel / waste / decommissioning fit | 10% |
| B7 | Site envelope and cooling resilience | 10% |
| B8 | Grid services / flexibility envelope | 5% |
| B9 | Security, safeguards, cyber by design | 5% |
| B10 | Operating model and staffing feasibility | 5% |
| B11 | Vendor / consortium credibility and lifecycle support | 5% |
| **Total** | | **100%** |

### B1. Safety-case robustness (weight 15%)

*Beyond Tier A4 (no showstoppers), this criterion scores the depth and quality of the demonstration.*

| Score | Condition |
|-------|-----------|
| 5 | PSAR or equivalent fully reviewed by a competent regulator; deterministic + Level 1/2 PSA published; severe accident management documented; external hazards (seismic, flood, extreme weather, aircraft impact) explicitly treated; source term independently challenged. |
| 4 | PSAR-equivalent submitted; PSA at Level 1, Level 2 in progress; external hazards treated against WENRA reference levels. |
| 3 | Pre-application safety case under review; Level 1 PSA only. |
| 2 | Conceptual safety case; PSA scope limited or not published. |
| 1 | No public safety case; safety claims rest on design philosophy only. |

**Source authority:** WENRA RHWG safety objectives O1–O7; IAEA SSG-3, SSG-4, SSG-9, SSG-18, SSG-79; EU Directive 2014/87/Euratom (preventing accidents and mitigating consequences).

### B2. Technology maturity / FOAK risk (weight 15%)

Decompose the headline "deployable in 10 years" into reactor core/fuel, balance-of-plant, digital I&C, and reference-plant status. Penalise the simultaneous introduction of multiple novel subsystems.

| Score | Condition |
|-------|-----------|
| 5 | Operating reference unit exists; first commercial unit under construction; no novel subsystem uniquely on critical path. |
| 4 | First commercial unit under construction; one or two novel subsystems remain to be qualified. |
| 3 | Detailed design complete; FOAK procurement underway; multiple subsystems still in qualification. |
| 2 | Design certification submitted; no construction; significant FOAK engineering open. |
| 1 | Conceptual or preliminary design only; novel core, fuel, and BoP introduced simultaneously. |

**Source authority:** NEA SMR Dashboard 3rd ed. — Licensing, Technology, and Siting readiness dimensions.

### B3. Constructability and schedule realism (weight 10%)

| Score | Condition |
|-------|-----------|
| 5 | Design freeze achieved; ≥70% factory fabrication; modular transportability confirmed; long-lead procurement contracted. |
| 4 | Design freeze in 12 months; ≥50% factory fabrication; long-lead items identified and supplier engagement under way. |
| 3 | Design freeze in 24 months; mixed factory/field fabrication. |
| 2 | Design freeze in >24 months; field-erection-dominated; long-lead items not characterised. |
| 1 | Construction philosophy not articulated; large unverified field-erection scope. |

**Source authority:** NEA SMR Dashboard (siting and supply-chain dimensions); INL/EPRI coal-to-nuclear constructability studies.

### B4. Supply-chain maturity and nuclear QA burden (weight 10%)

For Europe, this is a major discriminator. Score availability of qualified suppliers for heavy forgings, pressure boundaries, valves, instrumentation, control systems, and fuel; need for novel manufacturing; qualification status of critical materials and weld procedures; QA and traceability burden; geopolitical exposure of single-source vendors.

| Score | Condition |
|-------|-----------|
| 5 | All safety-class long-lead items have ≥2 qualified European or allied suppliers; novel manufacturing limited to vendor-internal facility with established capacity. |
| 4 | All safety-class long-lead items have ≥1 qualified supplier; second source under development. |
| 3 | Most long-lead items have qualified supply; one or two single-source dependencies on allied suppliers. |
| 2 | Multiple single-source dependencies; novel manufacturing processes still in qualification. |
| 1 | Sole-source dependency on a non-allied vendor for a safety-class long-lead item. |

**Source authority:** NEA SMR Dashboard (supply-chain readiness dimension); Foratom *European Nuclear Supply Chain* studies.

### B5. Fuel qualification status (weight 10%)

*Distinct from Tier A2 (front-end supply gate). This criterion scores qualification maturity of the fuel form, not the supply contract.*

| Score | Condition |
|-------|-----------|
| 5 | Standard LEU UO₂ assemblies with established qualification; commercial fabrication at multiple non-Russian facilities. |
| 4 | LEU UO₂ with minor design deviation; lead test assemblies in operation. |
| 3 | LEU+ (5–10%) with qualification under way; lead test assemblies inserted in commercial reactors. |
| 2 | HALEU with qualification programme under way; commercial fabrication facility under construction. |
| 1 | Novel fuel form (TRISO, metallic, molten salt) with qualification not yet at lead-test-assembly stage. |

**Source authority:** IAEA fuel qualification framework; NEA SMR Dashboard (fuel readiness dimension).

### B6. Spent fuel / waste / decommissioning fit (weight 10%)

*Beyond Tier A3 (compatibility gate), this criterion scores the favourability of the fit.*

| Score | Condition |
|-------|-----------|
| 5 | Standard PWR/BWR fuel form; volume per MWh within EU LWR experience; established conditioning/disposal route; published decommissioning cost basis. |
| 4 | Standard fuel form; minor non-standard ILW streams with documented conditioning. |
| 3 | Standard fuel form; some non-standard waste streams requiring new conditioning facility. |
| 2 | Non-standard fuel form (TRISO, metallic) with conditioning concept defined but not demonstrated. |
| 1 | Non-standard fuel form with no conditioning/disposal route articulated. |

**Source authority:** Directive 2011/70/Euratom; IAEA SSG-23, SSG-31, SSG-40; Romanian National Strategy for Spent Fuel and Radioactive Waste Management.

### B7. Site envelope and cooling resilience (weight 10%)

| Score | Condition |
|-------|-----------|
| 5 | Multiple cooling options proven (wet, dry, hybrid); land take ≤30 ha; transport envelope compatible with standard European road/rail; EPZ ≤ site boundary accepted by at least one regulator. |
| 4 | Wet + dry options; land take 30–50 ha; transport requires barge or oversize permit; EPZ ≤2 km. |
| 3 | Wet cooling only; land take 50–80 ha; standard transport; EPZ 2–5 km. |
| 2 | Wet cooling only with high water demand; land take >80 ha; major transport mitigation required. |
| 1 | Cooling-water demand exceeds drought-year availability at typical CEE coal sites; EPZ assumptions unaccepted by any European regulator. |

**Source authority:** IAEA SSR-1 Rev.1; IAEA SSG-18; EPRI Siting Guide 3002023910 (SMR refinements); project site database.

### B8. Grid services / flexibility envelope (weight 5%)

Score against a quantified envelope, not "load following yes/no".

| Score | Condition |
|-------|-----------|
| 5 | Minimum stable load ≤30%; ramp ≥5%/min; primary frequency control demonstrated; demonstrated cycling fatigue margin; black-start capability claimed and substantiated. |
| 4 | Minimum stable load 30–50%; ramp 3–5%/min; frequency control claimed. |
| 3 | Minimum stable load 50–70%; ramp 1–3%/min; load-following only. |
| 2 | Minimum stable load >70%; slow ramp (<1%/min); baseload-dominant. |
| 1 | Baseload-only operation with no flexibility provisions. |

**Source authority:** IAEA *Non-baseload Operation in Nuclear Power Plants* (NP-T-1.21, 2021); ENTSO-E grid code requirements for new generators.

### B9. Security, safeguards, cybersecurity by design (weight 5%)

| Score | Condition |
|-------|-----------|
| 5 | Safeguards-by-design integrated from the conceptual phase per IAEA STR-387; cyber architecture compliant with IEC 62645 / IEC 62859; physical protection concept reviewed by an IAEA INSServ-equivalent mission; insider-threat mitigation documented. |
| 4 | Safeguards-by-design partially integrated; cyber architecture aligned with IEC 62645. |
| 3 | Safeguards integration planned but not demonstrated; cyber concept articulated. |
| 2 | Safeguards and cyber architecture treated as bolt-on. |
| 1 | No public articulation of safeguards or cyber concept. |

**Source authority:** IAEA STR-387 *International Safeguards in the Design of Nuclear Reactors*; IAEA NSS-17; IEC 62645; WENRA/ENSREG cyber-security principles for the civil nuclear sector (2025).

### B10. Operating model and staffing feasibility (weight 5%)

| Score | Condition |
|-------|-----------|
| 5 | Operator staffing concept compatible with national licensing rules; control-room concept reviewed; training pipeline established; remote-monitoring claims (if any) consistent with regulator expectations. |
| 4 | Staffing concept articulated; training pipeline under development. |
| 3 | Generic staffing concept; training arrangements TBD. |
| 2 | Staffing concept underspecified or relies on remote-monitoring assumptions not yet accepted by any regulator. |
| 1 | No public operating-model documentation. |

**Source authority:** IAEA *Approaches to and Preparation for the Operation of Small Modular Reactors* (NR-T-2.18, 2024).

### B11. Vendor / consortium credibility and lifecycle support (weight 5%)

| Score | Condition |
|-------|-----------|
| 5 | Vendor balance sheet supports 60-year lifecycle commitment; EPC partner with European nuclear track record; warranty and performance guarantees articulated; spare-parts and obsolescence management documented; fuel take-back or back-end services included. |
| 4 | Strong vendor with EPC partner; warranty terms standard. |
| 3 | Vendor credible but EPC arrangements TBD; lifecycle support concept defined. |
| 2 | Start-up vendor with limited balance sheet; EPC and lifecycle support not yet structured. |
| 1 | Vendor financial sustainability over a 60-year asset life is in serious doubt. |

**Source authority:** NEA SMR Dashboard (commercial readiness dimension); vendor financial filings.

---

## 5. Tier C — Strategic-Fit Modifiers

These modifiers reflect alignment with Romanian and broader EU strategic objectives. Each modifier adjusts the Tier B aggregate by ±N%. The maximum cumulative modifier is +20% / −20% (i.e. modifiers cannot turn a failing design into a top scorer or vice versa).

| Modifier | Direction | Range | Applied when |
|----------|-----------|-------|--------------|
| C1. European industrial participation | Up | 0 to +5% | Vendor commits to ≥40% European supply-chain content, including a Romanian / regional industrial role. |
| C2. Energy sovereignty (non-Russian fuel cycle) | Up | 0 to +5% | Entire fuel cycle (enrichment + fabrication + back-end services) is contractable from EU/allied suppliers without transitional dependency on Russia. |
| C3. Cogeneration / district heat value | Up | 0 to +5% | Design supports steam extraction for district heating at temperatures and pressures usable by an existing or planned CEE district-heat network without significant safety or licensing penalty. |
| C4. Standardisation / fleet deployability across CEE | Up | 0 to +5% | Standard design suitable for multi-unit deployment at multiple CEE coal sites with common training, spares, and joint procurement potential. |
| C5. EU exportability to multiple states | Up | 0 to +5% | Design has signed MoUs or active engagement with ≥3 EU states within the project region. |
| C6. Concentrated geopolitical exposure | Down | 0 to −10% | Design has dependencies on suppliers in single jurisdictions where political risk could disrupt 60-year operation, even if not formally sanctioned. |
| C7. EU State-aid risk | Down | 0 to −5% | Project structure relies on State-aid instruments without precedent in the EU energy sector, raising clearance risk. |

---

## 6. Verdict Bands

The final verdict combines the Tier A pass status, the Tier B aggregate, and the Tier C modifier:

| Final score (Tier B × (1 + Tier C)) | All Tier A passed? | Verdict |
|-------------------------------------|--------------------|---------|
| ≥ 4.0 | yes | `shortlist_primary` — strong candidate for FOAK or NOAK European deployment |
| 3.0 – 3.99 | yes | `shortlist_secondary` — credible candidate; specific weaknesses to monitor |
| 2.0 – 2.99 | yes | `watch` — not shortlisted but worth re-evaluating in 24 months |
| < 2.0 | yes | `drop` — does not meet Tier B floor |
| any | no, but only on `data_gap` (`caution`) | `pending` — gate must be resolved before a final verdict |
| any | no (`fail`) | `eliminated` |

---

## 7. Evaluation-Matrix Template

One row per candidate design. The full row is produced by the LLM prompt in `smr_evaluation_prompt.md`.

| Field | Type | Source |
|-------|------|--------|
| `design_id` | text | e.g. `nuscale_voygr6` |
| `design_name` | text | Vendor and product name |
| `target_country` | text | Default `RO` |
| `evaluation_date` | date | ISO 8601 |
| `a1_licensability` | enum: pass / fail / caution | Tier A1 |
| `a1_evidence` | text + citations | |
| `a2_fuel_supply` | enum | Tier A2 |
| `a2_evidence` | text + citations | |
| `a3_waste_pathway` | enum | Tier A3 |
| `a3_evidence` | text + citations | |
| `a4_safety_showstoppers` | enum | Tier A4 |
| `a4_evidence` | text + citations | |
| `a5_design_freeze` | enum | Tier A5 |
| `a5_evidence` | text + citations | |
| `a6_site_fit` | enum | Tier A6 |
| `a6_evidence` | text + citations | |
| `a7_financeability` | enum | Tier A7 |
| `a7_evidence` | text + citations | |
| `b1_safety_case` … `b11_vendor_credibility` | int 1–5 | One column per Tier B criterion |
| `b1_rationale` … `b11_rationale` | text + citations | One per Tier B criterion |
| `b1_confidence` … `b11_confidence` | enum: direct / indirect / inference / data_gap | One per Tier B criterion |
| `b_aggregate_5pt` | float | Weighted average |
| `b_aggregate_100pt` | float | Normalised |
| `c_modifier_pct` | float | −20% to +20% |
| `c_modifier_breakdown` | text | Per-modifier contributions |
| `final_score` | float | b_aggregate × (1 + c_modifier_pct/100) |
| `verdict` | enum | Per §6 |
| `analyst_summary` | text | 200–400 word narrative |

---

## 8. Anti-Hallucination and Evidence Rules

The LLM prompt that operationalises this methodology MUST enforce the following:

1. Every gate verdict and every Tier B score must cite at least one source. Sources should be specific (vendor design control document, regulator decision, peer-reviewed paper, NEA Dashboard entry, IAEA publication, EU regulation), not "industry sources".
2. Where the model lacks evidence, it must use the confidence tag `data_gap` and produce verdict `caution` (Tier A) or score `null` with rationale (Tier B), not fabricate.
3. Vendor claims must be tagged as such (`vendor_claim`) and not treated as independently verified.
4. Regulator decisions must cite the regulator and decision identifier (e.g. *NRC SDA SMR-19, January 2023*).
5. For HALEU-dependent designs, the source on HALEU supply must be a published commitment (ESA, DOE, Centrus, Urenco, Orano), not a press release.
6. The output must not invent EPZ numbers, fuel cycle parameters, or land-take figures. If the figure is not in the model's training data, mark `data_gap`.

---

## 9. References (controlling documents)

- IAEA. *Milestones in the Development of a National Infrastructure for Nuclear Power* (NG-G-3.1 Rev.1, 2015).
- IAEA. *Site Evaluation for Nuclear Installations* (SSR-1 Rev.1, 2019).
- IAEA. *Site Survey and Site Selection for Nuclear Installations* (SSG-35, 2015).
- IAEA. *Non-baseload Operation in Nuclear Power Plants: Load Following and Frequency Control Modes of Flexible Operation* (NP-T-1.21, 2018).
- IAEA. *Approaches to and Preparation for the Operation of Small Modular Reactors* (NR-T-2.18, 2024).
- IAEA STR-387. *International Safeguards in the Design of Nuclear Reactors* (2014).
- WENRA RHWG. *Report on the Applicability of WENRA Safety Objectives to SMRs* (2021; rev. 2023).
- NEA. *Small Modular Reactor Dashboard, Third Edition* (2024).
- European Commission. Directive 2014/87/Euratom (nuclear safety).
- European Commission. Directive 2011/70/Euratom (spent fuel and radioactive waste).
- EPRI. *Advanced Nuclear Technology: Site Selection and Evaluation Guide* (3002023910, 2022).
- IEC 62645 / IEC 62859 (cyber security for I&C in nuclear facilities).
- WENRA / ENSREG. Joint principles on cybersecurity for the civil nuclear sector (2025).
- Romanian Government Decision 1259/2011 (and updates) — National Strategy for the Safe Management of Spent Fuel and Radioactive Waste.

---

## 10. Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-04-21 | Initial methodology. Supersedes the synthesis essay previously stored as `smr_evaluation_prompt.md`. Reorganised the original 15 criteria into the three-tier (gates / weighted / modifiers) structure; operationalised hard gates as testable conditions; added 1–5 scoring bands consistent with `requirements/06_scoring_matrix.md §8.1`; added explicit weights; added Romania-first jurisdictional anchor; added project-specific criteria (coal-site cooling resilience, EU State-aid financeability, Russian-fuel-free supply as its own gate, district-heat coupling, EPZ regulatory acceptance); added per-criterion source authority; added evaluation-matrix template; added anti-hallucination rules. |
| 1.1 | 2026-04-21 | Incorporated April 2026 evidence snapshot. (a) NuScale rebranded throughout to ENTRA1 (NuScale Power Module, 6 × 77 MWe VOYGR configuration), reflecting NEA Dashboard 3rd Ed. p. 198 and NRC US460 SDA approval 29 May 2025. (b) Project COD target updated from generic "~2036" to **2033 (Doicești unit 1, per SNN FID 12 February 2026), 2033–2040 fleet** — reflects Romanian PM and SNN public statements; total project cost ~USD 4.9B; phased payment (1 module first, 5 contingent). (c) Added NUWARD as 9th comparator with Tier A5 caution flag pending mid-2026 conceptual design freeze. (d) Tier A2 fail-trigger language strengthened with explicit 2026 HALEU supply snapshot (Centrus 12 MT/yr after 2030; Urenco Capenhurst 2031; DOE 50 MT/yr deficit by 2035; Russian import ban 2028). |
