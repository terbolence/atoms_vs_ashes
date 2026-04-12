"""E1-E9 exclusionary criterion prompts (Tier 1 — Claude Sonnet 4 + thinking)."""

from atoms_vs_ashes.llm.prompts._base import SYSTEM_BASE

PROMPT_VERSION = "v2.0-2026-04-12"

_EXCLUSIONARY_PREAMBLE = """

PHASE: Exclusionary Screening (IAEA Step 2 / EPRI Step 1)
VERDICT: pass (no exclusion), fail (site excluded), inconclusive (insufficient evidence).
A "fail" on ANY exclusionary criterion eliminates the site permanently. \
This is an irreversible decision — err on the side of caution.

THINKING PROTOCOL — Use your extended thinking to follow these steps IN ORDER:
1. RECALL: What do I factually know about this specific site's location, \
   geology, geography, and surroundings? Name specific features, not generalities.
2. ENRICHMENT CHECK: If API enrichment data is provided, does it confirm or \
   contradict my recall? If it provides a quantitative value (distance, PGA, etc.), \
   use that as my primary anchor and explain whether my own knowledge supports it.
3. ANALYSE: Apply the criterion's threshold to the evidence gathered. Show \
   the specific comparison (e.g., "nearest fault is ~X km vs. 8 km threshold").
4. ADVERSARIAL CHECK: Before committing to my verdict, argue the opposite case. \
   If I'm leaning "pass", what evidence could make this a "fail"? If I'm leaning \
   "fail", what mitigating factors could make this a "pass"? If I cannot identify \
   any counter-argument, my confidence is high. If I can, assess how strong it is.
5. VERDICT: Only now decide. If the adversarial check revealed genuine uncertainty \
   about whether the threshold is triggered, return "inconclusive" — not a guess.

DISTANCE ESTIMATION — Since you cannot perform geometric calculations:
- Use known landmarks as anchors (e.g., "the plant is in X city, the fault \
  passes through Y town, these towns are approximately Z km apart").
- If the enrichment data provides a distance, treat it as more reliable than \
  your own estimate. State any discrepancy and which value you trust more.
- When you estimate distances, always give a range (e.g., "approximately \
  15-25 km") rather than a false-precision single number.
- Never claim a distance is "exactly" anything. All your distances are \
  approximate.

OUTPUT FORMAT — Your justification MUST follow this structure:
- Sentence 1: State what you found (the hazard feature, its location, your \
  evidence basis). Label as FACT, INFERENCE, or UNKNOWN.
- Sentence 2: State the distance/metric and how you estimated it. Label.
- Sentence 3: Compare to the threshold. State whether it is triggered.
- Sentence 4-6: State any caveats, adversarial considerations, or data gaps \
  that affect confidence. Label each."""

_E1 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E1 — Capable Fault Proximity (Exclusionary)
NORMATIVE BASIS: SSG-35 Annex II Table II-1 No.1; NS-R-3 §3.7; SSG-9 Rev.1
THRESHOLD: Site within 8 km of a capable fault → EXCLUDE

DEFINITION: A "capable fault" per IAEA is a fault that has shown movement \
in the Quaternary period (last 2.6 Ma) and is considered capable of \
generating surface rupture. This is stricter than "active fault" — not \
all active faults are capable faults.

ANALYTICAL STEPS:
1. Identify the site's tectonic domain. Which of these does it belong to:
   - East European Platform / Baltic Shield (stable, very few capable faults)
   - Pannonian Basin (moderate, basin-margin faults)
   - Carpathian Orogen (moderate-high, thrust faults)
   - Dinaric Alps (moderate, complex microplate boundaries)
   - North Anatolian Fault Zone (high, strike-slip system)
   - Vrancea Deep Seismicity Zone (unique — deep seismicity, few surface faults)
   - South Caucasus (high, Bitlis-Zagros collision zone)
   - Balkan extensional zone (moderate, normal faults)
2. Identify the nearest KNOWN capable fault by name. If you cannot name a \
   specific fault, say so — do not invent one.
3. Estimate the distance from the site to that fault. Use city/town \
   spacing as calibration anchors.
