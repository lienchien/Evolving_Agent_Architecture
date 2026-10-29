from __future__ import annotations

from typing import Any

from src.domain.gap import CapabilityGap
from src.interfaces.llm import GeneratedCapability, LLMProvider
from src.infrastructure.sqlite_telemetry_repository import SqliteTelemetryRepository
from tests.support import build_main_agent


class _AlwaysWrongLLMProvider(LLMProvider):
    """Deterministically generates code that fails its own functional test,
    used to exercise the Testing -> Failed path without depending on a real LLM.
    """

    def generate_capability(self, gap: CapabilityGap) -> GeneratedCapability:
        return GeneratedCapability(
            name="always_wrong",
            description="deliberately broken capability for testing the FAILED path",
            code="def run(input):\n    return {'value': 1}\n",
            dependencies=[],
            inputs=["value"],
            outputs=["value"],
            functional_test_cases=[
                {
                    "name": "expects_two",
                    "input": {"value": 1},
                    "expected_output": {"value": 2},
                }
            ],
        )

    def generate_boundary_tests(self, capability) -> list[dict[str, Any]]:
        return []


def test_failed_functional_test_marks_capability_failed(tmp_path):
    main_agent, capability_service, _ = build_main_agent(
        tmp_path, llm_provider=_AlwaysWrongLLMProvider()
    )

    result = main_agent.run_task(
        task_family="always_broken",
        description="this will never pass its own functional test",
        input_data={"value": 1},
    )

    assert result["status"] == "capability_failed"
    capability = capability_service.get(result["capability_id"])
    assert capability.status.value == "failed"
    telemetry = SqliteTelemetryRepository(str(tmp_path / "capabilities.db"))
    trace = telemetry.get_trace(result["trace_id"])
    assert trace.final_outcome.value == "failed"
    observations = telemetry.list_execution_observations(result["trace_id"])
    assert observations[0].outcome.value == "failed"
    failures = telemetry.list_execution_failures(result["trace_id"])
    assert failures[0].stage.value == "validation"
    assert failures[0].category.value == "validation"


def test_revision_requested_reopens_the_gap(tmp_path):
    main_agent, capability_service, approval_service = build_main_agent(tmp_path)

    first = main_agent.run_task(
        task_family="csv_summary",
        description="summarize numeric columns of a csv file",
        input_data={"csv_text": "a,b\n1,2\n3,4\n"},
    )
    first_capability_id = first["capability_id"]

    approval_service.request_revision(first_capability_id, notes="please add more columns support")
    assert capability_service.get(first_capability_id).status.value == "revision_requested"

    second = main_agent.run_task(
        task_family="csv_summary",
        description="summarize numeric columns of a csv file",
        input_data={"csv_text": "a,b\n1,2\n3,4\n"},
    )

    assert second["status"] == "capability_pending_approval"
    assert second["capability_id"] != first_capability_id
