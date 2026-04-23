# man_hours: 4.5
"""Multi-strategy matching of ENTSO-E A71 generation units to site names.

Three matching stages, tried in order of decreasing confidence:

  Stage 1 — **Direct fuzzy match** on improved-normalised names
            (CamelCase/underscore splitting, diacritic removal,
            trailing-digit stripping).  Threshold ≥ 70.

  Stage 2 — **Core-name extraction** strips known TSO prefixes
            (CTE, CET, CHE, TE, TPP, …) and short code suffixes
            (G1, B01, CA, …) from the A71 unit name before fuzzy
            comparison.  Threshold ≥ 75.

  Stage 3 — **Prefix-abbreviation + capacity confirmation** handles
            heavily coded names (e.g. Czech ``ECHV_G1____`` →
            ``CHV`` → *Chvaletice*).  Requires the abbreviation to
            be a prefix of the site name *and* the unit capacity to
            fall within a plausible ratio of the GEM installed
            capacity.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from rapidfuzz import fuzz

from atoms_vs_ashes.connectors.entso_e.models import GenerationUnit
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# ── Normalisation constants ──────────────────────────────────────────

_SUFFIXES_TO_STRIP = (
    "power plant",
    "power station",
    "thermal power plant",
    "thermal",
    "kraftwerk",
    "electrocentrala",
    "elektrownia",
    "termoelektrana",
    "toplarna",
    "centrala",
)

_EXTRA_TRANSLITS: dict[str, str] = {
    "ł": "l", "Ł": "L",
    "ø": "o", "Ø": "O",
    "đ": "d", "Đ": "D",
    "ß": "ss",
    "æ": "ae", "Æ": "AE",
    "ı": "i",
}

# TSO-specific prefixes that precede the place name in coded A71 names.
# CTE = Centrala Termoelectrică (RO), CET = Centrala Electrică de
# Termoficare (RO), CHE = Centrala Hidroelectrică (RO),
# TE = Termoelektrana (BA/RS/SI), TPP = Thermal Power Plant (BG),
# FHKW = Fernheizkraftwerk (AT), EC = Elektrociepłownia (PL),
# ESP = Elektrownia Szczytowo-Pompowa (PL), NPP = Nuclear Power Plant,
# HE = Hydroelectric (BA/SI), HPP = Hydro (BG).
_TSO_PREFIXES = frozenset({
    "cte", "cet", "che", "te", "tpp", "fhkw", "ec", "esp",
    "cne", "cccc", "hpp", "npp", "he", "bgp",
})

# Single-letter TSO prefix used by Czech CEPS (E = Elektrárna):
# ECHV → E + CHV (= Chvaletice).
_SINGLE_LETTER_TSO_PREFIX = "e"

# Short tokens that are unit/block identifiers, not place names.
_CODE_TOKEN_RE = re.compile(
    r"^(?:"
    r"[a-z]\d+|"         # g1, b01, h1 …
    r"\d+[a-z]?|"        # 3, 6a …
    r"[a-z]{1,4}\d{1,3}" # rovi3, turc1, crai1, braz5, isal7 …
    r")$"
)

# Country-code and generic suffixes that carry no place-name signal.
_STRIP_SUFFIXES = frozenset({"ca", "ret", "st", "ae"})

DEFAULT_MATCH_THRESHOLD = 70


# ── Normalisation ────────────────────────────────────────────────────

def normalise(name: str) -> str:
    """Lowercase, split CamelCase/underscores, strip diacritics and
    common power-plant suffixes, remove trailing digits from place-name
    tokens."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = s.lower().replace("_", " ").replace(".", " ")
    for src, dst in _EXTRA_TRANSLITS.items():
        s = s.replace(src, dst)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    for suffix in _SUFFIXES_TO_STRIP:
        s = s.replace(suffix, "")
    tokens = s.split()
    cleaned: list[str] = []
    for t in tokens:
        if len(t) > 3 and t[-1].isdigit():
            t = t.rstrip("0123456789")
        if t:
            cleaned.append(t)
    return " ".join(cleaned)


# ── Core-name extraction (Stage 2) ──────────────────────────────────

def extract_core_tokens(unit_name: str) -> list[str]:
    """Strip TSO prefixes, code suffixes, and short identifiers from
    *unit_name* to isolate probable place-name tokens."""
    norm = normalise(unit_name)
    tokens = norm.split()
    if not tokens:
        return []

    if tokens[0] in _TSO_PREFIXES:
        tokens = tokens[1:]

    core: list[str] = []
    for t in tokens:
        if t in _STRIP_SUFFIXES:
            continue
        if len(t) <= 2:
            continue
        if _CODE_TOKEN_RE.match(t):
            continue
        core.append(t)
    return core


# ── Prefix-abbreviation extraction (Stage 3) ─────────────────────────

