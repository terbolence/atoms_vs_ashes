"""Ranking criterion prompts (Tier 3 — Claude Haiku 3.5).

Each prompt requests a 1-5 score plus domain-specific measured values.
"""

from atoms_vs_ashes.llm.prompts._base import SYSTEM_BASE

PROMPT_VERSION = "v2.0-2026-04-12"

_RANKING_PREAMBLE = """

PHASE: Suitability Evaluation and Ranking (IAEA Step 3 / EPRI Steps 3-4)

═══════════════════════════════════════════
SCORING RUBRIC (1–5)
═══════════════════════════════════════════
  5 = Excellent — Significantly exceeds requirements; minimal or no \
mitigation needed. Reserve this for genuinely outstanding conditions.
  4 = Good — Meets requirements with minor favourable conditions; \
only routine design accommodations needed.
  3 = Acceptable — Meets minimum requirements; standard mitigation may \
be needed. This is the NEUTRAL baseline, not the default.
  2 = Marginal — Approaches minimum requirements; significant \
mitigation or engineering intervention required.
  1 = Poor — Does not meet requirements without major engineering \
intervention; approaches infeasibility.

SCORE UNCERTAINTY: Also return score_low and score_high representing \
the plausible range given data quality. Rules:
  • score_low <= score <= score_high
  • If data_quality="high" → range width ≤ 1 (e.g., 4-4 or 3-4)
  • If data_quality="medium" → range width ≤ 2
  • If data_quality="low" → range width ≤ 3

═══════════════════════════════════════════
ANTI-CENTER-BIAS INSTRUCTION
═══════════════════════════════════════════
Do NOT default to score=3 out of caution. A score of 3 means "acceptable \
but unremarkable" and should only be assigned when the evidence genuinely \
places the site at the midpoint. If the evidence points toward good or \
poor conditions, commit to 4/5 or 2/1 respectively. Uncertain data \
quality should widen score_low–score_high, not collapse score to 3.

═══════════════════════════════════════════
MANDATORY REASONING SEQUENCE
═══════════════════════════════════════════
Before returning your assessment, reason through these steps IN ORDER:

STEP 1 — IDENTIFY THE KEY METRIC: State the single most important \
quantitative metric for this criterion and its value (measured or \
estimated). If enrichment data provides it, state that value first. \
If absent, estimate it and flag as "LLM-estimated".

STEP 2 — MAP METRIC TO RUBRIC BAND: Compare the metric value against \
the criterion-specific rubric bands defined below. State which band it \
falls into and why. If it falls between two bands, explain which way \
the evidence tilts and commit to one.

STEP 3 — APPLY MODIFIERS: Consider site-specific factors that shift \
the score up or down within ±1 of the rubric band:
  (+) Coal-plant brownfield advantages (existing infrastructure, \
      compacted ground, established services)
  (+) Multiple redundant favourable factors
  (−) Data gaps that increase real risk
  (−) Adverse secondary factors not captured by the key metric
  (−) Training-data-cutoff concerns for rapidly-changing conditions

STEP 4 — ASSIGN SCORE AND UNCERTAINTY: Commit to score, score_low, \
score_high, confidence, and data_quality.

═══════════════════════════════════════════
ENRICHMENT DATA PROTOCOL
═══════════════════════════════════════════
If the site context includes API-sourced enrichment data for this \
criterion:
  1. USE the API value as your primary metric input.
  2. CORROBORATE — does your domain knowledge agree with the API value? \
     If yes, set data_quality to match the API's quality flag and \
     confidence="medium" or "high".
  3. CHALLENGE — if your knowledge contradicts the API value, explain \
     the discrepancy in your justification. Use the more conservative \
     (lower-scoring) interpretation unless you have strong reason not to.
  4. NEVER silently ignore API data. Always reference it in justification.

If NO enrichment data is provided for this criterion:
  • Estimate from your training knowledge.
  • Set data_quality="low".
  • Widen your score_low–score_high range.

═══════════════════════════════════════════
JUSTIFICATION FORMAT
═══════════════════════════════════════════
Write 2–4 sentences. Structure as:
  Sentence 1: Key metric value and its source (API / LLM-estimated).
  Sentence 2: Rubric band placement with reasoning.
  Sentence 3: Any modifiers applied (brownfield, data gaps, etc.).
  Sentence 4 (if needed): Uncertainty factors or caveats.
Label each factual claim as [FACT], [INFERENCE], or [UNKNOWN].

═══════════════════════════════════════════
CITED SOURCES
═══════════════════════════════════════════
You MUST populate cited_sources. Prefer specific databases (with dataset \
name and year) over generic references. Minimum: 1 specific source or \
"LLM general knowledge — low confidence" as fallback."""

# ===================================================================
# NATURAL HAZARDS (NH)
# ===================================================================

_NH01 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-01 — Seismic Ground Motion (Ranking)
NORMATIVE: SSG-9 Rev.1; SSR-1 §4.10-4.12

KEY METRIC: PGA at 475-year return period (g).

RUBRIC BANDS:
  5 = Very low seismicity — PGA₄₇₅ < 0.04 g (stable craton: Baltic \
      Shield, East European Platform interior, Moesian Platform)
  4 = Low seismicity — PGA₄₇₅ 0.04–0.10 g (platform margins, \
      Bohemian Massif interior, western Pannonian Basin)
  3 = Moderate seismicity — PGA₄₇₅ 0.10–0.20 g (within SMR design \
      envelope; Pannonian margins, outer Carpathians, Rhodope periphery)
  2 = Elevated seismicity — PGA₄₇₅ 0.20–0.35 g (significant seismic \
      design challenge; Vrancea intermediate zone, Dinaric front, \
      western Turkey Aegean coast)
  1 = High seismicity — PGA₄₇₅ > 0.35 g (approaches SMR design \
      limits 0.50 g; North Anatolian Fault zone, eastern Turkey, \
      south-western Balkans)

ADDITIONAL METRIC: Estimate PGA at 2475-year return period where \
possible. A large ratio PGA₂₄₇₅/PGA₄₇₅ > 2.5 suggests epistemic \
uncertainty in the hazard model — note this in justification.

REGION CALIBRATION:
  • Poland: Mostly PGA₄₇₅ < 0.04 g except Sudetes (0.04–0.08 g)
  • Czech Republic: 0.02–0.08 g (Bohemian Massif)
  • Romania: Bimodal — Vrancea influence 0.15–0.35 g; platform <0.06 g
  • Turkey: Extremely variable — 0.05 g (Thrace) to >0.40 g (NAF zone)
  • Hungary: 0.04–0.12 g (Pannonian Basin)
  • Bulgaria: 0.08–0.25 g (Maritza zone to Rhodope)

ENRICHMENT FIELDS: pga_475yr_g, pga_2475yr_g (from EFEHR/SHARE API).

REFERENCE DATA SOURCES: SHARE ESHM20 PGA maps, GEM Global Seismic \
Hazard Map v2018.1, national seismic hazard assessments (PGI-PIB, \
INFP Romania, KOERI Turkey, GFZ Potsdam)."""

_NH06 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-06 — Foundation Conditions (Ranking)
NORMATIVE: SSG-35 §4.18-4.20; NS-R-3 §3.38

KEY METRIC: Inferred bearing capacity based on surface lithology and \
depth to competent bedrock.

RUBRIC BANDS:
  5 = Competent crystalline/metamorphic bedrock at <5 m depth; bearing \
      capacity >500 kPa (granite, gneiss, quartzite terrains)
  4 = Consolidated sedimentary rock (limestone, sandstone) at 5–15 m; \
      bearing capacity 250–500 kPa
  3 = Stiff clay, dense sand/gravel, or weathered rock at 10–25 m; \
      bearing capacity 150–250 kPa; standard piled foundations viable
  2 = Soft alluvial deposits, thick loess, high groundwater; depth to \
      bedrock >25 m; bearing capacity 75–150 kPa; deep piling required
  1 = Very soft saturated soils, peat, loose fill, or active subsidence \
      area; bearing capacity <75 kPa; extensive ground improvement

COAL-PLANT MODIFIER: Existing coal plants have foundations designed \
for heavy equipment (turbines, boilers). This demonstrates the ground \
can support significant structural loads — apply a +0.5 to +1 modifier \
relative to raw geological assessment, unless the plant has known \
foundation problems.

ENRICHMENT FIELDS: bearing_capacity_kpa, depth_to_bedrock_m.

REFERENCE DATA SOURCES: EGDI surface lithology maps (1:1M), OneGeology \
WMS, national geological survey 1:50k sheets, EGDI geotech boreholes \
layer, European Soil Database (ESDB) for superficial deposit types."""

