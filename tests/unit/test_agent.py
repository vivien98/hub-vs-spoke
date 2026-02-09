"""Unit tests for Agent and MockAgent."""

from __future__ import annotations

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent


class TestMockAgent:
    """Verify MockAgent behaviour without any network calls."""

    @pytest.mark.asyncio
    async def test_returns_preconfigured_responses(self) -> None:
        agent = MockAgent(name="test", responses=["first", "second", "third"])

        r1 = await agent.act("hello")
        assert r1.content == "first"

        r2 = await agent.act("world")
        assert r2.content == "second"

    @pytest.mark.asyncio
    async def test_fallback_when_responses_exhausted(self) -> None:
        agent = MockAgent(name="bot", responses=["only-one"])

        r1 = await agent.act("a")
        assert r1.content == "only-one"

        r2 = await agent.act("b")
        assert "[bot]" in r2.content  # fallback includes agent name

    @pytest.mark.asyncio
    async def test_response_fn_overrides_list(self) -> None:
        agent = MockAgent(
            name="fn",
            responses=["ignored"],
            response_fn=lambda msg: f"echo: {msg}",
        )
        r = await agent.act("ping")
        assert r.content == "echo: ping"

    @pytest.mark.asyncio
    async def test_tracks_usage(self) -> None:
        agent = MockAgent(name="counter", tokens_per_call=50)

        await agent.act("one")
        assert agent.total_usage.input_tokens == 50
        assert agent.total_usage.output_tokens == 50

        await agent.act("two")
        assert agent.total_usage.input_tokens == 100
        assert agent.total_usage.output_tokens == 100

    @pytest.mark.asyncio
    async def test_reset_clears_state(self) -> None:
        agent = MockAgent(name="resettable", responses=["a", "b"])
        await agent.act("x")
        agent.reset()

        assert agent.total_usage.input_tokens == 0
        assert len(agent.history) == 0

        # After reset, index is back to 0
        r = await agent.act("y")
        assert r.content == "a"

    def test_model_name(self) -> None:
        agent = MockAgent(name="m", model_name="my-model")
        assert agent.model_name == "my-model"

    def test_cost_is_zero(self) -> None:
        agent = MockAgent(name="free")
        assert agent.total_cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_history_recorded(self) -> None:
        agent = MockAgent(name="hist", responses=["reply"])
        await agent.act("question")
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"
