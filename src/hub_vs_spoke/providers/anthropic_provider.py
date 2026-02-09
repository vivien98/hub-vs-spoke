"""Anthropic messages API provider."""

from __future__ import annotations

from typing import Any

import anthropic
import structlog

from hub_vs_spoke.types import LLMResponse, Message, Role, Timer, Usage

logger = structlog.get_logger()


class AnthropicProvider:
    """Wraps the Anthropic messages API into the LLMProvider protocol."""

    def __init__(
        self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None
    ) -> None:
        self._model = model
        self._client = (
            anthropic.AsyncAnthropic(api_key=api_key)
            if api_key
            else anthropic.AsyncAnthropic()
        )

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        # Anthropic requires system prompt to be passed separately.
        system_prompt: str | None = None
        api_messages: list[dict[str, str]] = []

        for m in messages:
            if m.role == Role.SYSTEM:
                system_prompt = m.content
            else:
                api_messages.append({"role": m.role.value, "content": m.content})

        create_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt

        with Timer() as t:
            response = await self._client.messages.create(**create_kwargs)

        content_text = ""
        for block in response.content:
            if block.type == "text":
                content_text += block.text

        logger.debug(
            "anthropic_completion",
            model=self._model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=round(t.elapsed_ms, 1),
        )

        return LLMResponse(
            content=content_text,
            model=response.model,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            latency_ms=t.elapsed_ms,
            raw=response.model_dump(),
        )
