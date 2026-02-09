"""Agent: wraps an LLM provider with a role, conversation history, and cost tracking."""

from __future__ import annotations

from typing import Any

import structlog

from hub_vs_spoke.providers.base import LLMProvider
from hub_vs_spoke.types import (
    AgentResponse,
    CostRecord,
    Message,
    Role,
    Usage,
)

logger = structlog.get_logger()


class Agent:
    """An agent that uses an LLM provider to respond to messages.

    Maintains conversation history and cumulative cost tracking.
    """

    def __init__(
        self,
        name: str,
        provider: LLMProvider,
        system_prompt: str = "You are a helpful assistant.",
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        self.name = name
        self.provider = provider
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._history: list[Message] = []
        self._total_usage = Usage()
        self._cost_records: list[CostRecord] = []

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    @property
    def total_usage(self) -> Usage:
        return self._total_usage

    @property
    def total_cost_usd(self) -> float:
        return sum(r.total_cost_usd for r in self._cost_records)

    @property
    def history(self) -> list[Message]:
        return list(self._history)

    def reset(self) -> None:
        """Clear conversation history and cost tracking."""
        self._history.clear()
        self._total_usage = Usage()
        self._cost_records.clear()

    async def act(self, task_message: str, **kwargs: Any) -> AgentResponse:
        """Send a user message and return the assistant response.

        Appends both the user message and the assistant reply to history.
        """
        user_msg = Message(role=Role.USER, content=task_message, name=self.name)
        self._history.append(user_msg)

        messages = [Message(role=Role.SYSTEM, content=self.system_prompt)] + self._history

        llm_response = await self.provider.complete(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )

        assistant_msg = Message(role=Role.ASSISTANT, content=llm_response.content)
        self._history.append(assistant_msg)

        # Track usage
        self._total_usage = Usage(
            input_tokens=self._total_usage.input_tokens + llm_response.usage.input_tokens,
            output_tokens=self._total_usage.output_tokens + llm_response.usage.output_tokens,
        )
        self._cost_records.append(
            CostRecord.from_usage(llm_response.model, llm_response.usage)
        )

        logger.debug(
            "agent_act",
            agent=self.name,
            model=llm_response.model,
            input_tokens=llm_response.usage.input_tokens,
            output_tokens=llm_response.usage.output_tokens,
            latency_ms=round(llm_response.latency_ms, 1),
        )

        return AgentResponse(
            content=llm_response.content,
            usage=llm_response.usage,
            model=llm_response.model,
            latency_ms=llm_response.latency_ms,
        )
