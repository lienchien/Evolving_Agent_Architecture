from __future__ import annotations

from pathlib import Path

from src.domain.capability import Capability, CapabilityStatus
from src.domain.report import RiskLevel, TestReport
from src.interfaces.llm import LLMProvider
from src.interfaces.sandbox import SandboxInterface
from src.services.capability_service import CapabilityService
from src.services.report_store import TestReportStore


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
    ) -> None:
        self._llm_provider = llm_provider
        self._sandbox = sandbox
        self._capability_service = capability_service
        self._report_store = report_store
        self._report_directory = Path(report_directory)

    def run_autonomous_tests(self, capability: Capability, functional_results: list) -> TestReport:
        boundary_cases = self._llm_provider.generate_boundary_tests(capability)
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
