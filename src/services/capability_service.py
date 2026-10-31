from __future__ import annotations

from src.domain.capability import Capability, CapabilityStatus
from src.domain.approval import ApprovalRecord
from src.domain.errors import IllegalTransitionError, UnknownCapabilityError
from src.interfaces.repository import CapabilityRepository

_ALLOWED_TRANSITIONS: dict[CapabilityStatus, set[CapabilityStatus]] = {
    CapabilityStatus.DRAFT: {CapabilityStatus.CANDIDATE, CapabilityStatus.FAILED},
    CapabilityStatus.CANDIDATE: {CapabilityStatus.VALIDATING, CapabilityStatus.FAILED},
    CapabilityStatus.VALIDATING: {CapabilityStatus.TESTING, CapabilityStatus.FAILED},
    CapabilityStatus.TESTING: {CapabilityStatus.TESTED, CapabilityStatus.FAILED},
    CapabilityStatus.TESTED: {CapabilityStatus.PENDING_APPROVAL, CapabilityStatus.FAILED},
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


class CapabilityService:
    def __init__(self, repository: CapabilityRepository) -> None:
        self._repository = repository

    def create(self, capability: Capability) -> Capability:
        self._repository.create(capability)
        return capability

    def update(
        self, capability: Capability, *, approval: ApprovalRecord | None = None,
        audit: dict | None = None,
    ) -> Capability:
        self._repository.save(capability, approval=approval, audit=audit)
        return capability

    def list_approvals(self) -> list[ApprovalRecord]:
        return self._repository.list_approvals()

    def get(self, capability_id: str) -> Capability | None:
        return self._repository.get(capability_id)

    def list(self) -> list[Capability]:
        return self._repository.list()

    def find_active_by_task_family(self, task_family: str) -> Capability | None:
        return self._repository.find_active_by_task_family(task_family)

    def list_active_by_task_family(self, task_family: str) -> list[Capability]:
        return self._repository.list_active_by_task_family(task_family)

    def list_eligible_fallbacks(
        self,
        primary: Capability,
        input_data: dict,
        *,
        excluded_ids: set[str] | None = None,
    ) -> list[Capability]:
        excluded = excluded_ids or set()
        candidates = []
        for candidate in self.list_active_by_task_family(primary.task_family):
            if candidate.capability_id in excluded or not candidate.fallback_eligible:
                continue
            if (
                candidate.tenant_id != primary.tenant_id
                or candidate.owner_id != primary.owner_id
                or candidate.organization_id != primary.organization_id
                or candidate.scope != primary.scope
                or candidate.trust_level != primary.trust_level
            ):
                continue
            if not set(candidate.inputs).issubset(input_data):
                continue
            if candidate.safety_requirements.get("idempotent") is not True:
                continue
            candidates.append(candidate)
        return sorted(
            candidates,
            key=lambda item: (item.routing_priority, item.capability_id),
        )

    def reserve_for_task(self, task_family: str, description: str) -> tuple[Capability, bool]:
        return self._repository.reserve_for_task(task_family, description)

    def transition(self, capability_id: str, new_status: CapabilityStatus) -> Capability:
        capability = self._repository.get(capability_id)
        if capability is None:
            raise UnknownCapabilityError(f"unknown capability {capability_id}")

        self.apply_transition(capability, new_status)
        return self.update(capability)

    @staticmethod
    def apply_transition(capability: Capability, new_status: CapabilityStatus) -> None:
        """Validate a transition in memory; callers commit the final state once."""
        allowed = _ALLOWED_TRANSITIONS.get(capability.status, set())
        if new_status not in allowed:
            raise IllegalTransitionError(
                f"cannot transition {capability.capability_id} from {capability.status} to {new_status}"
            )

        capability.status = new_status
