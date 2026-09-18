from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_container
from src.main import Container

# TODO(security): Unresolved, intentionally deferred during local development.
# Audit data is readable anonymously without tenant filtering. Require an
# authorized audit-reader identity and scope results before shared use.
router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit_entries(container: Container = Depends(get_container)):
    return container.audit_service.list()