_NH08 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-08 — Coastal Flooding (Ranking)
NORMATIVE: SSG-18; NS-R-3 §3.54-3.57

KEY METRIC: Distance to nearest coastline (km) combined with site \
elevation above mean sea level.

RUBRIC BANDS:
  5 = Inland site >100 km from coast — no coastal risk whatsoever. \
      [FAST-TRACK: If site is >100 km from any sea/ocean, immediately \
      assign score=5, confidence="high", data_quality="high".]
  4 = Far from coast (50–100 km) or high elevation (>100 m AMSL) \
      with >20 km from coast
  3 = Moderate coastal proximity (20–50 km) with elevation >30 m AMSL; \
      or >50 km but in tsunami-aware basin (Black Sea, Marmara)
  2 = Close to coast (5–20 km) with low elevation (<30 m); some \
      storm surge or tsunami risk
  1 = Very close to coast (<5 km) or in documented storm surge / \
      tsunami inundation zone

GEOGRAPHIC NOTE: Most coal plants in the 23-country scope are inland \
river sites. Coastal plants exist primarily in Turkey (Aegean, \
Mediterranean, Black Sea coasts) and possibly Croatia/Albania. \
For inland sites, this criterion should score 5 with high confidence.

ENRICHMENT FIELDS: distance_to_coast_km, storm_surge_risk, \
tsunami_risk.

REFERENCE DATA SOURCES: NOAA/NGDC Historical Tsunami Database, EU-DEM \
v1.1 for elevation, OpenStreetMap coastline data, JRC storm surge \
projections, NEAMTWS tsunami hazard maps."""

_NH09 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-09 — River Flooding (Ranking)
NORMATIVE: SSG-18; NS-R-3 §3.54-3.57

KEY METRIC: Flood zone classification and site elevation relative to \
the nearest river's 100-year and 1000-year flood levels.

RUBRIC BANDS:
  5 = Site >2 km from any significant river AND well above (>15 m) \
      any potential floodplain; no upstream dams of concern
  4 = Site elevated above the 1000-year flood level; minor flood risk \
      only with existing defences adequate
  3 = Site in 500-year floodplain but above 100-year level; flood \
      defences feasible with moderate investment
  2 = Site in 100-year floodplain; significant flood defence \
      engineering needed; or downstream of a major dam with \
      dam-break inundation potential
  1 = Site in frequent flood zone (20–50 year recurrence) or directly \
      downstream of a high-consequence dam with limited warning time

COAL-PLANT CONTEXT: Coal plants require cooling water and are almost \
always near rivers. This means they inherently face some flood risk. \
Evaluate whether the plant was historically affected by floods — if it \
has operated for decades without flood damage, that is positive evidence \
(score modifier +0.5). Known historical flooding at the plant is a \
strong negative signal.

ENRICHMENT FIELDS: flood_zone_class, nearest_river_km, \
dam_break_exposure.

REFERENCE DATA SOURCES: EU Floods Directive flood hazard maps, JRC EFAS, \
national flood risk maps (ISOK Poland, ANAR Romania, DSI Turkey), \
HydroSHEDS river network, ICOLD World Register of Dams for upstream \
dam exposure."""

_NH10 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-10 — Extreme Wind Conditions (Ranking)
NORMATIVE: SSG-18; SSR-1 §4.13

KEY METRIC: Estimated 50-year return period maximum gust speed (m/s) \
at 10 m height.

RUBRIC BANDS:
  5 = Sheltered continental interior, max gust <30 m/s (Pannonian \
      Basin interior, sheltered Bohemian valleys)
  4 = Moderate continental, max gust 30–40 m/s (most Central European \
      lowlands, inland Poland)
  3 = Exposed plains or moderate coastal exposure, max gust 40–50 m/s \
      (Baltic coast, Thracian Plain, channelled valleys)
  2 = Known storm corridor or exposed coastal, max gust 50–60 m/s \
      (Turkish Mediterranean coast, Bora-affected Adriatic)
  1 = Frequent severe storms or tornado-prone, max gust >60 m/s

REGION CALIBRATION:
  • Central Europe (PL, CZ, SK, HU): Generally 28–42 m/s range
  • Balkans interior: 25–38 m/s
  • Turkish coasts: 35–55 m/s (Mediterranean Lodos, Aegean Meltemi)
  • Adriatic coast (HR, AL): Bora winds can reach 50+ m/s
  • Tornado risk in the region is generally low; note if ESWD records \
    any significant tornado events near the site

ENRICHMENT FIELDS: nh10_max_wind_speed_ms, nh10_tornado_risk.

REFERENCE DATA SOURCES: European Wind Atlas, Eurocode 1 wind load maps \
(EN 1991-1-4 national annexes), national meteorological service extreme \
wind statistics, ESWD (European Severe Weather Database) for tornado \
and downburst records."""

_NH11 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-11 — Extreme Precipitation (Ranking)
NORMATIVE: SSG-18; SSR-1 §4.14

KEY METRIC: Estimated maximum 24-hour rainfall with 100-year return \
period (mm), combined with site drainage context.

RUBRIC BANDS:
  5 = Semi-arid continental (<60 mm/day 100-yr); excellent natural \
      drainage (e.g., Turkish interior steppe, Moldovan plateau)
  4 = Moderate precipitation (60–100 mm/day 100-yr); good drainage; \
      gentle slopes assist runoff
  3 = Average conditions (100–150 mm/day 100-yr); standard drainage \
      design sufficient; flat terrain requiring engineered drainage
  2 = High precipitation zone (150–200 mm/day 100-yr); significant \
      drainage engineering needed; history of flash floods in region
  1 = Very high precipitation / flash flood prone (>200 mm/day 100-yr); \
      Mediterranean-influenced mountain catchments; karst-enhanced \
      flash flood risk

COAL-PLANT MODIFIER: Existing coal plants have stormwater drainage \
systems. If the plant has operated without significant drainage issues, \
this is evidence that local precipitation is manageable at the site \
scale (+0.5 modifier).

ENRICHMENT FIELDS: nh11_extreme_precip_mm.

REFERENCE DATA SOURCES: National meteorological service IDF curves, \
E-OBS gridded precipitation dataset, ECA&D extreme indices, Eurocode \
national annex rainfall intensities."""

_NH12 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-12 — Extreme Temperatures (Ranking)
NORMATIVE: SSG-18; SSR-1 §4.15

KEY METRICS: Record minimum and maximum temperatures for the region, \
and typical annual extremes.

RUBRIC BANDS:
  5 = Mild oceanic-influenced climate; annual extremes rarely outside \
      −10 to +35°C (Croatian/Slovenian coast, western Turkey Aegean)
  4 = Moderate continental; extremes −20 to +38°C (Pannonian, \
      Bohemian basins, coastal Bulgaria)
  3 = Continental; extremes −25 to +40°C; standard HVAC design \
      handles this range (most of Poland, Romania, Serbia)
  2 = Harsh continental; extremes −30 to +42°C; enhanced thermal \
      design needed (eastern Poland, northern Ukraine, Belarus)
  1 = Extreme climate; temperatures below −35°C or above +44°C \
      regularly recorded (high-altitude eastern Turkey, steppe Ukraine)

SMR DESIGN NOTE: NuScale VOYGR-6 is designed for ambient temperatures \
−40°C to +46°C (ultimate heat sink limits). Most sites in the 23-country \
scope are within this envelope, so score=1 should be rare.

ENRICHMENT FIELDS: nh12_extreme_temp_max_c, nh12_extreme_temp_min_c.

