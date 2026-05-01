# Report writing plan — master index

**Purpose.** Single editorial brief for preparing the final report: execution order, dependencies, section intents, tooling, and pointers to methodology artefacts.

**Status.** Living document — terrain-prep implementation underway. Update when DB version, sensitivity stamp, or rubric version freezes.

---

## 1. Dependency overview (what must happen first)

```
Scope + structure decision (Phase 0)
    → ToC cleanup (Phase 1)
        → Introduction draft 3.1–3.6 (Phase 2)
            → Part II — screening, criteria, technical basis (Phase 3)
                → Aggregate results + Intro §3.6 alignment (Phase 4)
                    → Site bundle export + LLM-assisted narratives (Phase 5)
                        → Conclusions, recommendations, references (Phase 6)
Executive standalone brief (Phase 7) — outline early; finalize metrics after final pipeline run
```

**Rule of thumb.** Name **once** in the Introduction: merged DB version / run ID, scoring rubric version, sensitivity analysis stamp, and any reference SMR case used for consistent narratives. Reuse those identifiers in Part II, country sections, and appendices.

---

## 2. Phase 0 — Freeze scope and audience

| Task | Notes |
|------|--------|
| Primary audience | Regulator-facing vs investor/policy vs internal — drives tone and depth of norm citations. |
| Reference SMR case (optional) | One vendor archetype for consistent “deployability” language in country sections — avoid implying licensing conclusions. |
| Structural choice | **Resolved in the canonical ToC:** keep Chapter 2 (**Stage 1: Site Survey**) and Chapter 3 (**Stage 2: Site Selection**) separate. Do not merge them into a single Part II unless [`tableOfContents.md`](tableOfContents.md) is changed first. |

### IAEA siting lifecycle (SSG-35) and report scope

**Publication work.** Reproduce the following **five-stage** framing in the final report Introduction (under §3.2 normative framework, or its own short subsection immediately after). Source alignment: `report/requirements/03_regulatory_framework.md` §5.2; primary IAEA procedural reference **SSG-35** (*Site Survey and Site Selection for Nuclear Installations*).

| Stage | Name | Purpose (summary) |
| ----- | ---- | ------------------- |
| 1 | **Site survey** | Regional analysis; identification of potential sites; screening to candidate sites |
| 2 | **Site selection** | Evaluation, comparison, and ranking of candidates → preferred site(s) |
| 3 | **Site characterization** | Confirmation of suitability; detailed characterization; design-basis parameters |
| 4 | **Pre-operational** | Confirmatory measurements and monitoring |
| 5 | **Operational** | Long-term monitoring and periodic safety review |

**Discuss in scope — Stages 1 and 2 only.** The report shall treat **site survey** and **site selection** (as named above) as the phases this study analyses end-to-end: desktop/API/LLM enrichment, criteria application, scoring, sensitivity, and ranking. **Stages 3–5 are out of scope** for substantive discussion (no claim to have performed characterization, licensing-grade investigation, or operational monitoring). Optional **one-sentence** pointers to Stage 3 as the **next** step for shortlisted sites are appropriate.

**Cross-link — SSG-35 §3.3 three-step process.** Also cite the **§3.3** sequence — (1) regional analysis → potential sites; (2) screening → candidate sites; (3) evaluation / comparison / ranking → preferred sites — and map it to project phases in `report/requirements/04_siting_methodology.md`. Using **both** the five-stage lifecycle (what this report covers vs later licence phases) and §3.3 (internal procedure) avoids ambiguity between “site survey” and “screening.”

**Data suitability vs later stages**

| Question | Answer for authors |
| -------- | ------------------- |
| Are merged DB + scoring + sensitivity adequate for **Stage 2** (selection / ranking)? | **Yes** — that is their purpose: exclusion, comparison, robustness of ranks. |
| Do they **replace Stage 3** (characterization, design basis)? | **No** — screening resolution; many SSR-1 requirements are only `partial` or deferred in `report/methodology/ssr1_traceability.md`; field programmes and regulator-facing detail sit in Stage 3. |
| Can outputs support a decision to **start** Stage 3 on shortlisted sites? | **Yes** — frame as “basis to authorise progression toward characterization,” not as a finished site evaluation for construction licensing. |
| Stages 4–5 | **Out of scope** — state explicitly if mentioned. |

**Deliverable.** Short scope paragraph for the Introduction opening **plus** the table and scope bullet above in the Introduction, so the master report matches this plan. The frozen editorial decision is recorded in [`phase_0_scope.md`](phase_0_scope.md).

