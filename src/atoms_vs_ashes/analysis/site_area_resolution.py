# man_hours: 7.0
"""Resolve site-area hectare evidence.

``resolve_site_area_ha`` is the original v1 merge helper and remains for
backwards compatibility. The v2 helpers below build an auditable candidate set
for the available main site / project land envelope stored in
``sites.site_area_ha``. Regional/favourable land evidence is still surfaced
separately, but the v2 estimator can use it as a bounded low-confidence
inference when direct footprint evidence is missing.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Literal

SourceTag = Literal[
    "llm",
    "api_footprint",
    "favourable_area",
    "favourable_band",
    "max_residual",
    "explicit_zero",
    "unidentified",
]


@dataclass(frozen=True)
class SiteAreaResolution:
    """Chosen hectare value and provenance for merged site-area repair."""

    value_ha: float | None
    source: SourceTag
    observation: str | None = None


FootprintSource = Literal[
    "manual_verified",
    "llm_web_structured",
    "llm_web_observation",
    "llm_db_site",
    "osm_polygon",
    "buildable_area_inference",
    "contiguous_capped_inference",
    "favourable_envelope_inference",
    "capacity_bounded_inference",
    "capacity_proxy",
    "cancelled_zero",
    "unidentified",
]

ConfidenceTier = Literal["high", "medium", "low", "review", "none"]

_SITE_AREA_RE = re.compile(r"Site area:\s*([0-9]+(?:\.[0-9]+)?)\s*ha", re.I)
_BUILDABLE_RE = re.compile(r"buildable:\s*([0-9]+(?:\.[0-9]+)?)\s*ha", re.I)
_EXPANSION_RE = re.compile(r"expansion:\s*([0-9]+(?:\.[0-9]+)?)\s*ha", re.I)
_CONFIDENCE_RE = re.compile(r"Confidence:\s*(high|medium|low)", re.I)
_URL_RE = re.compile(r"https?://[^\s;)]+")
_DIST_RE = re.compile(r"dist=([0-9]+(?:\.[0-9]+)?)\s*km", re.I)
_OSM_USEFUL_TAGS = (
    "power=plant",
    "landuse=industrial",
    "industrial=power_station",
    "industrial=power",
    "man_made=works",
)
_OFFICIAL_SOURCE_MARKERS = (
    "anpm",
    "permit",
    "cadastr",
    "auction",
    "licitatie",
    "licita",
    "insolv",
    "environmental",
    "autoriza",
    "report",
    "official",
)
_INFERENCE_SOURCES = {
    "buildable_area_inference",
    "contiguous_capped_inference",
    "favourable_envelope_inference",
    "capacity_bounded_inference",
}


@dataclass(frozen=True)
class SiteAreaObservation:
    """Parsed NS-05 web-search observation values."""

    site_area_ha: float | None = None
    buildable_area_ha: float | None = None
    expansion_potential_ha: float | None = None
    confidence: ConfidenceTier = "none"
    urls: tuple[str, ...] = ()
    never_built: bool = False
    text: str = ""


@dataclass(frozen=True)
class SiteAreaContext:
    """All non-candidate fields needed to judge site-area evidence."""

    site_id: str
    name: str
    country_code: str | None = None
    status: str | None = None
    installed_capacity_mw: float | None = None
    current_site_area_ha: float | None = None
    ns05_quality: str | None = None
    ns05_comment: str | None = None
    buildable_area_ha: float | None = None
    largest_contiguous_ha: float | None = None
    favourable_area_ha: float | None = None
    favourable_area_method: str | None = None
    merge_audit_final_ha: float | None = None
    llm_observation: SiteAreaObservation | None = None


@dataclass(frozen=True)
class SiteAreaCandidate:
    """One possible actual plant-footprint value."""

    value_ha: float | None
    source: FootprintSource
    provenance: str = ""
    source_confidence: ConfidenceTier = "none"
    has_url: bool = False
    useful_osm: bool = False
    weak_osm: bool = False
    flags: tuple[str, ...] = ()
    confidence_score: int = 0
    confidence_tier: ConfidenceTier = "none"
    write_eligible: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "value_ha": self.value_ha,
            "source": self.source,
            "provenance": self.provenance,
            "source_confidence": self.source_confidence,
            "has_url": self.has_url,
            "useful_osm": self.useful_osm,
            "weak_osm": self.weak_osm,
            "flags": list(self.flags),
            "confidence_score": self.confidence_score,
            "confidence_tier": self.confidence_tier,
            "write_eligible": self.write_eligible,
        }


@dataclass(frozen=True)
class SiteAreaRecommendation:
    """Selected footprint value plus full audit context."""

    site_id: str
    name: str
    proposed_site_area_ha: float | None
    source: FootprintSource
    confidence_tier: ConfidenceTier
    confidence_score: int
    write_eligible: bool
    review_flags: tuple[str, ...]
    candidates: tuple[SiteAreaCandidate, ...]
    regional_developable_ha: float | None = None
    regional_developable_method: str | None = None
    expansion_potential_ha: float | None = None
    buildable_text_ha: float | None = None
    selected_candidate: SiteAreaCandidate | None = None

    def candidates_json(self) -> list[dict[str, Any]]:
        return [candidate.to_dict() for candidate in self.candidates]


def resolve_site_area_ha(
    llm_ha: float | None,
    api_footprint_ha: float | None,
    favourable_area_ha: float | None,
    *,
    big_ha: float = 10.0,
    tiny_ha: float = 1.0,
) -> SiteAreaResolution:
    """Pick one hectare value using the merged-DB precedence rule."""
    llm = _finite(llm_ha)
    api = _finite(api_footprint_ha)
    fav = _finite(favourable_area_ha)

    if llm is not None and llm > big_ha:
        return SiteAreaResolution(llm, "llm")
    if api is not None and api > big_ha:
        return SiteAreaResolution(api, "api_footprint")
    if fav is not None and fav > big_ha:
        return SiteAreaResolution(fav, "favourable_area")

    present = [v for v in (llm, api, fav) if v is not None]
    if not present:
        return _unidentified()

    if all(v == 0.0 for v in present):
        return SiteAreaResolution(0.0, "explicit_zero")

    max_present = max(present)
    if max_present < tiny_ha:
        return _unidentified()

    if tiny_ha <= max_present <= big_ha:
        if fav is not None:
            return SiteAreaResolution(fav, "favourable_band")
        return SiteAreaResolution(max_present, "max_residual")

    if fav is not None:
        return SiteAreaResolution(fav, "favourable_area")
    return SiteAreaResolution(max_present, "max_residual")


def _unidentified() -> SiteAreaResolution:
    return SiteAreaResolution(
        None,
        "unidentified",
        "area could not be identified",
    )


def parse_site_area_observation(text: str | None) -> SiteAreaObservation:
    """Extract footprint/buildable/expansion values from NS-05 observation text."""
    if not text:
        return SiteAreaObservation()

    confidence_match = _CONFIDENCE_RE.search(text)
    confidence: ConfidenceTier = (
        confidence_match.group(1).lower()  # type: ignore[assignment]
        if confidence_match else "none"
    )
    lowered = text.lower()
    return SiteAreaObservation(
        site_area_ha=_match_float(_SITE_AREA_RE, text),
        buildable_area_ha=_match_float(_BUILDABLE_RE, text),
        expansion_potential_ha=_match_float(_EXPANSION_RE, text),
        confidence=confidence,
        urls=tuple(_URL_RE.findall(text)),
        never_built=(
            "never built" in lowered
            or "never constructed" in lowered
            or "no physical site" in lowered
            or "no physical power plant site" in lowered
            or "project was cancelled before construction" in lowered
        ),
        text=text,
    )


def build_site_area_recommendation(
    context: SiteAreaContext,
    *,
    manual_verified_ha: float | None = None,
    manual_note: str | None = None,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
    capacity_factor_ha_per_mw: float = 0.08,
) -> SiteAreaRecommendation:
    """Build a deterministic v2 footprint recommendation for one site."""
    flags = compute_review_flags(
        context,
        llm_structured_ha=llm_structured_ha,
        llm_db_site_ha=llm_db_site_ha,
        manual_verified_ha=manual_verified_ha,
    )
    candidates = build_footprint_candidates(
        context,
        manual_verified_ha=manual_verified_ha,
        manual_note=manual_note,
        llm_structured_ha=llm_structured_ha,
        llm_db_site_ha=llm_db_site_ha,
        capacity_factor_ha_per_mw=capacity_factor_ha_per_mw,
    )
    scored = tuple(score_candidate(candidate, candidates, context, flags) for candidate in candidates)
    selected = choose_site_area_candidate(scored)

    if selected is None and trusted_api_footprint(context, flags):
        selected = next((c for c in scored if c.source == "osm_polygon"), None)

    if selected is None:
        return SiteAreaRecommendation(
            site_id=context.site_id,
            name=context.name,
            proposed_site_area_ha=None,
            source="unidentified",
            confidence_tier="none",
            confidence_score=0,
            write_eligible=False,
            review_flags=tuple(sorted(flags)),
            candidates=scored,
            regional_developable_ha=_finite(context.favourable_area_ha),
            regional_developable_method=context.favourable_area_method,
            expansion_potential_ha=(
                context.llm_observation.expansion_potential_ha
                if context.llm_observation else None
            ),
            buildable_text_ha=(
                context.llm_observation.buildable_area_ha
                if context.llm_observation else None
            ),
            selected_candidate=None,
        )

    return SiteAreaRecommendation(
        site_id=context.site_id,
        name=context.name,
        proposed_site_area_ha=round(float(selected.value_ha), 2)
        if selected.value_ha is not None else None,
        source=selected.source,
        confidence_tier=selected.confidence_tier,
        confidence_score=selected.confidence_score,
        write_eligible=selected.write_eligible,
        review_flags=tuple(sorted(flags)),
        candidates=scored,
        regional_developable_ha=_finite(context.favourable_area_ha),
        regional_developable_method=context.favourable_area_method,
        expansion_potential_ha=(
            context.llm_observation.expansion_potential_ha
            if context.llm_observation else None
        ),
        buildable_text_ha=(
            context.llm_observation.buildable_area_ha
            if context.llm_observation else None
        ),
        selected_candidate=selected,
    )


def build_footprint_candidates(
    context: SiteAreaContext,
    *,
    manual_verified_ha: float | None = None,
    manual_note: str | None = None,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
    capacity_factor_ha_per_mw: float = 0.08,
) -> tuple[SiteAreaCandidate, ...]:
    """Collect candidate site/project land-envelope values.

    Direct footprint evidence still wins, but local spatial fields and bounded
    engineering estimates now provide lower-confidence candidates instead of
    forcing ``unidentified``.
    """
    candidates: list[SiteAreaCandidate] = []

    _append_candidate(
        candidates,
        manual_verified_ha,
        "manual_verified",
        manual_note or "user-approved manual value",
        "high",
        has_url=False,
    )
    _append_candidate(
        candidates,
        llm_structured_ha,
        "llm_web_structured",
        "merge_audit.llm_value.llm_site_area_ha",
        "medium",
        has_url=False,
    )

    observation = context.llm_observation
    if observation and observation.site_area_ha is not None:
        _append_candidate(
            candidates,
            observation.site_area_ha,
            "llm_web_observation",
            _observation_provenance(observation),
            observation.confidence,
            has_url=bool(observation.urls),
        )

    _append_candidate(
        candidates,
        llm_db_site_ha,
        "llm_db_site",
        "atoms_vs_ashes_llm.sites.site_area_ha",
        "medium",
        has_url=False,
    )

    useful_osm = _has_useful_osm_tags(context.ns05_comment)
    weak_osm = _weak_osm(context.ns05_comment)
    _append_candidate(
        candidates,
        context.current_site_area_ha,
        "osm_polygon",
        context.ns05_comment or "sites.site_area_ha",
        "medium" if useful_osm and not weak_osm else "low",
        has_url=False,
        useful_osm=useful_osm,
        weak_osm=weak_osm,
    )

    _append_candidate(
        candidates,
        _sane_buildable(context),
        "buildable_area_inference",
        "site_infrastructure_v2.buildable_area_ha",
        "low",
        has_url=False,
    )
    _append_candidate(
        candidates,
        _capped_contiguous(context, llm_structured_ha=llm_structured_ha, llm_db_site_ha=llm_db_site_ha),
        "contiguous_capped_inference",
        "capped site_infrastructure_v2.largest_contiguous_ha",
        "low",
        has_url=False,
    )
    _append_candidate(
        candidates,
        _favourable_envelope_estimate(context),
        "favourable_envelope_inference",
        "discounted site_infrastructure_v2.favourable_area_ha",
        "low",
        has_url=False,
    )

    capacity = _finite(context.installed_capacity_mw)
    if capacity is not None and capacity > 0:
        bounded_capacity = _bounded_capacity_estimate(
            context,
            capacity * capacity_factor_ha_per_mw,
            llm_structured_ha=llm_structured_ha,
            llm_db_site_ha=llm_db_site_ha,
        )
        _append_candidate(
            candidates,
            bounded_capacity,
            "capacity_bounded_inference",
            f"installed_capacity_mw * {capacity_factor_ha_per_mw}",
            "low",
            has_url=False,
        )

    if observation and observation.never_built and not _has_nonzero_land_evidence(
        context,
        llm_structured_ha=llm_structured_ha,
        llm_db_site_ha=llm_db_site_ha,
    ):
        candidates.append(SiteAreaCandidate(
            value_ha=0.0,
            source="cancelled_zero",
            provenance="NS-05 observation says never built/no physical site",
            source_confidence="high",
        ))

    return tuple(candidates)


def compute_review_flags(
    context: SiteAreaContext,
    *,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
    manual_verified_ha: float | None = None,
) -> set[str]:
    """Compute S1-S8 review flags independent of final candidate choice."""
    flags: set[str] = set()
    api = _finite(context.current_site_area_ha)
    fav = _finite(context.favourable_area_ha)
    buildable = _finite(context.buildable_area_ha)
    contiguous = _finite(context.largest_contiguous_ha)
    final = _finite(context.merge_audit_final_ha)

    if api is not None and api < 1:
        flags.add("S1")
    if api is not None and api < 10 and fav is not None and fav >= 50:
        flags.add("S2")
    if contiguous is not None and buildable is not None and contiguous > buildable * 1.05:
        flags.add("S3")
    if contiguous is not None and api is not None and contiguous > api * 1.05:
        flags.add("S4")
    if final is not None and api is not None and abs(final - api) > 0.5:
        flags.add("S5")

    llm_values = [
        _finite(manual_verified_ha),
        _finite(llm_structured_ha),
        _finite(llm_db_site_ha),
    ]
    if context.llm_observation:
        llm_values.append(_finite(context.llm_observation.site_area_ha))
    if api is not None and api > 0:
        if any(_ratio_conflict(api, value) for value in llm_values if value is not None and value > 0):
            flags.add("S6")

    if _weak_osm(context.ns05_comment):
        flags.add("S7")

    status = (context.status or "").lower()
    has_physical_value = any(
        value is not None and value >= 1
        for value in [api, fav, final, *llm_values]
    )
    never_built = bool(context.llm_observation and context.llm_observation.never_built)
    if (status == "cancelled" and has_physical_value) or (status != "cancelled" and never_built):
        flags.add("S8")

    return flags


def trusted_api_footprint(context: SiteAreaContext, flags: set[str] | tuple[str, ...]) -> bool:
    """Return whether the current OSM/API footprint can stand as site_area."""
    api = _finite(context.current_site_area_ha)
    if api is None or api < 10:
        return False
    if any(flag in set(flags) for flag in {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"}):
        return False
    if (context.ns05_quality or "").lower() not in {"high", "medium"}:
        return False
    return _has_useful_osm_tags(context.ns05_comment) and not _weak_osm(context.ns05_comment, max_dist=0.5)


def score_candidate(
    candidate: SiteAreaCandidate,
    candidates: tuple[SiteAreaCandidate, ...],
    context: SiteAreaContext,
    flags: set[str] | tuple[str, ...],
) -> SiteAreaCandidate:
    """Attach confidence score/tier/write eligibility to one candidate."""
    if candidate.value_ha is None:
        return candidate

    score = (
        _source_score(candidate, context, flags)
        + _provenance_score(candidate)
        + _plausibility_score(candidate, context)
        + _agreement_score(candidate, candidates)
        - _conflict_penalty(candidate, candidates, context, flags)
    )
    score = max(0, min(100, score))
    tier = _tier(score, candidate, flags)
    blocking = _has_blocking_conflict(candidate, flags)
    write_eligible = (
        tier in {"high", "medium", "low", "review"}
        and candidate.source != "capacity_proxy"
        and not blocking
    )
    if candidate.source in {"capacity_proxy", "capacity_bounded_inference"}:
        flags_tuple = tuple(sorted(set(candidate.flags) | {"S9"}))
    else:
        flags_tuple = candidate.flags
    return SiteAreaCandidate(
        value_ha=round(float(candidate.value_ha), 2),
        source=candidate.source,
        provenance=candidate.provenance,
        source_confidence=candidate.source_confidence,
        has_url=candidate.has_url,
        useful_osm=candidate.useful_osm,
        weak_osm=candidate.weak_osm,
        flags=flags_tuple,
        confidence_score=score,
        confidence_tier=tier,
        write_eligible=write_eligible,
    )


def choose_site_area_candidate(
    candidates: tuple[SiteAreaCandidate, ...],
) -> SiteAreaCandidate | None:
    """Choose the deterministic best candidate using the plan's evidence order."""
    manual = [c for c in candidates if c.source == "manual_verified" and c.write_eligible]
    if manual:
        return sorted(manual, key=lambda c: c.confidence_score, reverse=True)[0]

    eligible = [c for c in candidates if c.write_eligible]
    if not eligible:
        return None

    for sources, tiers in (
        ({"llm_web_observation", "llm_web_structured", "llm_db_site"}, {"high", "medium"}),
        ({"osm_polygon"}, {"high", "medium"}),
        ({"buildable_area_inference"}, {"high", "medium", "low", "review"}),
        ({"contiguous_capped_inference"}, {"high", "medium", "low", "review"}),
        ({"favourable_envelope_inference"}, {"high", "medium", "low", "review"}),
        ({"capacity_bounded_inference"}, {"high", "medium", "low", "review"}),
        ({"cancelled_zero"}, {"high", "medium", "low", "review"}),
    ):
        matches = [
            c for c in eligible
            if c.source in sources and c.confidence_tier in tiers
        ]
        if matches:
            return sorted(matches, key=lambda c: c.confidence_score, reverse=True)[0]

    return sorted(eligible, key=lambda c: c.confidence_score, reverse=True)[0]