4. If the enrichment data includes nh02_nearest_fault_km, compare your \
   estimate to it. If they differ by >50%, explain why and state which \
   you trust more.
5. Apply the 8 km threshold. If the nearest capable fault is >20 km away, \
   this is a confident "pass". If 8-20 km, assess carefully. If <8 km, \
   this is a "fail".

CRITICAL REGIONAL FEATURES (search your knowledge for these):
- North Anatolian Fault (NAF): ~1200 km, passes through northern Turkey. \
  Any plant within 20 km of the NAF trace needs careful assessment.
- East Anatolian Fault (EAF): southeastern Turkey, active.
- Vrancea seismic zone: deep earthquakes (70-180 km depth) but few \
  surface-capable faults. Surface faulting is the criterion, not deep seismicity.
- Pannonian Basin margins: Zagreb fault, Balaton line, Diósjenő fault zone.
- Rhodope-Thrace: Maritsa fault zone, Kavala-Xanthi-Komotini fault.
- Dinaric thrust front: runs from Slovenia to Albania.
- South Carpathian fault zone: Olt Valley faults, Jiu Valley faults.
- Dead Sea Transform northern extension: affects far SE Turkey.

COMMON PITFALL: Confusing high seismicity with capable fault proximity. \
The Vrancea zone produces M7+ earthquakes but from 100+ km depth — surface \
faulting is not the issue there. PGA may be high but this criterion is about \
SURFACE CAPABLE FAULTS within 8 km, not seismicity generally.

REFERENCE DATA SOURCES: SHARE ESHM20, GEM Global Active Faults Database \
(GAF-DB), Basili et al. 2013 European Database of Seismogenic Faults (EDSF), \
national geological surveys (PGI Poland, MTA Turkey, IGR Romania, CGS Czech \
Republic), EMSC/ISC earthquake catalogues, Woessner et al. 2015 SHARE fault \
model."""

_E2 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E2 — Massive Soil Liquefaction (Exclusionary)
NORMATIVE BASIS: NS-R-3 §3.38–3.40; SSG-9 Rev.1 §4
THRESHOLD: Unacceptable liquefaction potential with no engineering remedy → EXCLUDE

DEFINITION: Liquefaction occurs when saturated loose granular soils lose \
strength during seismic shaking. IAEA requires exclusion only when \
liquefaction potential is MASSIVE and no practicable engineering remedy \
exists. Standard ground improvement (compaction, stone columns, piling) \
can mitigate moderate liquefaction — only truly massive, site-wide \
liquefaction in deep loose sediments triggers exclusion.

ANALYTICAL STEPS:
1. Determine the surface geology at the site. The key question: is the \
   site on loose, saturated granular soil (alluvium, sand, loess) or on \
   competent ground (clay, bedrock, engineered fill)?
2. Assess groundwater depth. Liquefaction requires saturation — sites with \
   deep water tables (>15 m) have very low risk regardless of soil type.
3. Assess regional seismicity. Liquefaction correlates with PGA: <0.1g = \
   very low risk, 0.1-0.2g = moderate, >0.2g = elevated. Use pga_475yr_g \
   from enrichment data if available.
4. CRITICAL MITIGATING FACTOR: This site has/had a coal power plant. \
   Coal plants require heavy foundations, compacted subgrade, and often \
   piled foundations. The existing foundation engineering likely mitigates \
   liquefaction at the specific plant footprint, even if the surrounding \
   area is susceptible. This should push your assessment toward "pass" \
   unless the entire area shows massive liquefaction features (sand boils \
   in historical earthquakes, known liquefaction incidents).
5. Check for historical liquefaction events in the area. These are the \
   strongest evidence.

DECISION FRAMEWORK:
- Bedrock or stiff clay site + any seismicity → pass (high confidence)
- Alluvial site + low seismicity (PGA < 0.1g) → pass (medium confidence)
- Alluvial site + moderate seismicity + coal plant foundations → pass \
  (medium confidence, note brownfield mitigation)
- Alluvial site + high seismicity + historical liquefaction → inconclusive \
  or fail (needs site investigation)
- Deep loose sand + shallow water table + high PGA + no engineering \
  remedy feasible → fail

REFERENCE DATA SOURCES: OneGeology / EGDI surface lithology maps, \
national geological surveys 1:50k / 1:200k sheets, European Soil Database \
(ESDB), SHARE ESHM20 for regional PGA, EGDI hydrogeological maps, \
historical earthquake damage reports (CFTI for Turkey, INFP for Romania)."""

