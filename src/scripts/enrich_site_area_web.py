#!/usr/bin/env python
# man_hours: 4.0
"""Web-search enrichment for power-plant site area (NS-05 / A15 data feed).

Uses Claude's built-in web_search_20250305 tool to find the physical footprint
and available land area for each target site, then writes the result to the LLM
database.

Writes to:
  sites.site_area_ha
  site_infrastructure_v2.buildable_area_ha
  site_infrastructure_v2.ns05_quality
  site_infrastructure_v2.ns05_comment
  site_observations (justification + source URLs)

Usage:
    # Dry run (shows plan, no API calls, no DB writes):
    python scripts/enrich_site_area_web.py --dry-run

    # Test on the default 5 Romanian plants (requires explicit go-ahead):
    python scripts/enrich_site_area_web.py

    # All Romanian plants:
    python scripts/enrich_site_area_web.py --country RO

    # Specific sites by name:
    python scripts/enrich_site_area_web.py --sites "Rovinari power station" "Turceni power station"

    # Re-run even if data already exists:
    python scripts/enrich_site_area_web.py --force-rerun

Prompt: prompts/site_area_web_search.md
Consent: Required before each live run — see live-api-safety.mdc rule.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import anthropic
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
MAX_TURNS = 8          # max conversation turns per site (web search may require multi-turn)
INTER_SITE_DELAY_S = 4.0   # polite pause between sites

PROMPT_VERSION = "v1.3-2026-04-18"
SOURCE_NAME = "web_search:claude-sonnet-4"
SOURCE_URL = "https://api.anthropic.com"
CRITERION_ID = "NS-05"

# Named batch presets — run with: --batch cycle1-ro
BATCH_PRESETS: dict[str, list[str]] = {
    "cycle0-ro": [
        "Doicesti power station",
        "Mintia-Deva power station",
        "Rovinari power station",
        "Turceni power station",
        "Isalnita power station",
    ],
    "cycle1-ro": [
        "Craiova II power station",
        "Govora power station",
        "Galati Power Station",
        "Bucharest North East power station",
        "Slatina power station",
        "Giurgiu power station",
        "Romag Termo power station",
        "Paroseni power station",
        "Braila power station",
        "Târgu Jiu Thermal Plant",
    ],
    "cycle2-ro": [
        "Arad power station",
        "Bacau CHP power station",
        "Brăila-Chișcani Thermal Power Plant",
        "Brasov power station",
        "FPCU Feldioara",
        "Iasi-2 power station",
        "Oradea power station",
        "Suceava power station",
    ],
}

# Default batch if no --batch / --sites / --country supplied
DEFAULT_BATCH = "cycle1-ro"

# Country-specific search guidance: local terms + key databases
COUNTRY_HINTS: dict[str, dict[str, str]] = {
    "AL": {
        "language": "Albanian",
        "area_terms": "hektarë (ha), sipërfaqe (area/surface), terreno (land)",
        "databases": "AKBN (Albanian National Energy Regulator, akbn.gov.al), METE (Ministry of Energy), Albania Environment Agency (akm.gov.al)",
        "query_hints": 'Try: "[site name]" site:akbn.gov.al | "[site name]" "hektarë" | "Porto Romano" KESH (Albanian Power Corp)',
    },
    "AT": {
        "language": "German",
        "area_terms": "Hektar (ha), Fläche (area/surface), Gelände (site/grounds)",
        "databases": "Umweltbundesamt (umweltbundesamt.at), E-Control Austria (e-control.at), Landesumweltbehörde, Austrian Energy Agency (AEA), VERBUND annual reports",
        "query_hints": 'Try: "[site name]" site:umweltbundesamt.at "Fläche" | "[site name]" "Hektar" | "[site name]" Umweltverträglichkeitsprüfung (UVP = EIA)',
    },
    "BA": {
        "language": "Bosnian/Serbian/Croatian",
        "area_terms": "hektara (ha), površina (surface area), zemljište (land/ground)",
        "databases": "FERK (Federal Energy Regulator, ferk.ba), DERK (State Electricity Regulatory Commission, derk.ba), FHMZ (federal environmental), REC Bosnia",
        "query_hints": 'Try: "[site name]" site:ferk.ba "površina" | "[site name]" "hektara" | "[operator name]" godišnji izvještaj (annual report) "hektara"',
    },
    "BG": {
        "language": "Bulgarian (Cyrillic)",
        "area_terms": "хектара/хектари (ha), площ/площадка (area/site), терен (land), декар (dekar=0.1ha)",
        "databases": "РИОСВ (Regional Inspectorate for Environment and Water, riosv-*.org), МОСВ (Ministry of Environment, moew.government.bg), ЕСО (ESO Bulgaria), КЕВР (energy regulator, kevr.bg), NEK EAD",
        "query_hints": 'Try: "[site name]" site:moew.government.bg "хектара" | "[site name in Bulgarian]" РИОСВ "площ" | "[site name]" "Комплексно разрешително" (integrated permit)',
    },
    "BY": {
        "language": "Belarusian/Russian (Cyrillic)",
        "area_terms": "гектар (ha), площадь/плошча (area), территория (territory), земельный участок (land plot)",
        "databases": "Belenergo (belenergo.by), Ministry of Natural Resources Belarus (minpriroda.gov.by), Gosproekt",
        "query_hints": 'Try: "[site name]" "площадь" "гектар" | "[site name]" Белэнерго "га" | "[site name]" "земельный участок"',
    },
    "CZ": {
        "language": "Czech",
        "area_terms": "hektarů/hektary (ha), rozloha (expanse/area), plocha (surface), pozemek (land plot)",
        "databases": "ČHMÚ / CENIA (Czech Environmental Information Agency, cenia.cz), ERO (Energy Regulatory Office, eru.cz), ČEZ (CEZ Group, cez.cz) annual reports, IPPC portal (ippc.cz), EIA portal (eia.cenia.cz)",
        "query_hints": 'Try: "[site name]" site:eia.cenia.cz "plocha" | "[site name]" site:cez.cz "hektarů" | "[site name]" "integrované povolení" "plocha" | "[site name]" ČHMÚ rozloha',
    },
    "HR": {
        "language": "Croatian",
        "area_terms": "hektara (ha), površina (surface area), zemljište (land), čestica (plot)",
        "databases": "HAOP (Croatian Agency for Environment and Nature, haop.hr), MINGOR (Ministry of Economy), HEP (Croatian utility, hep.hr), AZTN",
        "query_hints": 'Try: "[site name]" site:haop.hr "površina" | "[site name]" site:hep.hr "hektara" | "[site name]" "studija utjecaja na okoliš" (EIA) "površina"',
    },
    "HU": {
        "language": "Hungarian",
        "area_terms": "hektár (ha), terület (area), telek (plot/lot), ingatlan (property)",
        "databases": "MEKH (Hungarian Energy and Public Utility Regulatory Authority, mekh.hu), OKFK (National Inspectorate for Environment), MVM (Magyar VillamosMűvek, mvm.hu), OMSZ",
        "query_hints": 'Try: "[site name]" site:mvm.hu "hektár" | "[site name]" "környezeti hatásvizsgálat" (EIA) "terület" | "[site name]" MFGI OR MBFSZ "hektár"',
    },
    "LV": {
        "language": "Latvian",
        "area_terms": "hektārs (ha), platība (area/surface), zeme (land), zemesgabals (land parcel)",
        "databases": "LVĢMC (Latvian Environment, Geology & Meteorology Centre, lvgmc.lv), SPRK (Public Utilities Commission, sprk.gov.lv), Latvenergo (latvenergo.lv)",
        "query_hints": 'Try: "[site name]" site:latvenergo.lv "platība" | "[site name]" "hektārs" | Kurzeme power plant territory area',
    },
    "MD": {
        "language": "Romanian/Moldovan (same as RO)",
        "area_terms": "hectare (ha), suprafaţă (surface), teren (land) — same as Romanian",
        "databases": "ANRE Moldova (anre.md), Ministry of Environment Moldova, Energocom (energocom.md), Moldelectrica",
        "query_hints": 'Try: "[site name]" site:anre.md "suprafata" | "Cuciurgan" OR "Kuchurgan" "hectare" | "[site name]" "autorizatie de mediu" Moldova',
    },
    "ME": {
        "language": "Montenegrin/Serbian",
        "area_terms": "hektara (ha), površina (surface area), zemljište (land)",
        "databases": "EPCG (Elektroprivreda Crne Gore, epcg.com), RAE (Regulatory Agency for Energy, rae.co.me), EPA Montenegro, Ministry of Economy Montenegro",
        "query_hints": 'Try: "[site name]" site:epcg.com "površina" | "[site name]" "hektara" | EPCG godišnji izvještaj (annual report) "[site name]"',
    },
    "MK": {
        "language": "Macedonian (Cyrillic) / Albanian",
        "area_terms": "хектари/хектар (ha), површина (area), земјиште (land) / hektarë (Albanian)",
        "databases": "MOEPP (Ministry of Environment and Physical Planning, moepp.gov.mk), ERC (Energy Regulatory Commission, erc.org.mk), ESM (electricity utility, esm.com.mk)",
        "query_hints": 'Try: "[site name]" site:esm.com.mk "хектари" | "Битола" OR "Bitola" "хектари" | ЕЛЕМ (ELEM utility) "површина"',
    },
    "PL": {
        "language": "Polish",
        "area_terms": "hektarów/hektary (ha), powierzchnia (surface area), teren/tereny (land), działka (plot)",
        "databases": "GDOŚ (General Directorate for Environmental Protection, gdos.gov.pl), URE (Energy Regulatory Office, ure.gov.pl), PGE (pge.pl), Tauron (tauron.pl), Enea (enea.pl) annual reports, BIP (Public Information Bulletin), RDOŚ (regional environmental)",
        "query_hints": 'Try: "[site name]" site:gdos.gov.pl "powierzchnia" | "[site name]" "pozwolenie zintegrowane" (integrated permit) "powierzchnia" | "[site name]" BIP "hektarów" | "[operator]" raport roczny (annual report) "hektarów"',
    },
    "RS": {
        "language": "Serbian (Cyrillic and Latin)",
        "area_terms": "hektara (ha), površina (surface area), земљиште/zemljište (land), парцела/parcela (plot)",
        "databases": "RATEL (Energy Agency, ratel.rs), Agencija za zaštitu životne sredine (environment, sepa.gov.rs), EPS (Elektroprivreda Srbije, eps.rs), TENT (Termoelektrane Nikola Tesla)",
        "query_hints": 'Try: "[site name]" site:eps.rs "hektara" OR "ha" | "[site name]" "integralna dozvola" (integrated permit) "površina" | "TENT" OR "Kolubara" izveštaj "površina"',
    },
    "SI": {
        "language": "Slovenian",
        "area_terms": "hektarjev/hektarov (ha), površina (surface area), parcela (plot), nepremičnina (property)",
        "databases": "ARSO (Slovenian Environment Agency, arso.gov.si), AGEN-RS (Energy Agency, agen-rs.si), HSE (Holding Slovenske elektrarne, hse.si), TEŠ (Šoštanj thermal plant)",
        "query_hints": 'Try: "[site name]" site:arso.gov.si "površina" | "[site name]" site:hse.si "hektarjev" | "Šoštanj" OR "Sostanj" "hektarjev" "okoljevarstveno dovoljenje" (environmental permit)',
    },
    "SK": {
        "language": "Slovak",
        "area_terms": "hektárov/hektáre (ha), plocha (surface area), pozemok (land plot), parcela (parcel)",
        "databases": "SAŽP (Slovak Environmental Agency, sazp.sk), URSO (Regulatory Office, urso.gov.sk), SE (Slovenské elektrárne, seas.sk), SPP, IPKZ portal (integrated permits)",
        "query_hints": 'Try: "[site name]" site:sazp.sk "plocha" | "[site name]" "integrované povolenie" "plocha" | "[site name]" site:urso.gov.sk | Slovak power plant "[name]" hektárov',
    },
    "UA": {
        "language": "Ukrainian (Cyrillic)",
        "area_terms": "гектар/га (ha), площа (area), ділянка (plot/parcel), земля (land)",
        "databases": "НКРЕКП (Energy regulator, nerc.gov.ua), Міністерство енергетики (Ministry of Energy, mev.gov.ua), ДТЕК (DTEK energy, dtek.com), Центрально-Диспетчерська служба, Ukrhydroenergo",
        "query_hints": 'Try: "[site name]" "площа" "гектар" OR "га" | "[site name in Ukrainian]" ДТЕК OR Energoatom "земельна ділянка" | "[site name]" "екологічний паспорт" (ecological passport) "площа"',
    },
    "XK": {
        "language": "Albanian / Serbian",
        "area_terms": "hektarë (Albanian ha), sipërfaqe (area), sipërfaqja totale | hektara (Serbian ha), površina (area)",
        "databases": "ZRRE (Energy Regulatory Office Kosovo, zrre.org), KEK (Kosovo Energy Corp, kek-energy.com), Ministry of Economy Kosovo, Kosovo Environment Agency",
        "query_hints": 'Try: "[site name]" site:kek-energy.com "hektarë" | "Kosovo A" OR "Kosovo B" "sipërfaqe" | KEK annual report "hektarë" | Kosovo power plant area hectares',
    },
}

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a power-plant siting analyst specialised in Central and Eastern European
energy infrastructure. Your task is to find reliable data on the physical site area
and available land of a power plant, to evaluate whether it can host a NuScale
VOYGR-6 SMR (minimum 14 ha; preferred 72.8 ha full footprint).

IMPORTANT — Romanian number format: documents use DOTS as thousand separators and
COMMAS as decimals. "3.297.807 m²" = 3,297,807 m² = 329.78 ha (divide by 10,000).
Also written as "m.p." (metri pătrați) in Romanian legal/auction documents.

═══ SEARCH STRATEGY — execute in this order ═══════════════════════════════════

STEP 0 — Plant status check (ALWAYS first — catches cancelled projects):
  "[plant name]" site:gem.wiki
  "[plant name]" site:globalenergymonitor.org
  → Check if the plant is: operating / retired / cancelled / never built.
    If CANCELLED or NEVER BUILT: set site_area_ha=0, plant_status="cancelled",
    confidence="high", and stop further area searches.
  → Also check for name variants (e.g., "CET [city]", "Termocentrale [city]").

STEP 1 — ANPM direct (highest yield for operating/retired plants):
  site:anpm.ro "[plant name]"
  "[plant name]" "raport de mediu" "suprafata" filetype:pdf
  "[plant name]" "autorizatie integrata de mediu" "suprafata totala"
  → ANPM environmental reports ALWAYS state footprint in ha or m².
    Look for: "ocupă o suprafaţă de", "suprafata totala", "amplasamentul are".

STEP 2 — Insolvency / liquidation / asset-sale documents (very high yield):
  "[plant name]" "licitatie" OR "vanzare" "teren" "m.p." OR "mp" OR "m2"
  "[plant name]" "teren în suprafaţă totală de" "metri pătraţi"
  "[plant name]" "masa credala" OR "lichidare judiciara" "teren"
  "[plant name]" site:publicitate-imobiliara.ro OR site:anaf.ro
  → Romanian insolvency/sale documents always list exact land area in m.p.
    Examples: "809.396 m.p.", "teren în suprafaţă totală de 92.882 metri pătraţi".
    Convert: X m.p. ÷ 10,000 = Y ha.

STEP 3 — Ministry of Environment + national regulator:
  "[plant name]" site:mmediu.ro "suprafata"
  "[plant name]" "studiu de impact" "suprafata" filetype:pdf

STEP 4 — Romanian Wikipedia:
  "[plant name]" site:ro.wikipedia.org
  → Romanian Wikipedia plant articles routinely list ha in infobox or opening.

STEP 5 — Romanian news with official figures:
  "[plant name]" "hectare" OR "ha" site:adevarul.ro OR site:digi24.ro
  "[plant name]" "metri patrati" OR "m2" OR "mp" "suprafata"
  → Focus on articles citing official permits, insolvency auctions, or sales.

STEP 6 — Ash pond / coal waste areas (lignite plants only):
  "[plant name]" "halda" OR "iaz de decantare" OR "depozit cenusa" "hectare"
  → Ash ponds are separately permitted and always state their area.
    This land is the PRIMARY expansion pool for lignite plants.

STEP 7 — Capacity proxy (last resort, confidence=low):
  Formula: installed_mw × 0.05–0.15 ha/MWe
  Midpoint for Romanian lignite: 0.08–0.10 ha/MWe.
  Anchor with any dimension clues found (e.g., plant is "800 m long").

═══ DISCREPANCY RECONCILIATION ════════════════════════════════════════════════

If the CURRENT DB AREA VALUE provided by the user is >2× larger or smaller than
your estimate, you MUST explicitly address this in the justification:
  - Explain what the DB value likely represents (OSM building polygon vs. full land)
  - State which figure you trust more and why
  - If DB value comes from an OSM building footprint, it is typically much smaller
    than the actual registered land area

═══ AREA DEFINITIONS ══════════════════════════════════════════════════════════

plant_status: "operating" | "retired" | "cancelled" | "unknown"
  cancelled = project was never built, no physical infrastructure at the site.

site_area_ha: Total fenced/registered area of the MAIN PLANT SITE only.
  If a breakdown is found (enclosure X ha + ash pond Y ha), use ONLY the
  main enclosure for site_area_ha; ash pond goes in expansion_potential_ha.
  Set 0 if the plant was never built (cancelled).

buildable_area_ha: Usable fraction of site_area_ha for SMR construction.
  Deduct: active cooling ponds, active rail sidings, >15° terrain.
  If no constraints identified → set equal to site_area_ha.

expansion_potential_ha: Adjacent acquirable land NOT in site_area_ha:
  ash ponds, mine reclamation land, adjacent agricultural/brownfield zones.
  For urban plants or cancelled projects → 0.

site_constrained: True if hemmed in on ≥ 2 sides by river, urban fabric,
  steep terrain, or protected area. Urban plants and cancelled projects → True.

═══ QUALITY RULES ══════════════════════════════════════════════════════════════

confidence=high:  official doc (ANPM, AIM permit, EIA, cadastral, insolvency
                  auction) with explicit ha or m² figure; or confirmed cancelled.
confidence=medium: reputable secondary source (Wikipedia with citation,
                   news citing official permit, GEM, company press release).
confidence=low:   only capacity proxy or physical dimension estimate.

═══ OUTPUT RULES ════════════════════════════════════════════════════════════════

- Execute AT LEAST 4 distinct searches (unless plant is cancelled — stop after STEP 0).
- Label every claim: FACT (with URL) | INFERENCE | ESTIMATE.
- If m² or m.p. figure found: show conversion "X ÷ 10,000 = Y ha".
- If DB value differs greatly from your estimate: reconcile explicitly.
- Call record_site_area ONCE with consolidated findings."""


