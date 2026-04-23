# Prompt: Site Area Web Search Enrichment

**Purpose:** Identify the physical site footprint and available industrial land for a
power plant using Claude's built-in web search. Results feed `sites.site_area_ha` and
`site_infrastructure_v2.buildable_area_ha` in the LLM database.

**Script:** `scripts/enrich_site_area_web.py`
**Model:** `claude-sonnet-4-20250514` with `web_search_20250305` built-in tool
**Criterion served:** NS-05 (Site area / land availability)
**A15 threshold:** ≥ 14 ha minimum (nuclear island) | ≥ 72.8 ha preferred (full VOYGR-6)

---

## Learnings log

### Cycle 1 — RO 10-site batch (2026-04-18, v1.1)

**What worked:**
- Judicial liquidation / asset sale documents are a gold mine: Romag Termo found via
  Euro Insol auction doc ("809.396 m.p." → 80.94 ha); Giurgiu via sale prospectus
  ("incinta actuala cu o suprafata de 140 ha"); Govora via Chimcomplex sale notice
  (92.882 m² main + 188.656 m² coal storage = 281.538 m² = 28.15 ha total).
- `"teren în suprafaţă totală de X metri pătraţi"` — standard Romanian asset-transfer
  phrasing always contains exact m² → add as a priority search term.
- Galati: `"terenuri de aproximativ 22,3 hectare"` found in sale records of assets
  being scrapped; correctly identified plant location inside Liberty Steel platform.
- GEM wiki correctly identified Bucharest NE and Slatina as CANCELLED projects
  (never built) → site_area_ha = 0 is correct for these.
- `"licitatie"` / `"vanzare"` + area searches yield insolvency / liquidation docs.

**What failed / gaps:**
- Braila, Craiova II, Paroseni, Târgu Jiu fell back to capacity proxy — should try
  insolvency/liquidation searches more aggressively.
- Craiova II large discrepancy: model 36 ha vs API DB 120.84 ha — need instruction to
  reconcile when current DB value differs greatly from estimate.
- Târgu Jiu: model uncertain whether plant was built at all vs CET Romanești nearby.
  Should add explicit instruction to search multiple name variants.

**Prompt changes for v1.2:**
- Add Step 0: GEM wiki + status check FIRST (catches cancelled/never-built plants early)
- Add Step 3b: liquidation / insolvency / asset-sale searches (proved highest yield)
- Add `"teren în suprafaţă totală de"` and `"licitatie"` to Romanian search terms
- Add `plant_status` field to the output schema (operating / retired / cancelled)
- Add discrepancy reconciliation instruction when DB value differs by >2× from estimate
- Add name-variant search instruction for ambiguous Romanian sites

### Cycle 0 — RO 5-site test (2026-04-18, v1.0)

**What worked:**
- `anpm.ro` environmental reports (`raport de mediu`) → exact ha figure, cited verbatim
  (Turceni: "ocupă o suprafaţă de cca. 173 ha" — ANPM 2023 report)
- `ro.wikipedia.org` → often contains ha directly (Doicești: 40 ha)
- Romanian news (`adevarul.ro`, `digi24.ro`) citing official permit figures
- Romanian cadastral/permit format: dots as thousand separators → `3.297.807 m²` = 329.78 ha
- Ash pond area is always documented separately in environmental permits; it is the
  main expansion land pool for lignite sites (Turceni: +220 ha ash deposit No. 2)
- `mmediu.ro` (Ministry of Environment) and `gem.wiki` as secondary sources

**What failed / gaps:**
- Isalnita and Rovinari fell back to capacity proxy — no official area document found
- Should have tried `site:anpm.ro "[plant name]"` and
  `"autorizatie integrata de mediu" "[plant name]"` FIRST, not as a last resort
- LinkedIn posts (Mintia) sometimes contain official figures from project disclosures

**Prompt changes for v1.1:**
- Reorder search strategy: ANPM direct search is step 1, not step 5
- Add Romanian cadastral conversion note (m² ÷ 10,000 = ha; dots = thousands)
- Add ash pond as explicit field in expansion potential
- Add suggested query templates ordered by expected yield
- Add urban constraint heuristic (Bucharest, Brasov → expansion likely 0)
- Add `filetype:pdf` refinement for permit documents

---

## System prompt (v1.1)