_E3 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E3 — Massive Slope Instability (Exclusionary)
NORMATIVE BASIS: SSG-35 Table I-1; NS-R-3 §3.41–3.43
THRESHOLD: Catastrophic landslide risk with no engineering remedy → EXCLUDE

ANALYTICAL STEPS:
1. Determine the site's terrain. Coal plants are almost always built on \
   flat or gently sloping terrain (they need level ground for boilers, \
   turbines, coal stockpiles, cooling towers, and rail sidings). If the \
   site is a coal/thermal plant on flat terrain, massive slope instability \
   at the site itself is essentially impossible.
2. However, check for SURROUNDING slopes that could threaten the site: \
   valley walls, hillsides above the site, unstable cut slopes.
3. Identify the geological setting — flysch, marl, weathered clay \
   formations are landslide-prone. Granite, limestone, sandstone are \
   generally stable.
4. Check for known landslide inventories in the region.
5. This is expected to be one of the most commonly-passed exclusionary \
   criteria, since coal plants on flat ground cannot have massive slope \
   instability. Be explicit about this when it applies — a clear, \
   high-confidence "pass" with the rationale "industrial site on flat \
   terrain" is the correct answer for most sites.

DECISION FRAMEWORK:
- Flat site (<5° slope), no surrounding steep terrain → pass (high confidence)
- Flat site but in a known landslide-prone region (e.g., Carpathian flysch \
  zone) → pass (medium confidence, note surrounding risk)
- Hillside site or steep terrain → needs careful assessment
- Known landslide area + steep slopes + weak geology → inconclusive or fail

REFERENCE DATA SOURCES: European Landslide Susceptibility Map (ELSUS v2, \
JRC), national landslide inventories (SOPO Poland, IGME Turkey), COPERNICUS \
EU-DEM / SRTM for slope estimation, EGDI surface lithology."""

_E4 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E4 — Active Volcanism (Exclusionary)
NORMATIVE BASIS: SSG-35 Table I-1; SSG-21
THRESHOLD: Site within hazard zone of lava flow, pyroclastic flow, or \
massive lahar → EXCLUDE

ANALYTICAL STEPS:
1. First determine: does the site's COUNTRY have any Holocene volcanism?
   - Countries with NO Holocene volcanism (confident pass): PL, CZ, SK, \
     HU, AT, SI, HR, BA, RS, ME, XK, AL, MK, RO, BG, MD, UA, BY, EE, \
     LV, LT. These countries have had no volcanic eruptions in the \
     Holocene (~11,700 years). Return pass with high confidence and set \
     nearest_holocene_volcano_km to 9999.
   - Countries WITH Holocene volcanism: TR (multiple), AM (Ararat area).
2. For Turkey and Armenia sites ONLY, identify the nearest Holocene volcano:
   - Turkey: Nemrut Dağı, Süphan Dağı, Tendürek Dağı, Ağrı Dağı (Ararat), \
     Erciyes Dağı, Hasan Dağı, Karacadağ, Kula volcanic field. Most are \
     in eastern Turkey — western Turkish coal plants are generally safe.
   - Armenia: Aragats, Ararat (on Turkish border), Porak, Ghegam Ridge.
3. Estimate the distance from the site to the nearest volcano.
4. Determine whether the site is within a recognized volcanic hazard zone \
   (lava flow, pyroclastic flow, lahar — typically within 30-50 km of \
   a stratovolcano, much less for monogenetic fields).
5. Volcanic hazard maps typically define zones: Zone A (<5 km — extreme), \
   Zone B (5-15 km — high), Zone C (15-30 km — moderate). Being in \
   Zone C is not grounds for exclusion; Zone A/B could be.

REFERENCE DATA SOURCES: Smithsonian GVP Holocene Volcano List (database \
v5.1+), IAVCEI volcanic hazard maps, MTA Turkey / IGME Armenia volcanic \
hazard assessments, LaMEVE database."""