def extract_abbreviation(unit_name: str) -> str | None:
    """Extract a potential place-name abbreviation from a coded A71 name.

    Handles patterns such as the Czech ``ECHV_G1____`` where the first
    character is a single-letter TSO prefix ('E' for Elektrárna) and the
    next 2-4 characters abbreviate the place name.

    Also handles compound-prefix codes like ``CetCraiova2_CRAI1_CA``
    where the TSO prefix is already stripped by :func:`normalise`.
    """
    norm = normalise(unit_name)
    tokens = norm.split()
    if not tokens:
        return None

    first = tokens[0]

    # Pattern: single-letter prefix + abbreviation (e.g. "echv" → "chv")
    if (
        len(first) >= 4
        and first[0] == _SINGLE_LETTER_TSO_PREFIX
        and first[1:].isalpha()
    ):
        abbrev = first[1:]
        if len(abbrev) >= 2:
            return abbrev

    # Pattern: multi-letter TSO prefix already stripped — first remaining
    # token IS the abbreviation if it's short and alphabetic
    if first in _TSO_PREFIXES and len(tokens) > 1:
        candidate = tokens[1]
        if candidate.isalpha() and len(candidate) <= 6:
            return candidate

    return None


# ── Capacity helpers ─────────────────────────────────────────────────

def capacity_confirms(
    unit_mw: float,
    site_mw: float,
    *,
    min_ratio: float = 0.15,
    max_ratio: float = 3.5,
) -> bool:
    """True when *unit_mw* is plausibly related to *site_mw*.

    A single A71 unit can be one block of a multi-block plant, so the
    unit capacity may be well below the total site capacity (hence the
    generous lower bound).  The unit should never be vastly larger than
    the plant, hence the tighter upper bound.
    """
    if site_mw <= 0 or unit_mw <= 0:
        return False
    ratio = unit_mw / site_mw
    return min_ratio <= ratio <= max_ratio


# ── Match result ─────────────────────────────────────────────────────

@dataclass
class MatchResult:
    """Outcome of matching A71 units against a site name."""

    matched: bool = False
    strategy: str = "none"
    capacity_mw: float | None = None
    unit_count: int = 0
    best_score: float = 0.0
    matched_units: list[GenerationUnit] = field(default_factory=list)
    zone_unknown_count: int = 0
    zone_unknown_total_mw: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "strategy": self.strategy,
            "capacity_mw": self.capacity_mw,
            "unit_count": self.unit_count,
            "best_score": round(self.best_score, 1),
            "matched_unit_names": [u.unit_name for u in self.matched_units],
            "zone_unknown_count": self.zone_unknown_count,
            "zone_unknown_total_mw": round(self.zone_unknown_total_mw, 1),
        }


# ── Main matching function ───────────────────────────────────────────

def match_entsoe_units(
    site_name: str,
    alternative_names: list[str] | None,
    zone_units: list[GenerationUnit],
    threshold: int = DEFAULT_MATCH_THRESHOLD,
    installed_capacity_mw: float | None = None,
) -> MatchResult:
    """Match ENTSO-E A71 generation units to a site using a 3-stage
    cascade.

    Parameters
    ----------
    site_name
        Primary site name from the database.
    alternative_names
        Additional name variants for fuzzy matching.
    zone_units
        All A71 generation units in the site's bidding zone.
    threshold
        Minimum ``token_set_ratio`` score for Stage 1 (default 70).
    installed_capacity_mw
        GEM installed capacity for the site (used by Stage 3 for
        capacity confirmation of prefix-abbreviation matches).

    Returns
    -------
    MatchResult
        Aggregated match outcome with provenance metadata.
    """
    if not zone_units or not site_name:
        return MatchResult()

    named_units = [u for u in zone_units if u.unit_name != "Unknown"]
    unknown_units = [u for u in zone_units if u.unit_name == "Unknown"]
    unknown_mw = sum(u.installed_mw for u in unknown_units)

    base = MatchResult(
        zone_unknown_count=len(unknown_units),
        zone_unknown_total_mw=unknown_mw,
    )

    if not named_units:
        return base

    candidates = [site_name]
    if alternative_names:
        candidates.extend(alternative_names)

    # ── Stage 1: Direct fuzzy match ──────────────────────────────
    result = _stage_fuzzy(candidates, named_units, threshold)
    if result is not None:
        result.strategy = "fuzzy_direct"
        result.zone_unknown_count = len(unknown_units)
        result.zone_unknown_total_mw = unknown_mw
        _log_match(site_name, result)
        return result

    # ── Stage 2: Core-name extraction + fuzzy + capacity ────────
    result = _stage_core_name(
        candidates, named_units,
        threshold=80, site_capacity_mw=installed_capacity_mw,
    )
    if result is not None:
        result.strategy = "core_name_extraction"
        result.zone_unknown_count = len(unknown_units)
        result.zone_unknown_total_mw = unknown_mw
        _log_match(site_name, result)
        return result

    # ── Stage 3: Prefix-abbreviation + capacity ──────────────────
    if installed_capacity_mw and installed_capacity_mw > 0:
        result = _stage_abbreviation(
            candidates, named_units, installed_capacity_mw,
        )
        if result is not None:
            result.strategy = "abbreviation_capacity"
            result.zone_unknown_count = len(unknown_units)
            result.zone_unknown_total_mw = unknown_mw
            _log_match(site_name, result)
            return result

    # ── No match — compute diagnostics ───────────────────────────
    best_score = _best_fuzzy_score(candidates, named_units)
    base.best_score = best_score
    return base


