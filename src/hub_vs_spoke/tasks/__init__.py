"""Task definitions and registry for benchmark scenarios."""

# Import category modules to populate the default registry.
import hub_vs_spoke.tasks.coding as _coding  # noqa: F401
import hub_vs_spoke.tasks.reasoning as _reasoning  # noqa: F401
import hub_vs_spoke.tasks.synthesis as _synthesis  # noqa: F401
from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, TaskRegistry, default_registry

__all__ = ["EvalMethod", "Task", "TaskCategory", "TaskRegistry", "default_registry"]