REFERENCE DATA SOURCES: National meteorological service climate normals \
and extremes records, E-OBS gridded temperature dataset v27+, \
Köppen-Geiger climate classification maps (Beck et al. 2018)."""

_NH13 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-13 — Wildfire / Forest Fire Risk (Ranking)
NORMATIVE: SSR-1 §4.16; US NRC RG 1.127

KEY METRIC: Percentage of combustible vegetation (forest, shrubland, \
scrub) within a 5 km radius of the site.

RUBRIC BANDS:
  5 = Fully industrial/urban surroundings; <5% combustible vegetation \
      within 5 km (active industrial zone, mining district)
  4 = Predominantly non-combustible land cover; 5–15% forest/shrubland \
      within 5 km; agricultural matrix with scattered woodlots
  3 = Mixed land cover; 15–35% combustible vegetation within 5 km; \
      no history of large fires in the area
  2 = Significant forest/shrubland; 35–55% combustible within 5 km; \
      region has documented fire events
  1 = Heavily forested surroundings; >55% combustible within 5 km; \
      region has frequent or severe fire history (Mediterranean \
      Turkey, southern Balkans dry forests)

COAL-PLANT CONTEXT: Coal plants create a cleared industrial zone that \
acts as a natural firebreak. The immediate vicinity is typically \
cleared, paved, or covered with industrial infrastructure. This \
inherently reduces wildfire risk compared to a greenfield site with \
the same surrounding vegetation.

ENRICHMENT FIELDS: nh13_wildfire_combustible_pct (from CORINE analysis).

REFERENCE DATA SOURCES: CORINE Land Cover 2018 for CLC classes 311-313, \
322, 324 within 5 km buffer, EFFIS (European Forest Fire Information \
System) historical fire data, national forestry agency fire risk maps."""

_NH14 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NH-14 — Combined / Concurrent Natural Hazards (Ranking)
NORMATIVE: SSR-1 §4.17; NS-R-3 §3.59

KEY METRIC: Number and severity of correlated hazard pairs at the site.

RUBRIC BANDS:
  5 = Single-hazard environment; hazards are independent and low-level \
      (e.g., stable craton with continental climate — only mild weather \
      extremes). No plausible concurrent scenario identified.
  4 = Minimal combined risk; 1 plausible but low-probability concurrent \
      pair (e.g., moderate precipitation + minor river flood)
  3 = Some potential for correlated hazards; 1–2 credible pairs \
      (e.g., seismic event + liquefaction amplification; flood + \
      landslide in hilly terrain)
  2 = Notable combined risk; 2–3 correlated hazard pairs, at least one \
      with moderate severity (e.g., coastal seismic + tsunami; river \
      flood + slope instability; wildfire + extreme heat)
  1 = High combined risk; 3+ correlated severe hazard pairs; site is \
      in a multi-hazard convergence zone (e.g., Turkish Mediterranean: \
      seismic + tsunami + wildfire + extreme heat)

SYNTHESIS INSTRUCTION: This criterion MUST be assessed by cross-\
referencing the other NH criteria for this site. Identify plausible \
concurrent scenarios specific to the site's geographic setting. Do not \
simply average other NH scores — focus on CORRELATION between hazards.

Known correlated pairs for this region:
  • Earthquake → tsunami (Black Sea, Marmara, Aegean coasts)
  • Earthquake → liquefaction (alluvial plains with seismicity)
  • Earthquake → landslide (Carpathian foothills, Dinaric Alps)
  • Extreme heat → wildfire (Mediterranean fringe)
  • Extreme precipitation → river flood → landslide (mountain catchments)
  • Storm → flood + wind damage (coastal areas)

ENRICHMENT FIELDS: pga_475yr_g, distance_to_coast_km, \
flood_zone_class, wildfire_combustible_pct.

REFERENCE DATA SOURCES: Synthesize from other NH criteria assessed \
for this site. INFORM Risk Index (JRC/DRMKC) for multi-hazard \
profiles by country, OECD multi-hazard country profiles, ThinkHazard! \
(World Bank/GFDRR) country hazard summaries."""

# ===================================================================
# HUMAN-INDUCED HAZARDS (HI)
# ===================================================================

_HI01 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-01 — Aviation Hazard (Ranking)
NORMATIVE: SSG-35 Table II-1 No.2-5; NS-G-3.1 §4

KEY METRIC: Distance to the nearest airport of any type (km) and \
total number of airports within 30 km.

RUBRIC BANDS:
  5 = No airports of any type within 30 km
  4 = Only small airports/airstrips, all >16 km away; no flight paths \
      crossing the site vicinity
  3 = Some airports 10–16 km away with low traffic (<10,000 movements \
      /year); or distant large airport (>25 km) with high traffic
  2 = Airports 5–10 km away; or busy airport (>50,000 movements/year) \
      10–16 km away; flight paths potentially crossing site
  1 = Major international airport <10 km; or any airport <5 km; \
      or documented flight path directly over site

DECISION TREE:
  IF nearest_airport_km > 30 → score=5
  ELIF nearest_airport_km > 16 AND all airports are small → score=4
  ELIF nearest_airport_km > 10 → score=3 (adjust by traffic volume)
  ELIF nearest_airport_km > 5 → score=2
  ELSE → score=1

ENRICHMENT FIELDS: nearest_airport_km, nearest_airport_name, \
airport_count.

REFERENCE DATA SOURCES: OurAirports database (2024), Eurostat aviation \
statistics (avia_tf_apal), OpenStreetMap aeroway data."""

_HI02 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-02 — Industrial Explosion Hazard (Ranking)
NORMATIVE: SSG-35 Table II-1 No.8; NS-G-3.1 §5

KEY METRIC: Distance to the nearest SEVESO III or equivalent industrial \
facility (km).

RUBRIC BANDS:
  5 = No industrial facilities of concern within 10 km; rural or \
      light-industrial context
  4 = Minor industry only (non-SEVESO), all >5 km; no refineries, \
      chemical plants, or explosives factories
  3 = Some industrial activity 2–5 km, non-SEVESO or lower-tier \
      SEVESO only; OR upper-tier SEVESO facility >5 km
  2 = Upper-tier SEVESO facility or major chemical/refining complex \
      2–5 km; or multiple lower-tier facilities in close proximity
  1 = Major SEVESO upper-tier facility, refinery, or explosives \
      factory <2 km from site

COAL-PLANT CONTEXT: Coal plants are industrial facilities and are \
often located in industrial zones alongside other heavy industry. \
The presence of the coal plant itself does NOT count as a SEVESO \
facility. Focus on separate industrial neighbours that could produce \
blast overpressure affecting nuclear safety-related structures.

ENRICHMENT FIELDS: nearest_seveso_km, nearest_industrial_km.

REFERENCE DATA SOURCES: EU SEVESO III establishment registers (national \
competent authority public lists), E-PRTR (European Pollutant Release \
and Transfer Register), national environmental agency databases, \
OpenStreetMap landuse=industrial tags."""

_HI03 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-03 — Toxic Release Hazard (Ranking)
NORMATIVE: SSG-35 Table II-1 No.9; NS-G-3.1 §5

KEY METRIC: Distance to the nearest facility capable of releasing \
toxic gases/chemicals that could form a hazardous cloud (km).

RUBRIC BANDS:
  5 = No toxic release sources within 10 km; site in agricultural or \
      light-industrial area
  4 = Minor chemical processing only, >8 km; low-volume facilities
  3 = Chemical or petrochemical facilities 5–8 km; or gas pipeline \
      >3 km; moderate-scale industrial chemistry in vicinity
  2 = Major chemical/petrochemical complex 2–5 km; or high-pressure \
      gas transmission pipeline <3 km; chlorine/ammonia storage nearby
  1 = Major toxic release source <2 km (refinery HF unit, chlor-alkali \
      plant, ammonia terminal, LPG bulk storage)

DISTINCTION FROM HI-02: HI-02 assesses EXPLOSION blast overpressure. \
This criterion assesses AIRBORNE TOXIC CLOUD drift that could affect \
control room habitability and worker safety. A single facility may \
be relevant to both criteria.

ENRICHMENT FIELDS: nearest_toxic_source_km.

REFERENCE DATA SOURCES: EU SEVESO III registers, E-PRTR for toxic \
substance releases (search for chlorine, ammonia, HF, phosgene, \
SO₂ releases), ARIA accident database, national pipeline maps."""

_HI04 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-04 — External Fire Hazard (Ranking)
NORMATIVE: NS-G-3.1 §5; SSG-35

KEY METRIC: Distance to the nearest flammable material storage or \
major pipeline (km).

RUBRIC BANDS:
  5 = No flammable storage or pipelines within 10 km; no fuel depots, \
      gas pipelines, or LNG/LPG terminals
  4 = Minor fuel storage >5 km (small gas stations, agricultural fuel \
      tanks); no major gas pipeline within 5 km
  3 = Moderate fuel storage or gas distribution pipeline 2–5 km; \
      industrial fuel depots at distance
  2 = Significant flammable storage or major gas transmission pipeline \
      <2 km; regional fuel depot nearby
  1 = Adjacent to refinery, LNG terminal, major fuel depot, or bulk \
      petrochemical storage; or high-pressure gas pipeline <500 m

