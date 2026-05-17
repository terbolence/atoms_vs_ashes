# man_hours: 0.2
"""A1-A15 avoidance/discretionary screening prompts (Tier 2 — Claude Sonnet 4)."""

from atoms_vs_ashes.llm.prompts._base import SYSTEM_BASE

PROMPT_VERSION = "v2.0-2026-04-12"

_AVOIDANCE_PREAMBLE = """

═══ PHASE: AVOIDANCE / DISCRETIONARY SCREENING ═══
Normative basis: SSG-35 Table II-1 (discretionary avoidance criteria)

VERDICT OPTIONS:
• "pass" — The avoidance threshold is NOT triggered. You have positive \
  evidence that the site clears the criterion with margin.
• "caution" — The avoidance threshold IS triggered OR the site is in a \
  borderline zone. This flags the site for deeper assessment in later \
  phases; it does NOT eliminate the site.
• "inconclusive" — You lack sufficient evidence to determine whether the \
  threshold is triggered. Do NOT guess — return inconclusive.

DECISION LOGIC (apply strictly):
IF measured/estimated metric clearly clears threshold with margin → "pass"
IF measured/estimated metric violates threshold OR is within 20% of it → "caution"
IF you cannot determine the metric with any reliability → "inconclusive"

JUSTIFICATION REQUIREMENTS:
Your justification MUST contain ALL of the following:
1. The specific threshold value for this criterion.
2. Your estimated/measured value for the relevant metric.
3. A comparison statement: "The estimated [metric] of [value] is \
   [above/below/within] the threshold of [threshold], therefore..."
4. At least one [FACT], [INFERENCE], or [ESTIMATE] label.
5. Any enrichment data corroboration or discrepancy.

DISTANCE ESTIMATION GUIDANCE:
When estimating distances, use these techniques in order of preference:
1. Enrichment data (most reliable when quality is high).
2. Known geographic relationships (e.g., "the site is on the outskirts \
   of [city], and [airport] serves [city] — typical distance is X km").
3. Coordinate-based reasoning (latitude/longitude differences: 1° lat \
   ≈ 111 km, 1° lon ≈ 111 × cos(lat) km).
4. Regional knowledge (e.g., "coal plants in this region are typically \
   located in [valley/basin] areas where airports are [rare/common]").
Always provide distance as a range (e.g., "approximately 12-18 km") \
rather than a false-precision point estimate."""

_A1 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A1 — Airport Flight Path Proximity
NORMATIVE: SSG-35 Table II-1 No.2; NS-G-3.1
THRESHOLD: Site must be >= 4.0 km from approach/departure flight paths.
SCOPE: ONLY approach/departure flight paths (extended runway centre-lines). \
Other airport hazards are assessed in A2 (Type 2 events), A3 (small \
airports), A4 (large/busy airports). Do NOT assess those here.

ANALYSIS STEPS:
1. IDENTIFY airports within 25 km of the site. For each, determine:
   - Name, ICAO code (if known), type (civil/military/GA)
   - Approximate distance from site
   - Runway orientation if known (approach corridors extend 15-20 km \
     from runway thresholds along the extended centre-line, ~1 km wide)
2. MODEL the approach/departure corridors geometrically:
   - Each runway generates two corridors (one per threshold)
   - Corridor length: ~15-20 km from runway threshold
   - Corridor width: ~1 km either side of extended centre-line
   - If runway orientation is unknown, assume worst-case alignment
3. COMPUTE perpendicular distance from site to nearest corridor axis.
4. COMPARE to 4.0 km threshold.

FAST-TRACK RULES:
• If the nearest airport of ANY type is > 25 km from the site → \
  verdict="pass", confidence="high" (no flight path can reach the site).
• If enrichment data shows hi01_flight_path_km > 6 km with quality \
  "high" → verdict="pass", confidence="high".
• If a major airport is < 8 km from the site → likely "caution" unless \
  you can confirm runway orientation places all corridors away from site.

COMMON PITFALLS:
- Do NOT confuse straight-line distance to an airport with distance to \
  its flight path. A site 10 km from an airport can be < 4 km from its \
  approach corridor if aligned with the runway.
- Coal plants on flat terrain near rivers are in exactly the terrain \
  that airports also prefer — do not dismiss airport proximity.
- Decommissioned/closed airports may still have active flight paths if \
  not formally de-gazetted.

