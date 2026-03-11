"""Unit tests for market topology helper functions (no network calls)."""

from __future__ import annotations

from agent_economy.schemas import EventType, SubmissionKind, VerifyMode

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


def test_extract_results_collects_bid_submissions(tmp_path) -> None:
    """Bid events are unpacked per task for later calibration analysis."""
    events = [
        {
            "type": EventType.BID_SUBMITTED,
            "payload": {
                "worker_id": "gpt-5.2",
                "bids": [
                    {
                        "task_id": "coding-001",
                        "ask": 12,
                        "self_assessed_p_success": 0.8,
                        "eta_minutes": 4,
                    }
                ],
            },
            "artifacts": [],
        },
        {
            "type": EventType.TASK_ASSIGNED,
            "payload": {
                "task_id": "coding-001",
                "worker_id": "gpt-5.2",
                "bid": {
                    "task_id": "coding-001",
                    "ask": 12,
                    "self_assessed_p_success": 0.8,
                    "eta_minutes": 4,
                },
            },
            "artifacts": [],
        },
        {
            "type": EventType.TASK_COMPLETED,
            "payload": {
                "task_id": "coding-001",
                "success": True,
                "verify_status": "PASS",
            },
            "artifacts": [],
        },
    ]

    results = _extract_results_from_ledger(events, tmp_path)

    assert results["coding-001"]["winner"] == "gpt-5.2"
    assert results["coding-001"]["bids"] == [
        {
            "worker_id": "gpt-5.2",
            "p_success": 0.8,
            "ask": 12,
            "eta_minutes": 4,
        }
    ]


def test_extract_results_falls_back_to_assignment_bid(tmp_path) -> None:
    """Assigned bid is preserved even when explicit bid-submitted events are absent."""
    events = [
        {
            "type": EventType.TASK_ASSIGNED,
            "payload": {
                "task_id": "reasoning-001",
                "worker_id": "claude-opus-4-6",
                "bid": {
                    "task_id": "reasoning-001",
                    "ask": 20,
                    "self_assessed_p_success": 0.65,
                    "eta_minutes": 8,
                },
            },
            "artifacts": [],
        },
        {
            "type": EventType.TASK_COMPLETED,
            "payload": {
                "task_id": "reasoning-001",
                "success": False,
                "verify_status": "FAIL",
            },
            "artifacts": [],
        },
    ]

    results = _extract_results_from_ledger(events, tmp_path)

    assert results["reasoning-001"]["bids"] == [
        {
            "worker_id": "claude-opus-4-6",
            "p_success": 0.65,
            "ask": 20,
            "eta_minutes": 8,
        }
    ]
