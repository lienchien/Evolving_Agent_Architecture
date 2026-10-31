from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.mock_llm import MockLLMProvider
from src.infrastructure.sqlite_telemetry_repository import SqliteTelemetryRepository
from src.interfaces.telemetry_repository import TelemetryRepository
from src.main import Container, create_app


class _FailingCapabilityGenerationProvider(MockLLMProvider):
    def generate_capability(self, gap):
        raise RuntimeError("secret=provider-generation")


class _FailingBoundaryTestProvider(MockLLMProvider):
    def generate_boundary_tests(self, capability):
        raise RuntimeError("secret=provider-boundary-tests")


def test_instrumentation_failure_does_not_change_task_outcome(tmp_path):
    telemetry_repository = Mock(spec=TelemetryRepository)
    telemetry_repository.save_trace.side_effect = RuntimeError("telemetry unavailable")
    telemetry_repository.save_routing_decision.side_effect = RuntimeError(
        "telemetry unavailable"
    )
    telemetry_repository.save_execution_observation.side_effect = RuntimeError(
        "telemetry unavailable"
    )
    telemetry_repository.complete_trace.side_effect = RuntimeError("telemetry unavailable")

    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
        telemetry_repository=telemetry_repository,
    )
    with TestClient(create_app(container)) as client:
        response = client.post(
            "/api/tasks",
            json={
                "task_family": "csv_summary",
                "description": "summarize CSV",
                "input": {"csv_text": "a\n1\n"},
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "capability_pending_approval"
    assert container.telemetry_service.instrumentation_failure_count >= 4


def test_missing_observation_is_detected_after_restart_without_failing_task(
    tmp_path,
):
    database = tmp_path / "missing-event.db"
    durable_repository = SqliteTelemetryRepository(str(database))
    telemetry_repository = Mock(
        spec=TelemetryRepository,
        wraps=durable_repository,
    )
    telemetry_repository.save_execution_observation.side_effect = RuntimeError(
        "injected missing observation"
    )
    container = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports"),
        telemetry_repository=telemetry_repository,
    )

    result = container.main_agent.run_task(
        "missing_event",
        "complete the task even when one telemetry event cannot be saved",
        {},
    )

    assert result["status"] == "capability_pending_approval"
    assert container.telemetry_service.instrumentation_failure_count == 1
    live_summary = container.telemetry_service.summarize(
        task_id=result["task_id"]
    )
    assert live_summary.trace_count == 1
    assert live_summary.observation_count == 0
    assert live_summary.missing_event_count == 1
    assert live_summary.missing_event_trace_count == 1
    assert live_summary.instrumentation_failure_count == 1

    restarted = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports-restarted"),
    )
    persisted_summary = restarted.telemetry_service.summarize(
        task_id=result["task_id"]
    )
    assert persisted_summary.missing_event_count == 1
    assert persisted_summary.missing_event_trace_count == 1
    assert persisted_summary.instrumentation_failure_count == 0
    metric = restarted.research_metrics_service.list_tasks(
        trace_id=result["trace_id"]
    )[0]
    assert metric.task_id == result["task_id"]
    with TestClient(create_app(restarted)) as client:
        api_summary = client.get(
            "/api/telemetry/summary", params={"task_id": result["task_id"]}
        )
    assert api_summary.status_code == 200
    assert api_summary.json()["missing_event_count"] == 1
    assert api_summary.json()["missing_event_trace_count"] == 1


def test_concurrent_tasks_preserve_trace_event_and_cost_correlation(tmp_path):
    database = tmp_path / "concurrent-telemetry.db"
    container = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports"),
    )
    created = container.main_agent.run_task(
        "concurrent_telemetry",
        "create a capability before the concurrent execution check",
        {"text": "setup"},
    )
    capability_id = created["capability_id"]
    container.approval_service.approve(capability_id)

    def execute(index: int):
        return container.main_agent.run_task(
            "concurrent_telemetry",
            f"concurrent execution {index}",
            {"text": f"task {index}"},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(execute, range(16)))

    assert all(result["status"] == "completed" for result in results)
    task_ids = {result["task_id"] for result in results}
    trace_ids = {result["trace_id"] for result in results}
    assert len(task_ids) == 16
    assert len(trace_ids) == 16

    for result in results:
        detail = container.telemetry_service.get_trace_detail(result["trace_id"])
        assert detail.trace.task_id == result["task_id"]
        assert detail.trace.final_outcome.value == "succeeded"
        assert len(detail.routing_decisions) == 1
        assert detail.routing_decisions[0].trace_id == result["trace_id"]
        assert detail.routing_decisions[0].task_id == result["task_id"]
        assert detail.routing_decisions[0].selected_target_id == capability_id
        assert len(detail.observations) == 1
        assert detail.observations[0].trace_id == result["trace_id"]
        assert detail.observations[0].decision_id == detail.routing_decisions[0].decision_id
        assert detail.observations[0].target_id == capability_id

    metrics = {
        item.task_id: item
        for item in container.research_metrics_service.list_tasks(
            "concurrent_telemetry"
        )
    }
    for result in results:
        metric = metrics[result["task_id"]]
        assert metric.trace_id == result["trace_id"]
        assert metric.capability_id == capability_id
        assert metric.task_success is True

    summary = container.telemetry_service.summarize(
        task_family="concurrent_telemetry"
    )
    assert summary.trace_count == 17
    assert summary.completed_trace_count == 17
    assert summary.succeeded_trace_count == 16
    assert summary.partial_trace_count == 1
    assert summary.routing_decision_count == 17
    assert summary.observation_count == 17
    assert summary.missing_event_count == 0
    assert summary.missing_event_trace_count == 0
    assert summary.instrumentation_failure_count == 0

    restarted = Container(
        database_path=str(database),
        report_directory=str(tmp_path / "reports-restarted"),
    )
    restarted_summary = restarted.telemetry_service.summarize(
        task_family="concurrent_telemetry"
    )
    assert restarted_summary == summary


