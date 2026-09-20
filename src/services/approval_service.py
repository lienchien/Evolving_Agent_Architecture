from __future__ import annotations

from src.domain.approval import ApprovalDecision, ApprovalRecord
from src.domain.capability import Capability, CapabilityStatus
from src.domain.errors import IllegalTransitionError, UnknownCapabilityError
from src.services.audit_service import AuditService
from src.services.capability_service import CapabilityService
from src.services.notification_service import NotificationService
from src.services.policy_service import PolicyService


class ApprovalService:
    def __init__(
        self, capability_service: CapabilityService,
        notification_service: NotificationService, audit_service: AuditService,
        policy_service: PolicyService | None = None,
    ) -> None:
        self._capability_service = capability_service
        self._notification_service = notification_service
        self._audit_service = audit_service
        self._policy_service = policy_service or PolicyService()

    def request_approval(self, capability: Capability) -> Capability:
        current = self._capability_service.get(capability.capability_id)
        if current is None:
            raise UnknownCapabilityError(f"unknown capability {capability.capability_id}")
        self._capability_service.apply_transition(current, CapabilityStatus.PENDING_APPROVAL)
        capability = self._capability_service.update(current, audit=self._audit_service.make_entry(
            "request_approval", current.capability_id
        ))
        self._notification_service.capability_ready_for_review(capability)
        return capability

    def approve(self, capability_id: str, reviewer: str = "administrator", notes: str = "") -> Capability:
        return self._decide(capability_id, ApprovalDecision.APPROVED, reviewer, notes)

    def reject(self, capability_id: str, reviewer: str = "administrator", notes: str = "") -> Capability:
        return self._decide(capability_id, ApprovalDecision.REJECTED, reviewer, notes)

    def request_revision(
        self, capability_id: str, reviewer: str = "administrator", notes: str = ""
    ) -> Capability:
        return self._decide(capability_id, ApprovalDecision.REVISION_REQUESTED, reviewer, notes)

    def approve_with_restrictions(
        self, capability_id: str, restrictions: dict,
        reviewer: str = "administrator", notes: str = "",
    ) -> Capability:
        return self._decide(
            capability_id, ApprovalDecision.APPROVED_WITH_RESTRICTIONS, reviewer, notes, restrictions
        )

    def _decide(
        self, capability_id: str, decision: ApprovalDecision, reviewer: str,
        notes: str, restrictions: dict | None = None,
    ) -> Capability:
        capability = self._capability_service.get(capability_id)
        if capability is None:
            raise UnknownCapabilityError(f"unknown capability {capability_id}")
        if capability.status != CapabilityStatus.PENDING_APPROVAL:
            raise IllegalTransitionError(f"{capability_id} is not pending approval")

        if decision in (ApprovalDecision.APPROVED, ApprovalDecision.APPROVED_WITH_RESTRICTIONS):
            if not self._policy_service.can_activate(capability_id):
                raise PermissionError(f"policy denies activation of {capability_id}")
            self._capability_service.apply_transition(capability, CapabilityStatus.APPROVED)
            self._capability_service.apply_transition(capability, CapabilityStatus.ACTIVE)
            if restrictions is not None:
                # TODO(security): Metadata only; execution restrictions are not enforced.
                capability.distribution_metadata["restrictions"] = restrictions
        else:
            target = (CapabilityStatus.ARCHIVED if decision == ApprovalDecision.REJECTED
                      else CapabilityStatus.REVISION_REQUESTED)
            self._capability_service.apply_transition(capability, target)

        record = ApprovalRecord(
            capability_id=capability_id, capability_version=capability.capability_version,
            decision=decision, reviewer=reviewer, notes=notes, restrictions=restrictions or {},
        )
        action = {
            ApprovalDecision.APPROVED: "approve",
            ApprovalDecision.REJECTED: "reject",
            ApprovalDecision.REVISION_REQUESTED: "request_revision",
            ApprovalDecision.APPROVED_WITH_RESTRICTIONS: "approve_with_restrictions",
        }[decision]
        audit = self._audit_service.make_entry(
            action, capability_id, {"reviewer": reviewer, "restrictions": restrictions or {}}
        )
        # State, restrictions, decision record and audit either all commit or
        # all roll back. A stale decision cannot leave a success record behind.
        self._capability_service.update(capability, approval=record, audit=audit)
        return capability

    def list_records(self) -> list[ApprovalRecord]:
        return self._capability_service.list_approvals()