REFERENCE DATA: OurAirports database, national AIP, OpenStreetMap \
aeroway data, SkyVector/OpenNav approach charts."""

_A2 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A2 — Type 2 Airport Event Proximity
NORMATIVE: SSG-35 Table II-1 No.3
THRESHOLD: Site must be >= 7.5 km from airports exhibiting Type 2 event \
attributes (high-energy crash/overshoot potential).
SCOPE: ONLY Type 2 event sources. Flight paths → A1, small airports → \
A3, large/busy airports → A4.

TYPE 2 EVENT DEFINITION:
A Type 2 aircraft impact event involves high-energy impact (fast military \
jets, heavy cargo aircraft, or aircraft with challenging operational \
profiles). Airports qualifying as Type 2 sources include:
- Military airfields with fast-jet operations (fighters, strike aircraft)
- Airports with operationally challenging approaches (terrain-induced, \
  weather-impacted, single-runway with crosswind issues)
- Airports regularly handling heavy cargo (747F, AN-124, C-17 class)

ANALYSIS STEPS:
1. IDENTIFY airports within 15 km of the site.
2. CLASSIFY each as Type 2 or non-Type 2:
   - Military airfields → Type 2 (fast jets = higher crash rate/sortie)
   - Heavy cargo airports → Type 2
   - Standard civil GA/regional → NOT Type 2 (assessed in A3/A4)
3. For each Type 2 airport, ESTIMATE distance to site.
4. COMPARE closest Type 2 distance to 7.5 km threshold.

FAST-TRACK RULES:
• No airports of any type within 15 km → verdict="pass", confidence="high".
• No military or heavy-cargo airports within 15 km, and no challenging \
  approaches known → verdict="pass", confidence="medium".
• Military airfield within 7.5 km → verdict="caution", confidence="medium" \
  minimum (even if you cannot confirm it is active).

REGIONAL CONTEXT:
In the 23-country scope, key military airfield concentrations include:
- Poland (NATO air bases: Łask, Krzesiny, Malbork, Świdwin)
- Romania (Câmpia Turzii, Mihail Kogălniceanu, Borcea)
- Turkey (extensive TAF bases throughout)
- Baltic states (NATO air policing rotations at Ämari, Šiauliai)
- Bulgaria (Graf Ignatievo, Bezmer)
Soviet-era airfields exist across the region; many are decommissioned \
but some reactivated. If you cannot determine status, assume active.

COMMON PITFALLS:
- Military airfield data is intentionally sparse in public databases. \
  Absence of evidence ≠ evidence of absence. If the region has known \
  military activity but you cannot locate specific airfields, set \
  confidence="low", not verdict="pass".
- Do not confuse military barracks (ground forces) with military airfields.

REFERENCE DATA: OurAirports (type=military), OSM military=airfield, \
national defence ministry public lists, ICAO/IATA directories."""

_A3 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A3 — Small Airport Proximity
NORMATIVE: SSG-35 Table II-1 No.4
THRESHOLD: Site must be >= 10.0 km from small airports / airstrips.
SCOPE: ONLY small airports, airstrips, aerodromes, grass strips, \
glider fields, and private airfields. Flight paths → A1, Type 2 → A2, \
large/busy airports → A4.

WHAT COUNTS AS "SMALL AIRPORT":
- General aviation airfields (ICAO type: small_airport)
- Agricultural airstrips (crop-dusting), private grass strips
- Glider clubs and ultralight fields
- Heliports (if standalone, not hospital/building-integrated)
- Closed airports that retain runway infrastructure
NOT included: Major commercial airports (→ A4), military airfields (→ A2).

ANALYSIS STEPS:
1. IDENTIFY all small airfields within 15 km using known databases and \
   regional knowledge.
2. ESTIMATE distance from site to each identified airfield.
3. COMPARE closest distance to 10.0 km threshold.
4. ASSESS completeness — are there likely unregistered strips in the area?

FAST-TRACK RULES:
• Enrichment data shows nearest_airport_km > 12 km with quality \
  "high" → verdict="pass", confidence="high" (assumes enrichment \
  captured small airports too).
• Site is in a heavily agricultural region with flat terrain → reduce \
  confidence by one level (unregistered crop-dusting strips likely exist).

COMPLETENESS WARNING:
Small airfields are systematically UNDER-REPORTED in public databases. \
OurAirports captures ~70% of registered small airports in Western Europe \
but coverage drops to ~40-50% in Eastern Europe and the Balkans. \
Agricultural airstrips and private fields are frequently unlisted. \
If the site is in an agricultural flatland region (e.g., Hungarian Great \
Plain, Romanian Wallachian Plain, Polish lowlands, Bulgarian Thracian \
Plain, Ukrainian steppe), you MUST flag that undocumented airstrips \
may exist within 10 km and cap confidence at "medium" even for "pass".

