Reliability Comparison: API-Based System vs. LLM Expert Prompts vs. Actual Study
Your Two Methods
Method A — Norms-based + API pipeline (what you're building): Extract criteria from IAEA SSG-35 / EPRI → identify data requirements → query authoritative APIs (EFEHR, EGDI, CORINE, Natura 2000 WFS, etc.) → deterministic pass/fail against YAML thresholds.

Method B — LLM expert prompts (your manual ChatGPT run): One expert prompt per criterion per site, 7–9 prompts per site, sequential. Could be parallelized.

Reliability Estimates for Eliminatory Criteria (E1–E9)
Here's my assessment, criterion by criterion:

Criterion API Pipeline (Method A) LLM Prompts (Method B) Why the gap
E1 Capable fault (8 km)
~85–90%
~60–75%
EFEHR/SHARE + GEM rasters give precise PGA and fault geometry. LLMs know major faults but lack precise distance calculations and may miss smaller capable faults.
E2 Liquefaction
~70–80%
~50–65%
EGDI geology layers provide lithology/soil data for proxy assessment. LLMs can identify obviously problematic areas but lack site-specific geotechnical resolution.
E3 Slope instability
~75–85%
~55–70%
DEM-derived slope + landslide inventories are quantitative. LLMs can flag known landslide-prone regions but miss localized risk.
E4 Volcanism
~90–95%
~85–90%
GVP database is definitive; volcanic hazard zones are well-documented. LLMs actually do well here — volcanoes are prominent, well-known features. Smallest gap.
E5 Karst
~65–75%
~45–60%
EGDI karst layers exist but coverage varies. LLMs know major karst regions (e.g., Apuseni, Mehedinti) but can't distinguish "massive karst threatening foundations" from minor karst features.
E6 Subsidence/collapse
~60–70%
~40–55%
Mining void data is often national/proprietary. Both methods struggle — this typically requires national mining cadastre data.
E7 Protected areas
~90–95%
~75–85%
Natura 2000 WFS + WDPA are authoritative and boundary-precise. LLMs know major protected areas but may miss smaller Natura 2000 sites or get boundaries wrong.
E8 EPZ infeasibility
~55–65%
~50–65%
Both methods struggle — this requires population distribution analysis, road network assessment, and institutional judgment. Closest gap — both are proxies for what requires real emergency planning analysis.
E9 Cooling water
~80–85%
~65–75%
Hydrological data + OSM water features give flow/proximity. LLMs know major rivers but can't assess minimum flow rates or seasonal availability.
Overall Reliability vs. Actual Study
Method Estimated Agreement with Full Study Confidence in Exclusion Decisions False Negative Risk (missing a real exclusion) False Positive Risk (excluding a viable site)
API Pipeline
~75–85%
Moderate-High
Low-Moderate
Moderate (conservative is acceptable)
LLM Prompts
~55–70%
Low-Moderate
Moderate-High
Moderate
Actual Study (PSAR-level)
Baseline (100%)
High
Low
Low
Key Insights

1. Where LLMs are surprisingly decent:

Volcanism (E4) — volcanoes are famous, well-catalogued, and LLMs have strong training data
Protected areas (E7) — major parks/reserves are well-known
Cooling water (E9) — major rivers near coal plants are well-documented 2. Where LLMs are dangerous:

Capable faults (E1) — the 8 km threshold requires precise spatial measurement, not general knowledge. An LLM might say "no major fault nearby" when there's a capable fault 6 km away
Karst/liquefaction (E2, E5) — these are geologically subtle, spatially heterogeneous, and require subsurface data
Subsidence (E6) — mining void data is often not in LLM training data at all 3. The fundamental problem with LLM prompts for eliminatory criteria:

No spatial precision — LLMs cannot measure distances, calculate buffer zones, or intersect geometries
Training data cutoff — geological hazard maps are updated; LLMs may have outdated information
Hallucination risk on binary decisions — for a pass/fail criterion, a confidently wrong answer is worse than no answer. LLMs can fabricate plausible-sounding geological assessments
No provenance — you can't trace an LLM's "no capable fault within 8 km" back to a specific fault database record, which your QA framework (IAEA QA 13.1.6) requires 4. Where the API pipeline also falls short vs. actual study:

Both methods are desk studies — a real siting study includes field investigations, borehole data, local institutional knowledge
API data resolution varies by country — Romania has decent EGDI coverage but gaps exist
E8 (emergency planning) genuinely requires human expert judgment in both cases
The Parallelized LLM Approach — Is It Worth It?
Running 7–9 prompts per site in parallel would indeed be fast (minutes vs. hours for the API pipeline setup). But I'd frame it as a useful triage/pre-screening tool, not a reliable eliminatory screen:

Good for: Quickly identifying obviously excluded sites (e.g., a coal plant next to a volcano, inside a national park, or with no water source) — probably 15–25% of sites could be confidently excluded this way
Risky for: The borderline cases that actually matter — a site 7 km from a capable fault, a site with moderate karst, a site where cooling water is marginal
Useful hybrid: Run LLM pre-screening to prioritize which sites to run through the full API pipeline first, rather than as a replacement
Recommendation
The two methods are complementary, not competing:

LLM prompts as a fast Phase 0 triage — flag obvious exclusions and rank sites by likely viability (hours, not days)
API pipeline as the Phase 1 formal screen — deterministic, traceable, reproducible (what your architecture is designed for)
Expert review as the human gate your methodology already requires
This aligns with what your requirements already state — exclusion decisions require human approval, and the system must be reproducible and traceable. The LLM approach fails on traceability, which is a regulatory requirement, not just a nice-to-have.