def _user_message(site: dict[str, Any]) -> str:
    capacity = f"{site['installed_capacity_mw']:.0f}" if site.get("installed_capacity_mw") else "unknown"
    current = f"{site['site_area_ha']:.2f}" if site.get("site_area_ha") else "not set"
    name = site["name"]
    country_code = site.get("country_code", "")

    # Strip English suffixes to get a cleaner local search name
    local_name = (
        name.replace(" power station", "")
            .replace(" Power Station", "")
            .replace(" Thermal Plant", "")
            .replace(" Thermal Power Plant", "")
            .replace(" Thermal Power Project", "")
            .replace(" Power Project", "")
            .replace(" CHP power station", "")
            .replace(" power project", "")
            .strip()
    )

    # Country-specific guidance block
    hints = COUNTRY_HINTS.get(country_code, {})
    if hints:
        country_block = (
            f"COUNTRY-SPECIFIC SEARCH GUIDANCE:\n"
            f"- Language: {hints.get('language','')}\n"
            f"- Local area terms: {hints.get('area_terms','')}\n"
            f"- Key databases: {hints.get('databases','')}\n"
            f"- Priority queries: {hints.get('query_hints','')}\n"
        )
    else:
        country_block = ""

    return (
        f"SITE: {name}\n"
        f"COUNTRY: {site['country_name']} ({country_code})\n"
        f"COORDINATES: {site['latitude']:.4f}°N, {site['longitude']:.4f}°E\n"
        f"INSTALLED CAPACITY: {capacity} MWe\n"
        f"PLANT TYPE: {site.get('plant_type', 'coal/thermal')}\n"
        f"OPERATOR: {site.get('owner_operator', 'unknown')}\n"
        f"LOCAL AREA / MUNICIPALITY: {site.get('local_area') or 'not recorded'}\n"
        f"CURRENT DB AREA VALUE: {current} ha  ← treat as unreliable OSM footprint\n\n"
        f"{country_block}\n"
        f"Task: Find the actual physical site area in hectares. "
        f"Execute ≥ 4 searches (local language + English). "
        f"Show m²→ha conversion if applicable. "
        f"Then call record_site_area with your consolidated findings."
    )


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

