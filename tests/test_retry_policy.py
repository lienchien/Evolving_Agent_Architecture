from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.domain.telemetry import (
    FailureCategory,
    FailureContext,
    FailureStage,
    ObservationKind,
    RetryDisposition,
    SideEffectStatus,
)
from src.main import Container
from src.services.retry_policy_service import BoundedRetryPolicy


def _failure_context(*, recoverable: bool = True) -> FailureContext:
    return FailureContext(
        trace_id="TRACE-policy",
        failure_id="FAIL-policy",
        stage=FailureStage.TOOL_EXECUTION,
        category=FailureCategory.TIMEOUT,
        target_type="capability",
        target_id="CAP-policy",
        exception_type="TimeoutError",
        recoverable=recoverable,
    )


@pytest.mark.parametrize(
    ("side_effect_status", "recoverable", "retry_count", "max_retries", "expected"),
    [
        (SideEffectStatus.IDEMPOTENT, True, 0, 2, RetryDisposition.RETRY),
        (SideEffectStatus.UNKNOWN, True, 0, 2, RetryDisposition.BLOCKED),
        (SideEffectStatus.NON_IDEMPOTENT, True, 0, 2, RetryDisposition.BLOCKED),
        (SideEffectStatus.IDEMPOTENT, False, 0, 2, RetryDisposition.BLOCKED),
        (SideEffectStatus.IDEMPOTENT, True, 2, 2, RetryDisposition.EXHAUSTED),
    ],
)
def test_retry_policy_is_bounded_and_fail_closed(
    side_effect_status,
    recoverable,
    retry_count,
    max_retries,
    expected,
):
    decision = BoundedRetryPolicy(hard_max_retries=2).decide(
        _failure_context(recoverable=recoverable),
        retry_count=retry_count,
        max_retries=max_retries,
        side_effect_status=side_effect_status,
    )

    assert decision.disposition is expected
    assert decision.retry_allowed is (expected is RetryDisposition.RETRY)
    assert decision.max_retries <= 2
    assert decision.recoverable is recoverable


@pytest.mark.parametrize(
    ("remaining_time_ms", "remaining_cost_usd"),
    [(0, None), (None, 0.0)],
)
def test_retry_policy_stops_when_time_or_cost_budget_is_exhausted(
    remaining_time_ms,
    remaining_cost_usd,
):
    decision = BoundedRetryPolicy().decide(
        _failure_context(),
        retry_count=0,
        max_retries=2,
        side_effect_status=SideEffectStatus.IDEMPOTENT,
        remaining_time_ms=remaining_time_ms,
        remaining_cost_usd=remaining_cost_usd,
    )

    assert decision.disposition is RetryDisposition.EXHAUSTED
    assert decision.retry_allowed is False
    assert decision.reason_code == "RETRY_BUDGET_EXHAUSTED"


def _active_capability(container: Container, task_family: str):
    first = container.main_agent.run_task(task_family, "create test capability", {})
    container.approval_service.approve(first["capability_id"])
    capability = container.capability_service.get(first["capability_id"])
    assert capability is not None
    return capability


def test_transient_idempotent_failure_retries_and_persists_evidence(tmp_path):
    database = tmp_path / "retry.db"
    container = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports"),
    )
    capability = _active_capability(container, "retry_success")
    capability.safety_requirements = {"idempotent": True, "max_retries": 1}
    container.capability_service.update(capability)
    container.execution_service.execute = Mock(
        side_effect=[TimeoutError("sensitive-timeout"), {"ok": True}]
    )

    result = container.main_agent.run_task("retry_success", "retry once", {})

    assert result["status"] == "completed"
    assert result["retry_count"] == 1
    detail = container.telemetry_service.get_trace_detail(result["trace_id"])
    assert [item.kind for item in detail.observations] == [
        ObservationKind.EXECUTION,
        ObservationKind.RETRY,
    ]
    assert len(detail.failures) == 1
    assert len(detail.recovery_attempts) == 1
    assert detail.recovery_attempts[0].retry_decision is not None
    assert (
        detail.recovery_attempts[0].retry_decision.disposition
        is RetryDisposition.RETRY
    )
    assert "sensitive-timeout" not in detail.model_dump_json()
    task_metric = container.research_metrics_service.list_tasks(
        trace_id=result["trace_id"]
    )[0]
    assert task_metric.retry_count == 1
    summary = container.telemetry_service.summarize(
        task_family="retry_success"
    )
    assert summary.retry_recovery_rate == 1.0

    restarted = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports-restarted"),
    )
    persisted = restarted.telemetry_service.get_trace_detail(result["trace_id"])
    assert persisted.recovery_attempts == detail.recovery_attempts


def test_unknown_side_effects_block_retry_and_record_policy_decision(tmp_path):
    container = Container(
        database_path=str(tmp_path / "blocked.db"),
        report_directory=str(tmp_path / "reports"),
    )
    _active_capability(container, "retry_blocked")
    container.execution_service.execute = Mock(side_effect=TimeoutError("blocked"))

    with pytest.raises(TimeoutError):
        container.main_agent.run_task("retry_blocked", "do not retry", {})

    failed_trace = container.telemetry_service.list_traces(
        task_family="retry_blocked"
    )[-1]
    detail = container.telemetry_service.get_trace_detail(failed_trace.trace_id)
    assert container.execution_service.execute.call_count == 1
    assert sum(item.kind is ObservationKind.RETRY for item in detail.observations) == 0
    assert detail.recovery_attempts[-1].retry_decision is not None
    assert (
        detail.recovery_attempts[-1].retry_decision.disposition
        is RetryDisposition.BLOCKED
    )
    assert (
        detail.recovery_attempts[-1].retry_decision.reason_code
        == "UNKNOWN_SIDE_EFFECTS"
    )


def test_retry_limit_exhaustion_is_persisted(tmp_path):
    container = Container(
        database_path=str(tmp_path / "exhausted.db"),
        report_directory=str(tmp_path / "reports"),
    )
    capability = _active_capability(container, "retry_exhausted")
    capability.safety_requirements = {"idempotent": True, "max_retries": 1}
    container.capability_service.update(capability)
    container.execution_service.execute = Mock(side_effect=TimeoutError("still down"))

    with pytest.raises(TimeoutError):
        container.main_agent.run_task("retry_exhausted", "retry to limit", {})

    failed_trace = container.telemetry_service.list_traces(
        task_family="retry_exhausted"
    )[-1]
    detail = container.telemetry_service.get_trace_detail(failed_trace.trace_id)
    assert container.execution_service.execute.call_count == 2
    assert len(detail.failures) == 2
    assert [
        attempt.retry_decision.disposition
        for attempt in detail.recovery_attempts
        if attempt.retry_decision is not None
    ] == [RetryDisposition.RETRY, RetryDisposition.EXHAUSTED]
    task_metric = container.research_metrics_service.list_tasks(
        trace_id=failed_trace.trace_id
    )[0]
    assert task_metric.retry_count == 1
    assert task_metric.error == "TimeoutError"
