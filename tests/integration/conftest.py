"""Integration test fixtures — require API keys."""

from __future__ import annotations

import os

import pytest

from hub_vs_spoke.agents.agent import Agent
from hub_vs_spoke.providers.anthropic_provider import AnthropicProvider
from hub_vs_spoke.providers.openai_provider import OpenAIProvider
from hub_vs_spoke.types import TokenBudget


def _has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _has_anthropic_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


skip_no_openai = pytest.mark.skipif(
    not _has_openai_key(), reason="OPENAI_API_KEY not set"
)
skip_no_anthropic = pytest.mark.skipif(
    not _has_anthropic_key(), reason="ANTHROPIC_API_KEY not set"
)
skip_no_keys = pytest.mark.skipif(
    not (_has_openai_key() and _has_anthropic_key()),
    reason="Both OPENAI_API_KEY and ANTHROPIC_API_KEY required",
)


@pytest.fixture
def openai_agent() -> Agent:
    return Agent(
        name="openai-agent",
        provider=OpenAIProvider(model="gpt-4o-mini"),
        system_prompt="You are a helpful assistant. Be concise.",
        max_tokens=512,
    )


@pytest.fixture
def anthropic_agent() -> Agent:
    return Agent(
        name="anthropic-agent",
        provider=AnthropicProvider(model="claude-3-5-haiku-20241022"),
        system_prompt="You are a helpful assistant. Be concise.",
        max_tokens=512,
    )


@pytest.fixture
def live_budget() -> TokenBudget:
    """Conservative budget for integration tests."""
    return TokenBudget(max_total_tokens=20_000, max_turns=15)
