"""Tests for the LLM assessment pipeline.

Unit tests cover prompt registry, schema validation, config loading,
and tool definition structure. Integration tests (gated) require
ANTHROPIC_API_KEY and a running database.
"""

from __future__ import annotations

import json
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atoms_vs_ashes.llm.config import (
    TIER_AVOIDANCE,
    TIER_EXCLUSIONARY,
    TIER_RANKING,
    LlmConfig,
)
from atoms_vs_ashes.llm.prompts import ALL_PROMPTS, get_prompt
from atoms_vs_ashes.llm.schemas import (
    ALL_KEYS,
    AVOIDANCE_KEYS,
    EXCLUSIONARY_KEYS,
    PROMPT_REGISTRY,
    RANKING_KEYS,
)


# ---------------------------------------------------------------------------
# Prompt registry completeness
# ---------------------------------------------------------------------------

class TestPromptRegistry:
    def test_all_schema_keys_have_prompts(self):
        """Every key in PROMPT_REGISTRY must have a corresponding prompt."""
        for key in PROMPT_REGISTRY:
            assert key in ALL_PROMPTS, f"Schema key {key} has no prompt"

    def test_all_prompt_keys_have_schemas(self):
        """Every key in ALL_PROMPTS must have a corresponding schema."""
        for key in ALL_PROMPTS:
            assert key in PROMPT_REGISTRY, f"Prompt key {key} has no schema"

    def test_exclusionary_count(self):
        assert len(EXCLUSIONARY_KEYS) == 9

    def test_avoidance_count(self):
        assert len(AVOIDANCE_KEYS) == 15

    def test_ranking_count(self):
        assert len(RANKING_KEYS) >= 22

    def test_total_prompts(self):
        assert len(ALL_KEYS) >= 46

    def test_get_prompt_returns_string(self):
        for key in ALL_KEYS:
            prompt = get_prompt(key)
            assert isinstance(prompt, str)
            assert len(prompt) > 100

    def test_get_prompt_invalid_key(self):
        with pytest.raises(KeyError):
            get_prompt("INVALID-99")


# ---------------------------------------------------------------------------
# Schema / tool definition structure
# ---------------------------------------------------------------------------

class TestSchemaToolDefinitions:
    def test_all_schemas_have_anthropic_tool(self):
        for key, cls in PROMPT_REGISTRY.items():
            tool = cls.anthropic_tool()
            assert "name" in tool, f"{key}: tool missing 'name'"
            assert "description" in tool, f"{key}: tool missing 'description'"
            assert "input_schema" in tool, f"{key}: tool missing 'input_schema'"
            schema = tool["input_schema"]
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

    def test_exclusionary_tools_have_verdict(self):
        for key in EXCLUSIONARY_KEYS:
            cls = PROMPT_REGISTRY[key]
            tool = cls.anthropic_tool()
            props = tool["input_schema"]["properties"]
            assert "verdict" in props
            assert "pass" in props["verdict"]["enum"]
            assert "fail" in props["verdict"]["enum"]

    def test_avoidance_tools_have_verdict(self):
        for key in AVOIDANCE_KEYS:
            cls = PROMPT_REGISTRY[key]
            tool = cls.anthropic_tool()
            props = tool["input_schema"]["properties"]
            assert "verdict" in props
            assert "caution" in props["verdict"]["enum"]

    def test_ranking_tools_have_score(self):
        for key in RANKING_KEYS:
            cls = PROMPT_REGISTRY[key]
            tool = cls.anthropic_tool()
            props = tool["input_schema"]["properties"]
            assert "score" in props
            assert props["score"]["minimum"] == 1
            assert props["score"]["maximum"] == 5

    def test_all_tools_have_confidence(self):
        for key, cls in PROMPT_REGISTRY.items():
            tool = cls.anthropic_tool()
            props = tool["input_schema"]["properties"]
            assert "confidence" in props, f"{key}: missing confidence"

    def test_all_tools_have_justification(self):
        for key, cls in PROMPT_REGISTRY.items():
            tool = cls.anthropic_tool()
            props = tool["input_schema"]["properties"]
            assert "justification" in props, f"{key}: missing justification"

    def test_tool_names_are_unique(self):
        names = []
        for cls in PROMPT_REGISTRY.values():
            tool = cls.anthropic_tool()
            names.append(tool["name"])
        assert len(names) == len(set(names)), "Duplicate tool names found"


# ---------------------------------------------------------------------------
# Schema tier assignment
# ---------------------------------------------------------------------------

class TestSchemaTiers:
    def test_exclusionary_schemas_are_tier1(self):
        for key in EXCLUSIONARY_KEYS:
            cls = PROMPT_REGISTRY[key]
            tier_field = cls.model_fields.get("tier")
            assert tier_field is not None
            assert tier_field.default == TIER_EXCLUSIONARY

    def test_avoidance_schemas_are_tier2(self):
        for key in AVOIDANCE_KEYS:
            cls = PROMPT_REGISTRY[key]
            tier_field = cls.model_fields.get("tier")
            assert tier_field is not None
            assert tier_field.default == TIER_AVOIDANCE

    def test_ranking_schemas_are_tier3(self):
        for key in RANKING_KEYS:
            cls = PROMPT_REGISTRY[key]
            tier_field = cls.model_fields.get("tier")
            assert tier_field is not None
            assert tier_field.default == TIER_RANKING


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

