from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from src.domain.report import TestCaseResult
from src.interfaces.sandbox import SandboxInterface

_RUNNER_FOOTER = """
import json
import sys

_payload = json.loads(sys.stdin.read())
_result = run(_payload)
sys.stdout.write(json.dumps(_result))
"""


class SubprocessSandbox(SandboxInterface):
    """Runs generated capability code in a plain subprocess.

    Stands in for the Docker-based sandbox described in the design docs.
    Same interface, so it can be swapped for a container-based
    implementation later without touching calling code.
    """

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout = timeout_seconds

    def _run_once(self, code: str, entrypoint: str, input_data: dict[str, Any]) -> dict[str, Any]:
        if entrypoint != "run":
            raise ValueError("only 'run' entrypoint is supported in the MVP sandbox")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            f.write("\n")
            f.write(_RUNNER_FOOTER)
            script_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "capability execution failed")
            return json.loads(proc.stdout)
        finally:
            Path(script_path).unlink(missing_ok=True)

    def execute(self, code: str, entrypoint: str, input_data: dict[str, Any]) -> dict[str, Any]:
        return self._run_once(code, entrypoint, input_data)

    def run_test_cases(
        self,
        code: str,
        entrypoint: str,
        test_cases: list[dict[str, Any]],
    ) -> list[TestCaseResult]:
        results: list[TestCaseResult] = []
        for case in test_cases:
            name = case.get("name", "unnamed")
            test_type = case.get("test_type", "functional")
            expected = case.get("expected_output")
            try:
                actual = self._run_once(code, entrypoint, case["input"])
                passed = expected is None or actual == expected
                results.append(
                    TestCaseResult(
                        name=name,
                        test_type=test_type,
                        passed=passed,
                        input=case["input"],
                        expected_output=expected,
                        actual_output=actual,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - capturing arbitrary generated-code failures
                results.append(
                    TestCaseResult(
                        name=name,
                        test_type=test_type,
                        passed=False,
                        input=case["input"],
                        expected_output=expected,
                        actual_output=None,
                        error=str(exc),
                    )
                )
        return results