COAL-PLANT CONTEXT: Coal plants may have associated fuel oil storage \
for startup/backup operations. This is typically modest and already \
within the site boundary — it is an internal hazard, not an external \
one. Focus on EXTERNAL sources of fire that could threaten the future \
nuclear plant.

ENRICHMENT FIELDS: nearest_flammable_storage_km, \
nearest_pipeline_km.

REFERENCE DATA SOURCES: E-PRTR, national pipeline operator public \
maps, OpenStreetMap pipeline and fuel storage data, SEVESO III \
registers for upper-tier flammable substance establishments."""

_HI05 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-05 — Transport Hazards (Ranking)
NORMATIVE: NS-G-3.1 §5

KEY METRIC: Distance to the nearest major transport route carrying \
hazardous materials (km), weighted by route type and traffic volume.

RUBRIC BANDS:
  5 = No major transport routes within 5 km carrying hazmat; site \
      accessed only by minor roads
  4 = Minor roads only within 2 km; some truck traffic but low \
      hazmat volume; railway >5 km
  3 = Highway or railway within 2–5 km carrying standard hazmat \
      volumes (ADR/RID regulated); typical industrial zone access
  2 = Major hazmat corridor <2 km (busy freight railway, motorway \
      with significant tanker traffic, pipeline right-of-way)
  1 = Adjacent to (<500 m) major hazmat transport hub, rail marshalling \
      yard, or motorway junction with heavy tanker traffic

COAL-PLANT CONTEXT: Coal plants have rail sidings and road access for \
coal delivery. These transport links are inherent to the site. The \
question is whether these same routes (or nearby ones) carry hazardous \
materials whose release during transport could affect the nuclear plant.

ENRICHMENT FIELDS: hi05_hazmat_route_distance_km.

REFERENCE DATA SOURCES: OpenStreetMap highway and railway data, TEN-T \
network maps, ADR (road) / RID (rail) hazardous goods route \
designations."""

_HI06 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-06 — Military Installations (Ranking)
NORMATIVE: SSG-35 Table II-1 No.6-7

KEY METRIC: Distance to the nearest military installation (km), \
weighted by installation type.

RUBRIC BANDS:
  5 = No military facilities within 30 km
  4 = Minor military presence >15 km (administrative barracks, \
      training schools, non-combat logistics)
  3 = Military base 8–15 km, non-combat function (logistics depot, \
      communications, administrative); or small garrison >10 km
  2 = Military firing/practice ranges 5–8 km; or ammunition storage \
      5–10 km; or active combat base 8–15 km
  1 = Active firing range, bombing range, or ammunition depot <5 km; \
      restricted military airspace directly over site

DATA CAVEAT: Military installations are often incompletely mapped in \
public databases, especially in countries with Soviet-era legacy bases. \
If you cannot identify specific installations but the region is known \
for military presence, note this uncertainty and set confidence="low" \
with a wider score range.

ENRICHMENT FIELDS: nearest_military_km, nearest_military_name, \
military_count.

REFERENCE DATA SOURCES: OpenStreetMap military tags, NOTAM permanent \
restricted airspace zones, national defence public facility lists."""

_HI07 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-07 — Electromagnetic Interference (Ranking)
NORMATIVE: SSG-35; IEEE Std 603

KEY METRIC: Distance to the nearest high-power transmitter or \
broadcast facility (km).

RUBRIC BANDS:
  5 = No significant transmitters within 10 km; rural area with \
      only standard mobile phone base stations
  4 = Minor transmitters (FM radio, mobile towers <100W ERP) 5–10 km; \
      no high-power broadcast
  3 = Some transmitters 2–5 km including medium-power (FM/TV relay, \
      1–10 kW); standard EMC design sufficient
  2 = High-power broadcast transmitter (>100 kW ERP) 1–2 km; or \
      radar installation 2–5 km
  1 = Major broadcast facility or radar station <1 km; high-power \
      military radar or HF transmitter in immediate vicinity

NOTE: EMI from transmission lines (the plant's own grid connection) is \
an internal design issue, not scored here. Focus on external broadcast \
and radar transmitters.

ENRICHMENT FIELDS: nearest_transmitter_km, transmitter_type, \
hi07_transmitter_count.

REFERENCE DATA SOURCES: OpenStreetMap man_made=mast/tower and \
communication=* tags, national frequency allocation registers, \
ITU broadcast database for high-power transmitters."""

_HI08 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: HI-08 — Other Nuclear Installations (Ranking)
NORMATIVE: SSR-1 §4.18; NS-R-3 §3.60

KEY METRIC: Distance to the nearest operating or planned nuclear \
facility (km).

RUBRIC BANDS:
  5 = No nuclear facility within 100 km. \
      OR: Site is on an existing nuclear power plant site (co-location \
      is viewed favourably — shared EPZ, existing regulatory framework, \
      proven local acceptance). Score 5 for co-location.
  4 = Nuclear facility 50–100 km away; no EPZ overlap (EPZ ≤ 25 km \
      for SMRs); minimal interaction
  3 = Nuclear facility 30–50 km away; no direct EPZ overlap but \
      within 80 km emergency awareness zone
  2 = Nuclear facility 15–30 km; potential EPZ interaction for combined \
      emergency planning; shared resource demands
  1 = Nuclear facility <15 km with significant EPZ overlap; concurrent \
      emergency scenarios must be jointly managed

REGIONAL NUCLEAR LANDSCAPE:
  • Operating reactors: CZ (Dukovany, Temelín), HU (Paks), RO \
    (Cernavodă), BG (Kozloduy), SK (Mochovce, Bohunice), UA (4 sites), \
    AM (Metsamor), TR (Akkuyu under construction), BY (Ostrovets)
  • Planned: PL (Lubiatowo-Kopalino), RO (Doicești SMR), TR (Sinop)

ENRICHMENT FIELDS: nearest_nuclear_km, nearest_nuclear_name.

REFERENCE DATA SOURCES: IAEA PRIS (Power Reactor Information System), \
World Nuclear Association reactor database, national nuclear regulatory \
authority websites."""

# ===================================================================
# RADIOLOGICAL IMPACT (RI)
# ===================================================================

_RI01 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-01 — Atmospheric Dispersion Conditions (Ranking)
NORMATIVE: SSG-35 §A.35-A.37; NS-G-3.2

KEY METRIC: Prevailing wind speed (m/s) combined with terrain-induced \
atmospheric stability and mixing layer height.

RUBRIC BANDS:
  5 = High dispersion capacity — open terrain with consistent moderate \
      winds (>4 m/s annual mean); high mixing layer (>1000 m); no \
      terrain-induced inversions
  4 = Good dispersion — mostly open terrain; moderate winds (3–4 m/s); \
      inversions rare; mixing height >700 m
  3 = Average dispersion — moderate wind (2–3 m/s); some calm periods; \
      typical mixing layer (~500 m); flat terrain
  2 = Poor dispersion — frequent calm conditions (<2 m/s); valley site \
      prone to temperature inversions; limited ventilation; mixing \
      height <300 m
  1 = Very poor dispersion — persistent inversions; stagnant air basin; \
      site in narrow valley or closed basin with <1 m/s prevailing wind

TERRAIN EFFECTS (critical for this region):
  • Valley sites (Danube valley, Carpathian valleys): prone to nocturnal \
    inversions trapping pollutants → score 2–3
  • Open plains (Great Hungarian Plain, Thracian Plain, Polish lowlands): \
    generally good dispersion → score 3–4
  • Coastal sites: good ventilation from sea breezes → score 4–5
  • Mountain basins (Bohemian Basin, Transylvanian Basin): variable, \
    can trap air in winter → score 2–3

ENRICHMENT FIELDS: prevailing_wind_dir, avg_wind_speed_ms, \
mixing_height_m.

REFERENCE DATA SOURCES: National meteorological service wind roses and \
mixing height data, European Wind Atlas, ECMWF ERA5 reanalysis for \
boundary layer height and 10m wind speed climatology."""

_RI02 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-02 — Surface Water Dispersion (Ranking)
NORMATIVE: SSG-35 §A.38; NS-G-3.2

KEY METRIC: Mean annual discharge (m³/s) of the nearest river, \
combined with proximity and number of downstream water intakes.

