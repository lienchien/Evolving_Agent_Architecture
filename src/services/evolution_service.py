from __future__ import annotations

from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.domain.gap import CapabilityGap
from src.interfaces.llm import LLMProvider
from src.services.capability_service import CapabilityService


class EvolutionService:
    def __init__(self, llm_provider: LLMProvider, capability_service: CapabilityService) -> None:
        self._llm_provider = llm_provider
        self._capability_service = capability_service

    def evolve(self, gap: CapabilityGap, reserved: Capability | None = None) -> Capability:
        generated = self._llm_provider.generate_capability(gap)

        capability = reserved or Capability(
            name=generated.name, task_family=gap.task_family,
            implementation=Implementation(code=generated.code),
        )
        capability.name = generated.name
        capability.description = generated.description
        capability.inputs = generated.inputs
        capability.outputs = generated.outputs
        capability.dependencies = generated.dependencies
        capability.implementation = Implementation(code=generated.code)
        capability.validation_requirements = {"functional_test_cases": generated.functional_test_cases}
        if reserved is None:
            self._capability_service.create(capability)
        self._capability_service.apply_transition(capability, CapabilityStatus.CANDIDATE)
        return self._capability_service.update(capability)