RECORD_TOOL: dict[str, Any] = {
    "name": "record_site_area",
    "description": (
        "Record verified site area findings for a power plant. "
        "Call this ONCE after completing all your web searches."
    ),
    "input_schema": {
        "type": "object",
        "required": ["plant_status", "site_area_ha", "confidence", "data_quality", "sources_used", "justification"],
        "properties": {
            "plant_status": {
                "type": "string",
                "enum": ["operating", "retired", "cancelled", "unknown"],
                "description": (
                    "Current operational status of the plant. "
                    "cancelled = project was never built. "
                    "retired = built but now decommissioned. "
                    "operating = currently generating power."
                ),
            },
            "site_area_ha": {
                "type": "number",
                "description": (
                    "Best estimate of total plant site area in hectares. "
                    "Use the total owned/fenced land, not just the building footprint."
                ),
            },
            "buildable_area_ha": {
                "type": "number",
                "description": (
                    "Available industrial land suitable for SMR construction "
                    "(may equal site_area_ha if no constraints). "
                    "Exclude flooded areas or major physical obstacles."
                ),
            },
            "expansion_potential_ha": {
                "type": "number",
                "description": (
                    "Adjacent land that COULD be acquired for SMR siting "
                    "(mine reclamation land, agricultural parcels, brownfield). "
                    "Set 0 if none identified."
                ),
            },
            "total_developable_ha": {
                "type": "number",
                "description": "buildable_area_ha + expansion_potential_ha — realistic upper bound.",
            },
            "site_constrained": {
                "type": "boolean",
                "description": (
                    "True if site is hemmed in on multiple sides with low expansion potential."
                ),
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": (
                    "high=official source with explicit ha figure; "
                    "medium=credible secondary source or satellite estimate; "
                    "low=capacity-based proxy or no specific source found."
                ),
            },
            "data_quality": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": (
                    "Quality of underlying data: "
                    "high=official permit/EIA document; "
                    "medium=credible report; "
                    "low=inference from capacity."
                ),
            },
            "sources_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Specific URLs or document names consulted. "
                    "Include at minimum the top source that informed the estimate."
                ),
            },
            "justification": {
                "type": "string",
                "description": (
                    "2-4 sentences. State the source of the area figure, your confidence, "
                    "and any expansion potential. Label claims as FACT, INFERENCE, or ESTIMATE."
                ),
            },
        },
    },
}