def _append_candidate(
    candidates: list[SiteAreaCandidate],
    value: float | None,
    source: FootprintSource,
    provenance: str,
    confidence: ConfidenceTier,
    *,
    has_url: bool,
    useful_osm: bool = False,
    weak_osm: bool = False,
) -> None:
    finite = _finite(value)
    if finite is None or finite < 0:
        return
    if finite == 0 and source not in {"cancelled_zero", "manual_verified"}:
        return
    candidates.append(SiteAreaCandidate(
        value_ha=round(finite, 2),
        source=source,
        provenance=provenance[:500],
        source_confidence=confidence,
        has_url=has_url,
        useful_osm=useful_osm,
        weak_osm=weak_osm,
    ))


def _match_float(pattern: re.Pattern[str], text: str) -> float | None:
    match = pattern.search(text)
    if not match:
        return None
    return _finite(match.group(1))


def _observation_provenance(observation: SiteAreaObservation) -> str:
    urls = "; ".join(observation.urls[:5])
    if urls:
        return f"site_llm_observations NS-05; urls={urls}"
    return "site_llm_observations NS-05"


def _has_useful_osm_tags(comment: str | None) -> bool:
    lowered = (comment or "").lower()
    return any(tag in lowered for tag in _OSM_USEFUL_TAGS)


