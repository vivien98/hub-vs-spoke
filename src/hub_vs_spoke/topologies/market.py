"""Market topology: competitive bidding via agent-economy's ClearinghouseEngine."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import structlog
from agent_economy.engine import ClearinghouseEngine, EngineSettings
from agent_economy.ledger import HashChainedLedger
from agent_economy.llm_anthropic import AnthropicJSONClient
from agent_economy.llm_openai import OpenAIJSONClient
from agent_economy.llm_router import LLMRouter
from agent_economy.openai_bidder import OpenAIBidder
from agent_economy.openai_executor import ExecutorSettings, OpenAIExecutor
from agent_economy.schemas import (
    EventType,
    JudgeSpec,
    PaymentRule,
    SubmissionKind,
    TaskSpec,
    VerifyMode,
    WorkerRuntime,
)
from agent_economy.state import replay_ledger

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.types import (
    CostRecord,
    TokenBudget,
    TopologyResult,
    Turn,
    Usage,
)

logger = structlog.get_logger()


def _build_llm_router() -> LLMRouter:
    """Construct an LLMRouter from environment API keys."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    openai_client = (
        OpenAIJSONClient(api_key=openai_key, base_url=None)
        if openai_key
        else None
    )
    anthropic_client = (
        AnthropicJSONClient(api_key=anthropic_key, base_url=None)
        if anthropic_key
        else None
    )
    return LLMRouter(openai=openai_client, anthropic=anthropic_client)


def _our_task_to_ae_spec(
    task: Task, *, judge_workers: list[str],
) -> TaskSpec:
    """Convert a hub_vs_spoke Task to an agent-economy TaskSpec."""
    return TaskSpec(
        id=task.task_id,
        title=task.description,
        description=task.prompt,
        bounty=100,
        max_attempts=3,
        verify_mode=VerifyMode.JUDGES,
        submission_kind=SubmissionKind.TEXT,
        judges=JudgeSpec(workers=judge_workers, min_passes=1),
    )


def _read_submission_text(run_dir: Path, event: dict[str, Any]) -> str:
    """Read submission text from a PATCH_SUBMITTED event's artifacts."""
    artifacts = event.get("artifacts", [])
    for art in artifacts:
        name = art.get("name", "") if isinstance(art, dict) else getattr(art, "name", "")
        path = art.get("path", "") if isinstance(art, dict) else getattr(art, "path", "")
        if name in ("submission.txt", "submission.json") and path:
            full = run_dir / path
            if full.exists():
                return full.read_text(encoding="utf-8").strip()
    return ""


