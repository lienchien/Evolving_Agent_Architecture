from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    task_family: str
    description: str = ""
    input: dict = {}


class TaskResponse(BaseModel):
    status: str
    capability_id: str | None = None
    output: dict | None = None


@router.post("", response_model=TaskResponse)
def submit_task(task: TaskRequest) -> TaskResponse:
    from src.main import container

    result = container.main_agent.run_task(task.task_family, task.description, task.input)
    return TaskResponse(
        status=result.get("status", "unknown"),
        capability_id=result.get("capability_id"),
        output=result.get("output"),
    )
