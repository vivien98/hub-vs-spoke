"""Task definitions and registry for benchmark scenarios."""

# Import category modules to populate the default registry.
import hub_vs_spoke.tasks.coding as _coding  # noqa: F401
import hub_vs_spoke.tasks.creative as _creative  # noqa: F401
import hub_vs_spoke.tasks.reasoning as _reasoning  # noqa: F401
import hub_vs_spoke.tasks.research as _research  # noqa: F401
import hub_vs_spoke.tasks.tool_use as _tool_use  # noqa: F401
from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, TaskRegistry, default_registry

__all__ = ["EvalMethod", "Task", "TaskCategory", "TaskRegistry", "default_registry"]
