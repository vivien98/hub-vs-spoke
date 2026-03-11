"""Integration tests: error injection for hub-spoke and the legacy peer mesh.

Tests how each topology handles failures — using a FaultyProvider wrapper
that randomly fails a percentage of calls.
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from hub_vs_spoke.agents.mock_agent import MockAgent
from hub_vs_spoke.evaluation.reliability import ReliabilityScorer
from hub_vs_spoke.tasks.base import Task, TaskCategory
from hub_vs_spoke.topologies.hub_spoke import HubSpokeTopology
from hub_vs_spoke.topologies.spoke_spoke import SpokeSpokeTopology
from hub_vs_spoke.types import AgentResponse, TokenBudget, Usage


class FaultyAgent:
    """An agent that fails a configurable percentage of calls.

    When it doesn't fail, it behaves like a MockAgent with canned responses.
    """

    def __init__(
        self,
        name: str,
        *,
        failure_rate: float = 0.5,
        model_name: str = "faulty-model",
        seed: int = 42,
    ) -> None:
        self.name = name
        self._model_name = model_name
        self._failure_rate = failure_rate
        self._rng = random.Random(seed)
        self._call_count = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def total_usage(self) -> Usage:
        return Usage()

    @property
    def total_cost_usd(self) -> float:
        return 0.0

    def reset(self) -> None:
        self._call_count = 0

    async def act(self, task_message: str, **kwargs: Any) -> AgentResponse:
        self._call_count += 1
        if self._rng.random() < self._failure_rate:
            raise RuntimeError(f"{self.name} injected failure on call {self._call_count}")
        return AgentResponse(
            content=f"[{self.name}] Response to: {task_message[:60]}",
            usage=Usage(input_tokens=50, output_tokens=50),
            model=self._model_name,
            latency_ms=1.0,
        )


FAULT_TASK = Task(
    task_id="fault-test",
    category=TaskCategory.REASONING,
    prompt="Calculate 7 * 8 and explain your reasoning.",
    description="Simple task for fault tolerance testing",
)


class TestHubSpokeErrorInjection:
    """Test hub-spoke topology under spoke failures."""

    @pytest.mark.asyncio
    async def test_recovers_from_some_spoke_failures(self) -> None:
        hub = MockAgent(name="hub", responses=[
            '["Task A", "Task B"]',
            "Synthesised answer: 56",
        ])
        spokes = [
            FaultyAgent(name="faulty-spoke-0", failure_rate=0.5, seed=10),
            MockAgent(name="reliable-spoke", responses=["7 * 8 = 56"]),
        ]

        topology = HubSpokeTopology(hub=hub, spokes=spokes, max_retries=2)  # type: ignore[arg-type]
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)
        result = await topology.run(FAULT_TASK, budget)

        # Should still produce an answer (hub synthesises whatever it gets)
        assert len(result.final_answer) > 0

    @pytest.mark.asyncio
    async def test_records_all_errors(self) -> None:
        hub = MockAgent(name="hub", responses=[
            '["Task A"]',
            "Done despite errors",
        ])
        always_fail = FaultyAgent(name="always-fails", failure_rate=1.0, seed=1)

        topology = HubSpokeTopology(hub=hub, spokes=[always_fail], max_retries=1)  # type: ignore[arg-type]
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)
        result = await topology.run(FAULT_TASK, budget)

        assert len(result.errors) >= 2  # initial + 1 retry

    @pytest.mark.asyncio
    async def test_hub_failure_is_unrecoverable(self) -> None:
        """If the hub itself fails, the topology cannot proceed."""
        faulty_hub = FaultyAgent(name="faulty-hub", failure_rate=1.0, seed=1)
        spokes = [MockAgent(name="spoke")]

        topology = HubSpokeTopology(hub=faulty_hub, spokes=spokes)  # type: ignore[arg-type]
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)

        with pytest.raises(RuntimeError, match="injected failure"):
            await topology.run(FAULT_TASK, budget)


class TestSpokeSpokeErrorInjection:
    """Test spoke-spoke topology under peer failures."""

    @pytest.mark.asyncio
    async def test_mesh_tolerates_one_peer_failure(self) -> None:
        coordinator = MockAgent(name="coord", responses=[
            '["Task A", "Task B", "Task C"]',
            "LGTM",
        ])
        faulty = FaultyAgent(name="faulty-peer", failure_rate=0.5, seed=5)
        reliable = MockAgent(name="reliable-peer", responses=[
            "Peer done",
            "Final synthesis: everything OK",
        ])

        topology = SpokeSpokeTopology(
            peers=[coordinator, faulty, reliable],  # type: ignore[list-item]
            max_retries=1,
        )
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)
        result = await topology.run(FAULT_TASK, budget)

        assert len(result.final_answer) > 0

    @pytest.mark.asyncio
    async def test_total_peer_failure_still_produces_result(self) -> None:
        """Even if middle execution peers fail, the synthesiser still runs.

        The coordinator (first) decomposes, middle peers fail execution,
        and the synthesiser (last) merges whatever partial results exist.
        """
        coordinator = MockAgent(name="coord", responses=[
            '["Task A", "Task B", "Task C"]',
            "LGTM",
        ])
        fail1 = FaultyAgent(name="fail-1", failure_rate=1.0, seed=1)
        # Synthesiser must be reliable so the topology can finish
        synth = MockAgent(name="synth", responses=[
            "Partial synthesis from available data",
            "Final answer despite failures",
        ])

        topology = SpokeSpokeTopology(
            peers=[coordinator, fail1, synth],  # type: ignore[list-item]
            max_retries=0,
        )
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)
        result = await topology.run(FAULT_TASK, budget)

        # Errors recorded but topology still returns
        assert len(result.errors) > 0
        assert len(result.final_answer) > 0


class TestComparativeFaultTolerance:
    """Compare the two topologies under identical failure conditions."""

    @pytest.mark.asyncio
    async def test_reliability_comparison_under_faults(self) -> None:
        """Run both topologies multiple times with 30% failure rate and compare."""
        hs_results = []
        ss_results = []
        budget = TokenBudget(max_total_tokens=50_000, max_turns=20)

        for run in range(5):
            seed = run * 100

            # Hub-spoke: reliable hub, faulty spokes
            hub = MockAgent(name="hub", responses=[
                '["Task A", "Task B"]',
                f"Synthesis run {run}",
            ])
            hs_spokes = [
                FaultyAgent(name=f"hs-spoke-{i}", failure_rate=0.3, seed=seed + i)
                for i in range(2)
            ]
            hs_topo = HubSpokeTopology(hub=hub, spokes=hs_spokes, max_retries=1)  # type: ignore[arg-type]

            try:
                hs_result = await hs_topo.run(FAULT_TASK, budget)
                hs_results.append(hs_result)
            except Exception:
                pass  # hub failure — won't happen here since hub is reliable

            # Spoke-spoke: all peers faulty at same rate
            peers = [
                MockAgent(name="coord", responses=[
                    '["Task A", "Task B", "Task C"]',
                    "Review OK",
                    f"Synthesis run {run}",
                ]),
                FaultyAgent(name="ss-peer-1", failure_rate=0.3, seed=seed + 10),
                MockAgent(name="synth", responses=["peer done", f"Final {run}"]),
            ]
            ss_topo = SpokeSpokeTopology(peers=peers, max_retries=1)  # type: ignore[arg-type]
            ss_result = await ss_topo.run(FAULT_TASK, budget)
            ss_results.append(ss_result)

        comparison = ReliabilityScorer.compare_topologies(hs_results, ss_results)

        # Both should have completed at least some runs
        assert comparison["hub_spoke"]["total_runs"] >= 3
        assert comparison["spoke_spoke"]["total_runs"] >= 3
        # Print for inspection
        print("\n--- Fault tolerance comparison ---")
        print(f"Hub-spoke success rate: {comparison['hub_spoke']['success_rate']:.0%}")
        print(f"Spoke-spoke success rate: {comparison['spoke_spoke']['success_rate']:.0%}")
        print(f"More reliable: {comparison['more_reliable']}")