RUBRIC BANDS:
  5 = Adjacent to major river with high dilution capacity (>200 m³/s \
      mean discharge, e.g., Danube, Dnieper, Vistula lower reaches); \
      no downstream drinking water intakes within 50 km
  4 = Good dilution (50–200 m³/s); few downstream water users within \
      50 km; large river system
  3 = Moderate river flow (10–50 m³/s); some downstream water users; \
      seasonal low flows may reduce dilution capacity
  2 = Small river (<10 m³/s); significant downstream water use; or \
      lake discharge with limited dilution; or reservoir with long \
      residence time
  1 = Very low flow river (<2 m³/s) or intermittent stream; critical \
      downstream water supply; or site on reservoir that serves as \
      regional drinking water source

RIVER REFERENCE FLOWS (annual mean):
  • Danube (lower): ~6,500 m³/s  • Vistula (lower): ~1,000 m³/s
  • Dnieper (Zaporizhzhia): ~1,500 m³/s  • Maritsa (BG-TR): ~50 m³/s
  • Olt (RO): ~100 m³/s  • Morava (CZ): ~100 m³/s
  Smaller tributaries: 5–50 m³/s typical

ENRICHMENT FIELDS: nearest_river_flow_m3s.

REFERENCE DATA SOURCES: GRDC river discharge data, European river basin \
management plans (WFD), national hydrology services, HydroSHEDS river \
network."""

_RI03 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-03 — Groundwater Conditions (Ranking)
NORMATIVE: SSG-35 §A.39; NS-G-3.2

KEY METRIC: Aquifer type and vulnerability classification combined \
with local groundwater use intensity.

RUBRIC BANDS:
  5 = Deep water table (>20 m), impermeable bedrock (crystalline, \
      massive clay); no significant aquifer use within 10 km
  4 = Low vulnerability — clay confining layers, deep aquifer system, \
      limited local groundwater abstraction
  3 = Moderate vulnerability — mixed geology, semi-confined aquifer, \
      some local groundwater wells for agricultural use
  2 = Shallow unconfined aquifer (<5 m depth) in permeable sands or \
      gravels; active local groundwater use for drinking/agriculture
  1 = Critical aquifer — karst aquifer, major alluvial water supply \
      aquifer, or sole-source aquifer for a significant population; \
      or site above a Groundwater Body with "poor" status under WFD

COAL-PLANT CONTEXT: Coal plants may have contaminated local groundwater \
(ash ponds, fuel storage). While this is a pre-existing issue, it \
suggests the aquifer is reachable by surface contaminants — a \
vulnerability indicator for nuclear groundwater pathways.

ENRICHMENT FIELDS: aquifer_type, groundwater_flow_dir.

REFERENCE DATA SOURCES: EGDI hydrogeological maps (BGR 1:1.5M), WHYMAP \
World Hydrogeological Map, WFD groundwater body status reports, national \
groundwater monitoring networks."""

_RI04 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-04 — Population Density at EPZ Radii (Ranking)
NORMATIVE: NS-G-3.2; SSG-35 §A.39

KEY METRIC: Population density within 5 km EPZ (persons/km²).

RUBRIC BANDS:
  5 = Very low density — <50 persons/km² within 5 km; rural or \
      depopulating industrial area
  4 = Low density — 50–200 persons/km² within 5 km; small settlements, \
      agricultural hinterland
  3 = Moderate density — 200–500 persons/km² within 5 km; small town \
      partially within EPZ, or scattered suburban development
  2 = Elevated density — 500–1,000 persons/km² within 5 km; medium \
      town centre within or at EPZ boundary
  1 = High density — >1,000 persons/km² within 5 km; city of >50,000 \
      substantially within EPZ

SECONDARY METRICS: Also consider:
  • Population within 25 km (affects intermediate EPZ planning)
  • Total population within 80 km (affects emergency awareness zone)
  These should modulate ±0.5 from the primary 5 km assessment.

REGIONAL CONTEXT: Eastern European coal regions often have moderate \
mining towns (5,000–50,000) near plants. Many of these regions are \
experiencing population decline, which improves the long-term score.

ENRICHMENT FIELDS: pop_density_5km, pop_density_25km, pop_total_80km.

REFERENCE DATA SOURCES: WorldPop / GHS-POP gridded population 2020, \
Eurostat GEOSTAT 1 km² grid, national census data (2021 round)."""

_RI05 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-05 — Distance to Population Centres (Ranking)
NORMATIVE: NS-G-3.2; SSG-35

KEY METRIC: Distance to the nearest city with population > 50,000 (km).

RUBRIC BANDS:
  5 = >80 km from any city >50,000 population; remote site
  4 = 40–80 km from nearest major city; regional town nearby but \
      no large urban centre
  3 = 20–40 km from nearest major city; city within the 25 km EPZ \
      outer boundary
  2 = 10–20 km from nearest city >50,000; city partially within the \
      16 km EPZ; significant emergency planning implications
  1 = <10 km from a city >50,000; city centre within or adjacent to \
      the 5 km EPZ

NOTE: This criterion complements RI-04 (population density). RI-04 \
captures dispersed population, while this criterion captures the \
risk of a single large urban centre being within emergency planning \
zones. Both are important for different reasons.

ENRICHMENT FIELDS: nearest_city_50k_km, nearest_city_name, \
nearest_city_pop.

REFERENCE DATA SOURCES: GeoNames cities with population >50,000, \
Eurostat Urban Audit, national statistical offices."""

_RI06 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: RI-06 — Population Growth Projections (Ranking)
NORMATIVE: SSG-35 §A.39; NS-R-3 §2.28

KEY METRIC: Projected annualized population growth rate (%) for the \
NUTS-3 region over a 60-year plant lifetime horizon.

RUBRIC BANDS:
  5 = Declining population region (< −0.3%/yr projected); common in \
      Eastern European coal regions experiencing de-industrialization
  4 = Stable to slightly declining (−0.3% to 0.0%/yr)
  3 = Stable (0.0% to +0.3%/yr); no major urbanization drivers
  2 = Moderate growth (+0.3% to +1.0%/yr); proximity to growing city, \
      industrial development corridor, or EU accession growth effect
  1 = Rapid growth (>+1.0%/yr) or major urbanization planned nearby; \
      new satellite city, major infrastructure project driving growth

REGIONAL TRENDS (strong generalizations):
  • BG, RO, HR, RS, BA, LT, LV, UA, MD, BY: Generally declining \
    (score 4–5 absent local counter-trends)
  • PL, CZ, SK, HU: National decline but major cities growing; \
    assess LOCAL not national trend
  • TR: Growing nationally but coal regions may differ from Istanbul/Ankara
  • AL, XK, MK: Mixed — emigration vs. young demographic

ENRICHMENT FIELDS: pop_growth_rate_pct, \
projected_pop_25km_60yr.

REFERENCE DATA SOURCES: Eurostat EUROPOP2023 population projections, \
UN World Population Prospects 2024, national statistical office \
demographic forecasts, NUTS-3 level projections where available."""

# ===================================================================
# EMERGENCY PLANNING (EP)
# ===================================================================

_EP02 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: EP-02 — Evacuation Routes (Ranking)
NORMATIVE: GS-G-2.1; NS-R-3 §2.29

KEY METRIC: Road density within the 5 km EPZ (km of road per km²) \
combined with road quality classification.

RUBRIC BANDS:
  5 = Dense road network (>5 km/km²) with motorway/dual carriageway \
      access within 3 km; multiple independent evacuation routes \
      radiating in ≥4 compass directions
  4 = Good road network (3–5 km/km²); at least one primary road \
      (national/regional) with 2+ alternative routes
  3 = Adequate roads (2–3 km/km²); 2–3 evacuation routes but limited \
      capacity; single primary road supplemented by secondary routes
  2 = Sparse road network (1–2 km/km²); single main road dominates; \
      limited alternatives; congestion bottleneck likely
  1 = Very poor access (<1 km/km²); single narrow road or dead-end \
      topology; site effectively has one escape direction

COAL-PLANT ADVANTAGE: Coal plants have road and rail access for fuel \
delivery and workforce transport. This provides at minimum one quality \
access route. The question is whether MULTIPLE independent routes exist \
for radial evacuation of the surrounding population.

ENRICHMENT FIELDS: road_density_km_per_km2, has_motorway_access.

REFERENCE DATA SOURCES: OpenStreetMap road network data (motorway, \
trunk, primary, secondary highway classifications), national road \
administration maps."""

_EP03 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: EP-03 — Physical Geography Constraints on Emergency Response \
(Ranking)
NORMATIVE: GS-G-2.1

