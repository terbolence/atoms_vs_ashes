"""Async orchestrator — fans out LLM assessments across sites and criteria.

Supports three run modes:
1. ``run()`` — standard all-at-once assessment (avoidance/ranking tiers).
2. ``run_second_pass()`` — re-run inconclusive Tier 1 with Opus.
3. ``run_sequential_elimination()`` — exclusionary tier with priority ordering,
   per-criterion batching, dedup, and short-circuit on failure.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.analysis._provenance import write_observation
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import (
    RankingScore,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.llm.audit_log import AuditLogger
from atoms_vs_ashes.llm.client import AnthropicLlmClient, LlmAssessmentError
from atoms_vs_ashes.llm.config import TIER_EXCLUSIONARY, LlmConfig
from atoms_vs_ashes.llm.context import build_context_for_criterion, compute_enrichment_coverage, load_sites, preload_site_data
from atoms_vs_ashes.llm.persist import persist_result
from atoms_vs_ashes.llm.prompts import get_prompt, get_prompt_version
from atoms_vs_ashes.llm.schemas import (
    ALL_KEYS,
    AVOIDANCE_KEYS,
    EXCLUSIONARY_KEYS,
    PROMPT_REGISTRY,
    RANKING_KEYS,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

EXCLUSIONARY_PRIORITY: list[str] = [
    "E9",  # Cooling Water Supply — binary pass/fail
    "E7",  # Protected Natural Areas — Natura 2000 binary
    "E1",  # Seismic (Capable Fault) — Vrancea zone
    "E8",  # Emergency Planning — population/infrastructure
    "E3",  # Site Topography — slope instability
    "E2",  # Geotechnical Suitability — liquefaction
    "E4",  # Volcanic Hazard — no Holocene volcanism in RO
    "E5",  # Subsurface (Karst)
    "E6",  # Subsurface (Subsidence)
]

HIGH_DISCRIMINATION_CRITERIA = frozenset({"E1", "E2", "E8"})
_ENRICHMENT_UPGRADE_THRESHOLD = 0.30

_DEFINITIVE_VERDICTS_EXCL = {"pass", "fail"}
_DEFINITIVE_VERDICTS_AVOID = {"pass", "fail", "caution"}

# Countries with zero Holocene volcanism — E4 can be resolved algorithmically.
_NON_VOLCANIC_COUNTRIES: frozenset[str] = frozenset({
    "PL", "CZ", "SK", "HU", "AT", "SI", "HR", "BA", "RS", "ME", "XK",
    "AL", "MK", "RO", "BG", "MD", "UA", "BY", "EE", "LV", "LT",
})

# Criteria that require API enrichment data to produce meaningful LLM results.
# When avg enrichment coverage for *primary* fields is below
# _DEFER_COVERAGE_THRESHOLD the entire phase is deferred.
DEFERRABLE_CRITERIA: dict[str, dict[str, Any]] = {
    "E1": {
        "primary_fields": {"nearest_fault_km", "fault_slip_rate_mm_yr"},
        "required_sources": ["GEM Global Active Faults Database (GAF-DB)", "EDSF European Database of Seismogenic Faults"],
        "reason": "Fault distance cannot be reliably estimated by LLM without geospatial DB data",
    },
    "E2": {
        "primary_fields": {"soil_type", "liquefaction_suscept"},
        "required_sources": ["EGDI surface lithology", "ESHM20 PGA hazard map"],
        "reason": "Soil type and liquefaction susceptibility require geotechnical survey or geodata API",
    },
    "E7": {
        "primary_fields": {"n2k_overlap", "n2k_nearest_distance_km", "wdpa_overlap", "wdpa_nearest_distance_km"},
        "required_sources": ["Natura 2000 WFS", "WDPA Protected Planet"],
        "reason": "Protected area overlap is a spatial query, not suitable for LLM desk study",
    },
    "E8": {
        "primary_fields": {"road_density_km_per_km2", "pop_density_5km", "ep01_composite_score", "ep01_evacuation_feasible"},
        "required_sources": ["OSM road density analysis", "GHS-POP population grid", "Copernicus DEM (terrain)"],
        "reason": "Road network, population density, and terrain data are quantitative inputs requiring GIS pipeline (DRV-02)",
    },
}

_DEFER_COVERAGE_THRESHOLD = 0.10

# Criteria eligible for second-pass resolution by Opus (LLM CAN help).
# Deferred criteria and criteria where the LLM fundamentally lacks data are excluded.
_SECOND_PASS_ELIGIBLE: frozenset[str] = frozenset({
    "E3", "E5", "E6", "E9",
})


# ===================================================================
# Data classes
# ===================================================================

@dataclass
class SecondPassCandidate:
    """A Tier 1 assessment that warrants re-evaluation with a stronger model."""

    site_id: uuid.UUID
    site_name: str
    prompt_key: str
    criterion_id: str
    verdict: str
    confidence: str
    reason: str


@dataclass
class EliminatedSite:
    """A site excluded during sequential elimination."""

    site_id: uuid.UUID
    site_name: str
    excluded_by_prompt_key: str
    excluded_by_criterion_id: str
    exclusion_justification: str
    phase_number: int


@dataclass
class AssessmentSummary:
    """Aggregated results for a full LLM assessment run."""

    run_id: str = ""
    total_sites: int = 0
    total_calls: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    elapsed_s: float = 0.0
    errors: list[dict[str, str]] = field(default_factory=list)
    second_pass_candidates: list[SecondPassCandidate] = field(default_factory=list)
    excluded_sites: list[EliminatedSite] = field(default_factory=list)
    api_calls_saved: int = 0
    phase_reports: list[dict[str, Any]] = field(default_factory=list)
    deferred_phases: list[dict[str, Any]] = field(default_factory=list)
    criterion_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    confidence_distribution: dict[str, dict[str, int]] = field(default_factory=dict)
    token_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    per_country_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    sources_needed_frequency: dict[str, int] = field(default_factory=dict)
    second_pass_upgrades: list[dict[str, str]] = field(default_factory=list)

    def record_verdict(self, criterion_id: str, verdict: str, confidence: str) -> None:
        """Track per-criterion verdict and confidence counts."""
        cs = self.criterion_stats.setdefault(criterion_id, {
            "pass": 0, "fail": 0, "inconclusive": 0, "deferred": 0, "not_assessed": 0,
        })
        cs[verdict] = cs.get(verdict, 0) + 1

        cd = self.confidence_distribution.setdefault(criterion_id, {
            "high": 0, "medium": 0, "low": 0,
        })
        if confidence in cd:
            cd[confidence] = cd.get(confidence, 0) + 1

    def record_tokens(self, criterion_id: str, input_tokens: int, output_tokens: int) -> None:
        tu = self.token_usage.setdefault(criterion_id, {"input_tokens": 0, "output_tokens": 0})
        tu["input_tokens"] += input_tokens
        tu["output_tokens"] += output_tokens

    def record_country_verdict(self, country_code: str, verdict: str, confidence: str) -> None:
        cs = self.per_country_stats.setdefault(country_code, {
            "pass": 0, "fail": 0, "inconclusive": 0, "deferred": 0,
            "high": 0, "medium": 0, "low": 0,
        })
        cs[verdict] = cs.get(verdict, 0) + 1
        if confidence in ("high", "medium", "low"):
            cs[confidence] = cs.get(confidence, 0) + 1

    def record_sources_needed(self, sources: list[str] | None) -> None:
        if not sources:
            return
        for src in sources:
            normalized = src.strip()
            if normalized:
                self.sources_needed_frequency[normalized] = (
                    self.sources_needed_frequency.get(normalized, 0) + 1
                )

    @property
    def quality_grade(self) -> float:
        """Percentage of LLM assessments with medium or high confidence."""
        total = 0
        medium_plus = 0
        for cid, cd in self.confidence_distribution.items():
            total += cd.get("high", 0) + cd.get("medium", 0) + cd.get("low", 0)
            medium_plus += cd.get("high", 0) + cd.get("medium", 0)
        return round((medium_plus / total * 100) if total > 0 else 0.0, 1)

    def _per_country_quality_grades(self) -> dict[str, dict[str, Any]]:
        grades: dict[str, dict[str, Any]] = {}
        for cc, stats in self.per_country_stats.items():
            high = stats.get("high", 0)
            medium = stats.get("medium", 0)
            low = stats.get("low", 0)
            total = high + medium + low
            pct = round((high + medium) / total * 100, 1) if total > 0 else 0.0
            grades[cc] = {
                "quality_grade_pct": pct,
                "total_assessments": total,
                "high_confidence": high,
                "medium_confidence": medium,
                "low_confidence": low,
            }
        return grades

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "total_calls": self.total_calls,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "elapsed_s": round(self.elapsed_s, 1),
            "error_count": len(self.errors),
            "errors": self.errors[:20],
            "second_pass_candidates": len(self.second_pass_candidates),
            "second_pass_details": [
                {
                    "site_name": c.site_name,
                    "prompt_key": c.prompt_key,
                    "verdict": c.verdict,
                    "confidence": c.confidence,
                    "reason": c.reason,
                }
                for c in self.second_pass_candidates
            ],
            "excluded_sites": [
                {
                    "site_name": e.site_name,
                    "excluded_by": e.excluded_by_prompt_key,
                    "phase": e.phase_number,
                }
                for e in self.excluded_sites
            ],
            "api_calls_saved": self.api_calls_saved,
            "phase_reports": self.phase_reports,
            "deferred_phases": self.deferred_phases,
            "criterion_stats": self.criterion_stats,
            "confidence_distribution": self.confidence_distribution,
            "token_usage": self.token_usage,
            "per_country_stats": self.per_country_stats,
            "per_country_quality_grade": self._per_country_quality_grades(),
            "sources_needed_frequency": dict(
                sorted(self.sources_needed_frequency.items(), key=lambda x: -x[1])[:30]
            ) if self.sources_needed_frequency else {},
            "second_pass_upgrades": self.second_pass_upgrades,
            "quality_grade_pct": self.quality_grade,
        }


# ===================================================================
# Orchestrator
# ===================================================================

class LlmOrchestrator:
    """Batch orchestrator for LLM siting assessments."""

    def __init__(
        self,
        settings: Settings,
        llm_config: LlmConfig,
        *,
        run_id: str,
    ) -> None:
        self._settings = settings
        self._llm_config = llm_config
        self._run_id = run_id

        self._main_engine = create_engine(
            settings.database.url, echo=False, pool_pre_ping=True,
        )
        self._main_session_factory = sessionmaker(bind=self._main_engine)

        llm_db_url = settings.database.url.replace(
            f"/{settings.database.db}",
            f"/{settings.database.db}_llm",
        )
        self._llm_engine = create_engine(
            llm_db_url, echo=False, pool_pre_ping=True,
        )
        self._llm_session_factory = sessionmaker(bind=self._llm_engine)

        self._site_data_cache: list[dict[str, Any]] = []

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    def _select_keys(self, tier: str) -> list[str]:
        if tier == "all":
            return list(ALL_KEYS)
        if tier == "exclusionary":
            return list(EXCLUSIONARY_KEYS)
        if tier == "avoidance":
            return list(AVOIDANCE_KEYS)
        if tier == "ranking":
            return list(RANKING_KEYS)
        raise ValueError(f"Unknown tier: {tier}")

    def _load_smr_keys(self) -> list[str]:
        with self._llm_session_factory() as session:
            return [r.smr_key for r in session.query(SmrDesign.smr_key).all()]

    def _load_and_cache_sites(
        self,
        site_ids: list[uuid.UUID] | None,
        country_codes: list[str] | None,
    ) -> list[dict[str, Any]]:
        with self._llm_session_factory() as llm_session:
            sites = load_sites(llm_session, site_ids=site_ids, country_codes=country_codes)
            self._site_data_cache = []
            for s in sites:
                try:
                    with self._main_session_factory() as main_session:
                        main_site = main_session.get(Site, s.site_id)
                        if main_site:
                            cached = preload_site_data(main_site, main_session)
                        else:
                            cached = preload_site_data(s, llm_session)
                except Exception:
                    cached = preload_site_data(s, llm_session)
                self._site_data_cache.append({
                    "site_id": s.site_id,
                    "name": s.name,
                    "cached": cached,
                })
        return self._site_data_cache

    # ---------------------------------------------------------------
    # Dedup — universal check for all tiers
    # ---------------------------------------------------------------

    def _check_existing_assessment(
        self,
        session: Session,
        site_id: uuid.UUID,
        prompt_key: str,
    ) -> dict[str, Any] | None:
        """Check DB for an existing usable LLM result for (site_id, prompt_key).

        Returns a summary dict if found, or None if an API call is needed.
        """
        schema_cls = PROMPT_REGISTRY[prompt_key]
        criterion_id = schema_cls.model_fields["criterion_id"].default

        if prompt_key in EXCLUSIONARY_KEYS:
            definitive = _DEFINITIVE_VERDICTS_EXCL
        elif prompt_key in AVOIDANCE_KEYS:
            definitive = _DEFINITIVE_VERDICTS_AVOID
        else:
            row = (
                session.query(RankingScore)
                .filter_by(site_id=site_id, criterion_id=criterion_id)
                .filter(RankingScore.score_0_10.isnot(None))
                .order_by(RankingScore.scored_at.desc())
                .first()
            )
            if row:
                return {
                    "type": "ranking_score",
                    # ``score`` is retained for audit-log compatibility;
                    # its value is the native 0–10 score post-Alembic 033.
                    "score": float(row.score_0_10),
                    "score_0_10": float(row.score_0_10),
                    "confidence": row.confidence,
                    "run_id": row.run_id,
                    "scored_at": str(row.scored_at),
                }
            return None

        row = (
            session.query(ScreeningVerdict)
            .filter_by(site_id=site_id, criterion_id=criterion_id)
            .filter(ScreeningVerdict.verdict.in_(definitive))
            .order_by(ScreeningVerdict.screened_at.desc())
            .first()
        )
        if row:
            return {
                "type": "screening_verdict",
                "verdict": row.verdict,
                "confidence": row.confidence,
                "run_id": row.run_id,
                "screened_at": str(row.screened_at),
                "prompt_key": row.prompt_key,
            }
        return None

    # ---------------------------------------------------------------
    # Standard run (avoidance / ranking / all-at-once)
    # ---------------------------------------------------------------

    async def run(
        self,
        *,
        tier: str = "all",
        site_ids: list[uuid.UUID] | None = None,
        country_codes: list[str] | None = None,
        dry_run: bool = False,
        force_rerun: bool = False,
    ) -> AssessmentSummary:
        """Execute the first-pass LLM assessment pipeline."""
        t0 = time.monotonic()
        keys = self._select_keys(tier)
        smr_keys = self._load_smr_keys()

        if not smr_keys:
            log.warning("llm_no_smr_designs", msg="No SMR designs in LLM DB.")
            smr_keys = ["nuscale_voygr6"]

        site_data = self._load_and_cache_sites(site_ids, country_codes)

        summary = AssessmentSummary(
            run_id=self._run_id,
            total_sites=len(site_data),
            total_calls=len(site_data) * len(keys),
        )

        if dry_run:
            log.info(
                "llm_dry_run",
                sites=len(site_data),
                criteria=len(keys),
                total_calls=summary.total_calls,
                keys=keys,
            )
            summary.elapsed_s = time.monotonic() - t0
            return summary

        async with AnthropicLlmClient(self._llm_config, run_id=self._run_id) as client:
            tasks = []
            for sd in site_data:
                for key in keys:
                    if not force_rerun:
                        with self._llm_session_factory() as sess:
                            existing = self._check_existing_assessment(sess, sd["site_id"], key)
                        if existing:
                            summary.skipped += 1
                            log.info(
                                "llm_assess_skipped",
                                site_id=str(sd["site_id"]),
                                prompt_key=key,
                                existing=existing,
                            )
                            if client.audit:
                                schema_cls = PROMPT_REGISTRY[key]
                                crit_id = schema_cls.model_fields["criterion_id"].default
                                client.audit.log_skip(
                                    site_id=str(sd["site_id"]),
                                    site_name=sd["name"],
                                    criterion_id=crit_id,
                                    prompt_key=key,
                                    skip_reason="definitive_verdict_exists",
                                    existing_verdict=existing.get("verdict"),
                                    existing_score=existing.get("score"),
                                    existing_confidence=existing.get("confidence"),
                                    existing_run_id=existing.get("run_id"),
                                )
                            continue

                    site_context = build_context_for_criterion(sd["cached"], key)
                    coverage = compute_enrichment_coverage(sd["cached"], key)
                    tasks.append(
                        self._assess_one(
                            client=client,
                            site_id=sd["site_id"],
                            site_name=sd["name"],
                            site_context=site_context,
                            prompt_key=key,
                            smr_keys=smr_keys,
                            summary=summary,
                            enrichment_coverage=coverage,
                        )
                    )
            await asyncio.gather(*tasks)

        summary.elapsed_s = time.monotonic() - t0
        log.info("llm_run_complete", **summary.to_dict())
        return summary

    # ---------------------------------------------------------------
    # Sequential elimination (exclusionary tier)
    # ---------------------------------------------------------------

    def _run_phase0_prescreen(
        self,
        active_sites: dict[uuid.UUID, dict[str, Any]],
        smr_keys: list[str],
        summary: AssessmentSummary,
        audit: AuditLogger,
    ) -> list[uuid.UUID]:
        """Phase 0: run BF-01/BF-02 algorithmic checks, return eliminated site IDs."""
        from atoms_vs_ashes.screening.grid_capacity import evaluate_site_for_smr as bf01_eval
        from atoms_vs_ashes.screening.land_area import evaluate_site_for_smr as bf02_eval

        eliminated_ids: list[uuid.UUID] = []

        with self._llm_session_factory() as session:
            for sid, sd in list(active_sites.items()):
                site = session.get(Site, sid)
                if not site:
                    continue

                capacity = None
                for attr in ("grid_capacity_mw", "installed_capacity_mw"):
                    val = getattr(site, attr, None)
                    if val is not None:
                        capacity = float(val)
                        break

                area = float(site.site_area_ha) if getattr(site, "site_area_ha", None) else None

                if capacity is None:
                    log.warning(
                        "phase0_bf01_skipped",
                        site=sd["name"],
                        site_id=str(sid),
                        reason="installed_capacity_mw is NULL — BF-01 cannot evaluate",
                    )
                if area is None:
                    log.warning(
                        "phase0_bf02_skipped",
                        site=sd["name"],
                        site_id=str(sid),
                        reason="site_area_ha is NULL — BF-02 cannot evaluate",
                    )

                bf01_all_fail = capacity is not None
                bf02_all_fail = area is not None

                for smr_key, spec in self._settings.smr_types.items():
                    if smr_key not in smr_keys:
                        continue
                    if capacity is not None:
                        v1, _, _ = bf01_eval(capacity, smr_key, spec["name"], float(spec["capacity_mwe"]))
                        if v1 != "fail":
                            bf01_all_fail = False
                    else:
                        bf01_all_fail = False

                    if area is not None:
                        v2, _, _ = bf02_eval(area, smr_key, spec["name"], float(spec["land_ha"]))
                        if v2 != "fail":
                            bf02_all_fail = False
                    else:
                        bf02_all_fail = False

                if bf01_all_fail:
                    reason = f"Grid capacity {capacity:.0f} MW below all SMR thresholds"
                    elim = EliminatedSite(
                        site_id=sid, site_name=sd["name"],
                        excluded_by_prompt_key="BF-01",
                        excluded_by_criterion_id="BF-01",
                        exclusion_justification=reason,
                        phase_number=0,
                    )
                    summary.excluded_sites.append(elim)
                    eliminated_ids.append(sid)
                    self._persist_not_assessed(sid, "BF-01", "BF-01", list(EXCLUSIONARY_PRIORITY), smr_keys)
                    audit.log_elimination(
                        site_id=str(sid), site_name=sd["name"],
                        excluded_by_criterion="BF-01",
                        excluded_by_prompt_key="BF-01",
                        exclusion_verdict="fail",
                        exclusion_justification=reason,
                        remaining_criteria_skipped=list(EXCLUSIONARY_PRIORITY),
                    )
                    log.info("phase0_eliminated", site=sd["name"], reason="BF-01", detail=reason)
                elif bf02_all_fail:
                    reason = f"Site area {area:.1f} ha below all SMR land requirements"
                    elim = EliminatedSite(
                        site_id=sid, site_name=sd["name"],
                        excluded_by_prompt_key="BF-02",
                        excluded_by_criterion_id="BF-02",
                        exclusion_justification=reason,
                        phase_number=0,
                    )
                    summary.excluded_sites.append(elim)
                    eliminated_ids.append(sid)
                    self._persist_not_assessed(sid, "BF-02", "BF-02", list(EXCLUSIONARY_PRIORITY), smr_keys)
                    audit.log_elimination(
                        site_id=str(sid), site_name=sd["name"],
                        excluded_by_criterion="BF-02",
                        excluded_by_prompt_key="BF-02",
                        exclusion_verdict="fail",
                        exclusion_justification=reason,
                        remaining_criteria_skipped=list(EXCLUSIONARY_PRIORITY),
                    )
                    log.info("phase0_eliminated", site=sd["name"], reason="BF-02", detail=reason)

        return eliminated_ids

    async def run_sequential_elimination(
        self,
        *,
        site_ids: list[uuid.UUID] | None = None,
        country_codes: list[str] | None = None,
        dry_run: bool = False,
        force_rerun: bool = False,
        no_defer: bool = False,
    ) -> AssessmentSummary:
        """Exclusionary assessment with priority ordering and short-circuit.

        Phase 0 runs BF-01/BF-02 algorithmic checks (no API calls).
        Phases 1-9 run one exclusionary criterion at a time across all
        active sites.  Sites that fail are eliminated and receive
        ``not_assessed`` for remaining criteria.

        Criteria in ``DEFERRABLE_CRITERIA`` are auto-deferred when enrichment
        coverage is below ``_DEFER_COVERAGE_THRESHOLD`` (overridden by
        ``no_defer=True``).  E4 (Volcanism) is resolved algorithmically for
        countries in ``_NON_VOLCANIC_COUNTRIES``.
        """
        t0 = time.monotonic()
        smr_keys = self._load_smr_keys()
        if not smr_keys:
            smr_keys = ["nuscale_voygr6"]

        site_data = self._load_and_cache_sites(site_ids, country_codes)

        summary = AssessmentSummary(
            run_id=self._run_id,
            total_sites=len(site_data),
        )

        active_sites = {sd["site_id"]: sd for sd in site_data}
        eliminated: dict[uuid.UUID, EliminatedSite] = {}

        if dry_run:
            total_possible = len(site_data) * len(EXCLUSIONARY_PRIORITY)
            log.info(
                "llm_sequential_dry_run",
                sites=len(site_data),
                criteria=len(EXCLUSIONARY_PRIORITY),
                priority_order=[k for k in EXCLUSIONARY_PRIORITY],
                max_api_calls=total_possible,
            )
            summary.total_calls = total_possible
            summary.elapsed_s = time.monotonic() - t0
            return summary

        audit = AuditLogger(self._run_id)

        # Phase 0: algorithmic pre-screening (no API calls)
        phase0_elim = self._run_phase0_prescreen(active_sites, smr_keys, summary, audit)
        for eid in phase0_elim:
            active_sites.pop(eid, None)
        if phase0_elim:
            summary.phase_reports.append({
                "phase": 0, "criterion": "BF-01/BF-02",
                "criterion_id": "basic_filter",
                "assessed": len(site_data), "skipped_dedup": 0,
                "eliminated": len(phase0_elim),
                "remaining": len(active_sites),
                "api_calls_saved_this_phase": len(phase0_elim) * len(EXCLUSIONARY_PRIORITY),
            })
            summary.api_calls_saved += len(phase0_elim) * len(EXCLUSIONARY_PRIORITY)

        async with AnthropicLlmClient(self._llm_config, run_id=self._run_id) as client:
            for phase_num, prompt_key in enumerate(EXCLUSIONARY_PRIORITY, start=1):
                if not active_sites:
                    log.info("llm_all_sites_eliminated", phase=phase_num)
                    break

                schema_cls = PROMPT_REGISTRY[prompt_key]
                criterion_id = schema_cls.model_fields["criterion_id"].default
                phase_assessed = 0
                phase_skipped = 0
                phase_eliminated_ids: list[uuid.UUID] = []

                coverages = {}
                for sid, sd in active_sites.items():
                    cov = compute_enrichment_coverage(sd["cached"], prompt_key)
                    coverages[sid] = cov
                avg_cov = (
                    sum(c["coverage_pct"] for c in coverages.values()) / len(coverages)
                    if coverages else 0.0
                )
                low_cov_sites = [
                    sd["name"] for sid, sd in active_sites.items()
                    if coverages.get(sid, {}).get("coverage_pct", 0) < _ENRICHMENT_UPGRADE_THRESHOLD
                ]
                log.info(
                    "llm_phase_enrichment_scan",
                    phase=phase_num,
                    criterion=prompt_key,
                    avg_coverage_pct=round(avg_cov, 2),
                    low_coverage_sites=low_cov_sites if low_cov_sites else None,
                    total_sites=len(active_sites),
                )

                # --- Algorithmic E4 for non-volcanic countries ---
                site_countries = {
                    sid: sd["cached"].get("country_code", "")
                    for sid, sd in active_sites.items()
                }
                all_non_volcanic = (
                    prompt_key == "E4"
                    and all(cc in _NON_VOLCANIC_COUNTRIES for cc in site_countries.values())
                )
                if all_non_volcanic:
                    phase_assessed = self._run_algorithmic_e4(
                        active_sites, smr_keys, summary, audit,
                        criterion_id, phase_num, force_rerun,
                    )
                    phase_report = {
                        "phase": phase_num,
                        "criterion": prompt_key,
                        "criterion_id": criterion_id,
                        "assessed": phase_assessed,
                        "skipped_dedup": 0,
                        "eliminated": 0,
                        "remaining": len(active_sites),
                        "api_calls_saved_this_phase": phase_assessed,
                        "avg_enrichment_coverage_pct": round(avg_cov, 2),
                        "mode": "algorithmic",
                    }
                    summary.phase_reports.append(phase_report)
                    summary.api_calls_saved += phase_assessed
                    log.info("llm_phase_complete", **phase_report)
                    continue

                # --- Defer enrichment-starved criteria ---
                defer_info = DEFERRABLE_CRITERIA.get(prompt_key)
                if defer_info and not no_defer:
                    primary_fields = defer_info["primary_fields"]
                    primary_coverage = self._compute_primary_field_coverage(
                        active_sites, coverages, primary_fields,
                    )
                    if primary_coverage < _DEFER_COVERAGE_THRESHOLD:
                        deferred_count = self._defer_phase(
                            active_sites, smr_keys, summary, audit,
                            prompt_key, criterion_id, phase_num, defer_info,
                            force_rerun,
                        )
                        defer_record = {
                            "criterion": prompt_key,
                            "criterion_id": criterion_id,
                            "phase": phase_num,
                            "sites_deferred": deferred_count,
                            "primary_coverage_pct": round(primary_coverage * 100, 1),
                            "reason": defer_info["reason"],
                            "required_sources": defer_info["required_sources"],
                        }
                        summary.deferred_phases.append(defer_record)
                        audit.log_deferral(
                            criterion_id=criterion_id,
                            prompt_key=prompt_key,
                            phase=phase_num,
                            sites_deferred=deferred_count,
                            primary_coverage_pct=round(primary_coverage * 100, 1),
                            reason=defer_info["reason"],
                            required_sources=defer_info["required_sources"],
                        )
                        phase_report = {
                            "phase": phase_num,
                            "criterion": prompt_key,
                            "criterion_id": criterion_id,
                            "assessed": 0,
                            "skipped_dedup": 0,
                            "eliminated": 0,
                            "remaining": len(active_sites),
                            "api_calls_saved_this_phase": deferred_count,
                            "avg_enrichment_coverage_pct": round(avg_cov, 2),
                            "mode": "deferred",
                        }
                        summary.phase_reports.append(phase_report)
                        summary.api_calls_saved += deferred_count
                        log.info("llm_phase_complete", **phase_report)
                        continue

                # --- Standard LLM assessment ---
                tasks: list[tuple[uuid.UUID, str, asyncio.Task]] = []

                for sid, sd in list(active_sites.items()):
                    if not force_rerun:
                        with self._llm_session_factory() as sess:
                            existing = self._check_existing_assessment(sess, sid, prompt_key)
                        if existing:
                            phase_skipped += 1
                            summary.skipped += 1
                            log.info(
                                "llm_assess_skipped",
                                site_id=str(sid),
                                prompt_key=prompt_key,
                                phase=phase_num,
                                existing=existing,
                            )
                            audit.log_skip(
                                site_id=str(sid),
                                site_name=sd["name"],
                                criterion_id=criterion_id,
                                prompt_key=prompt_key,
                                skip_reason="definitive_verdict_exists",
                                existing_verdict=existing.get("verdict"),
                                existing_confidence=existing.get("confidence"),
                                existing_run_id=existing.get("run_id"),
                            )
                            if existing.get("verdict") == "fail":
                                remaining = EXCLUSIONARY_PRIORITY[phase_num:]
                                elim = EliminatedSite(
                                    site_id=sid,
                                    site_name=sd["name"],
                                    excluded_by_prompt_key=prompt_key,
                                    excluded_by_criterion_id=criterion_id,
                                    exclusion_justification=f"Pre-existing fail verdict (run {existing.get('run_id')})",
                                    phase_number=phase_num,
                                )
                                eliminated[sid] = elim
                                summary.excluded_sites.append(elim)
                                phase_eliminated_ids.append(sid)
                                self._persist_not_assessed(
                                    sid, prompt_key, criterion_id,
                                    remaining, smr_keys,
                                )
                                audit.log_elimination(
                                    site_id=str(sid),
                                    site_name=sd["name"],
                                    excluded_by_criterion=criterion_id,
                                    excluded_by_prompt_key=prompt_key,
                                    exclusion_verdict="fail",
                                    exclusion_justification=elim.exclusion_justification,
                                    remaining_criteria_skipped=remaining,
                                )
                            continue

                    site_context = build_context_for_criterion(sd["cached"], prompt_key)
                    coverage = coverages.get(sid) or compute_enrichment_coverage(sd["cached"], prompt_key)
                    cc = sd["cached"].get("country_code", "")
                    coro = self._assess_one(
                        client=client,
                        site_id=sid,
                        site_name=sd["name"],
                        site_context=site_context,
                        prompt_key=prompt_key,
                        smr_keys=smr_keys,
                        summary=summary,
                        enrichment_coverage=coverage,
                        country_code=cc,
                    )
                    tasks.append((sid, sd["name"], asyncio.ensure_future(coro)))
                    phase_assessed += 1

                if tasks:
                    await asyncio.gather(*(t for _, _, t in tasks))

                summary.total_calls += phase_assessed

                for sid, sname, _ in tasks:
                    if self._site_failed_all_smr(sid, criterion_id, smr_keys):
                        remaining = EXCLUSIONARY_PRIORITY[phase_num:]
                        justification = self._get_fail_justification(sid, criterion_id)
                        elim = EliminatedSite(
                            site_id=sid,
                            site_name=sname,
                            excluded_by_prompt_key=prompt_key,
                            excluded_by_criterion_id=criterion_id,
                            exclusion_justification=justification,
                            phase_number=phase_num,
                        )
                        eliminated[sid] = elim
                        summary.excluded_sites.append(elim)
                        phase_eliminated_ids.append(sid)
                        self._persist_not_assessed(
                            sid, prompt_key, criterion_id,
                            remaining, smr_keys,
                        )
                        self._persist_elimination_observation(
                            sid, criterion_id, prompt_key, justification,
                        )
                        audit.log_elimination(
                            site_id=str(sid),
                            site_name=sname,
                            excluded_by_criterion=criterion_id,
                            excluded_by_prompt_key=prompt_key,
                            exclusion_verdict="fail",
                            exclusion_justification=justification,
                            remaining_criteria_skipped=remaining,
                        )

                for eid in phase_eliminated_ids:
                    active_sites.pop(eid, None)

                remaining_after = len(active_sites)
                saved = len(phase_eliminated_ids) * (len(EXCLUSIONARY_PRIORITY) - phase_num)
                summary.api_calls_saved += saved

                phase_report = {
                    "phase": phase_num,
                    "criterion": prompt_key,
                    "criterion_id": criterion_id,
                    "assessed": phase_assessed,
                    "skipped_dedup": phase_skipped,
                    "eliminated": len(phase_eliminated_ids),
                    "remaining": remaining_after,
                    "api_calls_saved_this_phase": saved,
                    "avg_enrichment_coverage_pct": round(avg_cov, 2),
                    "mode": "llm",
                    "second_pass_eligible": prompt_key in _SECOND_PASS_ELIGIBLE,
                }
                summary.phase_reports.append(phase_report)

                log.info(
                    "llm_phase_complete",
                    **phase_report,
                )

        summary.elapsed_s = time.monotonic() - t0
        audit.write_summary(summary.to_dict())
        audit.flush_index()

        log.info("llm_sequential_complete", **summary.to_dict())
        return summary

    def _site_failed_all_smr(
        self,
        site_id: uuid.UUID,
        criterion_id: str,
        smr_keys: list[str],
    ) -> bool:
        """True if every SMR design for this site+criterion has verdict='fail'."""
        with self._llm_session_factory() as session:
            fail_count = (
                session.query(ScreeningVerdict)
                .filter_by(site_id=site_id, criterion_id=criterion_id)
                .filter(ScreeningVerdict.verdict == "fail")
                .filter(ScreeningVerdict.smr_key.in_(smr_keys))
                .count()
            )
        return fail_count >= len(smr_keys)

    def _get_fail_justification(self, site_id: uuid.UUID, criterion_id: str) -> str:
        with self._llm_session_factory() as session:
            row = (
                session.query(ScreeningVerdict)
                .filter_by(site_id=site_id, criterion_id=criterion_id)
                .filter(ScreeningVerdict.verdict == "fail")
                .first()
            )
        if row:
            return row.justification[:500]
        return "Failed all SMR designs"

    def _persist_not_assessed(
        self,
        site_id: uuid.UUID,
        failed_prompt_key: str,
        failed_criterion_id: str,
        remaining_keys: list[str],
        smr_keys: list[str],
    ) -> None:
        """Write not_assessed verdicts for all remaining criteria after elimination."""
        now = datetime.now(timezone.utc)
        with self._llm_session_factory() as session:
            for rk in remaining_keys:
                rk_schema = PROMPT_REGISTRY[rk]
                rk_criterion = rk_schema.model_fields["criterion_id"].default
                for smr_key in smr_keys:
                    existing = session.query(ScreeningVerdict).filter_by(
                        site_id=site_id, smr_key=smr_key,
                        criterion_id=rk_criterion, prompt_key=rk,
                        run_id=self._run_id,
                    ).first()
                    justification = (
                        f"Site excluded by {failed_prompt_key} ({failed_criterion_id}). "
                        f"No further research warranted. "
                        f"Per SSG-35: a single exclusionary failure renders the site unsuitable."
                    )
                    if existing:
                        existing.verdict = "not_assessed"
                        existing.justification = justification
                        existing.confidence = "high"
                        existing.screened_at = now
                    else:
                        session.add(ScreeningVerdict(
                            site_id=site_id,
                            smr_key=smr_key,
                            criterion_id=rk_criterion,
                            prompt_key=rk,
                            phase="exclusionary",
                            verdict="not_assessed",
                            justification=justification,
                            confidence="high",
                            data_sources=[f"short_circuit:{failed_prompt_key}"],
                            run_id=self._run_id,
                        ))
            session.commit()

    def _persist_elimination_observation(
        self,
        site_id: uuid.UUID,
        criterion_id: str,
        prompt_key: str,
        justification: str,
    ) -> None:
        try:
            with self._llm_session_factory() as session:
                write_observation(
                    session,
                    site_id=site_id,
                    criterion_id=criterion_id,
                    observation=(
                        f"[SITE ELIMINATED] Excluded by {prompt_key} ({criterion_id}). "
                        f"{justification[:400]} "
                        f"No further research warranted."
                    ),
                    run_id=self._run_id,
                    source_type="llm",
                    impact="negative",
                    confidence="high",
                    author="sequential_elimination",
                )
                session.commit()
        except Exception:
            log.error("elimination_observation_failed", site_id=str(site_id))

    # ---------------------------------------------------------------
    # Algorithmic E4 (Volcanism) for non-volcanic countries
    # ---------------------------------------------------------------

    def _run_algorithmic_e4(
        self,
        active_sites: dict[uuid.UUID, dict[str, Any]],
        smr_keys: list[str],
        summary: AssessmentSummary,
        audit: AuditLogger,
        criterion_id: str,
        phase_num: int,
        force_rerun: bool,
    ) -> int:
        """Write algorithmic pass verdicts for E4 in non-volcanic countries."""
        now = datetime.now(timezone.utc)
        assessed = 0
        justification = (
            "ALGORITHMIC DETERMINATION: Site country has zero Holocene volcanism. "
            "No volcanic eruptions recorded in the Holocene (~11,700 years). "
            "Per SSG-35 Table I-1: no volcanic hazard zone exists. "
            "FACT: Country-level geological impossibility — confident pass."
        )
        with self._llm_session_factory() as session:
            for sid, sd in list(active_sites.items()):
                if not force_rerun:
                    existing = self._check_existing_assessment(session, sid, "E4")
                    if existing:
                        summary.skipped += 1
                        audit.log_skip(
                            site_id=str(sid), site_name=sd["name"],
                            criterion_id=criterion_id, prompt_key="E4",
                            skip_reason="definitive_verdict_exists",
                            existing_verdict=existing.get("verdict"),
                            existing_confidence=existing.get("confidence"),
                            existing_run_id=existing.get("run_id"),
                        )
                        continue

                for smr_key in smr_keys:
                    existing_v = session.query(ScreeningVerdict).filter_by(
                        site_id=sid, smr_key=smr_key, criterion_id=criterion_id,
                        prompt_key="E4", run_id=self._run_id,
                    ).first()
                    if existing_v:
                        existing_v.verdict = "pass"
                        existing_v.justification = justification
                        existing_v.confidence = "high"
                        existing_v.data_sources = ["algorithmic:non_volcanic_country"]
                        existing_v.screened_at = now
                    else:
                        session.add(ScreeningVerdict(
                            site_id=sid, smr_key=smr_key,
                            criterion_id=criterion_id, prompt_key="E4",
                            phase="exclusionary", verdict="pass",
                            justification=justification, confidence="high",
                            data_sources=["algorithmic:non_volcanic_country"],
                            run_id=self._run_id,
                        ))
                session.commit()

                summary.record_verdict(criterion_id, "pass", "high")
                summary.succeeded += 1
                assessed += 1

                audit.log_skip(
                    site_id=str(sid), site_name=sd["name"],
                    criterion_id=criterion_id, prompt_key="E4",
                    skip_reason="algorithmic_pass:non_volcanic_country",
                )

                log.info(
                    "algorithmic_e4_pass",
                    site=sd["name"], site_id=str(sid),
                    country=sd["cached"].get("country_code"),
                )

        return assessed

    # ---------------------------------------------------------------
    # Deferral helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _compute_primary_field_coverage(
        active_sites: dict[uuid.UUID, dict[str, Any]],
        coverages: dict[uuid.UUID, dict[str, Any]],
        primary_fields: set[str],
    ) -> float:
        """Fraction of active sites that have at least ONE primary enrichment field."""
        if not active_sites:
            return 0.0
        has_primary = 0
        for sid in active_sites:
            available = set(coverages.get(sid, {}).get("available_fields", []))
            if available & primary_fields:
                has_primary += 1
        return has_primary / len(active_sites)

    def _defer_phase(
        self,
        active_sites: dict[uuid.UUID, dict[str, Any]],
        smr_keys: list[str],
        summary: AssessmentSummary,
        audit: AuditLogger,
        prompt_key: str,
        criterion_id: str,
        phase_num: int,
        defer_info: dict[str, Any],
        force_rerun: bool,
    ) -> int:
        """Write deferred verdicts for all active sites on this criterion."""
        now = datetime.now(timezone.utc)
        deferred_count = 0
        justification = (
            f"DEFERRED: Enrichment data required for reliable assessment. "
            f"Reason: {defer_info['reason']}. "
            f"Required data sources: {', '.join(defer_info['required_sources'])}. "
            f"Assessment will be performed when API enrichment pipeline provides "
            f"the necessary data fields."
        )

        with self._llm_session_factory() as session:
            for sid, sd in list(active_sites.items()):
                if not force_rerun:
                    existing = self._check_existing_assessment(session, sid, prompt_key)
                    if existing:
                        summary.skipped += 1
                        audit.log_skip(
                            site_id=str(sid), site_name=sd["name"],
                            criterion_id=criterion_id, prompt_key=prompt_key,
                            skip_reason="definitive_verdict_exists",
                            existing_verdict=existing.get("verdict"),
                            existing_confidence=existing.get("confidence"),
                            existing_run_id=existing.get("run_id"),
                        )
                        continue

                for smr_key in smr_keys:
                    existing_v = session.query(ScreeningVerdict).filter_by(
                        site_id=sid, smr_key=smr_key, criterion_id=criterion_id,
                        prompt_key=prompt_key, run_id=self._run_id,
                    ).first()
                    if existing_v:
                        existing_v.verdict = "deferred"
                        existing_v.justification = justification
                        existing_v.confidence = "low"
                        existing_v.data_sources = [f"deferred:{','.join(defer_info['required_sources'])}"]
                        existing_v.screened_at = now
                    else:
                        session.add(ScreeningVerdict(
                            site_id=sid, smr_key=smr_key,
                            criterion_id=criterion_id, prompt_key=prompt_key,
                            phase="exclusionary", verdict="deferred",
                            justification=justification, confidence="low",
                            data_sources=[f"deferred:{','.join(defer_info['required_sources'])}"],
                            run_id=self._run_id,
                        ))
                session.commit()

                summary.record_verdict(criterion_id, "deferred", "low")
                deferred_count += 1

                audit.log_skip(
                    site_id=str(sid), site_name=sd["name"],
                    criterion_id=criterion_id, prompt_key=prompt_key,
                    skip_reason=f"deferred:enrichment_required",
                )

                log.info(
                    "llm_criterion_deferred",
                    site=sd["name"], site_id=str(sid),
                    criterion=prompt_key, reason=defer_info["reason"],
                )

        return deferred_count

    # ---------------------------------------------------------------
    # Second pass (Opus)
    # ---------------------------------------------------------------

    async def run_second_pass(
        self,
        candidates: list[SecondPassCandidate],
    ) -> AssessmentSummary:
        """Re-run selected Tier 1 assessments with the upgrade model (Opus)."""
        t0 = time.monotonic()
        smr_keys = self._load_smr_keys()
        if not smr_keys:
            smr_keys = ["nuscale_voygr6"]

        run_id = f"{self._run_id}:opus"
        summary = AssessmentSummary(
            run_id=run_id,
            total_sites=len({c.site_id for c in candidates}),
            total_calls=len(candidates),
        )

        site_cache_by_id = {sd["site_id"]: sd for sd in self._site_data_cache}

        upgrade_config = LlmConfig(
            provider=self._llm_config.provider,
            api_key=self._llm_config.api_key,
            database_profile=self._llm_config.database_profile,
            model_tier1=self._llm_config.model_tier1_upgrade,
            model_tier2=self._llm_config.model_tier2,
            model_tier3=self._llm_config.model_tier3,
            tier1_thinking_budget=self._llm_config.tier1_upgrade_thinking_budget,
            temperature=self._llm_config.temperature,
            max_tokens=self._llm_config.max_tokens,
            max_tokens_tier1=self._llm_config.max_tokens_tier1_upgrade,
            max_tokens_tier2=self._llm_config.max_tokens_tier2,
            max_tokens_tier3=self._llm_config.max_tokens_tier3,
            max_concurrent=self._llm_config.max_concurrent_upgrade,
            rps=self._llm_config.rps_upgrade,
            timeout_s=self._llm_config.timeout_s_upgrade,
            retry=self._llm_config.retry,
            few_shot_examples=self._llm_config.few_shot_examples,
        )

        async with AnthropicLlmClient(upgrade_config, run_id=self._run_id) as client:
            tasks = []
            for cand in candidates:
                sd = site_cache_by_id.get(cand.site_id)
                if sd is None:
                    log.warning(
                        "second_pass_site_not_cached",
                        site_id=str(cand.site_id),
                        prompt_key=cand.prompt_key,
                    )
                    continue
                site_context = build_context_for_criterion(sd["cached"], cand.prompt_key)
                coverage = compute_enrichment_coverage(sd["cached"], cand.prompt_key)
                cc = sd["cached"].get("country_code", "")
                tasks.append(
                    self._assess_one(
                        client=client,
                        site_id=cand.site_id,
                        site_name=cand.site_name,
                        site_context=site_context,
                        prompt_key=cand.prompt_key,
                        smr_keys=smr_keys,
                        summary=summary,
                        override_run_id=run_id,
                        enrichment_coverage=coverage,
                        country_code=cc,
                    )
                )
            await asyncio.gather(*tasks)

        for cand in candidates:
            with self._llm_session_factory() as sess:
                new_row = (
                    sess.query(ScreeningVerdict)
                    .filter_by(
                        site_id=cand.site_id,
                        criterion_id=cand.criterion_id,
                        run_id=run_id,
                    )
                    .first()
                )
                if new_row:
                    new_v = new_row.verdict
                    new_c = new_row.confidence
                    if new_v != cand.verdict or new_c != cand.confidence:
                        summary.second_pass_upgrades.append({
                            "site_name": cand.site_name,
                            "criterion_id": cand.criterion_id,
                            "prompt_key": cand.prompt_key,
                            "old_verdict": cand.verdict,
                            "old_confidence": cand.confidence,
                            "new_verdict": new_v,
                            "new_confidence": new_c,
                        })

        summary.elapsed_s = time.monotonic() - t0
        log.info("llm_second_pass_complete", **summary.to_dict())
        return summary

    # ---------------------------------------------------------------
    # Core assessment — single site × criterion
    # ---------------------------------------------------------------

    async def _assess_one(
        self,
        *,
        client: AnthropicLlmClient,
        site_id: uuid.UUID,
        site_name: str,
        site_context: str,
        prompt_key: str,
        smr_keys: list[str],
        summary: AssessmentSummary,
        override_run_id: str | None = None,
        enrichment_coverage: dict[str, Any] | None = None,
        country_code: str = "",
    ) -> None:
        """Assess a single criterion for a single site."""
        schema_cls = PROMPT_REGISTRY[prompt_key]
        tier = schema_cls.model_fields.get("tier")
        tier_val = tier.default if tier else 3

        system_prompt = get_prompt(prompt_key)
        tool = schema_cls.anthropic_tool()
        criterion_id = schema_cls.model_fields["criterion_id"].default
        prompt_ver = get_prompt_version(prompt_key)

        effective_run_id = override_run_id or self._run_id

        upgrade_thinking = None
        if (
            enrichment_coverage is not None
            and prompt_key in HIGH_DISCRIMINATION_CRITERIA
            and enrichment_coverage.get("coverage_pct", 1.0) < _ENRICHMENT_UPGRADE_THRESHOLD
            and override_run_id is None
            and tier_val == TIER_EXCLUSIONARY
        ):
            upgrade_thinking = self._llm_config.tier1_upgrade_thinking_budget
            log.info(
                "llm_auto_upgrade_model",
                site_id=str(site_id),
                prompt_key=prompt_key,
                coverage_pct=enrichment_coverage.get("coverage_pct"),
                reason="low enrichment on high-discrimination criterion",
            )

        try:
            result = await client.assess(
                system_prompt=system_prompt,
                user_message=site_context,
                tool=tool,
                tier=tier_val,
                site_id=str(site_id),
                site_name=site_name,
                criterion_id=criterion_id,
                prompt_key=prompt_key,
                prompt_version=prompt_ver,
                enrichment_coverage=enrichment_coverage,
                thinking_budget_override=upgrade_thinking,
            )
        except LlmAssessmentError as exc:
            summary.failed += 1
            summary.errors.append({
                "site_id": str(site_id),
                "site_name": site_name,
                "prompt_key": prompt_key,
                "error": str(exc),
            })
            log.warning(
                "llm_assess_failed",
                site_id=str(site_id),
                prompt_key=prompt_key,
                error=str(exc),
            )
            self._persist_error(site_id, criterion_id, prompt_key, str(exc), smr_keys)
            return

        def _do_persist() -> None:
            with self._llm_session_factory() as session:
                persist_result(
                    session,
                    site_id=site_id,
                    prompt_key=prompt_key,
                    result=result,
                    run_id=effective_run_id,
                    smr_keys=smr_keys,
                )
                session.commit()

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, _do_persist)
            summary.succeeded += 1
        except Exception as exc:
            summary.failed += 1
            summary.errors.append({
                "site_id": str(site_id),
                "site_name": site_name,
                "prompt_key": prompt_key,
                "error": f"persist error: {exc}",
            })
            log.error(
                "llm_persist_error",
                site_id=str(site_id),
                prompt_key=prompt_key,
                error=str(exc),
            )
            self._save_persist_error(site_id, site_name, prompt_key, criterion_id, result)
            return

        verdict = result.get("verdict", "")
        confidence = result.get("confidence", "")
        summary.record_verdict(criterion_id, verdict, confidence)
        summary.record_sources_needed(result.get("sources_needed"))
        if country_code:
            summary.record_country_verdict(country_code, verdict, confidence)

        usage = result.get("_usage", {})
        if usage:
            summary.record_tokens(
                criterion_id,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            )

        if (
            tier_val == TIER_EXCLUSIONARY
            and override_run_id is None
            and prompt_key in _SECOND_PASS_ELIGIBLE
        ):
            is_candidate, filter_reason = _is_second_pass_candidate(result, prompt_key)
            v = result.get("verdict", "")
            c = result.get("confidence", "")
            if is_candidate and (v == "inconclusive" or c == "low"):
                reason = _second_pass_reason(result)
                summary.second_pass_candidates.append(
                    SecondPassCandidate(
                        site_id=site_id,
                        site_name=site_name,
                        prompt_key=prompt_key,
                        criterion_id=criterion_id,
                        verdict=v or "inconclusive",
                        confidence=c or "low",
                        reason=reason,
                    )
                )
            elif filter_reason and client.audit:
                client.audit.log_second_pass_filtered(
                    site_id=str(site_id),
                    site_name=site_name,
                    criterion_id=criterion_id,
                    prompt_key=prompt_key,
                    verdict=v,
                    confidence=c,
                    reason=filter_reason,
                )

    def _save_persist_error(
        self,
        site_id: uuid.UUID,
        site_name: str,
        prompt_key: str,
        criterion_id: str,
        result: dict[str, Any],
    ) -> None:
        """Write raw LLM result JSON so data is recoverable after persist failures."""
        try:
            base = Path("logs/llm") / self._run_id / "persist_errors"
            base.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            fname = f"{ts}_{str(site_id)[:8]}_{criterion_id}.json"
            payload = {
                "site_id": str(site_id),
                "site_name": site_name,
                "prompt_key": prompt_key,
                "criterion_id": criterion_id,
                "run_id": self._run_id,
                "timestamp": ts,
                "raw_result": result,
            }
            (base / fname).write_text(
                json.dumps(payload, indent=2, default=str), encoding="utf-8"
            )
            log.info(
                "persist_error_saved",
                site_id=str(site_id),
                criterion_id=criterion_id,
                path=str(base / fname),
            )
        except Exception:
            log.error(
                "persist_error_save_failed",
                site_id=str(site_id),
                criterion_id=criterion_id,
            )

    def _persist_error(
        self,
        site_id: uuid.UUID,
        criterion_id: str,
        prompt_key: str,
        error_msg: str,
        smr_keys: list[str],
    ) -> None:
        try:
            with self._llm_session_factory() as session:
                write_observation(
                    session,
                    site_id=site_id,
                    criterion_id=criterion_id,
                    observation=f"[LLM ERROR] {prompt_key}: {error_msg[:500]}",
                    run_id=self._run_id,
                    source_type="llm_error",
                    impact="negative",
                    confidence="low",
                )
                session.commit()
        except Exception:
            log.error("llm_error_persist_failed", site_id=str(site_id), prompt_key=prompt_key)


_STRUCTURED_FIELDS_BY_PROMPT: dict[str, list[str]] = {
    "E3": ["slope_angle_deg", "slope_stability_class"],
    "E5": ["karst_present", "karst_severity"],
    "E6": ["mining_void_present", "subsidence_risk_class", "collapse_mechanism"],
    "E9": ["cooling_source_type", "cooling_source_name"],
}


def _is_second_pass_candidate(result: dict[str, Any], prompt_key: str = "") -> tuple[bool, str]:
    """Check if a result warrants Opus second pass.

    Returns (is_candidate, filter_reason). filter_reason is non-empty
    only when the candidate is rejected by the smart filter.
    """
    verdict = result.get("verdict", "")
    confidence = result.get("confidence", "")
    if verdict not in ("inconclusive",) and confidence not in ("low",):
        return False, ""

    fields = _STRUCTURED_FIELDS_BY_PROMPT.get(prompt_key, [])
    if fields:
        has_any_data = any(result.get(f) is not None for f in fields)
        if not has_any_data and verdict == "inconclusive":
            justification = (result.get("justification") or "").lower()
            skip_phrases = [
                "site-specific investigation",
                "site-specific geological",
                "site-specific geotechnical",
                "cannot be determined from available",
                "requires detailed",
            ]
            matched = [p for p in skip_phrases if p in justification]
            if matched:
                return False, f"all structured fields null; justification matches: {matched[0]}"

    return True, ""


def _second_pass_reason(result: dict[str, Any]) -> str:
    verdict = result.get("verdict", "")
    confidence = result.get("confidence", "")
    parts: list[str] = []
    if verdict == "inconclusive":
        parts.append("verdict=inconclusive")
    if confidence == "low":
        parts.append("confidence=low")
    return "; ".join(parts)
