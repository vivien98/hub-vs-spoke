"""Synthesis tasks: comparative analysis, argument construction, multi-level explanation."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

SYNTHESIS_TASKS = [
    Task(
        task_id="synthesis-001",
        category=TaskCategory.SYNTHESIS,
        prompt=(
            "A fintech startup processing 50,000 transactions per second needs to "
            "choose a data consistency strategy for their distributed payment system. "
            "Compare these three approaches:\n\n"
            "(a) Two-phase commit (2PC)\n"
            "(b) Saga pattern with compensating transactions\n"
            "(c) Event sourcing with CQRS\n\n"
            "For each approach, analyse:\n"
            "- Transaction throughput under load\n"
            "- Consistency guarantees (and their limits)\n"
            "- Failure recovery behavior\n"
            "- Operational complexity\n\n"
            "Conclude with a specific recommendation for this use case, justified by "
            "the analysis above."
        ),
        description="Distributed consistency strategy comparison for high-throughput payments",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) accurately describe all three approaches with correct technical "
            "specifics — not generic summaries (e.g., 2PC's blocking nature and "
            "coordinator SPOF; saga's temporary inconsistency window and compensation "
            "complexity; event sourcing's append-only log and projection rebuild cost), "
            "(2) address all four dimensions for each approach with substance, "
            "(3) note specific limitations relevant to 50K TPS payments (e.g., 2PC's "
            "latency penalty from synchronous coordination; saga's challenge with "
            "non-compensable operations like external transfers; CQRS read-model lag), "
            "(4) recommendation must follow logically from the analysis and reference "
            "the specific requirements. Score 1-3 if any approach is described "
            "inaccurately or if analysis is shallow. Score 7-10 if all four dimensions "
            "are treated with genuine depth and the recommendation is well-justified. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="synthesis-002",
        category=TaskCategory.SYNTHESIS,
        prompt=(
            "A 200-person engineering organization is deciding between a monorepo "
            "(single repository for all services and libraries) and a polyrepo "
            "(one repository per service). They currently have 15 microservices, "
            "8 shared libraries, and deploy roughly 20 times per day.\n\n"
            "Construct the strongest possible case FOR the monorepo (4 arguments), "
            "then the strongest possible case AGAINST it, i.e. for polyrepo "
            "(4 arguments). Each side must address:\n"
            "- CI/CD pipeline design\n"
            "- Code sharing and dependency management\n"
            "- Team autonomy\n"
            "- Developer onboarding\n\n"
            "Then provide a balanced recommendation that honestly acknowledges what "
            "the organization would be giving up with either choice."
        ),
        description="Adversarial debate: monorepo vs polyrepo with forced balance",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) present 4 substantive arguments per side — not strawmen "
            "(e.g., monorepo pro: atomic cross-service refactors, single version of "
            "shared libs; polyrepo pro: independent deploy pipelines, blast-radius "
            "isolation), (2) address all four topics on BOTH sides with specifics "
            "relevant to the scenario (200 people, 15 services, 8 shared libs, 20 "
            "deploys/day), (3) show understanding of concrete trade-offs (diamond "
            "dependency problem, build-cache invalidation, trunk-based vs branch-based "
            "development), (4) recommendation must acknowledge genuine downsides of "
            "the chosen approach — not hand-wave them. Score 1-3 for one-sided or "
            "generic arguments. Score 7-10 for arguments grounded in the specific "
            "scenario that a practitioner would find credible. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="synthesis-003",
        category=TaskCategory.SYNTHESIS,
        prompt=(
            "Explain how distributed consensus works — using Raft as the concrete "
            "example — at three levels:\n\n"
            "1. For a non-technical CEO (2-3 sentences, analogy-based, focused on "
            "why it matters for the business)\n"
            "2. For a senior backend engineer (one paragraph covering leader election, "
            "log replication, and safety guarantees)\n"
            "3. For a distributed systems researcher (one paragraph addressing the "
            "FLP impossibility result, how Raft navigates it via randomized election "
            "timeouts, and the specific trade-offs Raft makes versus Multi-Paxos in "
            "understandability vs. flexibility)\n\n"
            "Each level must be genuinely calibrated to its audience."
        ),
        description="Multi-audience technical explanation with calibrated depth",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) CEO explanation uses an accessible analogy, contains zero "
            "jargon (no 'log replication', 'quorum', etc.), and explains business "
            "relevance (data safety, uptime), (2) engineer explanation correctly "
            "covers leader election (term-based, majority vote), log replication "
            "(append entries, commit on majority ack), and safety (election safety, "
            "leader completeness), (3) researcher explanation references FLP "
            "impossibility (no deterministic consensus in async systems with crash "
            "faults), explains randomized timeouts as the liveness escape hatch, and "
            "makes a specific Raft-vs-Multi-Paxos comparison (single-decree vs. "
            "multi-decree, fixed leader vs. flexible, reduced state space vs. "
            "generality), (4) the three levels must sound genuinely different in "
            "vocabulary and depth. Score 1-3 if all three levels read the same, or "
            "if the researcher level oversimplifies. Score 8-10 if each level is "
            "clearly calibrated and technically accurate for its audience. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(SYNTHESIS_TASKS)
