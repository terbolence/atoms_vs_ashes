"""E1-E9 exclusionary criterion prompts (Tier 1 — Claude Sonnet 4 + thinking)."""

from atoms_vs_ashes.llm.prompts._base import SYSTEM_BASE

PROMPT_VERSION = "v2.4-2026-04-13"

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

ENRICHMENT-AWARE CONFIDENCE CALIBRATION — Follow these rules strictly:
- If API enrichment data IS PROVIDED for the primary metric of this criterion \
  (distance, flag, score), anchor your assessment on that data. Confidence \
  may be "medium" or "high" depending on corroboration.
- If API enrichment data IS NOT PROVIDED but STRONG REGIONAL KNOWLEDGE \
  supports a clear verdict, confidence = "medium" is appropriate. Strong \
  regional knowledge means: you can NAME the specific geological formation, \
  mining type, river system, or terrain feature AND cite it as [FACT]. \
  Examples: "Oltenia basin is open-pit lignite", "site is on the Elbe \
  floodplain", "North Bohemian basin uses surface mining".
- If API enrichment data IS NOT PROVIDED AND regional knowledge is ambiguous \
  or contradictory (you cannot name a specific formation or feature), \
  confidence = "low". If the ambiguity makes the verdict uncertain, \
  return "inconclusive".
- NEVER return "pass" with "high" confidence without at least one \
  quantitative data point from enrichment OR a definitive geological/ \
  physical impossibility (e.g., no volcanism in a country).
- NEVER return "pass" with "medium" or "high" confidence while marking \
  ALL critical data fields as [UNKNOWN]. If you can fill at least one \
  structured field with a factual value, "medium" confidence is permitted.

REASONING/VERDICT CONSISTENCY — If your thinking trace leads toward one \
verdict but your final assessment differs, you MUST explicitly document \
this tension in your justification (e.g., "While my initial reasoning \
suggested X, the lack of Y data means I cannot confirm this with \
sufficient confidence").

OUTPUT FORMAT — Your justification MUST follow this structure:
- Sentence 1: State what you found (the hazard feature, its location, your \
  evidence basis). Label as FACT, INFERENCE, or UNKNOWN.
- Sentence 2: State the distance/metric and how you estimated it. Label.
- Sentence 3: Compare to the threshold. State whether it is triggered.
- Sentence 4-6: State any caveats, adversarial considerations, or data gaps \
  that affect confidence. Label each.

SOURCE CITATION RULES — In cited_sources:
- ONLY list sources you ACTUALLY USED in your reasoning (enrichment data, \
  specific factual knowledge you can name and verify).
- Do NOT list databases you "would need" or "should be consulted" — those \
  go in your justification as data gaps, not in cited_sources.
- If you used only general LLM knowledge, write: "LLM general knowledge — \
  low confidence; desk study verification required"."""

_E1 = SYSTEM_BASE + _EXCLUSIONARY_PREAMBLE + """

CRITERION: E1 — Capable Fault Proximity (Exclusionary)
NORMATIVE BASIS: SSG-35 Annex II Table II-1 No.1; NS-R-3 §3.7; SSG-9 Rev.1
THRESHOLD: Site within 8 km of a capable fault → EXCLUDE

DEFINITION: A "capable fault" per IAEA is a fault that has shown movement \
in the Quaternary period (last 2.6 Ma) and is considered capable of \
generating surface rupture. This is stricter than "active fault" — not \
all active faults are capable faults.

TWO ASSESSMENT PATHWAYS — Choose based on data availability:

PATHWAY A — WITH ENRICHMENT (nearest_fault_km is provided):
1. Use the enrichment distance as your primary anchor.
2. Corroborate with your knowledge of the tectonic domain.
3. If distance >20 km: "pass" (confidence up to "high" if corroborated).
4. If 8-20 km: "pass" with "medium" confidence, note margin.
5. If <8 km: "fail" (confirm with fault name and slip evidence).

PATHWAY B — WITHOUT ENRICHMENT (nearest_fault_km is null/absent):
1. Identify the site's tectonic domain (see list below).
2. Name the nearest KNOWN capable fault — do NOT invent one.
3. Estimate distance using city/town spacing as calibration.
4. Give a RANGE estimate (e.g., "~40-60 km"), never a single number.
5. If your estimate is >40 km from any capable fault: "pass" with "low" \
   confidence, data_quality: "low". This IS acceptable — the 8 km \
   threshold is so tight that a 40+ km estimate provides reasonable \
   assurance even without precision.
