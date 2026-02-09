"""LLM-as-judge evaluator: pairwise and absolute scoring."""

from __future__ import annotations

import json
import random
from typing import Any

import structlog

from hub_vs_spoke.providers.base import LLMProvider
from hub_vs_spoke.types import Message, Role

logger = structlog.get_logger()


class LLMJudge:
    """Uses an LLM to evaluate output quality.

    Supports two modes:
        - absolute: score a single output on a rubric (1-10 scale)
        - pairwise: compare two outputs, declare a winner (A/B/tie)
    """

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def score_absolute(
        self,
        task_prompt: str,
        output: str,
        rubric: str,
    ) -> dict[str, Any]:
        """Score a single output on a 1-10 scale against a rubric.

        Returns: {"score": int, "reasoning": str}
        """
        system = (
            "You are an expert evaluator. Score the output on a scale of 1 to 10 "
            "based on the rubric. Return ONLY valid JSON: "
            '{"score": <int 1-10>, "reasoning": "<brief explanation>"}'
        )
        user = (
            f"## Task\n{task_prompt}\n\n"
            f"## Rubric\n{rubric}\n\n"
            f"## Output to evaluate\n{output}"
        )

        response = await self.provider.complete(
            [
                Message(role=Role.SYSTEM, content=system),
                Message(role=Role.USER, content=user),
            ],
            temperature=0.0,
        )

        return self._parse_score(response.content)

    async def compare_pairwise(
        self,
        task_prompt: str,
        output_a: str,
        output_b: str,
        rubric: str,
        *,
        label_a: str = "A",
        label_b: str = "B",
    ) -> dict[str, Any]:
        """Compare two outputs pairwise. Randomises order to reduce position bias.

        Returns: {"winner": "A"|"B"|"tie", "reasoning": str, "swapped": bool}
        """
        # Randomise presentation order
        swapped = random.random() < 0.5
        if swapped:
            first, second = output_b, output_a
            first_label, second_label = label_b, label_a
        else:
            first, second = output_a, output_b
            first_label, second_label = label_a, label_b

        system = (
            "You are an expert evaluator comparing two outputs. "
            "Decide which is better based on the rubric. "
            "Return ONLY valid JSON: "
            '{"winner": "first"|"second"|"tie", "reasoning": "<brief explanation>"}'
        )
        user = (
            f"## Task\n{task_prompt}\n\n"
            f"## Rubric\n{rubric}\n\n"
            f"## First output ({first_label})\n{first}\n\n"
            f"## Second output ({second_label})\n{second}"
        )

        response = await self.provider.complete(
            [
                Message(role=Role.SYSTEM, content=system),
                Message(role=Role.USER, content=user),
            ],
            temperature=0.0,
        )

        result = self._parse_comparison(response.content)

        # Un-swap to report in original order
        raw_winner = result.get("winner", "tie")
        if swapped:
            if raw_winner == "first":
                result["winner"] = label_b
            elif raw_winner == "second":
                result["winner"] = label_a
            else:
                result["winner"] = "tie"
        else:
            if raw_winner == "first":
                result["winner"] = label_a
            elif raw_winner == "second":
                result["winner"] = label_b
            else:
                result["winner"] = "tie"

        result["swapped"] = swapped
        return result

    @staticmethod
    def _parse_score(content: str) -> dict[str, Any]:
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            parsed = json.loads(content[start:end])
            return {
                "score": int(parsed.get("score", 5)),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except (ValueError, json.JSONDecodeError, KeyError):
            logger.warning("judge_parse_failed", content=content[:200])
            return {"score": 5, "reasoning": f"Parse failed; raw: {content[:200]}"}

    @staticmethod
    def _parse_comparison(content: str) -> dict[str, Any]:
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            parsed = json.loads(content[start:end])
            return {
                "winner": str(parsed.get("winner", "tie")),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except (ValueError, json.JSONDecodeError, KeyError):
            logger.warning("judge_parse_failed", content=content[:200])
            return {"winner": "tie", "reasoning": f"Parse failed; raw: {content[:200]}"}