def test_execution_failure_is_correlated_and_sanitized(tmp_path):
    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
    )
    first = container.main_agent.run_task(
        "csv_summary",
        "summarize CSV",
        {"csv_text": "a\n1\n"},
    )
    container.approval_service.approve(first["capability_id"])
    container.main_agent._execution_service.execute = Mock(  # noqa: SLF001
        side_effect=RuntimeError("secret=do-not-store")
    )

    with pytest.raises(RuntimeError, match="do-not-store"):
        container.main_agent.run_task(
            "csv_summary",
            "summarize CSV",
            {"csv_text": "a\n2\n"},
        )

    traces = container.telemetry_service.list_traces(task_family="csv_summary")
    failed_trace = next(trace for trace in traces if trace.final_outcome.value == "failed")
    detail = container.telemetry_service.get_trace_detail(failed_trace.trace_id)
    assert detail.trace.task_id
    assert detail.routing_decisions[0].selected_target_id == first["capability_id"]
    assert detail.observations[0].outcome.value == "failed"
    assert detail.failures[0].stage.value == "tool_execution"
    assert detail.failures[0].category.value == "execution"
    assert detail.failures[0].exception_type == "RuntimeError"
    assert "do-not-store" not in detail.model_dump_json()

    summary = container.telemetry_service.summarize(task_family="csv_summary")
    assert summary.failed_trace_count == 1
    assert summary.failure_count == 1
    assert summary.failure_recurrences[0].count == 1

    with TestClient(create_app(container)) as client:
        capability_filtered = client.get(
            "/api/telemetry/traces",
            params={"capability_id": first["capability_id"]},
        )
        assert capability_filtered.status_code == 200
        assert {item["trace_id"] for item in capability_filtered.json()} == {
            trace.trace_id for trace in traces
        }

        failure_filtered = client.get(
            "/api/telemetry/traces",
            params={
                "target_id": first["capability_id"],
                "failure_category": "execution",
                "exception_type": "RuntimeError",
                "outcome": "failed",
                "started_after": failed_trace.started_at.isoformat(),
                "started_before": failed_trace.completed_at.isoformat(),
            },
        )
        assert failure_filtered.status_code == 200
        assert [item["trace_id"] for item in failure_filtered.json()] == [
            failed_trace.trace_id
        ]

        filtered_summary = client.get(
            "/api/telemetry/summary",
            params={
                "task_id": failed_trace.task_id,
                "capability_id": first["capability_id"],
                "failure_category": "execution",
                "exception_type": "RuntimeError",
            },
        )
        assert filtered_summary.status_code == 200
        assert filtered_summary.json()["trace_count"] == 1
        assert filtered_summary.json()["failure_count"] == 1

        invalid_time = client.get(
            "/api/telemetry/traces",
            params={"started_after": "2026-10-26T12:00:00"},
        )
        assert invalid_time.status_code == 422


@pytest.mark.parametrize(
    ("provider_type", "operation", "error_code"),
    [
        (
            _FailingCapabilityGenerationProvider,
            "capability_generation",
            "PROVIDER_CAPABILITY_GENERATION_FAILED",
        ),
        (
            _FailingBoundaryTestProvider,
            "boundary_test_generation",
            "PROVIDER_BOUNDARY_TEST_GENERATION_FAILED",
        ),
    ],
)
def test_provider_failure_has_specific_stage_and_sanitized_correlation(
    tmp_path, provider_type, operation, error_code
):
    provider = provider_type()
    container = Container(
        database_path=str(tmp_path / "capabilities.db"),
        report_directory=str(tmp_path / "reports"),
        llm_provider=provider,
    )

    with pytest.raises(RuntimeError, match="secret=provider"):
        container.main_agent.run_task(
            "provider_failure",
            "exercise provider failure mapping",
            {},
        )

    traces = container.telemetry_service.list_traces(task_family="provider_failure")
    assert len(traces) == 1
    assert traces[0].final_outcome.value == "failed"

    detail = container.telemetry_service.get_trace_detail(traces[0].trace_id)
    assert len(detail.failures) == 1
    failure = detail.failures[0]
    assert failure.stage.value == "provider"
    assert failure.category.value == "dependency"
    assert failure.error_code == error_code
    assert failure.error_summary == "LLM provider operation failed"
    assert failure.exception_type == "RuntimeError"
    assert failure.recoverable is False

    observation = next(
        item for item in detail.observations if item.target_type == "llm_provider"
    )
    assert observation.target_id == provider_type.__name__
    assert observation.metadata == {"operation": operation}
    assert "secret=provider" not in detail.model_dump_json()