def _weak_osm(comment: str | None, *, max_dist: float = 1.0) -> bool:
    if not comment:
        return True
    distance = _distance_km(comment)
    lacks_tags = not _has_useful_osm_tags(comment)
    return lacks_tags and (distance is None or distance > max_dist)


def _distance_km(comment: str | None) -> float | None:
    if not comment:
        return None
    return _match_float(_DIST_RE, comment)


def _ratio_conflict(left: float, right: float) -> bool:
    if left <= 0 or right <= 0:
        return False
    ratio = max(left, right) / min(left, right)
    return ratio > 2


def _source_score(
    candidate: SiteAreaCandidate,
    context: SiteAreaContext,
    flags: set[str] | tuple[str, ...],
) -> int:
    if candidate.source == "manual_verified":
        return 45
    if candidate.source in {"llm_web_structured", "llm_web_observation"}:
        text = f"{candidate.provenance} {(context.llm_observation.text if context.llm_observation else '')}".lower()
        if candidate.source_confidence in {"high", "medium"} and any(marker in text for marker in _OFFICIAL_SOURCE_MARKERS):
            return 40
        return 30
    if candidate.source == "llm_db_site":
        return 25
    if candidate.source == "osm_polygon":
        return 25 if trusted_api_footprint(context, flags) else 5
    if candidate.source == "buildable_area_inference":
        return 22
    if candidate.source == "contiguous_capped_inference":
        return 20
    if candidate.source == "favourable_envelope_inference":
        return 22
    if candidate.source == "capacity_bounded_inference":
        return 15
    if candidate.source == "cancelled_zero":
        return 45
    return 0


