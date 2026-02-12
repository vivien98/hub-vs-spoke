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
    Task(
        task_id="reasoning-004",
        category=TaskCategory.REASONING,
        prompt=(
            "Five friends — Alice, Bob, Carol, Dave, and Eve — each own exactly one pet "
            "(cat, dog, fish, hamster, parrot) and live on the same street in houses "
            "numbered 1 through 5 from left to right.\n\n"
            "Constraints:\n"
            "1. Alice lives in house 1.\n"
            "2. The dog owner lives directly next to the cat owner.\n"
            "3. Eve lives in an even-numbered house.\n"
            "4. The fish owner lives in house 3.\n"
            "5. Bob lives immediately to the right of Carol.\n"
            "6. Dave does not own the parrot.\n"
            "7. The hamster owner lives in an odd-numbered house.\n"
            "8. Carol does not live next to Alice.\n"
            "9. Eve owns neither the dog nor the fish.\n"
            "10. The parrot owner lives in a higher-numbered house than the dog owner.\n"
            "11. Bob does not own the cat.\n\n"
            "Determine the complete assignment: who lives in which house and owns which "
            "pet. Show your deductive reasoning step by step. There is exactly one "
            "valid solution."
        ),
        description="Logic grid puzzle with 11 constraints and unique solution",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "The unique solution is: House 1: Alice-hamster, House 2: Carol-dog, "
            "House 3: Bob-fish, House 4: Eve-cat, House 5: Dave-parrot. "
            "Derivation: (1) Alice=H1. (8) Carol not in H2 (next to Alice). "
            "(5) Bob is directly right of Carol, so Carol-Bob pairs are (2,3),(3,4),(4,5). "
            "(8) eliminates (2,3) since Carol=H2 is next to H1. So Carol-Bob = (3,4) or (4,5). "
            "(4) Fish owner in H3. (3) Eve in even house (H2 or H4). "
            "If Carol=H4,Bob=H5: Eve=H2, Dave=H3. Dave-H3 owns fish(4). (6) Dave not parrot, ok. "
            "(7) Hamster in odd house (H1,H3,H5). H3=fish, so hamster=H1 or H5. "
            "(9) Eve not dog/fish. (10) Parrot higher than dog. (2) Dog next to cat. "
            "Test: Eve-H2=hamster? (7) H2 is even, hamster must be odd. Contradiction. "
            "Eve-H2=parrot? (10) parrot > dog, so dog in H1. (2) dog-H1 next to cat-H2. "
            "But Eve-H2=parrot, not cat. Contradiction. Eve-H2=cat? (2) dog next to cat=H2, "
            "so dog in H1 or H3. H3=fish, so dog=H1=Alice. (10) parrot higher than dog=H1. "
            "Bob-H5 or Carol-H4 gets parrot. (6) Dave not parrot but Dave=H3=fish. "
            "Hamster in odd (H1 or H5). H1=dog, so hamster=H5=Bob. (11) Bob not cat, ok. "
            "Carol-H4=parrot? (10) parrot-H4 > dog-H1, ok. But then who has what's left? "
            "All assigned: Alice-dog,Eve-cat,Dave-fish,Bob-hamster,Carol-parrot. "
            "(9) Eve not dog ✓. Check all: all hold. Wait — try Carol=H3,Bob=H4: "
            "Carol-H3 owns fish(4). Eve in H2. Dave=H5. (7) hamster odd: H1 or H5. "
            "(9) Eve-H2 not dog/fish. (2) dog next to cat. (10) parrot > dog. "
            "(11) Bob-H4 not cat. Try Alice-H1=hamster. Remaining: dog,cat,parrot for "
            "Eve-H2,Bob-H4,Dave-H5. Eve not dog(9), so Eve=cat or parrot. "
            "If Eve=cat, dog must be next to cat-H2, so dog=H1(hamster) or H3(fish). "
            "Neither works. If Eve=parrot-H2, (10) parrot-H2 > dog, so dog in H1 — but "
            "H1=hamster. Contradiction. So Carol-Bob=(3,4) fails. Carol-Bob=(4,5): "
            "Eve=H2, Dave=H3=fish. (7) hamster odd: H1 or H5. "
            "Alice-H1=hamster works. (9) Eve not dog/fish, so Eve=cat or parrot. "
            "(2) dog next to cat. If Eve-H2=cat, dog in H1(hamster) or H3(fish) — fails. "
            "Eve-H2=parrot, (10) parrot-H2>dog, dog=H1=hamster — fails. Eve-H2=cat: "
            "already shown fails. So try Alice-H1=dog? (7) hamster=H5=Bob. "
            "(11) Bob not cat ✓. Eve-H2: not dog/fish(9), so cat or parrot. "
            "(2) dog-H1 next to cat, so cat=H2. Eve-H2=cat. (10) parrot > dog=H1. "
            "Remaining: parrot for Carol-H4 or Dave-H3(fish). Carol-H4=parrot. "
            "(6) Dave not parrot ✓ Dave=fish. Check all 11 constraints: all hold. "
            "SOLUTION: H1-Alice-dog, H2-Eve-cat, H3-Dave-fish, H4-Carol-parrot, "
            "H5-Bob-hamster. "
            "But wait, recheck (8): Carol-H4 next to Dave-H3 and Bob-H5. Carol NOT "
            "next to Alice-H1 ✓. All constraints satisfied. "
            "Score 9-10 for correct final assignment with clear deductive chain. "
            "Score 5-7 for correct assignment but messy or incomplete reasoning. "
            "Score 1-4 for wrong assignment. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="reasoning-005",
        category=TaskCategory.REASONING,
        prompt=(
            "You have a 3×3 grid. Place the digits 1 through 9 (each used exactly once) "
            "in the grid so that:\n\n"
            "1. Each row sums to 15\n"
            "2. Each column sums to 15\n"
            "3. Both main diagonals sum to 15\n"
            "4. The top-left cell contains 2\n"
            "5. The center cell contains 5\n\n"
            "Provide the completed grid and prove it is the ONLY solution satisfying "
            "all five constraints. Your proof must show why no other placement works — "
            "don't just exhibit one solution."
        ),
        description="Constrained magic square with uniqueness proof",
        expected_answer=None,
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "The unique solution is: [[2,7,6],[9,5,1],[4,3,8]]. "
            "Proof sketch: top-left=2, center=5. Row 1: 2+a+b=15, so a+b=13. "
            "Remaining digits {1,3,4,6,7,8,9} with pairs summing to 13: (4,9),(6,7). "
            "Main diagonal: 2+5+c=15, c=8 (bottom-right). Anti-diagonal: a+5+d=15 "
            "where a is top-right and d is bottom-left. "
            "Column 1: 2+e+d=15. Row 3: d+f+8=15. "
            "Try top-row as [2,7,6]: diag 2+5+BR=15 → BR=8. Anti-diag 6+5+BL=15 → BL=4. "
            "Col1: 2+ML+4=15 → ML=9. Row2: 9+5+MR=15 → MR=1. Col2: 7+5+3=15 → BC=3. "
            "Check row3: 4+3+8=15 ✓. All constraints verified. "
            "For uniqueness: the other row-1 option [2,4,9] forces diag BR=8, "
            "anti-diag 9+5+BL=15 → BL=1. Col1: 2+ML+1=15 → ML=12, impossible. "
            "So [2,7,6] is forced, and every subsequent cell is determined. "
            "Must provide both a correct grid AND a uniqueness argument. "
            "Grid correct but no uniqueness proof = 5-6. "
            "Grid correct with valid proof = 8-10. "
            "Wrong grid = 1-3. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(REASONING_TASKS)
