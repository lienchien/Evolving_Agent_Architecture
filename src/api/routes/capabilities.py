from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_container
from src.domain.capability import Capability, CapabilityStatus
from src.domain.report import TestReport
from src.main import Container

# TODO(security): Unresolved, intentionally deferred during local development.
# Listing, detail and report routes have no authentication or owner/tenant/scope
# checks. Responses include implementation code, test data and metadata. Add
# access checks and appropriate response-field filtering before shared use.
router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("", response_model=list[Capability])
def list_capabilities(
    status: CapabilityStatus | None = None,
    task_family: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    container: Container = Depends(get_container),
):
    # TODO(security): Pagination currently limits the response only; push filters,
    # ordering and pagination into the repository to bound query resource usage.
    capabilities = container.capability_service.list()
    if status is not None:
        capabilities = [capability for capability in capabilities if capability.status == status]
    if task_family is not None:
        capabilities = [capability for capability in capabilities if capability.task_family == task_family]
    capabilities.sort(key=lambda capability: (capability.created_at, capability.capability_id))
    return capabilities[offset : offset + limit]


@router.get("/{capability_id}", response_model=Capability)
def get_capability(capability_id: str, container: Container = Depends(get_container)):
    capability = container.capability_service.get(capability_id)
    if capability is None:
        raise HTTPException(status_code=404, detail="capability not found")
    return capability


@router.get("/{capability_id}/test-report", response_model=TestReport)
def get_test_report(capability_id: str, container: Container = Depends(get_container)):
    report = container.report_store.get(capability_id)
    if report is None:
        raise HTTPException(status_code=404, detail="test report not found")
    return report