TOOLS: list[dict[str, Any]] = [
    {"type": "web_search_20250305", "name": "web_search"},   # Anthropic built-in server-side web search
    RECORD_TOOL,
]

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _llm_db_url(settings: Settings) -> str:
    base = settings.database.url
    return base.replace(f"/{settings.database.db}", f"/{settings.database.db}_llm")


def _ensure_infra_row(session: Session, site_id: str) -> None:
    """Insert a blank site_infrastructure_v2 row if it doesn't exist yet."""
    exists = session.execute(
        text("SELECT 1 FROM site_infrastructure_v2 WHERE site_id = :sid"),
        {"sid": site_id},
    ).fetchone()
    if not exists:
        session.execute(
            text("INSERT INTO site_infrastructure_v2 (site_id) VALUES (:sid)"),
            {"sid": site_id},
        )
        session.flush()


def _ensure_data_source(session: Session) -> None:
    exists = session.execute(
        text("SELECT 1 FROM data_sources WHERE name = :n"),
        {"n": SOURCE_NAME},
    ).fetchone()
    if not exists:
        session.execute(
            text(
                "INSERT INTO data_sources (source_id, name, url, description) "
                "VALUES (:id, :n, :u, :d)"
            ),
            {
                "id": str(uuid.uuid4()),
                "n": SOURCE_NAME,
                "u": SOURCE_URL,
                "d": f"Anthropic {MODEL} with web_search_20250305 — site area enrichment ({PROMPT_VERSION})",
            },
        )


