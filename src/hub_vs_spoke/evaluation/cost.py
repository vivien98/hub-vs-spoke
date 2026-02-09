"""Cost calculation from usage metadata."""

from __future__ import annotations

from hub_vs_spoke.types import MODEL_PRICING, CostRecord, Usage


class CostCalculator:
    """Compute costs for LLM usage."""

    @staticmethod
    def cost_from_usage(model: str, usage: Usage) -> float:
        """Compute USD cost for a single model + usage pair."""
        return CostRecord.from_usage(model, usage).total_cost_usd

    @staticmethod
    def available_models() -> list[str]:
        """Return list of models with known pricing."""
        return sorted(MODEL_PRICING.keys())
