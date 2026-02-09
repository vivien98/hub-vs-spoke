"""MockAgent: deterministic stub for unit tests, no network calls."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hub_vs_spoke.types import AgentResponse, Usage


class MockAgent:
    """A mock agent that returns pre-configured or computed responses.

    Satisfies the same interface as Agent (name, model_name, act, reset)
    but never touches a real LLM.
    """

    def __init__(
        self,
        name: str,
        *,
        model_name: str = "mock-model",
        responses: list[str] | None = None,
        response_fn: Callable[[str], str] | None = None,
        tokens_per_call: int = 100,
    ) -> None:
        self.name = name
        self._model_name = model_name
        self._responses = list(responses) if responses else []
        self._response_fn = response_fn
        self._tokens_per_call = tokens_per_call
        self._call_index = 0
        self._history: list[dict[str, str]] = []
        self._total_usage = Usage()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def total_usage(self) -> Usage:
        return self._total_usage

    @property
    def total_cost_usd(self) -> float:
        return 0.0  # mock is free

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    def reset(self) -> None:
        self._call_index = 0
        self._history.clear()
        self._total_usage = Usage()

    async def act(self, task_message: str, **kwargs: Any) -> AgentResponse:
        """Return the next pre-configured response or compute one via response_fn."""
        self._history.append({"role": "user", "content": task_message})

        if self._response_fn is not None:
            content = self._response_fn(task_message)
        elif self._call_index < len(self._responses):
            content = self._responses[self._call_index]
        else:
            content = f"[{self.name}] mock response to: {task_message[:80]}"

        self._call_index += 1
        self._history.append({"role": "assistant", "content": content})

        usage = Usage(
            input_tokens=self._tokens_per_call,
            output_tokens=self._tokens_per_call,
        )
        self._total_usage = Usage(
            input_tokens=self._total_usage.input_tokens + usage.input_tokens,
            output_tokens=self._total_usage.output_tokens + usage.output_tokens,
        )

        return AgentResponse(
            content=content,
            usage=usage,
            model=self._model_name,
            latency_ms=1.0,
        )
