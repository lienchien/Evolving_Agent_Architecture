from __future__ import annotations

from src.domain.capability import Capability, CapabilityStatus
from src.domain.report import TestCaseResult
from src.interfaces.sandbox import SandboxInterface
from src.services.capability_service import CapabilityService


class ValidationService:
    def __init__(self, sandbox: SandboxInterface, capability_service: CapabilityService) -> None:
        self._sandbox = sandbox
        self._capability_service = capability_service

    def validate(self, capability: Capability) -> list[TestCaseResult]:
        self._capability_service.transition(capability.capability_id, CapabilityStatus.VALIDATING)

        test_cases = capability.validation_requirements.get("functional_test_cases", [])
        for case in test_cases:
            case.setdefault("test_type", "functional")

        results = self._sandbox.run_test_cases(
            capability.implementation.code,
            capability.implementation.entrypoint,
            test_cases,
        )

        self._capability_service.transition(capability.capability_id, CapabilityStatus.TESTING)
        return results