def _provenance_score(candidate: SiteAreaCandidate) -> int:
    if candidate.source == "manual_verified":
        return 20
    if candidate.has_url:
        return 20
    if candidate.source == "osm_polygon" and candidate.useful_osm and not candidate.weak_osm:
        return 15
    if candidate.source == "llm_web_structured":
        return 10
    return 0


def _plausibility_score(candidate: SiteAreaCandidate, context: SiteAreaContext) -> int:
    value = candidate.value_ha
    if value is None:
        return 0
    if value == 0 and context.llm_observation and context.llm_observation.never_built:
        return 10
    if 1 <= value <= 500 and candidate.source != "cancelled_zero":
        return 10
    return 0


def _agreement_score(
    candidate: SiteAreaCandidate,
    candidates: tuple[SiteAreaCandidate, ...],
) -> int:
    value = candidate.value_ha
    if value is None or value <= 0:
        return 0
    ratios: list[float] = []
    for other in candidates:
        if other is candidate or other.value_ha is None or other.value_ha <= 0:
            continue
        if other.source == candidate.source or other.source == "capacity_proxy":
            continue
        ratios.append(min(value, other.value_ha) / max(value, other.value_ha))
    if any(ratio >= 0.75 for ratio in ratios):
        return 15
    if any(ratio >= 0.50 for ratio in ratios):
        return 8
    return 0


