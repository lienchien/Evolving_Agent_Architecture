from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


@router.get("/queue")
def queue_status():
    from src.main import container

    return {"pending": container.queue.size()}
