from __future__ import annotations

from time import perf_counter

from src.domain.capability import Capability, CapabilityStatus, Implementation
from src.domain.gap import CapabilityGap
from src.domain.research import ResearchPhase, TokenUsage
from src.interfaces.llm import LLMProvider, LLMResponse
from src.services.capability_service import CapabilityService
from src.services.research_metrics_service import ResearchMetricsService


class EvolutionService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        capability_service: CapabilityService,
        research_metrics: ResearchMetricsService | None = None,
    ) -> None:
        self._llm_provider = llm_provider
        self._capability_service = capability_service
        self._research_metrics = research_metrics

    def evolve(
        self, gap: CapabilityGap, reserved: Capability | None = None, task_id: str | None = None,
    ) -> Capability:
        started = perf_counter()
        try:
            raw_response = self._llm_provider.generate_capability(gap)
        except Exception as exc:
            if self._research_metrics is not None and task_id is not None:
                self._research_metrics.record_llm_interaction(
                    task_id=task_id,
                    task_family=gap.task_family,
                    capability_id=reserved.capability_id if reserved else None,
                    capability_version=reserved.capability_version if reserved else None,
                    phase=ResearchPhase.GENERATION,
                    usage=TokenUsage(),
                    latency_ms=(perf_counter() - started) * 1000,
                    success=False,
                    error=str(exc),
                )
            raise
        response = (
            raw_response if isinstance(raw_response, LLMResponse)
            else LLMResponse(value=raw_response)
        )
        generated = response.value

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
        if self._research_metrics is not None and task_id is not None:
            self._research_metrics.record_llm_interaction(
                task_id=task_id,
                task_family=gap.task_family,
                capability_id=capability.capability_id,
                capability_version=capability.capability_version,
                phase=ResearchPhase.GENERATION,
                usage=response.usage,
                latency_ms=(perf_counter() - started) * 1000,
                success=True,
            )
        if reserved is None:
            self._capability_service.create(capability)
        self._capability_service.apply_transition(capability, CapabilityStatus.CANDIDATE)
        return self._capability_service.update(capability)