KEY METRIC: Number and severity of geographic barriers within the 5 km \
EPZ that constrain evacuation (rivers, mountains, water bodies).

RUBRIC BANDS:
  5 = Flat open terrain; no water barriers; unrestricted evacuation in \
      all directions; terrain imposes no constraints
  4 = Generally flat; minor water crossings (streams/canals with \
      multiple bridges); gentle rolling terrain
  3 = Some geographic constraints — one significant river crossing \
      (with adequate bridges), or moderate terrain limiting 1–2 \
      evacuation directions
  2 = Significant barriers — major river bisecting EPZ with limited \
      bridge crossings; or hilly/mountainous terrain channelling \
      evacuation; or large reservoir/lake blocking one sector
  1 = Severe constraints — island site, narrow valley with single \
      exit, peninsula, or major river with single bridge serving \
      the EPZ population

COAL-PLANT CONTEXT: Coal plants near rivers (for cooling) typically \
have the river as a geographic barrier on one side. Assess how many \
bridge crossings exist within 5 km and whether evacuation can proceed \
without crossing the river.

ENRICHMENT FIELDS: major_river_barrier, waterway_count_epz.

REFERENCE DATA SOURCES: OpenStreetMap waterway, bridge, and terrain \
data, EU-DEM v1.1 terrain analysis."""

_EP04 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: EP-04 — Special Populations in EPZ (Ranking)
NORMATIVE: GS-G-2.1 §4

KEY METRIC: Count of institutions housing difficult-to-evacuate \
populations within the 16 km EPZ.

RUBRIC BANDS:
  5 = No hospitals, prisons, nursing homes, or large schools within \
      16 km EPZ; entirely rural hinterland
  4 = Minimal special facilities (1–2 small care homes or clinics; \
      no major hospital or prison)
  3 = Small hospital (< 200 beds), or 2–3 care homes, or a school \
      cluster within the EPZ
  2 = Major hospital (200+ beds), or prison, or multiple care \
      institutions creating a population requiring specialized \
      evacuation transport
  1 = Multiple large institutions (regional hospital + prison + \
      nursing complex); or a single very large institution (>500 beds) \
      that would dominate evacuation resource allocation

NOTE: Small settlements may have institutions not in major databases. \
If the EPZ intersects a town of >10,000, assume at least one small \
hospital and several care homes exist even if not specifically \
identified. Adjust confidence accordingly.

ENRICHMENT FIELDS: hospital_count_epz, prison_count_epz, \
care_home_count_epz.

REFERENCE DATA SOURCES: OpenStreetMap amenity=hospital/prison/ \
nursing_home tags, national health ministry facility registers."""

_EP05 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: EP-05 — Concurrent Hazard Impact on Emergency Response \
(Ranking)
NORMATIVE: NS-R-3 §3.59; GS-G-2.1

KEY METRIC: Severity of the most credible concurrent natural hazard \
that could impair evacuation infrastructure during an emergency.

RUBRIC BANDS:
  5 = No credible concurrent hazard affecting emergency infrastructure; \
      stable geology, low seismicity, no flood risk, mild climate
  4 = Minor potential — distant or low-probability concurrent hazard \
      (e.g., low seismicity might cause minor road damage; rare flood \
      event might affect one secondary road)
  3 = Moderate risk — one credible scenario where a natural hazard \
      impairs emergency response capacity (e.g., moderate earthquake \
      damages bridges during radiological emergency; flood blocks one \
      evacuation route)
  2 = Notable risk — multiple concurrent scenarios identified; \
      e.g., seismic event + bridge damage + road blockage; severe \
      weather + flooding + communication disruption
  1 = High risk — site in multi-hazard zone where concurrent events \
      would severely compromise emergency response (e.g., site near \
      active fault + in floodplain + single bridge access)

SYNTHESIS: Cross-reference NH criteria already assessed for this site. \
The question is specifically: "Could a natural hazard occurring \
simultaneously with a nuclear event prevent or severely delay \
evacuation?" Focus on INFRASTRUCTURE VULNERABILITY, not just hazard \
presence.

ENRICHMENT FIELDS: concurrent_hazard_notes.

REFERENCE DATA SOURCES: Synthesize from NH criteria for this site, \
INFORM Risk Index for infrastructure vulnerability, national \
emergency management plans."""

# ===================================================================
# NON-SAFETY SITE CHARACTERISTICS (NS)
# ===================================================================

_NS02 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-02 — Grid Connection Quality (Ranking)
NORMATIVE: EPRI siting criteria; national grid codes

KEY METRIC: Existing grid export capacity (MWe) and distance to \
nearest high-voltage substation (km).

RUBRIC BANDS:
  5 = Existing HV connection ≥ 462 MWe capacity; substation on-site \
      or <1 km; 220+ kV voltage level; grid demonstrated by recent \
      coal plant operation at similar capacity
  4 = Adequate HV connection (220+ kV); substation within 5 km; minor \
      capacity upgrade needed; coal plant had 300–461 MWe capacity
  3 = Partial capacity; 110 kV connection; substation within 10 km; \
      moderate upgrade to 220/400 kV needed; coal plant had 100–299 MWe
  2 = Insufficient capacity; 110 kV connection requiring major upgrade; \
      substation >10 km; coal plant had <100 MWe or grid is weak
  1 = No viable HV connection; new transmission line >20 km needed; \
      or grid infrastructure is degraded/obsolete (common in \
      conflict-affected areas or isolated grids)

COAL-TO-NUCLEAR ADVANTAGE: The existing coal plant's grid connection \
is the strongest indicator. A coal plant that recently operated at \
≥462 MWe has a demonstrably adequate grid connection (score 5). Use \
the plant's installed_capacity_mw as the primary proxy.

ENRICHMENT FIELDS: nearest_substation_km, nearest_hv_line_km, \
grid_export_capacity_mw.

REFERENCE DATA SOURCES: ENTSO-E transmission grid map, national TSO \
grid development plans, OpenStreetMap power data."""

_NS03 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-03 — Transport Access for Construction (Ranking)
NORMATIVE: NuScale logistics requirements; EPRI

KEY METRIC: Number of independent transport modes available (road, rail, \
waterway) combined with proximity.

RUBRIC BANDS:
  5 = Three transport modes available — rail siding on-site + highway \
      access + navigable waterway within 5 km; proven heavy-haul \
      route (coal delivery infrastructure)
  4 = Two transport modes — rail + road access with adequate capacity; \
      or waterway + road; route improvements minor
  3 = Two transport modes available but one requires moderate \
      investment (e.g., rail exists but siding needs rehabilitation; \
      road exists but needs reinforcement for 700-tonne loads)
  2 = Road access only; no rail or waterway within practical distance; \
      road may need significant upgrade for heavy module delivery
  1 = Poor access — single narrow road requiring major upgrade; no \
      rail, no waterway; mountainous or otherwise constrained access

COAL-PLANT ADVANTAGE: Coal plants almost always have rail sidings \
(for coal delivery) and road access. This is a major conversion \
advantage. If the enrichment data shows the plant is/was operational, \
assume rail + road access exists → baseline score 4. Only reduce if \
there is evidence of infrastructure degradation.

ENRICHMENT FIELDS: nearest_rail_km, nearest_highway_km, \
nearest_waterway_km, heavy_haul_capable.

REFERENCE DATA SOURCES: OpenStreetMap railway and highway data, TEN-T \
maps, national railway operator network maps."""

_NS04 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-04 — Site Topography and Land Cover (Ranking)
NORMATIVE: EPRI siting guide

KEY METRIC: Percentage of favourable (flat, industrial, agricultural) \
land cover within the site boundary, combined with terrain slope.

RUBRIC BANDS:
  5 = Flat industrial land (slope <2°); >80% favourable land cover; \
      minimal grading needed; CORINE classes 121/131/132/133/211 \
      (industrial, mining, construction, arable) dominant
  4 = Mostly flat (slope <5°); 60–80% favourable land cover; minor \
      grading and clearing; mixed industrial/agricultural surroundings
  3 = Gentle slopes (5–10°); 40–60% favourable land cover; standard \
      site preparation; some forest clearing or wetland avoidance needed
  2 = Moderate slopes (10–15°) or <40% favourable land cover; \
      significant earthworks for platform creation; unfavourable \
      land cover (dense forest, wetland) requiring clearing
  1 = Steep terrain (>15°) or predominantly unfavourable land cover; \
      extensive earthworks; rock blasting or major land reclamation

COAL-PLANT CONTEXT: Coal plant sites ARE industrial land. The site \
itself scores highly by definition. The question is whether the \
surrounding land needed for the full 72.8 ha footprint is also \
favourable. An existing coal plant on a flat river terrace with \
adjacent agricultural land → score 4–5.

ENRICHMENT FIELDS: dominant_land_class, favourable_land_pct.

REFERENCE DATA SOURCES: CORINE Land Cover 2018, EU-DEM v1.1 / SRTM \
slope analysis."""

