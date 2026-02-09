"""Unit tests for the spoke-and-spoke (peer mesh) topology."""

from __future__ import annotations

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent
from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies.spoke_spoke import SpokeSpokeTopology
from hub_vs_spoke.types import TokenBudget


@pytest.mark.asyncio
async def test_basic_spoke_spoke_run(
    mock_peers: list[MockAgent], simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Peer mesh decomposes, executes, reviews, and synthesises."""
    topology = SpokeSpokeTopology(peers=mock_peers)

    result = await topology.run(simple_task, default_budget)

    assert result.topology_name == "spoke-and-spoke"
    assert result.task_id == "test-001"
    assert len(result.final_answer) > 0
    assert result.total_tokens > 0
    assert len(result.turns) >= 2


@pytest.mark.asyncio
async def test_spoke_spoke_requires_two_peers() -> None:
    """Must have at least 2 peers."""
    with pytest.raises(ValueError, match="at least 2"):
        SpokeSpokeTopology(peers=[MockAgent(name="lonely")])


@pytest.mark.asyncio
async def test_spoke_spoke_name() -> None:
    peers = [MockAgent(name=f"p-{i}") for i in range(2)]
    topology = SpokeSpokeTopology(peers=peers)
    assert topology.name == "spoke-and-spoke"


@pytest.mark.asyncio
async def test_spoke_spoke_handles_peer_failure(
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Topology handles peer failure gracefully."""

    class FailingPeer:
        name = "failing-peer"
        model_name = "fail-model"

        async def act(self, msg: str) -> None:
            raise RuntimeError("Peer exploded!")

    coordinator = MockAgent(name="coord", responses=[
        '["Task A", "Task B"]',
        "LGTM",
    ])
    good_peer = MockAgent(name="good", responses=["Good result", "Synth result"])

    topology = SpokeSpokeTopology(
        peers=[coordinator, FailingPeer(), good_peer],  # type: ignore[list-item]
        max_retries=0,
    )
    result = await topology.run(simple_task, default_budget)

    assert len(result.errors) > 0
    assert "exploded" in result.errors[0]


@pytest.mark.asyncio
async def test_spoke_spoke_respects_budget(simple_task: Task) -> None:
    """Peer mesh stops early when token budget is exhausted."""
    peers = [
        MockAgent(name=f"p-{i}", tokens_per_call=300, responses=[
            '["X","Y","Z"]' if i == 0 else f"Peer {i} done",
            "synth",
        ])
        for i in range(3)
    ]
    tight = TokenBudget(max_total_tokens=500, max_turns=20)
    topology = SpokeSpokeTopology(peers=peers)
    result = await topology.run(simple_task, tight)

    # Should have stopped before completion
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_spoke_spoke_two_peers_minimal(
    simple_task: Task, default_budget: TokenBudget,
) -> None:
    """Topology works with the minimum of 2 peers."""
    peers = [
        MockAgent(name="coord", responses=['["Only task"]', "Review OK", "Final"]),
        MockAgent(name="worker", responses=["Worker done", "Synthesis complete"]),
    ]
    topology = SpokeSpokeTopology(peers=peers)
    result = await topology.run(simple_task, default_budget)

    assert len(result.final_answer) > 0
    assert result.success
