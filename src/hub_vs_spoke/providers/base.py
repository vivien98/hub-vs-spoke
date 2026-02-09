"""Abstract LLM provider protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from hub_vs_spoke.types import LLMResponse, Message


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that all LLM providers must satisfy."""

    @property
    def model_name(self) -> str:
        """Return the model identifier this provider is configured with."""
        ...

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send messages and return a normalised response."""
        ...