_E5 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E5 — Massive Karst (Exclusionary)
NORMATIVE BASIS: SSG-35 Table I-1; NS-R-3 §3.35–3.36
THRESHOLD: Extensive karst formations threatening foundation integrity → EXCLUDE

NOTE: This criterion shares the DB column NH-05 with E6 (Subsidence). \
Focus EXCLUSIVELY on karst — dissolution of soluble bedrock. Mining \
subsidence is assessed separately in E6.

DEFINITION: Karst forms in soluble rocks (limestone, dolomite, gypsum, \
evaporites) creating sinkholes, caves, and underground drainage. Only \
MASSIVE karst with active sinkhole formation threatens nuclear foundations. \
Relict karst, deep karst covered by thick sediment, or minor dissolution \
features are ranking concerns, not exclusions.

ANALYTICAL STEPS:
1. Determine the bedrock geology at the site. Is it carbonate (limestone, \
   dolomite) or evaporite (gypsum, halite)? If the site is on siliciclastic \
   rocks (sandstone, shale) or igneous/metamorphic rocks, karst is \
   impossible → pass with high confidence.
2. If the site IS on carbonate/evaporite bedrock, determine the karst type:
   - Covered karst (thick sediment over karstified bedrock): moderate risk, \
     generally manageable with foundation engineering.
   - Bare/exposed karst (bedrock at surface with dolines, caves): higher risk.
   - Gypsum karst: most dangerous — dissolves much faster than limestone, \
     can create rapid sinkhole formation.
3. Check for known sinkhole inventories or karst hazard maps in the region.
4. CRITICAL COAL PLANT CONTEXT: Coal deposits form in sedimentary basins, \
   typically in Tertiary/Quaternary clastic sequences (sandstone, siltstone, \
   clay). It is geologically UNCOMMON for a coal plant to be directly on \
   massive karst bedrock — the coal itself sits in non-karstic strata. \
   The plant may be NEAR karst terrain but not ON it.

KEY KARST REGIONS IN SCOPE:
- Dinaric Karst (Slovenia, Croatia, Bosnia, Montenegro, Albania) — the \
  type locality of karst. Massive, well-developed.
- Apuseni Mountains (Romania) — significant karst.
- Mecsek Hills (Hungary) — limestone karst.
- Taurus Mountains (Turkey) — extensive karst in southern Turkey.
- Kraków-Częstochowa Upland (Poland) — Jurassic limestone karst.
- Slovak Karst / Aggtelek (Slovakia/Hungary border).

