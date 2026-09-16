from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.capability import Capability
from src.domain.gap import CapabilityGap


class GeneratedCapability:
    def __init__(
        self,
        name: str,
        description: str,
        code: str,
        dependencies: list[str],
        inputs: list[str],
        outputs: list[str],
        functional_test_cases: list[dict[str, Any]],
    ) -> None:
        self.name = name
        self.description = description
        self.code = code
        self.dependencies = dependencies
        self.inputs = inputs
        self.outputs = outputs
        self.functional_test_cases = functional_test_cases


class LLMProvider(ABC):
    @abstractmethod
    def generate_capability(self, gap: CapabilityGap) -> GeneratedCapability: ...

    @abstractmethod
    def generate_boundary_tests(self, capability: Capability) -> list[dict[str, Any]]: ...
