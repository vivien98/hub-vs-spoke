"""Hub-and-spoke topology: central orchestrator delegates to worker spokes."""

from __future__ import annotations

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies._shared import (
    AgentLike,
    build_result,
    execute_with_retry,
    parse_subtasks,
)
from hub_vs_spoke.types import Timer, TokenBudget, TopologyResult, Turn


class HubSpokeTopology:
    """One orchestrator hub delegates subtasks to spoke agents and synthesises results.

    Flow:
        1. Hub decomposes the task into subtasks (structured JSON output).
        2. Hub assigns each subtask to a spoke (round-robin).
        3. Spokes execute subtasks and return results.
        4. Hub synthesises a final answer from spoke outputs.
        5. On spoke failure: hub retries with the next spoke or handles inline.
    """

    def __init__(
        self,
        hub: AgentLike,
        spokes: list[AgentLike],
        *,
        max_retries: int = 1,
    ) -> None:
        self.hub = hub
        self.spokes = spokes
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "hub-and-spoke"

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        turns: list[Turn] = []
        errors: list[str] = []
        total_tokens = 0

        with Timer() as wall_timer:
            # Step 1: Hub decomposes task
            decompose_prompt = (
                f"You are the orchestrator. Decompose this task into subtasks for "
                f"{len(self.spokes)} workers. Return ONLY a JSON array of strings, "
                f"each being a clear subtask instruction.\n\n"
                f"Task: {task.prompt}"
            )

            hub_response = await self.hub.act(decompose_prompt)
            total_tokens += hub_response.usage.total_tokens
            turns.append(Turn(
                from_agent="user",
                to_agent=self.hub.name,
                message=decompose_prompt,
                response=hub_response.content,
                usage=hub_response.usage,
                latency_ms=hub_response.latency_ms,
            ))

            subtasks = parse_subtasks(hub_response.content, len(self.spokes))

            if budget.exceeded(total_tokens, len(turns)):
                return build_result(
                    self.name, task, "", turns, total_tokens, errors, wall_timer
                )

            # Step 2-3: Assign subtasks to spokes, collect results
            spoke_results: list[str] = []
            for i, subtask in enumerate(subtasks):
                if budget.exceeded(total_tokens, len(turns)):
                    errors.append("Budget exhausted before all subtasks completed")
                    break

                spoke = self.spokes[i % len(self.spokes)]
                result = await execute_with_retry(
                    spoke, subtask,
                    from_agent=self.hub.name,
                    max_retries=self.max_retries,
                    turns=turns,
                    errors=errors,
                )
                total_tokens += result["tokens"]
                spoke_results.append(result["content"])

            if budget.exceeded(total_tokens, len(turns)):
                return build_result(
                    self.name, task, "\n\n".join(spoke_results),
                    turns, total_tokens, errors, wall_timer,
                )

            # Step 4: Hub synthesises final answer
            synthesis_prompt = (
                f"You are the orchestrator. Your workers have completed their subtasks. "
                f"Synthesise their outputs into a single coherent final answer.\n\n"
                f"Original task: {task.prompt}\n\n"
            )
            for j, sr in enumerate(spoke_results):
                synthesis_prompt += f"--- Worker {j + 1} output ---\n{sr}\n\n"

            hub_synth = await self.hub.act(synthesis_prompt)
            total_tokens += hub_synth.usage.total_tokens
            turns.append(Turn(
                from_agent="spoke_results",
                to_agent=self.hub.name,
                message=synthesis_prompt[:500],
                response=hub_synth.content,
                usage=hub_synth.usage,
                latency_ms=hub_synth.latency_ms,
            ))

        return build_result(
            self.name, task, hub_synth.content,
            turns, total_tokens, errors, wall_timer,
        )
