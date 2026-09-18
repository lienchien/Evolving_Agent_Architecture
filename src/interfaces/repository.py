from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.capability import Capability
from src.domain.approval import ApprovalRecord
from src.domain.report import TestReport


class CapabilityRepository(ABC):
    @abstractmethod
    def create(self, capability: Capability) -> None: ...

    @abstractmethod
    def save(
        self, capability: Capability, *, approval: ApprovalRecord | None = None,
        audit: dict | None = None,
    ) -> None: ...

    @abstractmethod
    def get(self, capability_id: str) -> Capability | None: ...

    @abstractmethod
    def list(self) -> list[Capability]: ...

    @abstractmethod
    def find_active_by_task_family(self, task_family: str) -> Capability | None: ...

    @abstractmethod
    def reserve_for_task(self, task_family: str, description: str) -> tuple[Capability, bool]: ...

    @abstractmethod
    def save_report(self, report: TestReport) -> None: ...

    @abstractmethod
    def get_report(self, capability_id: str) -> TestReport | None: ...

    @abstractmethod
    def record_audit(self, entry: dict) -> None: ...

    @abstractmethod
    def list_audit(self) -> list[dict]: ...

    @abstractmethod
    def list_approvals(self) -> list[ApprovalRecord]: ...
