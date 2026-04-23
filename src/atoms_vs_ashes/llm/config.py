"""LLM configuration: model tiers, rate limits, and retry policy."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LlmRetryConfig:
    max_retries: int = 3
    base_delay_s: float = 2.0
    max_delay_s: float = 60.0


@dataclass(frozen=True)
class LlmConfig:
    """Resolved LLM configuration from YAML + env vars."""

    provider: str = "anthropic"
    api_key: str | None = None
    database_profile: str = "llm"

    model_tier1: str = "claude-sonnet-4-20250514"
    model_tier2: str = "claude-sonnet-4-20250514"
    model_tier3: str = "claude-haiku-3.5-20250401"
    model_tier1_upgrade: str = "claude-opus-4-20250514"

    tier1_thinking_budget: int = 16_384
    tier1_upgrade_thinking_budget: int = 25_000
    temperature: float = 0.0
    max_tokens: int = 4096
    max_tokens_tier1: int = 16_384
    max_tokens_tier1_upgrade: int = 32_000
    max_tokens_tier2: int = 4096
    max_tokens_tier3: int = 2048
    max_concurrent: int = 50
    max_concurrent_upgrade: int = 10
    rps: float = 40.0
    rps_upgrade: float = 5.0
    timeout_s: int = 120
    timeout_s_upgrade: int = 300

    retry: LlmRetryConfig = field(default_factory=LlmRetryConfig)
    few_shot_examples: bool = True

    def __repr__(self) -> str:
        fields = {k: v for k, v in self.__dict__.items() if k != "api_key"}
        fields["api_key"] = "***REDACTED***" if self.api_key else None
        pairs = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        return f"LlmConfig({pairs})"

    @classmethod
    def from_yaml(cls, raw: dict[str, Any]) -> LlmConfig:
        """Build from the ``llm:`` section of config/default.yml."""
        llm = raw.get("llm", {})
        models = llm.get("models", {})
        retry_raw = llm.get("retry", {})
        retry = LlmRetryConfig(
            max_retries=retry_raw.get("max_retries", 3),
            base_delay_s=retry_raw.get("base_delay_s", 2.0),
            max_delay_s=retry_raw.get("max_delay_s", 60.0),
        )
        return cls(
            provider=llm.get("provider", "anthropic"),
            api_key=os.environ.get("ANTHROPIC_API_KEY") or llm.get("api_key"),
            database_profile=llm.get("database_profile", "llm"),
            model_tier1=models.get("tier1_exclusionary", cls.model_tier1),
            model_tier2=models.get("tier2_avoidance", cls.model_tier2),
            model_tier3=models.get("tier3_ranking", cls.model_tier3),
            model_tier1_upgrade=models.get("tier1_upgrade", cls.model_tier1_upgrade),
            tier1_thinking_budget=llm.get("tier1_thinking_budget", 16_384),
            tier1_upgrade_thinking_budget=llm.get("tier1_upgrade_thinking_budget", 32_768),
            temperature=llm.get("temperature", 0.0),
            max_tokens=llm.get("max_tokens", 4096),
            max_tokens_tier1=llm.get("max_tokens_tier1", 16_384),
            max_tokens_tier1_upgrade=llm.get("max_tokens_tier1_upgrade", 32_768),
            max_tokens_tier2=llm.get("max_tokens_tier2", 4096),
            max_tokens_tier3=llm.get("max_tokens_tier3", 2048),
            max_concurrent=llm.get("max_concurrent", 50),
            max_concurrent_upgrade=llm.get("max_concurrent_upgrade", 10),
            rps=llm.get("rps", 40.0),
            rps_upgrade=llm.get("rps_upgrade", 5.0),
            timeout_s=llm.get("timeout_s", 120),
            timeout_s_upgrade=llm.get("timeout_s_upgrade", 300),
            retry=retry,
            few_shot_examples=llm.get("few_shot_examples", True),
        )

    def model_for_tier(self, tier: int) -> str:
        return {1: self.model_tier1, 2: self.model_tier2, 3: self.model_tier3}[tier]

    def max_tokens_for_tier(self, tier: int) -> int:
        return {
            1: self.max_tokens_tier1,
            2: self.max_tokens_tier2,
            3: self.max_tokens_tier3,
        }[tier]


TIER_EXCLUSIONARY = 1
TIER_AVOIDANCE = 2
TIER_RANKING = 3