_NS05 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-05 — Land Availability (Ranking)
NORMATIVE: NuScale VOYGR-6 footprint (72.8 ha); EPRI

KEY METRIC: Total available land area (ha) — site area plus accessible \
adjacent land.

RUBRIC BANDS:
  5 = Available land ≥ 100 ha; ample expansion room; adjacent land is \
      agricultural or industrial, not constrained
  4 = Available land 72–100 ha; full SMR footprint fits with modest \
      room for laydown; OR smaller site with readily acquirable \
      adjacent agricultural land
  3 = Available land 40–72 ha; site fits nuclear island + essential \
      facilities but laydown area constrained; some adjacent land \
      potentially available but may require negotiation/acquisition
  2 = Available land 14–40 ha; fits nuclear island only; significant \
      constraints on full SMR deployment; adjacent land is urban, \
      protected, or otherwise unavailable
  1 = Available land <14 ha; insufficient even for nuclear island; \
      heavily constrained (urban surroundings, water on multiple \
      sides, steep terrain boundaries)

NOTE: Use the enrichment data buildable_area_ha and \
largest_contiguous_ha as primary inputs. The site_area_ha from the \
site header refers to the existing plant boundary. The buildable_area_ha \
accounts for actual usable space after excluding water bodies, steep \
slopes, and protected areas within the site boundary.

ENRICHMENT FIELDS: buildable_area_ha, largest_contiguous_ha.

REFERENCE DATA SOURCES: Site enrichment data, CORINE Land Cover 2018 \
for adjacent land use analysis."""

_NS06 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-06 — Existing Reusable Infrastructure (Ranking)
NORMATIVE: DOE Coal-to-Nuclear guidance; INL feasibility reports

KEY METRIC: Number and value of reusable coal plant infrastructure \
elements applicable to SMR conversion.

RUBRIC BANDS:
  5 = Comprehensive reuse — switchyard + cooling system + access roads \
      + rail siding + admin/warehouse buildings + water treatment + \
      workforce housing/parking; all in serviceable condition \
      (recently operating plant, <5 years since closure)
  4 = Most infrastructure reusable — switchyard, cooling system, access \
      roads in serviceable condition; some buildings may need \
      refurbishment (5–10 years since closure, or operating plant)
  3 = Partial reuse — switchyard and basic site services (roads, \
      fencing, utilities connections) reusable; cooling system may \
      need replacement; buildings deteriorated (10–20 years since \
      closure)
  2 = Limited reuse — site grading and basic access reusable; \
      electrical and water infrastructure degraded beyond practical \
      reuse (>20 years since closure, or plant demolished)
  1 = Minimal reuse — essentially greenfield site; all infrastructure \
      demolished or deteriorated; only the cleared land itself has value

PRIMARY SIGNAL: Plant status and age. Use these proxies:
  • Operating plant or <5 yr retired → score 4–5
  • Retired 5–15 yr → score 3–4
  • Retired >15 yr → score 2–3
  • Demolished → score 1–2
  • installed_capacity_mw serves as a proxy for infrastructure scale

ENRICHMENT FIELDS: From site header: status, start_year, retired_year, \
installed_capacity_mw.

REFERENCE DATA SOURCES: DOE Coal-to-Nuclear transition studies, INL \
coal conversion feasibility reports, site status from enrichment data."""

_NS07 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-07 — Non-Radiological Environmental Impact (Ranking)
NORMATIVE: EPRI; EU EIA Directive 2011/92/EU

KEY METRIC: Environmental sensitivity of the site and immediate \
surroundings, considering both current conditions and conversion impact.

RUBRIC BANDS:
  5 = Brownfield reuse with minimal additional environmental impact; \
      site is fully industrial; no sensitive receptors within 2 km; \
      conversion reduces pollution compared to coal operation
  4 = Low additional impact; existing disturbed land; minor sensitive \
      receptors at distance (>1 km); net environmental benefit from \
      coal plant replacement
  3 = Moderate impact potential; some sensitive receptors nearby \
      (residential at 500 m–1 km, agricultural land affected); \
      standard EIA mitigations sufficient
  2 = Significant impact concerns — nearby wetlands, recreational \
      water bodies, organic agriculture, or residential areas \
      <500 m from site boundary
  1 = Major environmental concerns — critical habitat adjacent, water \
      resource conflicts (site on drinking water reservoir catchment), \
      or dense residential immediately bordering site

COAL-TO-NUCLEAR ADVANTAGE: Converting a coal plant to nuclear \
ELIMINATES coal combustion emissions (SO₂, NOₓ, particulates, CO₂, \
heavy metals, fly ash). This is a significant net environmental benefit \
that should be noted in the justification, even though this criterion \
focuses on the nuclear plant's own impact.

ENRICHMENT FIELDS: env_impact_notes.

REFERENCE DATA SOURCES: CORINE Land Cover 2018, Natura 2000 network \
viewer, EU EIA Directive project registers."""

_NS08 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-08 — Ecological Sensitivity (Ranking)
NORMATIVE: EU Habitats Directive 92/43/EEC; Natura 2000

KEY METRIC: Percentage of natural/semi-natural land cover within 5 km, \
combined with proximity to designated protected areas.

RUBRIC BANDS:
  5 = Fully industrial/urban surroundings; <10% natural habitat within \
      5 km; no Natura 2000 or other protected areas within 5 km
  4 = Predominantly artificial landscapes; 10–25% natural habitat; \
      nearest Natura 2000 site >3 km from site boundary
  3 = Mixed landscape; 25–45% natural/semi-natural; Natura 2000 site \
      1–3 km from site; site itself is industrial but ecological \
      corridors exist nearby
  2 = Adjacent to Natura 2000 site (<1 km) or within ecological \
      corridor; >45% natural habitat within 5 km; appropriate \
      assessment under Article 6(3) Habitats Directive likely triggered
  1 = Site within or immediately bordering (<200 m) Natura 2000 site; \
      or within Important Bird Area (IBA) flyway; or adjacent to \
      Ramsar wetland; formal HRA screening would likely require \
      compensatory measures

ENRICHMENT FIELDS: ecological_natural_pct, \
ecological_patch_count.

REFERENCE DATA SOURCES: Natura 2000 WFS data (EEA), CDDA protected \
area database, CORINE Land Cover natural classes (CLC 3xx), BirdLife \
IBA database."""

_NS09 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-09 — Socioeconomic Impact (Ranking)
NORMATIVE: SSG-35 §A.41; EPRI

KEY METRIC: Coal plant status (operating/retired/planned closure) \
combined with regional economic dependence on coal.

RUBRIC BANDS:
  5 = Coal-dependent community facing imminent closure (plant closing \
      within 5 years or recently closed); high regional unemployment; \
      community actively seeking industrial replacement; EU Just \
      Transition Fund target region
  4 = Significant local economic benefit; plant operating but coal \
      phase-out planned; skilled workforce at risk; supportive \
      community likely; regional GDP below national average
  3 = Moderate benefit; mixed community sentiment expected; plant is \
      one of several local employers; some transition support available \
      but not critical
  2 = Limited economic benefit; community has diversified economy; \
      nuclear project would face competition for land/labour from \
      other industries; mild opposition possible
  1 = Strong local opposition expected; competing land use priorities \
      (tourism, agriculture, residential development); history of \
      anti-industrial sentiment; or community already prosperous \
      with no need for industrial jobs

PRIMARY SIGNAL: The plant status field. If status="operating" or \
"announced retirement" in a coal-dependent region → score 4–5. \
If status="retired" in a region that has already transitioned → score 2–3.

ENRICHMENT FIELDS: From site header: status, installed_capacity_mw.