def _extract_results_from_ledger(
    events: list[Any], run_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Parse ledger events to extract per-task market data.

    Returns a dict keyed by task_id with: winner, answer, bids, usage, attempts,
    reputation_at_completion.
    """
    results: dict[str, dict[str, Any]] = {}
    bids_by_task: dict[str, list[dict[str, Any]]] = {}
    attempts_by_task: dict[str, int] = {}

    for ev in events:
        etype = ev.type if hasattr(ev, "type") else ev.get("type")
        payload = ev.payload if hasattr(ev, "payload") else ev.get("payload", {})
        artifacts = ev.artifacts if hasattr(ev, "artifacts") else ev.get("artifacts", [])

        if etype == EventType.BID_SUBMITTED:
            tid = payload.get("task_id", "")
            bids_by_task.setdefault(tid, []).append({
                "worker_id": payload.get("worker_id", ""),
                "p_success": payload.get("bid", {}).get("self_assessed_p_success", 0.5),
                "ask": payload.get("bid", {}).get("ask", 0),
                "eta_minutes": payload.get("bid", {}).get("eta_minutes", 0),
            })

        elif etype == EventType.TASK_ASSIGNED:
            tid = payload.get("task_id", "")
            results.setdefault(tid, {})["winner"] = payload.get("worker_id", "")

        elif etype == EventType.PATCH_SUBMITTED:
            tid = payload.get("task_id", "")
            attempts_by_task[tid] = attempts_by_task.get(tid, 0) + 1

            # Build a dict-like object with artifacts for reading submission
            ev_dict = {"artifacts": []}
            for a in artifacts:
                if hasattr(a, "name"):
                    ev_dict["artifacts"].append({
                        "name": a.name, "path": a.path,
                    })
                else:
                    ev_dict["artifacts"].append(a)

            answer = _read_submission_text(run_dir, ev_dict)
            llm_usage = payload.get("llm_usage", {})

            results.setdefault(tid, {}).update({
                "answer": answer,
                "llm_usage": llm_usage,
                "worker_id": payload.get("worker_id", ""),
            })

        elif etype == EventType.TASK_COMPLETED:
            tid = payload.get("task_id", "")
            results.setdefault(tid, {})["verify_status"] = payload.get(
                "verify_status", ""
            )
            results.setdefault(tid, {})["success"] = payload.get("success", False)

    # Attach bids and attempts
    for tid, data in results.items():
        data["bids"] = bids_by_task.get(tid, [])
        data["attempts"] = attempts_by_task.get(tid, 0)

    return results


class MarketTopology:
    """Competitive market topology using agent-economy's ClearinghouseEngine.

    All tasks run in a single engine session so reputation develops across tasks.
    Use run_all() instead of the per-task run() method.
    """

    def __init__(
        self,
        worker_configs: list[tuple[str, str]],
        *,
        judge_workers: list[str] | None = None,
    ) -> None:
        """Initialise the market topology.

        Args:
            worker_configs: List of (worker_id, model_ref) pairs.
                Use 'claude:' prefix for Anthropic models.
            judge_workers: Worker IDs to use as judges. Defaults to first worker.
        """
        self._worker_configs = worker_configs
        self._judge_workers = judge_workers or [worker_configs[0][0]]

    @property
    def name(self) -> str:
        return "market"

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        """Run a single task through the market. Prefer run_all() for sessions."""
        results = await self.run_all([task], budget)
        return results[0]

    async def run_all(
        self, tasks: list[Task], budget: TokenBudget,
    ) -> list[TopologyResult]:
        """Run all tasks in one engine session, returning per-task results."""
        return await asyncio.to_thread(self._run_sync, tasks, budget)

    def _run_sync(
        self, tasks: list[Task], budget: TokenBudget,
    ) -> list[TopologyResult]:
        """Synchronous engine session (called via asyncio.to_thread)."""
        run_dir = Path(tempfile.mkdtemp(prefix="market-run-"))
        workspace_dir = run_dir / "workspace"
        workspace_dir.mkdir()

        try:
            return self._execute_engine(tasks, budget, run_dir, workspace_dir)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def _execute_engine(
        self,
        tasks: list[Task],
        budget: TokenBudget,
        run_dir: Path,
        workspace_dir: Path,
    ) -> list[TopologyResult]:
        t0 = time.perf_counter()

        # Build components
        llm = _build_llm_router()
        workers = [
            WorkerRuntime(worker_id=wid, model_ref=mref, reputation=1.0)
            for wid, mref in self._worker_configs
        ]
        task_specs = [
            _our_task_to_ae_spec(t, judge_workers=self._judge_workers)
            for t in tasks
        ]

        ledger = HashChainedLedger(run_dir / "ledger.jsonl")
        engine = ClearinghouseEngine(
            ledger=ledger,
            settings=EngineSettings(
                max_concurrency=1,
                deterministic=True,
                execution_timeout_seconds=300.0,
            ),
        )
        engine.create_run(
            run_id="market-yolo",
            payment_rule=PaymentRule.ASK,
            workers=workers,
            tasks=task_specs,
        )

        bidder = OpenAIBidder(
            llm=llm, payment_rule=PaymentRule.ASK, max_bids=2,
        )
        executor = OpenAIExecutor(
            llm=llm,
            workspace_dir=workspace_dir,
            run_dir=run_dir,
            workers=workers,
            settings=ExecutorSettings(judge_workers=self._judge_workers),
        )

        # Run engine rounds
        max_rounds = 30
        for round_num in range(max_rounds):
            engine.step(bidder=bidder, executor=executor)
            state = replay_ledger(events=list(ledger.iter_events()))

            done_count = sum(
                1 for t in state.tasks.values() if t.status in ("DONE", "REVIEW")
            )
            logger.info(
                "market_round",
                round=round_num,
                done=done_count,
                total=len(tasks),
            )
            if done_count >= len(tasks):
                break

        wall_ms = (time.perf_counter() - t0) * 1000

        # Extract results from ledger
        events = list(ledger.iter_events())
        state = replay_ledger(events=events)
        task_data = _extract_results_from_ledger(events, run_dir)

        # Build reputation snapshot
        reputations = {
            wid: w.reputation for wid, w in state.workers.items()
        }

        # Map to TopologyResult per task
        results: list[TopologyResult] = []
        for task in tasks:
            td = task_data.get(task.task_id, {})
            answer = td.get("answer", "")
            winner = td.get("winner", "unknown")
            llm_usage = td.get("llm_usage", {})

            # Build a Turn representing the market execution
            usage = Usage(
                input_tokens=int(llm_usage.get("input_tokens", 0)),
                output_tokens=int(llm_usage.get("output_tokens", 0)),
            )
            turns = [Turn(
                from_agent="market",
                to_agent=winner,
                message=task.prompt[:500],
                response=answer[:2000] if answer else "",
                usage=usage,
                model=winner,
            )]

            total_tokens = usage.total_tokens
            total_cost = CostRecord.from_usage(
                self._resolve_model_name(winner), usage,
            ).total_cost_usd

            errors: list[str] = []
            if not td.get("success", False):
                errors.append(
                    f"verify_status={td.get('verify_status', 'unknown')}"
                )

            metadata: dict[str, Any] = {
                "market_winner": winner,
                "market_bids": td.get("bids", []),
                "market_attempts": td.get("attempts", 0),
                "market_reputation": reputations,
            }

            results.append(TopologyResult(
                topology_name=self.name,
                task_id=task.task_id,
                final_answer=answer,
                turns=turns,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                wall_time_ms=wall_ms / len(tasks),  # amortise
                errors=errors,
                metadata=metadata,
            ))

        return results

    def _resolve_model_name(self, worker_id: str) -> str:
        """Map a worker_id back to the model name for cost lookup."""
        for wid, mref in self._worker_configs:
            if wid == worker_id:
                # Strip provider prefix (e.g., 'claude:claude-opus-4-6' -> 'claude-opus-4-6')
                return mref.split(":", 1)[-1] if ":" in mref else mref
        return worker_id
