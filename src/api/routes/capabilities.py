from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("")
def list_capabilities():
    from src.main import container

    return [c.model_dump(mode="json") for c in container.capability_service.list()]


@router.get("/{capability_id}")
def get_capability(capability_id: str):
    from src.main import container

    capability = container.capability_service.get(capability_id)
    if capability is None:
        raise HTTPException(status_code=404, detail="capability not found")
    return capability.model_dump(mode="json")


@router.get("/{capability_id}/test-report")
def get_test_report(capability_id: str):
    from src.main import container

    report = container.report_store.get(capability_id)
    if report is None:
        raise HTTPException(status_code=404, detail="test report not found")
    return report.model_dump(mode="json")
