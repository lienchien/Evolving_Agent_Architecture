from __future__ import annotations

from src.domain.report import TestReport
from src.interfaces.repository import CapabilityRepository


class TestReportStore:
    def __init__(self, repository: CapabilityRepository) -> None:
        self._repository = repository

    def save(self, report: TestReport) -> None:
        self._repository.save_report(report)

    def get(self, capability_id: str) -> TestReport | None:
        return self._repository.get_report(capability_id)
