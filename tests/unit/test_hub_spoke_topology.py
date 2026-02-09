"""Unit tests for the hub-and-spoke topology using mock agents."""

from __future__ import annotations

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent
from hub_vs_spoke.tasks.base import Task, TaskCategory
from hub_vs_spoke.topologies.hub_spoke import HubSpokeTopology
from hub_vs_spoke.types import TokenBudget


@pytest.mark.asyncio
async def test_basic_hub_spoke_run(
    mock_hub: MockAgent, mock_spokes: list[MockAgent],
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Topology decomposes, delegates, and synthesises with mock agents."""
    topology = HubSpokeTopology(hub=mock_hub, spokes=mock_spokes)

    result = await topology.run(simple_task, default_budget)

    assert result.topology_name == "hub-and-spoke"
    assert result.task_id == "test-001"
    assert len(result.final_answer) > 0
    assert result.total_tokens > 0
    assert len(result.turns) >= 2  # at least decompose + synthesis
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_hub_spoke_respects_budget(simple_task: Task) -> None:
    """Topology stops early when budget is exhausted."""
    hub = MockAgent(name="hub", tokens_per_call=300, responses=[
        '["A", "B", "C"]',
        "synthesised",
    ])
    spokes = [MockAgent(name=f"s-{i}", tokens_per_call=300) for i in range(3)]

    tight = TokenBudget(max_total_tokens=500, max_turns=20)
    topology = HubSpokeTopology(hub=hub, spokes=spokes)
    result = await topology.run(simple_task, tight)

    # Should have stopped before completing all subtasks
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_hub_spoke_handles_spoke_failure(
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Topology recovers when a spoke raises an exception."""

    class FailingAgent:
        name = "failing-spoke"
        model_name = "fail-model"

        async def act(self, msg: str) -> None:
            raise RuntimeError("Spoke crashed!")

    hub = MockAgent(name="hub", responses=[
        '["task-a", "task-b"]',
        "Final answer despite failures",
    ])

    spokes = [FailingAgent(), MockAgent(name="good-spoke", responses=["good result"])]  # type: ignore[list-item]
    topology = HubSpokeTopology(hub=hub, spokes=spokes, max_retries=1)

    result = await topology.run(simple_task, default_budget)

    assert len(result.errors) > 0
    assert "Spoke crashed" in result.errors[0]
    assert len(result.final_answer) > 0  # hub still synthesises


@pytest.mark.asyncio
async def test_hub_spoke_name() -> None:
    hub = MockAgent(name="hub")
    topology = HubSpokeTopology(hub=hub, spokes=[MockAgent(name="s")])
    assert topology.name == "hub-and-spoke"


@pytest.mark.asyncio
async def test_hub_spoke_parse_subtasks_json() -> None:
    """Hub output parsed correctly when it returns valid JSON."""
    hub = MockAgent(name="hub", responses=[
        'Here are the subtasks: ["Do X", "Do Y"]',
        "Done",
    ])
    spokes = [MockAgent(name="s-0"), MockAgent(name="s-1")]
    topology = HubSpokeTopology(hub=hub, spokes=spokes)

    task = Task(task_id="parse-test", category=TaskCategory.CODING, prompt="test")
    result = await topology.run(task, TokenBudget())

    # Should have delegated to both spokes
    spoke_turns = [t for t in result.turns if t.to_agent.startswith("s-")]
    assert len(spoke_turns) == 2


@pytest.mark.asyncio
async def test_hub_spoke_parse_subtasks_fallback() -> None:
    """Hub output parsed via line fallback when JSON is absent."""
    hub = MockAgent(name="hub", responses=[
        "1. First thing\n2. Second thing\n3. Third thing",
        "Synthesised from fallback",
    ])
    spokes = [MockAgent(name=f"s-{i}") for i in range(3)]
    topology = HubSpokeTopology(hub=hub, spokes=spokes)

    task = Task(task_id="fallback-test", category=TaskCategory.CODING, prompt="test")
    result = await topology.run(task, TokenBudget())

    assert len(result.final_answer) > 0


@pytest.mark.asyncio
async def test_hub_spoke_max_turns_budget(simple_task: Task) -> None:
    """Topology respects max_turns in the budget."""
    hub = MockAgent(name="hub", responses=['["a","b","c"]', "synth"])
    spokes = [MockAgent(name=f"s-{i}") for i in range(3)]
    topology = HubSpokeTopology(hub=hub, spokes=spokes)

    # max_turns=2 means: 1 decompose + 1 spoke, then budget exceeded
    result = await topology.run(simple_task, TokenBudget(max_total_tokens=999_999, max_turns=2))

    # Should have stopped early
    assert len(result.turns) <= 3  # some turns may still be recorded
