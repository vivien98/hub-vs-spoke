"""Tool-use benchmark tasks: function-calling coordination."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

TOOL_USE_TASKS = [
    Task(
        task_id="tool_use-001",
        category=TaskCategory.TOOL_USE,
        prompt=(
            "You have access to these tools:\n"
            "- search(query: str) -> list[str]: search a knowledge base\n"
            "- calculate(expression: str) -> float: evaluate math\n"
            "- format_report(title: str, sections: list[str]) -> str: create a report\n\n"
            "A user asks: 'How many seconds are in a leap year, and present the "
            "answer in a formatted report with the calculation breakdown?'\n\n"
            "Describe the exact sequence of tool calls you would make, with "
            "arguments and expected return values."
        ),
        description="Multi-tool orchestration for report generation",
        eval_method=EvalMethod.FUNCTION_CALL_CHECK,
        eval_rubric=(
            "Must call calculate with '366 * 24 * 60 * 60' (or equivalent), "
            "then format_report. Must include correct answer: 31622400."
        ),
        metadata={"expected_tools": ["calculate", "format_report"]},
        difficulty="easy",
    ),
    Task(
        task_id="tool_use-002",
        category=TaskCategory.TOOL_USE,
        prompt=(
            "You have access to these tools:\n"
            "- fetch_user(user_id: int) -> dict: get user profile\n"
            "- fetch_orders(user_id: int) -> list[dict]: get user's orders\n"
            "- fetch_product(product_id: int) -> dict: get product details\n"
            "- send_email(to: str, subject: str, body: str) -> bool: send email\n\n"
            "Task: For user #42, find their most recent order, look up the product "
            "details, and send them an email confirming the order with product info.\n\n"
            "Describe the exact sequence of tool calls needed."
        ),
        description="Sequential tool chain with data dependencies",
        eval_method=EvalMethod.FUNCTION_CALL_CHECK,
        eval_rubric=(
            "Must call in order: fetch_user(42), fetch_orders(42), fetch_product "
            "with the product_id from the most recent order, then send_email. "
            "Must show awareness of data dependencies between calls."
        ),
        metadata={
            "expected_tools": ["fetch_user", "fetch_orders", "fetch_product", "send_email"]
        },
        difficulty="medium",
    ),
    Task(
        task_id="tool_use-003",
        category=TaskCategory.TOOL_USE,
        prompt=(
            "You have access to these tools:\n"
            "- query_db(sql: str) -> list[dict]: run a SQL query\n"
            "- cache_set(key: str, value: str, ttl: int) -> bool: set cache\n"
            "- cache_get(key: str) -> str | None: get from cache\n"
            "- log_metric(name: str, value: float) -> None: record a metric\n\n"
            "Implement a caching strategy: first check cache for 'user_stats', "
            "if miss then query the database with "
            "'SELECT count(*) as total, avg(score) as avg FROM users', "
            "cache the result for 300 seconds, and log both the cache "
            "hit/miss and the query latency. Show the complete tool call sequence "
            "for both cache-hit and cache-miss scenarios."
        ),
        description="Implement caching strategy with conditional tool calls",
        eval_method=EvalMethod.FUNCTION_CALL_CHECK,
        eval_rubric=(
            "Must show two paths: (1) cache hit — cache_get returns data, log_metric "
            "for hit; (2) cache miss — cache_get returns None, query_db, cache_set "
            "with ttl=300, log_metric for miss and query time."
        ),
        metadata={"expected_tools": ["cache_get", "query_db", "cache_set", "log_metric"]},
        difficulty="hard",
    ),
]

default_registry.register_many(TOOL_USE_TASKS)