class TestLlmConfig:
    def test_from_yaml_defaults(self):
        cfg = LlmConfig.from_yaml({})
        assert cfg.provider == "anthropic"
        assert cfg.max_concurrent == 50
        assert cfg.temperature == 0.0

    def test_from_yaml_override(self):
        raw = {
            "llm": {
                "max_concurrent": 10,
                "rps": 5,
                "models": {"tier3_ranking": "claude-haiku-3.5-custom"},
            }
        }
        cfg = LlmConfig.from_yaml(raw)
        assert cfg.max_concurrent == 10
        assert cfg.rps == 5.0
        assert cfg.model_tier3 == "claude-haiku-3.5-custom"

    def test_model_for_tier(self):
        cfg = LlmConfig()
        assert "sonnet" in cfg.model_for_tier(1)
        assert "haiku" in cfg.model_for_tier(3)

    def test_env_api_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            cfg = LlmConfig.from_yaml({})
            assert cfg.api_key == "test-key"


# ---------------------------------------------------------------------------
# Schema validation (Pydantic parsing)
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_exclusionary_valid(self):
        from atoms_vs_ashes.llm.schemas import E1CapableFault
        result = E1CapableFault(
            verdict="pass",
            confidence="high",
            justification="No capable faults in the region.",
            data_quality="medium",
            nearest_fault_km=50.0,
        )
        assert result.verdict == "pass"
        assert result.criterion_id == "NH-02"

    def test_ranking_valid(self):
        from atoms_vs_ashes.llm.schemas import NH01SeismicGM
        result = NH01SeismicGM(
            score=4,
            score_low=3,
            score_high=5,
            confidence="medium",
            justification="Low seismicity region.",
            data_quality="medium",
            pga_475yr_g=0.08,
        )
        assert result.score == 4
        assert result.criterion_id == "NH-01"

    def test_ranking_invalid_score(self):
        from atoms_vs_ashes.llm.schemas import NH01SeismicGM
        with pytest.raises(Exception):
            NH01SeismicGM(
                score=6,
                confidence="medium",
                justification="test",
                data_quality="medium",
            )


# ---------------------------------------------------------------------------
# DB column compatibility (criterion_id → domain table)
# ---------------------------------------------------------------------------

class TestPersistFieldMapping:
    def test_field_map_keys_are_valid_criteria(self):
        from atoms_vs_ashes.llm.persist import _FIELD_MAP
        from atoms_vs_ashes.llm.schemas import PROMPT_REGISTRY

        all_criterion_ids = set()
        for cls in PROMPT_REGISTRY.values():
            cid = cls.model_fields["criterion_id"].default
            all_criterion_ids.add(cid)

        for cid in _FIELD_MAP:
            assert cid in all_criterion_ids, f"_FIELD_MAP key {cid} is not a valid criterion_id"

    def test_quality_columns_match_criteria(self):
        from atoms_vs_ashes.llm.persist import _QUALITY_COL

        for cid, col in _QUALITY_COL.items():
            prefix = cid.lower().replace("-", "")
            assert col.startswith(prefix), f"Quality column {col} doesn't match criterion {cid}"

    def test_domain_table_map_covers_all_criteria(self):
        from atoms_vs_ashes.llm.persist import _DOMAIN_TABLE_MAP

        for cls in PROMPT_REGISTRY.values():
            cid = cls.model_fields["criterion_id"].default
            assert cid in _DOMAIN_TABLE_MAP, f"Criterion {cid} missing from _DOMAIN_TABLE_MAP"


# ---------------------------------------------------------------------------
# Integration test (gated — requires ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM test",
)
class TestLlmIntegration:
    @pytest.mark.asyncio
    async def test_single_ranking_call(self):
        """Smoke test — make one real API call for NH-10 (extreme winds)."""
        from atoms_vs_ashes.llm.client import AnthropicLlmClient
        from atoms_vs_ashes.llm.schemas import NH10ExtremeWinds

        cfg = LlmConfig.from_yaml({})
        async with AnthropicLlmClient(cfg) as client:
            result = await client.assess(
                system_prompt=get_prompt("NH-10"),
                user_message=(
                    "SITE: Rovinari Power Station\n"
                    "COUNTRY: Romania (RO)\n"
                    "COORDINATES: 44.15°N, 23.12°E\n"
                    "ELEVATION: 200 m AMSL\n"
                    "STATUS: operating\n"
                    "INSTALLED CAPACITY: 1320 MWe\n\n"
                    "Evaluate this site for the specified criterion. "
                    "Return your assessment using the provided tool."
                ),
                tool=NH10ExtremeWinds.anthropic_tool(),
                tier=TIER_RANKING,
                site_id="test-site-001",
                criterion_id="NH-10",
            )
            assert "score" in result
            assert 1 <= result["score"] <= 5
            assert "justification" in result
