"""Unit tests for market topology helper functions (no network calls)."""

from __future__ import annotations

from agent_economy.schemas import SubmissionKind, VerifyMode

from hub_vs_spoke.tasks.base import Task, TaskCategory
from hub_vs_spoke.topologies.market import (
    MarketTopology,
    _extract_results_from_ledger,
    _our_task_to_ae_spec,
    _read_submission_text,
)


def test_our_task_to_ae_spec() -> None:
    """Converts a hub_vs_spoke Task to an agent-economy TaskSpec."""
    task = Task(
        task_id="coding-001",
        category=TaskCategory.CODING,
        prompt="Implement a widget",
        description="Widget task",
    )
    spec = _our_task_to_ae_spec(task, judge_workers=["gpt-5.2"])

    assert spec.id == "coding-001"
    assert spec.title == "Widget task"
    assert spec.description == "Implement a widget"
    assert spec.bounty == 100
    assert spec.verify_mode == VerifyMode.JUDGES
    assert spec.submission_kind == SubmissionKind.TEXT
    assert spec.judges is not None
    assert spec.judges.workers == ["gpt-5.2"]


def test_read_submission_text_missing(tmp_path) -> None:
    """Returns empty string when artifact doesn't exist."""
    event = {"artifacts": [{"name": "submission.txt", "path": "nonexistent/file.txt"}]}
    result = _read_submission_text(tmp_path, event)
    assert result == ""


def test_read_submission_text_found(tmp_path) -> None:
    """Reads submission text from artifact path."""
    sub_dir = tmp_path / "sandbox"
    sub_dir.mkdir()
    sub_file = sub_dir / "submission.txt"
    sub_file.write_text("Hello world\n")

    event = {"artifacts": [{"name": "submission.txt", "path": "sandbox/submission.txt"}]}
    result = _read_submission_text(tmp_path, event)
    assert result == "Hello world"


def test_market_topology_name() -> None:
    mt = MarketTopology([("gpt-5.2", "gpt-5.2")])
    assert mt.name == "market"


def test_market_resolve_model_name() -> None:
    mt = MarketTopology([
        ("gpt-5.2", "gpt-5.2"),
        ("opus-4.6", "claude:claude-opus-4-6"),
    ])
    assert mt._resolve_model_name("gpt-5.2") == "gpt-5.2"
    assert mt._resolve_model_name("opus-4.6") == "claude-opus-4-6"
    assert mt._resolve_model_name("unknown") == "unknown"


def test_extract_results_empty(tmp_path) -> None:
    """Empty event list returns empty results."""
    results = _extract_results_from_ledger([], tmp_path)
    assert results == {}
