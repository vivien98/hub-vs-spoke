"""Reasoning benchmark tasks: probability, constraint satisfaction, causal analysis."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

REASONING_TASKS = [
    Task(
        task_id="reasoning-001",
        category=TaskCategory.REASONING,
        prompt=(
            "A bag contains 5 red marbles, 4 blue marbles, and 3 green marbles. "
            "You draw 4 marbles without replacement. What is the probability that "
            "you draw exactly 2 red marbles AND at least 1 green marble?\n\n"
            "Show your complete working. Express the final answer as a simplified "
            "fraction."
        ),
        description="Combinatorial probability with multiple constraints",
        expected_answer="10/33",
        eval_method=EvalMethod.EXACT_MATCH,
        eval_rubric=(
            "The correct answer is 10/33. Working: C(12,4)=495 total ways. "
            "Exactly 2 red from 5: C(5,2)=10. Remaining 2 from 7 non-red: C(7,2)=21. "
            "So 2-red draws = 210. Subtract 2-red-0-green (2 red + 2 blue): "
            "C(5,2)*C(4,2)=60. Result: (210-60)/495 = 150/495 = 10/33. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="reasoning-002",
        category=TaskCategory.REASONING,
        prompt=(
            "Schedule 6 conference talks (A through F) into 3 rooms across 2 time "
            "slots (morning and afternoon). Each room holds exactly one talk per "
            "slot — so all 6 slots are filled.\n\n"
            "Constraints:\n"
            "1. Talks A and B share a speaker, so they CANNOT be in the same time slot.\n"
            "2. Talk C requires special AV equipment only available in Room 1.\n"
            "3. Talks D and E attract the same audience, so they CANNOT be in the same "
            "time slot.\n"
            "4. Talk F must be in the morning slot.\n"
            "5. Talk A must be in the afternoon slot.\n\n"
            "Provide a valid schedule as a table (Room 1/2/3 x Morning/Afternoon) and "
            "then explicitly verify that each of the 5 constraints is satisfied."
        ),
        description="Multi-constraint scheduling with explicit verification",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Schedule must: (1) place all 6 talks in exactly 6 slots (3 rooms x "
            "2 time slots), with no talk repeated or missing, (2) A and B in different "
            "time slots, (3) C in Room 1, (4) D and E in different time slots, "
            "(5) F in morning, (6) A in afternoon. ALL constraints must be satisfied "
            "simultaneously. The verification must explicitly walk through each "
            "constraint and confirm it holds. Any single constraint violation = score "
            "of 1. A valid schedule with verification = score of 9-10. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="reasoning-003",
        category=TaskCategory.REASONING,
        prompt=(
            "A web application experienced the following sequence of events over "
            "4 hours:\n\n"
            "1. 2:00 PM — Deployment of version 2.3.1 (adds a new in-memory caching "
            "layer for user sessions)\n"
            "2. 2:15 PM — Monitoring shows 15%% reduction in database query latency\n"
            "3. 2:45 PM — Memory usage on app servers begins climbing steadily\n"
            "4. 3:30 PM — First out-of-memory error on server-3\n"
            "5. 3:35 PM — Load balancer removes server-3 from rotation\n"
            "6. 3:40 PM — Traffic redistributes; servers 1, 2, 4 each see ~33%% more "
            "requests\n"
            "7. 4:00 PM — server-2 hits OOM; load balancer removes it\n"
            "8. 4:15 PM — Remaining servers overwhelmed; p99 latency exceeds 10 seconds\n"
            "9. 5:00 PM — On-call engineer rolls back to version 2.3.0\n"
            "10. 5:10 PM — Memory usage drops; all servers recover within 20 minutes\n\n"
            "Trace the full causal chain from root cause to cascading failure. "
            "Identify: (a) the root cause, (b) why the impact was delayed ~45 minutes, "
            "(c) the amplification mechanism that turned one server failure into a "
            "site-wide outage, and (d) the specific design flaw in the caching layer."
        ),
        description="Causal chain analysis of cascading system failure",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must identify: (a) root cause = new caching layer in v2.3.1 leaks memory "
            "(unbounded cache growth), (b) delay = cache fills gradually as user "
            "sessions accumulate — not instant, (c) amplification = cascading failure "
            "where each dead server pushes its traffic onto survivors, accelerating "
            "their memory growth and OOM, (d) design flaw = missing eviction policy "
            "(no TTL, no LRU, no max-size cap). Must connect each numbered event to "
            "the causal chain logically. Vague answers like 'the deployment caused "
            "problems' score 2-3. Precise answers that trace every step and name the "
            "missing eviction policy score 8-10. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(REASONING_TASKS)
