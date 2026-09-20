from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_container
from src.main import Container

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


@router.get("/queue")
def queue_status(container: Container = Depends(get_container)):
    return {"pending": container.queue.size()}