---

## 3. Phase 1 — Skeleton and navigation

| Task | Notes |
|------|--------|
| Restructure [`report/output/writing plan/tableOfContents.md`](tableOfContents.md) (canonical master ToC) | **Indentation and hierarchy only** — preserve verbatim wording of criteria, thresholds, weights, notes (including Romanian bullets). Break the single-line §2 stream into nested markdown lists (`2.1`, `2.5.2`, criterion families NH / HI / RI / EP / NS, etc.). Stub: [`report/output/tableOfContents.md`](../tableOfContents.md) redirects here. |
| Repair methodology artefacts table | The markdown table under “Methodology artefacts” must have aligned columns (Artefact \| Path \| Generator). |

**Deliverable.** Readable ToC as editorial checklist; working links.

---

## 4. Phase 2 — Introduction (structured subsections)

Draft in **this order** so each subsection builds on the previous.

### 4.1 §3.1 — Coal-to-nuclear transition (policy alignment)

- Why coal-adjacent or repurposed sites matter: grid, cooling, workforce, land reuse, climate/security narratives (as appropriate).
- Align language with **U.S. DOE** coal-to-nuclear / advanced reactor siting materials — cite **exact** program titles and documents from official sources when drafting (do not paraphrase without references).
- Clear **scope boundary**: what this study does *not* decide (licensing, vendor selection, commercial structure).

### 4.2 §3.2 — Normative framework — IAEA vs EPRI

- **IAEA lifecycle:** Include the **five-stage SSG-35 table** and explicit statement that this report covers **Stages 1–2 only** (see Phase 0 — IAEA siting lifecycle). Add **§3.3** three-step process + pointer to `04_siting_methodology.md`.
- **IAEA requirements:** SSR-1 / NS-G / GSR-style framing — safety objectives and graded approach for siting.
- **EPRI / industry:** Where practice-level guidance complements IAEA language.
- **Deliverable:** Comparison table — Theme \| IAEA articulation \| EPRI / industry \| **Project stance** (which framing drives each criterion family).
- **Data limits:** One short paragraph that screening data support **Stage 2** and **progression toward** Stage 3, but do **not** substitute characterization (consistent with `ssr1_traceability.md`).
- Link internal traceability: `report/methodology/ssr1_traceability.md` (generator: `scripts.generate_ssr1_traceability`).

### 4.3 §3.3 — Report methodology — data (merged DB)

- Single narrative: **API / deterministic connectors + LLM enrichment → merged database** — describe **latest merged form only**; avoid connector-by-connector detail unless an appendix is needed.
- **Per-criterion limitations matrix:** Criterion family \| Data type \| Main limitation \| Confidence (high / medium / low).
- Broad strokes only on sources (spatial domains, temporal coverage, LLM extraction caveats).

### 4.4 §3.4 — Scoring methodology and norm alignment

- Why scoring matters: auditable mapping from indicators to outcomes (pass/fail, bands, ranks).
- Point to generated artefacts:
  - `report/methodology/exclusionary_floors.md` — `scripts.generate_exclusionary_floors`
  - `report/methodology/swing_weight_audit.md` — `scripts.generate_swing_weight_audit`
  - `report/methodology/ssr1_traceability.md`
- Narrative: alignment with **graded approach** and traceability — avoid overstating “regulatory proof.”

### 4.5 §3.5 — Sensitivity methodology and norm alignment

- Reference: `report/methodology/sensitivity_analysis.md`; regional/national packs under `report/output/sensitivity/<stamp>/`.
- Frame sensitivity as **robustness / uncertainty exploration** of rankings — not a substitute for licensing or deterministic compliance.

### 4.6 §3.6 — Cross-country view — top sites and overall rankings

- Per country: up to **10** sites (or fewer if fewer candidates) — summary table.
- Global synthesis: **scoring vs sensitivity** — agreement and divergence; why rankings shift when they do.
- Must **match** frozen outputs from Phase 4 before country narratives are finalized.

### 4.7 §3.7 — Country deep dives (overview only in Introduction)

- State that detailed per-country site presentations follow in the body; point to editorial rule (§8 below).

### 4.8 §3.8 — Executive technical brief (pointer)

- One paragraph pointing to the **standalone executive document** (Phase 7): how the system was built, metrics, gaps — not the full methods dump.

---

## 5. Phase 3 — Stage 1 and Stage 2 chapter terrain

