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
    Task(
        task_id="synthesis-004",
        category=TaskCategory.SYNTHESIS,
        prompt=(
            "A hospital system is evaluating three architectures for their new "
            "electronic health records (EHR) platform that must serve 12 hospitals, "
            "4,000 physicians, and meet HIPAA requirements:\n\n"
            "(a) Monolithic application with a single shared database\n"
            "(b) Microservices with per-service databases and an API gateway\n"
            "(c) Modular monolith with domain boundaries enforced by module interfaces\n\n"
            "For each architecture, analyse:\n"
            "- Data consistency and cross-domain queries (e.g. 'show all medications "
            "for patient X across all departments')\n"
            "- Compliance and audit trail requirements under HIPAA\n"
            "- Deployment and rollback risk across 12 hospitals\n"
            "- Team scaling (currently 40 developers, growing to 120 over 2 years)\n"
            "- Failure blast radius and availability\n\n"
            "Your analysis must address a specific technical tension: the platform "
            "needs both real-time cross-department patient views AND the ability for "
            "individual hospitals to customise workflows without affecting others. "
            "Explain how each architecture handles (or fails to handle) this tension.\n\n"
            "Conclude with a phased recommendation (what to build first, what to migrate "
            "to later) with explicit criteria for when to trigger each phase transition."
        ),
        description="EHR platform architecture with regulatory and scaling constraints",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) address all five dimensions for each architecture with HIPAA-specific "
            "substance (not generic 'security is important' — must mention audit logging, "
            "BAAs, minimum necessary standard, encryption at rest/transit), (2) explicitly "
            "tackle the real-time-cross-department vs per-hospital-customisation tension "
            "for each option (e.g. monolith: easy cross-queries but customisation requires "
            "feature flags or multi-tenancy; microservices: per-hospital deploys are natural "
            "but cross-department views require choreography/orchestration; modular monolith: "
            "shared process makes cross-queries easy but customisation is limited to module "
            "configuration), (3) phased recommendation must have concrete trigger criteria "
            "(not 'when the team is ready' but specific metrics like team size, deployment "
            "frequency, or module coupling measurements), (4) rollback analysis must be "
            "specific to healthcare (e.g. can't just 'roll back' if patient data was written "
            "under new schema). Score 1-4 for generic architecture comparison without "
            "healthcare specifics. Score 5-7 for correct analysis but weak on the tension "
            "or vague phase triggers. Score 8-10 for healthcare-grounded analysis with "
            "concrete phase transition criteria. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="synthesis-005",
        category=TaskCategory.SYNTHESIS,
        prompt=(
            "Write a critical analysis of the following claim:\n\n"
            "'Microservices are always better than monoliths for organisations with "
            "more than 50 engineers.'\n\n"
            "Your analysis must:\n"
            "1. Identify exactly three hidden assumptions in this claim and explain why "
            "each is problematic.\n"
            "2. Provide one real-world counterexample where a large engineering org "
            "(>50 engineers) successfully used a monolith and explain WHY it worked "
            "for them. Name a specific company or well-documented project.\n"
            "3. Provide one real-world example where microservices adoption by a large "
            "org led to significant problems. Name a specific company or well-documented "
            "case.\n"
            "4. Propose a decision framework (not a blanket rule) for when to adopt "
            "microservices, expressed as 3-5 concrete yes/no questions an engineering "
            "leader should ask. Each question must have a clear rationale.\n\n"
            "Do NOT hedge every sentence. Take clear positions where the evidence "
            "supports them."
        ),
        description="Critical analysis of microservices claim with real counterexamples",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) identify three genuinely distinct hidden assumptions — not "
            "restatements (good examples: assumes team boundaries align with service "
            "boundaries; assumes the org has operational maturity for distributed systems; "
            "assumes the product domain has clean bounded contexts), (2) name a real "
            "company for the monolith success case with accurate details (e.g. Shopify's "
            "modular monolith, or Stack Overflow's monolith serving massive traffic), "
            "(3) name a real company for the microservices failure case with specifics "
            "(e.g. Segment's move back to monolith, or the well-documented 'distributed "
            "monolith' anti-pattern cases), (4) decision framework must be actionable "
            "yes/no questions with clear rationale (not vague like 'are you ready?'). "
            "Score 1-3 for generic analysis without real examples or with fabricated cases. "
            "Score 4-6 for real examples but weak assumptions or vague framework. "
            "Score 8-10 for accurate real-world examples, distinct assumptions, and a "
            "framework a practitioner would actually use. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(SYNTHESIS_TASKS)
