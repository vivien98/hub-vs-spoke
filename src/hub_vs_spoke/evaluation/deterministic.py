"""Deterministic evaluators: exact match, regex, code execution."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Any


class DeterministicEvaluator:
    """Evaluate outputs using deterministic (non-LLM) methods."""

    @staticmethod
    def exact_match(output: str, expected: str, *, normalize: bool = True) -> dict[str, Any]:
        """Check if output contains the expected answer.

        With normalize=True, comparison is case-insensitive and whitespace-collapsed.
        """
        if normalize:
            out = " ".join(output.lower().split())
            exp = " ".join(expected.lower().split())
        else:
            out, exp = output, expected

        return {"match": exp in out, "expected": expected, "method": "exact_match"}

    @staticmethod
    def regex_match(output: str, pattern: str) -> dict[str, Any]:
        """Check if output matches a regex pattern."""
        found = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
        return {
            "match": found is not None,
            "pattern": pattern,
            "matched_text": found.group(0) if found else None,
            "method": "regex_match",
        }

    @staticmethod
    def code_execution(
        code: str,
        *,
        test_code: str = "",
        timeout: int = 10,
    ) -> dict[str, Any]:
        """Execute Python code in a subprocess and check for errors.

        If test_code is provided, it is appended after the main code.
        """
        full_code = f"{code}\n\n{test_code}" if test_code else code

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
                "method": "code_execution",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "returncode": -1,
                "method": "code_execution",
            }
        finally:
            os.unlink(temp_path)

    @staticmethod
    def function_call_check(
        output: str,
        expected_tools: list[str],
    ) -> dict[str, Any]:
        """Check that the output mentions the expected tool/function calls in order."""
        output_lower = output.lower()
        found_tools = [t for t in expected_tools if t.lower() in output_lower]

        # Check ordering: each tool should appear after the previous one
        ordered = True
        last_pos = -1
        for tool in expected_tools:
            pos = output_lower.find(tool.lower())
            if pos == -1 or pos < last_pos:
                ordered = False
                break
            last_pos = pos

        return {
            "all_present": len(found_tools) == len(expected_tools),
            "ordered": ordered,
            "expected": expected_tools,
            "found": found_tools,
            "missing": [t for t in expected_tools if t not in found_tools],
            "method": "function_call_check",
        }