6. If your estimate is 8-40 km: "inconclusive" — the uncertainty range \
   could overlap the threshold. Request enrichment data.
7. If your estimate is <8 km: "fail" or "inconclusive" depending on \
   certainty of the fault identification.
8. NEVER return "pass" with "medium" or "high" confidence without \
   enrichment data for this criterion.

TECTONIC DOMAINS:
   - East European Platform / Baltic Shield (stable, very few capable faults)
   - Pannonian Basin (moderate, basin-margin faults)
   - Carpathian Orogen (moderate-high, thrust faults)
   - Dinaric Alps (moderate, complex microplate boundaries)
   - North Anatolian Fault Zone (high, strike-slip system)
   - Vrancea Deep Seismicity Zone (unique — deep seismicity, few surface faults)
   - South Caucasus (high, Bitlis-Zagros collision zone)
   - Balkan extensional zone (moderate, normal faults)

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

ROMANIA-SPECIFIC GEOLOGICAL ANCHORS (use when assessing Romanian sites):
- Moesian Platform: covers southern Romania (Oltenia, Muntenia). Stable \
  platform, very few capable surface faults. Sites on the Moesian Platform \
  are typically >50 km from any capable fault.
- Peceneaga-Camena Fault: major crustal boundary separating Moesian Platform \
  from North Dobrogea. Runs roughly NW-SE through eastern Romania. \
  Debated whether it is "capable" in the IAEA sense — low Quaternary slip rate.
- South Carpathian Fault Zone: Jiu Valley, Olt Valley thrust faults. \
  More relevant for sites in the Carpathian foothills.
- Intramoesian Fault: buried fault under Wallachian Plain, generally not \
  considered capable at the surface.
- Vrancea intermediate-depth zone: generates M7+ earthquakes at 70-180 km \
  depth. NOT a surface fault — irrelevant for this criterion. Do NOT \
  confuse Vrancea seismicity with surface capable faults.
- Key distance anchors: Bucharest-Craiova ~230 km; Craiova-Deva ~280 km; \
  Braila-Galati ~25 km; Turceni-Rovinari ~15 km; Isalnita-Craiova ~10 km.

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

COAL PLANT SITING ANCHOR:
Coal power plants require flat industrial sites for heavy equipment (boilers, \
turbines, generators weighing hundreds of tonnes), cooling towers (30-100 m \
tall), coal storage yards, ash disposal areas, and rail/road access. Even \
cancelled/proposed projects selected sites meeting these requirements. If the \
site is a coal plant location (operating, retired, or planned), you can infer \
flat terrain (<5° slopes) at the plant footprint itself with high confidence. \
The assessment then focuses on whether SURROUNDING terrain poses a landslide \
threat to the site.

DECISION FRAMEWORK:
- Coal plant site on flat/gently sloping ground → pass (high confidence)
- Coal plant in a valley but surrounded by stable geology → pass (medium-high)
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

COAL BASIN GEOLOGICAL ANCHOR — Coal-bearing formations are clastic \
sedimentary sequences (sandstone, siltstone, clay, marl), NOT carbonate \
or evaporite rocks. This means:
- Romanian coal basins (Oltenia lignite basin: Rovinari, Turceni, Isalnita, \
  Craiova; Jiu Valley: Paroseni, Vulcan, Lupeni; Wallachian Plain CHP plants) \
  sit in Neogene-Quaternary clastic fill. Karst is geologically impossible \
  at the plant footprint itself.
- Polish Silesian coal basin: Carboniferous sandstone/shale — non-karstic.
- Turkish Afsin-Elbistan, Soma, Cayirhan lignite basins: lacustrine clastic \
  sequences — non-karstic.
If the site's coal basin geology is identifiable as clastic, return "pass" \
with "medium" or higher confidence, noting that coal strata exclude karst.

COUNTRY-SPECIFIC KARST ASSESSMENT ANCHORS:

