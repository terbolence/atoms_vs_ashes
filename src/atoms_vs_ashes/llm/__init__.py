"""LLM-based siting assessment pipeline.

Provides specialist prompts, async orchestration, and database persistence
for evaluating all siting criteria via Anthropic Claude models.

Exports are lazy so ``import atoms_vs_ashes.llm.context`` (and standalone
scripts) do not pull in ``anthropic`` until client code is used.
"""

from __future__ import annotations

from typing import Any

__all__ = ["AnthropicLlmClient", "LlmOrchestrator"]


def __getattr__(name: str) -> Any:
    if name == "AnthropicLlmClient":
        from atoms_vs_ashes.llm.client import AnthropicLlmClient

        return AnthropicLlmClient
    if name == "LlmOrchestrator":
        from atoms_vs_ashes.llm.orchestrator import LlmOrchestrator

        return LlmOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
