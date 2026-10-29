from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.interfaces.telemetry_repository import TelemetryRepository
from src.main import Container, create_app


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
