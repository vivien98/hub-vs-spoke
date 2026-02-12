"""Unit tests for task definitions and registry."""

from __future__ import annotations

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, TaskRegistry, default_registry


class TestTaskRegistry:
    def test_register_and_get(self, sample_registry: TaskRegistry) -> None:
        task = sample_registry.get("reg-001")
        assert task.task_id == "reg-001"
        assert task.category == TaskCategory.CODING

    def test_by_category(self, sample_registry: TaskRegistry) -> None:
        coding = sample_registry.by_category(TaskCategory.CODING)
        assert len(coding) == 1
        assert coding[0].task_id == "reg-001"

    def test_all_tasks(self, sample_registry: TaskRegistry) -> None:
        assert len(sample_registry.all_tasks()) == 2

    def test_categories(self, sample_registry: TaskRegistry) -> None:
        cats = sample_registry.categories()
        assert TaskCategory.CODING in cats
        assert TaskCategory.REASONING in cats

    def test_len(self, sample_registry: TaskRegistry) -> None:
        assert len(sample_registry) == 2


class TestDefaultRegistry:
    """Verify that importing the tasks package populates the default registry."""

    def test_has_coding_tasks(self) -> None:
        coding = default_registry.by_category(TaskCategory.CODING)
        assert len(coding) >= 3

    def test_has_reasoning_tasks(self) -> None:
        reasoning = default_registry.by_category(TaskCategory.REASONING)
        assert len(reasoning) >= 3

    def test_has_synthesis_tasks(self) -> None:
        synthesis = default_registry.by_category(TaskCategory.SYNTHESIS)
        assert len(synthesis) >= 3

    def test_total_tasks(self) -> None:
        # 9 tasks total: 3 coding + 3 reasoning + 3 synthesis
        assert len(default_registry) >= 9

    def test_all_categories_present(self) -> None:
        cats = default_registry.categories()
        for cat in TaskCategory:
            assert cat in cats, f"Missing category: {cat}"


class TestTaskModel:
    def test_task_defaults(self) -> None:
        t = Task(task_id="t1", category=TaskCategory.CODING, prompt="hi")
        assert t.eval_method == EvalMethod.LLM_JUDGE
        assert t.difficulty == "medium"
        assert t.expected_answer is None

    def test_task_with_all_fields(self) -> None:
        t = Task(
            task_id="t2",
            category=TaskCategory.REASONING,
            prompt="Solve X",
            description="desc",
            expected_answer="42",
            eval_method=EvalMethod.EXACT_MATCH,
            eval_rubric="Must be 42",
            metadata={"key": "value"},
            difficulty="hard",
        )
        assert t.expected_answer == "42"
        assert t.metadata["key"] == "value"