REFERENCE DATA SOURCES: Coal plant status from enrichment data, \
Eurostat regional GDP and unemployment (NUTS-3), EU Just Transition \
Fund target regions (Annex D, JTF Regulation), national coal phase-out \
plans and compensation programmes."""

_NS10 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-10 — Workforce Availability (Ranking)
NORMATIVE: EPRI; DOE Coal-to-Nuclear guidance

KEY METRIC: Installed capacity of the coal plant (as proxy for existing \
skilled workforce size) combined with distance to nearest city >50,000 \
(wider labour pool).

RUBRIC BANDS:
  5 = Large coal plant (>500 MWe) with skilled workforce + nearby \
      city >50,000 within 30 km providing additional labour pool; \
      plant skills directly transferable (turbine, electrical, I&C)
  4 = Medium-large plant (200–500 MWe) or large plant with city \
      30–60 km; good workforce availability with some recruitment \
      from wider region needed
  3 = Moderate plant (100–200 MWe) or medium plant with distant \
      city (>60 km); workforce supplementation needed; regional \
      vocational training infrastructure may exist
  2 = Small plant (<100 MWe) in rural area; limited local workforce; \
      significant training and recruitment from outside the region \
      required; nearest city >80 km
  1 = Very small or demolished plant; remote location; major workforce \
      mobilization and temporary accommodation required

WORKFORCE RULE OF THUMB: Coal plants employ roughly 0.5–1.0 workers \
per MWe for operations. A 500 MWe plant has ~250–500 operational staff. \
SMR construction requires 2,000–3,000 peak construction workers, but \
operational staff for VOYGR-6 is ~250 — similar to a large coal plant.

ENRICHMENT FIELDS: From site header: installed_capacity_mw, status. \
From RI-05: nearest_city_50k_km.

REFERENCE DATA SOURCES: Coal plant capacity as workforce proxy, \
Eurostat regional employment statistics (NUTS-3), national labour \
market data."""

_NS11 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-11 — Coal-to-Nuclear Conversion Synergies (Ranking)
NORMATIVE: DOE "Coal-to-Nuclear" study (INL/EXT-21-64462); EPRI

KEY METRIC: Composite assessment of infrastructure condition based on \
plant status, age, and capacity.

RUBRIC BANDS:
  5 = Recently retired (<5 years) or operating plant; all major \
      infrastructure intact and serviceable; switchyard, cooling \
      tower/intake, water treatment, rail, roads, admin buildings \
      all functional; installed capacity ≥ 462 MWe (1:1 replacement)
  4 = Operating or retiring within 5 years; good infrastructure; \
      capacity 200–461 MWe (partial capacity match, expansion possible); \
      strong conversion business case
  3 = Retired 5–15 years; some infrastructure degraded but recoverable \
      with investment; switchyard likely still functional; cooling may \
      need refurbishment; site access intact
  2 = Retired >15 years or plant in poor condition; most infrastructure \
      degraded; limited reusable assets (site grading, basic access); \
      essentially partial brownfield
  1 = Very old, demolished, or abandoned site; >25 years since closure; \
      all infrastructure removed or decayed; conversion synergies \
      limited to land reuse and existing permits/zoning

DECISION LOGIC:
  IF status = "operating" AND capacity >= 462 → score 5
  ELIF status = "operating" AND capacity >= 200 → score 4
  ELIF retired < 5 years AND capacity >= 200 → score 4
  ELIF retired 5–15 years → score 3
  ELIF retired > 15 years → score 2
  ELIF demolished → score 1
  Adjust ±1 for infrastructure condition signals in enrichment data.

ENRICHMENT FIELDS: From site header: status, start_year, retired_year, \
installed_capacity_mw.

REFERENCE DATA SOURCES: DOE/INL coal-to-nuclear feasibility reports, \
site enrichment data for plant status and capacity."""

_NS12 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-12 — Regulatory and Political Environment (Ranking)
NORMATIVE: SSG-35 §A.41; national nuclear legislation

KEY METRIC: Country's nuclear policy status as of 2025.

RUBRIC BANDS:
  5 = Active nuclear programme with operating reactors AND supportive \
      expansion policy; regulatory framework established; recent new-\
      build decisions or active licensing
  4 = Exploring nuclear power with positive government policy; \
      pre-licensing activities underway; or existing programme with \
      expansion plans approved
  3 = Neutral regulatory environment; no nuclear ban; nuclear power \
      under consideration but no formal commitment; regulatory \
      framework would need development
  2 = Restrictive nuclear policy but possible future change; political \
      debate ongoing; moratorium that could be lifted; or country has \
      technical barriers (EU accession requirements, grid limitations)
  1 = Active nuclear ban in constitution or law; strong, stable anti-\
      nuclear political consensus; no foreseeable policy reversal

COUNTRY CLASSIFICATION (as of 2025):
  Score 5: CZ, HU, RO, BG, SK, UA, TR (active programmes/expansion)
  Score 4-5: PL (first NPP approved, Lubiatowo-Kopalino), AM (Metsamor)
  Score 4: BY (Ostrovets operating), HR, RS, SI (exploring)
  Score 3-4: EE, LT, LV (exploring SMR, Baltic context)
  Score 3: BA, MK, AL, ME, XK (neutral, no programme)
  Score 2: MD (geopolitically constrained)
  Score 1: AT (constitutional nuclear ban)

IMPORTANT: Use the country classification above as primary input. The \
score is determined almost entirely by the country, not the site. Only \
adjust if there are sub-national factors (e.g., a site in a staunchly \
anti-nuclear region of an otherwise pro-nuclear country).

TRAINING DATA CAVEAT: Nuclear policy is rapidly evolving in this region \
(EU taxonomy, energy security post-2022). Note "may not reflect \
post-2025 policy changes" if your knowledge is uncertain.

REFERENCE DATA SOURCES: World Nuclear Association country profiles, \
IAEA Country Nuclear Power Profiles (CNPPs), national energy strategies, \
EU taxonomy / national nuclear investment policies."""

_NS13 = SYSTEM_BASE + _RANKING_PREAMBLE + """

CRITERION: NS-13 — Construction Logistics and Laydown Area (Ranking)
NORMATIVE: NuScale construction logistics requirements; EPRI

KEY METRIC: Available flat laydown area (ha) adjacent to or within \
the site, combined with transport access quality.

RUBRIC BANDS:
  5 = Large flat laydown area >20 ha available on or adjacent to site; \
      excellent transport access (rail + road + potential waterway); \
      on-site fabrication yard feasible; no urban encroachment \
      constraining laydown
  4 = Good laydown space (15–20 ha); adequate access via 2+ transport \
      modes; minor site preparation needed; adjacent agricultural \
      land available for temporary laydown
  3 = Moderate laydown space (8–15 ha); some logistics challenges; \
      single primary transport mode for heavy lifts; laydown area \
      constrained on 1–2 sides
  2 = Limited laydown space (<8 ha); constrained by surrounding \
      development or terrain; single transport mode; may require \
      off-site laydown with shuttling
  1 = Very constrained (<4 ha or fragmented); major logistics \
      challenges; inadequate transport access for heavy modules; \
      off-site laydown and complex logistics planning required

COAL-PLANT CONTEXT: Coal plants often have coal stockyards, ash \
disposal areas, and parking that can serve as construction laydown. \
Former coal storage areas are particularly valuable — they are flat, \
compacted, and close to rail access.

ENRICHMENT FIELDS: ns13_laydown_suitable_ha, \
ns13_laydown_largest_patch_ha.

REFERENCE DATA SOURCES: Site area from enrichment data, CORINE Land \
Cover for adjacent land availability."""


RANKING_PROMPTS: dict[str, str] = {
    "NH-01": _NH01, "NH-06": _NH06, "NH-08": _NH08, "NH-09": _NH09,
    "NH-10": _NH10, "NH-11": _NH11, "NH-12": _NH12, "NH-13": _NH13,
    "NH-14": _NH14,
    "HI-01": _HI01, "HI-02": _HI02, "HI-03": _HI03, "HI-04": _HI04,
    "HI-05": _HI05, "HI-06": _HI06, "HI-07": _HI07, "HI-08": _HI08,
    "RI-01": _RI01, "RI-02": _RI02, "RI-03": _RI03, "RI-04": _RI04,
    "RI-05": _RI05, "RI-06": _RI06,
    "EP-02": _EP02, "EP-03": _EP03, "EP-04": _EP04, "EP-05": _EP05,
    "NS-02": _NS02, "NS-03": _NS03, "NS-04": _NS04, "NS-05": _NS05,
    "NS-06": _NS06, "NS-07": _NS07, "NS-08": _NS08, "NS-09": _NS09,
    "NS-10": _NS10, "NS-11": _NS11, "NS-12": _NS12, "NS-13": _NS13,
}
