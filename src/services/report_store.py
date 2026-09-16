from __future__ import annotations

from src.domain.report import TestReport


class TestReportStore:
    def __init__(self) -> None:
        self._reports: dict[str, TestReport] = {}

    def save(self, report: TestReport) -> None:
        self._reports[report.capability_id] = report

    def get(self, capability_id: str) -> TestReport | None:
        return self._reports.get(capability_id)
