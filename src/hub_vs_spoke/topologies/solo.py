"""Solo topology: single agent, single call — the simplest possible baseline."""

from __future__ import annotations

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies._shared import AgentLike, build_result
from hub_vs_spoke.types import Timer, TokenBudget, TopologyResult, Turn


class SoloTopology:
    """One agent answers the task directly. No decomposition, no collaboration."""

    def __init__(self, agent: AgentLike) -> None:
        self.agent = agent

    @property
    def name(self) -> str:
        return "solo"

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        turns: list[Turn] = []
        errors: list[str] = []

        with Timer() as wall_timer:
            try:
                response = await self.agent.act(task.prompt)
                turns.append(Turn(
                    from_agent="user",
                    to_agent=self.agent.name,
                    message=task.prompt,
                    response=response.content,
                    usage=response.usage,
                    latency_ms=response.latency_ms,
                    model=response.model,
                ))
            except Exception as exc:
                errors.append(f"{self.agent.name}: {exc}")

        final_answer = turns[0].response if turns else ""
        total_tokens = turns[0].usage.total_tokens if turns else 0
        return build_result(
            self.name, task, final_answer, turns, total_tokens, errors, wall_timer,
        )
