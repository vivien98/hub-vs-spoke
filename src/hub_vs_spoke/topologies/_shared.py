"""Shared helpers for topology implementations."""

from __future__ import annotations

import json
from typing import Any

import structlog

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.types import AgentResponse, CostRecord, Timer, TopologyResult, Turn

logger = structlog.get_logger()

# Duck-typed agent interface (Agent or MockAgent).
AgentLike = Any


def parse_subtasks(content: str, max_count: int) -> list[str]:
    """Parse a JSON array of subtask strings from LLM output.

    Falls back to line-splitting, then to treating the whole content as one task.
    """
    # Try JSON array extraction
    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        parsed = json.loads(content[start:end])
        if isinstance(parsed, list) and all(isinstance(s, str) for s in parsed):
            return parsed
    except (ValueError, json.JSONDecodeError):
        pass

    # Fallback: split by newlines, strip numbering
    lines = [
        ln.strip().lstrip("0123456789.-) ")
        for ln in content.split("\n")
        if ln.strip()
    ]
    if lines:
        return lines[:max_count]

    return [content]


async def execute_with_retry(
    agent: AgentLike,
    subtask: str,
    *,
    from_agent: str,
    max_retries: int,
    turns: list[Turn],
    errors: list[str],
) -> dict[str, Any]:
    """Execute a subtask on an agent, retrying on failure.

    Returns {"content": str, "tokens": int}.
    """
    last_error: str | None = None

    for attempt in range(1 + max_retries):
        try:
            response: AgentResponse = await agent.act(subtask)
            turns.append(Turn(
                from_agent=from_agent,
                to_agent=agent.name,
                message=subtask,
                response=response.content,
                usage=response.usage,
                latency_ms=response.latency_ms,
                model=response.model,
            ))
            return {"content": response.content, "tokens": response.usage.total_tokens}
        except Exception as exc:
            last_error = f"{agent.name} attempt {attempt + 1}: {exc}"
            logger.warning(
                "agent_failure", agent=agent.name, attempt=attempt + 1, error=str(exc)
            )
            errors.append(last_error)

    # All retries exhausted
    turns.append(Turn(
        from_agent=from_agent,
        to_agent=agent.name,
        message=subtask,
        response="",
        error=last_error,
    ))
    return {"content": f"[FAILED: {last_error}]", "tokens": 0}


def build_result(
    topology_name: str,
    task: Task,
    final_answer: str,
    turns: list[Turn],
    total_tokens: int,
    errors: list[str],
    timer: Timer,
) -> TopologyResult:
    """Construct a TopologyResult from run data, including cost from per-turn usage."""
    total_cost = sum(
        CostRecord.from_usage(t.model, t.usage).total_cost_usd
        for t in turns
        if t.model
    )
    return TopologyResult(
        topology_name=topology_name,
        task_id=task.task_id,
        final_answer=final_answer,
        turns=turns,
        total_tokens=total_tokens,
        total_cost_usd=total_cost,
        errors=errors,
        wall_time_ms=timer.elapsed_ms,
    )