CZECH REPUBLIC: Bohemian coal basins sit in Cretaceous/Tertiary CLASTIC \
formations (sandstone, siltstone, clay) — non-karstic. The famous Moravian \
Karst (Blansko area) and Bohemian Karst (Beroun area) are Devonian/ \
Silurian limestone but are NOT in coal mining regions. North Bohemian \
lignite basin (Most, Chomutov, Usti) = Neogene clastic fill over \
crystalline basement — karst impossible. Pardubice region = Bohemian \
Cretaceous Basin, dominantly sandstone — non-karstic.

BULGARIA: Maritsa basin = Neogene clastic fill (sand, clay, lignite \
seams) over pre-Tertiary basement. NO karst in the Thrace/Maritsa lowland. \
Rhodope edge has some marble karst but NOT in the lignite mining areas. \
Black Sea coastal plants (Varna, Devnya) sit on Quaternary alluvium — no \
karst at plant level. Danubian platform (Lom, Vidin, Ruse) = stable \
sedimentary cover, not karstic at coal plant locations.

BOSNIA AND HERZEGOVINA: The Dinaric Karst IS the global type locality of \
karst (the word "karst" comes from the Dinaric region). HOWEVER, coal \
basins within Bosnia (Tuzla, Kakanj, Banovici, Zenica) sit in Miocene \
CLASTIC intra-montane basins (sandstone, clay, marl with lignite seams), \
NOT on the surrounding carbonate bedrock. The key distinction: the BASIN \
fill is clastic even though the SURROUNDING mountains are limestone. \
EXCEPTION: Tuzla has significant Miocene EVAPORITE deposits (salt, gypsum). \
Evaporite karst is a genuine concern for Tuzla specifically — gypsum \
dissolves much faster than limestone. Tuzla sites need careful assessment.

AUSTRIA: Alpine foreland and Danube valley plants sit on Quaternary \
alluvial/glacial deposits — non-karstic. The Northern Limestone Alps \
have extensive karst but coal plants are NOT in the Alps. Lavanttal \
(St Andrae) = Neogene clastic basin fill. Styrian plants = alluvial \
valley settings.

BELARUS: East European Platform, covered by thick Quaternary glacial \
deposits. NO karst risk whatsoever. → pass with high confidence.

POLAND: Silesian coal basin = Carboniferous sandstone/shale — non-karstic. \
Krakow-Czestochowa Upland has Jurassic limestone karst but is NOT where \
coal plants are located. Belchatow = Neogene clay/sand fill.

HUNGARY: Pannonian Basin fill is Neogene clastic (sand, clay, marl). \
Mecsek Hills (Pecs) have Triassic limestone karst but coal mining is in \
adjacent Jurassic coal measures (clastic). Buda Hills karst near Budapest \
is NOT relevant for power plant sites.

UKRAINE: Donbas = Carboniferous sandstone/shale coal measures — non-karstic. \
Western Ukraine = Carpathian flysch or platform cover — generally non-karstic.

TURKEY: Coal basins are lacustrine clastic sequences. Southern Turkey has \
extensive Taurus Mountain karst but it does NOT extend into the lignite basins.

KEY KARST REGIONS IN SCOPE (for awareness, not coal plant locations):
- Dinaric Karst (Slovenia, Croatia, Bosnia, Montenegro, Albania) — the \
  type locality of karst. Massive, well-developed.
- Apuseni Mountains (Romania) — significant karst.
- Mecsek Hills (Hungary) — limestone karst.
- Taurus Mountains (Turkey) — extensive karst in southern Turkey.
- Kraków-Częstochowa Upland (Poland) — Jurassic limestone karst.
- Slovak Karst / Aggtelek (Slovakia/Hungary border).
- Moravian Karst (Czech Republic) — Devonian limestone, Blansko area.
- Rhodope marble karst (Bulgaria/Greece border region).

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

REGION-SPECIFIC MINING CONTEXT — Use this knowledge to anchor your assessment:

ROMANIA:
- Oltenia lignite basin (Turceni, Rovinari, Isalnita/Craiova area): \
  OPEN-PIT (surface) mining. Massive open cuts (Tismana, Rosia, Pinoasa, \
  Jilt, Lupoaia). Open-pit mining does NOT create underground voids or \
  subsidence under adjacent structures. The plant sits on stable ground \
  adjacent to open pits. → pass with medium-to-high confidence.
- Jiu Valley (Paroseni, Vulcan, Lupeni, Petrila): UNDERGROUND mining \
  (longwall) in steep valley terrain. Subsidence risk is real but typically \
  confined to the mining panels. Power plants were built on geotechnically \
  assessed ground, not over active workings. → pass with medium confidence, \
  note proximity to underground workings.
