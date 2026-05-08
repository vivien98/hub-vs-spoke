"""OpenAI chat completions provider."""

from __future__ import annotations

from typing import Any

import openai
import structlog

from hub_vs_spoke.types import LLMResponse, Message, Timer, Usage

logger = structlog.get_logger()

# Models that only accept temperature=1.0 (the API default).
# Sending any other value raises a 400 BadRequestError.
_TEMPERATURE_LOCKED_PREFIXES = ("gpt-5-mini", "o1-mini", "o3-mini", "o4-mini", "o1", "o3")


class OpenAIProvider:
    """Wraps the OpenAI chat completions API into the LLMProvider protocol."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self._model = model
        self._client = openai.AsyncOpenAI(api_key=api_key) if api_key else openai.AsyncOpenAI()

    @property
    def model_name(self) -> str:
        return self._model

    def _temperature_locked(self) -> bool:
        return any(self._model.startswith(p) for p in _TEMPERATURE_LOCKED_PREFIXES)

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        oai_messages = [
            {"role": m.role.value, "content": m.content}
            for m in messages
        ]

        create_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": oai_messages,  # type: ignore[arg-type]
            "max_completion_tokens": max_tokens,
            **kwargs,
        }
        if not self._temperature_locked():
            create_kwargs["temperature"] = temperature

        with Timer() as t:
            response = await self._client.chat.completions.create(**create_kwargs)

        choice = response.choices[0]
        usage = response.usage

        logger.debug(
            "openai_completion",
            model=self._model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=round(t.elapsed_ms, 1),
        )

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=Usage(
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            ),
            latency_ms=t.elapsed_ms,
            raw=response.model_dump(),
        )
