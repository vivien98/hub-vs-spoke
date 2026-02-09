"""Spoke-and-spoke (peer mesh) topology: agents coordinate directly."""

from __future__ import annotations

from typing import Any

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies._shared import (
    AgentLike,
    build_result,
    execute_with_retry,
    parse_subtasks,
)
from hub_vs_spoke.types import Timer, TokenBudget, TopologyResult, Turn


class SpokeSpokeTopology:
    """Peer mesh where agents coordinate directly without a permanent hub.

    Flow:
        1. Coordinator (first peer) decomposes the task and broadcasts subtasks.
        2. Peers execute subtasks (assigned round-robin).
        3. Middle peer reviews outputs for consistency.
        4. Synthesiser (last peer) merges results into a final answer.
        5. On peer failure: retries, then records failure and continues.
    """

    def __init__(
        self,
        peers: list[AgentLike],
        *,
        max_retries: int = 1,
    ) -> None:
        if len(peers) < 2:
            raise ValueError("Spoke-spoke topology requires at least 2 peers")
        self.peers = peers
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "spoke-and-spoke"

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        turns: list[Turn] = []
        errors: list[str] = []
        total_tokens = 0

        coordinator = self.peers[0]
        synthesiser = self.peers[-1]

        with Timer() as wall_timer:
            # Step 1: Coordinator decomposes task
            decompose_prompt = (
                f"You are a peer in a team of {len(self.peers)}. "
                f"Decompose this task into {len(self.peers)} subtasks — one for each "
                f"team member including yourself. Return ONLY a JSON array of strings.\n\n"
                f"Task: {task.prompt}"
            )

            coord_response = await coordinator.act(decompose_prompt)
            total_tokens += coord_response.usage.total_tokens
            turns.append(Turn(
                from_agent="user",
                to_agent=coordinator.name,
                message=decompose_prompt,
                response=coord_response.content,
                usage=coord_response.usage,
                latency_ms=coord_response.latency_ms,
            ))

            subtasks = parse_subtasks(coord_response.content, len(self.peers))

            if budget.exceeded(total_tokens, len(turns)):
                return build_result(
                    self.name, task, "", turns, total_tokens, errors, wall_timer
                )

            # Step 2: Peers execute subtasks
            peer_results: list[dict[str, Any]] = []
            for i, subtask in enumerate(subtasks):
                if budget.exceeded(total_tokens, len(turns)):
                    errors.append("Budget exhausted before all subtasks completed")
                    break

                worker = self.peers[i % len(self.peers)]
                result = await execute_with_retry(
                    worker, subtask,
                    from_agent="coordinator",
                    max_retries=self.max_retries,
                    turns=turns,
                    errors=errors,
                )
                total_tokens += result["tokens"]
                peer_results.append(result)

            if budget.exceeded(total_tokens, len(turns)):
                combined = "\n\n".join(r["content"] for r in peer_results)
                return build_result(
                    self.name, task, combined,
                    turns, total_tokens, errors, wall_timer,
                )

            # Step 3: Peer-to-peer review (if budget allows)
            if len(peer_results) >= 2 and not budget.exceeded(total_tokens, len(turns)):
                reviewer = self.peers[len(self.peers) // 2]
                review_prompt = f"Review these peer outputs for the task: {task.prompt}\n\n"
                for j, pr in enumerate(peer_results):
                    review_prompt += f"--- Peer {j + 1} ---\n{pr['content']}\n\n"
                review_prompt += (
                    "Flag any inconsistencies or gaps. "
                    "Respond with corrections or 'LGTM' if all looks good."
                )
                try:
                    review_resp = await reviewer.act(review_prompt)
                    total_tokens += review_resp.usage.total_tokens
                    turns.append(Turn(
                        from_agent="peers",
                        to_agent=reviewer.name,
                        message=review_prompt[:500],
                        response=review_resp.content,
                        usage=review_resp.usage,
                        latency_ms=review_resp.latency_ms,
                    ))
                except Exception as exc:
                    errors.append(f"Review step failed: {exc}")

            # Step 4: Synthesiser merges results
            if budget.exceeded(total_tokens, len(turns)):
                combined = "\n\n".join(r["content"] for r in peer_results)
                return build_result(
                    self.name, task, combined,
                    turns, total_tokens, errors, wall_timer,
                )

            synthesis_prompt = (
                f"You are the synthesiser in a peer team. Merge the outputs below "
                f"into a single coherent final answer.\n\n"
                f"Original task: {task.prompt}\n\n"
            )
            for j, pr in enumerate(peer_results):
                synthesis_prompt += f"--- Peer {j + 1} output ---\n{pr['content']}\n\n"

            synth_response = await synthesiser.act(synthesis_prompt)
            total_tokens += synth_response.usage.total_tokens
            turns.append(Turn(
                from_agent="peer_results",
                to_agent=synthesiser.name,
                message=synthesis_prompt[:500],
                response=synth_response.content,
                usage=synth_response.usage,
                latency_ms=synth_response.latency_ms,
            ))

        return build_result(
            self.name, task, synth_response.content,
            turns, total_tokens, errors, wall_timer,
        )