def persist_result(
    session: Session,
    *,
    site_id: str,
    site_name: str,
    result: dict[str, Any],
    run_id: str,
) -> None:
    """Write one site's area result to the LLM database."""
    _ensure_data_source(session)
    _ensure_infra_row(session, site_id)
    now = datetime.now(timezone.utc)

    site_area = result.get("site_area_ha")
    buildable = result.get("buildable_area_ha") or site_area
    confidence = result.get("confidence", "low")
    data_quality = result.get("data_quality", "low")
    justification = result.get("justification", "")
    sources = result.get("sources_used", [])
    expansion = result.get("expansion_potential_ha", 0) or 0
    plant_status = result.get("plant_status", "unknown")

    comment = (
        f"[web_search {PROMPT_VERSION}] [status:{plant_status}] {justification} "
        f"Expansion potential: {expansion:.1f} ha."
    )[:2000]

    # sites.site_area_ha
    if site_area is not None:
        session.execute(
            text("UPDATE sites SET site_area_ha = :v WHERE site_id = :sid"),
            {"v": site_area, "sid": site_id},
        )

    # site_infrastructure_v2
    session.execute(
        text(
            "UPDATE site_infrastructure_v2 SET "
            "  buildable_area_ha = :ba, "
            "  ns05_quality = :q, "
            "  ns05_comment = :c, "
            "  fetched_at = :fa, "
            "  run_id = :rid "
            "WHERE site_id = :sid"
        ),
        {
            "ba": buildable,
            "q": data_quality,
            "c": comment,
            "fa": now,
            "rid": run_id,
            "sid": site_id,
        },
    )

    # site_observations
    obs_text = (
        f"[NS-05 web_search {PROMPT_VERSION}] Status: {plant_status}. "
        f"Site area: {site_area} ha (buildable: {buildable} ha, expansion: {expansion} ha). "
        f"Confidence: {confidence}. Sources: {'; '.join(sources[:5])}. "
        f"{justification}"
    )[:4000]

    session.execute(
        text(
            "INSERT INTO site_observations "
            "  (observation_id, site_id, criterion_id, observation, confidence, "
            "   impact, source_type, author, run_id, created_at) "
            "VALUES (:oid, :sid, :cid, :obs, :conf, :imp, :src, :auth, :rid, :cat)"
        ),
        {
            "oid": str(uuid.uuid4()),
            "sid": site_id,
            "cid": CRITERION_ID,
            "obs": obs_text,
            "conf": confidence,
            "imp": "neutral",
            "src": "web_search",
            "auth": f"{MODEL}|{PROMPT_VERSION}",
            "rid": run_id,
            "cat": now,
        },
    )

    log.info(
        "persist_ok",
        site_name=site_name,
        site_area_ha=site_area,
        buildable_area_ha=buildable,
        confidence=confidence,
        run_id=run_id,
    )