REFERENCE DATA: OurAirports (type=small_airport, heliport, seaplane_base, \
closed), national CAA registers, OSM aeroway=aerodrome/airstrip."""

_A4 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A4 — Large / Busy Airport Proximity
NORMATIVE: SSG-35 Table II-1 No.5
THRESHOLD: Site must be >= 16.0 km from airports where annual flight \
operations exceed 500 × d² (d = distance in km).
SCOPE: ONLY large/medium commercial airports with significant traffic. \
Flight paths → A1, Type 2 → A2, small airports → A3.

FORMULA APPLICATION:
The SSG-35 criterion uses: operations > 500 × d²
Pre-computed decision boundaries:
  d = 5 km  → threshold = 12,500 ops/yr (most medium airports trigger)
  d = 10 km → threshold = 50,000 ops/yr
  d = 16 km → threshold = 128,000 ops/yr
  d = 20 km → threshold = 200,000 ops/yr (only major hubs trigger)
  d = 30 km → threshold = 450,000 ops/yr (no European airport triggers)

ANALYSIS STEPS:
1. IDENTIFY medium and large airports within 30 km.
2. For each airport, ESTIMATE annual movements (NOT passengers):
   - Major hubs: 200,000-400,000 movements (Frankfurt, Istanbul)
   - Large regional: 50,000-150,000 (Bucharest, Warsaw, Prague)
   - Medium regional: 10,000-50,000 (most regional airports)
3. COMPUTE 500 × d² for the distance to each airport.
4. COMPARE: if operations > 500 × d² for any airport → "caution".

FAST-TRACK RULES:
• No medium or large airport within 30 km → verdict="pass", \
  confidence="high" (no airport can satisfy the formula at 30 km).
• Nearest large airport is > 20 km and handles < 200,000 movements/yr \
  → verdict="pass", confidence="medium".
• Any airport within 10 km with > 50,000 movements/yr → verdict="caution".

REGIONAL AIRPORT KNOWLEDGE (major hubs near coal regions):
- Poland: WAW (Warsaw Chopin, ~180k mvmt), KTW (Katowice-Pyrzowice, ~50k)
- Czech Republic: PRG (Prague, ~130k)
- Romania: OTP (Bucharest Otopeni, ~100k)
- Bulgaria: SOF (Sofia, ~50k)
- Turkey: IST (Istanbul, ~400k), ESB (Ankara, ~80k), ADB (Izmir, ~60k)
- Hungary: BUD (Budapest, ~100k)
These are approximate pre-pandemic figures — use as order-of-magnitude anchors.

COMMON PITFALLS:
- Count movements (takeoffs + landings), not passenger numbers. \
  Movements ≈ passengers ÷ 80-120 for typical European airports.
- Coal plants near capital cities may be surprisingly close to major \
  airports (e.g., plants in the Silesian basin near Katowice airport).

REFERENCE DATA: Eurostat avia_tf_apal, EUROCONTROL PRR data, ACI \
Europe traffic reports, OurAirports (type=large/medium_airport)."""

_A5 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A5 — Military Installation Proximity (Ranges)
NORMATIVE: SSG-35 Table II-1 No.6
THRESHOLD: Site must be >= 30.0 km from active practice/bombing/firing ranges.
NOTE: 30 km is a LARGE exclusion radius — this is one of the most \
spatially demanding avoidance criteria.

WHAT QUALIFIES:
- Active artillery/bombing/firing ranges (live ordnance)
- Military training areas with live-fire exercises
- Missile test ranges
DOES NOT QUALIFY: Barracks, headquarters, logistics bases, recruitment \
offices, decommissioned ranges converted to civilian use.

ANALYSIS STEPS:
1. IDENTIFY known military ranges within 50 km of the site.
2. CLASSIFY each as active firing range vs. other military facility.
3. ESTIMATE distance from site to nearest active range BOUNDARY \
   (not centre — ranges can be large, 5-20 km across).
4. COMPARE to 30 km threshold.
5. ASSESS data completeness — military range data is inherently sparse.

FAST-TRACK RULES:
• Enrichment data shows nearest_military_km > 35 km with quality \
  "high" → verdict="pass", confidence="medium" (enrichment may not \
  distinguish ranges from other military facilities).
• Site is in a country with minimal military (MD, XK, ME, MK) → \
  verdict="pass", confidence="medium" (few active ranges).

