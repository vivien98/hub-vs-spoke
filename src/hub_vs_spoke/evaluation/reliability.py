"""Reliability scoring: success rates, error analysis, recovery metrics."""

from __future__ import annotations

from typing import Any

from hub_vs_spoke.types import TopologyResult


class ReliabilityScorer:
    """Compute reliability metrics from a collection of topology runs."""

    @staticmethod
    def score_single(result: TopologyResult) -> dict[str, Any]:
        """Compute reliability metrics for a single run."""
        total_turns = len(result.turns)
        error_turns = sum(1 for t in result.turns if t.error is not None)
        successful_turns = total_turns - error_turns

        return {
            "success": result.success,
            "total_turns": total_turns,
            "successful_turns": successful_turns,
            "error_turns": error_turns,
            "error_rate": error_turns / total_turns if total_turns > 0 else 0.0,
            "errors": result.errors,
            "has_final_answer": len(result.final_answer) > 0,
        }

    @staticmethod
    def score_batch(results: list[TopologyResult]) -> dict[str, Any]:
        """Compute aggregate reliability metrics across multiple runs."""
        if not results:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "mean_error_rate": 0.0,
                "total_errors": 0,
            }

        individual = [ReliabilityScorer.score_single(r) for r in results]
        successes = sum(1 for s in individual if s["success"])
        error_rates = [s["error_rate"] for s in individual]
        all_errors = []
        for s in individual:
            all_errors.extend(s["errors"])

        return {
            "total_runs": len(results),
            "success_rate": successes / len(results),
            "successful_runs": successes,
            "failed_runs": len(results) - successes,
            "mean_error_rate": sum(error_rates) / len(error_rates),
            "total_errors": len(all_errors),
            "unique_errors": len(set(all_errors)),
            "individual": individual,
        }

    @staticmethod
    def compare_topologies(
        hub_spoke_results: list[TopologyResult],
        spoke_spoke_results: list[TopologyResult],
    ) -> dict[str, Any]:
        """Compare reliability between the two topologies."""
        hs = ReliabilityScorer.score_batch(hub_spoke_results)
        ss = ReliabilityScorer.score_batch(spoke_spoke_results)

        return {
            "hub_spoke": hs,
            "spoke_spoke": ss,
            "success_rate_delta": hs["success_rate"] - ss["success_rate"],
            "error_rate_delta": hs["mean_error_rate"] - ss["mean_error_rate"],
            "more_reliable": (
                "hub-spoke"
                if hs["success_rate"] > ss["success_rate"]
                else "spoke-spoke"
                if ss["success_rate"] > hs["success_rate"]
                else "tie"
            ),
        }