# ---------------------------------------------------------------------------
# Anthropic call
# ---------------------------------------------------------------------------

def _content_to_dicts(content_blocks: list[Any]) -> list[dict[str, Any]]:
    """Serialize SDK response content blocks to plain dicts for message history."""
    result = []
    for block in content_blocks:
        if isinstance(block, dict):
            result.append(block)
        elif hasattr(block, "model_dump"):
            result.append(block.model_dump())
        else:
            # Fallback: extract known fields manually
            d: dict[str, Any] = {"type": getattr(block, "type", "unknown")}
            for field in ("id", "name", "input", "text", "thinking", "tool_use_id", "content"):
                val = getattr(block, field, None)
                if val is not None:
                    d[field] = val
            result.append(d)
    return result


def search_site_area(
    client: anthropic.Anthropic,
    site: dict[str, Any],
) -> dict[str, Any]:
    """Call Claude with web_search + record_site_area tool. Returns tool input dict.

    Uses the beta client with betas=["web-search-2025-03-05"] so that Anthropic
    handles web search execution fully server-side. This avoids pause_turn issues
    where the client would otherwise need to thread search results back manually.
    """
    user_msg = _user_message(site)
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_msg}]

    for turn in range(MAX_TURNS):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,           # type: ignore[arg-type]
            messages=messages,
            betas=["web-search-2025-03-05"],
        )

        log.info(
            "llm_turn",
            site_name=site["name"],
            turn=turn + 1,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        # Collect tool_use blocks; web_search results are handled server-side
        record_input: dict[str, Any] | None = None
        web_search_tool_results: list[dict[str, Any]] = []
        other_tool_results: list[dict[str, Any]] = []

        for block in response.content:
            btype = getattr(block, "type", "")
            if btype == "tool_use":
                if block.name == "record_site_area":
                    record_input = dict(block.input)
                elif block.name == "web_search":
                    # Web search — results come back as web_search_result_block;
                    # we need to acknowledge them so the conversation can continue.
                    web_search_tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed — results available above.",
                    })
            elif btype == "web_search_result":
                # These are already embedded in the assistant message; no action needed.
                pass

        if record_input is not None:
            return record_input

        # Add the full assistant content to history
        assistant_content = _content_to_dicts(response.content)
        messages.append({"role": "assistant", "content": assistant_content})

        stop = response.stop_reason
        if stop == "end_turn":
            # Model wrote text but didn't call record_site_area — nudge it
            messages.append({
                "role": "user",
                "content": (
                    "You have gathered the search results. Please now call the "
                    "record_site_area tool with your consolidated findings. "
                    "Include: plant_status, site_area_ha, buildable_area_ha, "
                    "expansion_potential_ha, confidence, data_quality, "
                    "sources_used, and justification."
                ),
            })
        elif stop in ("tool_use", "pause_turn"):
            # Pass back tool results so the model can continue
            all_tool_results = web_search_tool_results + other_tool_results
            if all_tool_results:
                messages.append({"role": "user", "content": all_tool_results})
            else:
                messages.append({
                    "role": "user",
                    "content": "Please call record_site_area with your findings.",
                })
        else:
            # max_tokens or unexpected stop
            messages.append({
                "role": "user",
                "content": "Please call record_site_area with your best estimate so far.",
            })

    raise RuntimeError(
        f"record_site_area not called after {MAX_TURNS} turns for site: {site['name']}"
    )


