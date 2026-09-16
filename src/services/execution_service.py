from __future__ import annotations

from typing import Any

from src.domain.capability import Capability
from src.interfaces.sandbox import SandboxInterface


class CapabilityExecutionService:
    def __init__(self, sandbox: SandboxInterface) -> None:
        self._sandbox = sandbox

    def execute(self, capability: Capability, input_data: dict[str, Any]) -> dict[str, Any]:
        return self._sandbox.execute(
            capability.implementation.code,
            capability.implementation.entrypoint,
            input_data,
        )
