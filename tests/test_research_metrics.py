from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.domain.research import TokenUsage, UsageSource
from src.infrastructure.mock_llm import MockLLMProvider
from src.main import Container, create_app


class _UsageReportingMockLLM(MockLLMProvider):
    def generate_capability(self, gap):
        response = super().generate_capability(gap)
        response.usage = TokenUsage(
            provider="research-mock",
            model="reported-usage",
            source=UsageSource.PROVIDER_REPORTED,
            input_tokens=50,
            output_tokens=20,
            reasoning_tokens=10,
            total_tokens=80,
            provider_cost_usd=0.008,
        )
        return response

    def generate_boundary_tests(self, capability):
        response = super().generate_boundary_tests(capability)
        response.usage = TokenUsage(
            provider="research-mock",
            model="reported-usage",
            source=UsageSource.PROVIDER_REPORTED,
            input_tokens=12,
            output_tokens=5,
            reasoning_tokens=3,
            total_tokens=20,
            provider_cost_usd=0.002,
        )
        return response


class _FailingMockLLM(MockLLMProvider):
    def generate_capability(self, gap):
        raise RuntimeError("provider generation failed")


def _submit_words(client: TestClient):
    return client.post(
        "/api/tasks",
        json={
            "task_family": "research_words",
            "description": "count words",
            "input": {"text": "one two three"},
        },
    )


def test_mock_usage_is_persisted_as_unavailable_without_estimation(tmp_path):
    database = tmp_path / "research.db"
    container = Container(
        database_path=str(database), report_directory=str(tmp_path / "reports")
    )
    with TestClient(create_app(container)) as client:
        created = _submit_words(client).json()
        task_id = created["task_id"]

        task_metric = client.get(f"/api/research/tasks?task_family=research_words").json()[0]
        assert task_metric["task_id"] == task_id
        assert task_metric["capability_created"] is True
        assert task_metric["outcome_status"] == "capability_pending_approval"
        assert task_metric["task_success"] is False
        assert task_metric["llm_call_count"] == 2
        assert task_metric["total_tokens"] is None
        assert task_metric["reasoning_tokens"] is None
        assert task_metric["provider_cost_usd"] == 0.0

        interactions = client.get(f"/api/research/interactions?task_id={task_id}").json()
        assert [item["phase"] for item in interactions] == ["generation", "testing"]
        assert all(item["usage"]["source"] == "unavailable" for item in interactions)
        assert all(item["usage"]["total_tokens"] is None for item in interactions)

        summary = client.get("/api/research/summary?task_family=research_words").json()
        assert summary["task_count"] == 1
        assert summary["token_data_complete"] is False
        assert summary["break_even_reuse_count"] is None
        assert "no token estimate" in summary["note"]

    restarted = Container(
        database_path=str(database), report_directory=str(tmp_path / "reports-restarted")
    )
    with TestClient(create_app(restarted)) as client:
        assert client.get(f"/api/research/tasks?task_family=research_words").json()[0][
            "task_id"
        ] == task_id
        assert len(client.get(f"/api/research/interactions?task_id={task_id}").json()) == 2


def test_reported_usage_calculates_amortization_and_break_even(tmp_path):
    container = Container(
        database_path=str(tmp_path / "research.db"),
        report_directory=str(tmp_path / "reports"),
        llm_provider=_UsageReportingMockLLM(),
    )
    with TestClient(create_app(container)) as client:
        created = _submit_words(client).json()
        capability_id = created["capability_id"]
        client.post(f"/api/approvals/{capability_id}/approve", json={})
        reused = _submit_words(client).json()
        assert reused["status"] == "completed"
        assert reused["capability_id"] == capability_id

        metrics = client.get(
            f"/api/research/tasks?capability_id={capability_id}"
        ).json()
        assert len(metrics) == 2
        assert metrics[0]["capability_created"] is True
        assert metrics[0]["total_tokens"] == 100
        assert metrics[0]["token_breakdown"]["generation_tokens"] == 80
        assert metrics[0]["token_breakdown"]["testing_tokens"] == 20
        assert metrics[1]["capability_reused"] is True
        assert metrics[1]["total_tokens"] == 0
        assert metrics[1]["llm_call_count"] == 0
        assert metrics[1]["capability_execution_ms"] is not None

        summary = client.get(
            "/api/research/summary",
            params={"task_family": "research_words", "baseline_tokens_per_task": 60},
        ).json()
        assert summary["task_count"] == 2
        assert summary["successful_task_count"] == 1
        assert summary["task_success_rate"] == 0.5
        assert summary["capability_creation_count"] == 1
        assert summary["capability_reuse_count"] == 1
        assert summary["llm_call_count"] == 2
        assert summary["token_data_complete"] is True
        assert summary["cumulative_ceaa_tokens"] == 100
        assert summary["average_tokens_per_task"] == 50
        assert summary["average_creation_tokens"] == 100
        assert summary["average_reuse_tokens"] == 0
        assert summary["average_latency_ms"] is not None
        assert summary["average_capability_execution_ms"] is not None
        assert summary["cumulative_baseline_tokens"] == 120
        assert summary["token_saving"] == 20
        assert summary["token_saving_rate"] == pytest.approx(1 / 6)
        assert summary["break_even_reuse_count"] == 1
        assert summary["cumulative_provider_cost_usd"] == pytest.approx(0.01)


def test_failed_generation_preserves_failure_cost_observation(tmp_path):
    container = Container(
        database_path=str(tmp_path / "research.db"),
        report_directory=str(tmp_path / "reports"),
        llm_provider=_FailingMockLLM(),
    )

    with pytest.raises(RuntimeError, match="provider generation failed"):
        container.main_agent.run_task("failing_research", "fail generation", {})

    tasks = container.research_metrics_service.list_tasks("failing_research")
    assert len(tasks) == 1
    assert tasks[0].capability_created is True
    assert tasks[0].capability_id is not None
    assert tasks[0].outcome_status == "error"
    assert tasks[0].task_success is False
    assert tasks[0].llm_call_count == 1
    assert tasks[0].total_tokens is None
    assert tasks[0].token_breakdown["generation_tokens"] is None

    interactions = container.research_metrics_service.list_interactions(tasks[0].task_id)
    assert len(interactions) == 1
    assert interactions[0].phase.value == "generation"
    assert interactions[0].success is False
    assert interactions[0].error == "provider generation failed"
