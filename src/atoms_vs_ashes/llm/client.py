"""Async Anthropic API client with retry, rate-limiting, and tiered model selection."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import anthropic

from atoms_vs_ashes.llm.audit_log import AuditLogger
from atoms_vs_ashes.llm.config import TIER_EXCLUSIONARY, LlmConfig
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

_MODEL_OUTPUT_CAPS: dict[str, int] = {
    "claude-opus-4-20250514": 32_000,
    "claude-sonnet-4-20250514": 64_000,
    "claude-haiku-3.5-20250401": 8_192,
}


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

    def __init__(self, config: LlmConfig, *, run_id: str = "") -> None:
        if not config.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Export it or add llm.api_key to config/default.yml."
            )
        self._config = config
        self._run_id = run_id
        self._client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            max_retries=config.retry.max_retries,
            timeout=config.timeout_s,
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._rate_limiter = _TokenBucketRateLimiter(config.rps)
        self.audit = AuditLogger(run_id) if run_id else None

    async def assess(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tool: dict[str, Any],
        tier: int,
        site_id: str = "",
        site_name: str = "",
        criterion_id: str = "",
        prompt_key: str = "",
        prompt_version: str = "",
        thinking_budget_override: int | None = None,
        enrichment_coverage: dict[str, Any] | None = None,
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
            model_cap = _MODEL_OUTPUT_CAPS.get(model, 128_000)
            computed = max(max_tokens, thinking_budget + 4096)
            kwargs["max_tokens"] = min(computed, model_cap)
            if thinking_budget >= kwargs["max_tokens"]:
                thinking_budget = kwargs["max_tokens"] - 4096
            kwargs["temperature"] = 1.0
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
            kwargs["tool_choice"] = {"type": "auto"}
        else:
            kwargs["temperature"] = self._config.temperature

        request_event_id: str | None = None
        if self.audit:
            request_event_id = self.audit.log_request(
                site_id=site_id,
                site_name=site_name,
                criterion_id=criterion_id,
                prompt_key=prompt_key,
                prompt_version=prompt_version,
                kwargs=kwargs,
                enrichment_coverage=enrichment_coverage,
            )

        _OVERLOAD_BACKOFFS = [5, 15, 45]

        async with self._semaphore:
            await self._rate_limiter.acquire()
            t0 = time.monotonic()
            response = None
            last_exc: anthropic.APIError | None = None

            for attempt in range(1 + len(_OVERLOAD_BACKOFFS)):
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
                        retry_attempt=attempt if attempt > 0 else None,
                    )
                    last_exc = None
                    break
                except anthropic.APIStatusError as exc:
                    if exc.status_code == 529 and attempt < len(_OVERLOAD_BACKOFFS):
                        wait = _OVERLOAD_BACKOFFS[attempt]
                        log.warning(
                            "llm_overloaded_retry",
                            site_id=site_id,
                            criterion_id=criterion_id,
                            attempt=attempt + 1,
                            backoff_s=wait,
                        )
                        await asyncio.sleep(wait)
                        last_exc = exc
                        continue
                    last_exc = exc
                    break
                except anthropic.APIError as exc:
                    last_exc = exc
                    break

            if last_exc is not None or response is None:
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                error_str = str(last_exc) if last_exc else "unknown error"
                log.error(
                    "llm_assess_error",
                    site_id=site_id,
                    criterion_id=criterion_id,
                    model=model,
                    elapsed_ms=elapsed_ms,
                    error=error_str,
                )
                if self.audit:
                    self.audit.log_response(
                        site_id=site_id,
                        site_name=site_name,
                        criterion_id=criterion_id,
                        prompt_key=prompt_key,
                        prompt_version=prompt_version,
                        elapsed_ms=elapsed_ms,
                        model=model,
                        error=error_str,
                        request_event_id=request_event_id,
                    )
                raise LlmAssessmentError(
                    f"API error for {criterion_id} on site {site_id}: {error_str}"
                ) from last_exc

        thinking_text = ""
        tool_input: dict[str, Any] = {}
        raw_content: list[dict[str, Any]] = []

        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
                raw_content.append({"type": "thinking", "thinking": thinking_text})
            elif block.type == "tool_use":
                tool_input = block.input
                raw_content.append({
                    "type": "tool_use", "id": block.id,
                    "name": block.name, "input": block.input,
                })
            elif block.type == "text":
                raw_content.append({"type": "text", "text": block.text})

        if self.audit:
            self.audit.log_response(
                site_id=site_id,
                site_name=site_name,
                criterion_id=criterion_id,
                prompt_key=prompt_key,
                prompt_version=prompt_version,
                elapsed_ms=elapsed_ms,
                model=model,
                response_content=raw_content,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                tool_input=tool_input if tool_input else None,
                request_event_id=request_event_id,
            )

        if not tool_input:
            raise LlmAssessmentError(
                f"No tool_use block in response for {criterion_id} on site {site_id}"
            )

        tool_input["_thinking"] = thinking_text
        tool_input["_model"] = model
        tool_input["_input_tokens"] = response.usage.input_tokens
        tool_input["_output_tokens"] = response.usage.output_tokens
        tool_input["_usage"] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return tool_input

    async def close(self) -> None:
        if self.audit:
            self.audit.flush_index()
        await self._client.close()

    async def __aenter__(self) -> AnthropicLlmClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


class LlmAssessmentError(Exception):
    """Raised when an LLM assessment call fails after retries."""
