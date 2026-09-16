from __future__ import annotations

from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.domain.gap import CapabilityGap
from src.interfaces.llm import LLMProvider
from src.services.capability_service import CapabilityService


class EvolutionService:
    def __init__(self, llm_provider: LLMProvider, capability_service: CapabilityService) -> None:
        self._llm_provider = llm_provider
        self._capability_service = capability_service

    def evolve(self, gap: CapabilityGap) -> Capability:
        generated = self._llm_provider.generate_capability(gap)

        capability = Capability(
            name=generated.name,
            description=generated.description,
            task_family=gap.task_family,
            inputs=generated.inputs,
            outputs=generated.outputs,
            dependencies=generated.dependencies,
            implementation=Implementation(code=generated.code),
            validation_requirements={
                "functional_test_cases": generated.functional_test_cases,
            },
        )
        self._capability_service.create(capability)
        return self._capability_service.transition(
            capability.capability_id, CapabilityStatus.CANDIDATE
        )
