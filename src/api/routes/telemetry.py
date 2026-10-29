from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_container
from src.domain.errors import UnknownTraceError
from src.domain.telemetry import (
    ExecutionTrace,
    ExecutionTraceDetail,
    FailureCategory,
    TelemetrySummary,
    TraceOutcome,
)
from src.main import Container


# TODO(security): Telemetry can reveal operational identifiers, routing behavior,
# failure patterns and exception types. Require an authorized operations-reader
# role and tenant scoping before exposing these endpoints outside development.
router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


def _validate_time_filters(*values: datetime | None) -> None:
    if any(
        value is not None and (value.tzinfo is None or value.utcoffset() is None)
        for value in values
    ):
        raise HTTPException(
            status_code=422,
            detail="telemetry time filters must include a timezone",
        )


@router.get("/traces", response_model=list[ExecutionTrace])
def list_traces(
    task_id: str | None = None,
    task_family: str | None = None,
    capability_id: str | None = None,
    target_id: str | None = None,
    failure_category: FailureCategory | None = None,
    exception_type: str | None = None,
    outcome: TraceOutcome | None = None,
    started_after: datetime | None = None,
    started_before: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    container: Container = Depends(get_container),
):
    _validate_time_filters(started_after, started_before)
    traces = container.telemetry_service.list_traces(
        task_id=task_id,
        task_family=task_family,
        capability_id=capability_id,
        target_id=target_id,
        failure_category=failure_category,
        exception_type=exception_type,
        outcome=outcome,
        started_after=started_after,
        started_before=started_before,
    )
    return traces[offset : offset + limit]


@router.get("/traces/{trace_id}", response_model=ExecutionTraceDetail)
def get_trace_detail(
    trace_id: str,
    container: Container = Depends(get_container),
):
    try:
        return container.telemetry_service.get_trace_detail(trace_id)
    except UnknownTraceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/summary", response_model=TelemetrySummary)
def get_summary(
    task_id: str | None = None,
    task_family: str | None = None,
    capability_id: str | None = None,
    target_id: str | None = None,
    failure_category: FailureCategory | None = None,
    exception_type: str | None = None,
    outcome: TraceOutcome | None = None,
    started_after: datetime | None = None,
    started_before: datetime | None = None,
    container: Container = Depends(get_container),
):
    _validate_time_filters(started_after, started_before)
    return container.telemetry_service.summarize(
        task_id=task_id,
        task_family=task_family,
        capability_id=capability_id,
        target_id=target_id,
        failure_category=failure_category,
        exception_type=exception_type,
        outcome=outcome,
        started_after=started_after,
        started_before=started_before,
    )
