"""Task definition and registry for benchmark scenarios."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskCategory(StrEnum):
    CODING = "coding"
    REASONING = "reasoning"
    RESEARCH = "research"
    CREATIVE = "creative"
    TOOL_USE = "tool_use"


class EvalMethod(StrEnum):
    """How the task's output should be evaluated."""

    EXACT_MATCH = "exact_match"
    CODE_EXECUTION = "code_execution"
    LLM_JUDGE = "llm_judge"
    REGEX_MATCH = "regex_match"
    FUNCTION_CALL_CHECK = "function_call_check"


class Task(BaseModel):
    """A single benchmark task."""

    task_id: str
    category: TaskCategory
    prompt: str
    description: str = ""
    expected_answer: str | None = None
    eval_method: EvalMethod = EvalMethod.LLM_JUDGE
    eval_rubric: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    difficulty: str = "medium"  # easy / medium / hard


class TaskRegistry:
    """Central registry of all benchmark tasks, queryable by category."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def register(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def register_many(self, tasks: list[Task]) -> None:
        for t in tasks:
            self.register(t)

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def by_category(self, category: TaskCategory) -> list[Task]:
        return [t for t in self._tasks.values() if t.category == category]

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def categories(self) -> list[TaskCategory]:
        return sorted({t.category for t in self._tasks.values()}, key=lambda c: c.value)

    def __len__(self) -> int:
        return len(self._tasks)


# Global default registry, populated by category modules on import.
default_registry = TaskRegistry()