# ---------------------------------------------------------------------------
# Site loading
# ---------------------------------------------------------------------------

def load_sites(
    session: Session,
    *,
    country: str | None = None,
    site_names: list[str] | None = None,
    skip_populated: bool = True,
    first_n: int | None = None,
) -> list[dict[str, Any]]:
    """Load target sites from the LLM DB.

    first_n: if set, picks the top N sites by installed_capacity_mw (after filtering
             out populated ones). Useful for phased runs (cycle0=5, cycle1=next 5).
    """
    where_clauses = ["s.country_code IS NOT NULL"]
    params: dict[str, Any] = {}

    if country:
        where_clauses.append("s.country_code = :country")
        params["country"] = country
    if site_names:
        where_clauses.append("s.name = ANY(:names)")
        params["names"] = site_names

    where_sql = " AND ".join(where_clauses)

    rows = session.execute(
        text(
            f"SELECT DISTINCT ON (s.name, s.country_code) "
            f"       s.site_id::text, s.name, s.country_name, s.country_code, "
            f"       s.latitude::float, s.longitude::float, "
            f"       s.installed_capacity_mw::float, s.plant_type, "
            f"       s.owner_operator, s.local_area, s.site_area_ha::float "
            f"FROM sites s "
            f"WHERE {where_sql} "
            f"ORDER BY s.name, s.country_code, s.site_id"
        ),
        params,
    ).fetchall()

    sites = [dict(r._mapping) for r in rows]

    if skip_populated:
        before = len(sites)
        sites = [s for s in sites if s.get("site_area_ha") is None]
        log.info("skip_populated_filter", before=before, after=len(sites))

    # Sort by capacity descending so --first-n always hits the largest (most documented) plants
    sites.sort(key=lambda s: (s.get("installed_capacity_mw") or 0), reverse=True)

    if first_n is not None:
        sites = sites[:first_n]

    return sites


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show plan without API calls")
    parser.add_argument(
        "--batch", default=None,
        help=(
            f"Named batch preset to run. Available: {', '.join(BATCH_PRESETS)}. "
            f"Default: {DEFAULT_BATCH}"
        ),
    )
    parser.add_argument(
        "--country", default=None,
        help="2-letter country code to process all sites (e.g. RO). Overrides --batch.",
    )
    parser.add_argument(
        "--sites", nargs="+", metavar="SITE_NAME",
        help="Specific site names to process. Overrides --batch and --country.",
    )
    parser.add_argument(
        "--first-n", type=int, default=None, metavar="N",
        help=(
            "Process only the top N remaining sites (by installed capacity). "
            "Useful for phased runs: --first-n 5 for cycle0, then run again for cycle1."
        ),
    )
    parser.add_argument(
        "--skip-populated", action="store_true", default=True,
        help="Skip sites that already have site_area_ha set (default: True)",
    )
    parser.add_argument(
        "--force-rerun", action="store_false", dest="skip_populated",
        help="Re-process sites even if site_area_ha is already populated",
    )
    args = parser.parse_args()

    # Determine target sites — precedence: --sites > --country > --batch > default
    site_names: list[str] | None = args.sites
    country: str | None = args.country
    if site_names is None and country is None:
        batch_key = args.batch or DEFAULT_BATCH
        if batch_key not in BATCH_PRESETS:
            print(f"ERROR: Unknown batch '{batch_key}'. Available: {', '.join(BATCH_PRESETS)}")
            sys.exit(1)
        site_names = BATCH_PRESETS[batch_key]
        print(f"  Batch: {batch_key} ({len(site_names)} sites)")

    settings = Settings()
    llm_url = _llm_db_url(settings)
    engine = create_engine(llm_url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)

    with SessionFactory() as session:
        sites = load_sites(
            session,
            country=country,
            site_names=site_names,
            skip_populated=args.skip_populated,
            first_n=args.first_n,
        )

    if not sites:
        print("No sites to process (all already populated, or none matched filters).")
        print("Use --force-rerun to re-process populated sites.")
        return

    # Show plan
    print(f"\n{'='*70}")
    print(f"  Web Search Site Area Enrichment — {len(sites)} site(s) to process")
    print(f"  Model: {MODEL} + web_search_20250305  |  Prompt: {PROMPT_VERSION}")
    print(f"  Target DB: {llm_url.split('@')[-1]}")
    print(f"{'='*70}")
    print(f"{'#':>4}  {'Country':>7}  {'Site':<42}  {'Current ha':>10}")
    print(f"{'-'*70}")
    for i, s in enumerate(sites, 1):
        current = f"{s['site_area_ha']:.1f}" if s.get("site_area_ha") else "—"
        print(f"{i:>4}  {s['country_code']:>7}  {s['name']:<42}  {current:>10}")
    print(f"{'-'*70}")

    est_calls = len(sites)
    est_tokens_per_site = 3000   # rough estimate incl. web search
    est_cost_usd = est_calls * est_tokens_per_site / 1_000_000 * 15  # Sonnet input ≈ $3/M, output ≈ $15/M
    print(f"\n  Estimated API calls : {est_calls}")
    print(f"  Estimated cost      : ~${est_cost_usd:.2f} USD (rough upper bound)")
    print(f"  Dry run             : {'YES — no API calls will be made' if args.dry_run else 'NO  — live API calls'}")
    print()

    if args.dry_run:
        print("DRY RUN complete. Re-run without --dry-run to execute.")
        return

    # Validate API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Export it or add it to .env.")
        sys.exit(1)

    run_id = f"site_area_web_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    print(f"  Run ID: {run_id}\n")

    client = anthropic.Anthropic(api_key=api_key)

    results_summary: list[dict[str, Any]] = []

    for i, site in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] Searching: {site['name']} ({site['country_code']}) ...")
        t0 = time.monotonic()
        try:
            result = search_site_area(client, site)
            elapsed = time.monotonic() - t0

            area = result.get("site_area_ha")
            buildable = result.get("buildable_area_ha") or area
            expansion = result.get("expansion_potential_ha", 0) or 0
            confidence = result.get("confidence", "?")

            print(
                f"  → site_area: {area:.1f} ha | buildable: {buildable:.1f} ha | "
                f"expansion: {expansion:.1f} ha | confidence: {confidence} | "
                f"{elapsed:.1f}s"
            )

            with SessionFactory() as session:
                persist_result(
                    session,
                    site_id=site["site_id"],
                    site_name=site["name"],
                    result=result,
                    run_id=run_id,
                )
                session.commit()

            results_summary.append({
                "name": site["name"],
                "country": site["country_code"],
                "site_area_ha": area,
                "buildable_area_ha": buildable,
                "expansion_potential_ha": expansion,
                "confidence": confidence,
                "plant_status": result.get("plant_status", "?"),
                "status": "ok",
            })

        except Exception as exc:
            elapsed = time.monotonic() - t0
            print(f"  ERROR: {exc} ({elapsed:.1f}s)")
            log.error("site_area_search_failed", site_name=site["name"], error=str(exc))
            results_summary.append({
                "name": site["name"],
                "country": site["country_code"],
                "status": "error",
                "error": str(exc),
            })

        if i < len(sites):
            time.sleep(INTER_SITE_DELAY_S)

    # Final summary table
    print(f"\n{'='*80}")
    print(f"  Run complete: {run_id}")
    print(f"{'='*80}")
    print(f"{'#':>4}  {'Site':<40}  {'Area ha':>8}  {'Build ha':>8}  {'Exp ha':>7}  {'Conf':>6}  {'Plt status':<12}  Run status")
    print(f"{'-'*100}")
    for i, r in enumerate(results_summary, 1):
        if r["status"] == "ok":
            print(
                f"{i:>4}  {r['name']:<40}  {r['site_area_ha']:>8.1f}  "
                f"{r['buildable_area_ha']:>8.1f}  {r['expansion_potential_ha']:>7.1f}  "
                f"{r['confidence']:>6}  {r.get('plant_status','?'):<12}  ok"
            )
        else:
            print(f"{i:>4}  {r['name']:<40}  {'—':>8}  {'—':>8}  {'—':>7}  {'—':>6}  {'—':<12}  ERROR: {r.get('error','?')[:30]}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
