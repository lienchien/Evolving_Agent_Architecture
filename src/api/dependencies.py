from __future__ import annotations

from fastapi import HTTPException, Request

from src.main import Container


def get_container(request: Request) -> Container:
    container = request.app.state.container
    if container is None:
        # Never initialize on a request thread. ASGI hosts and TestClient users
        # must run the app lifespan (or inject a prebuilt container).
        raise HTTPException(status_code=503, detail="Application startup has not completed")
    return container
