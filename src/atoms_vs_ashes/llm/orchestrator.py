"""Async orchestrator — fans out LLM assessments across sites and criteria."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import SmrDesign
from atoms_vs_ashes.llm.client import AnthropicLlmClient, LlmAssessmentError
from atoms_vs_ashes.llm.config import LlmConfig
from atoms_vs_ashes.llm.context import build_context_for_criterion, load_sites, preload_site_data
from atoms_vs_ashes.llm.persist import persist_result
from atoms_vs_ashes.llm.prompts import get_prompt
from atoms_vs_ashes.llm.schemas import (
    ALL_KEYS,
    AVOIDANCE_KEYS,
    EXCLUSIONARY_KEYS,
    PROMPT_REGISTRY,
    RANKING_KEYS,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


@dataclass
class AssessmentSummary:
    """Aggregated results for a full LLM assessment run."""

    run_id: str = ""
    total_sites: int = 0
    total_calls: int = 0
    succeeded: int = 0
    failed: int = 0
    elapsed_s: float = 0.0
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_sites": self.total_sites,
            "total_calls": self.total_calls,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "elapsed_s": round(self.elapsed_s, 1),
            "error_count": len(self.errors),
            "errors": self.errors[:20],
        }


class LlmOrchestrator:
    """Batch orchestrator for LLM siting assessments.

    Reads sites from the main DB, fires concurrent LLM calls per site per
    criterion, and writes results to the LLM DB.
    """

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

    async def run(
        self,
        *,
        tier: str = "all",
        site_ids: list[uuid.UUID] | None = None,
        country_codes: list[str] | None = None,
        dry_run: bool = False,
    ) -> AssessmentSummary:
        """Execute the full LLM assessment pipeline."""
        t0 = time.monotonic()
        keys = self._select_keys(tier)
        smr_keys = self._load_smr_keys()

        if not smr_keys:
            log.warning("llm_no_smr_designs", msg="No SMR designs in LLM DB. Run Alembic migrations first.")
            smr_keys = ["nuscale_voygr6"]

        with self._main_session_factory() as session:
            sites = load_sites(session, site_ids=site_ids, country_codes=country_codes)
            site_data = [
                {
                    "site_id": s.site_id,
                    "name": s.name,
                    "cached": preload_site_data(s, session),
                }
                for s in sites
            ]

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

        async with AnthropicLlmClient(self._llm_config) as client:
            tasks = []
            for sd in site_data:
                for key in keys:
                    site_context = build_context_for_criterion(sd["cached"], key)
                    tasks.append(
                        self._assess_one(
                            client=client,
                            site_id=sd["site_id"],
                            site_name=sd["name"],
                            site_context=site_context,
                            prompt_key=key,
                            smr_keys=smr_keys,
                            summary=summary,
                        )
                    )
            await asyncio.gather(*tasks)

        summary.elapsed_s = time.monotonic() - t0
        log.info("llm_run_complete", **summary.to_dict())
        return summary

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
    ) -> None:
        """Assess a single criterion for a single site."""
        schema_cls = PROMPT_REGISTRY[prompt_key]
        tier = schema_cls.model_fields.get("tier")
        tier_val = tier.default if tier else 3

        system_prompt = get_prompt(prompt_key)
        tool = schema_cls.anthropic_tool()
        criterion_id = schema_cls.model_fields["criterion_id"].default

        try:
            result = await client.assess(
                system_prompt=system_prompt,
                user_message=site_context,
                tool=tool,
                tier=tier_val,
                site_id=str(site_id),
                criterion_id=criterion_id,
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

        with self._llm_session_factory() as session:
            try:
                persist_result(
                    session,
                    site_id=site_id,
                    prompt_key=prompt_key,
                    result=result,
                    run_id=self._run_id,
                    smr_keys=smr_keys,
                )
                session.commit()
                summary.succeeded += 1
            except Exception as exc:
                session.rollback()
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

    def _persist_error(
        self,
        site_id: uuid.UUID,
        criterion_id: str,
        prompt_key: str,
        error_msg: str,
        smr_keys: list[str],
    ) -> None:
        """Write an error observation so failures are tracked in the DB."""
        from atoms_vs_ashes.analysis._provenance import write_observation

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
