"""Prompt registry — maps each criterion key to its system prompt."""

from __future__ import annotations

from typing import Any

from atoms_vs_ashes.llm.prompts._base import PROMPT_VERSION as BASE_VERSION
from atoms_vs_ashes.llm.prompts.avoidance import (
    AVOIDANCE_PROMPTS,
    PROMPT_VERSION as AVOIDANCE_VERSION,
)
from atoms_vs_ashes.llm.prompts.exclusionary import (
    EXCLUSIONARY_PROMPTS,
    PROMPT_VERSION as EXCLUSIONARY_VERSION,
)
from atoms_vs_ashes.llm.prompts.ranking import (
    RANKING_PROMPTS,
    PROMPT_VERSION as RANKING_VERSION,
)

ALL_PROMPTS: dict[str, str] = {
    **EXCLUSIONARY_PROMPTS,
    **AVOIDANCE_PROMPTS,
    **RANKING_PROMPTS,
}

PROMPT_VERSIONS: dict[str, str] = {
    "_base": BASE_VERSION,
    "exclusionary": EXCLUSIONARY_VERSION,
    "avoidance": AVOIDANCE_VERSION,
    "ranking": RANKING_VERSION,
}


def get_prompt(key: str) -> str:
    """Return the system prompt for a given criterion key (E1, A3, NH-01, etc.)."""
    if key not in ALL_PROMPTS:
        raise KeyError(f"No prompt registered for '{key}'. Available: {sorted(ALL_PROMPTS)}")
    return ALL_PROMPTS[key]


def get_prompt_version(key: str) -> str:
    """Return the version string for the module containing the given key."""
    if key.startswith("E"):
        return EXCLUSIONARY_VERSION
    if key.startswith("A"):
        return AVOIDANCE_VERSION
    return RANKING_VERSION
