from __future__ import annotations

from pathlib import Path
from time import perf_counter

from src.domain.capability import Capability, CapabilityStatus
from src.domain.report import RiskLevel, TestReport
from src.domain.research import ResearchPhase, TokenUsage
from src.interfaces.llm import LLMProvider, LLMResponse
from src.interfaces.sandbox import SandboxInterface
from src.services.capability_service import CapabilityService
from src.services.report_store import TestReportStore
from src.services.research_metrics_service import ResearchMetricsService


class TestingService:
    """Independent from EvolutionService: tries to find where the new
    capability might fail, rather than proving it works (see design doc §17).
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        sandbox: SandboxInterface,
        capability_service: CapabilityService,
        report_store: TestReportStore,
        report_directory: Path | str = "capability_library",
        research_metrics: ResearchMetricsService | None = None,
    ) -> None:
        self._llm_provider = llm_provider
        self._sandbox = sandbox
        self._capability_service = capability_service
        self._report_store = report_store
        self._report_directory = Path(report_directory)
        self._research_metrics = research_metrics

    def run_autonomous_tests(
        self, capability: Capability, functional_results: list, task_id: str | None = None,
    ) -> TestReport:
        started = perf_counter()
        try:
            raw_response = self._llm_provider.generate_boundary_tests(capability)
        except Exception as exc:
            if self._research_metrics is not None and task_id is not None:
                self._research_metrics.record_llm_interaction(
                    task_id=task_id,
                    task_family=capability.task_family,
                    capability_id=capability.capability_id,
                    capability_version=capability.capability_version,
                    phase=ResearchPhase.TESTING,
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
        boundary_cases = response.value
        if self._research_metrics is not None and task_id is not None:
            self._research_metrics.record_llm_interaction(
                task_id=task_id,
                task_family=capability.task_family,
                capability_id=capability.capability_id,
                capability_version=capability.capability_version,
                phase=ResearchPhase.TESTING,
                usage=response.usage,
                latency_ms=(perf_counter() - started) * 1000,
                success=True,
            )
        for case in boundary_cases:
            case.setdefault("test_type", "boundary")

        boundary_results = self._sandbox.run_test_cases(
            capability.implementation.code,
            capability.implementation.entrypoint,
            boundary_cases,
        )

        all_results = list(functional_results) + list(boundary_results)
        failed_results = [result for result in all_results if not result.passed]
        failed = [result.name for result in failed_results]
        pass_rate = (len(all_results) - len(failed)) / len(all_results) if all_results else 0.0

        risk_level = RiskLevel.LOW
        if pass_rate < 1.0:
            risk_level = RiskLevel.MEDIUM
        if pass_rate < 0.5:
            risk_level = RiskLevel.HIGH

        functional_passed = all(result.passed for result in functional_results)
        final_status = CapabilityStatus.TESTED if functional_passed else CapabilityStatus.FAILED
        recommended_action = "manual_review" if functional_passed else "regenerate"

        known_limitations = []
        for result in failed_results:
            detail = f"{result.test_type} test failed: {result.name}"
            if result.error:
                detail += f" ({result.error})"
            known_limitations.append(detail)

        report = TestReport(
            capability_id=capability.capability_id,
            capability_version=capability.capability_version,
            test_cases=all_results,
            pass_rate=pass_rate,
            failed_cases=failed,
            known_limitations=known_limitations,
            risk_level=risk_level,
            recommended_action=recommended_action,
        )
        self._report_store.save(report)
        self._write_report_files(capability, report)

        self._capability_service.transition(capability.capability_id, final_status)
        return report

    def _write_report_files(self, capability: Capability, report: TestReport) -> None:
        capability_dir = self._report_directory / capability.capability_id
        capability_dir.mkdir(parents=True, exist_ok=True)
        (capability_dir / "test_report.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )
        (capability_dir / "test_report.md").write_text(report.to_markdown(), encoding="utf-8")
