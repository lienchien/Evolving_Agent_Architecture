from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_container
from src.domain.research import LLMInteractionMetric, TaskCostMetric, TokenCostSummary
from src.main import Container

# TODO(security): Research metrics expose model/provider identifiers, task families,
# capability IDs, costs and failure details. Require an authorized research-reader
# role plus tenant scoping before exposing these endpoints outside local development.
router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("/tasks", response_model=list[TaskCostMetric])
def list_task_costs(
    task_family: str | None = None,
    capability_id: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    container: Container = Depends(get_container),
):
    metrics = container.research_metrics_service.list_tasks(task_family, capability_id)
    return metrics[offset : offset + limit]


@router.get("/interactions", response_model=list[LLMInteractionMetric])
def list_llm_interactions(
    task_id: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    container: Container = Depends(get_container),
):
    metrics = container.research_metrics_service.list_interactions(task_id)
    return metrics[offset : offset + limit]


@router.get("/summary", response_model=TokenCostSummary)
def get_token_cost_summary(
    task_family: str | None = None,
    baseline_tokens_per_task: int | None = Query(default=None, ge=0),
    container: Container = Depends(get_container),
):
    return container.research_metrics_service.summarize(
        task_family=task_family,
        baseline_tokens_per_task=baseline_tokens_per_task,
    )