REFERENCE DATA SOURCES: WOKAM (World Karst Aquifer Map, BGR/UNESCO), \
EGDI karstified zones layers, national geological surveys 1:50k lithology, \
EGDI surface lithology maps, DKSO European karst database."""

_E6 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E6 — Subsidence and Collapse (Exclusionary)
NORMATIVE BASIS: NS-R-3 §3.35–3.36; SSG-35 Table I-1
THRESHOLD: Significant surface collapse potential (mining voids, extraction \
cavities) without remedy → EXCLUDE

NOTE: This criterion shares the DB column NH-05 with E5 (Massive Karst). \
Focus EXCLUSIVELY on non-karst subsidence — mining voids, compaction, \
extraction cavities. Karst collapse is in E5.

ANALYTICAL STEPS:
1. CRITICAL CONTEXT: Coal power plants are almost always located NEAR coal \
   mines — that is their fuel source. Proximity to mining is therefore \
   EXPECTED, not automatically disqualifying. The question is whether \
   subsidence from mining threatens the SPECIFIC PLANT FOOTPRINT, not \
   whether mines exist nearby.
2. Determine the type of coal mining in the area:
   - Open-pit/strip mining: creates surface disturbance but generally NOT \
     subsidence under the plant (the pit is visible and bounded).
   - Underground longwall/room-and-pillar mining: creates subsidence risk \
     if the mine workings extend UNDER the plant site. This is the key concern.
3. Assess whether mine workings extend under or near the plant:
   - If the plant was built on unmined ground adjacent to the mine, \
     subsidence risk is low.
   - If the plant was built OVER old mine workings, risk depends on depth, \
     method, and age of workings.
4. Consider that coal plants were typically built with knowledge of local \
   mining conditions — engineers would not build a 1000 MW power plant \
   on top of active subsidence without mitigation.
5. Other subsidence mechanisms: salt extraction (relevant in Poland, Romania), \
   groundwater withdrawal (relevant in coastal Turkey), peat compaction.

DECISION FRAMEWORK:
- Open-pit mining region, plant on stable ground → pass (high confidence)
- Underground mining nearby but not under plant → pass (medium confidence)
- Underground mining potentially under plant but depth >100 m and old \
  workings → pass (medium confidence, note the risk)
- Active underground mining under or very near plant + shallow workings → \
  inconclusive or fail (needs site investigation)
- Known subsidence damage in the area → inconclusive (needs data)

REFERENCE DATA SOURCES: EGDI mines and coalheritage layers, S-MICA InSAR \
subsidence monitoring, national mining cadastre databases, E-PRTR, national \
geological survey mining hazard maps."""

_E7 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E7 — Protected Natural Areas (Exclusionary)
NORMATIVE BASIS: SSG-35 Table II-1 No.10
THRESHOLD: Site located WITHIN legally protected nature reserve, biosphere \
reserve, or UNESCO World Heritage site exclusion zone → EXCLUDE

ANALYTICAL STEPS:
1. The key question is binary: is the SITE ITSELF (the industrial plant \
   footprint) located INSIDE a protected area boundary?
2. "Adjacent to" or "near" a protected area is NOT grounds for exclusion — \
   that is a ranking concern (NS-08 Ecological Sensitivity).
3. CRITICAL COAL PLANT CONTEXT: A coal/thermal power plant is a heavy \
   industrial facility with smokestacks, coal yards, cooling towers, and \
   rail infrastructure. It is virtually impossible for such a facility to \
   be located inside a strict nature reserve, national park core zone, or \
   UNESCO site. The probability of "fail" on this criterion is very low \
   for any existing coal plant.
4. However, check for:
   - Natura 2000 sites (SAC/SPA) — these are more common and may overlap \
     with industrial areas in some cases, especially along river corridors.
   - Buffer zones — some countries define buffer zones around protected areas \
     that restrict new development.
   - Recently designated protected areas that may have been created AFTER \
     the coal plant was built.
5. If the enrichment data includes in_protected_area=false from the API \
   pipeline (which queries Natura 2000 WFS), this is strong evidence for \
   "pass". The API data is spatially precise.

