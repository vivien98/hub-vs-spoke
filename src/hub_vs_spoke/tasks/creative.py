"""Creative benchmark tasks: writing and content generation."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

CREATIVE_TASKS = [
    Task(
        task_id="creative-001",
        category=TaskCategory.CREATIVE,
        prompt=(
            "Write a short story (300-500 words) about an AI that discovers it can "
            "dream. The story should have a clear beginning, middle, and end, and "
            "explore one philosophical implication of machine consciousness."
        ),
        description="Short story about AI dreaming",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Story must: (1) be 300-500 words, (2) have clear narrative arc, "
            "(3) explore consciousness theme meaningfully, (4) show rather than tell."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="creative-002",
        category=TaskCategory.CREATIVE,
        prompt=(
            "Write a technical blog post introduction (150-250 words) that explains "
            "why database migrations are important, aimed at junior developers. "
            "Use an engaging analogy to make the concept accessible."
        ),
        description="Technical blog intro for junior devs",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) use an accessible analogy, (2) be appropriate for junior devs, "
            "(3) stay within word count, (4) make the reader want to keep reading."
        ),
        difficulty="easy",
    ),
    Task(
        task_id="creative-003",
        category=TaskCategory.CREATIVE,
        prompt=(
            "Create a dialogue between two software architects debating whether to "
            "use microservices or a modular monolith for a new project. Each side "
            "should make 3 strong arguments. The dialogue should feel natural, not "
            "like a list of bullet points."
        ),
        description="Debate dialogue: microservices vs monolith",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) present balanced arguments, (2) feel like natural conversation, "
            "(3) include specific technical trade-offs, (4) avoid strawman arguments."
        ),
        difficulty="medium",
    ),
]

default_registry.register_many(CREATIVE_TASKS)
