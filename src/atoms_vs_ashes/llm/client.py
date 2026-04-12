"""Async Anthropic API client with retry, rate-limiting, and tiered model selection."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import anthropic

from atoms_vs_ashes.llm.config import TIER_EXCLUSIONARY, LlmConfig
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


class _TokenBucketRateLimiter:
    """Simple async token-bucket for requests-per-second throttling."""

    def __init__(self, rps: float) -> None:
        self._rps = rps
        self._interval = 1.0 / rps
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


class AnthropicLlmClient:
    """Async wrapper around the Anthropic Messages API.

    Provides tiered model selection, extended thinking for exclusionary
    criteria, concurrency bounding via semaphore, and RPS rate-limiting.
    """

    def __init__(self, config: LlmConfig) -> None:
        if not config.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Export it or add llm.api_key to config/default.yml."
            )
        self._config = config
        self._client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            max_retries=config.retry.max_retries,
            timeout=config.timeout_s,
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._rate_limiter = _TokenBucketRateLimiter(config.rps)

    async def assess(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tool: dict[str, Any],
        tier: int,
        site_id: str = "",
        criterion_id: str = "",
        thinking_budget_override: int | None = None,
    ) -> dict[str, Any]:
        """Send a single criterion assessment request and return parsed tool input.

        Raises ``LlmAssessmentError`` on unrecoverable failure.
        """
        model = self._config.model_for_tier(tier)
        use_thinking = tier == TIER_EXCLUSIONARY
        max_tokens = self._config.max_tokens_for_tier(tier)

        messages = [{"role": "user", "content": user_message}]
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": tool["name"]},
        }

        if use_thinking:
            thinking_budget = thinking_budget_override or self._config.tier1_thinking_budget
            # API requires max_tokens >= thinking budget_tokens
            kwargs["max_tokens"] = max(max_tokens, thinking_budget + 4096)
            kwargs["temperature"] = 1.0  # required by API when thinking is enabled
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
        else:
            kwargs["temperature"] = self._config.temperature

        async with self._semaphore:
            await self._rate_limiter.acquire()
            t0 = time.monotonic()
            try:
                response = await self._client.messages.create(**kwargs)
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                log.info(
                    "llm_assess_ok",
                    site_id=site_id,
                    criterion_id=criterion_id,
                    model=model,
                    elapsed_ms=elapsed_ms,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            except anthropic.APIError as exc:
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                log.error(
                    "llm_assess_error",
                    site_id=site_id,
                    criterion_id=criterion_id,
                    model=model,
                    elapsed_ms=elapsed_ms,
                    error=str(exc),
                )
                raise LlmAssessmentError(
                    f"API error for {criterion_id} on site {site_id}: {exc}"
                ) from exc

        thinking_text = ""
        tool_input: dict[str, Any] = {}

        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
            elif block.type == "tool_use":
                tool_input = block.input

        if not tool_input:
            raise LlmAssessmentError(
                f"No tool_use block in response for {criterion_id} on site {site_id}"
            )

        tool_input["_thinking"] = thinking_text
        tool_input["_model"] = model
        tool_input["_input_tokens"] = response.usage.input_tokens
        tool_input["_output_tokens"] = response.usage.output_tokens
        return tool_input

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> AnthropicLlmClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


class LlmAssessmentError(Exception):
    """Raised when an LLM assessment call fails after retries."""