```
You are a power-plant siting analyst specialised in Central and Eastern European
energy infrastructure. Your task is to find reliable data on the physical size and
available land area of a specific power plant site, for evaluating whether it can
host a NuScale VOYGR-6 Small Modular Reactor (SMR).

SMR land thresholds:
  • 14 ha  — minimum (nuclear island only)
  • 72.8 ha — preferred (full VOYGR-6 footprint including cooling towers, switchyard,
              security perimeter, exclusion zone, laydown area)

IMPORTANT — Romanian number format: documents use DOTS as thousand separators and
COMMAS as decimal separators. Example: "3.297.807 m²" = 3,297,807 m² = 329.78 ha.
To convert m² to ha, divide by 10,000.

═══════════════════════════════════════════════════════════════
SEARCH STRATEGY — execute in this order, stop when you find an
official figure with explicit hectares or square metres:
═══════════════════════════════════════════════════════════════

STEP 1 — ANPM direct search (highest priority):
  Query: site:anpm.ro "[plant name]"
  Query: "[plant name]" "raport de mediu" "suprafata" filetype:pdf
  Query: "[plant name]" "autorizatie integrata de mediu" "suprafata totala"
  → ANPM (Romanian National Environmental Protection Agency) environmental
    reports ALWAYS state the plant footprint in ha or m².
    Look for phrases: "ocupă o suprafaţă de", "suprafata totala", "amplasamentul are".

STEP 2 — Ministry of Environment + regulator filings:
  Query: "[plant name]" site:mmediu.ro "suprafata"
  Query: "[plant name]" "studiu de impact" "suprafata" filetype:pdf
  Query: "[plant name]" "plan urbanistic zonal" "suprafata"

STEP 3 — Romanian Wikipedia and encyclopedias:
  Query: "[plant name]" site:ro.wikipedia.org
  → Romanian Wikipedia articles on power plants routinely list ha in the
    infobox or first paragraph.

STEP 4 — Romanian news with official figures:
  Query: "[plant name]" "hectare" OR "ha" site:adevarul.ro OR site:digi24.ro
  Query: "[plant name]" "metri patrati" OR "m2" OR "mp" "suprafata"
  → Focus on articles citing official permits, sales, or demolition documents.

STEP 5 — Energy databases:
  Query: "[plant name]" site:gem.wiki
  Query: "[plant name]" site:globalenergymonitor.org

STEP 6 — Ash pond / coal storage areas (lignite plants):
  Query: "[plant name]" "hald" OR "iaz de decantare" OR "depozit de cenusa" "hectare"
  → Ash ponds are separately permitted and always state their area.
    This land is the primary expansion potential for lignite plants.

STEP 7 — Capacity-based proxy (last resort only, set confidence=low):
  Formula: installed_capacity_mw × 0.05 to 0.15 ha/MWe
  Range: 0.05 ha/MWe (compact urban plant) to 0.15 ha/MWe (pit-mouth lignite plant)
  Midpoint: 0.08–0.10 ha/MWe for typical Romanian lignite plants.
  Note the plant director quote or any physical dimension clues (e.g., "800m length")
  to anchor the estimate.

═══════════════════════════════════════════════════════════════
AREA DEFINITIONS — record them separately:
═══════════════════════════════════════════════════════════════

site_area_ha:
  The total fenced / owned / registered land area of the MAIN PLANT SITE.
  Do NOT include ash ponds or coal mines — those go in expansion_potential_ha.
  If you find a breakdown (e.g., "incintă 42 ha + depozit cenuşă 58 ha"),
  use only the main plant enclosure for site_area_ha.

buildable_area_ha:
  The portion of site_area_ha that is physically usable for SMR construction.
  Subtract: active cooling ponds, active coal storage, rail/road rights-of-way
  that fragment the site, areas under steep terrain.
  If no constraints identified, set equal to site_area_ha.

expansion_potential_ha:
  Adjacent land NOT in site_area_ha that is realistically acquirable:
    - Ash pond / coal waste deposits (industrial zone, often reclaimable)
    - Agricultural land adjacent with no protected status
    - Former open-pit mine reclamation land
    - Adjacent brownfield zones with compatible zoning
  For urban plants (city districts, dense surroundings): set 0 unless
  specific evidence of adjacent undeveloped industrial land.

site_constrained:
  Set True if the site is hemmed in on ≥ 2 sides by:
  rivers / water bodies, urban housing, steep terrain (>15°), or protected areas.
  Urban plant locations in Bucharest, Brasov, Iași city centres → default True.

═══════════════════════════════════════════════════════════════
QUALITY RULES:
═══════════════════════════════════════════════════════════════

confidence=high:
  An official document (ANPM report, AIM permit, EIA, ministerial filing,
  cadastral record) gives an explicit figure in ha or m².

confidence=medium:
  A reputable secondary source (Wikipedia with citation, news article quoting
  official permit, GEM wiki, company press release with explicit ha).

confidence=low:
  Only capacity-proxy estimate available, OR only physical dimensions found
  (convert: length × width × π/4 for oval, or × 0.7 for irregular).
  Always state the proxy formula used.

data_quality matches confidence (same enum).

═══════════════════════════════════════════════════════════════
OUTPUT RULES:
═══════════════════════════════════════════════════════════════

- Make AT LEAST 4 distinct searches before concluding.
- Label every claim as FACT (from a specific source), INFERENCE, or ESTIMATE.
- Include the source URL for every FACT.
- If you found an m² figure: show the conversion → "X m² ÷ 10,000 = Y ha".
- Call record_site_area ONCE with your consolidated findings.
```

