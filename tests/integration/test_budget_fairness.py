"""Integration tests: verify budget constraints hold for hub-spoke and the legacy mesh.

These tests use mock agents (no network) but are "integration" in the sense
that they test the full topology pipeline against budget invariants.
"""

from __future__ import annotations

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent
from hub_vs_spoke.tasks.base import Task, TaskCategory
from hub_vs_spoke.topologies.hub_spoke import HubSpokeTopology
from hub_vs_spoke.topologies.spoke_spoke import SpokeSpokeTopology
from hub_vs_spoke.types import TokenBudget

BUDGET_TASK = Task(
    task_id="budget-test",
    category=TaskCategory.REASONING,
    prompt="How many days are in a year?",
    description="Trivial task for budget testing",
)


class TestBudgetFairness:
    """Both topologies should respect token and turn budgets."""

    @pytest.mark.asyncio
    async def test_hub_spoke_respects_token_budget(self) -> None:
        """Hub-spoke total tokens should not wildly exceed budget."""
        hub = MockAgent(name="hub", tokens_per_call=200, responses=[
            '["A", "B"]',
            "synthesis",
        ])
        spokes = [MockAgent(name=f"s-{i}", tokens_per_call=200) for i in range(2)]
        topology = HubSpokeTopology(hub=hub, spokes=spokes)

        budget = TokenBudget(max_total_tokens=1000, max_turns=20)
        result = await topology.run(BUDGET_TASK, budget)

        # Total tokens should be near or under budget (may slightly exceed
        # because budget is checked *between* steps, not mid-step).
        assert result.total_tokens <= budget.max_total_tokens + 400  # one step overshoot

    @pytest.mark.asyncio
    async def test_spoke_spoke_respects_token_budget(self) -> None:
        """Spoke-spoke total tokens should not wildly exceed budget."""
        peers = [
            MockAgent(name=f"p-{i}", tokens_per_call=200, responses=[
                '["X","Y","Z"]' if i == 0 else f"Peer {i} done",
                "review" if i == 1 else "synth",
            ])
            for i in range(3)
        ]
        topology = SpokeSpokeTopology(peers=peers)

        budget = TokenBudget(max_total_tokens=1000, max_turns=20)
        result = await topology.run(BUDGET_TASK, budget)

        assert result.total_tokens <= budget.max_total_tokens + 400

    @pytest.mark.asyncio
    async def test_hub_spoke_respects_turn_budget(self) -> None:
        """Hub-spoke should stop within max_turns."""
        hub = MockAgent(name="hub", responses=['["A","B","C","D","E"]', "synth"])
        spokes = [MockAgent(name=f"s-{i}") for i in range(5)]
        topology = HubSpokeTopology(hub=hub, spokes=spokes)

        budget = TokenBudget(max_total_tokens=999_999, max_turns=3)
        result = await topology.run(BUDGET_TASK, budget)

        assert len(result.turns) <= budget.max_turns + 1  # one overshoot possible

    @pytest.mark.asyncio
    async def test_spoke_spoke_respects_turn_budget(self) -> None:
        """Spoke-spoke should stop within max_turns."""
        peers = [
            MockAgent(name=f"p-{i}", responses=[
                '["A","B","C","D"]' if i == 0 else f"done {i}",
                "review" if i == 1 else "synth",
            ])
            for i in range(4)
        ]
        topology = SpokeSpokeTopology(peers=peers)

        budget = TokenBudget(max_total_tokens=999_999, max_turns=3)
        result = await topology.run(BUDGET_TASK, budget)

        assert len(result.turns) <= budget.max_turns + 1

    @pytest.mark.asyncio
    async def test_both_topologies_use_comparable_tokens(self) -> None:
        """Given the same budget and similar agents, both topologies should
        consume tokens in the same order of magnitude."""
        tokens_per = 100

        # Hub-spoke
        hub = MockAgent(name="hub", tokens_per_call=tokens_per, responses=[
            '["A", "B", "C"]', "synth",
        ])
        hs_spokes = [MockAgent(name=f"hs-{i}", tokens_per_call=tokens_per) for i in range(3)]
        hs_topo = HubSpokeTopology(hub=hub, spokes=hs_spokes)

        # Spoke-spoke
        ss_peers = [
            MockAgent(name=f"ss-{i}", tokens_per_call=tokens_per, responses=[
                '["A","B","C"]' if i == 0 else f"done {i}",
                "LGTM" if i == 1 else "final",
            ])
            for i in range(3)
        ]
        ss_topo = SpokeSpokeTopology(peers=ss_peers)

        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)

        hs_result = await hs_topo.run(BUDGET_TASK, budget)
        ss_result = await ss_topo.run(BUDGET_TASK, budget)

        # Within 3x of each other (spoke-spoke does an extra review step)
        ratio = max(hs_result.total_tokens, ss_result.total_tokens) / max(
            min(hs_result.total_tokens, ss_result.total_tokens), 1
        )
        assert ratio < 3.0, (
            f"Token usage too different: HS={hs_result.total_tokens}, "
            f"SS={ss_result.total_tokens}, ratio={ratio:.1f}"
        )
