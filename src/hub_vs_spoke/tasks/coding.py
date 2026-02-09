"""Coding benchmark tasks: generation, debugging, refactoring."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

CODING_TASKS = [
    Task(
        task_id="coding-001",
        category=TaskCategory.CODING,
        prompt=(
            "Write a Python function `merge_sorted_lists(a, b)` that merges two "
            "sorted lists into a single sorted list in O(n+m) time. Include type "
            "hints and a docstring."
        ),
        description="Merge two sorted lists efficiently",
        expected_answer=None,
        eval_method=EvalMethod.CODE_EXECUTION,
        eval_rubric=(
            "Function must: (1) return a sorted list, (2) handle empty inputs, "
            "(3) run in O(n+m) — no re-sorting allowed, (4) include type hints."
        ),
        difficulty="easy",
    ),
    Task(
        task_id="coding-002",
        category=TaskCategory.CODING,
        prompt=(
            "Debug the following Python code. It should return the second-largest "
            "unique element, but has a bug:\n\n"
            "```python\n"
            "def second_largest(nums):\n"
            "    unique = list(set(nums))\n"
            "    unique.sort()\n"
            "    return unique[-1]\n"
            "```\n\n"
            "Fix the bug and explain what was wrong."
        ),
        description="Debug second-largest element function",
        expected_answer="return unique[-2]",
        eval_method=EvalMethod.CODE_EXECUTION,
        eval_rubric="Must return unique[-2] and explain the off-by-one.",
        difficulty="easy",
    ),
    Task(
        task_id="coding-003",
        category=TaskCategory.CODING,
        prompt=(
            "Refactor this code into clean, well-structured Python. Preserve "
            "behaviour but improve readability, naming, and structure:\n\n"
            "```python\n"
            "def p(d):\n"
            "    r = []\n"
            "    for i in d:\n"
            "        if i['t'] == 'a' and i['v'] > 10:\n"
            "            r.append({'n': i['n'], 's': i['v'] * 2})\n"
            "        elif i['t'] == 'b':\n"
            "            r.append({'n': i['n'], 's': i['v'] + 5})\n"
            "    return sorted(r, key=lambda x: x['s'], reverse=True)\n"
            "```"
        ),
        description="Refactor opaque data-processing function",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Refactored code must: (1) use descriptive names, (2) preserve identical "
            "output for any input, (3) be readable without comments."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="coding-004",
        category=TaskCategory.CODING,
        prompt=(
            "Implement a thread-safe LRU cache in Python with a configurable max "
            "size. It should support get(key) and put(key, value) operations, both "
            "in O(1) average time. Do not use functools.lru_cache."
        ),
        description="Implement thread-safe LRU cache from scratch",
        eval_method=EvalMethod.CODE_EXECUTION,
        eval_rubric=(
            "Must use OrderedDict or doubly-linked list + dict. Must be thread-safe "
            "(threading.Lock or RLock). get and put must be O(1) average."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(CODING_TASKS)