### 5.1 Canonical structure

Use the current ToC structure:

- Chapter 2 — **Stage 1: Site Survey**
- Chapter 3 — **Stage 2: Site Selection**
- Annexes — traceability, scoring, sensitivity, failure analysis, assumptions, and generated artefact references

The implementation terrain lives under `report/output/chapters/` and `report/output/annexes/`.

### 5.2 Earlier merge option (superseded)

Use one major part, e.g. **Part II — Site screening, criteria, and technical basis**:

| Block | Content |
|-------|---------|
| II.1 | Scope and screening workflow |
| II.2 | Candidate sites — identification and description |
| II.3 | Evaluation framework (scoring architecture) |
| II.4 | Safety-related — natural hazards (+ supplemental geology / seismic / dispersion topics placed next to relevant NH criteria) |
| II.5 | Safety-related — human-induced (+ supplemental roads/rail/industry where linked) |
| II.6 | Radiological & emergency planning (+ supplemental dispersion / emergency feasibility) |
| II.7 | Non-safety & socioeconomic |
| II.8 | Data limitations, results, conclusions, recommendations for detailed evaluation |

### 5.3 If keeping separate chapters (selected)

- Old §2 = process + scoring lists.
- Old §3 = each subsection titled **Technical supplement to criterion …** with bidirectional links.

### 5.4 Editorial consistency

- Criterion order follows project rubric (NH → HI → RI / EP → NS → land use / socioeconomic).
- Figures: maps / contours where promised in ToC; cite methodology artefacts instead of duplicating long tables in prose.

---

## 6. Phase 4 — Aggregate results that anchor the narrative

| Task | Notes |
|------|--------|
| Freeze outputs | Use one **sensitivity stamp** (e.g. `report/output/sensitivity/20260425b/` or successor) and matching scoring exports under `audit/post_processing/06_scoring/` as cited in project practice. |
| Tables / figures | Country top-N, global rankings, failure-mode summaries — align with `report/methodology/failure_analysis*.md` and national markdown under `report/output/sensitivity/<stamp>/national/`. |
| Introduction §3.6 | Update numbers and prose **after** this freeze so Intro does not contradict Part II and country sections. |

---

## 7. Phase 5 — Site-level narratives (§3.7 execution detail)

### 7.1 Editorial rule — how many sites per country

- User-owned decision; **default heuristic:** **3–5** sites per country, capped by **min(10, available strong candidates)**.
- Reduce count when suitability is weak or **US-made SMR** deployment narrative would be speculative — say fewer sites with clearer caveats.
- Countries with very few viable sites may show **1–2** only.

### 7.2 Data bundle (prerequisite for LLM)

- **Script responsibility:** `export_site_bundle(site_id)` / `(country_code, site_id)` — returns structured JSON (or equivalent) including:
  - All criterion fields and quality flags
  - Commentary / LLM fields where present
  - **Ownership** and related attributes — for conservative interpretation only
  - Scoring outcomes, bands, failure reasons
  - Sensitivity outcomes for chosen stamp
  - References to map assets if stored as paths
- Goal: **one machine-readable “everything we know about this site.”**
- Implementation terrain: `src/scripts/export_site_bundle.py` (thin CLI) and `src/atoms_vs_ashes/reporting/site_bundle.py` (read-only bundle builder).

### 7.3 System prompt — expert site describer (template behaviour)

The prompt should enforce:

1. **Role:** Senior nuclear siting analyst; audience = policy / investment / strategic — not a licensing submission.
2. **Opening:** One short paragraph — site purpose in a coal-to-nuclear / repowering context; no overclaim.
3. **Per criterion family** (NH, HI, RI, EP, NS): value → quality → significance for SMR siting → stated limitation.
4. **Ownership:** Interpret only what the DB supports; flag gaps; avoid legal conclusions.
5. **US SMR angle:** Evidence-based, cautious — grid, water, infrastructure, procurement context — **not** NRC outcomes.
6. **Residual risks:** Top 3 concerns in a compact register style.
7. **Fixed headings** so assembled chapters are uniform.

Prompt terrain: `prompts/site_describer.md`.

### 7.4 LLM execution

- **Suggested models:** **Opus-class** for highest-quality first drafts of dense technical synthesis; **Sonnet-class** for bulk generation with stronger human edit pass — choose by volume and budget.
- **Workspace rule:** No live **Anthropic** (or other paid external API) calls without **explicit user consent** after stating scope and estimated cost.
- **Workflow:** Generate draft → **mandatory human review** for ownership wording and any country-specific political/legal sensitivity.

