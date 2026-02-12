"""Coding benchmark tasks: implementation, debugging, refactoring."""

from hub_vs_spoke.tasks.base import EvalMethod, Task, TaskCategory, default_registry

CODING_TASKS = [
    Task(
        task_id="coding-001",
        category=TaskCategory.CODING,
        prompt=(
            "Implement a Python class `IntervalStore` that manages a collection of "
            "numeric intervals. It must support three operations:\n\n"
            "1. `add(start: float, end: float)` — stores a new interval\n"
            "2. `merge() -> list[tuple[float, float]]` — returns a new list where all "
            "overlapping or adjacent intervals have been merged\n"
            "3. `query(point: float) -> bool` — returns True if the point lies within "
            "any stored interval (checked against the raw stored intervals, not merged)\n\n"
            "Handle edge cases: empty store, single-point intervals (start == end), "
            "fully overlapping additions, and intervals added in arbitrary order. "
            "Include type hints and docstrings."
        ),
        description="Interval store with merge and point-query operations",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Code must: (1) correctly merge overlapping and adjacent intervals using "
            "a sort-then-sweep approach or equivalent O(n log n) method, (2) handle all "
            "stated edge cases (empty, single-point, fully overlapping, arbitrary order), "
            "(3) implement query() by checking raw intervals, (4) include type hints and "
            "docstrings, (5) be clean and readable. Deduct heavily for: incorrect merge "
            "logic (e.g. failing on [1,3]+[2,5] or [1,2]+[2,3]), missing edge cases, "
            "no type hints. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="coding-002",
        category=TaskCategory.CODING,
        prompt=(
            "The following Python function is supposed to find the longest substring "
            "without repeating characters, but it has a bug that causes wrong results "
            "for certain inputs. Find the bug, explain clearly why it fails, and "
            "provide the corrected version.\n\n"
            "```python\n"
            "def longest_unique_substring(s: str) -> str:\n"
            "    start = 0\n"
            "    max_start = 0\n"
            "    max_len = 0\n"
            "    seen = {}\n"
            "    \n"
            "    for end, char in enumerate(s):\n"
            "        if char in seen:\n"
            "            start = seen[char] + 1\n"
            "        seen[char] = end\n"
            "        if end - start + 1 > max_len:\n"
            "            max_len = end - start + 1\n"
            "            max_start = start\n"
            "    \n"
            "    return s[max_start:max_start + max_len]\n"
            "```\n\n"
            "Failing test case: `longest_unique_substring('abba')` returns `'bba'` "
            "(length 3) instead of the correct `'ab'` or `'ba'` (length 2)."
        ),
        description="Debug sliding-window substring function with pointer regression bug",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must identify the exact bug: when a repeated character is found, `start` "
            "is set to `seen[char] + 1` unconditionally, but this can move `start` "
            "BACKWARDS if the repeated character was already before the current window. "
            "On 'abba': when processing the second 'a' at index 3, seen['a']=0, so "
            "start becomes 1, but start was already at 2 from the 'b' repeat — moving "
            "it backwards to 1 corrupts the window. The fix is "
            "`start = max(start, seen[char] + 1)`. The corrected code must pass the "
            "'abba' test case. Explanations that are vague ('the indexing is wrong') "
            "without identifying the backwards-pointer issue score low. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="coding-003",
        category=TaskCategory.CODING,
        prompt=(
            "Refactor the following function into clean, well-structured Python. "
            "The function currently works correctly — preserve its exact behavior "
            "while improving readability, structure, and maintainability. Break it "
            "into smaller functions with clear responsibilities.\n\n"
            "```python\n"
            "def process_sales_data(records):\n"
            "    results = []\n"
            "    total_rev = 0\n"
            "    error_count = 0\n"
            "    for r in records:\n"
            "        if not isinstance(r, dict):\n"
            "            error_count += 1\n"
            "            continue\n"
            "        if 'product' not in r or 'quantity' not in r or 'price' not in r:\n"
            "            error_count += 1\n"
            "            continue\n"
            "        try:\n"
            "            qty = int(r['quantity'])\n"
            "            price = float(r['price'])\n"
            "        except (ValueError, TypeError):\n"
            "            error_count += 1\n"
            "            continue\n"
            "        if qty <= 0 or price < 0:\n"
            "            error_count += 1\n"
            "            continue\n"
            "        revenue = qty * price\n"
            "        discount = 0.0\n"
            "        if qty >= 100:\n"
            "            discount = 0.15\n"
            "        elif qty >= 50:\n"
            "            discount = 0.10\n"
            "        elif qty >= 10:\n"
            "            discount = 0.05\n"
            "        final_revenue = revenue * (1 - discount)\n"
            "        total_rev += final_revenue\n"
            "        results.append({\n"
            "            'product': r['product'],\n"
            "            'quantity': qty,\n"
            "            'unit_price': price,\n"
            "            'gross_revenue': revenue,\n"
            "            'discount_pct': discount,\n"
            "            'net_revenue': round(final_revenue, 2),\n"
            "            'category': 'bulk' if qty >= 50 else 'standard'\n"
            "        })\n"
            "    results.sort(key=lambda x: x['net_revenue'], reverse=True)\n"
            "    return {\n"
            "        'items': results,\n"
            "        'total_revenue': round(total_rev, 2),\n"
            "        'record_count': len(results),\n"
            "        'error_count': error_count\n"
            "    }\n"
            "```"
        ),
        description="Refactor monolith data-processing function into clean modules",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Refactored code must: (1) break the monolith into at least 3 smaller "
            "functions with clear single responsibilities (e.g. validation, discount "
            "calculation, record processing), (2) preserve identical output for any "
            "valid input — all discount thresholds, rounding, sorting, and category "
            "assignment must be unchanged, (3) use descriptive function and variable "
            "names throughout, (4) include type hints. "
            "Deduct heavily for: changing behavior (e.g. altering discount thresholds "
            "or removing the rounding), too few functions (just renaming variables "
            "is not a refactor), losing the descending sort by net_revenue, or removing "
            "the error_count tracking. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="medium",
    ),
    Task(
        task_id="coding-004",
        category=TaskCategory.CODING,
        prompt=(
            "Implement a Python class `LRUCache` with O(1) time complexity for both "
            "`get` and `put` operations. The cache has a fixed capacity set at "
            "construction.\n\n"
            "```python\n"
            "class LRUCache:\n"
            "    def __init__(self, capacity: int): ...\n"
            "    def get(self, key: int) -> int: ...  # return -1 if not found\n"
            "    def put(self, key: int, value: int) -> None: ...\n"
            "```\n\n"
            "Constraints and edge cases your implementation must handle correctly:\n"
            "- `capacity` is always >= 1\n"
            "- `put` on an existing key updates the value AND marks it as most recently used\n"
            "- `get` on an existing key marks it as most recently used\n"
            "- When the cache is at capacity and a new key is inserted, evict the LEAST "
            "recently used key\n"
            "- The following sequence must produce exactly these results:\n\n"
            "```python\n"
            "c = LRUCache(2)\n"
            "c.put(1, 1)\n"
            "c.put(2, 2)\n"
            "c.get(1)       # returns 1 (marks 1 as recently used)\n"
            "c.put(3, 3)    # evicts key 2 (not key 1, because 1 was just accessed)\n"
            "c.get(2)       # returns -1 (evicted)\n"
            "c.put(4, 4)    # evicts key 1 (3 is more recent from the put)\n"
            "c.get(1)       # returns -1 (evicted)\n"
            "c.get(3)       # returns 3\n"
            "c.get(4)       # returns 4\n"
            "c.put(3, 30)   # updates value of 3 (marks as most recent)\n"
            "c.put(5, 5)    # evicts key 4 (3 was just touched by put)\n"
            "c.get(4)       # returns -1 (evicted)\n"
            "c.get(3)       # returns 30\n"
            "```\n\n"
            "Do NOT use `functools.lru_cache` or `collections.OrderedDict`. Implement "
            "the data structure from scratch using a dict and a doubly linked list."
        ),
        description="LRU cache from scratch with O(1) ops and precise eviction sequence",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Must: (1) implement using a hash map + doubly linked list (not OrderedDict "
            "or functools), (2) achieve O(1) for both get and put, (3) correctly handle "
            "the ENTIRE test sequence above — every return value and eviction must match "
            "exactly, (4) handle the 'put updates existing key' case correctly (must "
            "update value AND move to most-recent position), (5) include type hints. "
            "The critical trap: many implementations get the eviction order wrong when "
            "put() is called on an existing key. If put(3, 30) doesn't move key 3 to "
            "the head, then put(5, 5) will evict 3 instead of 4, and the last two "
            "assertions fail. Score 1-3 if the test sequence doesn't fully pass. "
            "Score 4-6 if it passes but uses OrderedDict or has O(n) operations. "
            "Score 8-10 if it uses dict + linked list, passes all assertions, and is clean. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
    Task(
        task_id="coding-005",
        category=TaskCategory.CODING,
        prompt=(
            "The following async Python code has three concurrency bugs. Find all three, "
            "explain each clearly, and provide the corrected version.\n\n"
            "```python\n"
            "import asyncio\n"
            "from typing import Any\n\n"
            "class AsyncBatcher:\n"
            "    '''Batches individual requests and processes them in groups.'''\n\n"
            "    def __init__(self, batch_size: int = 5, timeout: float = 1.0):\n"
            "        self.batch_size = batch_size\n"
            "        self.timeout = timeout\n"
            "        self.pending: list[tuple[Any, asyncio.Future]] = []\n"
            "        self.results: dict[int, Any] = {}\n"
            "        self.lock = asyncio.Lock()\n"
            "        self._batch_id = 0\n\n"
            "    async def submit(self, item: Any) -> Any:\n"
            "        future = asyncio.Future()\n"
            "        self.pending.append((item, future))\n\n"
            "        if len(self.pending) >= self.batch_size:\n"
            "            await self._flush()\n\n"
            "        return await future\n\n"
            "    async def _flush(self):\n"
            "        batch = self.pending[:self.batch_size]\n"
            "        self.pending = self.pending[self.batch_size:]\n"
            "        self._batch_id += 1\n"
            "        batch_id = self._batch_id\n\n"
            "        results = await self._process_batch(\n"
            "            [item for item, _ in batch]\n"
            "        )\n"
            "        self.results[batch_id] = results\n\n"
            "        for i, (_, future) in enumerate(batch):\n"
            "            future.set_result(results[i])\n\n"
            "    async def _process_batch(self, items: list) -> list:\n"
            "        await asyncio.sleep(0.1)  # simulate I/O\n"
            "        return [f'processed:{x}' for x in items]\n\n"
            "    async def run_timeout_flush(self):\n"
            "        while True:\n"
            "            await asyncio.sleep(self.timeout)\n"
            "            if self.pending:\n"
            "                await self._flush()\n"
            "```\n\n"
            "Hint: think about what happens when multiple coroutines call submit() "
            "concurrently, and what happens to futures that are added to `pending` "
            "but never make it into a batch."
        ),
        description="Find three concurrency bugs in async batching code",
        eval_method=EvalMethod.LLM_JUDGE,
        eval_rubric=(
            "Three bugs exist:\n"
            "(1) RACE ON PENDING: submit() appends to self.pending and checks length "
            "WITHOUT holding the lock. Two concurrent submit() calls can both see "
            "len >= batch_size and both call _flush(), causing items to be processed "
            "twice or futures to be resolved twice. Fix: acquire self.lock around the "
            "append + length check + flush.\n"
            "(2) RACE ON _flush(): _flush() reads and modifies self.pending and "
            "self._batch_id without the lock. Concurrent _flush() calls (from submit + "
            "run_timeout_flush) can interleave, corrupting the batch boundaries. Fix: "
            "acquire self.lock in _flush() or ensure only one caller at a time.\n"
            "(3) ORPHANED FUTURES: items added to pending that don't reach batch_size "
            "and whose timeout flush hasn't fired yet will have their futures awaited "
            "forever if no more submits arrive. The timeout loop helps but has its own "
            "race. Fix: ensure the timeout flush handles partial batches correctly, or "
            "add a drain/close method.\n"
            "Must identify all three bugs with specific explanations of the interleaving "
            "that triggers them. Identifying only 1-2 scores 3-5. Vague answers about "
            "'concurrency issues' without naming the specific race conditions score 1-3. "
            "All three identified with clear fixes = 8-10. "
            "Length alone is not quality; verbose padding without substance should be penalized."
        ),
        difficulty="hard",
    ),
]

default_registry.register_many(CODING_TASKS)