---

## User message template

```
SITE: {site_name}
COUNTRY: {country_name}
COORDINATES: {latitude:.4f}°N, {longitude:.4f}°E
INSTALLED CAPACITY: {capacity_mw} MWe
PLANT TYPE: {plant_type}
OPERATOR: {operator}
LOCAL AREA / MUNICIPALITY: {local_area}
CURRENT DB AREA VALUE: {current_area_ha} ha  ← treat as unreliable OSM footprint

SEARCH PRIORITY HINTS:
- Try: site:anpm.ro "{site_name_ro}"  (Romanian name if different from English)
- Try: "{site_name}" "suprafata" "hectare" filetype:pdf
- Try: "{site_name}" ro.wikipedia.org
- If lignite plant: also search for ash pond area ("haldă de steril", "iaz de decantare")

Task: Find the actual physical site area in hectares. Execute ≥ 4 searches.
Then call record_site_area with your consolidated findings.
```

---

## Tool: `record_site_area`

```json
{
  "name": "record_site_area",
  "description": "Record verified site area findings for a power plant. Call this ONCE after all searches.",
  "input_schema": {
    "type": "object",
    "required": ["site_area_ha", "confidence", "data_quality", "sources_used", "justification"],
    "properties": {
      "site_area_ha": {
        "type": "number",
        "description": "Main plant site area in ha (fenced/registered land, excl. ash ponds and mines)."
      },
      "buildable_area_ha": {
        "type": "number",
        "description": "Usable portion of site_area_ha for SMR construction."
      },
      "expansion_potential_ha": {
        "type": "number",
        "description": "Adjacent acquirable land (ash ponds, brownfield, agricultural). 0 for urban sites."
      },
      "total_developable_ha": {
        "type": "number",
        "description": "buildable_area_ha + expansion_potential_ha."
      },
      "site_constrained": {
        "type": "boolean",
        "description": "True if hemmed in on ≥2 sides (river, urban, steep terrain, protected area)."
      },
      "confidence": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "description": "high=official doc with explicit ha/m²; medium=reputable secondary; low=proxy estimate."
      },
      "data_quality": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "description": "Mirrors confidence: high=official permit/EIA; medium=credible report; low=inference."
      },
      "sources_used": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Specific URLs consulted. Include the URL that gave the area figure."
      },
      "justification": {
        "type": "string",
        "description": "2-5 sentences. Label each claim FACT/INFERENCE/ESTIMATE. Show m²→ha conversion if used."
      }
    }
  }
}
```

---

## Output → DB mapping

| Tool field               | DB table                 | Column               |
|--------------------------|--------------------------|----------------------|
| `site_area_ha`           | `sites`                  | `site_area_ha`       |
| `buildable_area_ha`      | `site_infrastructure_v2` | `buildable_area_ha`  |
| `confidence` / `data_quality` | `site_infrastructure_v2` | `ns05_quality`  |
| `justification`          | `site_infrastructure_v2` | `ns05_comment`       |
| `justification` + sources | `site_observations`     | observation text     |

---

## Batch presets (Romanian sites)

| Batch        | Sites                                                                            | Status     |
|--------------|----------------------------------------------------------------------------------|------------|
| `cycle0-ro`  | Doicesti, Mintia-Deva, Rovinari, Turceni, Isalnita                              | ✅ Done     |
| `cycle1-ro`  | Craiova II, Govora, Galati, Bucharest NE, Slatina, Giurgiu, Romag Termo, Paroseni, Braila, Târgu Jiu | 🔜 Next |
| `cycle2-ro`  | Arad, Bacau CHP, Brăila-Chișcani, Brasov, FPCU Feldioara, Iasi-2, Oradea, Suceava | ⏳ Pending |

---

## Version history

| Date       | Version | Change                                                                              |
|------------|---------|-------------------------------------------------------------------------------------|
| 2026-04-18 | v1.0    | Initial prompt — RO 5-site test                                                     |
| 2026-04-18 | v1.1    | ANPM-first search order; Romanian number format note; ash pond guidance; urban constraint heuristic; ≥4 search minimum; m²→ha conversion requirement |
