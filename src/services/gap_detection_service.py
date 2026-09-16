from __future__ import annotations

from src.domain.gap import CapabilityGap, GapType
from src.services.capability_service import CapabilityService


class GapDetectionService:
    def __init__(self, capability_service: CapabilityService) -> None:
        self._capability_service = capability_service

    def detect(self, task_family: str, description: str, task_input: dict) -> CapabilityGap | None:
        existing = self._capability_service.find_active_by_task_family(task_family)
        if existing is not None:
            return None
        return CapabilityGap(
            task_family=task_family,
            description=description,
            gap_type=GapType.MISSING_CAPABILITY,
            task_input=task_input,
        )