def _conflict_penalty(
    candidate: SiteAreaCandidate,
    candidates: tuple[SiteAreaCandidate, ...],
    context: SiteAreaContext,
    flags: set[str] | tuple[str, ...],
) -> int:
    if candidate.source in {"manual_verified", "cancelled_zero"}:
        return 0
    penalty = 0
    if (
        context.llm_observation
        and context.llm_observation.never_built
        and candidate.source in {"llm_web_structured", "llm_web_observation", "osm_polygon"}
        and candidate.value_ha is not None
        and candidate.value_ha > 0
    ):
        penalty += 30
    if _crosses_threshold(candidate, candidates):
        penalty += 5 if candidate.source in _INFERENCE_SOURCES else 20
    flag_set = set(flags)
    if candidate.source == "osm_polygon" and flag_set.intersection({"S1", "S2", "S5", "S6"}):
        penalty += 15
    if "S8" in flag_set and candidate.source not in _INFERENCE_SOURCES:
        penalty += 10
    if candidate.source == "osm_polygon" and candidate.weak_osm:
        penalty += 10
    if candidate.source in {"llm_web_structured", "llm_web_observation"} and candidate.source_confidence == "low":
        penalty += 10
    return penalty


def _crosses_threshold(
    candidate: SiteAreaCandidate,
    candidates: tuple[SiteAreaCandidate, ...],
) -> bool:
    value = candidate.value_ha
    if value is None:
        return False
    for other in candidates:
        if other is candidate or other.value_ha is None:
            continue
        if other.source == "capacity_proxy":
            continue
        for threshold in (14, 50):
            if (value < threshold <= other.value_ha) or (other.value_ha < threshold <= value):
                return True
    return False