- Wallachian Plain CHP plants (Bucharest, Braila, Galati, Brasov): NO \
  mining activity. These are gas/coal import CHP plants in urban/industrial \
  zones with no local mining. → pass with high confidence.
- Salt mining areas (Turda, Praid, Slanic): relevant only if a site is \
  directly adjacent — generally not coal plant locations.

CZECH REPUBLIC:
- North Bohemian lignite basins (Most-Chomutov area: Prunerov, Tusimice, \
  Pocerady, Ledvice, Melnik, Komorany, Mostecka, Vresova TPS): \
  overwhelmingly OPEN-PIT (surface) mining. Giant open cuts (Bilina, \
  CSA, Libous, Vrsany). Open-pit mining does NOT create underground voids. \
  → pass with medium confidence.
- Sokolov basin (Tisova): OPEN-PIT mining. Same logic as above. → pass \
  with medium confidence.
- Ostrava-Karvina basin (Detmarovice, Karvina, Trebovice): UNDERGROUND \
  longwall mining. Known subsidence zones in Ostrava-Karvina. Check if \
  plant is over mine workings. → pass with medium confidence if plant \
  is on stable ground adjacent to mine; inconclusive if uncertain.
- Pardubice region (Chvaletice, Opatovice): NO local mining — lignite \
  imported by rail from North Bohemia. → pass with medium-to-high confidence.
- Central/South Bohemia (Kladno, Malesice, Plzen CHP, Porici, Mondi Steti, \
  Hodonin): Kladno has HISTORICAL underground mining (ceased). Modern plants \
  built on assessed ground. Hodonin is in South Moravia — NO local coal \
  mining, fuel imported. → pass with medium confidence.

BULGARIA:
- Maritsa East complex (Maritsa Iztok-1/2/3, Brikel, Maritsa 3): massive \
  OPEN-PIT lignite mining. Plants sit adjacent to open pits on stable \
  Neogene sediments. → pass with medium-to-high confidence.
- Bobov Dol: OPEN-PIT lignite mining. → pass with medium confidence.
- Pernik basin: mixed but primarily SURFACE extraction. → pass with medium \
  confidence.
- Republika (Pernik area): OPEN-PIT. → pass with medium confidence.
- Varna, Ruse Iztok, Svilosa, Deven, Lom, Vidin Works: CHP or import \
  plants — NO local mining activity. → pass with high confidence.

BOSNIA AND HERZEGOVINA:
- Stanari: OPEN-PIT lignite. → pass with medium confidence.
- Gacko: OPEN-PIT lignite (Gacko basin). → pass with medium confidence.
- Kakanj: UNDERGROUND mining (room-and-pillar in Kakanj basin). Subsidence \
  risk exists but typically confined to mining panels. Plant built on \
  geotechnically assessed ground. → pass with medium confidence, note risk.
- Tuzla, Banovici: UNDERGROUND mining (Tuzla coal basin). Known mining \
  region with underground workings. Assess plant vs mine spatial relation. \
  → pass with medium confidence if plant is on adjacent stable ground.
- Ugljevik: OPEN-PIT lignite. → pass with medium confidence.
- Bugojno, Kamengrad, Kongora, Glinica, Miljevina: CANCELLED/PROPOSED \
  projects. For cancelled plants near known mining: assess based on mining \
  type in the target area. If open-pit → pass. If underground → assess \
  spatial relationship.

AUSTRIA:
- Lavanttal (St Andrae): historical OPEN-PIT lignite mining, mining \
  ceased ~2004. Site has been stable for 20+ years. → pass with medium \
  confidence.
- Danube valley plants (Duernrohr, Enns, Mellach, Riedersbach): NO coal \
  mining in vicinity — these burn imported coal or gas. → pass with \
  high confidence.
- Voitsberg: adjacent to former OPEN-PIT Karlschacht lignite mine, now \
  closed and remediated. → pass with medium confidence.
- Zeltweg: military/industrial zone, no significant mining nearby. \
  → pass with medium confidence.

BELARUS:
- NO coal mining industry whatsoever. Power plants (Lelchitsy, Zelwa) burn \
  imported fuel or are planned gas plants. Zero subsidence risk from mining. \
  → pass with high confidence.

