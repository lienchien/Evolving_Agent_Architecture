from __future__ import annotations

from src.domain.capability import Capability, CapabilityStatus
from src.interfaces.repository import CapabilityRepository

_ALLOWED_TRANSITIONS: dict[CapabilityStatus, set[CapabilityStatus]] = {
    CapabilityStatus.DRAFT: {CapabilityStatus.CANDIDATE},
    CapabilityStatus.CANDIDATE: {CapabilityStatus.VALIDATING},
    CapabilityStatus.VALIDATING: {CapabilityStatus.TESTING},
    CapabilityStatus.TESTING: {CapabilityStatus.TESTED, CapabilityStatus.FAILED},
    CapabilityStatus.TESTED: {CapabilityStatus.PENDING_APPROVAL},
    CapabilityStatus.FAILED: {CapabilityStatus.ARCHIVED},
    CapabilityStatus.PENDING_APPROVAL: {
        CapabilityStatus.APPROVED,
        CapabilityStatus.ARCHIVED,
        CapabilityStatus.REVISION_REQUESTED,
    },
    CapabilityStatus.REVISION_REQUESTED: {CapabilityStatus.ARCHIVED},
    CapabilityStatus.APPROVED: {CapabilityStatus.ACTIVE},
    CapabilityStatus.ACTIVE: {CapabilityStatus.DEPRECATED, CapabilityStatus.REVOKED},
    CapabilityStatus.DEPRECATED: {CapabilityStatus.ARCHIVED},
    CapabilityStatus.REVOKED: {CapabilityStatus.ARCHIVED},
    CapabilityStatus.ARCHIVED: set(),
}


class IllegalTransitionError(Exception):
    pass


class CapabilityService:
    def __init__(self, repository: CapabilityRepository) -> None:
        self._repository = repository

    def create(self, capability: Capability) -> Capability:
        self._repository.save(capability)
        return capability

    def update(self, capability: Capability) -> Capability:
        self._repository.save(capability)
        return capability

    def get(self, capability_id: str) -> Capability | None:
        return self._repository.get(capability_id)

    def list(self) -> list[Capability]:
        return self._repository.list()

    def find_active_by_task_family(self, task_family: str) -> Capability | None:
        return self._repository.find_active_by_task_family(task_family)

    def transition(self, capability_id: str, new_status: CapabilityStatus) -> Capability:
        capability = self._repository.get(capability_id)
        if capability is None:
            raise ValueError(f"unknown capability {capability_id}")

        allowed = _ALLOWED_TRANSITIONS.get(capability.status, set())
        if new_status not in allowed:
            raise IllegalTransitionError(
                f"cannot transition {capability_id} from {capability.status} to {new_status}"
            )

        capability.status = new_status
        self._repository.save(capability)
        return capability
