from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.dependencies import get_container
from src.api.errors import approval_error
from src.domain.capability import Capability
from src.main import Container
from src.services.capability_service import IllegalTransitionError

# TODO(security): Unresolved, intentionally deferred during local development.
# All approval actions currently allow anonymous callers; add authentication
# and administrator authorization before exposing these routes to other users.
router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    # TODO(security): Derive reviewer from authenticated identity. This field is
    # currently caller-controlled and cannot prove who approved a capability.
    reviewer: str = "administrator"
    notes: str = ""
    # TODO(security): Restrictions are stored metadata only, not enforced by
    # the executor or sandbox. They must not be treated as access controls.
    restrictions: dict = Field(default_factory=dict)


@router.post("/{capability_id}/approve", response_model=Capability)
def approve(capability_id: str, body: ApprovalRequest, container: Container = Depends(get_container)):
    try:
        capability = container.approval_service.approve(capability_id, body.reviewer, body.notes)
    except (ValueError, PermissionError, IllegalTransitionError) as exc:
        raise approval_error(exc) from exc
    return capability


@router.post("/{capability_id}/reject", response_model=Capability)
def reject(capability_id: str, body: ApprovalRequest, container: Container = Depends(get_container)):
    try:
        capability = container.approval_service.reject(capability_id, body.reviewer, body.notes)
    except (ValueError, IllegalTransitionError) as exc:
        raise approval_error(exc) from exc
    return capability


@router.post("/{capability_id}/request-revision", response_model=Capability)
def request_revision(capability_id: str, body: ApprovalRequest, container: Container = Depends(get_container)):
    try:
        capability = container.approval_service.request_revision(
            capability_id, body.reviewer, body.notes
        )
    except (ValueError, IllegalTransitionError) as exc:
        raise approval_error(exc) from exc
    return capability


@router.post("/{capability_id}/approve-with-restrictions", response_model=Capability)
def approve_with_restrictions(
    capability_id: str, body: ApprovalRequest, container: Container = Depends(get_container)
):
    try:
        capability = container.approval_service.approve_with_restrictions(
            capability_id, body.restrictions, body.reviewer, body.notes
        )
    except (ValueError, PermissionError, IllegalTransitionError) as exc:
        raise approval_error(exc) from exc
    return capability