---

## 8. Phase 6 — Closing report body

| Section | Content |
|---------|---------|
| Results and conclusions | Synthesize screening + scoring + sensitivity; reference frozen stamp. |
| Recommendations for detailed site evaluation | Field investigation, data gaps to close, suggested specialist studies. |
| Final remarks | Limitations, forward look. |
| References | DOE, IAEA, EPRI, plus internal methodology paths as cited. |

---

## 9. Phase 7 — Executive standalone document (§3.8)

**Audience:** Executives — **short**, non-technical where possible.

**Suggested sections:**

1. Objective and scope of the automated assessment system  
2. Broad process overview (pipeline phases)  
3. Data acquisition — API vs LLM at high level  
4. Merge, QA, versioning  
5. Data gaps and certainty by method  
6. Operational metrics — human workload, token usage (if tracked), run IDs, dates — **finalize after last production run**  
7. Clear **limitations** — decisions this output does **not** replace  

**Note.** Outline this section early; **finalize metrics** after Phase 5 or final scoring/sensitivity freeze so numbers are honest.

---

## 10. Methodology artefacts — quick reference

Use and cite these under Introduction (data limits, scoring, sensitivity) and Part II as needed. Paths relative to repo root `report/methodology/` unless stated otherwise.

| Artefact | Path | Generator / note |
|----------|------|-------------------|
| Sensitivity method + reference run | `report/methodology/sensitivity_analysis.md` | `scripts.run_phase_1_6_sensitivity`; narrative partly manual |
| Failure analysis — global | `report/methodology/failure_analysis.md` | `scripts.generate_failure_analysis` |
| Failure analysis — NuScale VOYGR-6 | `report/methodology/failure_analysis_nuscale_voygr6.md` | `scripts.generate_failure_analysis --smr-nuscale` |
| Failure analysis — other vendor packs | `report/methodology/failure_analysis_<smr_key>.md` | `scripts.generate_failure_analysis --smr-<vendor>` |
| Exclusionary floors | `report/methodology/exclusionary_floors.md` | `scripts.generate_exclusionary_floors` |
| Swing-weight audit | `report/methodology/swing_weight_audit.md` | `scripts.generate_swing_weight_audit` |
| Criterion correlation (e.g. ρ ≥ 0.7) | `report/methodology/criterion_correlation.md` | correlation figure scripts / Phase 1.6 figures |
| SSR-1 traceability | `report/methodology/ssr1_traceability.md` | `scripts.generate_ssr1_traceability` |
| Assumption register | `report/methodology/assumption_register.md` | Manual; version with rubric |
| Regional / national sensitivity | `report/output/sensitivity/<stamp>/` | `scripts.run_phase_1_6_extended_analysis` |

---

## 11. Related repo conventions

- **`report/output/**`** — exempt from the generic ≤500-line markdown split rule. This includes writing plans, assembled chapters, annexes, executive briefs, sensitivity notes, and generated report-output markdown.
- Other markdown under `report/` — if a single file grows past 500 lines, split into numbered files + `index.md` per `.cursor/rules/file-size-markdown.mdc`.

---

## 12. Checklist (copy for tracking)

- [x] Phase 0 terrain: Audience, reference SMR convention, structural choice, and Stage 1-2 scope recorded in [`phase_0_scope.md`](phase_0_scope.md).  
- [x] Phase 1 terrain: Canonical high-level ToC and artefact table exist in [`tableOfContents.md`](tableOfContents.md); root stub redirects from [`../tableOfContents.md`](../tableOfContents.md).  
- [x] Phase 2 terrain: Introduction refreshed within §1.1-§1.6, with `20260425b` anchor, methodology links, site-profile pointer, and executive-brief pointer.  
- [x] Phase 3 terrain: Chapter and annex stubs created under `report/output/chapters/` and `report/output/annexes/`.  
- [x] Phase 4 terrain: Frozen-stamp numbers aligned in Introduction §1.5 and Chapter 4 stub.  
- [x] Phase 5 terrain: Site bundle schema/script and expert site-describer prompt prepared; no live API calls made.  
- [x] Phase 6 terrain: Results, recommendations, final remarks, and references stubs ready for section-by-section drafting.  
- [x] Phase 7 terrain: Executive technical brief outlined with placeholder metrics and limitations.  

---

*Last updated: align with project scoring/sensitivity stamp at time of report freeze.*
