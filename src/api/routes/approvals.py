from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.capability_service import IllegalTransitionError

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    reviewer: str = "administrator"
    notes: str = ""
    restrictions: dict = {}


@router.post("/{capability_id}/approve")
def approve(capability_id: str, body: ApprovalRequest):
    from src.main import container

    try:
        capability = container.approval_service.approve(capability_id, body.reviewer, body.notes)
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return capability.model_dump(mode="json")


@router.post("/{capability_id}/reject")
def reject(capability_id: str, body: ApprovalRequest):
    from src.main import container

    try:
        capability = container.approval_service.reject(capability_id, body.reviewer, body.notes)
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return capability.model_dump(mode="json")


@router.post("/{capability_id}/request-revision")
def request_revision(capability_id: str, body: ApprovalRequest):
    from src.main import container

    try:
        capability = container.approval_service.request_revision(
            capability_id, body.reviewer, body.notes
        )
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return capability.model_dump(mode="json")


@router.post("/{capability_id}/approve-with-restrictions")
def approve_with_restrictions(capability_id: str, body: ApprovalRequest):
    from src.main import container

    try:
        capability = container.approval_service.approve_with_restrictions(
            capability_id, body.restrictions, body.reviewer, body.notes
        )
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return capability.model_dump(mode="json")
