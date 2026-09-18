from __future__ import annotations

from fastapi import HTTPException

from src.services.capability_service import IllegalTransitionError, UnknownCapabilityError


def approval_error(exc: Exception) -> HTTPException:
    if isinstance(exc, IllegalTransitionError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, UnknownCapabilityError):
        return HTTPException(status_code=404, detail=str(exc))
    raise exc