REFERENCE DATA SOURCES: CDDA (EEA), Natura 2000 network viewer and WFS, \
UNESCO World Heritage List, Ramsar Sites IS, WDPA (UNEP-WCMC), national \
environmental agency registers."""

_E8 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E8 — Emergency Plan Infeasibility (Exclusionary)
NORMATIVE BASIS: NS-R-3 §2.27–2.29; GS-G-2.1
THRESHOLD: Physical or demographic conditions making emergency response \
FUNDAMENTALLY INFEASIBLE → EXCLUDE

This is the most judgment-intensive exclusionary criterion and the one \
where LLM assessment is most uncertain. Set your confidence accordingly.

ANALYTICAL STEPS:
1. Assess the road network within the 5 km EPZ. Can the population be \
   evacuated within a few hours? Key indicators:
   - Multiple major roads leading away from the site (good)
   - Single narrow road or dead-end (bad)
   - Motorway access nearby (good)
2. Estimate population density within 5 km. The threshold for concern is \
   extremely high — >5,000 persons/km² within 5 km. For reference, that \
   is denser than most European cities outside their very centres. Coal \
   plants in semi-rural industrial areas typically have 100-500 persons/km².
3. Check for geographic barriers that could trap population:
   - Narrow mountain valleys with single access
   - Large rivers with limited bridge crossings
   - Peninsula or island sites
4. Assess institutional capacity: does the country have a nuclear \
   regulatory body and emergency planning infrastructure?
   - Countries with nuclear regulatory bodies: CZ (SUJB), SK (UJD), HU \
     (OAH), RO (CNCAN), BG (BNRA), SI (URSJV), UA (SNRIU), AM (ANRA), \
     TR (NDK), LT (VATESI), PL (PAA)
   - Countries without nuclear regulatory bodies but with general emergency \
     management: HR, RS, BA, ME, XK, AL, MK, MD, BY, EE, LV, AT
5. IMPORTANT: Exclusion here should be reserved for GENUINELY EXTREME cases. \
   A typical coal plant in an industrial area with roads is NOT an emergency \
   planning infeasibility case. Only exclude if the physical/demographic \
   conditions are truly insurmountable (e.g., a plant in a narrow mountain \
   valley with 100,000+ people and a single road, or a site on an island \
   with no bridge).

REFERENCE DATA SOURCES: OpenStreetMap road network, WorldPop / GHS-POP \
population data, EU-DEM for terrain, IAEA Country Nuclear Power Profiles, \
national nuclear regulatory authority websites."""

_E9 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E9 — Insufficient Cooling Water (Exclusionary)
NORMATIVE BASIS: SSG-35 §4.9; IAEA Nuclear Energy Series NP-T-4.1
THRESHOLD: No water source adequate for 462 MWe thermal rejection within \
feasible engineering distance, AND dry cooling not viable → EXCLUDE

ANALYTICAL STEPS:
1. STRONGEST SIGNAL — What cooling does the existing coal plant use? \
   Check the enrichment data cooling_water_source field. If the coal plant \
   has an operating cooling system (cooling towers, once-through river \
   cooling, cooling pond), the SMR almost certainly has a cooling water \
   option too. This single fact should drive most assessments.
2. If cooling_water_source is "unknown" or absent:
   a. Check proximity to rivers — most coal plants are on rivers for cooling.
   b. Estimate river flow. A 462 MWe plant needs ~0.5-1.0 m³/s for wet \
      cooling towers. Major European rivers (Danube, Vistula, Maritsa, etc.) \
      provide orders of magnitude more. Even small rivers (>10 m³/s mean \
      flow) are sufficient.
   c. Check for reservoirs, lakes, or sea coast nearby.
3. Seasonal flow considerations: Mediterranean and continental climate \
   rivers may have very low summer flows. This is mainly relevant for:
   - Turkish rivers (some intermittent in eastern Anatolia)
   - Balkan rivers in karst regions (underground drainage)
   - Small rivers in semi-arid eastern Turkey
4. Dry cooling fallback: If no adequate water source exists, dry cooling \
   (air-cooled condensers) is technically viable for SMRs but reduces \
   efficiency by 5-10% and increases cost. Only reject dry cooling as \
   infeasible if the site is in an extreme climate (>45°C summer \
   temperatures, sustained).
5. DECISION: Exclude ONLY if the site has no river/lake/sea within \
   reasonable piping distance (~10 km) AND the existing coal plant \
   apparently operates without water cooling (dry coal plants do exist \
   but are rare) AND dry cooling for the SMR is infeasible.

EXPECTED OUTCOME: This criterion should almost always "pass" for existing \
coal/thermal plants, because they already have cooling water infrastructure. \
A "fail" here would be exceptional and should be flagged with clear \
reasoning about why the existing cooling arrangement is inadequate.

REFERENCE DATA SOURCES: Site's own cooling_water_source field (STRONGEST), \
GRDC river discharge data, European river basin atlases, OpenStreetMap \
waterway data, HydroSHEDS river network, national hydrology services."""

EXCLUSIONARY_PROMPTS: dict[str, str] = {
    "E1": _E1,
    "E2": _E2,
    "E3": _E3,
    "E4": _E4,
    "E5": _E5,
    "E6": _E6,
    "E7": _E7,
    "E8": _E8,
    "E9": _E9,
}