def _tier(
    score: int,
    candidate: SiteAreaCandidate,
    flags: set[str] | tuple[str, ...],
) -> ConfidenceTier:
    if candidate.source == "capacity_proxy":
        return "low"
    if score >= 25 and _crosses_any_review_threshold(candidate, flags):
        return "review"
    if score >= 75 and not _has_blocking_conflict(candidate, flags):
        return "high"
    if score >= 50:
        return "medium"
    if score >= 25:
        return "low"
    return "none"


def _has_blocking_conflict(
    candidate: SiteAreaCandidate,
    flags: set[str] | tuple[str, ...],
) -> bool:
    if candidate.source == "manual_verified":
        return False
    flag_set = set(flags)
    if candidate.source == "osm_polygon" and flag_set.intersection({"S1", "S2", "S5", "S6", "S7"}):
        return True
    return False


def _sane_buildable(context: SiteAreaContext) -> float | None:
    buildable = _finite(context.buildable_area_ha)
    if buildable is None or buildable <= 0:
        return None
    if buildable < 1:
        return None
    if buildable < 10 and _max_local_evidence(context) >= 50:
        return None
    return buildable


def _capped_contiguous(
    context: SiteAreaContext,
    *,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
) -> float | None:
    contiguous = _finite(context.largest_contiguous_ha)
    if contiguous is None or contiguous <= 0:
        return None
    if contiguous < 1:
        return None
    if contiguous < 10 and _max_local_evidence(
        context,
        llm_structured_ha=llm_structured_ha,
        llm_db_site_ha=llm_db_site_ha,
    ) >= 50:
        return None
    bounds = [
        _finite(context.buildable_area_ha),
        _finite(context.favourable_area_ha),
        _finite(context.current_site_area_ha),
        _finite(context.merge_audit_final_ha),
        _finite(llm_structured_ha),
        _finite(llm_db_site_ha),
    ]
    capacity = _finite(context.installed_capacity_mw)
    if capacity is not None and capacity > 0:
        bounds.append(capacity * 0.08)
    if context.llm_observation:
        bounds.append(_finite(context.llm_observation.site_area_ha))
    upper = max([value for value in bounds if value is not None and value > 0], default=contiguous)
    if contiguous > upper * 1.05:
        return upper
    return contiguous


