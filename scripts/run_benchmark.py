#!/usr/bin/env python
"""CLI benchmark runner: execute the full topology comparison matrix and emit JSONL results.

Usage:
    python scripts/run_benchmark.py                     # run all configurations
    python scripts/run_benchmark.py --category coding   # single category
    python scripts/run_benchmark.py --reps 5            # 5 repetitions per config
    python scripts/run_benchmark.py --dry-run           # show matrix without running
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure the src package is importable when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import structlog

from hub_vs_spoke.agents.agent import Agent
from hub_vs_spoke.providers.anthropic_provider import AnthropicProvider
from hub_vs_spoke.providers.openai_provider import OpenAIProvider
from hub_vs_spoke.tasks import TaskCategory, default_registry
from hub_vs_spoke.topologies.hub_spoke import HubSpokeTopology
from hub_vs_spoke.topologies.spoke_spoke import SpokeSpokeTopology
from hub_vs_spoke.types import TokenBudget, TopologyResult

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Configuration matrix
# ---------------------------------------------------------------------------

@dataclass
class TopologyConfig:
    label: str
    topology_type: str  # "hub-spoke" or "spoke-spoke"
    hub_model: str | None
    spoke_models: list[str]


DEFAULT_CONFIGS: list[TopologyConfig] = [
    TopologyConfig("claude-hub+gpt-spokes", "hub-spoke", "claude-sonnet-4-20250514",
                   ["gpt-4o-mini"] * 3),
    TopologyConfig("gpt-hub+claude-spokes", "hub-spoke", "gpt-4o",
                   ["claude-3-5-haiku-20241022"] * 3),
    TopologyConfig("gpt-peers", "spoke-spoke", None, ["gpt-4o"] * 3),
    TopologyConfig("claude-peers", "spoke-spoke", None,
                   ["claude-sonnet-4-20250514"] * 3),
    TopologyConfig("mixed-peers", "spoke-spoke", None,
                   ["gpt-4o", "claude-sonnet-4-20250514", "gpt-4o-mini"]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider(model: str) -> OpenAIProvider | AnthropicProvider:
    """Create the right provider for a given model name.

    SDKs read API keys from OPENAI_API_KEY / ANTHROPIC_API_KEY automatically.
    """
    if model.startswith("claude"):
        return AnthropicProvider(model=model)
    return OpenAIProvider(model=model)


def _build_topology(config: TopologyConfig) -> HubSpokeTopology | SpokeSpokeTopology:
    """Instantiate a topology from its config."""
    if config.topology_type == "hub-spoke" and config.hub_model:
        hub = Agent(
            name="hub",
            provider=_make_provider(config.hub_model),
            system_prompt="You are an orchestrator. Decompose tasks and synthesise results.",
            max_tokens=1024,
        )
        spokes = [
            Agent(
                name=f"spoke-{i}",
                provider=_make_provider(m),
                system_prompt="You are a specialist worker. Complete subtasks concisely.",
                max_tokens=768,
            )
            for i, m in enumerate(config.spoke_models)
        ]
        return HubSpokeTopology(hub=hub, spokes=spokes)

    peers = [
        Agent(
            name=f"peer-{i}",
            provider=_make_provider(m),
            system_prompt="You are a peer in a collaborative team. Be concise and direct.",
            max_tokens=768,
        )
        for i, m in enumerate(config.spoke_models)
    ]
    return SpokeSpokeTopology(peers=peers)


def _result_to_jsonl(
    config: TopologyConfig,
    category: str,
    task_id: str,
    rep: int,
    result: TopologyResult,
) -> dict[str, Any]:
    """Convert a run result to a JSONL-serialisable dict."""
    return {
        "config_label": config.label,
        "topology_type": config.topology_type,
        "hub_model": config.hub_model,
        "spoke_models": config.spoke_models,
        "category": category,
        "task_id": task_id,
        "repetition": rep,
        "success": result.success,
        "total_tokens": result.total_tokens,
        "total_cost_usd": result.total_cost_usd,
        "wall_time_ms": round(result.wall_time_ms, 1),
        "num_turns": len(result.turns),
        "num_errors": len(result.errors),
        "errors": result.errors[:5],
        "answer_length": len(result.final_answer),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

async def run_benchmark(
    configs: list[TopologyConfig],
    categories: list[TaskCategory],
    reps: int,
    budget: TokenBudget,
    output_path: Path,
) -> None:
    """Run the full benchmark matrix and write JSONL results."""
    all_results: list[dict[str, Any]] = []
    total_runs = 0
    total_errors = 0

    with open(output_path, "w") as fout:
        for config in configs:
            for category in categories:
                tasks = default_registry.by_category(category)
                if not tasks:
                    logger.warning("no_tasks", category=category.value)
                    continue

                for task in tasks:
                    for rep in range(reps):
                        total_runs += 1
                        topology = _build_topology(config)
                        label = (
                            f"{config.label}/{category.value}"
                            f"/{task.task_id}/rep{rep}"
                        )

                        logger.info("run_start", run=label)
                        t0 = time.perf_counter()

                        try:
                            result = await topology.run(task, budget)
                        except Exception as exc:
                            logger.error("run_failed", run=label, error=str(exc))
                            total_errors += 1
                            result = TopologyResult(
                                topology_name=config.topology_type,
                                task_id=task.task_id,
                                final_answer="",
                                errors=[str(exc)],
                                wall_time_ms=(time.perf_counter() - t0) * 1000,
                            )

                        row = _result_to_jsonl(
                            config, category.value, task.task_id, rep, result
                        )
                        fout.write(json.dumps(row) + "\n")
                        fout.flush()
                        all_results.append(row)

                        status = "OK" if result.success else "FAIL"
                        logger.info(
                            "run_done", run=label, status=status,
                            tokens=result.total_tokens,
                            time_ms=round(result.wall_time_ms, 0),
                        )

    _print_summary(all_results, total_runs, total_errors)


def _print_summary(
    results: list[dict[str, Any]], total_runs: int, total_errors: int,
) -> None:
    """Print a human-readable summary of benchmark results."""
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Total runs: {total_runs}  |  Errors: {total_errors}\n")

    # By config
    by_config: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_config.setdefault(r["config_label"], []).append(r)

    fmt = "{:<30} {:>5} {:>5} {:>6} {:>8} {:>10}"
    print(fmt.format("Config", "Runs", "Pass", "Rate", "Tokens", "Time(ms)"))
    print("-" * 70)
    for label, rows in sorted(by_config.items()):
        n = len(rows)
        passed = sum(1 for r in rows if r["success"])
        avg_tok = sum(r["total_tokens"] for r in rows) / n
        avg_ms = sum(r["wall_time_ms"] for r in rows) / n
        print(fmt.format(label, n, passed, f"{passed/n:.0%}", f"{avg_tok:.0f}", f"{avg_ms:.0f}"))

    # By category
    print()
    cat_fmt = "{:<20} {:>5} {:>5} {:>6}"
    print(cat_fmt.format("Category", "Runs", "Pass", "Rate"))
    print("-" * 38)
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    for cat, rows in sorted(by_cat.items()):
        n = len(rows)
        passed = sum(1 for r in rows if r["success"])
        print(cat_fmt.format(cat, n, passed, f"{passed/n:.0%}"))

    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run hub-vs-spoke benchmark matrix")
    parser.add_argument("--category", type=str, default=None,
                        help="Run only this task category")
    parser.add_argument("--reps", type=int, default=1,
                        help="Repetitions per configuration")
    parser.add_argument("--budget-tokens", type=int, default=20_000,
                        help="Max tokens per run")
    parser.add_argument("--budget-turns", type=int, default=15,
                        help="Max turns per run")
    parser.add_argument("--output", type=str, default="benchmark_results.jsonl",
                        help="Output JSONL path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the matrix without running")
    parser.add_argument("--config", type=str, default=None,
                        help="Run only configs matching this label substring")
    args = parser.parse_args()

    # Resolve categories
    if args.category:
        try:
            categories = [TaskCategory(args.category)]
        except ValueError:
            print(f"Unknown category: {args.category}")
            print(f"Available: {[c.value for c in TaskCategory]}")
            sys.exit(1)
    else:
        categories = list(TaskCategory)

    # Filter configs
    configs = DEFAULT_CONFIGS
    if args.config:
        configs = [c for c in configs if args.config in c.label]
        if not configs:
            print(f"No configs match '{args.config}'")
            sys.exit(1)

    budget = TokenBudget(max_total_tokens=args.budget_tokens, max_turns=args.budget_turns)

    if args.dry_run:
        print("Benchmark matrix (dry run):\n")
        total = 0
        for config in configs:
            for cat in categories:
                for task in default_registry.by_category(cat):
                    for rep in range(args.reps):
                        total += 1
                        print(f"  {config.label} / {cat.value} / {task.task_id} / rep{rep}")
        print(f"\nTotal runs: {total}")
        return

    output_path = Path(args.output)
    cats = [c.value for c in categories]
    print(f"Running benchmark -> {output_path}")
    print(f"Configs: {len(configs)}  |  Categories: {cats}  |  Reps: {args.reps}")
    print(f"Budget: {budget.max_total_tokens} tokens, {budget.max_turns} turns\n")
    asyncio.run(run_benchmark(configs, categories, args.reps, budget, output_path))


if __name__ == "__main__":
    main()
