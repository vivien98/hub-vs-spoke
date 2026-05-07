"""Futarchy topology: LMSR prediction market for agent selection (Hanson 2003).

Each agent submits a confidence signal P(solve correctly). An LMSR-based market
aggregates these signals into prices, selects the winner, and optionally triggers
a minority-veto synthesis if a dissenting coalition is strong enough. Reputation
updates via Brier score across tasks when run_all() is used.

Theory: "Intrafirm Futarchy and Organisational Survival" — Section 4 (LMSR),
Section 5 (incentive compatibility), Section 6 (optimal design with minority veto).
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

import structlog

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.topologies._shared import AgentLike, build_result, execute_with_retry
from hub_vs_spoke.types import Timer, TokenBudget, TopologyResult, Turn

logger = structlog.get_logger()

_SIGNAL_PROMPT = """\
You are bidding in a prediction market. Estimate your probability of producing a \
high-quality solution (score >= 7/10) to the task below.

Consider: task type, your strengths, approach complexity.

TASK:
{task_prompt}

Respond with ONLY valid JSON — no markdown fences, no commentary:
{{"self_confidence": <float 0.0-1.0>, "approach_summary": "<one sentence>"}}
"""

_SYNTHESIS_PROMPT = """\
Two agents independently solved this task. The prediction market chose Agent A, but \
a dissenting minority preferred Agent B. Synthesise the best answer, incorporating \
Agent B's insights where they improve on A. If both agree, keep Agent A's wording.

TASK:
{task_prompt}

Agent A (market winner, stated confidence {conf_a:.2f}):
{answer_a}

Agent B (minority dissenter, stated confidence {conf_b:.2f}):
{answer_b}

Produce a single coherent final answer.
"""

_CALIBRATION_PROMPT = """\
You just answered the task below. Rate the quality of YOUR OWN answer from 1-10:
  10 = fully correct, complete, well-reasoned
   7 = mostly correct, minor gaps
   5 = partially correct
   3 = major errors or omissions
   1 = wrong or empty

TASK: {task_prompt}

YOUR ANSWER:
{answer}