def _favourable_envelope_estimate(context: SiteAreaContext) -> float | None:
    favourable = _finite(context.favourable_area_ha)
    if favourable is None or favourable <= 0:
        return None
    if (context.status or "").lower() in {"cancelled", "announced", "pre_permit", "permitted", "shelved"}:
        discount = 1.0
    elif (context.ns05_quality or "").lower() in {"worldcover_10m", "corine_proxy", "low"}:
        discount = 0.5
    else:
        discount = 0.75
    return round(favourable * discount, 2)


def _bounded_capacity_estimate(
    context: SiteAreaContext,
    raw_capacity_estimate: float,
    *,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
) -> float | None:
    if raw_capacity_estimate <= 0:
        return None
    upper_values = [
        _finite(context.buildable_area_ha),
        _capped_contiguous(context, llm_structured_ha=llm_structured_ha, llm_db_site_ha=llm_db_site_ha),
        _finite(context.favourable_area_ha),
        _finite(context.merge_audit_final_ha),
        _finite(llm_structured_ha),
        _finite(llm_db_site_ha),
    ]
    if context.llm_observation:
        upper_values.append(_finite(context.llm_observation.site_area_ha))
    upper = max([value for value in upper_values if value is not None and value >= 1], default=None)
    if upper is None:
        return raw_capacity_estimate
    return min(raw_capacity_estimate, upper)


def _has_nonzero_land_evidence(
    context: SiteAreaContext,
    *,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
) -> bool:
    values = [
        _finite(context.current_site_area_ha),
        _finite(context.buildable_area_ha),
        _finite(context.largest_contiguous_ha),
        _finite(context.favourable_area_ha),
        _finite(context.merge_audit_final_ha),
        _finite(llm_structured_ha),
        _finite(llm_db_site_ha),
        _finite(context.installed_capacity_mw),
    ]
    if context.llm_observation:
        values.extend([
            _finite(context.llm_observation.site_area_ha),
            _finite(context.llm_observation.buildable_area_ha),
            _finite(context.llm_observation.expansion_potential_ha),
        ])
    return any(value is not None and value > 0 for value in values)


def _crosses_any_review_threshold(
    candidate: SiteAreaCandidate,
    flags: set[str] | tuple[str, ...],
) -> bool:
    return bool(set(flags).intersection({"S3", "S4", "S6", "S8"})) and candidate.source in _INFERENCE_SOURCES


def _max_local_evidence(
    context: SiteAreaContext,
    *,
    llm_structured_ha: float | None = None,
    llm_db_site_ha: float | None = None,
) -> float:
    values = [
        _finite(context.buildable_area_ha),
        _finite(context.largest_contiguous_ha),
        _finite(context.favourable_area_ha),
        _finite(context.merge_audit_final_ha),
        _finite(llm_structured_ha),
        _finite(llm_db_site_ha),
    ]
    capacity = _finite(context.installed_capacity_mw)
    if capacity is not None and capacity > 0:
        values.append(capacity * 0.08)
    if context.llm_observation:
        values.extend([
            _finite(context.llm_observation.site_area_ha),
            _finite(context.llm_observation.buildable_area_ha),
            _finite(context.llm_observation.expansion_potential_ha),
        ])
    return max([value for value in values if value is not None and value > 0], default=0.0)


def _finite(value: float | str | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number
