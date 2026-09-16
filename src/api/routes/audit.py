from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit_entries():
    from src.main import container

    return container.audit_service.list()