Respond with ONLY valid JSON: {{"self_score": <int 1-10>, "reason": "<one sentence>"}}
"""


def _lmsr_prices(confidences: dict[str, float], lambda_lmsr: float) -> dict[str, float]:
    """LMSR market prices: softmax over confidence / lambda.

    price_i = exp(c_i / λ) / Σ_j exp(c_j / λ)

    Higher λ flattens the distribution (more conservative winner margin).
    Lower λ sharpens it (winner takes most probability mass).
    Numerically stable via the log-sum-exp trick.
    """
    if not confidences:
        return {}
    scaled = {k: v / lambda_lmsr for k, v in confidences.items()}
    max_s = max(scaled.values())
    exps = {k: math.exp(v - max_s) for k, v in scaled.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def _parse_confidence(content: str) -> tuple[float, str]:
    """Extract (self_confidence, approach_summary) from agent JSON response."""
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        obj = json.loads(content[start:end])
        conf = float(obj.get("self_confidence", 0.5))
        conf = max(0.01, min(0.99, conf))
        summary = str(obj.get("approach_summary", ""))[:300]
        return conf, summary
    except (ValueError, json.JSONDecodeError):
        pass
    # Fallback: grab the first float in (0,1)
    hits = re.findall(r"\b(0\.\d+|1\.0)\b", content)
    if hits:
        return max(0.01, min(0.99, float(hits[0]))), content[:200]
    return 0.5, content[:200]


def _parse_self_score(content: str) -> float:
    """Extract self_score (1-10) from calibration probe response."""
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        obj = json.loads(content[start:end])
        return float(obj.get("self_score", 5))
    except (ValueError, json.JSONDecodeError):
        hits = re.findall(r"\b(10|[1-9])\b", content)
        return float(hits[0]) if hits else 5.0


class FutarchyTopology:
    """Prediction-market agent coordination via LMSR (Hanson 2003).

    Protocol per task:
      1. SIGNAL    — each agent submits P(solve correctly) + one-line approach
      2. MARKET    — LMSR aggregates signals weighted by accumulated reputation
      3. WINNER    — highest-priced agent executes the task
      4. VETO      — if a dissenting coalition reaches the threshold, a second
                     agent also executes (Theorem 6.1 minority-veto clause)
      5. SYNTHESIS — hub merges winner + dissenter outputs when veto fires
      6. CALIBRATE — in run_all(), winner self-assesses → Brier-score reputation update

    Parameters
    ----------
    agents : dict[str, AgentLike]
        Named market participants.  At least 2 required.
    hub : AgentLike
        Synthesis agent used when the minority veto fires.
    lambda_lmsr : float
        LMSR liquidity parameter λ.  Low → manipulable; high → ignores signals.
        Optimal at intermediate value (Prop 5.3).  Default 1.0.
    veto_threshold : float
        Minimum raw confidence a non-winner needs to join the veto coalition.
    veto_min_coalition : int
        Minimum number of dissenters required to trigger a veto.
    """

    def __init__(
        self,
        agents: dict[str, AgentLike],
        hub: AgentLike,
        *,
        lambda_lmsr: float = 1.0,
        veto_threshold: float = 0.55,
        veto_min_coalition: int = 1,
    ) -> None:
        if len(agents) < 2:
            raise ValueError("FutarchyTopology requires at least 2 agents")
        self.agents = agents
        self.hub = hub
        self.lambda_lmsr = lambda_lmsr
        self.veto_threshold = veto_threshold
        self.veto_min_coalition = veto_min_coalition
        # Reputation: multiplicative calibration weight, starts at 1.0
        self._reputation: dict[str, float] = {name: 1.0 for name in agents}
        self._calibration_log: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "futarchy"

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        """Run one task through the futarchy market using current reputation."""
        turns: list[Turn] = []
        errors: list[str] = []
        total_tokens = 0

        with Timer() as wall_timer:
            # ── Phase 1: Signal Collection ──────────────────────────────────
            signal_prompt = _SIGNAL_PROMPT.format(task_prompt=task.prompt)
            raw_confidences: dict[str, float] = {}
            approach_summaries: dict[str, str] = {}

            for agent_name, agent in self.agents.items():
                if budget.exceeded(total_tokens, len(turns)):
                    errors.append("Budget exhausted during signal phase")
                    break
                try:
                    resp = await agent.act(signal_prompt)
                    total_tokens += resp.usage.total_tokens
                    turns.append(Turn(
                        from_agent="market",
                        to_agent=agent_name,
                        message=signal_prompt[:300],
                        response=resp.content,
                        usage=resp.usage,
                        latency_ms=resp.latency_ms,
                        model=resp.model,
                    ))
                    conf, summary = _parse_confidence(resp.content)
                    raw_confidences[agent_name] = conf
                    approach_summaries[agent_name] = summary
                    logger.debug("signal", agent=agent_name, confidence=conf)
                except Exception as exc:
                    errors.append(f"Signal from {agent_name} failed: {exc}")
                    raw_confidences[agent_name] = 0.5
                    logger.warning("signal_failed", agent=agent_name, error=str(exc))

            if not raw_confidences:
                return build_result(
                    self.name, task, "", turns, total_tokens, errors, wall_timer,
                )

            # ── Phase 2: LMSR Market Aggregation ────────────────────────────
            # Reputation scales effective confidence before softmax
            eff_confidences = {
                name: conf * self._reputation.get(name, 1.0)
                for name, conf in raw_confidences.items()
            }
            market_prices = _lmsr_prices(eff_confidences, self.lambda_lmsr)
            winner_name = max(market_prices, key=market_prices.get)

            logger.info(
                "market_resolved",
                task=task.task_id,
                winner=winner_name,
                prices={k: round(v, 3) for k, v in market_prices.items()},
            )

            # ── Phase 3: Minority Veto Check ─────────────────────────────────
            non_winner_confs = {
                k: raw_confidences[k]
                for k in raw_confidences
                if k != winner_name
            }
            veto_coalition = [
                (name, conf)
                for name, conf in non_winner_confs.items()
                if conf >= self.veto_threshold
            ]
            veto_triggered = len(veto_coalition) >= self.veto_min_coalition

            if veto_triggered:
                logger.info(
                    "minority_veto",
                    coalition=[v[0] for v in veto_coalition],
                    winner=winner_name,
                )

            # ── Phase 4: Execute Winner ──────────────────────────────────────
            if budget.exceeded(total_tokens, len(turns)):
                result = build_result(
                    self.name, task, "", turns, total_tokens, errors, wall_timer,
                )
                result.metadata.update(self._build_metadata(
                    winner_name, market_prices, raw_confidences, eff_confidences,
                    veto_triggered, veto_coalition, approach_summaries,
                ))
                return result

            winner_out = await execute_with_retry(
                self.agents[winner_name],
                task.prompt,
                from_agent="market",
                max_retries=1,
                turns=turns,
                errors=errors,
            )
            total_tokens += winner_out["tokens"]
            final_answer = winner_out["content"]

            # ── Phase 5: Veto Execution + Hub Synthesis ──────────────────────
            if veto_triggered and not budget.exceeded(total_tokens, len(turns)):
                dissenter_name, dissenter_conf = max(veto_coalition, key=lambda x: x[1])
                dissenter_out = await execute_with_retry(
                    self.agents[dissenter_name],
                    task.prompt,
                    from_agent="market_veto",
                    max_retries=0,
                    turns=turns,
                    errors=errors,
                )
                total_tokens += dissenter_out["tokens"]

                if not budget.exceeded(total_tokens, len(turns)):
                    synth_prompt = _SYNTHESIS_PROMPT.format(
                        task_prompt=task.prompt,
                        conf_a=raw_confidences[winner_name],
                        answer_a=winner_out["content"],
                        conf_b=dissenter_conf,
                        answer_b=dissenter_out["content"],
                    )
                    hub_resp = await self.hub.act(synth_prompt)
                    total_tokens += hub_resp.usage.total_tokens
                    turns.append(Turn(
                        from_agent="veto_synthesis",
                        to_agent=self.hub.name,
                        message=synth_prompt[:400],
                        response=hub_resp.content,
                        usage=hub_resp.usage,
                        latency_ms=hub_resp.latency_ms,
                        model=hub_resp.model,
                    ))
                    final_answer = hub_resp.content

        result = build_result(
            self.name, task, final_answer, turns, total_tokens, errors, wall_timer,
        )
        result.metadata.update(self._build_metadata(
            winner_name, market_prices, raw_confidences, eff_confidences,
            veto_triggered, veto_coalition, approach_summaries,
        ))
        return result

    def _build_metadata(
        self,
        winner_name: str,
        market_prices: dict[str, float],
        raw_confidences: dict[str, float],
        eff_confidences: dict[str, float],
        veto_triggered: bool,
        veto_coalition: list[tuple[str, float]],
        approach_summaries: dict[str, str],
    ) -> dict[str, Any]:
        return {
            "futarchy_winner": winner_name,
            "futarchy_prices": {k: round(v, 4) for k, v in market_prices.items()},
            "futarchy_confidences": {k: round(v, 3) for k, v in raw_confidences.items()},
            "futarchy_effective_confidences": {k: round(v, 3) for k, v in eff_confidences.items()},
            "futarchy_reputation": {k: round(v, 4) for k, v in self._reputation.items()},
            "futarchy_lambda": self.lambda_lmsr,
            "futarchy_veto_triggered": veto_triggered,
            "futarchy_veto_coalition": [v[0] for v in veto_coalition],
            "futarchy_approach_summaries": approach_summaries,
        }

    async def _calibration_probe(
        self,
        agent: AgentLike,
        task: Task,
        answer: str,
        turns: list[Turn],
        errors: list[str],
    ) -> float:
        """Ask the winning agent to self-assess its answer on a 1-10 scale."""
        probe = _CALIBRATION_PROMPT.format(
            task_prompt=task.prompt[:500],
            answer=answer[:1000],
        )
        try:
            resp = await agent.act(probe)
            turns.append(Turn(
                from_agent="calibration",
                to_agent=agent.name,
                message=probe[:300],
                response=resp.content,
                usage=resp.usage,
                latency_ms=resp.latency_ms,
                model=resp.model,
            ))
            return _parse_self_score(resp.content)
        except Exception as exc:
            errors.append(f"Calibration probe failed: {exc}")
            return 5.0

    def _update_reputation(
        self,
        agent_name: str,
        predicted_confidence: float,
        actual_score_0_10: float,
    ) -> None:
        """Brier-score reputation update.

        Brier score B = (predicted_p - actual_p)^2 ∈ [0, 1].
        Well-calibrated agents (B → 0) preserve reputation.
        Poorly-calibrated agents (B → 1) lose reputation weight.
        Reputation bounds: [0.4, 2.0].
        """
        actual_p = actual_score_0_10 / 10.0
        brier = (predicted_confidence - actual_p) ** 2
        old_rep = self._reputation.get(agent_name, 1.0)
        # Multiplicative damping: bad calibration → down, near-perfect → flat
        new_rep = max(0.4, min(2.0, old_rep * (1.0 - 0.20 * brier)))
        self._reputation[agent_name] = new_rep

        entry: dict[str, Any] = {
            "agent": agent_name,
            "predicted": round(predicted_confidence, 3),
            "actual_p": round(actual_p, 3),
            "brier": round(brier, 4),
            "rep_before": round(old_rep, 4),
            "rep_after": round(new_rep, 4),
        }
        self._calibration_log.append(entry)
        logger.info("reputation_update", **entry)

    async def run_all(
        self,
        tasks: list[Task],
        budget: TokenBudget,
    ) -> list[TopologyResult]:
        """Run all tasks sequentially with cross-task reputation tracking.

        After each task the market winner self-assesses its answer. The resulting
        Brier score updates the winner's reputation weight for subsequent tasks.
        Agents that are well-calibrated (their stated confidence matches actual
        outcome) accumulate higher reputation and have their future signals
        up-weighted in the LMSR.
        """
        results: list[TopologyResult] = []

        for task in tasks:
            result = await self.run(task, budget)

            winner = result.metadata.get("futarchy_winner", "")
            winner_conf = result.metadata.get("futarchy_confidences", {}).get(winner, 0.5)

            if winner and winner in self.agents and result.final_answer:
                probe_turns: list[Turn] = []
                probe_errors: list[str] = []
                self_score = await self._calibration_probe(
                    self.agents[winner], task, result.final_answer,
                    probe_turns, probe_errors,
                )
                result.turns.extend(probe_turns)
                result.errors.extend(probe_errors)
                self._update_reputation(winner, winner_conf, self_score)

            result.metadata["futarchy_calibration_log"] = list(self._calibration_log)
            results.append(result)

        return results
