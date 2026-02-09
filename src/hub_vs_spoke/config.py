"""Configuration via pydantic-settings, sourced from .env and environment."""

from __future__ import annotations

import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level harness configuration.

    API keys are intentionally omitted — the OpenAI and Anthropic SDKs
    read OPENAI_API_KEY / ANTHROPIC_API_KEY from the environment natively.
    """

    model_config = SettingsConfigDict(
        env_prefix="HUB_VS_SPOKE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Default models
    default_hub_model: str = "claude-sonnet-4-20250514"
    default_spoke_model: str = "gpt-4o-mini"

    # Budget defaults
    token_budget: int = 50_000
    max_turns: int = 20

    # Benchmark repetitions
    repetitions: int = 3

    # Judge model for LLM-as-judge evaluation
    judge_model: str = "gpt-4o"


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()  # type: ignore[call-arg]