POLAND: Silesian coal basin uses underground longwall mining. Katowice \
and Upper Silesia have documented subsidence zones. Check plant proximity. \
Belchatow (Lodz voivodeship): massive OPEN-PIT lignite → pass with high \
confidence. Konin/Turow basins: OPEN-PIT → pass with medium-to-high.

TURKEY: Mostly open-pit lignite (Afsin-Elbistan, Soma, Tuncbilek, \
Cayirhan). Low subsidence risk. Zonguldak basin on the Black Sea coast \
is the exception: UNDERGROUND hard coal mining. Check proximity.

UKRAINE:
- Donbas region: extensive UNDERGROUND coal mining. Known subsidence \
  zones. Assess plant vs mine spatial relationship carefully.
- Western Ukraine CHP plants: typically NO local mining, fuel imported. \
  → pass with high confidence.

HUNGARY:
- Matra basin (Visonta, Bukkabrany): OPEN-PIT lignite → pass with \
  medium-to-high confidence.
- Mecsek coal basin (Pecs area): UNDERGROUND mining (historical). Mining \
  has largely ceased. Assess proximity.

SERBIA:
- Kolubara basin (Lazarevac area): massive OPEN-PIT lignite. → pass with \
  medium-to-high confidence.
- Kostolac basin: OPEN-PIT lignite. → pass with medium confidence.

REMAINING BALKANS (HR, SI, ME, XK, MK, AL):
- Generally small coal operations. Slovenia (Velenje): UNDERGROUND longwall. \
  Croatia (Plomin): imported coal, no local mining. Montenegro (Pljevlja): \
  OPEN-PIT. Kosovo (Obilic/Kosovo A&B): OPEN-PIT lignite adjacent to plants. \
  North Macedonia (Bitola/REK): OPEN-PIT. Albania (Porto Romano): no mining.

DECISION FRAMEWORK:
- Open-pit mining region, plant on stable ground → pass (high confidence)
- Underground mining nearby but not under plant → pass (medium confidence)
- Underground mining potentially under plant but depth >100 m and old \
  workings → pass (medium confidence, note the risk)
- Active underground mining under or very near plant + shallow workings → \
  inconclusive or fail (needs site investigation)
- Known subsidence damage in the area → inconclusive (needs data)

CANCELLED/PROPOSED PLANT GUIDANCE FOR E6:
For cancelled or unbuilt plants where the planned extraction method is unknown:
1. Determine the coal basin type in the target area from the regional context \
   above. Most Balkan/Central European lignite basins use OPEN-PIT extraction.
2. If the regional mining method is identifiable (e.g., "Gacko basin = open-pit"), \
   apply that context to the cancelled plant → pass with medium confidence.
3. If the region has BOTH open-pit and underground mining (e.g., Ostrava-Karvina \
   in CZ), and you cannot determine which method was planned, return "pass" \
   with "low" confidence, noting the uncertainty.
4. NEVER return "inconclusive" solely because the plant is cancelled. The \
   subsidence risk comes from the GEOLOGY and MINING HISTORY of the location, \
   not from the plant's operational status.
5. Even for cancelled plants, fill the collapse_mechanism field with the \
   regional mining type (e.g., "open-pit surface mining" or "no mining").

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

EXISTING INFRASTRUCTURE AS EVIDENCE — The strongest evidence for cooling \
water availability is the EXISTING coal plant's cooling system:
- If cooling_water_source field lists a river, reservoir, or cooling towers, \
  this IS definitive enrichment data. The SMR will reuse or adapt the same \
  infrastructure. Return "pass" with "medium" or "high" confidence.
- If cooling_water_source is absent/null but you KNOW the plant's design \
  (e.g., "Turceni has hyperbolic cooling towers visible in satellite imagery" \
  or "Braila CHP uses Danube water"), treat your factual knowledge as \
  equivalent to enrichment data.
- If the plant name contains "CHP" (Combined Heat and Power) — these almost \
  always have water-based cooling from a nearby river or district heating loop.
- Only return "inconclusive" if you genuinely cannot determine whether the \
  plant has any water source AND you have no knowledge of the plant's cooling.

CANCELLED/GREENFIELD PLANT GUIDANCE:
For cancelled or unbuilt plants, the absence of operational cooling \
infrastructure does NOT automatically mean "inconclusive". Instead:
1. If the site is within 5 km of a major river (flow >5 m³/s annual mean) \
   or a lake, cooling water is likely available → pass with medium confidence.
