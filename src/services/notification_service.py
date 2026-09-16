from __future__ import annotations

from src.domain.capability import Capability
from src.interfaces.notification import NotificationProvider


class NotificationService:
    def __init__(self, provider: NotificationProvider) -> None:
        self._provider = provider

    def capability_ready_for_review(self, capability: Capability) -> None:
        self._provider.send(
            "CapabilityReadyForReview",
            f"{capability.capability_id} ({capability.name}) is pending approval.",
        )
