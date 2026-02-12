"""Unit tests for the solo topology using mock agents."""

from __future__ import annotations

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent
from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies.solo import SoloTopology
from hub_vs_spoke.types import TokenBudget


@pytest.mark.asyncio
async def test_solo_returns_direct_answer(
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Solo topology returns the agent's direct answer."""
    agent = MockAgent(name="solo-agent", responses=["def add(a, b): return a + b"])
    topology = SoloTopology(agent=agent)

    result = await topology.run(simple_task, default_budget)

    assert result.topology_name == "solo"
    assert result.task_id == "test-001"
    assert result.final_answer == "def add(a, b): return a + b"
    assert result.total_tokens > 0
    assert len(result.turns) == 1
    assert result.turns[0].from_agent == "user"
    assert result.turns[0].to_agent == "solo-agent"
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_solo_name() -> None:
    agent = MockAgent(name="test")
    topology = SoloTopology(agent=agent)
    assert topology.name == "solo"


@pytest.mark.asyncio
async def test_solo_handles_failure(
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Solo topology records error when agent fails."""

    class FailingAgent:
        name = "fail-agent"

        async def act(self, msg: str) -> None:
            raise RuntimeError("Agent crashed!")

    topology = SoloTopology(agent=FailingAgent())  # type: ignore[arg-type]
    result = await topology.run(simple_task, default_budget)

    assert result.final_answer == ""
    assert len(result.errors) == 1
    assert "Agent crashed" in result.errors[0]


@pytest.mark.asyncio
async def test_solo_single_turn(simple_task: Task) -> None:
    """Solo topology always produces exactly 1 turn on success."""
    agent = MockAgent(name="solo", responses=["answer"])
    topology = SoloTopology(agent=agent)
    result = await topology.run(simple_task, TokenBudget())

    assert len(result.turns) == 1
    assert result.turns[0].message == simple_task.prompt