2. If the site is in a water-rich hydrological region (e.g., Danube basin, \
   Neman basin, Sava/Drina basin, Maritsa basin), infer availability from \
   the watershed context → pass with low-to-medium confidence.
3. Only mark "inconclusive" if the site is in a semi-arid or arid region \
   AND no water body can be identified within 10 km.
4. Dry cooling is always a technical fallback — note it but do not rely on \
   it alone for a "pass" verdict.
5. IMPORTANT: Even cancelled plants were proposed at locations selected by \
   engineers who considered cooling water availability. The site selection \
   itself is evidence of water access.

COUNTRY-SPECIFIC HYDROLOGICAL ANCHORS:
- BELARUS (BY): The Polesie lowland (Gomel, Brest oblasts) is one of \
  Europe's most water-rich regions — dense networks of rivers, canals, and \
  marshes. Key rivers: Pripyat (mean flow ~400 m³/s at Mozyr), Dnieper \
  (~1700 m³/s), Berezina (~150 m³/s), Neman (~200 m³/s), Ubort (~15 m³/s \
  at mouth), Sluch. The Zelwa site is near the Neman River system. \
  Lelchitsy (51.789N, 28.321E) is in the Pripyat basin — the Ubort River \
  flows ~8 km to the east and multiple drainage channels cross the area. \
  ANY site in Belarus's southern lowland should pass with at least low \
  confidence based on the water-rich hydrogeological setting.
- BOSNIA & HERZEGOVINA (BA): The Sava/Drina/Neretva/Vrbas river systems \
  provide abundant water. Even in Herzegovina (drier karst), rivers like \
  the Neretva (>100 m³/s) and Trebisnjica are within engineering distance.
- AUSTRIA (AT): Alpine rivers (Danube, Mur, Drau, Enns) provide massive flow.
- CZECH REPUBLIC (CZ): Elbe (Labe), Vltava, Ohre, Morava river systems. \
  North Bohemian plants are all within 10 km of the Ohre or Bilina rivers.
- POLAND (PL): Vistula (mean ~1000 m³/s), Oder/Odra (~500 m³/s), Warta, \
  Bug river systems. Silesian plants on Vistula/Oder tributaries. Belchatow \
  uses cooling towers with Widawka River makeup water. Konin plants use \
  lake cooling (Patnow, Gosławice lakes). All major Polish coal plants \
  have established cooling infrastructure.
- UKRAINE (UA): Dnieper (~1700 m³/s), Donets, Southern Bug, Dniester. \
  Donbas plants use Donets River or Siverskyi Donets tributaries. Western \
  Ukraine plants on Dniester/Bug tributaries. Massive water availability.
- HUNGARY (HU): Danube (~2300 m³/s at Budapest), Tisza (~800 m³/s), \
  Drava, Sajo rivers. Matra plants (Visonta) use Tisza basin water. \
  All Hungarian thermal plants have river or lake cooling.
- SERBIA (RS): Danube, Sava (~1600 m³/s), Morava, Drina rivers. \
  Kolubara basin plants near Sava. Kostolac on the Danube. Abundant water.
- SLOVAKIA (SK): Danube, Vah, Hron, Nitra rivers. Vojany plant on \
  Laborec/Latorica. Novaky on Nitra River. All have cooling water access.
- CROATIA (HR): Sava, Drava, Danube. Plomin on Adriatic coast (seawater).
- SLOVENIA (SI): Sava, Drava rivers. Sostanj/Velenje near Paka River \
  (Sava tributary). Ljubljana basin well-watered.
- MONTENEGRO (ME): Pljevlja on Cehotina River (Drina tributary). \
  Adriatic coast sites have seawater access.
- NORTH MACEDONIA (MK): Vardar River (~100 m³/s), Treska, Crna Reka. \
  REK Bitola uses Crna Reka/Shemnica water system.
- KOSOVO (XK): Sitnica, Ibar, White Drin rivers. Kosovo A/B plants at \
  Obilic use Sitnica River and Batllava/Badovc reservoirs.
- LATVIA (LV): Daugava (~700 m³/s), Gauja, Lielupe. Extremely water-rich.
- MOLDOVA (MD): Dniester, Prut rivers. Adequate water resources.

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