# ── Stage implementations ────────────────────────────────────────────

def _stage_fuzzy(
    candidates: list[str],
    units: list[GenerationUnit],
    threshold: int,
) -> MatchResult | None:
    """Stage 1: token_set_ratio on normalised names."""
    norm_cands = [normalise(c) for c in candidates]
    matched: list[GenerationUnit] = []
    best_score: float = 0.0

    for unit in units:
        norm_unit = normalise(unit.unit_name)
        if not norm_unit:
            continue
        for nc in norm_cands:
            score = fuzz.token_set_ratio(nc, norm_unit)
            if score > best_score:
                best_score = score
            if score >= threshold:
                matched.append(unit)
                break

    if not matched:
        return None

    return MatchResult(
        matched=True,
        capacity_mw=sum(u.installed_mw for u in matched),
        unit_count=len(matched),
        best_score=best_score,
        matched_units=matched,
    )


def _stage_core_name(
    candidates: list[str],
    units: list[GenerationUnit],
    threshold: int,
    site_capacity_mw: float | None = None,
) -> MatchResult | None:
    """Stage 2: extract place-name core from unit, then fuzzy-match.

    Requires capacity confirmation to prevent false positives when
    generic place names (e.g. "Maritsa") appear in multiple plants.
    """
    if not site_capacity_mw or site_capacity_mw <= 0:
        return None

    norm_cands = [normalise(c) for c in candidates]
    matched: list[GenerationUnit] = []
    best_score: float = 0.0

    for unit in units:
        core_tokens = extract_core_tokens(unit.unit_name)
        if not core_tokens:
            continue
        core_str = " ".join(core_tokens)

        if not capacity_confirms(
            unit.installed_mw, site_capacity_mw,
            min_ratio=0.25, max_ratio=3.0,
        ):
            continue

        for nc in norm_cands:
            score = fuzz.token_set_ratio(nc, core_str)
            if score > best_score:
                best_score = score
            if score >= threshold:
                matched.append(unit)
                break

    if not matched:
        return None

    return MatchResult(
        matched=True,
        capacity_mw=sum(u.installed_mw for u in matched),
        unit_count=len(matched),
        best_score=best_score,
        matched_units=matched,
    )


def _stage_abbreviation(
    candidates: list[str],
    units: list[GenerationUnit],
    site_capacity_mw: float,
) -> MatchResult | None:
    """Stage 3: prefix-abbreviation from coded unit name + capacity
    confirmation.

    The abbreviation must be a prefix of at least one site-name token.
    Capacity confirmation thresholds are tighter for shorter
    abbreviations.
    """
    norm_cands = [normalise(c) for c in candidates]
    cand_tokens: list[list[str]] = [nc.split() for nc in norm_cands]

    matched: list[GenerationUnit] = []
    best_score: float = 0.0

    for unit in units:
        abbrev = extract_abbreviation(unit.unit_name)
        if not abbrev or len(abbrev) < 2:
            continue

        min_r = 0.5 if len(abbrev) <= 2 else 0.15
        max_r = 2.0 if len(abbrev) <= 2 else 3.5

        if not capacity_confirms(
            unit.installed_mw, site_capacity_mw,
            min_ratio=min_r, max_ratio=max_r,
        ):
            continue

        for tokens in cand_tokens:
            for tok in tokens:
                if tok.startswith(abbrev):
                    score = 100.0 * len(abbrev) / max(len(tok), 1)
                    if score > best_score:
                        best_score = score
                    matched.append(unit)
                    break
            else:
                continue
            break

    if not matched:
        return None

    return MatchResult(
        matched=True,
        capacity_mw=sum(u.installed_mw for u in matched),
        unit_count=len(matched),
        best_score=best_score,
        matched_units=matched,
    )


# ── Helpers ──────────────────────────────────────────────────────────

def _best_fuzzy_score(
    candidates: list[str],
    units: list[GenerationUnit],
) -> float:
    """Return the highest token_set_ratio seen across all candidate ×
    unit pairs (for diagnostics when no stage matched)."""
    norm_cands = [normalise(c) for c in candidates]
    best: float = 0.0
    for unit in units:
        norm_unit = normalise(unit.unit_name)
        if not norm_unit:
            continue
        for nc in norm_cands:
            score = fuzz.token_set_ratio(nc, norm_unit)
            if score > best:
                best = score
    return best


def _log_match(site_name: str, result: MatchResult) -> None:
    log.info(
        "entsoe_units_matched",
        site_name=site_name,
        strategy=result.strategy,
        unit_count=result.unit_count,
        total_mw=round(result.capacity_mw or 0, 1),
        best_score=round(result.best_score, 1),
        unit_names=[u.unit_name for u in result.matched_units],
    )