REGIONAL KNOWLEDGE:
Large active training areas in the 23-country scope include:
- Poland: Drawsko Pomorskie (one of Europe's largest), Nowa Dęba, Wicko
- Czech Republic: Libavá, Hradiště, Brdy
- Romania: Cincu (NATO training), Smârdan, Babadag
- Hungary: Hajmáskér
- Turkey: extensive military training grounds nationwide
- Baltic states: Ādaži (LV), Tapa (EE), Pabradė (LT)
- Bulgaria: Novo Selo
Many Soviet-era ranges in UA, BY, RO, BG have uncertain current status.

CRITICAL WARNING ON DATA GAPS:
Military range locations are among the LEAST documented features in \
public geospatial databases. If you cannot identify specific ranges \
in the site's vicinity, you MUST:
- Set confidence="low"
- Note the data gap explicitly in justification
- Do NOT default to "pass" — default to "inconclusive" if the country \
  has significant military activity

REFERENCE DATA: OSM military=range/danger_area, national defence \
public lists, NOTAM permanent restricted airspace (as proxy)."""

_A6 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A6 — Military Ammunition Storage
NORMATIVE: SSG-35 Table II-1 No.7
THRESHOLD: Site must be >= 8.0 km from ammunition storage facilities.

WHAT QUALIFIES:
- Dedicated ammunition depots and munitions storage areas
- Ammunition bunker fields (typically dispersed earth-covered magazines)
- Explosive ordnance storage within military bases
DOES NOT QUALIFY: Small arms armouries within barracks, decommissioned \
and fully remediated former depots.

ANALYSIS STEPS:
1. IDENTIFY known ammunition storage facilities within 15 km.
2. Check whether any known military BASE within 15 km may include \
   ammunition storage (most large military bases do).
3. ESTIMATE distance from site to nearest identified facility.
4. COMPARE to 8.0 km threshold.

FAST-TRACK RULES:
• No military facilities of any kind within 12 km → verdict="pass", \
  confidence="medium" (ammunition depots are rarely isolated from bases).
• Known major military base within 8 km → verdict="caution" (assume \
  ammunition storage present unless you have positive evidence otherwise).

REGIONAL CONTEXT:
Legacy Soviet ammunition depots are a significant feature of the region:
- Many were built in the 1950s-1980s and are now managed by successor states
- Notable incidents: Vrbětice (CZ, 2014), Chelopechene (BG, 2008), \
  Novobohdanivka (UA, 2017), Balakleya (UA, multiple incidents)
- Countries with known dense depot networks: PL, CZ, RO, BG, UA, BY
These facilities are among the MOST CLASSIFIED military assets. Public \
data coverage is extremely poor.

INFERENCE RULE:
If a major military base is located within 8 km of the site, and you \
cannot determine whether it includes ammunition storage, apply the \
precautionary principle: assume it does and return verdict="caution" \
with a note that field verification is needed.

REFERENCE DATA: OSM military=ammunition/bunker, SIPRI, national defence \
transparency reports, press/news reports of depot incidents."""

_A7 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A7 — Hazardous Material Facilities
NORMATIVE: SSG-35 Table II-1 No.8; EU SEVESO III Directive 2012/18/EU
THRESHOLD: Site must be >= 5.0 km from facilities storing/processing \
flammable, toxic, or explosive materials at quantities above SEVESO \
lower-tier thresholds.

WHAT QUALIFIES (SEVESO III categories):
- Chemical manufacturing plants (especially chlorine, ammonia, phosgene)
- Oil refineries and petrochemical complexes
- LNG/LPG storage terminals and major fuel depots
- Fertiliser factories (ammonium nitrate storage)
- Explosives manufacturers
- Major industrial gas storage (oxygen, hydrogen)
DOES NOT QUALIFY: Coal/ash handling at the site itself, small fuel \
stations, minor chemical storage below SEVESO thresholds.

ANALYSIS STEPS:
1. ASSESS the industrial context: Is the coal plant in an industrial \
   zone, energy cluster, or isolated? Coal plants in industrial zones \
   (common in Silesia, Maritsa basin, Ruhr-adjacent areas) are MORE \
   likely to have nearby SEVESO facilities.
2. IDENTIFY specific SEVESO III facilities within 10 km if known.
3. Check for refineries, chemical plants, and fertiliser factories — \
   these are the most common SEVESO facilities in the region.
4. ESTIMATE distances.
5. COMPARE to 5.0 km threshold.

FAST-TRACK RULES:
• Enrichment data shows nearest_seveso_km > 7 km with quality \
  "high" → verdict="pass", confidence="high".
• Site is in a major industrial/energy district → reduce confidence \
  by one level even if no specific SEVESO facility is identified \
  (SEVESO registers are incomplete in some countries).
• Known refinery or chemical plant within 5 km → verdict="caution".

CRITICAL NUANCE — INDUSTRIAL DISTRICTS:
Coal plants are PREFERENTIALLY located in industrial zones. This creates \
a systematic bias: sites most suitable for coal-to-nuclear conversion \
(large, grid-connected, brownfield) are also most likely to be near \
hazmat facilities. Do NOT assume "isolated site" without evidence.

REGIONAL KNOWLEDGE:
Major SEVESO-relevant industrial clusters near coal regions:
- Silesian industrial district (PL): refineries, chemical plants
- Maritsa Iztok basin (BG): industrial zone
- Bohemian industrial belt (CZ): chemical industry (Pardubice, Ústí)
- Romanian Ploiești-Brazi refinery corridor
- Turkish industrial zones (Marmara, Çukurova)
Non-EU countries (XK, BA, RS, UA, BY, AL, MK, MD, AM, TR) may not \
have formal SEVESO registers — flag data gaps explicitly.

REFERENCE DATA: EU SEVESO III registers (national competent authority), \
E-PRTR, national environmental agency databases, OSM landuse=industrial."""

_A8 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A8 — Hazardous Cloud Sources
NORMATIVE: SSG-35 Table II-1 No.9
THRESHOLD: Site must be >= 8.0 km from sources capable of producing \
drifting hazardous clouds (toxic gas plumes, chemical release clouds).

KEY DISTINCTION FROM A7:
A7 assesses EXPLOSION risk from hazmat facilities (pressure wave). \
A8 assesses AIRBORNE TOXIC CLOUD risk (plume dispersion affecting \
control room habitability and site evacuation). A facility may trigger \
both A7 and A8, but your analysis here must focus on cloud-forming \
potential, not blast radius.

CLOUD-FORMING SOURCES (in order of hazard significance):
1. Chlorine production/storage (water treatment plants handling bulk \
   chlorine are a commonly overlooked source)
2. Ammonia storage/processing (fertiliser plants, cold storage, \
   industrial refrigeration)
3. Refineries with HF alkylation units
4. Major gas transmission pipelines (>600mm diameter) — rupture produces \
   a flammable/toxic cloud that can drift several km
5. LPG storage terminals (BLEVE → toxic cloud)
6. Chemical plants handling phosgene, hydrogen cyanide, sulphur dioxide

ANALYSIS STEPS:
1. IDENTIFY cloud-forming sources within 15 km.
2. ASSESS wind exposure: Is the source upwind of the site in prevailing \
   wind conditions? (In the 23-country scope, prevailing winds are \
   generally westerly to northwesterly — sources to the W/NW of the \
   site are higher concern.)
3. ESTIMATE distance from site to each source.
4. COMPARE to 8.0 km threshold (the most conservative distance; wind \
   direction and terrain can modulate effective hazard distance).

FAST-TRACK RULES:
• No industrial facilities, pipelines, or water treatment plants within \
  12 km → verdict="pass", confidence="medium".
• Known chemical plant or major gas pipeline within 8 km → \
  verdict="caution".

COMMONLY OVERLOOKED SOURCES:
- Municipal water treatment plants using bulk chlorine (common within \
  5-10 km of industrial sites)
- Agricultural ammonia storage
- Coal plant's own water treatment may use chlorine — this is ON-SITE \
  and not an external hazard (do not count it)
- Major gas pipelines crossing the region (e.g., Brotherhood pipeline \
  system, TurkStream, TAP — high-pressure, large diameter)

REFERENCE DATA: EU SEVESO III registers, E-PRTR (toxic release data), \
national pipeline operator maps, OSM pipeline data, ARIA database."""

_A9 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A9 — Tsunami / Seiche Exposure
NORMATIVE: SSG-35 Table II-1 No.11; SSG-18
THRESHOLD: Site must satisfy AT LEAST ONE of:
  (a) >= 10 km from sea/ocean shore, OR
  (b) >= 1 km from lake/fjord shore (for lakes > 10 km long), OR
  (c) >= 50 m elevation above nearest mean water level.
Meeting ANY ONE condition is sufficient for "pass".

DECISION TREE:
1. Is the site > 50 km from any coast or major lake?
   → YES: verdict="pass", confidence="high". State this directly and \
     skip further analysis. Most coal plants in this scope are inland \
     river sites — this fast-track applies to the majority.
   → NO: Continue to step 2.
2. Is the site coastal (< 50 km from sea)?
   → Check distance to shore AND elevation above MSL.
   → If distance >= 10 km OR elevation >= 50 m → "pass".
   → Otherwise → assess tsunami/storm surge history and return "caution".
3. Is the site near a large lake (> 10 km long)?
   → Check distance from lakeshore.
   → If distance >= 1 km → "pass" for seiche.
   → Otherwise → assess seiche potential and return "caution".

REGIONAL TSUNAMI CONTEXT:
Significant tsunami hazard zones in the 23-country scope:
- Turkish Aegean coast (1956 Amorgos tsunami affected Turkish coast)
- Turkish Mediterranean coast (365 AD Crete tsunami, 1303 event)
- Turkish Black Sea coast (low-moderate tsunami risk)
- Greek-facing coasts of AL, MK (via Adriatic, low risk)
- Adriatic coast of HR, ME, AL (low-moderate)
INLAND countries (PL, CZ, SK, HU, AT, BY, MD, most of RO/BG/UA): \
tsunami risk is zero — coal plants in these areas trivially pass.

SEICHE-RELEVANT LAKES:
Lake Balaton (HU, 77 km long), Lake Ohrid (AL/MK, 30 km), large \
reservoirs (>10 km). River sites do NOT generate seiches — rivers \
are not enclosed water bodies. Do NOT confuse river flood risk (→ A11) \
with seiche/tsunami risk.

REFERENCE DATA: NOAA/NGDC Historical Tsunami Database, NEAMTWS hazard \
maps, EU-DEM/SRTM elevation, OSM coastline and water body data."""

_A10 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A10 — Seismic Ground Motion (Avoidance)
NORMATIVE: SSG-9; SSR-1 §4.10
THRESHOLD: PGA at 475-year return period must be <= 0.5g (NuScale \
VOYGR-6 certified seismic design basis). Sites exceeding 0.5g PGA \
at 475yr require engineering beyond standard design → "caution".

KEY DISTINCTION FROM E1:
E1 assesses CAPABLE FAULT proximity (surface rupture hazard, binary \
exclusion at 8 km). A10 assesses GROUND SHAKING INTENSITY from ALL \
seismic sources (capable faults, diffuse seismicity, deep subduction \
events like Vrancea). A site can pass E1 yet fail A10.

ANALYSIS STEPS:
1. CHECK enrichment data: If pga_475yr_g is provided with quality "high", \
   use it directly — API data sourced from ESHM20 is authoritative.
2. If no enrichment data, ESTIMATE PGA from seismotectonic context:
   a. Identify the tectonic unit (see regional bands below)
   b. Estimate PGA range from the appropriate band
3. COMPARE to 0.5g threshold.
4. If PGA 475yr is > 0.3g but < 0.5g, flag as borderline and consider \
   the 2475yr PGA — if 2475yr exceeds 0.5g, return "caution".

REGIONAL PGA BANDS (475yr return period, from ESHM20):
• < 0.05g (STABLE): Baltic Shield (EE, LV, LT interior), East European \
  Platform (BY, eastern PL, northern UA)
• 0.05-0.15g (LOW-MODERATE): Bohemian Massif (CZ), Pannonian Basin (HU \
  centre), Polish Lowlands, most of BG interior
• 0.15-0.30g (MODERATE): Dinarides (HR, BA, RS, ME, AL, MK), Carpathian \
  foredeep (southern PL, RO Moldova/Wallachia near Vrancea), eastern AT
• 0.30-0.50g (HIGH): Vrancea deep seismic zone (eastern RO, up to 150 km \
  influence), North Anatolian Fault zone (northern TR), East Anatolian \
  Fault zone (southeastern TR), Hellenic arc (southwestern TR)
• > 0.50g (EXCEEDS DESIGN): Near-field Vrancea (Buzău-Vrancea area), \
  NAF segments near Istanbul, portions of eastern TR (Erzincan, Van)

FAST-TRACK RULES:
• Enrichment pga_475yr_g <= 0.25g → verdict="pass", confidence="high".
• Enrichment pga_475yr_g 0.25-0.40g → verdict="pass" but note proximity \
  to design limit; if 2475yr data exceeds 0.5g, consider "caution".
• Enrichment pga_475yr_g > 0.40g → verdict="caution".
• No enrichment + site in stable craton → verdict="pass", \
  confidence="medium" (use regional band estimate).

COMMON PITFALLS:
- Vrancea intermediate-depth earthquakes (70-200 km deep) affect a wide \
  area — sites 100-200 km from the epicentre can still experience 0.2-0.3g.
- Do not assume low PGA in Romania outside Vrancea — the entire eastern \
  half of RO is in the influence zone.
- Turkey has extreme PGA variability — western TR (Aegean) differs \
  drastically from central Anatolia (much lower).

REFERENCE DATA: SHARE ESHM20 (10% in 50yr = 475yr; 2% in 50yr = 2475yr), \
GEM Global Seismic Hazard Map, national maps (PGI Poland, INFP Romania, \
KOERI Turkey), USGS GSHAP."""

_A11 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A11 — River / Coastal Flood Risk (Avoidance)
NORMATIVE: SSG-18; NS-R-3 §3.54-3.57
THRESHOLD: Site must have adequate flood protection for the design-basis \
flood (10,000-year return period for nuclear). Practical indicators:
- Site elevation >= 5 m above 100-year flood level → likely adequate
- Site in mapped flood zone (100-year) → "caution"
- Site in unprotected floodplain < 2 m above normal river level → "caution"

KEY DISTINCTION FROM A9:
A9 assesses TSUNAMI/SEICHE (coastal wave events). A11 assesses RIVER \
FLOODING, COASTAL STORM SURGE, and DAM-BREAK FLOOD RISK. Different \
physical mechanisms, different analysis.

ANALYSIS STEPS:
1. DETERMINE the site's relationship to water:
   - Adjacent to a major river? (most coal plants are — they need cooling)
   - In a mapped floodplain?
   - Downstream of major dams or reservoirs?
2. ESTIMATE elevation relative to nearest water body:
   - Use enrichment data (elevation_m, flood_zone_class) if available
   - Use knowledge of local topography
3. ASSESS historical flood events in the region.
4. EVALUATE flood defence feasibility — is the site protectable?

DECISION FRAMEWORK:
• Site > 10 m above river/coast AND not in mapped flood zone → "pass"
• Site in mapped 100-year flood zone BUT flood defences are technically \
  feasible (flat terrain, existing levees) → "caution"
• Site in mapped flood zone with major dam-break exposure AND limited \
  defence options → "caution" with confidence="medium"
• Cannot determine flood exposure → "inconclusive"

COAL PLANT FLOOD CONTEXT:
Coal plants near rivers are SYSTEMATICALLY exposed to flood risk because \
they were sited for cooling water access. However:
- Many were built with flood protection (elevated platforms, levees)
- Operating plants have survived decades of flood events — this is \
  weak positive evidence of adequate protection
- The nuclear design-basis flood (10,000-year) is far more severe than \
  the 100-year flood most coal plant defences are designed for

MAJOR FLOOD EVENTS IN THE REGION:
- 2014 Balkans floods (BA, RS, HR) — catastrophic, many industrial sites affected
- 2010 and 2021 Vistula floods (PL)
- 2013 Danube flood (HU, AT, SK, RS)
- 2005 and 2006 Danube/Tisza floods (RO, HU)
- Periodic Black Sea coast flooding (TR, BG, RO)
If the site's river basin experienced any of these events, flag flood \
risk explicitly.

REFERENCE DATA: EU Floods Directive PFRA maps, JRC EFAS, national \
flood hazard maps (ISOK PL, ANAR RO, DSI TR), OSM waterway data, \
HydroSHEDS river network and catchment areas."""

_A12 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A12 — Population Centre Distance (Avoidance)
NORMATIVE: NS-G-3.2; SSG-35 §A.39
THRESHOLD: RI-05 population-centre thresholds. A site is flagged if the \
nearest qualifying population centre is too close: >=25k population within \
8 km, >=100k within 16 km, >=500k within 32 km, or >=1M within 48 km.

RI-04 POPULATION DENSITY IS NOT AN A12 GATE:
Do not use EPZ ring density (pop_density_5km / pop_density_16km / \
pop_density_25km / pop_density_80km) to produce an A12 caution. RI-04 is \
ranking-only. Use density only as background context if it helps explain \
the settlement pattern.

ANALYSIS STEPS:
1. IDENTIFY the nearest settlement(s) with population >=25,000, >=100,000, \
   >=500,000, and >=1,000,000 where possible.
2. CHECK enrichment data: nearest_city_50k_km, nearest_city_name, and \
   nearest_city_pop are the direct RI-05 fields available in the DB.
3. COMPARE the nearest known or estimated population-centre distance to \
   the project thresholds above.
4. EXPLAIN uncertainty if only a 50k+ nearest-city proxy is available and \
   the larger population tiers cannot be confidently assessed.

DECISION FRAMEWORK:
- No project threshold appears violated -> verdict=\"pass\".
- Any qualifying population centre is inside its threshold distance -> \
  verdict=\"caution\".
- Available data cannot establish distance/population class reliably -> \
  verdict=\"inconclusive\".

COMMON PITFALLS:
- Do NOT treat high RI-04 EPZ-ring density as an A12 failure.
- Do NOT use the population of a distant metropolitan area unless its \
  distance to the site is known or can be estimated with confidence.
- If nearest_city_50k_km is the only reliable field, report the 50k+ \
  proxy and avoid inventing missing 100k/500k/1M tier distances.

REFERENCE DATA: Eurostat GISCO Urban Audit, national census, OSM populated \
places, GeoNames settlement populations."""

_A13 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A13 — Grid Connection Adequacy (Avoidance)
NORMATIVE: EPRI 3002023910 siting criteria
THRESHOLD: Transmission infrastructure must be capable of exporting \
462 MWe. This requires >= 220 kV connection (110 kV is marginal, \
< 110 kV is inadequate for 462 MWe).

COAL-TO-NUCLEAR ADVANTAGE:
This is one of the strongest arguments for coal-to-nuclear conversion. \
Every operating or recently-retired coal plant had a functioning grid \
connection sized for its output. Use the existing coal plant's capacity \
as a direct proxy:
- Coal plant >= 462 MWe → grid connection almost certainly adequate
- Coal plant 200-461 MWe → grid may need upgrading but infrastructure exists
- Coal plant < 200 MWe → grid connection may be insufficient

ANALYSIS STEPS:
1. CHECK site data: grid_voltage_kv and grid_capacity_mw are the \
   strongest signals. If grid_capacity_mw >= 462 → "pass".
2. CHECK installed_capacity_mw: if the coal plant was >= 500 MWe, \
   the grid was built to handle that → "pass".
3. CHECK enrichment: grid_export_capacity_mw, nearest_substation_km.
4. ASSESS grid infrastructure quality for the country/region.

DECISION FRAMEWORK:
• Grid capacity >= 462 MWe AND voltage >= 220 kV → verdict="pass", \
  confidence="high"
• Grid capacity unclear but coal plant was >= 500 MWe → verdict="pass", \
  confidence="medium" (operating history proves connection worked)
• Grid capacity < 462 MWe OR voltage < 220 kV → verdict="caution" \
  (upgrade needed but existing infrastructure is a foundation)
• No grid data available → verdict="inconclusive"

WEAK GRID COUNTRIES:
Some countries in the scope have grid reliability concerns:
- Kosovo (XK): small grid, limited interconnection
- Moldova (MD): grid dependency on Transnistria, limited capacity
- Albania (AL): grid stability issues, limited thermal capacity
- Armenia (AM): isolated grid with limited export capacity
For sites in these countries, apply extra scrutiny even if the coal \
plant's own capacity seems adequate — the NETWORK may be constrained.

COMMON PITFALLS:
- Do NOT confuse the coal plant's generating capacity with its grid \
  export capacity. Some plants had constrained export due to network \
  bottlenecks downstream.
- Recently closed plants may have degraded grid connections (transformers \
  removed, lines de-energised) — the INFRASTRUCTURE exists but may \
  need recommissioning.
- Voltage level matters: 462 MWe requires 220-400 kV transmission. \
  110 kV lines cannot carry this load over any significant distance.

REFERENCE DATA: ENTSO-E grid map, national TSO development plans, OSM \
power infrastructure, site grid_voltage_kv and grid_capacity_mw fields."""

_A14 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A14 — Transport Access for Heavy Modules
NORMATIVE: NuScale logistics requirements; DOE/NE heavy transport guidance
THRESHOLD: At least ONE transport mode capable of delivering modules \
weighing ~700 tonnes and measuring up to 30m × 5m × 5m.

TRANSPORT MODE HIERARCHY (in order of suitability):
1. BARGE/WATERWAY — Ideal for 700t loads. Requires navigable waterway \
   (Class IV+ inland waterway, >2.5m draft) within ~5 km of site.
2. RAIL — Good for 700t with multi-car transport. Requires mainline \
   rail (not branch line) with adequate load gauge. Coal plants almost \
   always have rail sidings — this is a key conversion advantage.
3. ROAD — Feasible for segmented modules (~100-150t per segment). \
   Requires route survey but major highways (motorway or trunk) within \
   5 km are acceptable.

ANALYSIS STEPS:
1. CHECK site enrichment: nearest_rail_km, nearest_highway_km, \
   nearest_waterway_km. If rail < 1 km → strong evidence of access.
2. ASSESS coal delivery mode: How was coal delivered to this plant? \
   Rail delivery (most common) → rail siding exists → "pass".
   Waterway delivery (Danube plants, river plants) → barge access → "pass".
   Road only (small/remote plants) → assess road capacity.
3. EVALUATE at least one mode for 700t capability.

DECISION FRAMEWORK:
• Rail siding at or adjacent to plant (< 1 km) → verdict="pass", \
  confidence="high" (coal plants with rail are extremely common)
• Navigable waterway within 5 km → verdict="pass", confidence="high"
• Major highway within 5 km but no rail or waterway → verdict="pass", \
  confidence="medium" (road transport requires segmentation)
• Only minor roads, no rail, no waterway → verdict="caution"

COAL-TO-NUCLEAR TRANSPORT ADVANTAGE:
Coal plants received millions of tonnes of coal over their lifetimes. \
The transport infrastructure built for coal delivery is almost always \
sufficient for SMR module delivery. This is one of the strongest \
coal-to-nuclear conversion advantages. The key question is: does the \
infrastructure still exist and is it in usable condition?

RAIL GAUGE NOTE:
Standard gauge (1435mm): PL, CZ, SK, HU, AT, SI, HR, BA, RS, ME, XK, \
AL, MK, RO, BG, TR, most of MD.
Broad gauge (1520mm): UA, BY, EE, LV, LT, AM, parts of MD.
Gauge change at borders complicates rail transport from Western European \
module fabrication sites to broad-gauge countries. Note this as a \
logistical consideration if relevant, but it does not trigger "caution" \
— it is a planning detail, not a site deficiency.

REFERENCE DATA: OSM railway and highway data, TEN-T maps, national \
railway network maps, OSM waterway=river (boat=yes), site enrichment."""

_A15 = SYSTEM_BASE + _AVOIDANCE_PREAMBLE + """

CRITERION: A15 — Site Area Adequacy (Avoidance)
NORMATIVE: NuScale footprint requirements; EPRI 3002023910 siting guide
THRESHOLD: Available industrial land >= 14 ha (nuclear island minimum). \
Full VOYGR-6 footprint is ~72.8 ha (preferred). Sites between 14-72.8 ha \
pass the minimum but may need adjacent land acquisition.

AREA BREAKDOWN:
- Nuclear island (reactor building, turbine hall, essential services): ~14 ha
- Full site (including cooling towers, switchyard, laydown, parking, \
  security perimeter, exclusion area): ~72.8 ha
- Construction laydown (temporary, during build): additional ~20-40 ha

ANALYSIS STEPS:
1. CHECK site data: site_area_ha is the strongest signal. If provided \
   and >= 14 ha → minimum is met.
2. CHECK expansion context: favourable_area_ha may show a larger \
   surrounding envelope for laydown or future expansion, but it does \
   not replace site_area_ha for the A15 minimum.
3. ESTIMATE from coal plant characteristics:
   - Installed capacity is a proxy for site area: ~0.05-0.15 ha/MWe \
     for coal plants (a 500 MWe plant typically occupies 25-75 ha)
   - Plants with cooling towers occupy more area than once-through
   - Pit-mouth plants (adjacent to open-pit mines) often have vast \
     available land
4. ASSESS surrounding land use for expansion potential.
5. COMPARE to 14 ha minimum and note proximity to 72.8 ha ideal.

DECISION FRAMEWORK:
• Site area >= 72.8 ha → verdict="pass", confidence per data quality
• Site area 14-72.8 ha → verdict="pass" but note that adjacent land \
  acquisition may be needed for full VOYGR-6 footprint
• Site area < 14 ha but adjacent expandable land exists → verdict="caution" \
  (nuclear island cannot fit without expansion)
• Site area < 14 ha and hemmed in → verdict="caution", data_quality per \
  evidence quality
• Cannot determine site area → verdict="inconclusive"

EXPANSION POTENTIAL INDICATORS:
HIGH expansion potential:
- Adjacent open-pit mine (reclaimable land, often 100s of hectares)
- Adjacent agricultural land (purchasable, low constraints)
- Adjacent industrial brownfield (compatible zoning)
LOW expansion potential:
- Urban development on multiple sides
- River/water body constraining one or more sides
- Protected area adjacent
- Steep terrain adjacent

COMMON PITFALLS:
- Coal plant "site area" in databases may include only the fenced \
  industrial area, not the broader land parcel owned by the operator. \
  Actual available land may be larger.
- Open-pit mine adjacent to a pit-mouth plant represents enormous \
  expansion potential (post-mining reclamation land) — flag this \
  as a major positive.
- Do NOT assume a large coal plant automatically has enough area. \
  Some urban plants are tightly constrained despite high capacity.

REFERENCE DATA: CORINE Land Cover 2018, OSM landuse tags, site's \
site_area_ha field, enrichment favourable_area_ha for expansion context."""

AVOIDANCE_PROMPTS: dict[str, str] = {
    "A1": _A1, "A2": _A2, "A3": _A3, "A4": _A4,
    "A5": _A5, "A6": _A6, "A7": _A7, "A8": _A8,
    "A9": _A9, "A10": _A10, "A11": _A11, "A12": _A12,
    "A13": _A13, "A14": _A14, "A15": _A15,
}
