from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.interfaces.repository import CapabilityRepository


class AuditService:
    def __init__(self, repository: CapabilityRepository) -> None:
        self._repository = repository

    def record(self, action: str, capability_id: str, metadata: dict[str, Any] | None = None) -> None:
        self._repository.record_audit(self.make_entry(action, capability_id, metadata))

    @staticmethod
    def make_entry(action: str, capability_id: str, metadata: dict | None = None) -> dict:
        return {
            "action": action, "capability_id": capability_id, "metadata": metadata or {},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    def list(self) -> list[dict[str, Any]]:
        return self._repository.list_audit()
