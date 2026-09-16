from __future__ import annotations

from src.domain.approval import ApprovalDecision, ApprovalRecord
from src.domain.capability import Capability, CapabilityStatus
from src.services.audit_service import AuditService
from src.services.capability_service import CapabilityService
from src.services.notification_service import NotificationService
from src.services.policy_service import PolicyService


class ApprovalService:
    def __init__(
        self,
        capability_service: CapabilityService,
        notification_service: NotificationService,
        audit_service: AuditService,
        policy_service: PolicyService | None = None,
    ) -> None:
        self._capability_service = capability_service
        self._notification_service = notification_service
        self._audit_service = audit_service
        self._policy_service = policy_service or PolicyService()
        self._records: dict[str, ApprovalRecord] = {}

    def request_approval(self, capability: Capability) -> Capability:
        capability = self._capability_service.transition(
            capability.capability_id, CapabilityStatus.PENDING_APPROVAL
        )
        self._notification_service.capability_ready_for_review(capability)
        self._audit_service.record("request_approval", capability.capability_id)
        return capability

    def approve(self, capability_id: str, reviewer: str = "administrator", notes: str = "") -> Capability:
        if not self._policy_service.can_activate(capability_id):
            raise PermissionError(f"policy denies activation of {capability_id}")
        capability = self._capability_service.transition(capability_id, CapabilityStatus.APPROVED)
        capability = self._capability_service.transition(capability_id, CapabilityStatus.ACTIVE)
        self._record(capability_id, ApprovalDecision.APPROVED, reviewer, notes)
        self._audit_service.record("approve", capability_id, {"reviewer": reviewer})
        return capability

    def reject(self, capability_id: str, reviewer: str = "administrator", notes: str = "") -> Capability:
        capability = self._capability_service.transition(capability_id, CapabilityStatus.ARCHIVED)
        self._record(capability_id, ApprovalDecision.REJECTED, reviewer, notes)
        self._audit_service.record("reject", capability_id, {"reviewer": reviewer})
        return capability

    def request_revision(
        self, capability_id: str, reviewer: str = "administrator", notes: str = ""
    ) -> Capability:
        capability = self._capability_service.transition(
            capability_id, CapabilityStatus.REVISION_REQUESTED
        )
        self._record(capability_id, ApprovalDecision.REVISION_REQUESTED, reviewer, notes)
        self._audit_service.record("request_revision", capability_id, {"reviewer": reviewer})
        return capability

    def approve_with_restrictions(
        self,
        capability_id: str,
        restrictions: dict,
        reviewer: str = "administrator",
        notes: str = "",
    ) -> Capability:
        if not self._policy_service.can_activate(capability_id):
            raise PermissionError(f"policy denies activation of {capability_id}")
        capability = self._capability_service.transition(capability_id, CapabilityStatus.APPROVED)
        capability = self._capability_service.transition(capability_id, CapabilityStatus.ACTIVE)
        capability.distribution_metadata["restrictions"] = restrictions
        self._capability_service.update(capability)
        self._record(capability_id, ApprovalDecision.APPROVED_WITH_RESTRICTIONS, reviewer, notes)
        self._audit_service.record(
            "approve_with_restrictions", capability_id, {"reviewer": reviewer, **restrictions}
        )
        return capability

    def _record(
        self, capability_id: str, decision: ApprovalDecision, reviewer: str, notes: str
    ) -> None:
        record = ApprovalRecord(
            capability_id=capability_id,
            capability_version="0.1.0",
            decision=decision,
            reviewer=reviewer,
            notes=notes,
        )
        self._records[record.approval_id] = record

    def list_records(self) -> list[ApprovalRecord]:
        return list(self._records.values())
