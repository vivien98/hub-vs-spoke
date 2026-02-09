"""Research benchmark tasks: multi-step information synthesis."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

RESEARCH_TASKS = [
    Task(
        task_id="research-001",
        category=TaskCategory.RESEARCH,
        prompt=(
            "Compare and contrast three approaches to database connection pooling "
            "in Python web applications: SQLAlchemy's built-in pool, pgbouncer, "
            "and asyncpg's pool. Cover performance characteristics, configuration "
            "complexity, and failure modes."
        ),
        description="Compare database connection pooling strategies",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must cover all three approaches with accurate technical details. "
            "Should address: max connections, timeout handling, connection recycling, "
            "and trade-offs for async vs sync workloads."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="research-002",
        category=TaskCategory.RESEARCH,
        prompt=(
            "Explain the trade-offs between hub-and-spoke and mesh topologies in "
            "distributed systems. Provide concrete examples from real systems "
            "(e.g., Kafka, service meshes, CDNs). Discuss fault tolerance, latency, "
            "and operational complexity."
        ),
        description="Distributed systems topology trade-offs",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must reference at least 2 real systems per topology. Should cover "
            "single-point-of-failure, message amplification, and operational overhead."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="research-003",
        category=TaskCategory.RESEARCH,
        prompt=(
            "Summarise the key differences between supervised fine-tuning, RLHF, "
            "and DPO for aligning language models. What are the data requirements, "
            "computational costs, and known failure modes of each?"
        ),
        description="LLM alignment technique comparison",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must accurately describe all three methods with correct technical details. "
            "Should mention reward model training for RLHF, preference pairs for DPO, "
            "and data quality requirements for SFT."
        ),
        difficulty="medium",
    ),
]

default_registry.register_many(RESEARCH_TASKS)
