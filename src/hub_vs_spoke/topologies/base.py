"""Abstract topology protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from hub_vs_spoke.tasks.base import Task
from hub_vs_spoke.types import TokenBudget, TopologyResult


@runtime_checkable
class Topology(Protocol):
    """Protocol that all topology implementations must satisfy."""

    @property
    def name(self) -> str:
        """Human-readable topology name."""
        ...

    async def run(self, task: Task, budget: TokenBudget) -> TopologyResult:
        """Execute a task using this topology and return results."""
        ...
