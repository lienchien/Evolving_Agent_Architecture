from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.report import TestCaseResult


class SandboxInterface(ABC):
    @abstractmethod
    def run_test_cases(
        self,
        code: str,
        entrypoint: str,
        test_cases: list[dict[str, Any]],
    ) -> list[TestCaseResult]: ...

    @abstractmethod
    def execute(
        self,
        code: str,
        entrypoint: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]: ...
