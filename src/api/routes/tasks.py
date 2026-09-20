from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.dependencies import get_container
from src.main import Container

# TODO(security): Unresolved, intentionally deferred during local development.
# Anonymous callers can generate and execute capabilities; capability lookup
# does not check owner/tenant access. Authentication, execution authorization,
# request-size limits and resource quotas remain to be implemented.
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    task_family: str
    description: str = ""
    input: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    status: str
    capability_id: str | None = None
    output: dict | None = None


@router.post("", response_model=TaskResponse)
def submit_task(task: TaskRequest, container: Container = Depends(get_container)) -> TaskResponse:
    result = container.main_agent.run_task(task.task_family, task.description, task.input)
    return TaskResponse(
        status=result.get("status", "unknown"),
        capability_id=result.get("capability_id"),
        output=result.get("output"),
    )
