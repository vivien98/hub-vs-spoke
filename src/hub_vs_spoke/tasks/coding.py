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
]

default_registry.register_many(CODING_TASKS)
