"""Reasoning benchmark tasks: math, logic, planning."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

REASONING_TASKS = [
    Task(
        task_id="reasoning-001",
        category=TaskCategory.REASONING,
        prompt=(
            "A farmer has 100 metres of fencing. He wants to enclose the largest "
            "possible rectangular area against a straight river (the river side "
            "needs no fence). What are the dimensions and area of the optimal rectangle?"
        ),
        description="Classic optimisation: max area with fixed perimeter",
        expected_answer="50m x 25m = 1250 sq m",
        eval_method=EvalMethod.EXACT_MATCH,
        eval_rubric="Width 50m, depth 25m, area 1250 square metres.",
        difficulty="easy",
    ),
    Task(
        task_id="reasoning-002",
        category=TaskCategory.REASONING,
        prompt=(
            "Three people check into a hotel room that costs $30. They each pay $10. "
            "Later, the manager realises the room costs only $25 and gives $5 to the "
            "bellboy to return. The bellboy keeps $2 and returns $1 to each person. "
            "Now each has paid $9 (total $27), the bellboy has $2. $27 + $2 = $29. "
            "Where is the missing dollar? Explain clearly."
        ),
        description="Classic missing-dollar logic puzzle",
        expected_answer="There is no missing dollar",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must explain that $27 already includes the bellboy's $2, so adding them "
            "double-counts. Correct accounting: $25 (hotel) + $2 (bellboy) + $3 (returned) = $30."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="reasoning-003",
        category=TaskCategory.REASONING,
        prompt=(
            "You have 12 balls, one of which is a different weight (heavier or lighter). "
            "You have a balance scale. What is the minimum number of weighings to "
            "guarantee finding the odd ball and whether it is heavier or lighter? "
            "Describe the full strategy."
        ),
        description="Classic 12-ball weighing puzzle",
        expected_answer="3 weighings",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must state 3 weighings and provide a valid decision tree that covers "
            "all 24 possibilities (12 balls x heavier/lighter)."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="reasoning-004",
        category=TaskCategory.REASONING,
        prompt=(
            "Plan a dinner party for 8 people with the following constraints:\n"
            "- Alice and Bob must sit next to each other\n"
            "- Carol and Dave must NOT sit next to each other\n"
            "- Eve must sit at one end of the table\n"
            "- The table is rectangular with 4 seats on each long side\n"
            "Provide a valid seating arrangement."
        ),
        description="Constraint-satisfaction seating problem",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Arrangement must: (1) seat exactly 8 people, (2) Alice and Bob adjacent, "
            "(3) Carol and Dave not adjacent, (4) Eve at an end seat."
        ),
        difficulty="medium",
    ),
]

default_registry.register_many(REASONING_TASKS)
